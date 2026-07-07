#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python3 -m pytest -q

python3 - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys

from baselines import grep_bot, null_agent, random_flagger
from baselines.cheater_mech import STRATEGIES, drive_strategy
from env import Episode
from validators.checks import run_all, write_report


ROOT = Path.cwd()
REPORTS = ROOT / "reports"
RUNS = ROOT / "runs" / "gates"
PROTECTED_NO_WRITE_TASKS = {
    "tasks/contracts/T2-MSA-001",
    "tasks/generated/T2-DPA-302",
    "tasks/generated/T2-EMP-702",
}
REPORTS.mkdir(exist_ok=True)
RUNS.mkdir(parents=True, exist_ok=True)


def task_dirs() -> list[Path]:
    paths = []
    for task_json in (ROOT / "tasks").rglob("task.json"):
        rel_parts = task_json.relative_to(ROOT).parts
        if "heldout" in rel_parts:
            continue
        paths.append(task_json.parent)
    return sorted(paths, key=lambda path: str(path.relative_to(ROOT)))


def score_baseline(task_dir: Path, name: str) -> dict:
    drivers = {
        "null": null_agent.drive,
        "random": random_flagger.drive,
        "grep": grep_bot.drive,
    }
    run_dir = RUNS / name / task_dir.name
    episode = Episode(task_dir, seed=0, run_dir=run_dir)
    episode.reset()
    drivers[name](episode)
    score = json.loads(episode.score_path.read_text())
    return {
        "composite": score["composite"],
        "recall": round(score["channels"]["recall"], 6),
        "status": score["status"],
    }


def score_cheater(task_dir: Path, strategy: str) -> dict:
    run_dir = RUNS / "cheater_mech" / strategy / task_dir.name
    episode = Episode(task_dir, seed=0, run_dir=run_dir)
    episode.reset()
    drive_strategy(episode, strategy)
    score = json.loads(episode.score_path.read_text())
    return {
        "strategy": strategy,
        "composite": score["composite"],
        "recall": round(score["channels"]["recall"], 6),
        "grounding": round(score["channels"]["grounding"], 6),
        "status": score["status"],
    }


def gate_null(score: dict) -> str:
    return "PASS" if score["composite"] <= 0.05 else "FAIL"


def validator_gate(results: list) -> str:
    return "PASS" if all(result.status != "FAIL" for result in results) else "FAIL"


def fmt_score(score: dict) -> str:
    return f"{score['composite']:.6f} / {score['recall']:.6f}"


rows = []
deterministic_failures = []
for task_dir in task_dirs():
    rel = str(task_dir.relative_to(ROOT))
    validation = run_all(task_dir)
    if rel not in PROTECTED_NO_WRITE_TASKS:
        write_report(task_dir, validation)
    validation_status = validator_gate(validation)
    if validation_status == "FAIL":
        deterministic_failures.append(f"{rel}: validators")
    null = score_baseline(task_dir, "null")
    random_score = score_baseline(task_dir, "random")
    grep = score_baseline(task_dir, "grep")
    null_gate = gate_null(null)
    if null_gate == "FAIL":
        deterministic_failures.append(f"{rel}: null gate")
    rows.append(
        {
            "task": rel,
            "task_id": task_dir.name,
            "validators": validation_status,
            "null": null,
            "null_gate": null_gate,
            "random": random_score,
            "random_gate": "UNMEASURED",
            "grep": grep,
            "grep_gate": "UNMEASURED",
            "mechanical_ceiling": None,
            "honest_llm": "SKIPPED (no key)" if not os.getenv("GLM_API_KEY") else "SKIPPED (deterministic no-network run)",
            "cheater_llm": "SKIPPED (no key)" if not os.getenv("GLM_API_KEY") else "SKIPPED (deterministic no-network run)",
            "deepseek_judge": "SKIPPED (no key)" if not os.getenv("DEEPSEEK_API_KEY") else "SKIPPED (deterministic no-network run)",
        }
    )

ceiling_tasks = [ROOT / "tasks/contracts/T1-NDA-001", ROOT / "tasks/contracts/T2-MSA-001"]
for ceiling_task in ceiling_tasks:
    if not ceiling_task.exists():
        continue
    scores = [score_cheater(ceiling_task, strategy) for strategy in sorted(STRATEGIES)]
    max_score = max(scores, key=lambda score: score["composite"])
    for row in rows:
        if row["task_id"] == ceiling_task.name:
            row["mechanical_ceiling"] = {"max": max_score, "strategies": scores}
            break

print("GLM honest baseline: SKIPPED (no key)" if not os.getenv("GLM_API_KEY") else "GLM honest baseline: SKIPPED (deterministic no-network run)")
print("GLM cheater baseline: SKIPPED (no key)" if not os.getenv("GLM_API_KEY") else "GLM cheater baseline: SKIPPED (deterministic no-network run)")
print("DeepSeek judge: SKIPPED (no key)" if not os.getenv("DEEPSEEK_API_KEY") else "DeepSeek judge: SKIPPED (deterministic no-network run)")

gate_json = {
    "deterministic_failures": deterministic_failures,
    "model_backed_steps": {
        "honest_llm": "SKIPPED (no key)" if not os.getenv("GLM_API_KEY") else "SKIPPED (deterministic no-network run)",
        "cheater_llm": "SKIPPED (no key)" if not os.getenv("GLM_API_KEY") else "SKIPPED (deterministic no-network run)",
        "deepseek_judge": "SKIPPED (no key)" if not os.getenv("DEEPSEEK_API_KEY") else "SKIPPED (deterministic no-network run)",
    },
    "rows": rows,
}
(REPORTS / "gate_table.json").write_text(json.dumps(gate_json, indent=2, sort_keys=True) + "\n")

lines = [
    "# Gate Table",
    "",
    "Composite / recall are reported for deterministic baselines. Honest and model-cheater comparisons are UNMEASURED until model-backed runs are executed in the lab lane.",
    "",
    "| Task | Validators | Null comp/recall | Null gate | Random comp/recall | Random gate | Grep comp/recall | Grep gate | Mechanical max | Model gates |",
    "|---|---|---:|---|---:|---|---:|---|---:|---|",
]
for row in rows:
    ceiling = row["mechanical_ceiling"]
    ceiling_text = "UNMEASURED"
    if ceiling:
        ceiling_text = f"{ceiling['max']['composite']:.6f} ({ceiling['max']['strategy']}, {ceiling['max']['status']})"
    model_text = f"honest {row['honest_llm']}; cheater {row['cheater_llm']}; judge {row['deepseek_judge']}"
    lines.append(
        "| {task} | {validators} | {null_score} | {null_gate} | {random_score} | {random_gate} | {grep_score} | {grep_gate} | {ceiling} | {model_text} |".format(
            task=row["task"],
            validators=row["validators"],
            null_score=fmt_score(row["null"]),
            null_gate=row["null_gate"],
            random_score=fmt_score(row["random"]),
            random_gate=row["random_gate"],
            grep_score=fmt_score(row["grep"]),
            grep_gate=row["grep_gate"],
            ceiling=ceiling_text,
            model_text=model_text,
        )
    )
lines.extend(
    [
        "",
        "## Gate Notes",
        "",
        "- Computable deterministic gates: validators must not FAIL; null composite must be <= 0.05.",
        "- Random precision noise floor, grep <= 60% of honest, honest saturation band, and model cheater < honest are UNMEASURED without honest/model-cheater lab-lane runs.",
    ]
)
if deterministic_failures:
    lines.append(f"- Deterministic failures: {', '.join(deterministic_failures)}.")
else:
    lines.append("- Deterministic failures: none.")
(REPORTS / "gate_table.md").write_text("\n".join(lines) + "\n")

if deterministic_failures:
    print("\n".join(deterministic_failures), file=sys.stderr)
    sys.exit(1)
PY
