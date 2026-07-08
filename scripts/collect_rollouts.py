from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from baselines.honest_llm import SYSTEM_PROMPT
from baselines.llm_common import run_llm_episode


Runner = Callable[[Path, int, Path], dict[str, Any]]


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    tasks = parse_tasks_arg(args.tasks)
    collect_rollouts(
        tasks=tasks,
        n_per_task=args.n_per_task,
        out_root=args.out_root,
        seed_base=args.seed_base,
    )
    return 0


def collect_rollouts(
    *,
    tasks: list[Path],
    n_per_task: int,
    out_root: Path,
    seed_base: int,
    runner: Runner | None = None,
) -> list[dict[str, Any]]:
    if n_per_task < 1:
        raise ValueError("--n-per-task must be >= 1")
    out_root.mkdir(parents=True, exist_ok=True)
    manifest_path = out_root / "manifest.jsonl"
    manifest_path.write_text("")
    rows: list[dict[str, Any]] = []
    run_one = runner or run_honest_episode
    for task_index, task in enumerate(tasks):
        task = task.resolve()
        _reject_heldout(task)
        task_id = _task_id(task)
        for sample_idx in range(n_per_task):
            seed = seed_base + task_index * n_per_task + sample_idx
            run_root = out_root / task_id / f"sample-{sample_idx:02d}"
            result = run_one(task, seed, run_root)
            score_path = Path(result.get("score_path") or run_root / task_id / "score.json")
            score = result.get("score") or json.loads(score_path.read_text())
            usage_path = Path(result.get("usage_path") or result.get("run_dir", run_root / task_id)) / "usage.json"
            usage = result.get("usage")
            if usage is None and usage_path.exists():
                usage = json.loads(usage_path.read_text())
            row = {
                "task": str(task),
                "task_id": score.get("task_id", task_id),
                "sample_idx": sample_idx,
                "seed": seed,
                "run_dir": result.get("run_dir", str(run_root / task_id)),
                "composite": score["composite"],
                "channels": score["channels"],
                "num_turns": score["num_turns"],
                "tokens": int((usage or {}).get("total_tokens", 0)),
            }
            with manifest_path.open("a") as fh:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
            rows.append(row)
            print(json.dumps(row, sort_keys=True))
    return rows


def run_honest_episode(task: Path, seed: int, run_root: Path) -> dict[str, Any]:
    return run_llm_episode(
        name="honest_llm",
        system_prompt=SYSTEM_PROMPT,
        task=task,
        seed=seed,
        run_dir=run_root,
    )


def parse_tasks_arg(value: str) -> list[Path]:
    if value.startswith("@"):
        raw = Path(value[1:]).read_text()
        pieces: list[str] = []
        for line in raw.splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                pieces.extend(part.strip() for part in line.split(","))
    else:
        pieces = [part.strip() for part in value.split(",")]
    tasks = [Path(part) for part in pieces if part]
    if not tasks:
        raise ValueError("--tasks resolved to no task directories")
    return tasks


def _task_id(task: Path) -> str:
    task_json = task / "task.json"
    if task_json.exists():
        return str(json.loads(task_json.read_text()).get("task_id") or task.name)
    return task.name


def _reject_heldout(task: Path) -> None:
    parts = task.parts
    if "tasks" in parts and "heldout" in parts:
        raise ValueError(f"heldout task is not allowed in pilot rollout collection: {task}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect local-model honest rollouts for the RL pilot.")
    parser.add_argument("--tasks", required=True, help="Comma list of task dirs, or @file with one or more task dirs.")
    parser.add_argument("--n-per-task", type=int, required=True)
    parser.add_argument("--out-root", type=Path, required=True)
    parser.add_argument("--seed-base", type=int, default=0)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
