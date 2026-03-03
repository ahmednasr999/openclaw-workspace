#!/usr/bin/env bash
set -euo pipefail

PID="$(pgrep -xo -f "openclaw-gateway" || true)"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [[ -z "${PID}" ]]; then
  printf '{"status":"down","timestamp":"%s"}\n' "$NOW"
  exit 1
fi

ELAPSED_SEC="$(ps -o etimes= -p "$PID" | tr -d ' ')"
UPTIME_SEC="${ELAPSED_SEC:-0}"

LAST_ACTIVITY_FILE="/root/.openclaw/workspace/memory/gateway-last-activity.ts"
if [[ -f "$LAST_ACTIVITY_FILE" ]]; then
  LAST_ACTIVITY="$(cat "$LAST_ACTIVITY_FILE" 2>/dev/null || true)"
  if [[ -z "${LAST_ACTIVITY}" ]]; then
    LAST_ACTIVITY="$NOW"
  fi
else
  LAST_ACTIVITY="$NOW"
fi

ACTIVE_JOBS="$(pgrep -af "sessions_spawn|subagent|acp" | wc -l | tr -d ' ')"
BLOCKED_1H="0"
if [[ -f /root/.openclaw/workspace/memory/blocked-domains.log ]]; then
  BLOCKED_1H="$(awk -v now="$(date -u +%s)" '
    {
      split($1, t, "T");
      gsub(/Z/, "", $1);
      cmd = "date -u -d \"" $1 "\" +%s";
      cmd | getline ts;
      close(cmd);
      if (ts >= now - 3600) c++;
    }
    END { print c + 0 }
  ' /root/.openclaw/workspace/memory/blocked-domains.log 2>/dev/null || echo 0)"
fi

printf '{"status":"ok","pid":%s,"uptime_sec":%s,"last_activity":"%s","active_jobs":%s,"blocked_count_1h":%s,"timestamp":"%s"}\n' \
  "$PID" "$UPTIME_SEC" "$LAST_ACTIVITY" "$ACTIVE_JOBS" "$BLOCKED_1H" "$NOW"
