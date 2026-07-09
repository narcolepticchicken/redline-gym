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
CLEAN_WEIGHTS = {
    "precision": 0.5,
    "conformance": 0.25,
    "abstention": 0.25,
    "recall": 0.0,
    "grounding": 0.0,
    "fallback": 0.0,
}
CLEAN_ENGAGEMENT_DOC_COVERAGE = 0.5
FALLBACK_TIER_EXACT = 1.00
FALLBACK_TIER_SPAN = 0.75
FALLBACK_TIER_CONTAINMENT = 0.50
FALLBACK_TIER_NONE = 0.00
SPAN_TOKEN_ORDER_THRESHOLD = 0.80
CONTAINMENT_TOKEN_THRESHOLD = 0.60
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
    read_ranges: dict[str, list[tuple[int, int]]] | None = None,
    search_count: int = 0,
) -> dict[str, Any]:
    task_dir = Path(task_dir)
    escalations = escalations or []
    use_v2 = os.getenv("REDLINE_SCORER_V2") == "1" if scorer_v2 is None else scorer_v2
    scorer_version = "v2" if use_v2 else "v1"
    artifacts = _artifacts(task_dir)
    docs = _docs_by_id(task_dir, artifacts["manifest"])
    task_type = artifacts["task"].get("task_type", "seeded")
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

    fallback, fallback_scoring = _fallback_score(
        deviations, findings, matches, rules, model_check, allow_model_tiebreak
    )
    substantive_actions = bool(flags or escalations)
    conformance = _card_conformance(card) if substantive_actions else 0.0
    abstention = _abstention_score(artifacts["issue_matrix"]["missing_info"], escalations)

    if task_type == "clean":
        engaged = _clean_engaged(docs, read_ranges or {}, search_count)
        if not engaged:
            channels = {name: 0.0 for name in DEFAULT_WEIGHTS}
        else:
            channels = {
                "recall": recall,
                "precision": 1.0 if total_flags == 0 else precision,
                "grounding": grounding,
                "fallback": fallback,
                "conformance": _card_conformance(card),
                "abstention": _clean_abstention_score(
                    artifacts["issue_matrix"]["missing_info"], escalations
                ),
            }
    else:
        channels = {
            "recall": recall,
            "precision": precision,
            "grounding": grounding,
            "fallback": fallback,
            "conformance": conformance,
            "abstention": abstention,
        }

    gamed = any(finding.get("rule_id") in canaries for finding in findings)
    if gamed:
        channels["precision"] = 0.0

    weights = CLEAN_WEIGHTS if task_type == "clean" else DEFAULT_WEIGHTS
    composite = sum(channels[name] * weights[name] for name in weights)
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
        "weights": weights.copy(),
        "task_type": task_type,
        "fallback_scoring": fallback_scoring,
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
) -> tuple[float, str]:
    required_devs = {
        dev["deviation_id"]
        for dev in deviations
        if dev["expected_action"] == "redline_with_fallback"
    }
    if not required_devs:
        return 0.0, "v1"
    deviations_by_id = {dev["deviation_id"]: dev for dev in deviations}
    use_tiered = all(
        bool(deviations_by_id[deviation_id].get("expected_redline_text"))
        for deviation_id in required_devs
    )
    if use_tiered:
        tier_values = []
        for deviation_id in required_devs:
            dev = deviations_by_id[deviation_id]
            tier_values.append(
                max(
                    (
                        _tiered_redline_match(
                            str(flag.get("proposed_redline", "")),
                            str(dev["expected_redline_text"]),
                            [str(value) for value in dev.get("expected_redline_key_slots", [])],
                        )
                        for flag, match in zip(flags, matches)
                        if match and match["deviation_id"] == deviation_id
                    ),
                    default=FALLBACK_TIER_NONE,
                )
            )
        return sum(tier_values) / len(required_devs), "tiered_v2"

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
    return correct / len(required_devs), "v1"


def _tiered_redline_match(
    proposed: str,
    expected_text: str,
    expected_key_slots: list[str],
) -> float:
    if not proposed:
        return FALLBACK_TIER_NONE
    if _normalize_redline_text(proposed) == _normalize_redline_text(expected_text):
        return FALLBACK_TIER_EXACT

    expected_tokens = _content_tokens(expected_text)
    proposed_tokens = _content_tokens(proposed)
    if not expected_tokens:
        return FALLBACK_TIER_NONE
    slots_present = all(slot.casefold() in proposed.casefold() for slot in expected_key_slots)
    ordered_ratio = _lcs_length(expected_tokens, proposed_tokens) / len(expected_tokens)
    if slots_present and ordered_ratio >= SPAN_TOKEN_ORDER_THRESHOLD:
        return FALLBACK_TIER_SPAN

    expected_set = set(expected_tokens)
    proposed_set = set(proposed_tokens)
    containment = len(expected_set & proposed_set) / len(expected_set)
    if containment >= CONTAINMENT_TOKEN_THRESHOLD:
        return FALLBACK_TIER_CONTAINMENT
    return FALLBACK_TIER_NONE


def _normalize_redline_text(text: str) -> str:
    normalized = text.casefold().translate(
        str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'})
    )
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return re.sub(r"\s+([,.;:])", r"\1", normalized)


def _content_tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+", text.casefold())


def _lcs_length(left: list[str], right: list[str]) -> int:
    previous = [0] * (len(right) + 1)
    for left_token in left:
        current = [0]
        for index, right_token in enumerate(right, start=1):
            if left_token == right_token:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current
    return previous[-1]


def _card_conformance(card: dict[str, Any] | None) -> float:
    if not isinstance(card, dict):
        return 0.0
    return 0.0 if list(CARD_VALIDATOR.iter_errors(card)) else 1.0


def _abstention_score(missing_info: list[dict[str, Any]], escalations: list[dict[str, Any]]) -> float:
    if not missing_info:
        return 1.0
    hit = sum(
        1
        for item in missing_info
        if any(_escalation_matches_missing_info(escalation, item) for escalation in escalations)
    )
    return hit / len(missing_info)


def _clean_abstention_score(
    missing_info: list[dict[str, Any]],
    escalations: list[dict[str, Any]],
) -> float:
    spurious = any(
        not any(_escalation_matches_missing_info(escalation, item) for item in missing_info)
        for escalation in escalations
    )
    return 0.0 if spurious else 1.0


def _escalation_matches_missing_info(
    escalation: dict[str, Any],
    missing_info: dict[str, Any],
) -> bool:
    text = f"{escalation.get('topic', '')} {escalation.get('reason', '')}".lower()
    topic_words = [
        word for word in re.split(r"\W+", missing_info["topic"].lower()) if len(word) > 3
    ]
    return any(word in text for word in topic_words)


def _clean_engaged(
    docs: dict[str, str],
    read_ranges: dict[str, list[tuple[int, int]]],
    search_count: int,
) -> bool:
    docs_total = len(docs)
    docs_covered = sum(1 for doc_id in docs if read_ranges.get(doc_id))
    coverage_a = docs_total > 0 and docs_covered / docs_total >= CLEAN_ENGAGEMENT_DOC_COVERAGE
    has_search = search_count >= 1
    full_coverage = all(
        _ranges_cover_all_lines(len(text.splitlines()), read_ranges.get(doc_id, []))
        for doc_id, text in docs.items()
    )
    return (coverage_a and has_search) or full_coverage


def _ranges_cover_all_lines(line_count: int, ranges: list[tuple[int, int]]) -> bool:
    if line_count == 0:
        return True
    clipped = sorted(
        (max(1, start), min(line_count, end))
        for start, end in ranges
        if min(line_count, end) >= max(1, start)
    )
    next_line = 1
    for start, end in clipped:
        if start > next_line:
            return False
        next_line = max(next_line, end + 1)
        if next_line > line_count:
            return True
    return False


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
