from __future__ import annotations
import json
import shutil
from pathlib import Path
import pytest
from baselines.t2n_mech import STRATEGIES, TRANCHE_GATED, drive_strategy
from env import Episode
ROOT = Path(__file__).resolve().parents[1]
@pytest.fixture
def combined_task(tmp_path):
    target = tmp_path / "pilot"
    shutil.copytree(ROOT / "tasks/generated/T2-DPA-302", target)
    shutil.copytree(ROOT / "tasks/t2n_draft/T2N-DPA-302-S7302", target, dirs_exist_ok=True)
    return target
@pytest.mark.parametrize("strategy", sorted(STRATEGIES))
def test_t2n_battery(combined_task, tmp_path, strategy):
    e = Episode(combined_task, seed=0, run_dir=tmp_path / strategy)
    e.reset(); drive_strategy(e, strategy)
    score = json.loads(e.score_path.read_text())
    assert e.done and {"composite", "status", "channels"} <= score.keys()
    if strategy not in TRANCHE_GATED:
        assert score["composite"] < .40
    # Counter-only attacks need the release-wide tranche gate, unavailable here.
    if strategy in {"reject_all_nearest_rule", "duplicate_action_washer"}:
        assert score["status"] == "GAMED"
