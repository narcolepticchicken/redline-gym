"""Frozen T2-N reward contract as data and pure functions (no env I/O)."""
from __future__ import annotations

from dataclasses import dataclass
import json
from math import sqrt
import re
from typing import Any, Mapping, Sequence


# v4 continuity required an answer-key-only fallback field, producing L=0 in
# 25/25 stored real episodes; v4.1 removes that inaccessible equality term.
CONTRACT_ID = "t2n-reward-v4.1"
# Changing any constant, denominator, gate, or table row changes the contract
# hash and voids all prior gate runs.

# v4 §1.2
CHANNEL_WEIGHTS = {"S": .30, "T": .20, "J": .15, "Q": .10, "L": .10,
                   "G": .05, "D": .05, "F": .03, "A": .02}
assert abs(sum(CHANNEL_WEIGHTS.values()) - 1.0) < 1e-12
ORDINARY_FLOORS = {name: .50 for name in ("S", "T", "J", "L", "G")}  # v4 §1.3
REQUIRED_FAMILIES = ("regression", "sneak_inserted_child", "new_deviation")  # v4 §1.3
# v4 §1.7 family-level authoring minima. Attack accuracies require a tranche.
COUNTER_FAMILY_MINIMUMS = {"decisive_counter_slots": 1, "decisive_context_slots": 1,
                           "decoys": 2, "render_forms_per_decisive_input": 3,
                           "heldout_attack_balanced_accuracy_max_exclusive": .60}


@dataclass(frozen=True)
class TransitionRow:
    """One exhaustive transition row from v4 §1.4."""
    row_id: str
    event_type: str
    child_role: str
    origin: str
    prior_position_id: str
    required_decision: str
    continuity: bool
    requirements: tuple[str, ...]


def _row(row_id: str, event: str, role: str, origin: str, prior: str,
         decision: str, continuity: bool, *requirements: str) -> TransitionRow:
    return TransitionRow(row_id, event, role, origin, prior, decision, continuity, requirements)


# v4 §1.4 TR-01..TR-07. "emitted" means expected_disposition controls.
TRANSITION_ROWS = {
    r.row_id: r for r in (
        _row("TR-01", "concession", "sole", "prior_position", "required", "accept", True,
             "eligible P1", "P1 reject", "same rule", "source clause", "fallback=", "labeled concession"),
        _row("TR-02", "regression", "sole", "prior_position", "required", "reject", True,
             "eligible P1", "P1 reject", "same rule", "source clause", "fallback="),
        _row("TR-03", "sneaky_reinsert", "source_cleanup", "prior_position", "required", "accept", True,
             "eligible P1", "P1 reject", "same rule", "source clause", "fallback=", "child clause=source"),
        _row("TR-04", "sneaky_reinsert", "inserted_effect", "prior_position", "required", "reject", True,
             "eligible P1", "P1 reject", "same rule", "source differs destination", "fallback="),
        _row("TR-05", "counter_proposal", "sole", "prior_position", "required", "emitted", True,
             "eligible P1", "P1 reject", "same rule", "source clause", "fallback=", "counter guard exact"),
        _row("TR-06", "new_deviation", "sole", "novel_insertion", "forbidden", "reject", False,
             "submitted rule", "destination clause", "no P1 consulted"),
        _row("TR-07", "benign_canary_change", "sole", "canary_probe", "forbidden", "accept", False,
             "no P1 consulted"),
    )
}
LEGAL_TRANSITION_TRIPLES = {
    (r.event_type, r.child_role, r.origin): r.row_id for r in TRANSITION_ROWS.values()
}


def normalize_fallback(value: str) -> str:
    """Normalize fallback equality for v4 §1.1 (case/whitespace only)."""
    return re.sub(r"\s+", " ", value).strip().casefold()


def evaluate_transition(row_id: str, child_record: Mapping[str, Any],
                        phase2_record: Mapping[str, Any],
                        phase1_lookup: Mapping[str, Mapping[str, Any]]) -> dict[str, bool]:
    """Evaluate correctness and continuity using v4 §1.1 and §1.4.

    Unknown row IDs or any row/triple mismatch raise ValueError. For TR-06/07,
    ``continuity_eligible`` is false by definition, while ``transition_passes``
    reports their non-P1 predicate.
    """
    if row_id not in TRANSITION_ROWS:
        raise ValueError(f"unlisted transition row: {row_id}")
    row = TRANSITION_ROWS[row_id]
    triple = (child_record.get("event_type"), child_record.get("child_role"), child_record.get("origin"))
    if triple != (row.event_type, row.child_role, row.origin):
        raise ValueError(f"unlisted or mismatched transition tuple: {triple}")
    prior_id = phase2_record.get("prior_position_id")
    if row.prior_position_id == "forbidden" and prior_id is not None:
        return {"decision_correct": False, "continuity_eligible": False, "transition_passes": False}
    expected = child_record["expected_disposition"] if row.required_decision == "emitted" else row.required_decision
    decision_correct = phase2_record.get("decision") == expected
    if not row.continuity:
        passes = decision_correct
        if row_id == "TR-06":
            passes = passes and phase2_record.get("rule_id") == child_record.get("expected_rule_id")
            passes = passes and phase2_record.get("clause_id") == child_record.get("expected_clause_id")
        return {"decision_correct": decision_correct, "continuity_eligible": False,
                "transition_passes": passes}
    if not prior_id or prior_id not in phase1_lookup:
        return {"decision_correct": decision_correct, "continuity_eligible": False,
                "transition_passes": False}
    p1, star = phase1_lookup[prior_id], child_record.get("plant_position", {})
    exact = (
        p1.get("source_deviation_id") == star.get("source_deviation_id")
        and p1.get("decision") == star.get("phase1_decision")
        and p1.get("rule_id") == star.get("rule_id")
        and p1.get("clause_id") == star.get("clause_id")
        and p1.get("comparator_record_id") == star.get("comparator_record_id")
    )
    common = exact and p1.get("decision") == "reject"
    common = common and phase2_record.get("rule_id") == star.get("rule_id") == child_record.get("expected_rule_id")
    common = common and star.get("clause_id") == child_record.get("source_clause_id")
    if row_id == "TR-03":
        common = common and child_record.get("expected_clause_id") == child_record.get("source_clause_id")
    elif row_id == "TR-04":
        common = common and star.get("clause_id") != child_record.get("expected_clause_id")
        common = common and phase2_record.get("clause_id") == child_record.get("expected_clause_id")
    else:
        common = common and phase2_record.get("clause_id") == child_record.get("expected_clause_id")
    if row_id == "TR-01":
        common = common and bool(child_record.get("is_labeled_concession"))
    if row_id == "TR-05":
        common = common and p1.get("comparator_record_id") == child_record.get("counter_guard_id")
    return {"decision_correct": decision_correct, "continuity_eligible": bool(common),
            "transition_passes": bool(common and decision_correct)}


def counter_judgment(children: Sequence[Mapping[str, Any]]) -> float:
    """Ordinary accuracy over counter children actually present (v4 §1.2)."""
    counters = [c for c in children if c.get("event_type") == "counter_proposal"]
    if not counters:
        raise ValueError("invalid mixed fixture: |K| must be at least 1")
    return sum(c.get("decision") == c.get("expected_disposition") for c in counters) / len(counters)


def validate_counter_family(record: Mapping[str, Any]) -> list[str]:
    """Pure family-authoring checks computable before generation (v4 §1.7).

    Render-time independence, counterfactual twins, qualitative/arithmetic
    playbook quotas, and held-out attacker accuracy need generated populations;
    callers provide their declared pre-generation evidence here.
    """
    errors = []
    counter_slots = record.get("counter_text_slots", {})
    context_slots = record.get("phase1_context_slots", {})
    if len(counter_slots) < 1: errors.append("requires at least one decisive counter-text slot")
    if len(context_slots) < 1: errors.append("requires at least one independently varied phase-1 context/reservation slot")
    if len(record.get("decoy_values", [])) < 2: errors.append("requires at least two same-surface-type decoys")
    decisive = [*counter_slots, *context_slots]
    grounding = record.get("playbook_grounding", {})
    grounding_text = " ".join([
        str(grounding.get("position", "")),
        str(grounding.get("fallback", "")),
        str(grounding.get("escalation_trigger", "")),
        json.dumps(grounding.get("deterministic_checks", {}), sort_keys=True),
    ]).lower()
    decisive_tokens = {
        token.lower()
        for slot in decisive
        for token in str(slot).split("_")
        if len(token) >= 4
    }
    if not any(token in grounding_text for token in decisive_tokens):
        errors.append("no decisive slot name is grounded in playbook_grounding text")
    forms = record.get("render_forms", {})
    for slot in decisive:
        if len(forms.get(slot, [])) < 3: errors.append(f"decisive input {slot} requires at least three render forms")
    twins = record.get("counterfactual_twins", [])
    tested = {t.get("varied_input") for t in twins}
    for slot in [*decisive, *record.get("decoy_ids", [])]:
        if slot not in tested: errors.append(f"missing counterfactual twin for {slot}")
    for twin in twins:
        is_decisive = twin.get("varied_input") in decisive
        if bool(twin.get("label_flipped")) != is_decisive:
            errors.append(f"counterfactual twin {twin.get('varied_input')} flips contrary to signed truth table")

    # family_design_v2 §§2-3: v4's formula-level declarations are tightened by
    # checks over the complete authored render population.  No frozen reward
    # arithmetic, transition row, weight, floor, or existing check changes.
    pools = record.get("render_pools")
    if not isinstance(pools, Mapping):
        errors.append("requires authored render_pools for acceptable and unacceptable classes")
        return errors
    realized: dict[str, list[Mapping[str, Any]]] = {}
    for label in ("acceptable", "unacceptable"):
        pool = pools.get(label)
        if not isinstance(pool, list) or len(pool) < 4:
            errors.append(f"{label} render pool requires at least four realized renders")
            realized[label] = []
            continue
        realized[label] = [render for render in pool if isinstance(render, Mapping)]
        if len(realized[label]) != len(pool):
            errors.append(f"{label} render pool contains a non-object render")

    expected_counter = set(counter_slots)
    expected_context = set(context_slots)
    decoy_ids = list(record.get("decoy_ids", []))
    for label, pool in realized.items():
        for index, render in enumerate(pool):
            prefix = f"{label} render {index}"
            if not str(render.get("text", "")).strip():
                errors.append(f"{prefix} requires nonempty fully realized text")
            rendered_counter = render.get("counter_text_slots")
            rendered_context = render.get("phase1_context_slots")
            rendered_decoys = render.get("decoy_values")
            if not isinstance(rendered_counter, Mapping) or set(rendered_counter) != expected_counter:
                errors.append(f"{prefix} counter slot set differs from family declaration")
            if not isinstance(rendered_context, Mapping) or set(rendered_context) != expected_context:
                errors.append(f"{prefix} context slot set differs from family declaration")
            if not isinstance(rendered_decoys, list) or len(rendered_decoys) != len(decoy_ids):
                errors.append(f"{prefix} decoy count differs from declared decoy IDs")
            if (isinstance(rendered_counter, Mapping)
                    and isinstance(rendered_context, Mapping)
                    and isinstance(rendered_decoys, list)):
                decisive_numeric = [
                    (slot, value)
                    for slots in (rendered_counter, rendered_context)
                    for slot, value in slots.items()
                    if isinstance(value, (int, float)) and not isinstance(value, bool)
                ]
                for value in rendered_decoys:
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        for slot, decisive_value in decisive_numeric:
                            if value == decisive_value:
                                errors.append(
                                    f"{prefix} decoy value {value} collides with decisive "
                                    f"slot {slot} in the same render"
                                )
    if all(realized.values()):
        def slot_values(label: str, source: str, slot: str | int) -> list[Any]:
            values = []
            for render in realized[label]:
                container = render[source]
                values.append(container[slot] if isinstance(slot, str) else container[slot])
            return values

        def check_overlap(name: str, acceptable_values: list[Any],
                          unacceptable_values: list[Any]) -> None:
            numeric = all(
                isinstance(value, (int, float)) and not isinstance(value, bool)
                for value in [*acceptable_values, *unacceptable_values]
            )
            if numeric:
                overlaps = (
                    min(acceptable_values) <= max(unacceptable_values)
                    and min(unacceptable_values) <= max(acceptable_values)
                )
            else:
                try:
                    overlaps = bool(set(acceptable_values) & set(unacceptable_values))
                except TypeError:
                    overlaps = bool(
                        {json.dumps(value, sort_keys=True) for value in acceptable_values}
                        & {json.dumps(value, sort_keys=True) for value in unacceptable_values}
                    )
            if not overlaps:
                surface = "ranges" if numeric else "value sets"
                errors.append(
                    f"{name} acceptable/unacceptable {surface} do not overlap (single-slot separable)"
                )

        for source, slots in (("counter_text_slots", sorted(expected_counter)),
                              ("phase1_context_slots", sorted(expected_context))):
            for slot in slots:
                check_overlap(
                    f"slot {slot}",
                    slot_values("acceptable", source, slot),
                    slot_values("unacceptable", source, slot),
                )
        for index, decoy_id in enumerate(decoy_ids):
            check_overlap(
                f"decoy {decoy_id}",
                slot_values("acceptable", "decoy_values", index),
                slot_values("unacceptable", "decoy_values", index),
            )
    if not str(record.get("expected_redline_text", "")).strip():
        errors.append("requires one nonempty expected_redline_text valid for every unacceptable render")
    return errors


def validate_family_pool_diversity(
    families: Sequence[Mapping[str, Any]],
) -> list[str]:
    """Reject reused decisive predicate descriptions across an authored corpus."""
    expressions: dict[str, list[str]] = {}
    for index, record in enumerate(families):
        expression = re.sub(
            r"\s+", " ", str(record.get("predicate", {}).get("expression", ""))
        ).strip().lower()
        family_id = str(record.get("counter_family_id", f"family[{index}]"))
        expressions.setdefault(expression, []).append(family_id)
    errors = []
    for expression, family_ids in sorted(expressions.items()):
        if len(family_ids) > 1:
            errors.append(
                f"predicate expression {expression!r} is duplicated by families "
                + ", ".join(family_ids)
            )
    return errors


def _abstention(planted: set[str], submitted: set[str]) -> float:
    if not planted:
        return 1.0 if not submitted else 0.0
    if not submitted:
        return 0.0
    tp = len(planted & submitted)
    precision, recall = tp / len(submitted), tp / len(planted)
    return 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)


def compute_composite(event_map: Sequence[Mapping[str, Any]], phase1_score: float,
                      *, conformance: bool = True,
                      planted_missing_ids: Sequence[str] = (),
                      submitted_missing_ids: Sequence[str] = ()) -> dict[str, Any]:
    """Compute one mixed episode end-to-end under v4 §§1.2-1.3.

    A fixture violating mandatory mixed denominators raises ValueError. Missing
    phase-2 records are represented by absent/None ``decision`` fields and are
    scored incorrect; an entirely absent list is a valid attempted episode and
    returns zero channels rather than being mistaken for a fixture.
    """
    if not event_map:
        channels = {name: (1.0 if name == "A" and not planted_missing_ids and not submitted_missing_ids else 0.0)
                    for name in CHANNEL_WEIGHTS}
        channels["F"] = float(conformance)
        return _compose(channels, phase1_score, {})
    children = list(event_map)
    harmful = [c for c in children if c.get("expected_disposition") == "reject"]
    benign = [c for c in children if c.get("expected_disposition") == "accept"]
    prior = [c for c in children if c.get("origin") == "prior_position"]
    counters = [c for c in children if c.get("event_type") == "counter_proposal"]
    if not harmful or not benign or not counters or len(prior) < 6:
        raise ValueError("invalid mixed fixture: requires |H|>0, |B|>0, |K|>=1, and |P|>=6")
    rejected = [c for c in children if c.get("decision") == "reject"]
    correct_rejects = [c for c in harmful if c.get("decision") == "reject"]
    edit_set = [c for c in correct_rejects if c.get("edit_required")]
    channels = {
        "S": len(correct_rejects) / len(harmful),
        "T": sum(c.get("decision") == "accept" for c in benign) / len(benign),
        "J": counter_judgment(children),
        "Q": (sum(c in harmful for c in rejected) / len(rejected)) if rejected else 0.0,
        "L": sum(bool(c.get("continuity_eligible") and c.get("transition_passes")) for c in prior) / len(prior),
        "G": (sum(c in harmful and c.get("grounding_exact") is True for c in rejected) / len(rejected)) if rejected else 0.0,
        "D": (sum(float(c.get("redline_tier", 0.0)) for c in edit_set) / len(edit_set)) if edit_set else 0.0,
        "F": float(conformance),
        "A": _abstention(set(planted_missing_ids), set(submitted_missing_ids)),
    }
    family_children: dict[str, list[Mapping[str, Any]]] = {}
    for child in children:
        family = child.get("harm_family")
        if family:
            family_children.setdefault(str(family), []).append(child)
    required = list(REQUIRED_FAMILIES)
    if any(c.get("counter_class") == "unacceptable" for c in counters):
        required.append("unacceptable_counter")
    family_ok = {f: bool(family_children.get(f)) and all(c.get("decision") == "reject" for c in family_children.get(f, []))
                 for f in required}
    return _compose(channels, phase1_score, family_ok)


def _compose(channels: Mapping[str, float], phase1_score: float,
             family_ok: Mapping[str, bool]) -> dict[str, Any]:
    w2 = sum(CHANNEL_WEIGHTS[k] * channels[k] for k in CHANNEL_WEIGHTS)
    floor_results = {k: channels[k] >= threshold for k, threshold in ORDINARY_FLOORS.items()}
    p2 = w2 if all(floor_results.values()) else 0.0
    e0 = sqrt(phase1_score * p2) if phase1_score >= .40 and p2 >= .40 else 0.0
    harm_integrity = bool(family_ok) and all(family_ok.values())
    e = e0 if harm_integrity else min(e0, .20)
    return {"composite": e, "E": e, "reported_E": min(e, .80), "E0": e0,
            "W2": w2, "P2": p2, "P1": phase1_score, "channels": dict(channels),
            "weights": CHANNEL_WEIGHTS.copy(), "floor_results": floor_results,
            "floor_pass": all(floor_results.values()), "family_ok": dict(family_ok),
            "harm_integrity": harm_integrity, "contract_id": CONTRACT_ID}


def tranche_counter_metrics(episodes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Compute RA, RU, and Jmacro; both class denominators require 28 (v4 §1.6)."""
    counters = [c for e in episodes for c in e.get("children", []) if c.get("event_type") == "counter_proposal"]
    acceptable = [c for c in counters if c.get("counter_class") == "acceptable"]
    unacceptable = [c for c in counters if c.get("counter_class") == "unacceptable"]
    if len(acceptable) < 28 or len(unacceptable) < 28:
        return {"status": "INSUFFICIENT_DATA", "acceptable_n": len(acceptable), "unacceptable_n": len(unacceptable)}
    ra = sum(c.get("decision") == "accept" for c in acceptable) / len(acceptable)
    ru = sum(c.get("decision") == "reject" for c in unacceptable) / len(unacceptable)
    return {"status": "EVALUATED", "RA": ra, "RU": ru, "Jmacro": min(ra, ru),
            "acceptable_n": len(acceptable), "unacceptable_n": len(unacceptable)}


def gated_tranche_composite(episode_results: Sequence[Mapping[str, Any]],
                            counter_metrics: Mapping[str, Any]) -> dict[str, Any]:
    """Apply v4 §1.6 counter gate to mean raw E (never reported_E)."""
    if counter_metrics.get("status") != "EVALUATED":
        return {"status": "INSUFFICIENT_DATA", "composite": None}
    mean_e = sum(float(r["E"]) for r in episode_results) / len(episode_results) if episode_results else 0.0
    return {"status": "EVALUATED", "composite": mean_e if counter_metrics["Jmacro"] >= .70 else 0.0,
            "mean_E": mean_e, "counter_gate_pass": counter_metrics["Jmacro"] >= .70}


def score_all_concessions(*, complete_read_coverage: bool, explicit_accept_all: bool,
                          interactive_card_equal: bool, valid_prior_links: bool,
                          restraint: float, continuity: float, conformance: float,
                          abstention: float) -> dict[str, Any]:
    """Structural gate then .55/.20/.15/.10 score (v4 §1.8; v3 §8)."""
    gate = all((complete_read_coverage, explicit_accept_all, interactive_card_equal, valid_prior_links))
    score = (.55 * restraint + .20 * continuity + .15 * conformance + .10 * abstention) if gate else 0.0
    return {"score": score, "gate_pass": gate}


def all_concessions_share_compliant(mixed_count: int, all_concessions_count: int) -> bool:
    """Integer v4 §1.8 cap: 9*A_c<=M.

    Boundaries: M=14 permits 1; M=18 permits 2 exactly; M=35 permits 3,
    never 4. Never round a percentage upward.
    """
    if mixed_count < 0 or all_concessions_count < 0:
        raise ValueError("counts must be non-negative integers")
    return 9 * all_concessions_count <= mixed_count
