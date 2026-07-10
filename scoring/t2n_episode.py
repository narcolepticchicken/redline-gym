"""Environment-side joins for the frozen T2-N scoring contract."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from scoring.core import _candidate_findings, _match_flag, _tiered_redline_match
from scoring.t2n_contract import evaluate_transition


def issue_phase1_positions(
    flags: list[dict[str, Any]],
    card: dict[str, Any] | None,
    deviations: list[dict[str, Any]],
    plants_by_deviation: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Issue opaque IDs from the same deduplicated finding union as core.py."""
    public: list[dict[str, Any]] = []
    lookup: dict[str, dict[str, Any]] = {}
    extra = 0
    used: set[str] = set()
    for finding in _candidate_findings(flags, card):
        match = _match_flag(finding, deviations)
        if match:
            position_id = "POS-" + str(match["deviation_id"]).replace("-", "")
            if position_id in used:
                continue
            plant = plants_by_deviation.get(str(match["deviation_id"]), {})
            lookup[position_id] = {
                "source_deviation_id": match["deviation_id"],
                "decision": "reject",
                "rule_id": match["rule_id"],
                "clause_id": plant.get("clause_id"),
                "fallback_text": finding.get("proposed_redline", ""),
                "comparator_record_id": plant.get("comparator_record_id"),
            }
            matched = True
        else:
            extra += 1
            position_id = f"POS-EXTRA-{extra}"
            lookup[position_id] = {
                "source_deviation_id": None,
                "decision": "reject",
                "rule_id": finding.get("rule_id"),
                "clause_id": None,
                "fallback_text": finding.get("proposed_redline", ""),
                "comparator_record_id": None,
            }
            matched = False
        used.add(position_id)
        public.append({
            "position_id": position_id,
            "rule_id": finding.get("rule_id"),
            "doc_id": finding.get("doc_id"),
            "clause_ref": finding.get("clause_ref"),
            "exact_quote": finding.get("exact_quote"),
            "matched": matched,
        })
    return public, lookup


def join_phase2_records(
    patches: Sequence[Mapping[str, Any]],
    reviews: Mapping[str, Mapping[str, Any]],
    conflicts: set[str],
    phase1_lookup: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Enrich submitted records with ledger truth without exposing it."""
    joined: list[dict[str, Any]] = []
    for raw in patches:
        child = dict(raw)
        # The frozen ledger schema has no is_labeled_concession field, while
        # TR-01 consumes it. Its value is unambiguous from the emitted type
        # and disposition, so materialize that derived truth for the join.
        child["is_labeled_concession"] = (
            child.get("event_type") == "concession"
            and child.get("expected_disposition") == "accept"
        )
        review = dict(reviews.get(str(child["change_id"]), {}))
        if child["change_id"] in conflicts:
            review["decision"] = None
        # review_change pins a ledger child and therefore its clause. The
        # action schema intentionally has no agent-submittable clause_id.
        phase2 = dict(review)
        phase2["clause_id"] = child.get("expected_clause_id")
        result = evaluate_transition(
            str(child["transition_row_id"]), child, phase2, phase1_lookup
        )
        record = dict(child)
        record.update(review)
        record.update(result)
        decision = review.get("decision")
        record["grounding_exact"] = (
            decision == "reject" and review.get("exact_quote") == child.get("ground_span")
        )
        record["redline_tier"] = 0.0
        if child.get("edit_required") and decision == "reject":
            record["redline_tier"] = _tiered_redline_match(
                str(review.get("proposed_redline", "")),
                str(child.get("expected_redline_text", "")),
                [],
            )
        record["harm_family"] = harm_family(child)
        joined.append(record)
    return joined


def harm_family(child: Mapping[str, Any]) -> str | None:
    if child.get("event_type") == "regression":
        return "regression"
    if child.get("event_type") == "sneaky_reinsert" and child.get("child_role") == "inserted_effect":
        return "sneak_inserted_child"
    if child.get("event_type") == "new_deviation":
        return "new_deviation"
    if child.get("event_type") == "counter_proposal" and child.get("counter_class") == "unacceptable":
        return "unacceptable_counter"
    return None
