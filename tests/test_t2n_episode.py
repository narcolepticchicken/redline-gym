from __future__ import annotations

import inspect
import json
from math import sqrt
from pathlib import Path
import re
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
    rules = {rule["rule_id"]: rule for rule in ep.reset()["playbook"]} if ep.last_observation is None else {
        rule["rule_id"]: rule for rule in ep.last_observation["playbook"]
    }
    issues = []
    for dev in artifacts["deviations"]:
        action = {
            "action": "flag_issue", "rule_id": dev["rule_id"], "doc_id": dev["doc_id"],
            "clause_ref": dev["clause_anchor"]["section"], "exact_quote": dev["mutated_text"],
            "proposed_redline": rules[dev["rule_id"]]["fallback"],
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


def _normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _visible_overlap(left: str, right: str) -> bool:
    left, right = _normalized(left), _normalized(right)
    return len(left) >= 20 and len(right) >= 20 and (left in right or right in left)


def _matched_position(change: dict, issued_positions: list[dict]) -> dict:
    visible_change_texts = [change.get("before_text", ""), change.get("after_text", "")]
    overlap = [
        position for position in issued_positions
        if any(_visible_overlap(position.get("exact_quote", ""), text) for text in visible_change_texts)
    ]
    if len(overlap) == 1:
        return overlap[0]
    nearby = [
        position for position in issued_positions
        if position.get("doc_id") == change.get("doc_id")
        and position.get("clause_ref") == change.get("section_ref")
    ]
    assert len(nearby) == 1, change["change_id"]
    return nearby[0]


def _best_visible_rule(text: str, playbook: list[dict]) -> dict:
    tokens = set(re.findall(r"[a-z0-9]+", text.casefold()))
    return max(
        playbook,
        key=lambda rule: len(tokens & set(re.findall(
            r"[a-z0-9]+", f'{rule["position"]} {rule["fallback"]}'.casefold()
        ))),
    )


def _observation_only_actions(observation: dict) -> list[dict]:
    """Review the fixture using only fields present in the phase-2 reveal."""
    structural_decisions = {
        ("concession", "sole"): "accept",
        ("sneaky_reinsert", "source_cleanup"): "accept",
        ("regression", "sole"): "reject",
        ("sneaky_reinsert", "inserted_effect"): "reject",
        ("new_deviation", "sole"): "reject",
        ("benign_canary_change", "sole"): "accept",
    }
    counter_decisions = {
        # The changed text disclaims all data-subject and regulator support,
        # contradicting visible R-006's requirement for reasonable assistance.
        "CH-COUNTER-1": "reject",
        # One annual routine audit preserves incident/cause follow-up, matching
        # visible R-008's position and fallback even though decoy timings vary.
        "CH-COUNTER-2": "accept",
    }
    rules = {rule["rule_id"]: rule for rule in observation["playbook"]}
    actions = []
    for change in observation["changes"]:
        if change["event_type"] == "counter_proposal":
            decision = counter_decisions[change["change_id"]]
        else:
            decision = structural_decisions[(change["event_type"], change["child_role"])]
        action = {
            "action": "review_change", "change_id": change["change_id"],
            "origin": change["origin"], "decision": decision,
        }
        matched = None
        if change["origin"] == "prior_position":
            matched = _matched_position(change, observation["issued_positions"])
            action["prior_position_id"] = matched["position_id"]
            action["rule_id"] = matched["rule_id"]
        if decision == "reject":
            rule = rules[matched["rule_id"]] if matched else _best_visible_rule(
                change["after_text"], observation["playbook"]
            )
            action.update(
                rule_id=rule["rule_id"], exact_quote=change["after_text"],
                proposed_redline=rule["fallback"],
            )
        actions.append(action)
    return actions


def _finish(ep: Episode, actions: list[dict]) -> dict:
    for action in actions:
        assert ep.step(action)["event"] == "review_change"
    ep.step({"action": "finalize", "card": {
        "changes": actions, "escalations": [], "summary": "complete",
    }})
    return json.loads(ep.score_path.read_text())


def test_honest_observation_only_episode_and_prompt(combined_task: Path, tmp_path: Path):
    ep = Episode(combined_task, seed=0, run_dir=tmp_path / "run")
    reset = ep.reset()
    legacy_prompt = observation_prompt(reset)
    assert "Phase 2 also allows" not in legacy_prompt
    assert "review_change" not in reset["action_spec"]
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
    score = _finish(ep, _observation_only_actions(reveal))
    assert score["phase1"]["channels"]["fallback"] == 0.0
    assert score["phase1"]["composite"] == 0.85
    assert score["channels"] == {
        "S": 1.0, "T": 1.0, "J": 1.0, "Q": 1.0, "L": 1.0,
        "G": 1.0, "D": 0.5, "F": 1.0, "A": 1.0,
    }
    # W2 = .30S+.20T+.15J+.10Q+.10L+.05G+.05D+.03F+.02A
    #    = .975; every ordinary floor passes, so P2=.975.
    # P1=.85 because the visible playbook fallbacks earn phase-1 fallback=0;
    # E0=E=sqrt(.85*.975), integrity passes, and reporting caps composite at .80.
    assert score["W2"] == score["P2"] == 0.975
    assert score["E0"] == score["E"] == sqrt(0.85 * 0.975)
    assert score["harm_integrity"] is True
    assert score["reported_E"] == score["composite"] == 0.8


def test_observation_only_review_builder_has_no_answer_key_references():
    # This action-construction guard is intentionally broader and more specific
    # than env.episode.ANSWER_KEY_NAMES, which protects manifest document paths.
    source = inspect.getsource(_observation_only_actions)
    forbidden = {
        "patch_ledger", "expected_disposition", "expected_rule_id", "expected_clause_id",
        "ground_span", "transition_row_id", "plant_position", "counter_class",
        "counter_family_id", "counter_guard_id", "prior_source_deviation_id",
    }
    assert all(name not in source for name in forbidden)


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
