#!/usr/bin/env bash
# Merge the QLoRA adapter once, then expose the merged model with vLLM /v1.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="${VENV_DIR:-"$ROOT/.venv-pod"}"
PYTHON_BIN="${PYTHON_BIN:-"$VENV_DIR/bin/python"}"
VLLM_BIN="${VLLM_BIN:-"$VENV_DIR/bin/vllm"}"

# Best guess only: the SFT rows are instruction/chat style, so use the instruct
# variant unless BASE_MODEL is overridden after verifying the original HF ID.
BASE_MODEL="${BASE_MODEL:-Qwen/Qwen3.5-9B-Instruct}"
ADAPTER_DIR="${ADAPTER_DIR:-"$ROOT/adapters_pod/pilot_v2"}"
MERGED_DIR="${MERGED_DIR:-"$ROOT/merged_pod/pilot_v2"}"
MODEL_NAME="${MODEL_NAME:-redline-pilot-v2}"
HOST="${VLLM_HOST:-0.0.0.0}"
PORT="${VLLM_PORT:-8000}"
MAX_MODEL_LEN="${VLLM_MAX_MODEL_LEN:-8192}"
GPU_MEMORY_UTILIZATION="${VLLM_GPU_MEMORY_UTILIZATION:-0.90}"
TRUST_REMOTE_CODE="${TRUST_REMOTE_CODE:-0}"
export TRUST_REMOTE_CODE

: "${VLLM_API_KEY:?Set VLLM_API_KEY to require bearer authentication before serving.}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "ERROR: pod Python not found at $PYTHON_BIN; run scripts/pod/setup.sh first." >&2
  exit 1
fi
if [[ ! -x "$VLLM_BIN" ]]; then
  echo "ERROR: vLLM command not found at $VLLM_BIN; run scripts/pod/setup.sh first." >&2
  exit 1
fi
if [[ ! -f "$ADAPTER_DIR/adapter_config.json" ]]; then
  echo "ERROR: missing adapter_config.json under $ADAPTER_DIR; train or sync the adapter first." >&2
  exit 1
fi

# Merged serving is deliberately chosen over vLLM's raw --enable-lora path.
# It costs disk space and a one-time merge, but avoids depending on a newly
# resolved model architecture also being supported by vLLM's LoRA injection
# path. The resulting standard Hugging Face checkpoint is simpler to inspect
# and has no runtime adapter-routing configuration.
if [[ ! -f "$MERGED_DIR/.redline_merge_complete" ]]; then
  echo "Merging adapter into bf16 base weights at $MERGED_DIR"
  "$PYTHON_BIN" - "$BASE_MODEL" "$ADAPTER_DIR" "$MERGED_DIR" <<'PY'
from __future__ import annotations

import os
from pathlib import Path
import sys

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base_model, adapter_dir, merged_dir = sys.argv[1:]
trust_remote_code = os.getenv("TRUST_REMOTE_CODE") == "1"
out = Path(merged_dir)
out.mkdir(parents=True, exist_ok=True)

base = AutoModelForCausalLM.from_pretrained(
    base_model,
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    trust_remote_code=trust_remote_code,
)
model = PeftModel.from_pretrained(base, adapter_dir)
model = model.merge_and_unload()
model.save_pretrained(out, safe_serialization=True, max_shard_size="5GB")
tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=trust_remote_code)
tokenizer.save_pretrained(out)
(out / ".redline_merge_complete").write_text("merged\n", encoding="utf-8")
PY
fi

VLLM_ARGS=(
  serve "$MERGED_DIR"
  --host "$HOST"
  --port "$PORT"
  --api-key "$VLLM_API_KEY"
  --served-model-name "$MODEL_NAME"
  --dtype bfloat16
  --max-model-len "$MAX_MODEL_LEN"
  --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION"
)
if [[ "$TRUST_REMOTE_CODE" == "1" ]]; then
  VLLM_ARGS+=(--trust-remote-code)
fi

echo "Serving $MODEL_NAME at http://$HOST:$PORT/v1"
exec "$VLLM_BIN" "${VLLM_ARGS[@]}"
