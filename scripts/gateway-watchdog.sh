#!/bin/bash
LOG="/tmp/openclaw/openclaw-$(date -u +%Y-%m-%d).log"
BOT_TOKEN=$(python3 -c "import json; print(json.load(open('/root/.openclaw/openclaw.json'))['channels']['telegram']['botToken'])")
CHAT_ID="866838380"

COOLDOWN_SECONDS=900
STAMP_FILE="/tmp/openclaw/gateway-watchdog.last"
NOW=$(date +%s)
LAST=0
[ -f "$STAMP_FILE" ] && LAST=$(cat "$STAMP_FILE" 2>/dev/null || echo 0)

ERRORS=$(grep "$(date -u +%Y-%m-%dT%H:%M 2>/dev/null)" "$LOG" 2>/dev/null | grep -c "401.*authentication_error" || echo 0)
ERRORS=$((ERRORS + $(grep "$(date -u -d '-5 minutes' +%Y-%m-%dT%H:%M 2>/dev/null)" "$LOG" 2>/dev/null | grep -c "401.*authentication_error" || echo 0)))

if [ "$ERRORS" -gt 5 ]; then
  if [ $((NOW - LAST)) -lt "$COOLDOWN_SECONDS" ]; then
    exit 0
  fi

  echo "$NOW" > "$STAMP_FILE"
  pkill -f openclaw-gateway
  sleep 3
  nohup openclaw gateway --port 18789 > /tmp/gateway-restart.log 2>&1 &
  curl -sf -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d "chat_id=${CHAT_ID}" \
    -d "text=🔄 Gateway Watchdog: Detected ${ERRORS} auth errors in 5min. Auto-restarted. Cooldown 15m active." > /dev/null 2>&1
fi
