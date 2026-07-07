from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from validators.model_checks import ModelCheck

from .judge_claude_sub import fallback_tiebreak_prompt, validator_prompt

# Judge lane switched from sonnet-on-subscription to DeepSeek v4 Pro
# (Aaron, 2026-07-06 — Claude subscription monthly cap hit). Post-hoc only;
# never called inside a live episode (SPEC invariant 5 unchanged).
BASE_URL = "https://api.deepseek.com"
MODEL = os.getenv("REDLINE_JUDGE_MODEL", "deepseek-v4-pro")
GATE_MESSAGE = "DEEPSEEK_API_KEY not set; judge calls are gated on the lab serving lane"


class DeepSeekJudge(ModelCheck):
    _usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0}

    @classmethod
    def usage_totals(cls) -> dict[str, int]:
        return dict(cls._usage)

    def fallback_tiebreak_judge(self, proposed: str, expected: str, *_: Any, **__: Any) -> bool:
        output = self._chat(fallback_tiebreak_prompt(proposed, expected))
        upper = output.upper()
        return "PASS" in upper and "FAIL" not in upper

    def clean_base_judge_pass(self, task_text: str = "", playbook_text: str = "", *_: Any, **__: Any) -> str:
        return self._chat(validator_prompt("V3 clean-base", task_text, playbook_text))

    def round_trip_extractor(self, task_text: str = "", playbook_text: str = "", *_: Any, **__: Any) -> str:
        return self._chat(validator_prompt("V4 round-trip detectability", task_text, playbook_text))

    def missing_info_semantic_search(self, task_text: str = "", playbook_text: str = "", *_: Any, **__: Any) -> str:
        return self._chat(validator_prompt("V7-semantic missing-info", task_text, playbook_text))

    def realism_judge(self, task_text: str = "", playbook_text: str = "", *_: Any, **__: Any) -> str:
        return self._chat(validator_prompt("V11 realism/coherence", task_text, playbook_text))

    def _chat(self, prompt: str, max_tokens: int = 2000) -> str:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError(GATE_MESSAGE)
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": max_tokens,
        }
        last_exc: Exception | None = None
        for _ in range(2):
            try:
                request = urllib.request.Request(
                    f"{BASE_URL}/chat/completions",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=300) as response:
                    data = json.loads(response.read().decode("utf-8"))
                self._record_usage(data.get("usage"), payload["model"])
                choice = data["choices"][0]
                content = choice["message"].get("content") or ""
                if not content and choice.get("finish_reason") == "length":
                    # Reasoning model spent the whole budget thinking; one
                    # retry with triple the cap (bug class: empty-content-on-length).
                    if max_tokens < 30000:
                        return self._chat(prompt, max_tokens=max_tokens * 3)
                    raise RuntimeError("DeepSeek returned empty content at max budget")
                return content
            except (urllib.error.URLError, OSError) as exc:
                last_exc = exc
        raise RuntimeError(f"DeepSeek judge request failed: {last_exc}") from last_exc

    @classmethod
    def _record_usage(cls, usage: Any, model: str) -> None:
        usage = usage if isinstance(usage, dict) else {}
        prompt_tokens = _int_token_count(usage.get("prompt_tokens"))
        completion_tokens = _int_token_count(usage.get("completion_tokens"))
        cls._usage["prompt_tokens"] += prompt_tokens
        cls._usage["completion_tokens"] += completion_tokens
        cls._usage["calls"] += 1

        log_path = os.getenv("REDLINE_JUDGE_USAGE_LOG")
        if not log_path:
            return
        parent = os.path.dirname(log_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        record = {
            "ts_call": cls._usage["calls"],
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")


def _int_token_count(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
