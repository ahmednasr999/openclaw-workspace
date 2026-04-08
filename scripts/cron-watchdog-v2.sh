#!/bin/bash
# Cron Watchdog + Heartbeat v2 - Combined health check
# Runs every 2 hours, checks for cron failures AND basic system health

echo "🔍 Running health checks..."

# 1. Gateway health
GATEWAY_PID=$(pgrep -f 'openclaw.*gateway' | head -1)
if [ -z "$GATEWAY_PID" ]; then
    echo "🔴 Gateway DOWN - PID not found"
    GATEWAY_STATUS="down"
else
    echo "✅ Gateway running (PID: $GATEWAY_PID)"
    GATEWAY_STATUS="running"
fi

# 2. Disk usage
DISK_USAGE=$(df / --output=pcent 2>/dev/null | tail -1 | tr -d '%')
if [ "$DISK_USAGE" -ge 85 ]; then
    echo "🔴 Disk CRITICAL: ${DISK_USAGE}%"
elif [ "$DISK_USAGE" -ge 75 ]; then
    echo "🟡 Disk WARNING: ${DISK_USAGE}%"
else
    echo "✅ Disk OK: ${DISK_USAGE}%"
fi

# 3. Active tasks freshness
if [ -f /root/.openclaw/workspace/memory/active-tasks.md ]; then
    TASK_AGE=$(($(date +%s) - $(stat -c %Y /root/.openclaw/workspace/memory/active-tasks.md 2>/dev/null || echo 0) | bc) / 3600)
    if [ "$TASK_AGE" -gt 48 ]; then
        echo "🟡 active-tasks.md stale: ${TASK_AGE}h"
    else
        echo "✅ active-tasks.md fresh: ${TASK_AGE}h"
    fi
fi

# 4. Check scanner output (jobs radar)
CAIRO_HOUR=$(TZ=Africa/Cairo date +%H 2>/dev/null || echo "0")
TODAY=$(TZ=Africa/Cairo date +%Y-%m-%d 2>/dev/null || echo "")
SCANNER_FILE="/root/.openclaw/workspace/jobs-bank/scraped/qualified-jobs-${TODAY}.md"
if [ "$CAIRO_HOUR" -ge 7 ] && [ -f "$SCANNER_FILE" ]; then
    JOBS_COUNT=$(grep -c '##\|linkedin.com/jobs' "$SCANNER_FILE" 2>/dev/null || echo 0)
    if [ "$JOBS_COUNT" -lt 10 ]; then
        echo "🟡 Scanner degraded: ${JOBS_COUNT} jobs"
    else
        echo "✅ Scanner OK: ${JOBS_COUNT} jobs"
    fi
elif [ "$CAIRO_HOUR" -ge 7 ]; then
    echo "🔴 Scanner missing: no output for today"
fi

# 5. Cron failures (via openclaw cron list)
echo ""
echo "📋 Checking cron status..."
CRON_OUTPUT=$(openclaw cron list 2>&1)
ERROR_CRONS=$(echo "$CRON_OUTPUT" | grep -E 'error|warning' | wc -l)
if [ "$ERROR_CRONS" -gt 0 ]; then
    echo "🔴 $ERROR_CRONS crons in error state:"
    echo "$CRON_OUTPUT" | grep -E 'error|warning' | head -5
else
    echo "✅ All crons OK"
fi

# 6. Session size check
echo ""
echo "📊 Checking sessions..."
BLOATED=0
for f in /root/.openclaw/sessions/*.json; do
    [ -f "$f" ] || continue
    SIZE=$(stat -c %s "$f" 2>/dev/null || echo 0)
    if [ "$SIZE" -gt 5242880 ]; then
        BLOATED=$((BLOATED + 1))
    fi
done
if [ "$BLOATED" -gt 0 ]; then
    echo "🟡 $BLOATED bloated sessions detected"
else
    echo "✅ No bloated sessions"
fi

echo ""
echo "🏁 Health check complete"
