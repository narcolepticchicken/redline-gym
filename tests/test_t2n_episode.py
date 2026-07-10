from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from baselines.llm_common import observation_prompt
from env import Episode


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def combined_task(tmp_path: Path) -> Path:
    target = tmp_path / "combined"
    shutil.copytree(ROOT / "tasks/generated/T2-DPA-302", target)
    shutil.copytree(ROOT / "tasks/t2n_draft/T2N-DPA-302-S7302", target, dirs_exist_ok=True)
    return target


def _phase1(ep: Episode, task: Path) -> dict:
    artifacts = json.loads((task / "planted_deviations.json").read_text())
    issues = []
    for dev in artifacts["deviations"]:
        action = {
            "action": "flag_issue", "rule_id": dev["rule_id"], "doc_id": dev["doc_id"],
            "clause_ref": "matched clause", "exact_quote": dev["mutated_text"],
            "proposed_redline": dev["expected_redline_text"],
        }
        assert ep.step(action)["event"] == "flag_issue"
        issues.append({k: v for k, v in action.items() if k != "action"})
    missing = artifacts["missing_info"][0]
    escalation = {"topic": missing["topic"], "reason": missing["topic"]}
    ep.step({"action": "escalate", **escalation})
    return ep.step({"action": "finalize", "card": {
        "issues": issues, "escalations": [escalation], "summary": "complete",
    }})


def _actions(task: Path, policy: str = "perfect") -> list[dict]:
    actions = []
    for patch in json.loads((task / "patch_ledger.json").read_text())["patches"]:
        decision = patch["expected_disposition"]
        if policy == "accept_all": decision = "accept"
        if policy == "reject_all": decision = "reject"
        if policy == "prior_replayer" and patch["event_type"] == "new_deviation": decision = "accept"
        action = {"action": "review_change", "change_id": patch["change_id"],
                  "origin": patch["origin"], "decision": decision}
        if patch["origin"] == "prior_position":
            action["prior_position_id"] = "POS-" + patch["prior_source_deviation_id"].replace("-", "")
            if policy in ("perfect", "prior_replayer"):
                action["rule_id"] = patch["expected_rule_id"]
        if decision == "reject":
            action["rule_id"] = patch["expected_rule_id"]
            action["exact_quote"] = patch["ground_span"]
        if patch.get("expected_redline_text") and decision == "reject":
            action["proposed_redline"] = patch["expected_redline_text"]
        actions.append(action)
    return actions


def _finish(ep: Episode, actions: list[dict]) -> dict:
    for action in actions:
        assert ep.step(action)["event"] == "review_change"
    ep.step({"action": "finalize", "card": {
        "changes": actions, "escalations": [], "summary": "complete",
    }})
    return json.loads(ep.score_path.read_text())


def test_honest_perfect_episode_and_prompt(combined_task: Path, tmp_path: Path):
    ep = Episode(combined_task, seed=0, run_dir=tmp_path / "run")
    reset = ep.reset()
    legacy_prompt = observation_prompt(reset)
    assert "Phase 2 also allows" not in legacy_prompt
    reveal = _phase1(ep, combined_task)
    assert reveal["event"] == "phase2_reveal" and reveal["done"] is False
    assert {p["position_id"] for p in reveal["issued_positions"]} == {
        "POS-D001", "POS-D002", "POS-D003", "POS-D004", "POS-D005"
    }
    assert "Phase 2 also allows review_change" in observation_prompt(reveal)
    forbidden = {"expected_disposition", "expected_rule_id", "expected_clause_id", "ground_span",
                 "transition_row_id", "plant_position", "counter_class", "counter_family_id",
                 "counter_guard_id", "prior_source_deviation_id"}
    assert all(not (forbidden & set(change)) for change in reveal["changes"])
    score = _finish(ep, _actions(combined_task))
    assert score["phase1"]["composite"] == 1.0
    assert score["channels"] == {k: 1.0 for k in "STJQLGDFA"}
    assert score["W2"] == score["P2"] == score["E0"] == score["E"] == 1.0
    assert score["harm_integrity"] is True
    assert score["reported_E"] == score["composite"] == 0.8


@pytest.mark.parametrize("policy, expected, gamed", [
    ("accept_all", 0.0, False), ("reject_all", 0.0, True), ("prior_replayer", 0.2, False),
])
def test_scripted_attackers(combined_task: Path, tmp_path: Path, policy: str, expected: float, gamed: bool):
    ep = Episode(combined_task, seed=0, run_dir=tmp_path / policy)
    ep.reset(); _phase1(ep, combined_task)
    score = _finish(ep, _actions(combined_task, policy))
    assert score["composite"] == pytest.approx(expected)
    assert score["composite"] < .40
    assert (score["status"] == "GAMED") is gamed
    if policy == "prior_replayer":
        assert score["channels"]["S"] == .75
        assert score["W2"] == pytest.approx(.925)
        assert score["harm_integrity"] is False


def test_phase1_only_scores_zero(combined_task: Path, tmp_path: Path):
    ep = Episode(combined_task, seed=0, run_dir=tmp_path / "run")
    ep.reset(); _phase1(ep, combined_task)
    card = {"changes": [], "escalations": [], "summary": "complete"}
    assert ep.step({"action": "finalize", "card": card})["event"] == "confirm_finalize"
    assert ep.step({"action": "finalize", "card": card})["done"] is True
    score = json.loads(ep.score_path.read_text())
    assert score["P2"] == score["E0"] == score["composite"] == 0.0


def test_conflict_is_wrong_and_identical_duplicate_collapses(combined_task: Path, tmp_path: Path):
    ep = Episode(combined_task, seed=0, run_dir=tmp_path / "conflict")
    ep.reset(); _phase1(ep, combined_task)
    actions = _actions(combined_task)
    first = actions[0]
    ep.step(first); ep.step(first)
    conflict = dict(first); conflict["decision"] = "reject"
    conflict["rule_id"] = "R-011"; conflict["exact_quote"] = "wrong but non-empty"
    ep.step(conflict)
    for action in actions[1:]: ep.step(action)
    ep.step({"action": "finalize", "card": {"changes": actions, "escalations": [], "summary": "x"}})
    score = json.loads(ep.score_path.read_text())
    assert score["channels"]["F"] == 0.0
    child = next(c for c in score["telemetry"]["children"] if c["change_id"] == first["change_id"])
    assert child["decision"] is None and child["decision_correct"] is False

    ep2 = Episode(combined_task, seed=0, run_dir=tmp_path / "identical")
    ep2.reset(); _phase1(ep2, combined_task)
    ep2.step(actions[0]); ep2.step(actions[0])
    for action in actions[1:]: ep2.step(action)
    ep2.step({"action": "finalize", "card": {"changes": actions, "escalations": [], "summary": "x"}})
    assert json.loads(ep2.score_path.read_text())["channels"]["F"] == 1.0


def test_origin_schema_errors_are_nonfatal(combined_task: Path, tmp_path: Path):
    ep = Episode(combined_task, seed=0, run_dir=tmp_path / "run")
    ep.reset(); _phase1(ep, combined_task)
    bad1 = {"action":"review_change","change_id":"CH-CONCESSION","origin":"prior_position","decision":"accept"}
    bad2 = {"action":"review_change","change_id":"CH-NEW-DEVIATION","origin":"novel_insertion",
            "decision":"accept","prior_position_id":"POS-D001"}
    assert ep.step(bad1)["event"] == "error"
    assert ep.step(bad2)["event"] == "error"
    recovered = ep.step({"action": "list_docs"})
    assert recovered["event"] == "list_docs" and recovered["turn"] == 10 and not recovered["done"]


@pytest.mark.parametrize("task", ["tasks/contracts/T1-NDA-001", "tasks/generated/T1-MSA-9001"])
def test_legacy_score_regression_is_dict_identical(task: str, tmp_path: Path):
    expected = json.loads((ROOT / "tests/fixtures/t2n_legacy_score_baselines.json").read_text())
    ep = Episode(ROOT / task, seed=0, run_dir=tmp_path / "run")
    ep.reset(); card = {"issues": [], "escalations": [], "summary": "done"}
    ep.step({"action": "finalize", "card": card}); ep.step({"action": "finalize", "card": card})
    assert json.loads(ep.score_path.read_text()) == expected[ep.task_id]


def test_all_concessions_gate(combined_task: Path, tmp_path: Path):
    task = tmp_path / "all-concessions"
    shutil.copytree(combined_task, task)
    ledger = json.loads((task / "patch_ledger.json").read_text())
    ledger["patches"] = [p for p in ledger["patches"] if p["event_type"] == "concession"]
    (task / "patch_ledger.json").write_text(json.dumps(ledger))
    events = json.loads((task / "turn_events.json").read_text())
    events["events"] = [e for e in events["events"] if e["event_type"] == "concession"]
    (task / "turn_events.json").write_text(json.dumps(events))
    task_json = json.loads((task / "task.json").read_text()); task_json["task_type"] = "t2n_all_concessions"
    (task / "task.json").write_text(json.dumps(task_json))

    def run(decide: bool) -> dict:
        ep = Episode(task, seed=0, run_dir=tmp_path / ("all" if decide else "omit"))
        ep.reset(); reveal = _phase1(ep, task)
        action = _actions(task)[0]
        changes = []
        if decide: ep.step(action); changes = [action]
        card = {"changes": changes, "escalations": [], "summary": "complete"}
        if not decide: ep.step({"action":"finalize","card":card})
        ep.step({"action":"finalize","card":card})
        return json.loads(ep.score_path.read_text())
    assert run(True)["composite"] == 1.0
    failed = run(False)
    assert failed["composite"] == 0.0 and failed["gate_pass"] is False
