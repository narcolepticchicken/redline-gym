#!/usr/bin/env bash
# Retrieve adapters plus their CSV/JSON metrics from a manually operated pod.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
: "${SSH_DEST:?Set SSH_DEST, for example user@host:22 or a configured SSH alias.}"
REMOTE_ROOT="${REMOTE_ROOT:-redline-gym}"

REMOTE_HOST="$SSH_DEST"
SSH_PORT=""
if [[ "$SSH_DEST" =~ ^(.+):([0-9]+)$ ]]; then
  REMOTE_HOST="${BASH_REMATCH[1]}"
  SSH_PORT="${BASH_REMATCH[2]}"
fi
if [[ -n "$SSH_PORT" ]]; then
  RSYNC_SSH="ssh -p $SSH_PORT"
else
  RSYNC_SSH="ssh"
fi

mkdir -p "$ROOT/adapters_pod"
rsync -avz --progress -e "$RSYNC_SSH" \
  "$REMOTE_HOST:$REMOTE_ROOT/adapters_pod/" \
  "$ROOT/adapters_pod/"

if [[ "${SYNC_MERGED:-0}" == "1" ]]; then
  mkdir -p "$ROOT/merged_pod"
  rsync -avz --progress -e "$RSYNC_SSH" \
    "$REMOTE_HOST:$REMOTE_ROOT/merged_pod/" \
    "$ROOT/merged_pod/"
fi

echo "Synced adapters_pod (including loss_curve.csv and summary.json) from $REMOTE_HOST:$REMOTE_ROOT"
