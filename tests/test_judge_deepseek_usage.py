from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import scoring.judge_deepseek as judge_deepseek
from scoring.judge_deepseek import DeepSeekJudge


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_chat_records_usage_totals_and_jsonl(monkeypatch: Any, tmp_path: Path) -> None:
    _reset_usage()
    log_path = tmp_path / "judge_usage.jsonl"
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("REDLINE_JUDGE_USAGE_LOG", str(log_path))

    def fake_urlopen(*_: object, **__: object) -> _FakeResponse:
        return _FakeResponse(
            {
                "usage": {"prompt_tokens": 11, "completion_tokens": 7},
                "choices": [{"message": {"content": "PASS"}, "finish_reason": "stop"}],
            }
        )

    monkeypatch.setattr(judge_deepseek.urllib.request, "urlopen", fake_urlopen)

    assert DeepSeekJudge()._chat("prompt") == "PASS"
    assert DeepSeekJudge.usage_totals() == {"prompt_tokens": 11, "completion_tokens": 7, "calls": 1}
    assert json.loads(log_path.read_text()) == {
        "ts_call": 1,
        "model": judge_deepseek.MODEL,
        "prompt_tokens": 11,
        "completion_tokens": 7,
    }


def test_chat_records_every_response_when_length_retry_occurs(monkeypatch: Any, tmp_path: Path) -> None:
    _reset_usage()
    log_path = tmp_path / "judge_usage.jsonl"
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("REDLINE_JUDGE_USAGE_LOG", str(log_path))
    responses = iter(
        [
            {
                "usage": {"prompt_tokens": 2, "completion_tokens": 3},
                "choices": [{"message": {"content": ""}, "finish_reason": "length"}],
            },
            {
                "usage": {"prompt_tokens": 5, "completion_tokens": 7},
                "choices": [{"message": {"content": "PASS"}, "finish_reason": "stop"}],
            },
        ]
    )

    def fake_urlopen(*_: object, **__: object) -> _FakeResponse:
        return _FakeResponse(next(responses))

    monkeypatch.setattr(judge_deepseek.urllib.request, "urlopen", fake_urlopen)

    assert DeepSeekJudge()._chat("prompt", max_tokens=10) == "PASS"
    assert DeepSeekJudge.usage_totals() == {"prompt_tokens": 7, "completion_tokens": 10, "calls": 2}
    lines = [json.loads(line) for line in log_path.read_text().splitlines()]
    assert [line["ts_call"] for line in lines] == [1, 2]


def test_stubbed_chat_can_meter_usage_without_api() -> None:
    _reset_usage()

    class StubJudge(DeepSeekJudge):
        def _chat(self, prompt: str, max_tokens: int = 2000) -> str:
            self._record_usage({"prompt_tokens": len(prompt), "completion_tokens": 4}, "stub-model")
            return "PASS"

    assert StubJudge()._chat("abc") == "PASS"
    assert DeepSeekJudge.usage_totals() == {"prompt_tokens": 3, "completion_tokens": 4, "calls": 1}


def _reset_usage() -> None:
    DeepSeekJudge._usage = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0}
