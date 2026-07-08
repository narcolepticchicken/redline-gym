#!/usr/bin/env bash
set -euo pipefail

MODEL="mlx-community/Qwen3.5-9B-4bit"
PORT="${PORT:-8080}"

cat <<EOF
mlx_lm >= 0.31 exposes an OpenAI-compatible /v1 server.

Driver exports:
export REDLINE_AGENT_BASE_URL=http://localhost:${PORT}/v1
export REDLINE_AGENT_MODEL=${MODEL}
export REDLINE_AGENT_KEY_ENV=LOCAL_KEY
export LOCAL_KEY=local

The driver requires a non-empty key; the local mlx_lm server ignores it.
EOF

exec python3 -m mlx_lm.server --model "${MODEL}" --port "${PORT}"
