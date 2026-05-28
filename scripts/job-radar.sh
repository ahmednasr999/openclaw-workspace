#!/usr/bin/env bash
set -Eeuo pipefail

WORKSPACE="/root/.openclaw/workspace"
LOG_DIR="$WORKSPACE/logs/cron"
mkdir -p "$LOG_DIR"

cd "$WORKSPACE"
exec /usr/bin/python3 "$WORKSPACE/scripts/job-radar.py"
