#!/usr/bin/env bash
# Run the health dashboard without turning an intentional CRITICAL verdict
# (exit 2) into an OpenClaw tool-execution failure.

set -uo pipefail

DASHBOARD="${OPENCLAW_HEALTH_DASHBOARD:-/root/.openclaw/workspace/scripts/openclaw-health-dashboard.py}"
OUTPUT=$(mktemp)
trap 'rm -f "$OUTPUT"' EXIT

python3 "$DASHBOARD" --write-report "$@" >"$OUTPUT" 2>&1
rc=$?
cat "$OUTPUT"

case "$rc" in
  0)
    exit 0
    ;;
  2)
    printf '\nHEALTH_ALERT_EXIT=2 (reported as health state; wrapper exit=0)\n'
    exit 0
    ;;
  *)
    printf '\nHEALTH_EXECUTION_ERROR=%s\n' "$rc" >&2
    exit "$rc"
    ;;
esac
