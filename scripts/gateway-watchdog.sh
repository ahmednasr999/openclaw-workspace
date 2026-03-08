#!/bin/bash
# Gateway Watchdog v2 — Enhanced with log capture + token health check
# Updated: 2026-03-08

LOG="/tmp/openclaw/openclaw-$(date -u +%Y-%m-%d).log"
BOT_TOKEN=$(python3 -c "import json; print(json.load(open('/root/.openclaw/openclaw.json'))['channels']['telegram']['botToken'])")
CHAT_ID="866838380"

COOLDOWN_SECONDS=900
STAMP_FILE="/tmp/openclaw/gateway-watchdog.last"
RESTART_COUNT_FILE="/tmp/openclaw/gateway-watchdog.restarts"
NOW=$(date +%s)
LAST=0
[ -f "$STAMP_FILE" ] && LAST=$(cat "$STAMP_FILE" 2>/dev/null || echo 0)

# Count recent errors (auth failures, crashes, unhandled rejections)
ERRORS=$(tail -200 "$LOG" 2>/dev/null | grep -cE "401.*authentication_error|account_inactive|unhandledRejection|FATAL|gateway.*crash" || echo 0)

if [ "$ERRORS" -gt 5 ]; then
  if [ $((NOW - LAST)) -lt "$COOLDOWN_SECONDS" ]; then
    exit 0
  fi

  echo "$NOW" > "$STAMP_FILE"

  # Track restart count
  RESTARTS=0
  [ -f "$RESTART_COUNT_FILE" ] && RESTARTS=$(cat "$RESTART_COUNT_FILE" 2>/dev/null || echo 0)
  RESTARTS=$((RESTARTS + 1))
  echo "$RESTARTS" > "$RESTART_COUNT_FILE"

  # Capture last 30 lines of logs for diagnosis
  LOG_TAIL=$(tail -30 "$LOG" 2>/dev/null | head -c 3000)

  if [ "$RESTARTS" -le 2 ]; then
    # Attempt restart
    pkill -f openclaw-gateway
    sleep 3
    nohup openclaw gateway --port 18789 > /tmp/gateway-restart.log 2>&1 &

    curl -sf -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
      -d "chat_id=${CHAT_ID}" \
      -d "parse_mode=HTML" \
      -d "text=🔄 Gateway Watchdog: Detected ${ERRORS} errors. Auto-restart attempt ${RESTARTS}/2.

<pre>$(echo "$LOG_TAIL" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g' | tail -15)</pre>" > /dev/null 2>&1
  else
    # 2+ restarts failed — escalate with full log context
    curl -sf -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
      -d "chat_id=${CHAT_ID}" \
      -d "parse_mode=HTML" \
      -d "text=⚠️ Watchdog: Gateway down after ${RESTARTS} restart attempts. Escalating.

<b>Last 15 lines of log:</b>
<pre>$(echo "$LOG_TAIL" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g' | tail -15)</pre>

<b>Likely cause:</b> Check for account_inactive, bad token, or unhandled rejection above.
<b>Quick fix:</b> openclaw config set channels.slack.enabled false then restart." > /dev/null 2>&1

    # Reset restart counter after escalation
    echo "0" > "$RESTART_COUNT_FILE"
  fi
else
  # No errors — reset restart counter
  [ -f "$RESTART_COUNT_FILE" ] && echo "0" > "$RESTART_COUNT_FILE"
fi
