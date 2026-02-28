#!/bin/bash
BOT_TOKEN=$(python3 -c "import json; print(json.load(open('/root/.openclaw/openclaw.json'))['channels']['telegram']['botToken'])")
CHAT_ID="866838380"
FAILED=""

RESULT=$(openclaw models status --status-plain 2>/dev/null)
echo "$RESULT" | grep -qi "error\|cooldown\|expired\|invalid" && FAILED="$FAILED\n❌ Model auth issues detected"
openclaw health 2>/dev/null | grep -qi "error\|unreachable" && FAILED="$FAILED\n❌ Gateway unhealthy"
openclaw channels status 2>/dev/null | grep -qi "error\|stopped\|disconnected" && FAILED="$FAILED\n❌ Telegram channel down"

if [ -n "$FAILED" ]; then
  MSG="🔑 Daily Health Check FAILED — $(TZ=Africa/Cairo date '+%Y-%m-%d %H:%M')$(echo -e $FAILED)\n\nRun: openclaw models status && openclaw channels status"
  curl -sf -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d "chat_id=${CHAT_ID}" -d "text=${MSG}" > /dev/null 2>&1
fi
