#!/bin/bash
# Disk Health Check - Alert on threshold breaches
# Thresholds: 60% warning, 75% action, 85% critical

THRESHOLD_WARNING=60
THRESHOLD_ACTION=75
THRESHOLD_CRITICAL=85

LOG_FILE="/tmp/disk-health.log"
DISCORD_WEBHOOK_URL=""  # Optional: add Discord webhook for alerts

# Get disk usage percentage
USAGE=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
AVAILABLE=$(df -h / | tail -1 | awk '{print $4}')

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Log the check
echo "[$TIMESTAMP] Disk usage: ${USAGE}% (${AVAILABLE} available)" >> $LOG_FILE

# Check thresholds and alert
if [ "$USAGE" -ge "$THRESHOLD_CRITICAL" ]; then
    echo "[$TIMESTAMP] 🚨 CRITICAL: Disk at ${USAGE}% - Immediate cleanup needed!" >> $LOG_FILE
    echo "🚨 CRITICAL DISK ALERT: ${USAGE}% used (${AVAILABLE} free) - Immediate action required!"
elif [ "$USAGE" -ge "$THRESHOLD_ACTION" ]; then
    echo "[$TIMESTAMP] ⚠️ WARNING: Disk at ${USAGE}% - Cleanup recommended" >> $LOG_FILE
    echo "⚠️ DISK WARNING: ${USAGE}% used (${AVAILABLE} free) - Review recommended"
elif [ "$USAGE" -ge "$THRESHOLD_WARNING" ]; then
    echo "[$TIMESTAMP] 📊 INFO: Disk at ${USAGE}% - Monitor closely" >> $LOG_FILE
else
    echo "[$TIMESTAMP] ✅ OK: Disk at ${USAGE}% - Healthy" >> $LOG_FILE
fi

# Keep log clean (last 30 entries only)
tail -30 $LOG_FILE > ${LOG_FILE}.tmp && mv ${LOG_FILE}.tmp $LOG_FILE
