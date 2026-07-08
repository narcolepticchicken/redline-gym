#!/usr/bin/env bash
set -euo pipefail

# Train the pilot adapter from data/ (for example data/pilot_sft.jsonl).
python3 -m mlx_lm.lora \
  --model mlx-community/Qwen3.5-9B-4bit \
  --train \
  --data data/ \
  --iters 600 \
  --batch-size 1 \
  --num-layers 8 \
  --adapter-path adapters/pilot_v1

# Serve the adapter for re-eval:
# python3 -m mlx_lm.server --model mlx-community/Qwen3.5-9B-4bit --adapter-path adapters/pilot_v1 --port 8080
