#!/usr/bin/env bash
set -euo pipefail

WORKSPACE=/root/.openclaw/workspace
LOG="$WORKSPACE/logs/resource-pressure-guard.log"
mkdir -p "$(dirname "$LOG")"

output=$(/usr/bin/python3 "$WORKSPACE/scripts/resource-pressure-guard.py" monitor --reap)
printf '[%s] %s\n' "$(date -Is)" "$output" >> "$LOG"

alert=$(printf '%s' "$output" | /usr/bin/jq -r '.alert // empty')
if [[ -n "$alert" ]]; then
  /usr/bin/timeout --kill-after=5s 30s /usr/bin/openclaw message send \
    --channel telegram \
    --target 866838380 \
    --message "$alert" \
    --json >/dev/null 2>&1 || true
fi
