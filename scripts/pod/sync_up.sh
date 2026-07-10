#!/usr/bin/env bash
# Copy only the pod-training inputs and pod scripts to a manually created pod.
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
  ssh -p "$SSH_PORT" "$REMOTE_HOST" "mkdir -p -- $(printf '%q' "$REMOTE_ROOT/data/pilot") $(printf '%q' "$REMOTE_ROOT/scripts/pod")"
else
  RSYNC_SSH="ssh"
  ssh "$REMOTE_HOST" "mkdir -p -- $(printf '%q' "$REMOTE_ROOT/data/pilot") $(printf '%q' "$REMOTE_ROOT/scripts/pod")"
fi

rsync -avz --progress -e "$RSYNC_SSH" \
  "$ROOT/data/pilot/" \
  "$REMOTE_HOST:$REMOTE_ROOT/data/pilot/"
rsync -avz --progress -e "$RSYNC_SSH" \
  "$ROOT/scripts/pod/" \
  "$REMOTE_HOST:$REMOTE_ROOT/scripts/pod/"

echo "Synced training data and pod scripts to $REMOTE_HOST:$REMOTE_ROOT"
