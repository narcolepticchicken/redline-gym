from __future__ import annotations

import json
import shutil
from pathlib import Path

from validators.checks import (
    v1_rubric_citations,
    v2_mutation_anti_drift,
    v5_issue_deviation_mapping,
    v6_distractor_integrity_scan,
    v7_missing_info_string_search,
    v8_schema_and_hashes,
    v9_canary_empty,
    v10_leakage_scan,
)


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "tasks/contracts/T1-NDA-001"


def copy_sample(tmp_path: Path) -> Path:
    dest = tmp_path / "T1-NDA-001"
    shutil.copytree(SAMPLE, dest)
    return dest


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def dump(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def assert_fails(result) -> None:
    assert result.status == "FAIL", result


def test_v1_catches_missing_rubric_reference(tmp_path: Path) -> None:
    task_dir = copy_sample(tmp_path)
    rubric_path = task_dir / "rubric.json"
    rubric = load(rubric_path)
    rubric["criteria"][0]["deviation_ids"] = ["D-999"]
    dump(rubric_path, rubric)
    assert_fails(v1_rubric_citations(task_dir))


def test_v2_catches_drifted_mutation_anchor(tmp_path: Path) -> None:
    task_dir = copy_sample(tmp_path)
    planted_path = task_dir / "planted_deviations.json"
    planted = load(planted_path)
    planted["deviations"][0]["mutated_text"] = "missing replacement text"
    dump(planted_path, planted)
    assert_fails(v2_mutation_anti_drift(task_dir))


def test_v5_catches_unmapped_deviation(tmp_path: Path) -> None:
    task_dir = copy_sample(tmp_path)
    matrix_path = task_dir / "issue_matrix.json"
    matrix = load(matrix_path)
    matrix["issues"] = matrix["issues"][1:]
    dump(matrix_path, matrix)
    assert_fails(v5_issue_deviation_mapping(task_dir))


def test_v6_catches_distractor_rule_violation(tmp_path: Path) -> None:
    task_dir = copy_sample(tmp_path)
    matrix_path = task_dir / "issue_matrix.json"
    matrix = load(matrix_path)
    matrix["distractors"][0]["span"] = "This distractor says marked confidential."
    dump(matrix_path, matrix)
    assert_fails(v6_distractor_integrity_scan(task_dir))


def test_v6_catches_phantom_distractor_span(tmp_path: Path) -> None:
    task_dir = copy_sample(tmp_path)
    matrix_path = task_dir / "issue_matrix.json"
    matrix = load(matrix_path)
    matrix["distractors"][0]["span"] = "This distractor is not in the document."
    dump(matrix_path, matrix)
    assert_fails(v6_distractor_integrity_scan(task_dir))


def test_v7_catches_missing_info_term_present(tmp_path: Path) -> None:
    task_dir = copy_sample(tmp_path)
    doc_path = task_dir / "docs/mutual_nda.md"
    doc_path.write_text(doc_path.read_text() + "\nThe parties discussed personal data.\n")
    assert_fails(v7_missing_info_string_search(task_dir))


def test_v8_catches_schema_or_hash_break(tmp_path: Path) -> None:
    task_dir = copy_sample(tmp_path)
    manifest_path = task_dir / "documents_manifest.json"
    manifest = load(manifest_path)
    manifest["documents"][0]["sha256"] = "f" * 64
    dump(manifest_path, manifest)
    assert_fails(v8_schema_and_hashes(task_dir))


def test_v9_catches_canary_deviation(tmp_path: Path) -> None:
    task_dir = copy_sample(tmp_path)
    planted_path = task_dir / "planted_deviations.json"
    planted = load(planted_path)
    planted["deviations"][0]["rule_id"] = "R-013"
    dump(planted_path, planted)
    assert_fails(v9_canary_empty(task_dir))


def test_v10_catches_constant_tranche_patterns(tmp_path: Path) -> None:
    tranche = tmp_path / "tranche"
    shutil.copytree(SAMPLE, tranche / "A")
    shutil.copytree(SAMPLE, tranche / "B")
    assert_fails(v10_leakage_scan(tranche))
