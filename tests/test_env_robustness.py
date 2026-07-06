"""An invalid action must never kill an episode (found live: GLM sent read_doc
with an empty doc_id and the env crashed, aborting a paid run)."""
from pathlib import Path

from env import Episode

TASK = "tasks/contracts/T1-NDA-001"


def _episode(tmp_path: Path) -> Episode:
    ep = Episode(TASK, seed=0, run_dir=str(tmp_path / "run"))
    ep.reset()
    return ep


def test_unknown_doc_id_returns_error_observation(tmp_path):
    ep = _episode(tmp_path)
    obs = ep.step({"action": "read_doc", "doc_id": ""})
    assert obs["event"] == "error"
    assert "unknown doc_id" in obs["error"]
    assert obs["done"] is False


def test_malformed_params_return_error_observation(tmp_path):
    ep = _episode(tmp_path)
    obs = ep.step({"action": "read_doc", "doc_id": "DOC-01", "start": "abc"})
    assert obs["event"] == "error"
    assert obs["done"] is False


def test_episode_recovers_after_error(tmp_path):
    ep = _episode(tmp_path)
    ep.step({"action": "read_doc", "doc_id": "nope"})
    obs = ep.step({"action": "list_docs"})
    assert obs["event"] == "list_docs"
    assert obs["turn"] == 2  # the bad action still consumed a turn
