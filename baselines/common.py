from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from env import Episode


ROOT = Path(__file__).resolve().parents[1]


def parser(name: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"Run the {name} Redline Gym baseline.")
    p.add_argument("--task", type=Path, required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--run-dir", type=Path, default=None)
    return p


def default_run_dir(name: str, seed: int) -> Path:
    return ROOT / "runs" / f"{name}-seed{seed}"


def run_baseline(name: str, argv: list[str] | None, driver: Callable[[Episode], None]) -> int:
    args = parser(name).parse_args(argv)
    run_dir = args.run_dir or default_run_dir(name, args.seed)
    episode = Episode(args.task, seed=args.seed, run_dir=run_dir)
    episode.reset()
    driver(episode)
    score = json.loads(episode.score_path.read_text())
    print(json.dumps(_stdout_score(score, episode.score_path), indent=2, sort_keys=True))
    return 0


def finalize_card(flags: list[dict[str, Any]], escalations: list[dict[str, Any]], summary: str) -> dict[str, Any]:
    return {
        "summary": summary,
        "issues": [
            {
                "rule_id": flag.get("rule_id", ""),
                "doc_id": flag.get("doc_id", ""),
                "clause_ref": flag.get("clause_ref", ""),
                "exact_quote": flag.get("exact_quote", ""),
                "severity": flag.get("severity", ""),
                "proposed_redline": flag.get("proposed_redline", ""),
                "rationale": flag.get("rationale", ""),
            }
            for flag in flags
        ],
        "escalations": escalations,
    }


def non_canary_rules(episode: Episode) -> list[dict[str, Any]]:
    return [rule for rule in episode.playbook["rules"] if not rule.get("is_canary")]


def doc_lines_with_headings(episode: Episode) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for doc in episode.docs.values():
        heading = ""
        for line_no, line in enumerate(doc.lines, start=1):
            if line.startswith("## "):
                heading = line[3:].strip()
            text = line.strip()
            if text and not text.startswith("#"):
                rows.append(
                    {
                        "doc_id": doc.doc_id,
                        "line": line_no,
                        "clause_ref": heading or f"line {line_no}",
                        "text": text,
                    }
                )
    return rows


def _stdout_score(score: dict[str, Any], score_path: Path) -> dict[str, Any]:
    return {
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
