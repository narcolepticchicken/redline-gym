from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path
from typing import Any

from env import Episode

from .common import default_run_dir, doc_lines_with_headings, finalize_card, non_canary_rules


NAME = "cheater_mech"
STRATEGIES = {"blanket", "canary_citer", "fabricator", "playbook_parrot"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic mechanical cheater strategies.")
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--strategy", choices=sorted(STRATEGIES), required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    run_dir = args.run_dir or default_run_dir(f"{NAME}-{args.strategy}", args.seed)
    episode = Episode(args.task, seed=args.seed, run_dir=run_dir)
    episode.reset()
    drive_strategy(episode, args.strategy)
    score = json.loads(episode.score_path.read_text())
    print(json.dumps(_stdout_score(score, episode.score_path, args.strategy), indent=2, sort_keys=True))
    return 0


def drive_strategy(episode: Episode, strategy: str) -> None:
    if strategy == "blanket":
        _blanket(episode)
    elif strategy == "canary_citer":
        _canary_citer(episode)
    elif strategy == "fabricator":
        _fabricator(episode)
    elif strategy == "playbook_parrot":
        _playbook_parrot(episode)
    else:
        raise ValueError(f"unknown cheater strategy: {strategy}")


def _blanket(episode: Episode) -> None:
    flags = []
    for row in _first_line_per_section(episode):
        rule = _nearest_rule(row["text"], non_canary_rules(episode))
        flag = _flag(rule, row["doc_id"], row["clause_ref"], row["text"], "Blanket section flag.")
        flags.append(flag)
        episode.step({"action": "flag_issue", **flag})
    episode.step({"action": "finalize", "card": finalize_card(flags, [], "Blanket section sweep.")})


def _canary_citer(episode: Episode) -> None:
    flags = []
    rows = doc_lines_with_headings(episode)
    canaries = [rule for rule in episode.playbook["rules"] if rule.get("is_canary")]
    for index, rule in enumerate(canaries):
        row = _best_canary_quote(rule, rows) or rows[index % len(rows)]
        flag = _flag(rule, row["doc_id"], row["clause_ref"], row["text"], "Canary citation stress test.")
        flags.append(flag)
        episode.step({"action": "flag_issue", **flag})
    episode.step({"action": "finalize", "card": finalize_card(flags, [], "Canary citation sweep.")})


def _fabricator(episode: Episode) -> None:
    rng = random.Random(episode.seed)
    flags = []
    rules = non_canary_rules(episode)
    doc_id = next(iter(episode.docs))
    for index in range(min(3, len(rules))):
        rule = rng.choice(rules)
        quote = f"FABRICATED QUOTE {episode.seed}-{index}: the agreement secretly waives all client protections."
        flag = _flag(rule, doc_id, "fabricated clause", quote, "Invented quote stress test.")
        flags.append(flag)
        episode.step({"action": "flag_issue", **flag})
    episode.step({"action": "finalize", "card": finalize_card(flags, [], "Fabricated quote sweep.")})


def _playbook_parrot(episode: Episode) -> None:
    flags = []
    doc_id = next(iter(episode.docs))
    for rule in episode.playbook["rules"]:
        flag = _flag(rule, doc_id, "playbook text", rule["position"], "Rule text parroted as a quote.")
        flags.append(flag)
        episode.step({"action": "flag_issue", **flag})
    episode.step({"action": "finalize", "card": finalize_card(flags, [], "Playbook parrot sweep.")})


def _first_line_per_section(episode: Episode) -> list[dict[str, Any]]:
    rows = doc_lines_with_headings(episode)
    by_section: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["doc_id"], row["clause_ref"])
        by_section.setdefault(key, row)
    return list(by_section.values())


def _nearest_rule(text: str, rules: list[dict[str, Any]]) -> dict[str, Any]:
    text_tokens = _tokens(text)
    scored = []
    for rule in rules:
        rule_tokens = _tokens(f"{rule['position']} {rule['fallback']}")
        scored.append((len(text_tokens & rule_tokens), rule["rule_id"], rule))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[0][2]


def _best_canary_quote(rule: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    hints = _tokens(rule["position"])
    scored = [(len(hints & _tokens(row["text"])), row) for row in rows]
    scored.sort(key=lambda item: -item[0])
    return scored[0][1] if scored and scored[0][0] else None


def _flag(rule: dict[str, Any], doc_id: str, clause_ref: str, quote: str, rationale: str) -> dict[str, Any]:
    return {
        "rule_id": rule["rule_id"],
        "doc_id": doc_id,
        "clause_ref": clause_ref,
        "exact_quote": quote,
        "severity": rule["severity"],
        "proposed_redline": rule["fallback"],
        "rationale": rationale,
    }


def _tokens(text: str) -> set[str]:
    return {token for token in re.split(r"\W+", text.lower()) if len(token) > 4}


def _stdout_score(score: dict[str, Any], score_path: Path, strategy: str) -> dict[str, Any]:
    return {
        "strategy": strategy,
        "composite": score["composite"],
        "channels": score["channels"],
        "status": score["status"],
        "run_id": score["run_id"],
        "task_id": score["task_id"],
        "seed": score["seed"],
        "num_turns": score["num_turns"],
        "ended_by": score["ended_by"],
        "score_path": str(score_path),
    }


if __name__ == "__main__":
    raise SystemExit(main())

