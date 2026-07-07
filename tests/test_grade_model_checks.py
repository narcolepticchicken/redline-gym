from __future__ import annotations

import json
from pathlib import Path

from scripts.grade_model_checks import grade_task, update_summary
from scripts.run_model_checks import (
    aggregate_v4_samples,
    aggregate_v7_samples,
    aggregate_v11_samples,
    parse_json_response,
    write_aggregate_from_samples,
)


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
    _dump(
        checks / "V11_realism.json",
        aggregate_v11_samples(
            [
                _v11_sample({"q1": True, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
                _v11_sample({"q1": True, "q2": True, "q3": False, "q4": True, "q5": True, "q6": True}),
                _v11_sample({"q1": True, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
            ],
            mechanical_q1=True,
        ),
    )

    row = grade_task(task_dir)

    assert row["v3"] == "PASS"
    assert row["v4_matched"] == 2
    assert row["v4_total"] == 2
    assert row["v4_gate"] == "PASS"
    assert row["v4_extra"] == 1
    assert row["v7"] == "PASS"
    assert row["v11"] == "PASS"
    assert row["v11_passed"] == 6
    assert row["v11_total"] == 6
    assert row["v11_failing_questions"] == []


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


def test_run_model_checks_writes_v4_aggregate_from_partial_samples(tmp_path: Path) -> None:
    aggregate = write_aggregate_from_samples(
        "V4_round_trip",
        [{"found": [{"rule_id": "R-001", "section": "2", "quote": "first"}]}],
        tmp_path,
        "",
    )

    assert aggregate == {
        "found_union": [{"rule_id": "R-001", "section": "2", "quote": "first"}],
        "found_stable": [],
    }
    assert json.loads((tmp_path / "V4_round_trip.json").read_text()) == aggregate
    assert not (tmp_path / "V4_round_trip.error").exists()


def test_run_model_checks_writes_check_error_when_all_samples_fail(tmp_path: Path) -> None:
    aggregate = write_aggregate_from_samples("V4_round_trip", [], tmp_path, "")

    assert aggregate is None
    assert not (tmp_path / "V4_round_trip.json").exists()
    assert "all samples failed" in (tmp_path / "V4_round_trip.error").read_text()


def test_v7_union_aggregation_deduplicates_gaps() -> None:
    aggregate = aggregate_v7_samples(
        [
            {"gaps": ["current subprocessor list location", "security exhibit"]},
            {"gaps": ["Current Subprocessor List Location", "deletion certificate contact"]},
            {"gaps": ["  ", "subprocessor portal URL"]},
        ]
    )

    assert aggregate == {
        "gaps_union": [
            "current subprocessor list location",
            "security exhibit",
            "deletion certificate contact",
            "subprocessor portal URL",
        ]
    }


def test_v7_grade_matches_keywords_against_any_union_gap(tmp_path: Path) -> None:
    task_dir = tmp_path / "T2-DPA-995"
    checks = task_dir / "model_checks"
    checks.mkdir(parents=True)
    _dump(task_dir / "task.json", {"difficulty_tier": "T2"})
    _dump(
        task_dir / "planted_deviations.json",
        {
            "deviations": [],
            "missing_info": [
                {
                    "topic": "Current subprocessor list location",
                    "match_keywords": ["subprocessor", "portal", "list"],
                }
            ],
        },
    )
    _dump(checks / "V3_clean_base.json", {"verdict": "PASS", "violations": []})
    _dump(checks / "V4_round_trip.json", {"found_union": [], "found_stable": []})
    _dump(checks / "V7_semantic.json", {"gaps_union": ["security exhibit", "subprocessor portal URL"]})
    _dump(
        checks / "V11_realism.json",
        aggregate_v11_samples(
            [
                _v11_sample({"q1": True, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
                _v11_sample({"q1": True, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
                _v11_sample({"q1": True, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
            ]
        ),
    )

    row = grade_task(task_dir)

    assert row["v7"] == "PASS"
    assert row["v7_uncovered"] == []


def test_v7_grade_matches_keyword_phrase_case_insensitive(tmp_path: Path) -> None:
    row = _grade_v7_fixture(
        tmp_path,
        ["earnout scenario"],
        ["The judge identified an EARNOUT SCENARIO diligence gap."],
    )

    assert row["v7"] == "PASS"
    assert row["v7_uncovered"] == []


def test_v7_grade_matches_keyword_word_case_insensitive(tmp_path: Path) -> None:
    row = _grade_v7_fixture(
        tmp_path,
        ["earnout scenario"],
        ["Earnout provision"],
    )

    assert row["v7"] == "PASS"
    assert row["v7_uncovered"] == []


def test_grade_model_checks_marks_missing_v4_aggregate_ungraded(tmp_path: Path) -> None:
    task_dir = tmp_path / "T2-DPA-994"
    checks = task_dir / "model_checks"
    checks.mkdir(parents=True)
    _dump(task_dir / "task.json", {"difficulty_tier": "T2"})
    _dump(
        task_dir / "planted_deviations.json",
        {
            "deviations": [
                {
                    "rule_id": "R-001",
                    "clause_anchor": {"section": "2"},
                    "mutated_text": "Vendor may decide processing purposes.",
                }
            ],
            "missing_info": [],
        },
    )
    _dump(checks / "V3_clean_base.json", {"verdict": "PASS", "violations": []})
    _dump(checks / "V7_semantic.json", {"gaps": []})
    _dump(
        checks / "V11_realism.json",
        aggregate_v11_samples(
            [
                _v11_sample({"q1": True, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
                _v11_sample({"q1": True, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
                _v11_sample({"q1": True, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
            ]
        ),
    )

    row = grade_task(task_dir)
    summary = tmp_path / "summary.md"
    update_summary(row, summary)

    assert row["v4_gate"] == "UNGRADED"
    assert row["v4_recall"] is None
    assert f"| {row['task']} | PASS | UNGRADED | UNGRADED | 0 | PASS | V11 reg 6/6 failing none |" in summary.read_text()


def test_v11_majority_vote_aggregates_and_propagates_failing_evidence() -> None:
    aggregate = aggregate_v11_samples(
        [
            _v11_sample(
                {"q1": True, "q2": True, "q3": False, "q4": True, "q5": True, "q6": True},
                {"q3": "a reasonable while"},
            ),
            _v11_sample(
                {"q1": True, "q2": True, "q3": False, "q4": True, "q5": True, "q6": True},
                {"q3": "the next quarter"},
            ),
            _v11_sample({"q1": False, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
        ],
        mechanical_q1=True,
    )

    assert aggregate["passed"] == 5
    assert aggregate["total"] == 6
    assert aggregate["per_question"]["q1"] == {"passed": True, "yes_votes": 2, "no_votes": 1}
    assert aggregate["per_question"]["q3"] == {"passed": False, "yes_votes": 1, "no_votes": 2}
    assert aggregate["failing_evidence"] == {"q3": ["a reasonable while", "the next quarter"]}
    assert aggregate["mechanical_agreement"]["q1"] == {
        "mechanical_passed": True,
        "judge_passed": True,
        "agrees": True,
    }


def test_v11_gate_passes_at_five_of_six_and_summary_lists_failures(tmp_path: Path) -> None:
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
    _dump(
        checks / "V11_realism.json",
        aggregate_v11_samples(
            [
                _v11_sample({"q1": True, "q2": True, "q3": False, "q4": True, "q5": True, "q6": True}),
                _v11_sample({"q1": True, "q2": True, "q3": False, "q4": True, "q5": True, "q6": True}),
                _v11_sample({"q1": True, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
            ]
        ),
    )

    row = grade_task(task_dir)
    summary = tmp_path / "summary.md"
    update_summary(row, summary)

    assert row["v11"] == "PASS"
    assert row["v11_passed"] == 5
    assert row["v11_failing_questions"] == ["q3"]
    assert "V11 reg 5/6 failing q3" in summary.read_text()


def test_v11_gate_fails_below_five_of_six(tmp_path: Path) -> None:
    task_dir = tmp_path / "T1-NDA-996"
    checks = task_dir / "model_checks"
    checks.mkdir(parents=True)
    _dump(task_dir / "task.json", {"difficulty_tier": "T1"})
    _dump(task_dir / "planted_deviations.json", {"deviations": [], "missing_info": []})
    _dump(checks / "V3_clean_base.json", {"verdict": "PASS", "violations": []})
    _dump(checks / "V4_round_trip.json", {"found_union": [], "found_stable": []})
    _dump(checks / "V7_semantic.json", {"gaps": []})
    _dump(
        checks / "V11_realism.json",
        aggregate_v11_samples(
            [
                _v11_sample({"q1": True, "q2": True, "q3": False, "q4": False, "q5": True, "q6": True}),
                _v11_sample({"q1": True, "q2": True, "q3": False, "q4": False, "q5": True, "q6": True}),
                _v11_sample({"q1": True, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
            ]
        ),
    )

    row = grade_task(task_dir)

    assert row["v11"] == "FAIL"
    assert row["v11_passed"] == 4
    assert row["v11_failing_questions"] == ["q3", "q4"]


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
    _dump(
        checks / "V11_realism.json",
        aggregate_v11_samples(
            [
                _v11_sample({"q1": True, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
                _v11_sample({"q1": True, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
                _v11_sample({"q1": True, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
            ]
        ),
    )

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
        "v11_passed": 6,
        "v11_total": 6,
        "v11_failing_questions": [],
        "v11_score": 6,
    }
    update_summary(row, summary)
    changed = dict(row, v4_matched=1, v4_extra=1, v11="FAIL", v11_passed=4, v11_failing_questions=["q3", "q4"], v11_score=4)
    update_summary(changed, summary)

    text = summary.read_text()
    assert text.count("tasks/generated/T1-NDA-101") == 1
    assert "| tasks/generated/T1-NDA-101 | PASS | 1/2 | PASS | 1 | PASS | V11 reg 4/6 failing q3,q4 |" in text


def test_parse_json_response_tolerates_fenced_json() -> None:
    payload = '{"answers":{"q1":true},"evidence":{"q1":""}}'
    assert parse_json_response(f"```json\n{payload}\n```") == {"answers": {"q1": True}, "evidence": {"q1": ""}}


def _dump(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def _grade_v7_fixture(tmp_path: Path, match_keywords: list[str], gaps: list[str]) -> dict:
    task_dir = tmp_path / "T1-MA-TEST"
    checks = task_dir / "model_checks"
    checks.mkdir(parents=True)
    _dump(task_dir / "task.json", {"difficulty_tier": "T1"})
    _dump(
        task_dir / "planted_deviations.json",
        {
            "deviations": [],
            "missing_info": [
                {
                    "topic": "Earnout issue",
                    "match_keywords": match_keywords,
                }
            ],
        },
    )
    _dump(checks / "V3_clean_base.json", {"verdict": "PASS", "violations": []})
    _dump(checks / "V4_round_trip.json", {"found_union": [], "found_stable": []})
    _dump(checks / "V7_semantic.json", {"gaps_union": gaps})
    _dump(
        checks / "V11_realism.json",
        aggregate_v11_samples(
            [
                _v11_sample({"q1": True, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
                _v11_sample({"q1": True, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
                _v11_sample({"q1": True, "q2": True, "q3": True, "q4": True, "q5": True, "q6": True}),
            ]
        ),
    )
    return grade_task(task_dir)


def _v11_sample(answers: dict[str, bool], evidence: dict[str, str] | None = None) -> dict:
    complete_evidence = {qid: "" for qid in answers}
    complete_evidence.update(evidence or {})
    return {"answers": answers, "evidence": complete_evidence}
