#!/usr/bin/env bash
# Run from the Mac against a pod's OpenAI-compatible vLLM endpoint.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

: "${POD_BASE_URL:?Set POD_BASE_URL, for example http://pod-host:8000/v1.}"
: "${POD_MODEL:?Set POD_MODEL to the vLLM served-model name.}"
: "${POD_API_KEY:?Set POD_API_KEY to the same bearer key used by vLLM.}"

export REDLINE_AGENT_BASE_URL="${POD_BASE_URL%/}"
export REDLINE_AGENT_MODEL="$POD_MODEL"
export REDLINE_AGENT_KEY_ENV="POD_API_KEY"
export POD_API_KEY
export REDLINE_AGENT_TEMPERATURE="${REDLINE_AGENT_TEMPERATURE:-0}"
export REDLINE_AGENT_MAX_TOKENS="${REDLINE_AGENT_MAX_TOKENS:-4000}"
export REDLINE_SCORER_V2="${REDLINE_SCORER_V2:-1}"

OUTPUT_ROOT="${EVAL_OUTPUT_DIR:-runs_pod_eval}"
BASELINE_TASKS=(
  T1-DPA-311
  T1-MSA-121
  T1-NDA-101
  T2-DPA-302
  T2-EMP-702
  T2-MSA-001
)
read -r -a TRANSFER_TASK_ARRAY <<< "${TRANSFER_TASKS:-T1-DPA-301 T2-EMP-703}"
read -r -a SEED_ARRAY <<< "${EVAL_SEEDS:-0 1 2}"
TRAINING_TASKS=(T2-MSA-001 T2-DPA-302 T2-EMP-702)

if [[ "${#TRANSFER_TASK_ARRAY[@]}" -eq 0 || "${#SEED_ARRAY[@]}" -eq 0 ]]; then
  echo "ERROR: TRANSFER_TASKS and EVAL_SEEDS must each contain at least one value." >&2
  exit 1
fi

ALL_TASKS=()
for task_id in "${BASELINE_TASKS[@]}" "${TRANSFER_TASK_ARRAY[@]}"; do
  case " ${ALL_TASKS[*]} " in
    *" $task_id "*) ;;
    *) ALL_TASKS+=("$task_id") ;;
  esac
done

task_dir_for() {
  local task_id="$1"
  if [[ -f "tasks/contracts/$task_id/task.json" ]]; then
    printf '%s\n' "tasks/contracts/$task_id"
    return 0
  fi
  if [[ -f "tasks/generated/$task_id/task.json" ]]; then
    printf '%s\n' "tasks/generated/$task_id"
    return 0
  fi
  echo "ERROR: no task.json found for $task_id in tasks/contracts or tasks/generated." >&2
  return 1
}

for task_id in "${ALL_TASKS[@]}"; do
  task_dir_for "$task_id" >/dev/null
done

mkdir -p "$OUTPUT_ROOT"
echo "Endpoint: $REDLINE_AGENT_BASE_URL"
echo "Model: $REDLINE_AGENT_MODEL"
echo "Temperature: $REDLINE_AGENT_TEMPERATURE"
echo "Scorer v2 env: $REDLINE_SCORER_V2"

for task_id in "${ALL_TASKS[@]}"; do
  task_dir="$(task_dir_for "$task_id")"
  for seed in "${SEED_ARRAY[@]}"; do
    run_dir="$OUTPUT_ROOT/$task_id-seed$seed"
    if [[ -e "$run_dir/$task_id/episode.jsonl" ]]; then
      echo "ERROR: refusing to overwrite existing episode $run_dir/$task_id/episode.jsonl." >&2
      echo "Choose a new EVAL_OUTPUT_DIR or move the prior run deliberately." >&2
      exit 1
    fi
    mkdir -p "$run_dir"
    echo "Evaluating task=$task_id seed=$seed"
    python3 -m baselines.honest_llm \
      --task "$task_dir" \
      --seed "$seed" \
      --run-dir "$run_dir"
  done
done

RUN_DIRS=("$OUTPUT_ROOT"/*-seed*)
python3 scripts/rescore_v2.py "${RUN_DIRS[@]}"

TASK_LIST="${ALL_TASKS[*]}" \
TRAINING_TASK_LIST="${TRAINING_TASKS[*]}" \
SEED_LIST="${SEED_ARRAY[*]}" \
EVAL_OUTPUT_DIR="$OUTPUT_ROOT" \
python3 - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path
from statistics import mean
import sys

root = Path(os.environ["EVAL_OUTPUT_DIR"])
task_order = os.environ["TASK_LIST"].split()
training_tasks = set(os.environ["TRAINING_TASK_LIST"].split())
seeds = os.environ["SEED_LIST"].split()
scores: dict[str, list[float]] = {task: [] for task in task_order}

for path in sorted(root.glob("*/*/score_v2.json")):
    task_id = path.parent.name
    if task_id not in scores:
        continue
    try:
        scores[task_id].append(float(json.loads(path.read_text(encoding="utf-8"))["composite"]))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {path}: {exc}", file=sys.stderr)
        raise SystemExit(1)

missing = [task for task in task_order if len(scores[task]) != len(seeds)]
if missing:
    details = ", ".join(f"{task}={len(scores[task])}/{len(seeds)}" for task in missing)
    print(f"ERROR: missing rescored episodes: {details}", file=sys.stderr)
    raise SystemExit(1)

task_means = {task: mean(scores[task]) for task in task_order}
overall = mean(value for task in task_order for value in scores[task])
baseline = 0.374

print()
print("| task | mean composite | in-distribution-for-training |")
print("|---|---:|---|")
for task in task_order:
    flag = "yes" if task in training_tasks else "no"
    print(f"| {task} | {task_means[task]:.6f} | {flag} |")
print(f"| overall | {overall:.6f} | mixed; not a clean holdout |")
print()
print(
    f"Overall mean {overall:.6f} versus the 0.374 9B baseline: "
    f"{overall - baseline:+.6f}."
)
print(
    "Caveat: T2-MSA-001, T2-DPA-302, and T2-EMP-702 were used to distill "
    "the SFT rows, so this aggregate mixes trained-on tasks with transfer tasks."
)
PY
