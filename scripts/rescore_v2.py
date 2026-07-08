#!/usr/bin/env python3
"""Post-hoc deterministic rescore of stored episodes with v0.2 union semantics.

Reads each <run_dir>/<task_id>/episode.jsonl, reconstructs flags/escalations/
card, scores v1 and v2 locally, writes score_v2.json next to score.json, and
prints the composite delta. Fallback uses deterministic exact-match scoring only;
no judge/model tiebreak is called in this pass.

Usage: python3 scripts/rescore_v2.py runs/honest_llm-seed0 [more run dirs]
"""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from scoring.core import score_episode  # noqa: E402


def _task_dir(task_id: str) -> pathlib.Path | None:
    candidates = [
        pathlib.Path("tasks/contracts") / task_id,
        pathlib.Path("tasks/generated") / task_id,
    ]
    return next((candidate for candidate in candidates if candidate.exists()), None)


def _reconstruct(transcript: pathlib.Path) -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, Any] | None]:
    flags: list[dict[str, Any]] = []
    escalations: list[dict[str, str]] = []
    card: dict[str, Any] | None = None
    for line in transcript.read_text().splitlines():
        action = json.loads(line).get("action", {})
        kind = action.get("action")
        if kind == "flag_issue":
            flags.append({key: value for key, value in action.items() if key != "action"})
        elif kind == "escalate":
            escalations.append({"topic": str(action.get("topic", "")), "reason": str(action.get("reason", ""))})
        elif kind == "finalize" and isinstance(action.get("card"), dict):
            card = action["card"]
    return flags, escalations, card


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: python3 scripts/rescore_v2.py <run_dir> [more run dirs]", file=sys.stderr)
        return 2

    print("v2 deterministic rescore: fallback exact-match only; no judge/model tiebreak")
    for run_arg in argv:
        for transcript in sorted(pathlib.Path(run_arg).glob("*/episode.jsonl")):
            task_id = transcript.parent.name
            task_dir = _task_dir(task_id)
            if task_dir is None:
                print(f"skip {task_id}: no task dir found")
                continue
            flags, escalations, card = _reconstruct(transcript)
            v1 = score_episode(task_dir, flags, escalations, card, allow_model_tiebreak=False, scorer_v2=False)
            v2 = score_episode(task_dir, flags, escalations, card, allow_model_tiebreak=False, scorer_v2=True)
            out = transcript.parent / "score_v2.json"
            out.write_text(json.dumps(v2, indent=2, sort_keys=True))
            print(f"{run_arg} {task_id}: v1={v1['composite']} v2={v2['composite']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
