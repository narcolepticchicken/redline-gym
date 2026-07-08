# RL Training Pilot

This is a local, RAFT-style training pilot: rejection sampling / best-of-n filtered SFT on a locally served model. It is build scaffolding only. Rollouts run through the lab scripts here, never through an interactive coding-assistant harness.

## Serving

Start the local OpenAI-compatible server:

```bash
scripts/serve_local.sh
```

`mlx_lm >= 0.31` exposes `/v1`. The rollout driver expects:

```bash
export REDLINE_AGENT_BASE_URL=http://localhost:8080/v1
export REDLINE_AGENT_MODEL=mlx-community/Qwen3.5-9B-4bit
export REDLINE_AGENT_KEY_ENV=LOCAL_KEY
export LOCAL_KEY=local
```

`LOCAL_KEY` only satisfies the driver key gate; the local server ignores it. Set `REDLINE_AGENT_TEMPERATURE` above `0` when collecting best-of-n samples.

## Protocol

1. Baseline-eval the base 9B model on three dev T2 gate tasks plus three T1 tasks, with `n=3`.
2. Collect best-of-8 on about twelve dev instances. Use a T1-weighted curriculum; conformance is the trainable prize.
3. Filter rollouts with `--min-composite 0.5 --top-k-per-task 2`.
4. Train the LoRA adapter with `scripts/train_lora.sh`.
5. Re-eval the same tasks, plus two untouched dev tasks as a transfer check.
6. Report the curve as measured, with reward channels and token usage.

Heldout tasks are never used for training or pilot eval here. Anything under `tasks/heldout/` is reserved for formal gates only.

## Example Commands

```bash
export REDLINE_AGENT_TEMPERATURE=0.7
python3 scripts/collect_rollouts.py \
  --tasks @pilot_tasks.txt \
  --n-per-task 8 \
  --out-root runs_pilot/pilot_v1 \
  --seed-base 1000

python3 scripts/build_sft_data.py \
  --manifest runs_pilot/pilot_v1/manifest.jsonl \
  --min-composite 0.5 \
  --top-k-per-task 2 \
  --out data/pilot_sft.jsonl

scripts/train_lora.sh
```

All rollout artifacts are local. Judge tiebreaks, if used later, remain post-hoc scoring of static transcripts.
