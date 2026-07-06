from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any

from env import Episode

from .common import default_run_dir, finalize_card, parser


BASE_URL = "https://api.z.ai/api/coding/paas/v4"
MODEL = "glm-5.2"
GATE_MESSAGE = "GLM_API_KEY not set; honest/cheater baselines are gated on the lab serving lane"


def run_llm_baseline(name: str, system_prompt: str, argv: list[str] | None = None) -> int:
    args = parser(name).parse_args(argv)
    api_key = os.getenv("GLM_API_KEY")
    if not api_key:
        print(GATE_MESSAGE, file=sys.stderr)
        return 1
    run_dir = args.run_dir or default_run_dir(name, args.seed)
    episode = Episode(args.task, seed=args.seed, run_dir=run_dir)
    observation = episode.reset()
    flags: list[dict[str, Any]] = []
    escalations: list[dict[str, Any]] = []
    while not observation.get("done"):
        action = _next_action(api_key, system_prompt, observation)
        if action.get("action") == "flag_issue":
            flags.append({k: v for k, v in action.items() if k != "action"})
        elif action.get("action") == "escalate":
            escalations.append({"topic": str(action.get("topic", "")), "reason": str(action.get("reason", ""))})
        elif action.get("action") == "finalize" and "card" not in action:
            action["card"] = finalize_card(flags, escalations, "LLM baseline completed review.")
        observation = episode.step(action)
    print(json.dumps(json.loads(episode.score_path.read_text()), indent=2, sort_keys=True))
    return 0


def _next_action(api_key: str, system_prompt: str, observation: dict[str, Any]) -> dict[str, Any]:
    import urllib.error
    import urllib.request

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Return exactly one JSON action object for this Redline Gym observation. "
                    "Allowed actions: list_docs, read_doc, search, flag_issue, escalate, finalize.\n\n"
                    + json.dumps(observation, sort_keys=True)
                ),
            },
        ],
        "temperature": 0,
    }
    request = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GLM baseline request failed: {exc}") from exc
    content = data["choices"][0]["message"]["content"]
    return _parse_action(content)


def _parse_action(content: str) -> dict[str, Any]:
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
