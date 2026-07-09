from __future__ import annotations

import json
from pathlib import Path

import pytest

from env import Episode
from scripts.build_sft_data import build_sft_data, build_sft_data_from_runs
from scripts.collect_rollouts import collect_rollouts

ROOT = Path(__file__).resolve().parents[1]
GENERATED_NDA = ROOT / "tasks/generated/T1-NDA-101"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def test_collect_rollouts_manifest_logic_uses_fake_runner(tmp_path: Path) -> None:
    task = tmp_path / "tasks" / "generated" / "T1-FAKE-001"
    _write_json(task / "task.json", {"task_id": "T1-FAKE-001"})

    def fake_runner(task_dir: Path, seed: int, run_root: Path) -> dict:
        task_id = json.loads((task_dir / "task.json").read_text())["task_id"]
        episode_dir = run_root / task_id
        score = {
            "task_id": task_id,
            "composite": 0.5 + seed / 100,
            "channels": {"recall": 1.0},
            "num_turns": seed,
        }
        _write_json(episode_dir / "score.json", score)
        _write_json(episode_dir / "usage.json", {"total_tokens": seed * 10})
        return {"run_dir": str(episode_dir), "score_path": str(episode_dir / "score.json")}

    rows = collect_rollouts(
        tasks=[task],
        n_per_task=2,
        out_root=tmp_path / "runs_pilot" / "fake",
        seed_base=7,
        runner=fake_runner,
    )

    manifest_rows = [
        json.loads(line)
        for line in (tmp_path / "runs_pilot" / "fake" / "manifest.jsonl").read_text().splitlines()
    ]
    assert rows == manifest_rows
    assert [row["sample_idx"] for row in rows] == [0, 1]
    assert [row["seed"] for row in rows] == [7, 8]
    assert [row["tokens"] for row in rows] == [70, 80]
    assert all(row["task_id"] == "T1-FAKE-001" for row in rows)
    assert all(Path(row["run_dir"]).name == "T1-FAKE-001" for row in rows)


def test_build_sft_data_filters_top_k_and_skips_salvage_finalize(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.jsonl"
    rows = [
        _episode_fixture(tmp_path, "task-a", 0, 0.7, assistant='{"action":"list_docs"}'),
        _episode_fixture(tmp_path, "task-a", 1, 0.6, assistant='{"action":"search","query":"x"}'),
        _episode_fixture(tmp_path, "task-a", 2, 0.4, assistant='{"action":"list_docs"}'),
        _episode_fixture(tmp_path, "task-b", 0, 0.55, assistant='{"action":"read_doc","doc_id":"DOC-01"}'),
    ]
    _write_jsonl(manifest, rows)

    out = tmp_path / "data" / "pilot_sft.jsonl"
    training_rows = build_sft_data(
        manifest=manifest,
        min_composite=0.5,
        top_k_per_task=1,
        out=out,
    )

    written = [json.loads(line) for line in out.read_text().splitlines()]
    assert written == training_rows
    assert len(training_rows) == 2
    assert training_rows[0]["messages"] == [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "observation prompt 0"},
        {"role": "assistant", "content": '{"action":"list_docs"}'},
    ]
    all_content = "\n".join(
        message["content"]
        for row in training_rows
        for message in row["messages"]
    )
    assert "salvage" not in all_content
    assert '{"action":"search","query":"x"}' not in all_content


def test_build_sft_data_from_runs_reconstructs_missing_driver_conversation(tmp_path: Path) -> None:
    run_root = tmp_path / "runs" / "honest_llm-seed7"
    episode_dir = _replay_episode_fixture(run_root, seed=7, composite=0.8)

    out = tmp_path / "data" / "pilot_sft.jsonl"
    sidecar = tmp_path / "data" / "pilot_sft_manifest.jsonl"
    rows = build_sft_data_from_runs(
        run_globs=[str(run_root)],
        min_composite=0.5,
        max_per_task=1,
        out=out,
        sidecar_manifest=sidecar,
    )

    assert len(rows) == 1
    assert not (episode_dir / "driver_conversation.jsonl").exists()
    messages = rows[0]["messages"]
    assert messages[0]["role"] == "system"
    assert len([message for message in messages if message["role"] == "assistant"]) == 3
    assert '"event": "reset"' in messages[1]["content"]
    assert messages[2] == {"role": "assistant", "content": '{"action":"list_docs"}'}
    manifest_row = json.loads(sidecar.read_text().splitlines()[0])
    assert manifest_row["source"]["teacher_model"] == "honest_llm"
    assert manifest_row["source"]["run_dir"] == str(run_root)


def test_build_sft_data_from_runs_skips_replay_event_mismatch(tmp_path: Path) -> None:
    run_root = tmp_path / "runs" / "honest_llm-seed8"
    episode_dir = _replay_episode_fixture(run_root, seed=8, composite=0.8)
    transcript = _read_jsonl(episode_dir / "episode.jsonl")
    transcript[0]["observation"]["event"] = "wrong"
    _write_jsonl(episode_dir / "episode.jsonl", transcript)

    out = tmp_path / "data" / "pilot_sft.jsonl"
    sidecar = tmp_path / "data" / "pilot_sft_manifest.jsonl"
    with pytest.warns(UserWarning, match="replay event mismatch"):
        rows = build_sft_data_from_runs(
            run_globs=[str(run_root)],
            min_composite=0.5,
            max_per_task=1,
            out=out,
            sidecar_manifest=sidecar,
        )

    assert rows == []
    assert out.read_text() == ""
    assert sidecar.read_text() == ""


def test_build_sft_data_from_runs_uses_score_v2_min_composite_and_max_per_task(tmp_path: Path) -> None:
    low = _conversation_run_fixture(tmp_path, "rank_dsv4pro-seed1", composite=0.9, score_v2_composite=0.4)
    high = _conversation_run_fixture(tmp_path, "rank_dsv4pro-seed2", composite=0.2, score_v2_composite=0.85)
    other = _conversation_run_fixture(tmp_path, "rank_minimaxm3-seed3", composite=0.95, score_v2_composite=0.83)

    out = tmp_path / "data" / "pilot_sft.jsonl"
    sidecar = tmp_path / "data" / "pilot_sft_manifest.jsonl"
    rows = build_sft_data_from_runs(
        run_globs=[str(tmp_path / "runs" / "rank_*-seed*")],
        min_composite=0.8,
        max_per_task=1,
        out=out,
        sidecar_manifest=sidecar,
    )

    assert len(rows) == 1
    source = json.loads(sidecar.read_text().splitlines()[0])["source"]
    assert source["run_dir"] == str(high)
    assert source["composite"] == 0.85
    assert source["scorer_version"] == "v2"
    assert source["teacher_model"] == "rank_dsv4pro"
    assert str(low) not in sidecar.read_text()
    assert str(other) not in sidecar.read_text()


def _episode_fixture(tmp_path: Path, task_id: str, sample_idx: int, composite: float, assistant: str) -> dict:
    task = tmp_path / "tasks" / "generated" / task_id
    run_dir = tmp_path / "runs" / task_id / f"sample-{sample_idx}" / task_id
    _write_json(task / "task.json", {"task_id": task_id})
    _write_jsonl(
        run_dir / "episode.jsonl",
        [
            {"turn": 1, "action": json.loads(assistant), "observation": {"event": "ok"}},
            {"turn": 2, "action": {"action": "finalize"}, "observation": {"event": "finalize"}},
        ],
    )
    _write_jsonl(
        run_dir / "driver_conversation.jsonl",
        [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "turn": 1, "content": f"observation prompt {sample_idx}"},
            {"role": "assistant", "turn": 1, "content": assistant, "salvage_finalize": False},
            {"role": "user", "turn": 2, "content": "salvage user"},
            {"role": "assistant", "turn": 2, "content": "salvage assistant", "salvage_finalize": True},
        ],
    )
    return {
        "task": str(task),
        "task_id": task_id,
        "sample_idx": sample_idx,
        "run_dir": str(run_dir),
        "composite": composite,
        "channels": {"recall": composite},
        "num_turns": 2,
        "tokens": 100,
    }


def _replay_episode_fixture(run_root: Path, *, seed: int, composite: float) -> Path:
    episode = Episode(GENERATED_NDA, seed=seed, run_dir=run_root)
    episode.reset()
    episode.step({"action": "list_docs"})
    episode.step({"action": "finalize"})
    episode.step({"action": "finalize"})
    episode_dir = run_root / GENERATED_NDA.name
    score = json.loads((episode_dir / "score.json").read_text())
    score["composite"] = composite
    _write_json(episode_dir / "score.json", score)
    return episode_dir


def _conversation_run_fixture(
    tmp_path: Path,
    run_name: str,
    *,
    composite: float,
    score_v2_composite: float,
) -> Path:
    task_id = GENERATED_NDA.name
    run_root = tmp_path / "runs" / run_name
    episode_dir = run_root / task_id
    _write_jsonl(
        episode_dir / "episode.jsonl",
        [{"turn": 1, "action": {"action": "list_docs"}, "observation": {"event": "list_docs"}}],
    )
    _write_jsonl(
        episode_dir / "driver_conversation.jsonl",
        [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "turn": 1, "content": "observation"},
            {"role": "assistant", "turn": 1, "content": '{"action":"list_docs"}', "salvage_finalize": False},
        ],
    )
    _write_json(episode_dir / "score.json", {"task_id": task_id, "seed": 3, "composite": composite})
    _write_json(episode_dir / "score_v2.json", {"task_id": task_id, "composite": score_v2_composite, "scorer_version": "v2"})
    return run_root


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]
