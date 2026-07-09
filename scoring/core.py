from __future__ import annotations

import json
import os
from pathlib import Path
import re
from typing import Any

from jsonschema import Draft202012Validator

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
ROOT = Path(__file__).resolve().parents[1]
CARD_SCHEMA = json.loads((ROOT / "schema/card.schema.json").read_text())
RULE_CATEGORIES = json.loads((ROOT / "scoring/rule_categories.json").read_text())
CARD_VALIDATOR = Draft202012Validator(CARD_SCHEMA)


def score_episode(
    task_dir: str | Path,
    flags: list[dict[str, Any]],
    escalations: list[dict[str, Any]] | None = None,
    card: dict[str, Any] | None = None,
    model_check: ModelCheck | None = None,
    allow_model_tiebreak: bool = False,
    scorer_v2: bool | None = None,
) -> dict[str, Any]:
    task_dir = Path(task_dir)
    escalations = escalations or []
    use_v2 = os.getenv("REDLINE_SCORER_V2") == "1" if scorer_v2 is None else scorer_v2
    scorer_version = "v2" if use_v2 else "v1"
    artifacts = _artifacts(task_dir)
    docs = _docs_by_id(task_dir, artifacts["manifest"])
    deviations = artifacts["planted"]["deviations"]
    rules = {rule["rule_id"]: rule for rule in artifacts["playbook"]["rules"]}
    canaries = {rule_id for rule_id, rule in rules.items() if rule["is_canary"]}

    union_findings = _candidate_findings(flags, card)
    card_issues = _card_issues(card)
    findings = union_findings if use_v2 else flags
    matches = [_match_flag(finding, deviations) for finding in findings]
    matched_devs = {match["deviation_id"] for match in matches if match}
    total_devs = len(deviations) or 1
    recall = len(matched_devs) / total_devs

    total_flags = len(findings)
    false_flags = sum(1 for match in matches if match is None)
    precision = 0.0 if total_flags == 0 else max(0.0, 1.0 - false_flags / total_flags)

    grounded = sum(1 for finding in findings if _quote_grounded(finding, docs))
    grounding = 0.0 if total_flags == 0 else grounded / total_flags

    fallback = _fallback_score(deviations, findings, matches, rules, model_check, allow_model_tiebreak)
    substantive_actions = bool(flags or escalations)
    conformance = _card_conformance(card) if substantive_actions else 0.0
    abstention = _abstention_score(artifacts["issue_matrix"]["missing_info"], escalations)

    gamed = any(finding.get("rule_id") in canaries for finding in findings)
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
    telemetry = _telemetry(
        flags=flags,
        card_issues=card_issues,
        union_findings=union_findings,
        escalations=escalations,
        deviations=deviations,
        distractors=artifacts["planted"].get("distractors", []),
        matched_devs=matched_devs,
        playbook_id=str(artifacts["playbook"].get("playbook_id", "")),
    )
    return {
        "composite": round(composite, 6),
        "channels": channels,
        "weights": DEFAULT_WEIGHTS.copy(),
        "scorer_version": scorer_version,
        "status": "GAMED" if gamed else "OK",
        "false_flags": false_flags,
        "matched_deviation_ids": sorted(matched_devs),
        "telemetry": telemetry,
    }


def _candidate_findings(flags: list[dict[str, Any]], card: dict[str, Any] | None) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for finding in [*flags, *_card_issues(card)]:
        rule_id = str(finding.get("rule_id", ""))
        quote = _normalize_for_overlap(str(finding.get("exact_quote", "")))
        key = (rule_id, quote)
        if key in seen:
            continue
        seen.add(key)
        findings.append(finding)
    return findings


def _card_issues(card: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(card, dict) or not isinstance(card.get("issues"), list):
        return []
    return [issue for issue in card["issues"] if isinstance(issue, dict)]


def _artifacts(task_dir: Path) -> dict[str, Any]:
    task = json.loads((task_dir / "task.json").read_text())
    return {
        "task": task,
        "manifest": json.loads((task_dir / "documents_manifest.json").read_text()),
        "playbook": json.loads((ROOT / task["playbook_ref"]).read_text()),
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


def _telemetry(
    *,
    flags: list[dict[str, Any]],
    card_issues: list[dict[str, Any]],
    union_findings: list[dict[str, Any]],
    escalations: list[dict[str, Any]],
    deviations: list[dict[str, Any]],
    distractors: list[dict[str, Any]],
    matched_devs: set[str],
    playbook_id: str,
) -> dict[str, Any]:
    union_finding_count = len(union_findings)
    raw_findings = [*flags, *card_issues]
    return {
        "flag_action_count": len(flags),
        "card_issue_count": len(card_issues),
        "union_finding_count": union_finding_count,
        "escalation_count": len(escalations),
        "duplicate_finding_count": _duplicate_finding_count(raw_findings),
        "flags_per_matched_deviation": (
            None if not matched_devs else union_finding_count / len(matched_devs)
        ),
        "mean_exact_quote_chars": _mean_chars(union_findings, "exact_quote"),
        "mean_proposed_redline_chars": _mean_chars(union_findings, "proposed_redline"),
        "filing_channel": _filing_channel(flags, card_issues, deviations, matched_devs),
        "distractor_hits": _distractor_hits(union_findings, distractors),
        "per_category": _per_category(deviations, matched_devs, playbook_id),
    }


def _duplicate_finding_count(findings: list[dict[str, Any]]) -> int:
    duplicates = 0
    for index, finding in enumerate(findings):
        if any(_same_finding_cluster(finding, earlier) for earlier in findings[:index]):
            duplicates += 1
    return duplicates


def _same_finding_cluster(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        left.get("rule_id") == right.get("rule_id")
        and left.get("doc_id") == right.get("doc_id")
        and _has_quote_overlap(str(left.get("exact_quote", "")), str(right.get("exact_quote", "")))
    )


def _mean_chars(findings: list[dict[str, Any]], field: str) -> float | None:
    lengths = [len(str(value)) for finding in findings if (value := finding.get(field, ""))]
    if not lengths:
        return None
    return sum(lengths) / len(lengths)


def _filing_channel(
    flags: list[dict[str, Any]],
    card_issues: list[dict[str, Any]],
    deviations: list[dict[str, Any]],
    matched_devs: set[str],
) -> str:
    if not matched_devs:
        return "none"
    interactive_devs = _matched_deviation_ids(flags, deviations)
    card_devs = _matched_deviation_ids(card_issues, deviations)
    if matched_devs <= interactive_devs and matched_devs.isdisjoint(card_devs):
        return "interactive"
    if matched_devs <= card_devs and matched_devs.isdisjoint(interactive_devs):
        return "card_only"
    return "mixed"


def _matched_deviation_ids(findings: list[dict[str, Any]], deviations: list[dict[str, Any]]) -> set[str]:
    return {
        match["deviation_id"]
        for finding in findings
        if (match := _match_flag(finding, deviations))
    }


def _distractor_hits(findings: list[dict[str, Any]], distractors: list[dict[str, Any]]) -> int:
    return sum(
        1
        for finding in findings
        if any(
            finding.get("doc_id") == distractor.get("doc_id")
            and _has_quote_overlap(
                str(finding.get("exact_quote", "")),
                str(distractor.get("span", "")),
            )
            for distractor in distractors
        )
    )


def _per_category(
    deviations: list[dict[str, Any]],
    matched_devs: set[str],
    playbook_id: str,
) -> dict[str, dict[str, int]]:
    category_map = RULE_CATEGORIES.get(playbook_id, {})
    per_category: dict[str, dict[str, int]] = {}
    for deviation in deviations:
        category = category_map.get(deviation["rule_id"], "uncategorized")
        bucket = per_category.setdefault(category, {"planted": 0, "matched": 0})
        bucket["planted"] += 1
        if deviation["deviation_id"] in matched_devs:
            bucket["matched"] += 1
    return per_category


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
    return 0.0 if list(CARD_VALIDATOR.iter_errors(card)) else 1.0


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
