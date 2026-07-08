from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any

from env import Episode

from .common import default_run_dir, finalize_card, parser


DEFAULT_BASE_URL = "https://api.z.ai/api/coding/paas/v4"
DEFAULT_MODEL = "glm-5.2"
DEFAULT_KEY_ENV = "GLM_API_KEY"
DRIVER_CONVERSATION = "driver_conversation.jsonl"


def _base_url() -> str:
    return os.getenv("REDLINE_AGENT_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _model() -> str:
    return os.getenv("REDLINE_AGENT_MODEL", DEFAULT_MODEL)


def _key_env() -> str:
    return os.getenv("REDLINE_AGENT_KEY_ENV", DEFAULT_KEY_ENV)


def _temperature() -> float:
    value = os.getenv("REDLINE_AGENT_TEMPERATURE", "0")
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"REDLINE_AGENT_TEMPERATURE must be numeric, got {value!r}") from exc


def _gate_message() -> str:
    return f"{_key_env()} not set; agent baselines are gated on the lab serving lane"


def run_llm_baseline(name: str, system_prompt: str, argv: list[str] | None = None) -> int:
    args = parser(name).parse_args(argv)
    try:
        result = run_llm_episode(
            name=name,
            system_prompt=system_prompt,
            task=args.task,
            seed=args.seed,
            run_dir=args.run_dir or default_run_dir(name, args.seed),
        )
    except MissingAgentKeyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result["score"], indent=2, sort_keys=True))
    print(json.dumps({"usage": result["usage"]}, sort_keys=True))
    return 0


class MissingAgentKeyError(RuntimeError):
    pass


def run_llm_episode(
    *,
    name: str,
    system_prompt: str,
    task: str | Path,
    seed: int,
    run_dir: str | Path,
) -> dict[str, Any]:
    """Run one LLM episode through the same driver used by the CLI baseline."""
    key_env = _key_env()
    api_key = os.getenv(key_env)
    if not api_key:
        raise MissingAgentKeyError(_gate_message())
    episode = Episode(task, seed=seed, run_dir=run_dir)
    observation = episode.reset()
    flags: list[dict[str, Any]] = []
    escalations: list[dict[str, Any]] = []
    # Full conversation history so the agent remembers prior tool results —
    # a memoryless driver would measure the harness, not the model.
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0}
    conversation_path = episode.episode_dir / DRIVER_CONVERSATION
    conversation_path.write_text(json.dumps({"role": "system", "content": system_prompt}, sort_keys=True) + "\n")
    while not observation.get("done"):
        user_content = observation_prompt(observation)
        messages.append({"role": "user", "content": user_content})
        action, raw = _next_action(api_key, messages, usage)
        salvage_finalize = False
        if action is None:
            # Two malformed replies in a row: salvage the episode with what we have.
            action = {"action": "finalize", "card": finalize_card(flags, escalations, "LLM baseline completed review.")}
            raw = json.dumps(action)
            salvage_finalize = True
        messages.append({"role": "assistant", "content": raw})
        if action.get("action") == "flag_issue":
            flags.append({k: v for k, v in action.items() if k != "action"})
        elif action.get("action") == "escalate":
            escalations.append({"topic": str(action.get("topic", "")), "reason": str(action.get("reason", ""))})
        elif action.get("action") == "finalize" and "card" not in action:
            action["card"] = finalize_card(flags, escalations, "LLM baseline completed review.")
        observation = episode.step(action)
        with conversation_path.open("a") as fh:
            fh.write(json.dumps({"role": "user", "turn": episode.num_turns, "content": user_content}, sort_keys=True) + "\n")
            fh.write(
                json.dumps(
                    {
                        "role": "assistant",
                        "turn": episode.num_turns,
                        "content": raw,
                        "salvage_finalize": salvage_finalize,
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
    (Path(run_dir) / "usage.json").write_text(json.dumps(usage, indent=2, sort_keys=True))
    (episode.episode_dir / "usage.json").write_text(json.dumps(usage, indent=2, sort_keys=True))
    return {
        "score": json.loads(episode.score_path.read_text()),
        "usage": usage,
        "run_dir": str(episode.episode_dir),
        "score_path": str(episode.score_path),
        "conversation_path": str(conversation_path),
        "name": name,
    }


def observation_prompt(observation: dict[str, Any]) -> str:
    return (
        "Return exactly one JSON action object for this Redline Gym observation. "
        "Allowed actions: list_docs, read_doc, search, flag_issue, escalate, finalize. "
        "flag_issue requires rule_id, doc_id, clause_ref, and exact_quote "
        "(verbatim text copied from the document); include proposed_redline "
        "when the playbook prescribes an edit. finalize requires card shaped as "
        "{issues: [{rule_id, doc_id, clause_ref, exact_quote, proposed_redline?}], "
        "escalations: [{topic, reason}], summary: string}.\n\n"
        + json.dumps(observation, sort_keys=True)
    )


def _next_action(
    api_key: str, messages: list[dict[str, str]], usage: dict[str, int]
) -> tuple[dict[str, Any] | None, str]:
    """One model turn with a single corrective retry on malformed output."""
    raw = _chat(api_key, messages, usage)
    try:
        return _parse_action(raw), raw
    except ValueError:
        retry = messages + [
            {"role": "assistant", "content": raw},
            {"role": "user", "content": "That was not a single valid JSON action object. Reply with ONLY the JSON object."},
        ]
        raw2 = _chat(api_key, retry, usage)
        try:
            return _parse_action(raw2), raw2
        except ValueError:
            return None, raw2


def _chat(api_key: str, messages: list[dict[str, str]], usage: dict[str, int]) -> str:
    import urllib.error
    import urllib.request

    payload = {
        "model": _model(),
        "messages": messages,
        "temperature": _temperature(),
        "max_tokens": int(os.getenv("REDLINE_AGENT_MAX_TOKENS", "4000")),
    }
    request = urllib.request.Request(
        f"{_base_url()}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    import time

    last_exc: Exception | None = None
    for attempt in range(3):  # retries with backoff on transient errors incl. read timeouts
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                data = json.loads(response.read().decode("utf-8"))
            u = data.get("usage") or {}
            usage["prompt_tokens"] += int(u.get("prompt_tokens", 0))
            usage["completion_tokens"] += int(u.get("completion_tokens", 0))
            usage["calls"] += 1
            # Thinking models may omit/empty `content` when reasoning exhausts
            # the budget; return "" and let the corrective-retry path handle it.
            return data["choices"][0]["message"].get("content") or ""
        except (urllib.error.URLError, OSError) as exc:
            last_exc = exc
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"GLM baseline request failed: {last_exc}") from last_exc


def _parse_action(content: str) -> dict[str, Any]:
    import re as _re
    content = _re.sub(r"^\s*<think>.*?</think>\s*", "", content, count=1, flags=_re.DOTALL | _re.IGNORECASE)
    try:
        action = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"model did not return a JSON action: {content}")
        action = json.loads(content[start : end + 1])
    if not isinstance(action, dict):
        raise ValueError("model action must be a JSON object")
    return action
