#!/usr/bin/env bash
# Heartbeat v2 — Reliable system health check
# Outputs JSON report for the heartbeat cron agent to parse and alert on
# Key fix: filters out plugin loading noise from openclaw CLI output

set -euo pipefail

WORKSPACE="/root/.openclaw/workspace"
STATE_FILE="$WORKSPACE/.watchdog/last-alerts.json"

# Ensure state file exists
mkdir -p "$WORKSPACE/.watchdog"
[ -f "$STATE_FILE" ] || echo '{}' > "$STATE_FILE"

# ============================================================
# 1. GATEWAY HEALTH
# ============================================================
gateway_status="unknown"
gateway_pid=""
if pgrep -f "openclaw.*gateway" > /dev/null 2>&1; then
    gateway_status="running"
    gateway_pid=$(pgrep -f "openclaw.*gateway" | head -1)
else
    gateway_status="down"
fi

# ============================================================
# 2. CRON FAILURES (fixed: filter plugin noise from JSON)
# ============================================================
cron_failures="[]"
openclaw cron list --json > /tmp/heartbeat_cron_raw.txt 2>/dev/null || true
if [ -s /tmp/heartbeat_cron_raw.txt ]; then
    cron_failures=$(python3 /root/.openclaw/workspace/scripts/parse-cron-failures.py 2>/dev/null || echo "[]")
fi
rm -f /tmp/heartbeat_cron_raw.txt

# ============================================================
# 3. DISK USAGE
# ============================================================
disk_pct=$(df / --output=pcent 2>/dev/null | tail -1 | tr -d ' %' || echo "0")

# ============================================================
# 4. ACTIVE TASKS STALENESS
# ============================================================
tasks_file="$WORKSPACE/memory/active-tasks.md"
tasks_age_hours=0
if [ -f "$tasks_file" ]; then
    last_mod=$(stat -c %Y "$tasks_file" 2>/dev/null || echo "0")
    now=$(date +%s)
    tasks_age_hours=$(( (now - last_mod) / 3600 ))
fi

# ============================================================
# 5. SCANNER OUTPUT (after 7 AM Cairo only)
# ============================================================
cairo_hour=$(TZ=Africa/Cairo date +%H)
scanner_status="not_checked"
scanner_total=0
scanner_file="$WORKSPACE/jobs-bank/scraped/qualified-jobs-$(TZ=Africa/Cairo date +%Y-%m-%d).md"

if [ "$cairo_hour" -ge 7 ]; then
    if [ -f "$scanner_file" ]; then
        scanner_total=$(grep -c "^##\|^###\|linkedin.com/jobs" "$scanner_file" 2>/dev/null || echo "0")
        if [ "$scanner_total" -eq 0 ]; then
            scanner_status="empty"
        else
            scanner_status="ok"
        fi
    else
        scanner_status="missing"
    fi
fi

# ============================================================
# 6. MODEL FALLBACKS (check last 100 lines of gateway log)
# ============================================================
log_file="/tmp/openclaw/openclaw-$(date +%Y-%m-%d).log"
fallbacks="[]"
if [ -f "$log_file" ]; then
    fallback_lines=$(grep -i "fallback\|model.*fail\|rate.limit" "$log_file" 2>/dev/null | tail -5 || true)
    if [ -n "$fallback_lines" ]; then
        fallbacks=$(echo "$fallback_lines" | python3 -c "
import sys, json
lines = [l.strip() for l in sys.stdin if l.strip()]
print(json.dumps(lines[:5]))
" 2>/dev/null || echo "[]")
    fi
fi

# ============================================================
# 7. BLOATED SESSIONS (>5MB)
# ============================================================
bloated="[]"
sessions_dir="$HOME/.openclaw/sessions"
if [ -d "$sessions_dir" ]; then
    bloated=$(find "$sessions_dir" -name "*.json" -size +5M 2>/dev/null | python3 -c "
import sys, os, json
files = [l.strip() for l in sys.stdin if l.strip()]
result = []
for f in files:
    size_mb = os.path.getsize(f) / (1024*1024) if os.path.exists(f) else 0
    result.append({'file': os.path.basename(f), 'size_mb': round(size_mb, 1)})
print(json.dumps(result))
" 2>/dev/null || echo "[]")
fi

# ============================================================
# 8. UPCOMING DEADLINES (from STATE.yaml)
# ============================================================
deadlines="[]"
state_file="$WORKSPACE/STATE.yaml"
if [ -f "$state_file" ]; then
    deadlines=$(python3 -c "
import yaml, json
from datetime import datetime, timedelta
try:
    with open('$state_file') as f:
        data = yaml.safe_load(f)
    alerts = data.get('alerts', [])
    upcoming = []
    now = datetime.utcnow()
    for a in alerts:
        if not isinstance(a, dict) or a.get('status') == 'done':
            continue
        deadline = a.get('deadline', a.get('due', ''))
        if deadline:
            upcoming.append({'item': a.get('item',''), 'deadline': str(deadline), 'action': a.get('action','')})
    print(json.dumps(upcoming))
except:
    print('[]')
" 2>/dev/null || echo "[]")
fi

# ============================================================
# OUTPUT JSON
# ============================================================
cat << ENDJSON
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "cairo_time": "$(TZ=Africa/Cairo date +%H:%M)",
  "gateway": {
    "status": "$gateway_status",
    "pid": "$gateway_pid"
  },
  "cron_failures": $cron_failures,
  "disk_usage_pct": $disk_pct,
  "active_tasks_age_hours": $tasks_age_hours,
  "scanner": {
    "status": "$scanner_status",
    "total": $scanner_total
  },
  "model_fallbacks": $fallbacks,
  "bloated_sessions": $bloated,
  "upcoming_deadlines": $deadlines
}
ENDJSON
