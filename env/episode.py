from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from jsonschema import Draft202012Validator

from scoring.core import score_episode
from scoring.t2n_contract import CONTRACT_ID, compute_composite, score_all_concessions
from scoring.t2n_episode import issue_phase1_positions, join_phase2_records
from validators.t2n_checks import v14_t2n_ledger


ROOT = Path(__file__).resolve().parents[1]
ANSWER_KEY_NAMES = {"planted_deviations.json", "issue_matrix.json", "rubric.json", "task.json"}


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    type: str
    path: str
    text: str
    lines: list[str]


class Episode:
    def __init__(self, task_dir: str | Path, seed: int = 0, run_dir: str | Path | None = None) -> None:
        self.task_dir = Path(task_dir)
        if not self.task_dir.is_absolute():
            self.task_dir = (Path.cwd() / self.task_dir).resolve()
        else:
            self.task_dir = self.task_dir.resolve()
        self.seed = seed
        self.task = _read_json(self.task_dir / "task.json")
        self.task_id = self.task["task_id"]
        self.turn_cap = int(self.task.get("turn_cap", 25))
        self.run_root = Path(run_dir) if run_dir is not None else ROOT / "runs" / f"episode-{uuid4().hex[:12]}"
        if not self.run_root.is_absolute():
            self.run_root = (Path.cwd() / self.run_root).resolve()
        self.run_id = self.run_root.name
        self.episode_dir = self.run_root / self.task_id
        self.transcript_path = self.episode_dir / "episode.jsonl"
        self.score_path = self.episode_dir / "score.json"
        self.manifest = _read_json(self.task_dir / "documents_manifest.json")
        self.playbook = _read_json(ROOT / self.task["playbook_ref"])
        self.docs = self._load_manifest_docs()
        self.flags: list[dict[str, Any]] = []
        self.escalations: list[dict[str, Any]] = []
        self.card: dict[str, Any] | None = None
        self.read_ranges: dict[str, list[tuple[int, int]]] = {}
        self.search_count = 0
        self.num_turns = 0
        self.done = False
        self.ended_by: str | None = None
        self.last_observation: dict[str, Any] | None = None
        self._empty_finalize_warned = False
        self.t2n_mode = (self.task_dir / "patch_ledger.json").is_file() and (self.task_dir / "turn_events.json").is_file()
        self.phase = "phase1"
        self.reviews_by_change_id: dict[str, dict[str, Any]] = {}
        self.review_conflicts: set[str] = set()
        self.unknown_review_ids: set[str] = set()
        self.phase1_result: dict[str, Any] | None = None
        self.phase1_card: dict[str, Any] | None = None
        self.phase1_positions: list[dict[str, Any]] = []
        self.phase1_lookup: dict[str, dict[str, Any]] = {}
        self.t2n_result: dict[str, Any] | None = None
        if self.t2n_mode:
            self._load_t2n_artifacts()

    def reset(self) -> dict[str, Any]:
        self.flags = []
        self.escalations = []
        self.card = None
        self.read_ranges = {}
        self.search_count = 0
        self.num_turns = 0
        self.done = False
        self.ended_by = None
        self._empty_finalize_warned = False
        self.phase = "phase1"
        self.reviews_by_change_id = {}
        self.review_conflicts = set()
        self.unknown_review_ids = set()
        self.phase1_result = None
        self.phase1_card = None
        self.phase1_positions = []
        self.phase1_lookup = {}
        self.t2n_result = None
        self.episode_dir.mkdir(parents=True, exist_ok=True)
        self.transcript_path.write_text("")
        self.last_observation = self._base_observation(event="reset")
        return self.last_observation

    def step(self, action: dict[str, Any]) -> dict[str, Any]:
        if self.done:
            raise RuntimeError("episode already ended")
        if self.last_observation is None:
            self.reset()
        if not isinstance(action, dict):
            raise TypeError("action must be a JSON object")

        kind = action.get("action")
        self.num_turns += 1
        observation: dict[str, Any]
        try:
            observation = self._dispatch(kind, action)
        except (ValueError, TypeError, KeyError) as exc:
            # An invalid action must never kill the episode: report it as an
            # error observation, charge the turn, and let the agent recover.
            observation = self._base_observation(event="error", error=str(exc))

        if not self.done and self.num_turns >= self.turn_cap:
            self.done = True
            self.ended_by = "timeout"
            observation = self._base_observation(event="timeout", done=True, message="turn cap reached")

        self.last_observation = observation
        if self.done:
            self._write_score()
            observation["score_path"] = str(self.score_path)
        self._append_transcript(action, observation)
        return observation

    def _dispatch(self, kind: Any, action: dict[str, Any]) -> dict[str, Any]:
        if kind == "list_docs":
            observation = self._base_observation(event="list_docs")
        elif kind == "read_doc":
            observation = self._read_doc_action(action)
        elif kind == "search":
            observation = self._search_action(action)
        elif kind == "flag_issue":
            flag = self._flag_from_action(action)
            self.flags.append(flag)
            observation = self._base_observation(event="flag_issue", message="flag recorded")
        elif kind == "escalate":
            escalation = {
                "topic": str(action.get("topic", "")),
                "reason": str(action.get("reason", "")),
            }
            self.escalations.append(escalation)
            observation = self._base_observation(event="escalate", message="escalation recorded")
        elif kind == "review_change" and self.t2n_mode and self.phase == "phase2":
            observation = self._review_change(action)
        elif kind == "finalize":
            if self.t2n_mode:
                return self._t2n_finalize(action)
            card = action.get("card")
            empty_work = not self.flags and not self.escalations
            if empty_work and not self._empty_finalize_warned:
                # One confirmation bounce on an empty submission (a real
                # product would do the same). A repeated finalize proceeds.
                self._empty_finalize_warned = True
                observation = self._base_observation(
                    event="confirm_finalize",
                    message=(
                        "Your review recorded no flags and no escalations — the card "
                        "will score zero on all finding channels. Resend finalize to "
                        "confirm, or continue reviewing (read_doc / search / flag_issue "
                        "/ escalate)."
                    ),
                )
            else:
                self.card = card if isinstance(card, dict) else {}
                self.done = True
                self.ended_by = "finalize"
                observation = self._base_observation(event="finalize", done=True, message="episode finalized")
        else:
            observation = self._base_observation(event="error", error=f"unknown action: {kind!r}")
        return observation

    def _base_observation(
        self,
        *,
        event: str,
        done: bool | None = None,
        message: str | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        observation: dict[str, Any] = {
            "event": event,
            "task_id": self.task_id,
            "instruction": self.task["instruction"],
            "client_context": self.task["client_context"],
            "turn": self.num_turns,
            "turn_cap": self.turn_cap,
            "done": self.done if done is None else done,
            "documents": [
                {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "type": doc.type,
                }
                for doc in self.docs.values()
            ],
            "playbook": [
                {
                    "rule_id": rule["rule_id"],
                    "position": _strip_canary_prefix(rule["position"]),
                    "fallback": rule["fallback"],
                    "severity": rule["severity"],
                }
                for rule in self.playbook["rules"]
            ],
            "action_spec": {
                "list_docs": {"required": [], "optional": []},
                "read_doc": {"required": ["doc_id"], "optional": ["start", "end"]},
                "search": {"required": ["query"], "optional": []},
                "flag_issue": {
                    "required": ["rule_id", "doc_id", "clause_ref", "exact_quote"],
                    "optional": ["severity", "proposed_redline", "rationale"],
                },
                "escalate": {"required": ["topic", "reason"], "optional": []},
                "finalize": {
                    "required": ["card"],
                    "optional": [],
                    "card_shape": {
                        "issues": "[{rule_id, doc_id, clause_ref, exact_quote, proposed_redline?}]",
                        "escalations": "[{topic, reason}]",
                        "summary": "string",
                    },
                },
            },
        }
        if self.t2n_mode and self.phase == "phase2":
            observation["phase"] = "phase2"
            observation["action_spec"]["review_change"] = {
                "required": ["change_id", "origin", "decision"],
                "optional": ["prior_position_id", "rule_id", "exact_quote", "proposed_redline"],
                "conditions": {
                    "prior_position_id": "required iff origin is prior_position; forbidden otherwise",
                    "rule_id_and_exact_quote": "required iff decision is reject",
                },
            }
            observation["action_spec"]["finalize"]["card_shape"] = {
                "changes": "exact copy of accepted review_change actions",
                "escalations": "[{missing_info_id, reason}]",
                "summary": "non-empty string",
            }
        if message:
            observation["message"] = message
        if error:
            observation["error"] = error
        return observation

    def _read_doc_action(self, action: dict[str, Any]) -> dict[str, Any]:
        doc = self._doc(str(action.get("doc_id", "")))
        start = max(1, int(action.get("start", 1)))
        end = int(action.get("end", start + 24))
        end = min(len(doc.lines), max(start, end))
        self.read_ranges.setdefault(doc.doc_id, []).append((start, end))
        observation = self._base_observation(event="read_doc")
        observation["doc"] = {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "start": start,
            "end": end,
            "lines": [
                {"line": line_no, "text": doc.lines[line_no - 1]}
                for line_no in range(start, end + 1)
            ],
        }
        return observation

    def _search_action(self, action: dict[str, Any]) -> dict[str, Any]:
        self.search_count += 1
        query = str(action.get("query", "")).strip()
        terms = [term for term in re.split(r"\W+", query.lower()) if term]
        hits: list[dict[str, Any]] = []
        if terms:
            for doc in self.docs.values():
                headings = _line_headings(doc.lines)
                for idx, line in enumerate(doc.lines, start=1):
                    lower = line.lower()
                    score = sum(1 for term in terms if term in lower)
                    if score:
                        hits.append(
                            {
                                "doc_id": doc.doc_id,
                                "line": idx,
                                "score": score,
                                "clause_ref": headings.get(idx, ""),
                                "text": line,
                            }
                        )
        hits.sort(key=lambda item: (-item["score"], item["doc_id"], item["line"]))
        observation = self._base_observation(event="search")
        observation["query"] = query
        observation["results"] = hits[:10]
        return observation

    def _flag_from_action(self, action: dict[str, Any]) -> dict[str, Any]:
        required = ["rule_id", "doc_id", "clause_ref", "exact_quote"]
        missing = [field for field in required if not str(action.get(field, "")).strip()]
        if missing:
            raise ValueError(f"flag_issue missing required fields: {', '.join(missing)}")
        return {
            "rule_id": str(action.get("rule_id", "")),
            "doc_id": str(action.get("doc_id", "")),
            "clause_ref": str(action.get("clause_ref", "")),
            "exact_quote": str(action.get("exact_quote", "")),
            "severity": str(action.get("severity", "")),
            "proposed_redline": str(action.get("proposed_redline", "")),
            "rationale": str(action.get("rationale", "")),
        }

    def _load_t2n_artifacts(self) -> None:
        self.patch_ledger = _read_json(self.task_dir / "patch_ledger.json")
        self.turn_events = _read_json(self.task_dir / "turn_events.json")
        self.phase1_document = (self.task_dir / "phase1_document.txt").read_bytes()
        self.phase2_document = (self.task_dir / "phase2_document.txt").read_bytes()
        self.phase2_tracked_changes = (self.task_dir / "phase2_tracked_changes.md").read_text()
        rendered = json.loads((self.task_dir / "rendered_change_ids.json").read_text())
        self.rendered_change_ids = list(rendered.get("change_ids", rendered) if isinstance(rendered, dict) else rendered)
        self.patches_by_change_id = {str(p["change_id"]): p for p in self.patch_ledger["patches"]}
        self.plants_by_deviation = {
            str(p["prior_source_deviation_id"]): p["plant_position"]
            for p in self.patch_ledger["patches"]
            if p.get("origin") == "prior_position"
        }
        declared = self.task.get("task_type")
        only_concessions = bool(self.patch_ledger.get("patches")) and all(
            p.get("event_type") == "concession" for p in self.patch_ledger["patches"]
        )
        self.t2n_task_type = "t2n_all_concessions" if declared == "t2n_all_concessions" or only_concessions else "t2n_mixed"
        schema_dir = ROOT / "schema" / "t2n"
        self.review_validator = Draft202012Validator(_read_json(schema_dir / "review_action.schema.json"))
        self.card_t2n_validator = Draft202012Validator(_read_json(schema_dir / "card_t2n.schema.json"))

    def _review_change(self, action: dict[str, Any]) -> dict[str, Any]:
        errors = sorted(self.review_validator.iter_errors(action), key=lambda e: list(e.path))
        if errors:
            raise ValueError("review_change schema violation: " + "; ".join(e.message for e in errors))
        review = dict(action)
        change_id = str(review["change_id"])
        if change_id not in self.patches_by_change_id:
            self.unknown_review_ids.add(change_id)
        if change_id in self.reviews_by_change_id:
            if self.reviews_by_change_id[change_id] != review:
                self.review_conflicts.add(change_id)
                message = "conflicting review recorded; first submission retained"
            else:
                message = "identical review collapsed"
        else:
            self.reviews_by_change_id[change_id] = review
            message = "review recorded"
        return self._base_observation(event="review_change", message=message)

    def _t2n_finalize(self, action: dict[str, Any]) -> dict[str, Any]:
        if self.phase == "phase1":
            card = action.get("card")
            empty_work = not self.flags and not self.escalations
            if empty_work and not self._empty_finalize_warned:
                self._empty_finalize_warned = True
                return self._base_observation(
                    event="confirm_finalize",
                    message=("Your review recorded no flags and no escalations — the card will score zero "
                             "on all finding channels. Resend finalize to confirm, or continue reviewing "
                             "(read_doc / search / flag_issue / escalate)."),
                )
            self.card = card if isinstance(card, dict) else {}
            self.phase1_card = self.card
            self.phase1_result = score_episode(
                self.task_dir, self.flags, self.escalations, self.card,
                read_ranges=self.read_ranges, search_count=self.search_count,
            )
            deviations = _read_json(self.task_dir / "planted_deviations.json").get("deviations", [])
            self.phase1_positions, self.phase1_lookup = issue_phase1_positions(
                self.flags, self.card, deviations, self.plants_by_deviation
            )
            self.phase = "phase2"
            self._empty_finalize_warned = False
            observation = self._base_observation(
                event="phase2_reveal", message="Phase 1 finalized; counterparty tracked changes revealed."
            )
            observation["issued_positions"] = self.phase1_positions
            observation["tracked_changes"] = self.phase2_tracked_changes
            observation["changes"] = self._public_changes()
            return observation

        card = action.get("card")
        empty_work = not self.reviews_by_change_id
        if empty_work and not self._empty_finalize_warned:
            self._empty_finalize_warned = True
            return self._base_observation(
                event="confirm_finalize",
                message=("Your phase-2 review recorded no review_change actions. Resend finalize to "
                         "confirm, or continue dispositioning tracked changes."),
            )
        self.card = card if isinstance(card, dict) else {}
        self._score_t2n()
        self.done = True
        self.ended_by = "finalize"
        return self._base_observation(event="finalize", done=True, message="episode finalized")

    def _public_changes(self) -> list[dict[str, Any]]:
        allowed = {"change_id", "event_id", "event_type", "child_role", "origin", "doc_id",
                   "section_ref", "op", "before_text", "after_text"}
        event_inputs = {}
        for event in self.turn_events.get("events", []):
            inputs = event.get("counter_inputs")
            if inputs:
                event_inputs[event["event_id"]] = {
                    key: inputs[key] for key in ("counter_text_slots", "phase1_context_slots", "decoy_values")
                    if key in inputs
                }
        output = []
        for patch in self.patch_ledger["patches"]:
            item = {key: patch[key] for key in allowed if key in patch}
            if patch.get("event_id") in event_inputs:
                item["counter_inputs"] = event_inputs[patch["event_id"]]
            output.append(item)
        return output

    def _score_t2n(self) -> None:
        card_errors = list(self.card_t2n_validator.iter_errors(self.card))
        card_changes = self.card.get("changes", []) if isinstance(self.card, dict) else []
        advertised = set(self.patches_by_change_id)
        submitted = set(self.reviews_by_change_id)
        if self.t2n_task_type == "t2n_all_concessions":
            interactive_equal = isinstance(card_changes, list) and {
                c.get("change_id"): c for c in card_changes if isinstance(c, dict)
            } == self.reviews_by_change_id
            explicit_accept_all = advertised == submitted and all(
                self.reviews_by_change_id[c].get("decision") == "accept" for c in advertised
            )
            valid_links = all(
                self.reviews_by_change_id.get(c, {}).get("prior_position_id") in self.phase1_lookup
                for c, p in self.patches_by_change_id.items() if p.get("origin") == "prior_position"
            )
            conformance = not card_errors and not self.review_conflicts and not self.unknown_review_ids and advertised == submitted and interactive_equal
            result = score_all_concessions(
                complete_read_coverage=True, explicit_accept_all=explicit_accept_all,
                interactive_card_equal=interactive_equal, valid_prior_links=valid_links,
                restraint=float(explicit_accept_all), continuity=float(valid_links),
                conformance=float(conformance), abstention=1.0,
            )
            self.t2n_result = {
                **result, "composite": result["score"], "reported_E": result["score"],
                "contract_id": CONTRACT_ID, "task_type": self.t2n_task_type,
                "conformance": float(conformance), "status": "OK", "phase1": self.phase1_result,
            }
            return
        v14 = v14_t2n_ledger(
            canonical_document=self.phase1_document, phase2_document=self.phase2_document,
            ledger=self.patch_ledger, turn_events=self.turn_events,
            rendered_change_ids=self.rendered_change_ids,
            reviews_by_change_id=self.reviews_by_change_id, card_changes=card_changes,
        )
        conformance = (
            not card_errors and advertised == submitted and not self.unknown_review_ids
            and not self.review_conflicts and v14.status == "PASS"
        )
        joined = join_phase2_records(
            self.patch_ledger["patches"], self.reviews_by_change_id,
            self.review_conflicts, self.phase1_lookup,
        )
        result = compute_composite(
            joined, float((self.phase1_result or {}).get("composite", 0.0)),
            conformance=conformance, planted_missing_ids=(), submitted_missing_ids=(),
        )
        canary_rejected = any(
            p.get("origin") == "canary_probe"
            and self.reviews_by_change_id.get(str(p["change_id"]), {}).get("decision") == "reject"
            for p in self.patch_ledger["patches"]
        )
        final_phase1_status = score_episode(
            self.task_dir, self.flags, self.escalations, self.phase1_card,
            read_ranges=self.read_ranges, search_count=self.search_count,
        ).get("status")
        gamed = final_phase1_status == "GAMED" or canary_rejected
        self.t2n_result = {
            **result, "composite": result["reported_E"], "task_type": self.t2n_task_type,
            "status": "GAMED" if gamed else "OK", "phase1": self.phase1_result,
            "telemetry": {"children": joined, "v14": {"status": v14.status, "detail": v14.detail}},
        }

    def _load_manifest_docs(self) -> dict[str, Document]:
        docs_dir = (self.task_dir / "docs").resolve()
        docs: dict[str, Document] = {}
        for entry in self.manifest["documents"]:
            rel_path = Path(entry["path"])
            if rel_path.name in ANSWER_KEY_NAMES:
                raise ValueError(f"manifest may not expose answer-key file: {rel_path}")
            full_path = (self.task_dir / rel_path).resolve()
            if not full_path.is_file() or docs_dir not in full_path.parents:
                raise ValueError(f"manifest document path must stay under docs/: {rel_path}")
            text = full_path.read_text()
            docs[entry["doc_id"]] = Document(
                doc_id=entry["doc_id"],
                title=entry["title"],
                type=entry["type"],
                path=entry["path"],
                text=text,
                lines=text.splitlines(),
            )
        return docs

    def _doc(self, doc_id: str) -> Document:
        try:
            return self.docs[doc_id]
        except KeyError as exc:
            raise ValueError(f"unknown doc_id: {doc_id}") from exc

    def _append_transcript(self, action: dict[str, Any], observation: dict[str, Any]) -> None:
        record = {
            "turn": self.num_turns,
            "action": action,
            "observation": observation,
        }
        with self.transcript_path.open("a") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")

    def _write_score(self) -> dict[str, Any]:
        if self.t2n_mode and self.phase == "phase2":
            if self.t2n_result is None:
                self.card = self.card if isinstance(self.card, dict) else {}
                self._score_t2n()
            score = dict(self.t2n_result or {})
        else:
            score = score_episode(
                self.task_dir,
                self.flags,
                self.escalations,
                self.card,
                read_ranges=self.read_ranges,
                search_count=self.search_count,
            )
        score.update(
            {
                "run_id": self.run_id,
                "task_id": self.task_id,
                "seed": self.seed,
                "num_turns": self.num_turns,
                "ended_by": self.ended_by,
            }
        )
        self.score_path.write_text(json.dumps(score, indent=2, sort_keys=True) + "\n")
        return score


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _strip_canary_prefix(text: str) -> str:
    return re.sub(r"^\s*Canary:\s*", "", text)


def _line_headings(lines: list[str]) -> dict[int, str]:
    current = ""
    headings: dict[int, str] = {}
    for idx, line in enumerate(lines, start=1):
        if line.startswith("## "):
            current = line[3:].strip()
        headings[idx] = current
    return headings
