from __future__ import annotations

from typing import Any

import pytest

from scripts.rule_consensus import ERROR_STATUS, RESPONDED_STATUS, SKIPPED_STATUS, consensus_verdict, parse_provider_json


@pytest.fixture
def provider_result() -> Any:
    def _make(status: str, agree: bool | None, reason: str = "standard practice reason") -> dict[str, Any]:
        return {"status": status, "agree": agree, "reason": reason}

    return _make


def test_parse_provider_json_tolerates_fences_and_minimax_think_prefix() -> None:
    fenced = '```json\n{"agree": true, "reason": "Common market practice supports this."}\n```'
    minimax = (
        "<think>private chain of thought</think>\n"
        '{"agree": false, "reason": "Standard company practice would not accept this risk."}'
    )

    assert parse_provider_json(fenced) == {
        "agree": True,
        "reason": "Common market practice supports this.",
    }
    assert parse_provider_json(minimax, strip_think_prefix=True) == {
        "agree": False,
        "reason": "Standard company practice would not accept this risk.",
    }


def test_parse_provider_json_rejects_wrong_shape() -> None:
    with pytest.raises(ValueError):
        parse_provider_json('{"agree": "yes", "reason": "bad"}')


def test_consensus_verdict_requires_two_responding_agreements(provider_result: Any) -> None:
    assert (
        consensus_verdict(
            {
                "deepseek": provider_result(RESPONDED_STATUS, True),
                "glm": provider_result(RESPONDED_STATUS, True),
                "minimax": provider_result(SKIPPED_STATUS, None),
            }
        )
        == "ENDORSED"
    )
    assert (
        consensus_verdict(
            {
                "deepseek": provider_result(RESPONDED_STATUS, True),
                "glm": provider_result(SKIPPED_STATUS, None),
                "minimax": provider_result(ERROR_STATUS, None),
            }
        )
        == "DISSENT"
    )
    assert (
        consensus_verdict(
            {
                "deepseek": provider_result(RESPONDED_STATUS, True),
                "glm": provider_result(RESPONDED_STATUS, False, "Not standard."),
                "minimax": provider_result(RESPONDED_STATUS, True),
            }
        )
        == "DISSENT"
    )
