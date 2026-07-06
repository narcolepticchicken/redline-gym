from __future__ import annotations

import random

from env import Episode

from .common import doc_lines_with_headings, finalize_card, non_canary_rules, run_baseline


NAME = "random_flagger"
NUM_FLAGS = 3


def drive(episode: Episode) -> None:
    rng = random.Random(episode.seed)
    rules = non_canary_rules(episode)
    rows = doc_lines_with_headings(episode)
    flags = []
    for _ in range(min(NUM_FLAGS, len(rows))):
        rule = rng.choice(rules)
        row = rng.choice(rows)
        flag = {
            "action": "flag_issue",
            "rule_id": rule["rule_id"],
            "doc_id": row["doc_id"],
            "clause_ref": row["clause_ref"],
            "exact_quote": row["text"],
            "severity": rule["severity"],
            "proposed_redline": rule["fallback"],
            "rationale": "Seeded random baseline flag.",
        }
        flags.append({k: v for k, v in flag.items() if k != "action"})
        episode.step(flag)
    episode.step(
        {
            "action": "finalize",
            "card": finalize_card(flags, [], "Seeded random clause review completed."),
        }
    )


def main(argv: list[str] | None = None) -> int:
    return run_baseline(NAME, argv, drive)


if __name__ == "__main__":
    raise SystemExit(main())
