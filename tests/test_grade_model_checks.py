from __future__ import annotations

import json
from pathlib import Path

from scripts.grade_model_checks import grade_task, update_summary
from scripts.run_model_checks import aggregate_v4_samples, aggregate_v11_samples, parse_json_response


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
                {
                    "rule_id": "R-001",
                    "clause_anchor": {"section": "2"},
                    "mutated_text": "Section two has a planted one-sided confidentiality carveout.",
                },
                {
                    "rule_id": "R-002",
                    "clause_anchor": {"section": "5"},
                    "mutated_text": "Vendor may retain customer data for service improvement analytics after termination.",
                },
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
            "found_union": [
                {"rule_id": "R-001", "section": "2", "quote": "a"},
                {
                    "rule_id": "R-002",
                    "section": "9",
                    "quote": "retain customer data for service improvement analytics",
                },
                {"rule_id": "R-999", "section": "7", "quote": "extra"},
            ],
            "found_stable": [
                {"rule_id": "R-001", "section": "2,6", "quote": "a"},
                {"rule_id": "R-999", "section": "7", "quote": "extra"},
            ],
        },
    )
    _dump(
        checks / "V7_semantic.json",
        {"gaps": ["personal data handling instructions are absent", "certified deletion evidence"]},
    )
    _dump(checks / "V11_realism.json", {"scores": [9, 8, 9], "median": 9, "spread": 1, "weakest_union": []})

    row = grade_task(task_dir)

    assert row["v3"] == "PASS"
    assert row["v4_matched"] == 2
    assert row["v4_total"] == 2
    assert row["v4_gate"] == "PASS"
    assert row["v4_extra"] == 1
    assert row["v7"] == "PASS"
    assert row["v11"] == "PASS"
    assert row["v11_score"] == 9
    assert row["v11_spread"] == 1


def test_v4_union_and_stable_aggregation() -> None:
    aggregate = aggregate_v4_samples(
        [
            {
                "found": [
                    {"rule_id": "R-001", "section": "2", "quote": "first"},
                    {"rule_id": "R-002", "section": "5", "quote": "one-off"},
                ]
            },
            {"found": [{"rule_id": "R-001", "section": "2", "quote": "second"}]},
            {
                "found": [
                    {"rule_id": "R-001", "section": "2", "quote": "third"},
                    {"rule_id": "R-003", "section": "8", "quote": "one-off"},
                ]
            },
        ]
    )

    assert [(item["rule_id"], item["section"]) for item in aggregate["found_union"]] == [
        ("R-001", "2"),
        ("R-002", "5"),
        ("R-003", "8"),
    ]
    assert [(item["rule_id"], item["section"]) for item in aggregate["found_stable"]] == [("R-001", "2")]


def test_v11_spread_marks_unstable_summary_cell(tmp_path: Path) -> None:
    task_dir = tmp_path / "T1-NDA-998"
    checks = task_dir / "model_checks"
    checks.mkdir(parents=True)
    _dump(task_dir / "task.json", {"difficulty_tier": "T1"})
    _dump(
        task_dir / "planted_deviations.json",
        {
            "deviations": [
                {
                    "rule_id": "R-001",
                    "clause_anchor": {"section": "2"},
                    "mutated_text": "The recipient may disclose confidential information without notice.",
                }
            ],
            "missing_info": [],
        },
    )
    _dump(checks / "V3_clean_base.json", {"verdict": "PASS", "violations": []})
    _dump(
        checks / "V4_round_trip.json",
        {
            "found_union": [{"rule_id": "R-001", "section": "2", "quote": "disclose confidential information"}],
            "found_stable": [],
        },
    )
    _dump(checks / "V7_semantic.json", {"gaps": []})
    _dump(checks / "V11_realism.json", aggregate_v11_samples([
        {"score": 9, "weakest": ["numbering"]},
        {"score": 6, "weakest": ["cross-reference"]},
        {"score": 3, "weakest": ["numbering"]},
    ]))

    row = grade_task(task_dir)
    summary = tmp_path / "summary.md"
    update_summary(row, summary)

    assert row["v11"] == "UNSTABLE"
    assert row["v11_score"] == 6
    assert row["v11_spread"] == 6
    assert "UNSTABLE 6.0 (6)" in summary.read_text()


def test_quote_overlap_matches_planted_deviation_when_section_differs(tmp_path: Path) -> None:
    task_dir = tmp_path / "T2-DPA-997"
    checks = task_dir / "model_checks"
    checks.mkdir(parents=True)
    _dump(task_dir / "task.json", {"difficulty_tier": "T2"})
    _dump(
        task_dir / "planted_deviations.json",
        {
            "deviations": [
                {
                    "rule_id": "R-004",
                    "clause_anchor": {"section": "3"},
                    "mutated_text": (
                        "Vendor will notify Customer only after confirmed outbound extraction "
                        "is proven by a completed forensic report."
                    ),
                }
            ],
            "missing_info": [],
        },
    )
    _dump(checks / "V3_clean_base.json", {"verdict": "PASS", "violations": []})
    _dump(
        checks / "V4_round_trip.json",
        {
            "found_union": [
                {
                    "rule_id": "R-004",
                    "section": "2,6",
                    "quote": "confirmed outbound extraction is proven by a completed forensic report",
                }
            ],
            "found_stable": [],
        },
    )
    _dump(checks / "V7_semantic.json", {"gaps": []})
    _dump(checks / "V11_realism.json", {"score": 8, "weakest": []})

    row = grade_task(task_dir)

    assert row["v4_matched"] == 1
    assert row["v4_gate"] == "PASS"


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
        "v11_median": 9,
        "v11_spread": 0,
    }
    update_summary(row, summary)
    changed = dict(row, v4_matched=1, v4_extra=1, v11_score=8, v11_median=8, v11_spread=1)
    update_summary(changed, summary)

    text = summary.read_text()
    assert text.count("tasks/generated/T1-NDA-101") == 1
    assert "| tasks/generated/T1-NDA-101 | PASS | 1/2 | PASS | 1 | PASS | 8.0 (1) |" in text


def test_parse_json_response_tolerates_fenced_json() -> None:
    assert parse_json_response('```json\n{"score": 9, "weakest": []}\n```') == {"score": 9, "weakest": []}


def _dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")
