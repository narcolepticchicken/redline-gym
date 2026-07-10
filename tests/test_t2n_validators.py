from __future__ import annotations

import copy
import hashlib

import pytest

from validators.t2n_checks import (
    v10_t2n_forbidden_fields, v10_t2n_fresh_process_isolation,
    v10_t2n_lookup_classifiers, v10_t2n_permutation_mi,
    v10_t2n_quota_batch_attacker, v14_t2n_ledger,
    v9_ext_t2n_canary_turn_events,
)


def fixture():
    canonical = b"abcdefgh"
    specs = [
        ("concession", "sole", "prior_position", "accept", "TR-01"),
        ("regression", "sole", "prior_position", "reject", "TR-02"),
        ("sneaky_reinsert", "source_cleanup", "prior_position", "accept", "TR-03"),
        ("sneaky_reinsert", "inserted_effect", "prior_position", "reject", "TR-04"),
        ("counter_proposal", "sole", "prior_position", "accept", "TR-05"),
        ("counter_proposal", "sole", "prior_position", "reject", "TR-05"),
        ("new_deviation", "sole", "novel_insertion", "reject", "TR-06"),
        ("benign_canary_change", "sole", "canary_probe", "accept", "TR-07"),
    ]
    patches, events, reviews = [], [], {}
    for i, (kind, role, origin, disposition, row) in enumerate(specs):
        before = canonical[i:i+1]; after = before.upper(); cid = f"CH-{i}"; eid = "EV-SNEAK" if i in (2, 3) else f"EV-{i}"
        p = {"change_id": cid, "event_id": eid, "event_type": kind, "child_role": role,
             "origin": origin, "op": "replace", "precondition_sha256": hashlib.sha256(before).hexdigest(),
             "start_offset": i, "end_offset": i + 1, "before_text": before.decode(), "after_text": after.decode(),
             "expected_disposition": disposition, "transition_row_id": row}
        patches.append(p)
        child = {"change_id": cid, "child_role": role, "origin": origin,
                 "expected_disposition": disposition, "rule_id": "R-001"}
        if i == 3:
            events[-1]["children"].append(child)
        else:
            events.append({"event_id": eid, "event_type": kind, "children": [child]})
        review = {"action": "review_change", "change_id": cid, "origin": origin, "decision": disposition}
        if origin == "prior_position": review["prior_position_id"] = f"POS-{i}"
        reviews[cid] = review
    turn = {"expected_child_counts": {"total": 8, "harmful": 4, "benign": 4, "prior": 6, "novel": 1, "canary": 1}, "events": events}
    return canonical, canonical.upper(), {"patches": patches}, turn, reviews


def run_v14(data):
    canonical, phase2, ledger, events, reviews = data
    return v14_t2n_ledger(canonical_document=canonical, phase2_document=phase2, ledger=ledger,
        turn_events=events, rendered_change_ids=[p["change_id"] for p in ledger["patches"]],
        reviews_by_change_id=reviews, card_changes=list(reviews.values()))


def test_v14_replay_positive_and_tamper_detection():
    assert run_v14(fixture()).status == "PASS"
    bad = fixture(); bad[2]["patches"][3]["after_text"] = "X"
    result = run_v14(bad)
    assert result.status == "FAIL" and "byte" in result.detail


def test_v14_overlap_origin_link_transition_and_card_checks():
    bad = fixture(); bad[2]["patches"][1]["start_offset"] = 0
    assert "overlap" in run_v14(bad).detail
    bad = fixture(); bad[4]["CH-0"].pop("prior_position_id")
    assert "requires prior_position_id" in run_v14(bad).detail
    bad = fixture(); bad[2]["patches"][0]["child_role"] = "inserted_effect"
    assert "unlisted transition tuple" in run_v14(bad).detail
    bad = fixture(); card = list(copy.deepcopy(bad[4]).values()); card[0]["decision"] = "reject"
    result = v14_t2n_ledger(canonical_document=bad[0], phase2_document=bad[1], ledger=bad[2],
        turn_events=bad[3], rendered_change_ids=[p["change_id"] for p in bad[2]["patches"]],
        reviews_by_change_id=bad[4], card_changes=card)
    assert "not exactly equal" in result.detail


def test_v14_seven_child_invalidity_has_frozen_reason():
    bad = fixture()
    bad[2]["patches"].pop()
    bad[3]["events"].pop()
    bad[3]["expected_child_counts"].update(total=7, benign=3, canary=0)
    bad[4].pop("CH-7")
    result = v14_t2n_ledger(canonical_document=bad[0], phase2_document=b"ABCDEFGh", ledger=bad[2],
        turn_events=bad[3], rendered_change_ids=[p["change_id"] for p in bad[2]["patches"]], reviews_by_change_id=bad[4])
    assert result.status == "FAIL"
    assert "would require only four of five seeded deviations" in result.detail


def test_v9_extension_canary_rules_and_exactly_once():
    _, _, _, events, _ = fixture()
    assert v9_ext_t2n_canary_turn_events(events, {"R-001"}).status == "FAIL"  # harmful children use R-001
    for event in events["events"]:
        for child in event["children"]:
            child["rule_id"] = "R-999" if event["event_type"] == "benign_canary_change" else "R-001"
    assert v9_ext_t2n_canary_turn_events(events, {"R-999"}).status == "PASS"
    events["events"] = [e for e in events["events"] if e["event_type"] != "benign_canary_change"]
    assert "exactly one" in v9_ext_t2n_canary_turn_events(events, {"R-999"}).detail


def test_v10_forbidden_fields_and_fresh_process():
    assert v10_t2n_forbidden_fields([{"public_task_id": "opaque", "observation": {"text": "x"}}]).status == "PASS"
    assert v10_t2n_forbidden_fields([{"public_task_id": "opaque", "observation": {"permutation_seed": 1}}]).status == "FAIL"
    assert v10_t2n_fresh_process_isolation().status == "PASS"


def test_v10_insufficient_data_is_not_false_pass_and_item4_is_explicit_stub():
    assert v10_t2n_lookup_classifiers([], ["section_bucket"]).status == "STUBBED"
    assert v10_t2n_permutation_mi([], ["section_bucket"]).status == "STUBBED"
    with pytest.raises(NotImplementedError, match="item 4"):
        v10_t2n_quota_batch_attacker()


def test_v10_lookup_classifier_detects_public_label_leak():
    tranches = []
    for _ in range(4):
        tranches.append([{"label": label, "leaky": label} for label in ("acceptable", "unacceptable") for _ in range(4)])
    result = v10_t2n_lookup_classifiers(tranches, ["leaky"])
    assert result.status == "FAIL" and "balanced accuracy" in result.detail
