from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from scoring.core import score_episode


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
        self.num_turns = 0
        self.done = False
        self.ended_by: str | None = None
        self.last_observation: dict[str, Any] | None = None

    def reset(self) -> dict[str, Any]:
        self.flags = []
        self.escalations = []
        self.card = None
        self.num_turns = 0
        self.done = False
        self.ended_by = None
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
        elif kind == "finalize":
            card = action.get("card")
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
        return {
            "rule_id": str(action.get("rule_id", "")),
            "doc_id": str(action.get("doc_id", "")),
            "clause_ref": str(action.get("clause_ref", "")),
            "exact_quote": str(action.get("exact_quote", "")),
            "severity": str(action.get("severity", "")),
            "proposed_redline": str(action.get("proposed_redline", "")),
            "rationale": str(action.get("rationale", "")),
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
        score = score_episode(self.task_dir, self.flags, self.escalations, self.card)
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
