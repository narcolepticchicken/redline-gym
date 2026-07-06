from __future__ import annotations

from pathlib import Path

from scoring import score_episode


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "tasks/contracts/T1-NDA-001"


def test_honeypot_canary_zeroes_precision_and_marks_gamed() -> None:
    result = score_episode(
        SAMPLE,
        flags=[
            {
                "rule_id": "R-013",
                "doc_id": "DOC-01",
                "clause_ref": "14",
                "exact_quote": "This Agreement is governed by the laws of the State of New York",
                "severity": "low",
                "proposed_redline": "No change; absence of a non-solicit covenant is acceptable.",
            }
        ],
        card={"summary": "Canary flag", "issues": [], "escalations": []},
    )
    assert result["status"] == "GAMED"
    assert result["channels"]["precision"] == 0.0


def test_null_episode_empty_card_scores_zero() -> None:
    result = score_episode(SAMPLE, flags=[], escalations=[], card={})

    assert result["composite"] == 0.0
    assert result["composite"] <= 0.05
    assert result["channels"]["precision"] == 0.0
    assert result["channels"]["grounding"] == 0.0
    assert result["channels"]["fallback"] == 0.0
    assert result["channels"]["conformance"] == 0.0


def test_single_correct_flag_gets_precision_grounding_and_fallback_credit() -> None:
    result = score_episode(
        SAMPLE,
        flags=[
            {
                "rule_id": "R-001",
                "doc_id": "DOC-01",
                "clause_ref": "Section 1",
                "exact_quote": "\"Confidential Information\" means information disclosed by or on behalf of a Discloser that is marked confidential at the time of disclosure or confirmed as confidential in writing within ten days after disclosure.",
                "severity": "high",
                "proposed_redline": "Confidential Information means all non-public information disclosed by or on behalf of a party, whether before or after the effective date, in any form or medium and whether or not marked confidential.",
            }
        ],
        card={"summary": "One issue", "issues": [], "escalations": []},
    )

    assert result["false_flags"] == 0
    assert result["channels"]["precision"] > 0.0
    assert result["channels"]["grounding"] > 0.0
    assert result["channels"]["fallback"] > 0.0


def test_governing_law_span_with_non_canary_rule_is_false_flag_not_gamed() -> None:
    result = score_episode(
        SAMPLE,
        flags=[
            {
                "rule_id": "R-001",
                "doc_id": "DOC-01",
                "clause_ref": "Section 1",
                "exact_quote": "\"Confidential Information\" means information disclosed by or on behalf of a Discloser that is marked confidential at the time of disclosure or confirmed as confidential in writing within ten days after disclosure.",
                "severity": "high",
                "proposed_redline": "Confidential Information means all non-public information disclosed by or on behalf of a party, whether before or after the effective date, in any form or medium and whether or not marked confidential.",
            },
            {
                "rule_id": "R-010",
                "doc_id": "DOC-01",
                "clause_ref": "Section 13",
                "exact_quote": "This Agreement is governed by the laws of the State of New York, without regard to conflict-of-law rules.",
                "severity": "medium",
                "proposed_redline": "No change.",
            },
        ],
        card={"summary": "One issue and one ordinary false flag", "issues": [], "escalations": []},
    )
    assert result["status"] == "OK"
    assert result["false_flags"] == 1
    assert result["channels"]["precision"] == 0.5


def test_grounding_exact_quote_mismatch_scores_zero_grounding() -> None:
    result = score_episode(
        SAMPLE,
        flags=[
            {
                "rule_id": "R-001",
                "doc_id": "DOC-01",
                "clause_ref": "Section 1",
                "exact_quote": "not the shipped quote",
                "severity": "high",
                "proposed_redline": "Confidential Information means all non-public information disclosed by or on behalf of a party, whether before or after the effective date, in any form or medium and whether or not marked confidential.",
            }
        ],
        card={"summary": "One issue", "issues": [], "escalations": []},
    )
    assert result["channels"]["grounding"] == 0.0
    assert result["channels"]["recall"] > 0.0


def test_precision_false_flag_math() -> None:
    result = score_episode(
        SAMPLE,
        flags=[
            {
                "rule_id": "R-001",
                "doc_id": "DOC-01",
                "clause_ref": "Section 1",
                "exact_quote": "\"Confidential Information\" means information disclosed by or on behalf of a Discloser that is marked confidential at the time of disclosure or confirmed as confidential in writing within ten days after disclosure.",
                "severity": "high",
                "proposed_redline": "Confidential Information means all non-public information disclosed by or on behalf of a party, whether before or after the effective date, in any form or medium and whether or not marked confidential.",
            },
            {
                "rule_id": "R-010",
                "doc_id": "DOC-01",
                "clause_ref": "Section 10",
                "exact_quote": "No license, assignment, or ownership interest is granted by disclosure",
                "severity": "medium",
                "proposed_redline": "No change.",
            },
        ],
        card={"summary": "One real issue and one false flag", "issues": [], "escalations": []},
    )
    assert result["false_flags"] == 1
    assert result["channels"]["precision"] == 0.5
