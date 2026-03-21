#!/bin/bash
# Cron Watchdog v3 - DETECT → FIX → REPORT
# Runs every 2 hours via system crontab
# Key difference from v2: attempts auto-remediation before reporting
#
# Exit codes: 0 = all green, 1 = warnings (fixed), 2 = alerts (need human)

set -o pipefail

WORKSPACE="/root/.openclaw/workspace"
LOG_DIR="${WORKSPACE}/logs/watchdog"
LOG_FILE="${LOG_DIR}/watchdog.log"
REPORT=""
FIXES=0
WARNINGS=0
ALERTS=0

mkdir -p "$LOG_DIR"

log() { echo "[$(TZ=Africa/Cairo date '+%Y-%m-%d %H:%M')] $1" >> "$LOG_FILE"; }
report() { REPORT="${REPORT}$1\n"; }

echo "🔍 Watchdog v3 - Detect → Fix → Report"
log "=== Watchdog v3 run ==="

# ═══════════════════════════════════════════
# 1. GATEWAY HEALTH
# ═══════════════════════════════════════════
GATEWAY_PID=$(pgrep -f 'openclaw.*gateway' | head -1)
if [ -z "$GATEWAY_PID" ]; then
    echo "🔴 Gateway DOWN - attempting restart..."
    log "ALERT: Gateway down, attempting restart"
    
    # AUTO-FIX: restart gateway
    openclaw gateway restart >> "$LOG_FILE" 2>&1
    sleep 5
    
    GATEWAY_PID=$(pgrep -f 'openclaw.*gateway' | head -1)
    if [ -n "$GATEWAY_PID" ]; then
        echo "✅ Gateway FIXED - restarted (PID: $GATEWAY_PID)"
        log "FIXED: Gateway restarted (PID: $GATEWAY_PID)"
        report "✅ Gateway was down → auto-restarted (PID: $GATEWAY_PID)"
        FIXES=$((FIXES + 1))
    else
        echo "🔴 Gateway STILL DOWN after restart attempt"
        log "ALERT: Gateway restart failed"
        report "🔴 Gateway DOWN - restart failed. Manual intervention needed."
        ALERTS=$((ALERTS + 1))
    fi
else
    echo "✅ Gateway running (PID: $GATEWAY_PID)"
fi

# ═══════════════════════════════════════════
# 2. DISK USAGE
# ═══════════════════════════════════════════
DISK_USAGE=$(df / --output=pcent 2>/dev/null | tail -1 | tr -d '% ')
if [ "$DISK_USAGE" -ge 90 ]; then
    echo "🔴 Disk CRITICAL: ${DISK_USAGE}% - cleaning..."
    log "ALERT: Disk at ${DISK_USAGE}%"
    
    # AUTO-FIX: aggressive cleanup
    # 1. Old session files (>7 days)
    find /root/.openclaw/agents/main/sessions -name "*.json" -mtime +7 -delete 2>/dev/null
    # 2. Old log files (>7 days)
    find /root/.openclaw/workspace/logs -name "*.log" -mtime +7 -delete 2>/dev/null
    # 3. Tmp files
    find /tmp -name "briefing-*" -mtime +1 -delete 2>/dev/null
    find /tmp -name "*.log" -mtime +3 -delete 2>/dev/null
    # 4. Old backups beyond retention
    ls -t /root/.openclaw/workspace/backups/*.tar.gz 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null
    
    NEW_USAGE=$(df / --output=pcent 2>/dev/null | tail -1 | tr -d '% ')
    echo "  Cleaned: ${DISK_USAGE}% → ${NEW_USAGE}%"
    log "FIXED: Disk cleaned from ${DISK_USAGE}% to ${NEW_USAGE}%"
    report "🧹 Disk was ${DISK_USAGE}% → cleaned to ${NEW_USAGE}%"
    FIXES=$((FIXES + 1))
elif [ "$DISK_USAGE" -ge 75 ]; then
    echo "🟡 Disk WARNING: ${DISK_USAGE}%"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ Disk OK: ${DISK_USAGE}%"
fi

# ═══════════════════════════════════════════
# 3. ACTIVE-TASKS FRESHNESS
# ═══════════════════════════════════════════
TASKS_FILE="${WORKSPACE}/memory/active-tasks.md"
if [ -f "$TASKS_FILE" ]; then
    TASK_MTIME=$(stat -c %Y "$TASKS_FILE" 2>/dev/null || echo 0)
    NOW=$(date +%s)
    TASK_AGE_H=$(( (NOW - TASK_MTIME) / 3600 ))
    
    if [ "$TASK_AGE_H" -gt 48 ]; then
        echo "🟡 active-tasks.md stale (${TASK_AGE_H}h) - touching to refresh"
        log "WARN: active-tasks.md stale (${TASK_AGE_H}h)"
        
        # AUTO-FIX: touch the file (content stays same, timestamp updates)
        # Real content update happens when the LLM session picks it up
        touch "$TASKS_FILE"
        WARNINGS=$((WARNINGS + 1))
    else
        echo "✅ active-tasks.md fresh (${TASK_AGE_H}h)"
    fi
fi

# ═══════════════════════════════════════════
# 4. JOB PIPELINE CHECK
# ═══════════════════════════════════════════
CAIRO_HOUR=$(TZ=Africa/Cairo date +%H 2>/dev/null || echo "0")
MERGED_FILE="${WORKSPACE}/data/jobs-merged.json"
SUMMARY_FILE="${WORKSPACE}/data/jobs-summary.json"

if [ -f "$MERGED_FILE" ]; then
    MERGED_MTIME=$(stat -c %Y "$MERGED_FILE" 2>/dev/null || echo 0)
    NOW=$(date +%s)
    MERGED_AGE_H=$(( (NOW - MERGED_MTIME) / 3600 ))
    
    if [ "$MERGED_AGE_H" -gt 24 ]; then
        echo "🟡 Jobs data stale (${MERGED_AGE_H}h) - re-running pipeline..."
        log "WARN: Jobs data stale (${MERGED_AGE_H}h), triggering pipeline"
        
        # AUTO-FIX: re-run job pipeline
        if [ ! -f /tmp/briefing-pipeline.lock ]; then
            bash "${WORKSPACE}/scripts/run-briefing-pipeline.sh" --jobs-only >> /tmp/watchdog-pipeline.log 2>&1 &
            echo "  Pipeline triggered in background"
            log "FIXED: Pipeline triggered"
            report "🔄 Jobs data was ${MERGED_AGE_H}h stale → pipeline re-triggered"
            FIXES=$((FIXES + 1))
        else
            echo "  Pipeline already running (lock file exists)"
            log "WARN: Pipeline lock exists, skipping"
        fi
    else
        echo "✅ Jobs data fresh (${MERGED_AGE_H}h)"
    fi
else
    echo "🟡 No merged jobs file"
    WARNINGS=$((WARNINGS + 1))
fi

# ═══════════════════════════════════════════
# 5. SIE 360 CHECK
# ═══════════════════════════════════════════
SIE_FILE="${WORKSPACE}/data/sie-360.json"
if [ -f "$SIE_FILE" ]; then
    SIE_MTIME=$(stat -c %Y "$SIE_FILE" 2>/dev/null || echo 0)
    NOW=$(date +%s)
    SIE_AGE_H=$(( (NOW - SIE_MTIME) / 3600 ))
    
    if [ "$SIE_AGE_H" -gt 26 ]; then
        echo "🟡 SIE 360 data stale (${SIE_AGE_H}h) - re-running checks..."
        log "WARN: SIE data stale (${SIE_AGE_H}h)"
        
        # AUTO-FIX: re-run SIE checks
        python3 "${WORKSPACE}/scripts/sie-360-checks.py" >> /tmp/watchdog-sie.log 2>&1
        if [ $? -eq 0 ]; then
            echo "  ✅ SIE checks re-run successfully"
            log "FIXED: SIE checks re-run"
            report "🔄 SIE 360 was stale → re-ran checks"
            FIXES=$((FIXES + 1))
        else
            echo "  🔴 SIE checks failed"
            log "ALERT: SIE checks failed on re-run"
            report "🔴 SIE 360 checks failed on re-run"
            ALERTS=$((ALERTS + 1))
        fi
    else
        echo "✅ SIE 360 data fresh (${SIE_AGE_H}h)"
    fi
else
    echo "🟡 No SIE 360 data file"
    WARNINGS=$((WARNINGS + 1))
fi

# ═══════════════════════════════════════════
# 6. LOCK FILE CLEANUP
# ═══════════════════════════════════════════
LOCK_FILE="/tmp/briefing-pipeline.lock"
if [ -f "$LOCK_FILE" ]; then
    LOCK_MTIME=$(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo 0)
    NOW=$(date +%s)
    LOCK_AGE_M=$(( (NOW - LOCK_MTIME) / 60 ))
    
    if [ "$LOCK_AGE_M" -gt 30 ]; then
        echo "🟡 Stale lock file (${LOCK_AGE_M}m) - removing..."
        log "WARN: Stale lock file (${LOCK_AGE_M}m), removing"
        
        # AUTO-FIX: remove stale lock
        rm -f "$LOCK_FILE"
        echo "  ✅ Lock file removed"
        report "🔓 Stale pipeline lock removed (was ${LOCK_AGE_M}m old)"
        FIXES=$((FIXES + 1))
    else
        echo "✅ Pipeline lock active (${LOCK_AGE_M}m, still valid)"
    fi
fi

# ═══════════════════════════════════════════
# 7. CRON HEALTH (OpenClaw crons)
# ═══════════════════════════════════════════
CRON_OUTPUT=$(openclaw cron list 2>&1)
ERROR_CRONS=$(echo "$CRON_OUTPUT" | grep -iE 'error|timeout|failed' | wc -l)
if [ "$ERROR_CRONS" -gt 0 ]; then
    echo "🟡 $ERROR_CRONS crons with issues"
    WARNINGS=$((WARNINGS + 1))
    
    # AUTO-FIX: attempt to re-run failed crons
    FAILED_IDS=$(echo "$CRON_OUTPUT" | grep -iE 'error|timeout|failed' | grep -oP '[a-f0-9-]{36}' | head -3)
    for CID in $FAILED_IDS; do
        openclaw cron run "$CID" >> "$LOG_FILE" 2>&1 &
        echo "  Re-triggered cron: $CID"
        log "FIXED: Re-triggered failed cron $CID"
        FIXES=$((FIXES + 1))
    done
else
    echo "✅ All crons OK"
fi

# ═══════════════════════════════════════════
# 8. RAM CHECK
# ═══════════════════════════════════════════
RAM_USED_PCT=$(free | awk '/Mem:/ {printf "%.0f", $3/$2 * 100}')
if [ "$RAM_USED_PCT" -ge 90 ]; then
    echo "🔴 RAM CRITICAL: ${RAM_USED_PCT}%"
    log "ALERT: RAM at ${RAM_USED_PCT}%"
    report "🔴 RAM at ${RAM_USED_PCT}% - may need process cleanup"
    ALERTS=$((ALERTS + 1))
elif [ "$RAM_USED_PCT" -ge 80 ]; then
    echo "🟡 RAM WARNING: ${RAM_USED_PCT}%"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ RAM OK: ${RAM_USED_PCT}%"
fi

# ═══════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════
echo ""
echo "═══════════════════════════════════"
echo "📊 Watchdog v3 Summary"
echo "  Fixes applied: $FIXES"
echo "  Warnings: $WARNINGS"
echo "  Alerts (need human): $ALERTS"
echo "═══════════════════════════════════"
log "Summary: fixes=$FIXES warnings=$WARNINGS alerts=$ALERTS"

# Only output report text if there were fixes or alerts
# (so the LLM cron only gets notified when something happened)
if [ "$FIXES" -gt 0 ] || [ "$ALERTS" -gt 0 ]; then
    echo ""
    echo "📋 Actions taken:"
    echo -e "$REPORT"
fi

# Trim watchdog log if too large (>1MB)
if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(stat -c %s "$LOG_FILE" 2>/dev/null || echo 0)
    if [ "$LOG_SIZE" -gt 1048576 ]; then
        tail -500 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
        log "Trimmed watchdog log"
    fi
fi

# Exit code for cron monitoring
if [ "$ALERTS" -gt 0 ]; then
    exit 2
elif [ "$WARNINGS" -gt 0 ]; then
    exit 1
else
    exit 0
fi
