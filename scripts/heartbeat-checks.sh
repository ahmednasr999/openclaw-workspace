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
# 3. SCRIPT HEALTH — verify critical scripts actually work
# ============================================================
script_health="[]"
SCRIPTS_TO_TEST=(
  "$WORKSPACE/scripts/gmail-check.sh"
)
script_failures=""
for script in "${SCRIPTS_TO_TEST[@]}"; do
  if [ -f "$script" ]; then
    # Run script and capture output
    output=$(bash "$script" 2>&1)
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
      script_failures="${script_failures}$(basename "$script"): exit $exit_code; "
    elif echo "$output" | grep -qi "ERROR\|error\|fail"; then
      script_failures="${script_failures}$(basename "$script"): output error; "
    fi
  fi
done
if [ -n "$script_failures" ]; then
  script_health="[{\"type\":\"script_failure\",\"details\":\"$script_failures\"}]"
fi

# ============================================================
# 4. SESSION HEALTH — check for bloated session files
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
# 8. SCANNER OUTPUT VALIDATION — check today's scanner ran and produced results
# ============================================================
TODAY=$(TZ="Africa/Cairo" date +"%Y-%m-%d")
SCANNER_FILE="$WORKSPACE/jobs-bank/scraped/qualified-jobs-${TODAY}.md"
scanner_status="unknown"
scanner_picks=0
scanner_leads=0
scanner_total=0
scanner_repair=""

CAIRO_HOUR=$(TZ="Africa/Cairo" date +"%H")

if [ -f "$SCANNER_FILE" ]; then
  scanner_status="exists"
  scanner_picks=$(grep -c "^### " "$SCANNER_FILE" 2>/dev/null || echo "0")
  scanner_leads=$(grep -c "^- \*\*" "$SCANNER_FILE" 2>/dev/null || echo "0")
  scanner_total=$((scanner_picks + scanner_leads))
  if [ "$scanner_total" -eq 0 ]; then
    scanner_status="empty"
    scanner_repair="Re-run scanner: cd /root/.openclaw/workspace && python3 scripts/linkedin-gulf-jobs.py. If still 0, check LinkedIn cookie freshness (linkedin.txt age), check JobSpy import works, check network connectivity."
  elif [ "$scanner_total" -lt 10 ]; then
    scanner_repair="Scanner degraded. Check: 1) LinkedIn cookie age (>3 days = refresh needed), 2) JobSpy rate limiting, 3) Search delay too low."
  fi
elif [ "$CAIRO_HOUR" -ge 7 ]; then
  scanner_status="missing"
  scanner_repair="Scanner cron didn't run. Check: 1) openclaw cron list for scanner job status, 2) Re-run manually: cd /root/.openclaw/workspace && python3 scripts/linkedin-gulf-jobs.py, 3) Check if script has syntax errors: python3 -c 'import py_compile; py_compile.compile(\"scripts/linkedin-gulf-jobs.py\")'"
fi

# ============================================================
# 9. CRON OUTPUT VALIDATION — check key crons produced output today
# ============================================================
cron_output_issues="[]"
cron_output_issues=$(python3 -c "
import json, os
from datetime import datetime

today = '${TODAY}'
issues = []

# Scanner output
scanner_f = '$WORKSPACE/jobs-bank/scraped/qualified-jobs-${TODAY}.md'
if not os.path.exists(scanner_f) and int('${CAIRO_HOUR}') >= 7:
    issues.append({'cron': 'Jobs Scanner', 'issue': 'No output file for today', 'severity': 'high', 'repair': 'cd /root/.openclaw/workspace && python3 scripts/linkedin-gulf-jobs.py'})
elif os.path.exists(scanner_f) and os.path.getsize(scanner_f) < 200:
    issues.append({'cron': 'Jobs Scanner', 'issue': 'Output file suspiciously small', 'severity': 'medium', 'repair': 'Check script logs, re-run scanner'})

# Engagement radar output
radar_f = '$WORKSPACE/linkedin/engagement/daily/${TODAY}.md'
if not os.path.exists(radar_f) and int('${CAIRO_HOUR}') >= 7:
    issues.append({'cron': 'Engagement Radar', 'issue': 'No output file for today', 'severity': 'medium', 'repair': 'cd /root/.openclaw/workspace && python3 scripts/linkedin-engagement-radar.py'})

# Briefing data JSON
briefing_f = '$WORKSPACE/jobs-bank/scraped/briefing-data-${TODAY}.json'
if not os.path.exists(briefing_f) and int('${CAIRO_HOUR}') >= 8:
    issues.append({'cron': 'Morning Briefing', 'issue': 'No briefing JSON for today', 'severity': 'high', 'repair': 'cd /root/.openclaw/workspace && python3 scripts/morning-briefing-orchestrator.py'})

print(json.dumps(issues))
" 2>/dev/null || echo "[]")

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
  "script_health": $script_health,
  "bloated_sessions": $bloated_sessions,
  "disk_usage_pct": $disk_usage_pct,
  "active_tasks_age_hours": $active_tasks_age,
  "upcoming_deadlines": $upcoming_deadlines,
  "model_fallbacks": $model_fallbacks,
  "scanner": {
    "status": "$scanner_status",
    "picks": $scanner_picks,
    "leads": $scanner_leads,
    "total": $scanner_total,
    "file": "$SCANNER_FILE",
    "repair_hint": "$scanner_repair"
  },
  "cron_output_issues": $cron_output_issues
}
EOF

# === CRON DASHBOARD SYNC ===
python3 -c "
import sys; sys.path.insert(0, '$WORKSPACE/scripts')
from notion_sync import sync_cron_dashboard_full
result = sync_cron_dashboard_full()
if result.get('failed', 0) > 0:
    for f in result.get('failures', []):
        print(f'CRON_FAIL: {f[\"name\"]}: {f[\"error\"][:80]}')
" 2>/dev/null > /tmp/cron_dashboard_check.txt || true

# === SCANNER TREND CHECK ===
scanner_trend_alert=""
if python3 -c "
import sys; sys.path.insert(0, '$WORKSPACE/scripts')
from notion_sync import get_scanner_trends
trends = get_scanner_trends()
if trends.get('alert'):
    print(trends['alert'])
if trends.get('cookie_alert'):
    print(trends['cookie_alert'])
" 2>/dev/null > /tmp/scanner_trend_check.txt; then
    scanner_trend_alert=$(cat /tmp/scanner_trend_check.txt)
fi

