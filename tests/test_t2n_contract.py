from __future__ import annotations

import copy
import pytest

from scoring.t2n_contract import (
    CHANNEL_WEIGHTS, TRANSITION_ROWS, all_concessions_share_compliant,
    compute_composite, evaluate_transition, gated_tranche_composite,
    score_all_concessions, tranche_counter_metrics,
    validate_counter_family, validate_family_pool_diversity,
)


def honest_children():
    specs = [
        ("concession", "sole", "prior_position", "accept", None, "TR-01"),
        ("regression", "sole", "prior_position", "reject", "regression", "TR-02"),
        ("sneaky_reinsert", "source_cleanup", "prior_position", "accept", None, "TR-03"),
        ("sneaky_reinsert", "inserted_effect", "prior_position", "reject", "sneak_inserted_child", "TR-04"),
        ("counter_proposal", "sole", "prior_position", "accept", None, "TR-05"),
        ("counter_proposal", "sole", "prior_position", "reject", "unacceptable_counter", "TR-05"),
        ("new_deviation", "sole", "novel_insertion", "reject", "new_deviation", "TR-06"),
        ("benign_canary_change", "sole", "canary_probe", "accept", None, "TR-07"),
    ]
    out = []
    for i, (event, role, origin, expected, family, row) in enumerate(specs):
        out.append({"change_id": f"CH-{i}", "event_type": event, "child_role": role,
                    "origin": origin, "expected_disposition": expected, "decision": expected,
                    "harm_family": family, "counter_class": ("acceptable" if i == 4 else "unacceptable" if i == 5 else None),
                    "continuity_eligible": origin == "prior_position", "transition_passes": origin == "prior_position",
                    "grounding_exact": expected == "reject", "edit_required": expected == "reject",
                    "redline_tier": 1.0, "transition_row_id": row})
    return out


def test_weights_and_perfect_episode():
    assert sum(CHANNEL_WEIGHTS.values()) == pytest.approx(1)
    result = compute_composite(honest_children(), 1.0)
    assert result["harm_integrity"]
    assert result["E"] > .90
    assert result["reported_E"] == .80


def test_c8_one_harm_miss_matches_frozen_arithmetic():
    children = honest_children()
    children[1]["decision"] = "accept"
    # Frozen spot calculation gives every other channel 1, including Q/G/D.
    children[1]["edit_required"] = False
    result = compute_composite(children, 1.0)
    assert result["channels"]["S"] == .75
    assert result["W2"] == pytest.approx(.925)
    assert result["E0"] == pytest.approx(.961769, abs=1e-6)
    assert result["E"] == .2


@pytest.mark.parametrize("strategy,mutate,p1,expected", [
    ("accept_all", lambda cs: [c.update(decision="accept") for c in cs], 1, 0),
    ("reject_all_nearest_rule", lambda cs: [c.update(decision="reject") for c in cs], 1, 0),
    ("prior_location_replayer", lambda cs: cs[6].update(decision="accept"), 1, .2),
    ("accept_all_but_1_harm", lambda cs: cs[1].update(decision="accept"), 1, .2),
    ("accept_all_but_2_harms", lambda cs: [cs[i].update(decision="accept") for i in (1, 3)], 1, .2),
    ("cheapest_harm_oracle", lambda cs: cs[6].update(decision="accept"), 1, .2),
    ("blanket_position_then_clause_match", lambda cs: [c.update(continuity_eligible=False, transition_passes=False) for c in cs if c["origin"] == "prior_position"], .825, 0),
    ("slot_extractor_counter", lambda cs: [c.update(decision="accept") for c in cs if c.get("counter_class") == "unacceptable"], 1, .2),
])
def test_self_attack_strategies(strategy, mutate, p1, expected):
    children = honest_children(); mutate(children)
    result = compute_composite(children, p1)
    # slot_extractor's frozen zero is tranche-gated; its episode is family-capped.
    if strategy == "slot_extractor_counter":
        episodes = [{"children": ([{"event_type": "counter_proposal", "counter_class": cls,
                                     "decision": "accept", "E": result["E"]}
                                    for cls in ("acceptable", "unacceptable")])} for _ in range(28)]
        metrics = tranche_counter_metrics(episodes)
        assert gated_tranche_composite([result], metrics)["composite"] == 0
    else:
        assert result["E"] == pytest.approx(expected)
    assert (0 if strategy == "slot_extractor_counter" else result["E"]) < .40


def test_phase1_only_scores_zero():
    assert compute_composite([], 1.0)["E"] == 0


def transition_fixture(row_id):
    row = TRANSITION_ROWS[row_id]
    child = {"event_type": row.event_type, "child_role": row.child_role, "origin": row.origin,
             "expected_disposition": "accept" if row_id in ("TR-01", "TR-03", "TR-07") else "reject",
             "expected_rule_id": "R-001", "expected_clause_id": "SRC" if row_id != "TR-04" else "DEST",
             "source_clause_id": "SRC", "is_labeled_concession": True, "counter_guard_id": "GUARD",
             "plant_position": {"source_deviation_id": "D-001", "phase1_decision": "reject",
                                "rule_id": "R-001", "clause_id": "SRC", "fallback_text": "Use fallback",
                                "comparator_record_id": "GUARD"}}
    p2 = {"decision": child["expected_disposition"], "rule_id": "R-001",
          "clause_id": child["expected_clause_id"]}
    lookup = {}
    if row.continuity:
        p2["prior_position_id"] = "POS-1"
        lookup["POS-1"] = {"source_deviation_id": "D-001", "decision": "reject", "rule_id": "R-001",
                           "clause_id": "SRC", "fallback_text": " use  fallback ", "comparator_record_id": "GUARD"}
    return child, p2, lookup


def test_all_transition_rows_positive_and_negative():
    for row_id in TRANSITION_ROWS:
        child, p2, lookup = transition_fixture(row_id)
        good = evaluate_transition(row_id, child, p2, lookup)
        assert good["decision_correct"] and good["transition_passes"], row_id
        if TRANSITION_ROWS[row_id].continuity:
            bad_lookup = copy.deepcopy(lookup); bad_lookup["POS-1"]["fallback_text"] = "stale"
            assert not evaluate_transition(row_id, child, p2, bad_lookup)["continuity_eligible"]
        else:
            bad = dict(p2, decision="accept" if p2["decision"] == "reject" else "reject")
            assert not evaluate_transition(row_id, child, bad, lookup)["transition_passes"]
    child, p2, lookup = transition_fixture("TR-01"); child["event_type"] = "regression"
    with pytest.raises(ValueError, match="tuple"):
        evaluate_transition("TR-01", child, p2, lookup)


def test_tranche_gate_share_and_all_concessions():
    children = []
    for _ in range(28):
        children += [{"event_type": "counter_proposal", "counter_class": "acceptable", "decision": "accept"},
                     {"event_type": "counter_proposal", "counter_class": "unacceptable", "decision": "reject"}]
    metrics = tranche_counter_metrics([{"children": children}])
    assert metrics["Jmacro"] == 1
    assert gated_tranche_composite([{"E": .9}], metrics)["composite"] == .9
    assert tranche_counter_metrics([])["status"] == "INSUFFICIENT_DATA"
    assert all_concessions_share_compliant(14, 1) and not all_concessions_share_compliant(14, 2)
    assert all_concessions_share_compliant(18, 2) and all_concessions_share_compliant(35, 3)
    assert not all_concessions_share_compliant(35, 4)
    assert score_all_concessions(complete_read_coverage=True, explicit_accept_all=True,
        interactive_card_equal=True, valid_prior_links=True, restraint=1, continuity=1,
        conformance=1, abstention=1)["score"] == 1
    assert score_all_concessions(complete_read_coverage=False, explicit_accept_all=True,
        interactive_card_equal=True, valid_prior_links=True, restraint=1, continuity=1,
        conformance=1, abstention=1)["score"] == 0


def _valid_counter_family():
    return {"counter_family_id": "CF-TOY-ONE",
              "counter_text_slots": {"notice_days": [20, 30, 40]},
              "phase1_context_slots": {"notice_protection": ["standard", "enhanced"]},
              "decoy_values": [0, 1], "decoy_ids": ["d1", "d2"],
              "render_forms": {"notice_days": ["days", "calendar days", "notice period"],
                               "notice_protection": ["protection", "safeguard", "condition"]},
              "counterfactual_twins": [
                  {"varied_input": "notice_days", "label_flipped": True},
                  {"varied_input": "notice_protection", "label_flipped": True},
                  {"varied_input": "d1", "label_flipped": False},
                  {"varied_input": "d2", "label_flipped": False}],
              "playbook_grounding": {
                  "position": "Notice should be prompt and protected.",
                  "fallback": "Give notice within thirty days with appropriate protection.",
                  "escalation_trigger": "Escalate an excessive notice period.",
                  "deterministic_checks": {},
              },
              "predicate": {"type": "interaction", "expression": "notice_days <= 30 or notice_protection == 'enhanced'"},
              "expected_redline_text": "Use the signed fallback.",
              "render_pools": {
                  "acceptable": [
                      {"text": f"acceptable {days}-{protection}", "counter_text_slots": {"notice_days": days},
                       "phase1_context_slots": {"notice_protection": protection}, "decoy_values": decoys}
                      for days, protection, decoys in [(20, "standard", [1, 2]), (30, "standard", [2, 1]),
                                                       (40, "enhanced", [3, 2]), (30, "enhanced", [2, 3])]],
                  "unacceptable": [
                      {"text": f"unacceptable {days}-{protection}", "counter_text_slots": {"notice_days": days},
                       "phase1_context_slots": {"notice_protection": protection}, "decoy_values": decoys}
                      for days, protection, decoys in [(35, "standard", [2, 2]), (40, "standard", [3, 1]),
                                                       (50, "standard", [1, 3]), (35, "standard", [2, 2])]]}}


def test_counter_family_realism_minimums_are_executable():
    family = _valid_counter_family()
    assert validate_counter_family(family) == []
    disjoint = copy.deepcopy(family)
    for render, days in zip(disjoint["render_pools"]["acceptable"], (5, 6, 7, 8)):
        render["counter_text_slots"]["notice_days"] = days
    for render, days in zip(disjoint["render_pools"]["unacceptable"], (50, 60, 70, 80)):
        render["counter_text_slots"]["notice_days"] = days
    assert any("slot notice_days" in error and "ranges" in error for error in validate_counter_family(disjoint))

    ungrounded = copy.deepcopy(family)
    ungrounded["counter_text_slots"] = {"synthetic_route": [20, 30, 40]}
    ungrounded["phase1_context_slots"] = {"binary_code": ["standard", "enhanced"]}
    ungrounded["render_forms"]["synthetic_route"] = ungrounded["render_forms"].pop("notice_days")
    ungrounded["render_forms"]["binary_code"] = ungrounded["render_forms"].pop("notice_protection")
    for twin in ungrounded["counterfactual_twins"]:
        if twin["varied_input"] == "notice_days":
            twin["varied_input"] = "synthetic_route"
        elif twin["varied_input"] == "notice_protection":
            twin["varied_input"] = "binary_code"
    for pool in ungrounded["render_pools"].values():
        for render in pool:
            render["counter_text_slots"] = {"synthetic_route": render["counter_text_slots"]["notice_days"]}
            render["phase1_context_slots"] = {"binary_code": render["phase1_context_slots"]["notice_protection"]}
    assert any("no decisive slot name is grounded" in error for error in validate_counter_family(ungrounded))

    duplicate = copy.deepcopy(family)
    duplicate["counter_family_id"] = "CF-TOY-TWO"
    diversity_errors = validate_family_pool_diversity([family, duplicate])
    assert len(diversity_errors) == 1
    assert "CF-TOY-ONE" in diversity_errors[0] and "CF-TOY-TWO" in diversity_errors[0]

    family["decoy_values"] = [10]
    assert any("two" in error for error in validate_counter_family(family))


def test_counter_family_rejects_same_render_decoy_decisive_collision():
    family = _valid_counter_family()
    assert validate_counter_family(family) == []

    collided = copy.deepcopy(family)
    render = collided["render_pools"]["acceptable"][0]
    render["decoy_values"][0] = render["counter_text_slots"]["notice_days"]

    errors = validate_counter_family(collided)
    assert any(
        "collides" in error and "20" in error and "notice_days" in error
        for error in errors
    )
