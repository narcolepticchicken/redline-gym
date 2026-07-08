from __future__ import annotations

import argparse
import os
import subprocess
from typing import Any

from validators.model_checks import ModelCheck


ENABLE_ENV = "REDLINE_JUDGE_ENABLED"
# Judge model is pinned to sonnet (subscription lane) per SPEC §11 decision 5.
JUDGE_MODEL = os.getenv("REDLINE_JUDGE_MODEL", "sonnet")


class SubscriptionCLIJudge(ModelCheck):
    def __init__(self, *, dry_run: bool = False) -> None:
        super().__init__()
        self.dry_run = dry_run

    def fallback_tiebreak_judge(self, proposed: str, expected: str, *_: Any, **__: Any) -> bool:
        prompt = fallback_tiebreak_prompt(proposed, expected)
        output = self._run_or_dry(prompt)
        return "PASS" in output.upper() and "FAIL" not in output.upper()

    def clean_base_judge_pass(self, task_text: str = "", playbook_text: str = "", *_: Any, **__: Any) -> str:
        return self._run_or_dry(validator_prompt("V3 clean-base", task_text, playbook_text))

    def round_trip_extractor(self, task_text: str = "", playbook_text: str = "", *_: Any, **__: Any) -> str:
        return self._run_or_dry(validator_prompt("V4 round-trip detectability", task_text, playbook_text))

    def missing_info_semantic_search(self, task_text: str = "", playbook_text: str = "", *_: Any, **__: Any) -> str:
        return self._run_or_dry(validator_prompt("V7-semantic missing-info", task_text, playbook_text))

    def realism_judge(self, task_text: str = "", playbook_text: str = "", *_: Any, **__: Any) -> str:
        return self._run_or_dry(validator_prompt("V11 realism/coherence", task_text, playbook_text))

    def _run_or_dry(self, prompt: str) -> str:
        if self.dry_run:
            print(prompt)
            return prompt
        if os.getenv(ENABLE_ENV) != "1":
            raise RuntimeError(f"{ENABLE_ENV}=1 is required before executing the subscription CLI")
        completed = subprocess.run(
            [os.getenv("SUBSCRIPTION_JUDGE_CLI", "claude"), "-p", "--model", JUDGE_MODEL, prompt],
            check=True,
            text=True,
            capture_output=True,
        )
        return completed.stdout


def fallback_tiebreak_prompt(proposed: str, expected: str) -> str:
    return (
        "Redline Gym channel-4 fallback tiebreak.\n"
        "Decide whether the proposed redline is substantively equivalent to the expected fallback.\n"
        "Return exactly PASS or FAIL, followed by one short reason.\n\n"
        f"Expected fallback:\n{expected}\n\n"
        f"Proposed redline:\n{proposed}\n"
    )


def validator_prompt(check_name: str, task_text: str, playbook_text: str) -> str:
    return (
        f"Redline Gym model validator: {check_name}.\n"
        "Use the static task artifacts only. Do not assume hidden answer keys unless included below.\n"
        "Return a concise PASS/FAIL style assessment with reasons.\n\n"
        f"Task artifacts:\n{task_text}\n\n"
        f"Playbook:\n{playbook_text}\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Subscription CLI judge adapter for Redline Gym.")
    parser.add_argument(
        "check",
        choices=["fallback", "v3-clean-base", "v4-round-trip", "v7-semantic", "v11-realism"],
    )
    parser.add_argument("--proposed", default="")
    parser.add_argument("--expected", default="")
    parser.add_argument("--task-text", default="")
    parser.add_argument("--playbook-text", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    judge = ClaudeSubscriptionJudge(dry_run=args.dry_run)
    if args.check == "fallback":
        judge.fallback_tiebreak_judge(args.proposed, args.expected)
    else:
        dispatch = {
            "v3-clean-base": judge.clean_base_judge_pass,
            "v4-round-trip": judge.round_trip_extractor,
            "v7-semantic": judge.missing_info_semantic_search,
            "v11-realism": judge.realism_judge,
        }
        dispatch[args.check](args.task_text, args.playbook_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
