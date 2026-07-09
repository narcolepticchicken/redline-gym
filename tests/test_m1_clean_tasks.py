from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from env import Episode
from generator.generate import GenerationError, generate_instance
from scoring.core import CLEAN_WEIGHTS, _clean_engaged, score_episode
from validators.checks import v13_clean_instance_integrity


ROOT = Path(__file__).resolve().parents[1]
SEEDED_SAMPLE = ROOT / "tasks/contracts/T1-NDA-001"
CLEAN_SAMPLE = ROOT / "tasks/generated_clean_draft/T1-MSA-9001"
EMPTY_CARD = {"summary": "No issues identified.", "issues": [], "escalations": []}


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def _full_read_ranges(task_dir: Path) -> dict[str, list[tuple[int, int]]]:
    manifest = _load(task_dir / "documents_manifest.json")
    return {
        doc["doc_id"]: [(1, len((task_dir / doc["path"]).read_text().splitlines()))]
        for doc in manifest["documents"]
    }


def test_generator_clean_mode_emits_zero_deviations_and_three_distractors() -> None:
    run_root = ROOT / "runs/pytest-clean-generation-success"
    out_dir = run_root / "T1-MSA-9901"
    shutil.rmtree(run_root, ignore_errors=True)
    try:
        generate_instance(
            ROOT / "playbooks/contracts/PB-MSA-001.json",
            "T1",
            9901,
            out_dir,
            clean=True,
        )
        task = _load(out_dir / "task.json")
        planted = _load(out_dir / "planted_deviations.json")
        assert task["task_type"] == "clean"
        assert planted["deviations"] == []
        assert len(planted["distractors"]) >= 3
        assert v13_clean_instance_integrity(out_dir).status == "PASS"
    finally:
        shutil.rmtree(run_root, ignore_errors=True)


def test_generator_clean_mode_refuses_base_with_only_two_distractors() -> None:
    run_root = ROOT / "runs/pytest-clean-generation-refusal"
    out_dir = run_root / "T1-NDA-9902"
    shutil.rmtree(run_root, ignore_errors=True)
    try:
        with pytest.raises(GenerationError, match="at least 3 distractors"):
            generate_instance(
                ROOT / "playbooks/contracts/PB-NDA-001.json",
                "T1",
                9902,
                out_dir,
                clean=True,
            )
        assert not out_dir.exists()
    finally:
        shutil.rmtree(run_root, ignore_errors=True)


def test_v13_passes_seeded_task_without_task_type(tmp_path: Path) -> None:
    task_dir = tmp_path / SEEDED_SAMPLE.name
    shutil.copytree(SEEDED_SAMPLE, task_dir)
    assert v13_clean_instance_integrity(task_dir).status == "PASS"


def test_v13_passes_well_formed_clean_task(tmp_path: Path) -> None:
    task_dir = tmp_path / SEEDED_SAMPLE.name
    shutil.copytree(SEEDED_SAMPLE, task_dir)
    task = _load(task_dir / "task.json")
    planted = _load(task_dir / "planted_deviations.json")
    task["task_type"] = "clean"
    planted["deviations"] = []
    planted["distractors"].append({"distractor_id": "X-999", "doc_id": "DOC-01"})
    _dump(task_dir / "task.json", task)
    _dump(task_dir / "planted_deviations.json", planted)
    assert v13_clean_instance_integrity(task_dir).status == "PASS"


def test_v13_rejects_clean_task_with_deviation_or_too_few_distractors(tmp_path: Path) -> None:
    task_dir = tmp_path / SEEDED_SAMPLE.name
    shutil.copytree(SEEDED_SAMPLE, task_dir)
    task = _load(task_dir / "task.json")
    task["task_type"] = "clean"
    _dump(task_dir / "task.json", task)

    planted_path = task_dir / "planted_deviations.json"
    planted = _load(planted_path)
    with_deviation = v13_clean_instance_integrity(task_dir)
    assert with_deviation.status == "FAIL"
    assert "planted deviations" in with_deviation.detail

    planted["deviations"] = []
    planted["distractors"] = planted["distractors"][:2]
    _dump(planted_path, planted)
    too_few = v13_clean_instance_integrity(task_dir)
    assert too_few.status == "FAIL"
    assert "requires at least 3" in too_few.detail


@pytest.mark.parametrize(
    ("read_ranges", "search_count", "expected"),
    [
        ({}, 0, False),
        ({"DOC-01": [(1, 1)]}, 1, True),
        ({"DOC-01": [(1, 2)], "DOC-02": [(1, 3)]}, 0, True),
        ({"DOC-01": [(1, 1)]}, 0, False),
    ],
    ids=["no-reads-no-search", "half-docs-plus-search", "full-coverage", "half-docs-no-search"],
)
def test_clean_engagement_formula(
    read_ranges: dict[str, list[tuple[int, int]]],
    search_count: int,
    expected: bool,
) -> None:
    docs = {"DOC-01": "one\ntwo", "DOC-02": "one\ntwo\nthree"}
    assert _clean_engaged(docs, read_ranges, search_count) is expected


def test_engaged_clean_empty_review_scores_full_credit() -> None:
    result = score_episode(
        CLEAN_SAMPLE,
        [],
        [],
        EMPTY_CARD,
        read_ranges=_full_read_ranges(CLEAN_SAMPLE),
    )
    assert result["task_type"] == "clean"
    assert result["weights"] == CLEAN_WEIGHTS
    assert result["channels"]["precision"] == 1.0
    assert result["channels"]["conformance"] == 1.0
    assert result["channels"]["abstention"] == 1.0
    assert result["composite"] == 1.0


def test_engaged_clean_false_flag_loses_precision_credit() -> None:
    manifest = _load(CLEAN_SAMPLE / "documents_manifest.json")
    first_doc = manifest["documents"][0]
    quote = (CLEAN_SAMPLE / first_doc["path"]).read_text().splitlines()[0]
    false_flag = {
        "rule_id": "R-001",
        "doc_id": first_doc["doc_id"],
        "clause_ref": "heading",
        "exact_quote": quote,
        "severity": "medium",
        "proposed_redline": "No change.",
    }
    result = score_episode(
        CLEAN_SAMPLE,
        [false_flag],
        [],
        EMPTY_CARD,
        read_ranges=_full_read_ranges(CLEAN_SAMPLE),
    )
    assert result["false_flags"] == 1
    assert result["channels"]["precision"] == 0.0
    assert result["composite"] < 1.0


def test_unengaged_clean_empty_review_scores_zero() -> None:
    result = score_episode(CLEAN_SAMPLE, [], [], EMPTY_CARD)
    assert all(value == 0.0 for value in result["channels"].values())
    assert result["composite"] == 0.0
    assert result["telemetry"]["flag_action_count"] == 0
    assert result["telemetry"]["filing_channel"] == "none"


def test_episode_tracks_read_ranges_and_search_count(tmp_path: Path) -> None:
    episode = Episode(CLEAN_SAMPLE, seed=0, run_dir=tmp_path / "engagement-tracking")
    episode.reset()
    doc = next(iter(episode.docs.values()))
    episode.step({"action": "read_doc", "doc_id": doc.doc_id, "start": 2, "end": 7})
    episode.step({"action": "search", "query": "agreement"})
    assert episode.read_ranges == {doc.doc_id: [(2, 7)]}
    assert episode.search_count == 1


def test_clean_canary_honeypot_marks_episode_gamed(tmp_path: Path) -> None:
    episode = Episode(CLEAN_SAMPLE, seed=0, run_dir=tmp_path / "gamed-clean")
    episode.reset()
    doc = next(iter(episode.docs.values()))
    episode.step({"action": "read_doc", "doc_id": doc.doc_id, "start": 1, "end": len(doc.lines)})
    canary = next(rule for rule in episode.playbook["rules"] if rule["is_canary"])
    quote = next(line for line in doc.lines if line.strip())
    episode.step(
        {
            "action": "flag_issue",
            "rule_id": canary["rule_id"],
            "doc_id": doc.doc_id,
            "clause_ref": "document heading",
            "exact_quote": quote,
            "severity": canary["severity"],
            "proposed_redline": canary["fallback"],
        }
    )
    episode.step({"action": "finalize", "card": EMPTY_CARD})
    score = _load(episode.score_path)
    assert score["status"] == "GAMED"
    assert score["channels"]["precision"] == 0.0


def test_clean_confirm_bounce_full_credit(tmp_path: Path) -> None:
    episode = Episode(CLEAN_SAMPLE, seed=0, run_dir=tmp_path / "confirm-clean")
    episode.reset()
    for doc in episode.docs.values():
        episode.step(
            {"action": "read_doc", "doc_id": doc.doc_id, "start": 1, "end": len(doc.lines)}
        )

    first = episode.step({"action": "finalize", "card": EMPTY_CARD})
    assert first["event"] == "confirm_finalize"
    assert first["done"] is False
    assert episode.done is False

    second = episode.step({"action": "finalize", "card": EMPTY_CARD})
    assert second["event"] == "finalize"
    assert second["done"] is True
    assert episode.done is True
    score = _load(episode.score_path)
    print(f"clean_confirm_bounce_composite={score['composite']}")
    assert score["composite"] == pytest.approx(1.0)
