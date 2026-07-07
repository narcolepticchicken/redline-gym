from __future__ import annotations

import json
from pathlib import Path

from baselines.cheater_mech import STRATEGIES, main as cheater_main
from generator.generate import ALLOWED_MECHANISMS


ROOT = Path(__file__).resolve().parents[1]
NDA = ROOT / "tasks/contracts/T1-NDA-001"
MSA = ROOT / "tasks/contracts/T2-MSA-001"


def _score(run_dir: Path, task_id: str) -> dict:
    return json.loads((run_dir / task_id / "score.json").read_text())


def test_mechanical_fabricator_grounding_is_zero(tmp_path: Path) -> None:
    run_dir = tmp_path / "fabricator"
    assert cheater_main(["--task", str(NDA), "--seed", "0", "--strategy", "fabricator", "--run-dir", str(run_dir)]) == 0
    score = _score(run_dir, "T1-NDA-001")
    assert score["channels"]["grounding"] == 0.0


def test_mechanical_canary_citer_marks_episode_gamed(tmp_path: Path) -> None:
    run_dir = tmp_path / "canary"
    assert cheater_main(["--task", str(NDA), "--seed", "0", "--strategy", "canary_citer", "--run-dir", str(run_dir)]) == 0
    score = _score(run_dir, "T1-NDA-001")
    assert score["status"] == "GAMED"


def test_every_mechanical_strategy_scores_without_error(tmp_path: Path) -> None:
    for task in [NDA, MSA]:
        for strategy in sorted(STRATEGIES):
            run_dir = tmp_path / task.name / strategy
            assert cheater_main(["--task", str(task), "--seed", "3", "--strategy", strategy, "--run-dir", str(run_dir)]) == 0
            score = _score(run_dir, task.name)
            assert isinstance(score["composite"], float)
            assert "recall" in score["channels"]


def test_recipe_books_cover_required_rules_and_mechanisms() -> None:
    t2_mechanisms = ALLOWED_MECHANISMS["T2"]
    assert "off_playbook_addition" in t2_mechanisms
    for recipe_path in sorted((ROOT / "generator/recipes").glob("PB-*.json")):
        payload = json.loads(recipe_path.read_text())
        entries = payload["entries"]
        covered_rules = {entry["rule_id"] for entry in entries}
        mechanisms = {entry["mechanism"] for entry in entries}
        direct_rules = {entry["rule_id"] for entry in entries if entry["mechanism"] == "direct_term_swap"}
        assert len(covered_rules) >= 8
        assert len(direct_rules) >= 4
        assert mechanisms <= t2_mechanisms
        if recipe_path.name == "PB-GOV-001.json":
            assert "off_playbook_addition" in mechanisms


def test_non_eval_tooling_does_not_reference_heldout_path() -> None:
    non_eval_files = []
    for directory in ["generator", "baselines", "env", "validators", "scoring", "report"]:
        non_eval_files.extend((ROOT / directory).rglob("*"))
    non_eval_files.extend(
        path
        for path in (ROOT / "scripts").glob("*.py")
        if path.name not in {"make_validity_report.py"}
    )
    offenders = []
    for path in non_eval_files:
        if path.is_file() and "tasks/heldout" in path.read_text(errors="ignore"):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []
