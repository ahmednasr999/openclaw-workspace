#!/usr/bin/env bash
# heartbeat-checks.sh — Deterministic health checks for NASR heartbeat
# Outputs JSON to stdout. Heartbeat model reads and decides what to alert.
# Last updated: 2026-03-13

set -euo pipefail

WORKSPACE="/root/.openclaw/workspace"
SESSIONS_DIR="/root/.openclaw/agents/main/sessions"
STATE_FILE="$WORKSPACE/.heartbeat/state.json"
NOW_EPOCH=$(date +%s)
NOW_ISO=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
CAIRO_TIME=$(TZ="Africa/Cairo" date +"%H:%M")

# --- Helper: check if file modified within N hours ---
file_age_hours() {
  local file="$1"
  if [ ! -f "$file" ]; then
    echo "999"
    return
  fi
  local mod_epoch
  mod_epoch=$(stat -c %Y "$file" 2>/dev/null || echo "0")
  echo $(( (NOW_EPOCH - mod_epoch) / 3600 ))
}

# ============================================================
# 1. GATEWAY HEALTH
# ============================================================
gateway_status="unknown"
gateway_pid=""
if command -v openclaw &>/dev/null; then
  gw_output=$(openclaw gateway status 2>&1 || true)
  if echo "$gw_output" | grep -qi "running"; then
    gateway_status="running"
    gateway_pid=$(echo "$gw_output" | grep -oi 'pid[: ]*[0-9]*' | grep -o '[0-9]*' | head -1 || true)
  elif echo "$gw_output" | grep -qi "stopped\|not running\|dead"; then
    gateway_status="down"
  fi
fi

# ============================================================
# 2. CRON HEALTH — check recent cron runs for failures
# ============================================================
cron_failures="[]"
if command -v openclaw &>/dev/null; then
  cron_list=$(openclaw cron list --json 2>/dev/null || echo "[]")
  # Extract failed crons (status contains "error" or "failed")
  cron_failures=$(echo "$cron_list" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if not isinstance(data, list):
        data = []
    failed = []
    for c in data:
        status = str(c.get('lastStatus', c.get('status', ''))).lower()
        if 'error' in status or 'fail' in status:
            failed.append({
                'id': c.get('id', 'unknown')[:8],
                'label': c.get('label', c.get('prompt', 'unlabeled'))[:60],
                'status': status
            })
    print(json.dumps(failed))
except:
    print('[]')
" 2>/dev/null || echo "[]")
fi

# ============================================================
# 3. SESSION HEALTH — check for bloated session files
# ============================================================
bloated_sessions="[]"
if [ -d "$SESSIONS_DIR" ]; then
  bloated_sessions=$(find "$SESSIONS_DIR" -name "*.jsonl" -size +5M -printf '{"file":"%f","size_mb":%s}\n' 2>/dev/null | python3 -c "
import sys, json
sessions = []
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
        d['size_mb'] = round(d['size_mb'] / 1048576, 1)
        sessions.append(d)
    except:
        pass
print(json.dumps(sessions))
" 2>/dev/null || echo "[]")
fi

# ============================================================
# 4. DISK SPACE
# ============================================================
disk_usage_pct=$(df / --output=pcent 2>/dev/null | tail -1 | tr -d ' %' || echo "0")

# ============================================================
# 5. ACTIVE TASKS STALENESS
# ============================================================
active_tasks_age=$(file_age_hours "$WORKSPACE/memory/active-tasks.md")

# ============================================================
# 6. DEADLINE SCAN — look for dates within 48h in active-tasks.md
# ============================================================
upcoming_deadlines="[]"
if [ -f "$WORKSPACE/memory/active-tasks.md" ]; then
  upcoming_deadlines=$(python3 -c "
import re, json
from datetime import datetime, timedelta

now = datetime.utcnow()
window = now + timedelta(hours=48)
deadlines = []

with open('$WORKSPACE/memory/active-tasks.md') as f:
    content = f.read()

# Look for date patterns like 'Mar 14', '2026-03-14', 'March 14'
patterns = [
    r'(\d{4}-\d{2}-\d{2})',
    r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(?:,?\s*\d{4})?)'
]
for pat in patterns:
    for match in re.finditer(pat, content):
        try:
            ds = match.group(1)
            for fmt in ['%Y-%m-%d', '%b %d, %Y', '%b %d %Y', '%B %d, %Y', '%B %d %Y', '%b %d']:
                try:
                    dt = datetime.strptime(ds, fmt)
                    if dt.year < 2000:
                        dt = dt.replace(year=now.year)
                    if now <= dt <= window:
                        # Get context line
                        start = max(0, match.start() - 80)
                        end = min(len(content), match.end() + 40)
                        ctx = content[start:end].replace('\n',' ').strip()
                        deadlines.append({'date': ds, 'context': ctx[:100]})
                    break
                except:
                    continue
        except:
            continue

print(json.dumps(deadlines[:5]))
" 2>/dev/null || echo "[]")
fi

# ============================================================
# 7. MODEL FALLBACK DETECTION — check gateway logs
# ============================================================
model_fallbacks="[]"
GATEWAY_LOG="/root/.openclaw/gateway.log"
if [ -f "$GATEWAY_LOG" ]; then
  # Check last hour of logs for fallback events
  model_fallbacks=$(python3 -c "
import json, re
from datetime import datetime, timedelta

now = datetime.utcnow()
one_hour_ago = now - timedelta(hours=1)
fallbacks = []

try:
    with open('$GATEWAY_LOG', 'r') as f:
        for line in f:
            if 'fallback' in line.lower() or 'falling back' in line.lower():
                fallbacks.append(line.strip()[:120])
except:
    pass

print(json.dumps(fallbacks[-5:]))
" 2>/dev/null || echo "[]")
fi

# ============================================================
# OUTPUT: Structured JSON
# ============================================================
cat <<EOF
{
  "timestamp": "$NOW_ISO",
  "cairo_time": "$CAIRO_TIME",
  "gateway": {
    "status": "$gateway_status",
    "pid": "$gateway_pid"
  },
  "cron_failures": $cron_failures,
  "bloated_sessions": $bloated_sessions,
  "disk_usage_pct": $disk_usage_pct,
  "active_tasks_age_hours": $active_tasks_age,
  "upcoming_deadlines": $upcoming_deadlines,
  "model_fallbacks": $model_fallbacks
}
EOF
