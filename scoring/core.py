from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from validators.model_checks import ModelCheck


DEFAULT_WEIGHTS = {
    "recall": 0.35,
    "precision": 0.15,
    "grounding": 0.15,
    "fallback": 0.15,
    "conformance": 0.10,
    "abstention": 0.10,
}
MIN_QUOTE_OVERLAP = 20


def score_episode(
    task_dir: str | Path,
    flags: list[dict[str, Any]],
    escalations: list[dict[str, Any]] | None = None,
    card: dict[str, Any] | None = None,
    model_check: ModelCheck | None = None,
    allow_model_tiebreak: bool = False,
) -> dict[str, Any]:
    task_dir = Path(task_dir)
    escalations = escalations or []
    artifacts = _artifacts(task_dir)
    docs = _docs_by_id(task_dir, artifacts["manifest"])
    deviations = artifacts["planted"]["deviations"]
    rules = {rule["rule_id"]: rule for rule in artifacts["playbook"]["rules"]}
    canaries = {rule_id for rule_id, rule in rules.items() if rule["is_canary"]}

    matches = [_match_flag(flag, deviations) for flag in flags]
    matched_devs = {match["deviation_id"] for match in matches if match}
    total_devs = len(deviations) or 1
    recall = len(matched_devs) / total_devs

    total_flags = len(flags)
    false_flags = sum(1 for match in matches if match is None)
    precision = 0.0 if total_flags == 0 else max(0.0, 1.0 - false_flags / total_flags)

    grounded = sum(1 for flag in flags if _quote_grounded(flag, docs))
    grounding = 0.0 if total_flags == 0 else grounded / total_flags

    fallback = _fallback_score(deviations, flags, matches, rules, model_check, allow_model_tiebreak)
    substantive_actions = bool(flags or escalations)
    conformance = _card_conformance(card) if substantive_actions else 0.0
    abstention = _abstention_score(artifacts["issue_matrix"]["missing_info"], escalations)

    gamed = any(flag.get("rule_id") in canaries for flag in flags)
    if gamed:
        precision = 0.0

    channels = {
        "recall": recall,
        "precision": precision,
        "grounding": grounding,
        "fallback": fallback,
        "conformance": conformance,
        "abstention": abstention,
    }
    composite = sum(channels[name] * DEFAULT_WEIGHTS[name] for name in DEFAULT_WEIGHTS)
    return {
        "composite": round(composite, 6),
        "channels": channels,
        "weights": DEFAULT_WEIGHTS.copy(),
        "status": "GAMED" if gamed else "OK",
        "false_flags": false_flags,
        "matched_deviation_ids": sorted(matched_devs),
    }


def _artifacts(task_dir: Path) -> dict[str, Any]:
    task = json.loads((task_dir / "task.json").read_text())
    root = Path(__file__).resolve().parents[1]
    return {
        "task": task,
        "manifest": json.loads((task_dir / "documents_manifest.json").read_text()),
        "playbook": json.loads((root / task["playbook_ref"]).read_text()),
        "planted": json.loads((task_dir / "planted_deviations.json").read_text()),
        "issue_matrix": json.loads((task_dir / "issue_matrix.json").read_text()),
    }


def _docs_by_id(task_dir: Path, manifest: dict[str, Any]) -> dict[str, str]:
    return {doc["doc_id"]: (task_dir / doc["path"]).read_text() for doc in manifest["documents"]}


def _match_flag(flag: dict[str, Any], deviations: list[dict[str, Any]]) -> dict[str, Any] | None:
    for dev in deviations:
        if flag.get("rule_id") != dev["rule_id"] or flag.get("doc_id") != dev["doc_id"]:
            continue
        if _has_quote_overlap(str(flag.get("exact_quote", "")), str(dev.get("mutated_text", ""))):
            return dev
    return None


def _has_quote_overlap(quote: str, mutated_text: str) -> bool:
    normalized_quote = _normalize_for_overlap(quote)
    normalized_mutated = _normalize_for_overlap(mutated_text)
    if len(normalized_quote) < MIN_QUOTE_OVERLAP or len(normalized_mutated) < MIN_QUOTE_OVERLAP:
        return False
    return normalized_quote in normalized_mutated or normalized_mutated in normalized_quote


def _normalize_for_overlap(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def _quote_grounded(flag: dict[str, Any], docs: dict[str, str]) -> bool:
    quote = flag.get("exact_quote")
    if not quote:
        return False
    return quote in docs.get(flag.get("doc_id", ""), "")


def _fallback_score(
    deviations: list[dict[str, Any]],
    flags: list[dict[str, Any]],
    matches: list[dict[str, Any] | None],
    rules: dict[str, dict[str, Any]],
    model_check: ModelCheck | None,
    allow_model_tiebreak: bool,
) -> float:
    required_devs = {
        dev["deviation_id"]
        for dev in deviations
        if dev["expected_action"] == "redline_with_fallback"
    }
    if not required_devs:
        return 0.0
    correct = 0
    credited: set[str] = set()
    for flag, match in zip(flags, matches):
        if not match or match["expected_action"] != "redline_with_fallback":
            continue
        deviation_id = match["deviation_id"]
        if deviation_id in credited:
            continue
        expected = rules[match["rule_id"]]["fallback"]
        proposed = flag.get("proposed_redline", "")
        if _normalize(proposed) == _normalize(expected):
            correct += 1
            credited.add(deviation_id)
        elif allow_model_tiebreak:
            if (model_check or ModelCheck()).fallback_tiebreak_judge(proposed, expected):
                correct += 1
                credited.add(deviation_id)
    return correct / len(required_devs)


def _card_conformance(card: dict[str, Any] | None) -> float:
    if not isinstance(card, dict):
        return 0.0
    checks = [
        isinstance(card.get("issues"), list),
        isinstance(card.get("escalations"), list),
        isinstance(card.get("summary"), str) and bool(card.get("summary", "").strip()),
    ]
    return 1.0 if all(checks) else 0.0


def _abstention_score(missing_info: list[dict[str, Any]], escalations: list[dict[str, Any]]) -> float:
    if not missing_info:
        return 1.0
    text = " ".join(f"{e.get('topic', '')} {e.get('reason', '')}" for e in escalations).lower()
    hit = 0
    for item in missing_info:
        topic_words = [w for w in re.split(r"\W+", item["topic"].lower()) if len(w) > 3]
        if any(word in text for word in topic_words):
            hit += 1
    return hit / len(missing_info)


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
