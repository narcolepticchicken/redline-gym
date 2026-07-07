#!/usr/bin/env python3
"""Post-hoc rescore of stored episodes with the DeepSeek fallback tiebreak.

Reads each <run_dir>/<task_id>/episode.jsonl, reconstructs flags/escalations/
card, rescores with allow_model_tiebreak=True, writes score_judged.json next
to the deterministic score.json, and prints the delta.

Usage: DEEPSEEK_API_KEY=... python3 scripts/rescore_run.py runs/honest_llm-seed0 [more run dirs]
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from scoring.core import score_episode  # noqa: E402
from scoring.judge_deepseek import DeepSeekJudge  # noqa: E402


def _print_judge_usage() -> None:
    totals = DeepSeekJudge.usage_totals()
    print(
        f"judge usage: {totals['prompt_tokens']} prompt + "
        f"{totals['completion_tokens']} completion tokens across {totals['calls']} calls"
    )


judge = DeepSeekJudge()

try:
    for run_arg in sys.argv[1:]:
        for transcript in sorted(pathlib.Path(run_arg).glob("*/episode.jsonl")):
            task_id = transcript.parent.name
            task_dir = pathlib.Path("tasks/contracts") / task_id
            flags, escalations, card = [], [], None
            for line in transcript.read_text().splitlines():
                action = json.loads(line).get("action", {})
                kind = action.get("action")
                if kind == "flag_issue":
                    flags.append({k: v for k, v in action.items() if k != "action"})
                elif kind == "escalate":
                    escalations.append({"topic": str(action.get("topic", "")), "reason": str(action.get("reason", ""))})
                elif kind == "finalize" and isinstance(action.get("card"), dict):
                    card = action["card"]
            judged = score_episode(task_dir, flags, escalations, card,
                                   model_check=judge, allow_model_tiebreak=True)
            out = transcript.parent / "score_judged.json"
            out.write_text(json.dumps(judged, indent=2, sort_keys=True))
            det_path = transcript.parent / "score.json"
            det = json.load(det_path.open())["composite"] if det_path.exists() else None
            print(f"{run_arg} {task_id}: deterministic={det} judged={judged['composite']} "
                  f"(fallback {judged['channels']['fallback']})")
finally:
    _print_judge_usage()
