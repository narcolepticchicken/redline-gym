from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scoring.t2n_contract import CONTRACT_ID


ROOT = Path(__file__).resolve().parents[1]


def validator(name):
    return Draft202012Validator(json.loads((ROOT / "schema/t2n" / f"{name}.schema.json").read_text()))


def action(origin="prior_position", decision="reject"):
    result = {"action": "review_change", "change_id": "CH-001", "origin": origin, "decision": decision}
    if origin == "prior_position": result["prior_position_id"] = "POS-001"
    if decision == "reject": result.update(rule_id="R-001", exact_quote="changed text")
    return result


def patch(origin="prior_position"):
    before = b"a"
    result = {"change_id": "CH-001", "event_id": "EV-001", "event_type": "regression",
              "child_role": "sole", "origin": origin, "op": "replace",
              "precondition_sha256": hashlib.sha256(before).hexdigest(), "doc_id": "DOC-01",
              "section_ref": "1", "start_offset": 0, "end_offset": 1, "before_text": "a", "after_text": "b",
              "expected_disposition": "reject", "expected_rule_id": "R-001", "expected_clause_id": "C1",
              "source_clause_id": "C1", "ground_span": "b", "edit_required": True,
              "expected_redline_text": "c", "transition_row_id": "TR-02"}
    if origin == "prior_position":
        result["prior_source_deviation_id"] = "D-001"
        result["plant_position"] = {"source_deviation_id": "D-001", "phase1_decision": "reject",
            "rule_id": "R-001", "clause_id": "C1", "fallback_text": "fallback"}
    return result


def turn_events(total=8):
    events = []
    specs = [("concession", "accept"), ("regression", "reject"),
             ("sneaky_reinsert", "accept"), ("counter_proposal", "accept"),
             ("counter_proposal", "reject"), ("new_deviation", "reject"),
             ("benign_canary_change", "accept")]
    for i, (kind, disposition) in enumerate(specs):
        role = "source_cleanup" if kind == "sneaky_reinsert" else "sole"
        origin = "novel_insertion" if kind == "new_deviation" else "canary_probe" if kind == "benign_canary_change" else "prior_position"
        children = [{"change_id": f"CH-{i}A", "child_role": role, "origin": origin,
                     "expected_disposition": disposition, "rule_id": "R-001"}]
        if kind == "sneaky_reinsert":
            children.append({"change_id": f"CH-{i}B", "child_role": "inserted_effect", "origin": "prior_position",
                             "expected_disposition": "reject", "rule_id": "R-001"})
        event = {"event_id": f"EV-{i}", "event_type": kind, "children": children}
        if kind == "counter_proposal":
            event["counter_inputs"] = {"counter_family_id": f"CF-{i}", "counter_class": "acceptable" if disposition == "accept" else "unacceptable",
                "counter_text_slots": {"days": 30}, "phase1_context_slots": {"urgent": False}, "decoy_values": [10, 20]}
        events.append(event)
    return {"expected_child_counts": {"total": total, "harmful": 4, "benign": 4, "prior": 6, "novel": 1, "canary": 1}, "events": events}


def assert_valid(name, instance):
    assert list(validator(name).iter_errors(instance)) == []


def assert_invalid(name, instance):
    assert list(validator(name).iter_errors(instance))


def test_review_action_schema_origin_conditionals_and_strictness():
    assert_valid("review_action", action())
    bad = action(); bad.pop("prior_position_id"); assert_invalid("review_action", bad)
    bad = action("novel_insertion", "accept"); bad["prior_position_id"] = "POS-001"; assert_invalid("review_action", bad)
    bad = action(); bad["extra"] = True; assert_invalid("review_action", bad)
    bad = action(); bad["decision"] = "maybe"; assert_invalid("review_action", bad)


def test_patch_ledger_schema_origin_ops_counter_and_strictness():
    assert_valid("patch_ledger", {"contract_id": CONTRACT_ID, "patches": [patch()]})
    bad = patch(); bad.pop("plant_position"); assert_invalid("patch_ledger", {"contract_id": CONTRACT_ID, "patches": [bad]})
    bad = patch(); bad["op"] = "move"; assert_invalid("patch_ledger", {"contract_id": CONTRACT_ID, "patches": [bad]})
    bad = patch(); bad["extra"] = 1; assert_invalid("patch_ledger", {"contract_id": CONTRACT_ID, "patches": [bad]})
    bad = patch(); bad.update(event_type="counter_proposal", transition_row_id="TR-05"); assert_invalid("patch_ledger", {"contract_id": CONTRACT_ID, "patches": [bad]})


def test_turn_events_schema_valid_counter_inputs_minimum_and_c7_rejection():
    assert_valid("turn_events", turn_events())
    assert_invalid("turn_events", turn_events(7))
    bad = turn_events(); bad["events"][3]["counter_inputs"]["decoy_values"] = [1]; assert_invalid("turn_events", bad)
    bad = turn_events(); bad["events"][0]["extra"] = 1; assert_invalid("turn_events", bad)
    bad = turn_events(); bad["events"][0]["event_type"] = "unknown"; assert_invalid("turn_events", bad)


def test_card_schema_valid_and_major_failures():
    card = {"changes": [action()], "escalations": [], "summary": "Reviewed."}
    assert_valid("card_t2n", card)
    bad = copy.deepcopy(card); bad["changes"][0].pop("prior_position_id"); assert_invalid("card_t2n", bad)
    bad = copy.deepcopy(card); bad["changes"][0]["extra"] = True; assert_invalid("card_t2n", bad)
    bad = copy.deepcopy(card); bad["changes"][0]["decision"] = "flag"; assert_invalid("card_t2n", bad)
