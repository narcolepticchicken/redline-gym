"""Empty-submission confirmation bounce: a finalize with zero flags and zero
escalations gets one warning; a repeated finalize proceeds. Non-empty
finalizes are unaffected. (Prep for the DPA premature-quit rerun decision.)"""
from pathlib import Path

from env import Episode

TASK = "tasks/contracts/T1-NDA-001"


def _episode(tmp_path: Path) -> Episode:
    ep = Episode(TASK, seed=0, run_dir=str(tmp_path / "run"))
    ep.reset()
    return ep


def test_empty_finalize_bounces_once_then_proceeds(tmp_path):
    ep = _episode(tmp_path)
    obs = ep.step({"action": "finalize", "card": {"issues": [], "escalations": [], "summary": "done"}})
    assert obs["event"] == "confirm_finalize"
    assert obs["done"] is False
    obs = ep.step({"action": "finalize", "card": {"issues": [], "escalations": [], "summary": "done"}})
    assert obs["event"] == "finalize"
    assert obs["done"] is True


def test_nonempty_finalize_unaffected(tmp_path):
    ep = _episode(tmp_path)
    ep.step({"action": "escalate", "topic": "t", "reason": "r"})
    obs = ep.step({"action": "finalize", "card": {"issues": [], "escalations": [{"topic": "t", "reason": "r"}], "summary": "done"}})
    assert obs["event"] == "finalize"
    assert obs["done"] is True


def test_agent_can_resume_work_after_bounce(tmp_path):
    ep = _episode(tmp_path)
    ep.step({"action": "finalize", "card": {"issues": [], "escalations": [], "summary": "x"}})
    obs = ep.step({"action": "list_docs"})
    assert obs["event"] == "list_docs"
    assert obs["done"] is False
