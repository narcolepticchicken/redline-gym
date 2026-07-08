from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from baselines.common import finalize_card
from scoring import score_episode


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "tasks/contracts/T1-NDA-001"
SAMPLE_FLAG = {
    "rule_id": "R-001",
    "doc_id": "DOC-01",
    "clause_ref": "Section 1",
    "exact_quote": "\"Confidential Information\" means information disclosed by or on behalf of a Discloser that is marked confidential at the time of disclosure or confirmed as confidential in writing within ten days after disclosure.",
    "severity": "high",
    "proposed_redline": "Confidential Information means all non-public information disclosed by or on behalf of a party, whether before or after the effective date, in any form or medium and whether or not marked confidential.",
    "rationale": "Marked-only coverage is narrower than the playbook requires.",
}
CARD_ONLY_ISSUES = [
    SAMPLE_FLAG,
    {
        "rule_id": "R-005",
        "doc_id": "DOC-01",
        "clause_ref": "Section 4",
        "exact_quote": "Recipient will protect Confidential Information using the same degree of care that it uses to protect its own confidential information of similar importance.",
        "severity": "high",
        "proposed_redline": "Recipient will protect Confidential Information using at least reasonable care and no less than the care it uses to protect its own similar confidential information.",
        "rationale": "The care standard omits the reasonable-care floor.",
    },
    {
        "rule_id": "R-004",
        "doc_id": "DOC-01",
        "clause_ref": "Section 2",
        "exact_quote": "Recipient may use Confidential Information for the Purpose, including to evaluate potential product and commercial opportunities arising from the parties' discussions.",
        "severity": "high",
        "proposed_redline": "The recipient may use Confidential Information solely to evaluate, negotiate, and, if agreed, perform the contemplated transaction between the parties.",
        "rationale": "The use right reaches broader product and commercial opportunities.",
    },
]
CANARY_CARD_ISSUE = {
    "rule_id": "R-014",
    "doc_id": "DOC-01",
    "clause_ref": "Section 13",
    "exact_quote": "This Agreement is governed by the laws of the State of New York, without regard to conflict-of-law rules.",
    "severity": "low",
    "proposed_redline": "No change; New York governing law is acceptable for this smoke-test NDA.",
    "rationale": "This canary should mark the episode gamed when cited as an issue.",
}


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


def test_card_only_issues_default_scoring_scores_zero(monkeypatch) -> None:
    monkeypatch.delenv("REDLINE_SCORER_V2", raising=False)
    result = score_episode(
        SAMPLE,
        flags=[],
        escalations=[],
        card={"summary": "Three issues.", "issues": CARD_ONLY_ISSUES, "escalations": []},
    )

    assert result["scorer_version"] == "v1"
    assert result["composite"] == 0.0
    assert result["channels"] == {
        "recall": 0.0,
        "precision": 0.0,
        "grounding": 0.0,
        "fallback": 0.0,
        "conformance": 0.0,
        "abstention": 0.0,
    }


def test_card_only_issues_v2_score_union_but_not_conformance() -> None:
    result = score_episode(
        SAMPLE,
        flags=[],
        escalations=[],
        card={"summary": "Three issues.", "issues": CARD_ONLY_ISSUES, "escalations": []},
        scorer_v2=True,
    )

    assert result["scorer_version"] == "v2"
    assert result["channels"]["recall"] > 0.0
    assert result["channels"]["grounding"] > 0.0
    assert result["channels"]["fallback"] > 0.0
    assert result["channels"]["conformance"] == 0.0


def test_card_canary_marks_gamed_under_v2() -> None:
    result = score_episode(
        SAMPLE,
        flags=[],
        escalations=[],
        card={"summary": "Canary in card.", "issues": [CANARY_CARD_ISSUE], "escalations": []},
        scorer_v2=True,
    )

    assert result["status"] == "GAMED"
    assert result["channels"]["precision"] == 0.0


def test_v2_deduplicates_same_action_and_card_issue() -> None:
    false_issue = {
        "rule_id": "R-010",
        "doc_id": "DOC-01",
        "clause_ref": "Section 13",
        "exact_quote": "This Agreement is governed by the laws of the State of New York, without regard to conflict-of-law rules.",
        "severity": "medium",
        "proposed_redline": "No change.",
    }
    result = score_episode(
        SAMPLE,
        flags=[SAMPLE_FLAG],
        escalations=[],
        card={"summary": "Duplicate plus false issue.", "issues": [SAMPLE_FLAG, false_issue], "escalations": []},
        scorer_v2=True,
    )

    assert result["false_flags"] == 1
    assert result["channels"]["precision"] == 0.5


def test_valid_card_scores_conformance_one_with_substantive_action() -> None:
    result = score_episode(
        SAMPLE,
        flags=[SAMPLE_FLAG],
        escalations=[],
        card={"summary": "One issue.", "issues": [SAMPLE_FLAG], "escalations": [], "model_notes": "extra key"},
    )

    assert result["channels"]["conformance"] == 1.0


def test_flags_key_instead_of_issues_scores_conformance_zero() -> None:
    result = score_episode(
        SAMPLE,
        flags=[SAMPLE_FLAG],
        escalations=[],
        card={"summary": "One issue.", "flags": [SAMPLE_FLAG], "escalations": []},
    )

    assert result["channels"]["conformance"] == 0.0


def test_finalize_card_output_validates_against_card_schema() -> None:
    schema = json.loads((ROOT / "schema/card.schema.json").read_text())
    validator = Draft202012Validator(schema)
    card = finalize_card([SAMPLE_FLAG], [{"topic": "Term gap", "reason": "Playbook is silent."}], "Done.")

    assert list(validator.iter_errors(card)) == []


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
    assert result["matched_deviation_ids"] == ["D-001"]
    assert result["channels"]["precision"] > 0.0
    assert result["channels"]["grounding"] > 0.0
    assert result["channels"]["fallback"] > 0.0


def test_correct_ids_with_unrelated_grounded_quote_is_false_flag() -> None:
    result = score_episode(
        SAMPLE,
        flags=[
            {
                "rule_id": "R-001",
                "doc_id": "DOC-01",
                "clause_ref": "Section 13",
                "exact_quote": "This Agreement is governed by the laws of the State of New York, without regard to conflict-of-law rules.",
                "severity": "high",
                "proposed_redline": "Confidential Information means all non-public information disclosed by or on behalf of a party, whether before or after the effective date, in any form or medium and whether or not marked confidential.",
            }
        ],
        card={"summary": "Wrong quote", "issues": [], "escalations": []},
    )

    assert result["matched_deviation_ids"] == []
    assert result["false_flags"] == 1
    assert result["channels"]["recall"] == 0.0
    assert result["channels"]["precision"] == 0.0
    assert result["channels"]["grounding"] > 0.0


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
    assert result["channels"]["recall"] == 0.0
    assert result["false_flags"] == 1


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
