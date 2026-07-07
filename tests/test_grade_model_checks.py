from __future__ import annotations

import json
from pathlib import Path

from scripts.grade_model_checks import grade_task, update_summary
from scripts.run_model_checks import parse_json_response


def test_grade_model_checks_from_fixture_json(tmp_path: Path) -> None:
    task_dir = tmp_path / "T2-NDA-999"
    checks = task_dir / "model_checks"
    checks.mkdir(parents=True)
    _dump(
        task_dir / "task.json",
        {
            "difficulty_tier": "T2",
        },
    )
    _dump(
        task_dir / "planted_deviations.json",
        {
            "deviations": [
                {"rule_id": "R-001", "clause_anchor": {"section": "2"}},
                {"rule_id": "R-002", "clause_anchor": {"section": "5"}},
            ],
            "missing_info": [
                {
                    "topic": "Personal data handling instructions",
                    "match_keywords": ["personal data", "privacy"],
                },
                {
                    "topic": "Certified deletion evidence at exit",
                    "match_keywords": ["deletion", "certificate"],
                },
            ],
        },
    )
    _dump(checks / "V3_clean_base.json", {"verdict": "PASS", "violations": []})
    _dump(
        checks / "V4_round_trip.json",
        {
            "found": [
                {"rule_id": "R-001", "section": "2", "quote": "a"},
                {"rule_id": "R-999", "section": "7", "quote": "extra"},
            ]
        },
    )
    _dump(
        checks / "V7_semantic.json",
        {"gaps": ["personal data handling instructions are absent", "certified deletion evidence"]},
    )
    _dump(checks / "V11_realism.json", {"score": 8, "weakest": []})

    row = grade_task(task_dir)

    assert row["v3"] == "PASS"
    assert row["v4_matched"] == 1
    assert row["v4_total"] == 2
    assert row["v4_gate"] == "FAIL"
    assert row["v4_extra"] == 1
    assert row["v7"] == "PASS"
    assert row["v11"] == "PASS"


def test_update_summary_replaces_existing_row(tmp_path: Path) -> None:
    summary = tmp_path / "summary.md"
    row = {
        "task": "tasks/generated/T1-NDA-101",
        "v3": "PASS",
        "v4_recall": 1.0,
        "v4_matched": 2,
        "v4_total": 2,
        "v4_extra": 0,
        "v4_gate": "PASS",
        "v7": "PASS",
        "v7_uncovered": [],
        "v11": "PASS",
        "v11_score": 9,
    }
    update_summary(row, summary)
    changed = dict(row, v4_matched=1, v4_extra=1, v11_score=8)
    update_summary(changed, summary)

    text = summary.read_text()
    assert text.count("tasks/generated/T1-NDA-101") == 1
    assert "| tasks/generated/T1-NDA-101 | PASS | 1/2 | PASS | 1 | PASS | 8.0 |" in text


def test_parse_json_response_tolerates_fenced_json() -> None:
    assert parse_json_response('```json\n{"score": 9, "weakest": []}\n```') == {"score": 9, "weakest": []}


def _dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")
