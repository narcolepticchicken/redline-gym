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
TELEMETRY_KEYS = {
    "flag_action_count",
    "card_issue_count",
    "union_finding_count",
    "escalation_count",
    "duplicate_finding_count",
    "flags_per_matched_deviation",
    "mean_exact_quote_chars",
    "mean_proposed_redline_chars",
    "filing_channel",
    "distractor_hits",
    "per_category",
}
TAXONOMY = {
    "risk_allocation",
    "data_protection",
    "commercial_terms",
    "ip_rights",
    "compliance",
    "process",
}
NON_TELEMETRY_KEYS = {
    "composite",
    "channels",
    "weights",
    "scorer_version",
    "status",
    "false_flags",
    "matched_deviation_ids",
}


def _without_telemetry(result: dict) -> dict:
    return {key: result[key] for key in NON_TELEMETRY_KEYS}


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


def test_telemetry_fields_are_present_and_sane_for_interactive_card_none_and_mixed() -> None:
    interactive = score_episode(
        SAMPLE,
        flags=[SAMPLE_FLAG],
        escalations=[],
        card={"summary": "One issue", "issues": [], "escalations": []},
    )["telemetry"]
    assert set(interactive) == TELEMETRY_KEYS
    assert interactive["flag_action_count"] == 1
    assert interactive["card_issue_count"] == 0
    assert interactive["union_finding_count"] == 1
    assert interactive["escalation_count"] == 0
    assert interactive["duplicate_finding_count"] == 0
    assert interactive["flags_per_matched_deviation"] == 1.0
    assert interactive["mean_exact_quote_chars"] == float(len(SAMPLE_FLAG["exact_quote"]))
    assert interactive["mean_proposed_redline_chars"] == float(len(SAMPLE_FLAG["proposed_redline"]))
    assert interactive["filing_channel"] == "interactive"
    assert interactive["distractor_hits"] == 0
    assert interactive["per_category"] == {
        "data_protection": {"planted": 4, "matched": 1},
        "process": {"planted": 2, "matched": 0},
    }

    card_only = score_episode(
        SAMPLE,
        flags=[],
        escalations=[],
        card={"summary": "One issue", "issues": [SAMPLE_FLAG], "escalations": []},
        scorer_v2=True,
    )["telemetry"]
    assert card_only["flag_action_count"] == 0
    assert card_only["card_issue_count"] == 1
    assert card_only["union_finding_count"] == 1
    assert card_only["filing_channel"] == "card_only"

    none = score_episode(SAMPLE, flags=[], escalations=[], card={})["telemetry"]
    assert none["filing_channel"] == "none"
    assert none["flags_per_matched_deviation"] is None
    assert none["mean_exact_quote_chars"] is None
    assert none["mean_proposed_redline_chars"] is None

    mixed = score_episode(
        SAMPLE,
        flags=[SAMPLE_FLAG],
        escalations=[],
        card={"summary": "Two channels", "issues": [CARD_ONLY_ISSUES[1]], "escalations": []},
        scorer_v2=True,
    )["telemetry"]
    assert mixed["flag_action_count"] == 1
    assert mixed["card_issue_count"] == 1
    assert mixed["union_finding_count"] == 2
    assert mixed["filing_channel"] == "mixed"
    assert mixed["per_category"]["data_protection"] == {"planted": 4, "matched": 2}


def test_duplicate_finding_count_uses_raw_flag_and_card_issue_overlap() -> None:
    result = score_episode(
        SAMPLE,
        flags=[SAMPLE_FLAG],
        escalations=[],
        card={"summary": "Duplicate issue", "issues": [SAMPLE_FLAG], "escalations": []},
        scorer_v2=True,
    )

    assert result["telemetry"]["duplicate_finding_count"] >= 1
    assert result["telemetry"]["union_finding_count"] == 1


def test_telemetry_does_not_change_pinned_reward_path_shape() -> None:
    result = score_episode(
        SAMPLE,
        flags=[SAMPLE_FLAG],
        escalations=[],
        card={"summary": "One issue", "issues": [], "escalations": []},
    )

    assert _without_telemetry(result) == {
        "composite": 0.488333,
        "channels": {
            "recall": 1 / 6,
            "precision": 1.0,
            "grounding": 1.0,
            "fallback": 0.2,
            "conformance": 1.0,
            "abstention": 0.0,
        },
        "weights": {
            "recall": 0.35,
            "precision": 0.15,
            "grounding": 0.15,
            "fallback": 0.15,
            "conformance": 0.10,
            "abstention": 0.10,
        },
        "scorer_version": "v1",
        "status": "OK",
        "false_flags": 0,
        "matched_deviation_ids": ["D-001"],
    }


def test_rule_category_mapping_covers_every_non_canary_rule_once() -> None:
    categories = json.loads((ROOT / "scoring/rule_categories.json").read_text())
    playbook_paths = sorted((ROOT / "playbooks").glob("*/PB-*.json"))
    total_non_canary_rules = 0
    total_mapped_rules = sum(
        len(mapping) for playbook_id, mapping in categories.items() if not playbook_id.startswith("_")
    )

    assert len(playbook_paths) == 8
    for path in playbook_paths:
        playbook = json.loads(path.read_text())
        category_map = categories[playbook["playbook_id"]]
        for rule in playbook["rules"]:
            if rule["is_canary"]:
                continue
            total_non_canary_rules += 1
            assert rule["rule_id"] in category_map
            assert category_map[rule["rule_id"]] in TAXONOMY

    assert total_non_canary_rules == 103
    assert total_non_canary_rules == total_mapped_rules


def test_rule_category_mapping_excludes_canaries_for_every_playbook() -> None:
    categories = json.loads((ROOT / "scoring/rule_categories.json").read_text())

    for path in sorted((ROOT / "playbooks").glob("*/PB-*.json")):
        playbook = json.loads(path.read_text())
        category_map = categories[playbook["playbook_id"]]
        for rule in playbook["rules"]:
            if rule["is_canary"]:
                assert rule["rule_id"] not in category_map

    assert "R-014" not in categories["PB-MSA-001"]
    assert "R-015" not in categories["PB-MSA-001"]
