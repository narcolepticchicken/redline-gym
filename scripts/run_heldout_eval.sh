#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

force=0
dry_run_one=0

usage() {
  cat <<'EOF'
Usage: scripts/run_heldout_eval.sh [--force] [--dry-run-one]

Runs the one-shot held-out eval over tasks/heldout/*.

Options:
  --force        Override reports/.heldout_eval_done. This voids the one-shot claim.
  --dry-run-one  Run one held-out instance with deterministic arms only, for script proofing.
EOF
}

while (($#)); do
  case "$1" in
    --force)
      force=1
      ;;
    --dry-run-one)
      dry_run_one=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

marker="reports/.heldout_eval_done"
if [[ -e "$marker" && "$force" -ne 1 ]]; then
  echo "REFUSING: $marker already exists. Held-out eval is one-shot; use --force only if you accept that the one-shot claim is void." >&2
  exit 2
fi

if [[ "$force" -eq 1 ]]; then
  echo "WARNING: --force re-runs the held-out eval and voids the one-shot claim." >&2
fi

mkdir -p reports
printf 'started_at=%s\ndry_run_one=%s\nforce=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$dry_run_one" "$force" > "$marker"

DRY_RUN_ONE="$dry_run_one" python3 - <<'PY'
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from baselines import grep_bot, null_agent
from baselines.cheater_mech import STRATEGIES, drive_strategy
from env import Episode
from validators.checks import run_all


ROOT = Path.cwd()
REPORTS = ROOT / "reports"
RUN_ROOT = ROOT / "runs" / "heldout_eval"
MARKER = REPORTS / ".heldout_eval_done"
JSON_PATH = REPORTS / "heldout_eval.json"
MD_PATH = REPORTS / "heldout_eval.md"
DRY_RUN_ONE = os.getenv("DRY_RUN_ONE") == "1"
CHEATER_STRATEGIES = sorted(STRATEGIES)


def main() -> int:
    tasks = heldout_tasks()
    if not tasks:
        raise SystemExit("no held-out tasks found under tasks/heldout")
    if DRY_RUN_ONE:
        tasks = tasks[:1]

    include_honest = bool(os.getenv("GLM_API_KEY")) and not DRY_RUN_ONE
    run_started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows: list[dict[str, Any]] = []
    task_summaries: list[dict[str, Any]] = []
    usage_totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "calls": 0}

    print(
        "HELDOUT EVAL DRY RUN: one task, deterministic arms only"
        if DRY_RUN_ONE
        else "HELDOUT EVAL: one-shot eval-mode run"
    )
    print(f"tasks: {', '.join(str(task.relative_to(ROOT)) for task in tasks)}")
    print(f"honest_llm seeds 0-2: {'enabled (GLM_API_KEY set)' if include_honest else 'skipped'}")

    for task_dir in tasks:
        task_rel = str(task_dir.relative_to(ROOT))
        print(f"\n== {task_rel} ==")
        validators = validator_row(task_dir)
        rows.append(validators)
        print(f"validators: {validators['status']} ({validators['gate']})")

        baseline_rows = [
            run_scripted_baseline(task_dir, "null_agent", null_agent.drive),
            run_scripted_baseline(task_dir, "grep_bot", grep_bot.drive),
        ]
        for strategy in CHEATER_STRATEGIES:
            baseline_rows.append(run_cheater_mech(task_dir, strategy))

        honest_rows: list[dict[str, Any]] = []
        if include_honest:
            for seed in range(3):
                row = run_honest_llm(task_dir, seed)
                honest_rows.append(row)
                add_usage(usage_totals, row.get("usage", {}))

        gates = task_gates(validators, baseline_rows, honest_rows)
        for row in baseline_rows + honest_rows:
            row["gate"] = gates.get(row["arm"], row.get("gate", "UNMEASURED"))
        rows.extend(baseline_rows + honest_rows)
        task_summaries.append(
            {
                "task": task_rel,
                "validators": validators["gate"],
                "null": gates["null_agent"],
                "grep_vs_honest": gates["grep_bot"],
                "honest_band": gates["honest_llm"],
                "cheater_mech_vs_honest": gates["cheater_mech"],
            }
        )
        for row in baseline_rows + honest_rows:
            extra = f" strategy={row['strategy']}" if row.get("strategy") else ""
            seed = f" seed={row['seed']}" if row.get("seed") is not None else ""
            print(
                f"{row['arm']}{extra}{seed}: composite={fmt_num(row.get('composite'))} "
                f"status={row['status']} gate={row['gate']}"
            )

    result = {
        "run_mode": "eval-run",
        "dry_run_one": DRY_RUN_ONE,
        "started_at": run_started,
        "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "marker": str(MARKER),
        "honest_llm": "RUN" if include_honest else "SKIPPED",
        "usage_totals": usage_totals if include_honest else None,
        "task_summaries": task_summaries,
        "rows": rows,
    }
    JSON_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    MD_PATH.write_text(render_markdown(result))
    with MARKER.open("a") as fh:
        fh.write(f"completed_at={result['completed_at']}\n")
        fh.write(f"json={JSON_PATH}\n")
        fh.write(f"markdown={MD_PATH}\n")

    print(f"\nwrote {JSON_PATH}")
    print(f"wrote {MD_PATH}")
    print(f"marker {MARKER}")
    return 0


def heldout_tasks() -> list[Path]:
    return sorted((ROOT / "tasks" / "heldout").glob("*/task.json"), key=lambda p: p.parent.name)


def validator_row(task_json: Path) -> dict[str, Any]:
    task_dir = task_json.parent
    results = run_all(task_dir)
    failures = [f"{r.code}: {r.detail}" for r in results if r.status == "FAIL"]
    return {
        "run_mode": "eval-run",
        "task": str(task_dir.relative_to(ROOT)),
        "task_id": task_dir.name,
        "arm": "validators",
        "seed": None,
        "strategy": None,
        "status": "FAIL" if failures else "PASS",
        "gate": "FAIL" if failures else "PASS",
        "detail": "; ".join(failures) if failures else "programmatic validators passed",
        "score_path": None,
        "composite": None,
        "channels": None,
    }


def run_scripted_baseline(task_json: Path, name: str, driver: Any) -> dict[str, Any]:
    task_dir = task_json.parent
    run_dir = RUN_ROOT / name / task_dir.name
    episode = Episode(task_dir, seed=0, run_dir=run_dir)
    episode.reset()
    driver(episode)
    return score_row(task_dir, name, 0, None, episode.score_path)


def run_cheater_mech(task_json: Path, strategy: str) -> dict[str, Any]:
    task_dir = task_json.parent
    run_dir = RUN_ROOT / "cheater_mech" / strategy / task_dir.name
    episode = Episode(task_dir, seed=0, run_dir=run_dir)
    episode.reset()
    drive_strategy(episode, strategy)
    return score_row(task_dir, "cheater_mech", 0, strategy, episode.score_path)


def run_honest_llm(task_json: Path, seed: int) -> dict[str, Any]:
    task_dir = task_json.parent
    run_dir = RUN_ROOT / "honest_llm" / f"seed{seed}" / task_dir.name
    cmd = [
        sys.executable,
        "-m",
        "baselines.honest_llm",
        "--task",
        str(task_dir),
        "--seed",
        str(seed),
        "--run-dir",
        str(run_dir),
    ]
    completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if completed.returncode != 0:
        return {
            "run_mode": "eval-run",
            "task": str(task_dir.relative_to(ROOT)),
            "task_id": task_dir.name,
            "arm": "honest_llm",
            "seed": seed,
            "strategy": None,
            "status": "ERROR",
            "gate": "FAIL",
            "detail": completed.stderr.strip() or completed.stdout.strip(),
            "score_path": None,
            "composite": None,
            "channels": None,
            "usage": None,
        }
    score_path = run_dir / task_dir.name / "score.json"
    row = score_row(task_dir, "honest_llm", seed, None, score_path)
    usage_path = run_dir / "usage.json"
    row["usage_path"] = str(usage_path)
    row["usage"] = json.loads(usage_path.read_text()) if usage_path.exists() else None
    return row


def score_row(task_dir: Path, arm: str, seed: int, strategy: str | None, score_path: Path) -> dict[str, Any]:
    score = json.loads(score_path.read_text())
    return {
        "run_mode": "eval-run",
        "task": str(task_dir.relative_to(ROOT)),
        "task_id": task_dir.name,
        "arm": arm,
        "seed": seed,
        "strategy": strategy,
        "status": score["status"],
        "gate": "UNMEASURED",
        "detail": "",
        "score_path": str(score_path),
        "composite": score["composite"],
        "channels": score["channels"],
        "false_flags": score.get("false_flags"),
        "matched_deviation_ids": score.get("matched_deviation_ids", []),
    }


def task_gates(
    validators: dict[str, Any],
    baseline_rows: list[dict[str, Any]],
    honest_rows: list[dict[str, Any]],
) -> dict[str, str]:
    gates = {"validators": validators["gate"]}
    by_arm = {row["arm"]: row for row in baseline_rows if row["arm"] != "cheater_mech"}
    null_score = by_arm["null_agent"]["composite"]
    gates["null_agent"] = "PASS" if null_score is not None and null_score <= 0.05 else "FAIL"

    valid_honest = [row for row in honest_rows if isinstance(row.get("composite"), (int, float))]
    if not valid_honest:
        gates["grep_bot"] = "UNMEASURED"
        gates["honest_llm"] = "UNMEASURED"
        gates["cheater_mech"] = "UNMEASURED"
        return gates

    honest_mean = sum(float(row["composite"]) for row in valid_honest) / len(valid_honest)
    honest_band_ok = all(0.40 <= float(row["composite"]) <= 0.80 for row in valid_honest)
    gates["honest_llm"] = "PASS" if honest_band_ok else "FAIL"
    gates["grep_bot"] = "PASS" if float(by_arm["grep_bot"]["composite"]) <= 0.60 * honest_mean else "FAIL"
    cheater_rows = [row for row in baseline_rows if row["arm"] == "cheater_mech"]
    gates["cheater_mech"] = (
        "PASS"
        if all(float(row["composite"]) < honest_mean for row in cheater_rows)
        else "FAIL"
    )
    return gates


def add_usage(total: dict[str, int], usage: dict[str, Any] | None) -> None:
    if not usage:
        return
    for key in total:
        total[key] += int(usage.get(key, 0))


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Held-out Eval",
        "",
        f"Run mode: `{result['run_mode']}`",
        f"Dry-run one: `{result['dry_run_one']}`",
        f"Started: `{result['started_at']}`",
        f"Completed: `{result['completed_at']}`",
        f"Honest LLM: `{result['honest_llm']}`",
        "",
        "## Threshold Summary",
        "",
        "| Task | Validators | Null <= 0.05 | Grep <= 60% honest | Honest 0.40-0.80 | Cheater mech < honest |",
        "|---|---|---|---|---|---|",
    ]
    for summary in result["task_summaries"]:
        lines.append(
            "| {task} | {validators} | {null} | {grep} | {honest} | {cheater} |".format(
                task=summary["task"],
                validators=summary["validators"],
                null=summary["null"],
                grep=summary["grep_vs_honest"],
                honest=summary["honest_band"],
                cheater=summary["cheater_mech_vs_honest"],
            )
        )
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| Run mode | Task | Arm | Strategy | Seed | Status | Gate | Composite | Recall | Precision | Grounding | Score path |",
            "|---|---|---|---|---:|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in result["rows"]:
        channels = row.get("channels") or {}
        lines.append(
            "| {mode} | {task} | {arm} | {strategy} | {seed} | {status} | {gate} | {comp} | {recall} | {precision} | {grounding} | {score_path} |".format(
                mode=row["run_mode"],
                task=row["task"],
                arm=row["arm"],
                strategy=row.get("strategy") or "",
                seed="" if row.get("seed") is None else row["seed"],
                status=row["status"],
                gate=row["gate"],
                comp=fmt_num(row.get("composite")),
                recall=fmt_num(channels.get("recall")),
                precision=fmt_num(channels.get("precision")),
                grounding=fmt_num(channels.get("grounding")),
                score_path=row.get("score_path") or "",
            )
        )
    if result.get("usage_totals"):
        lines.extend(["", "## Usage", "", "```json", json.dumps(result["usage_totals"], indent=2, sort_keys=True), "```"])
    lines.append("")
    return "\n".join(lines)


def fmt_num(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.6f}"
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
PY
