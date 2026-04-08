#!/bin/bash
# Channel Token Health Check — validates all configured channel tokens
# Runs weekly via cron. Alerts on Telegram if any token is dead.
# Updated: 2026-03-08

BOT_TOKEN=$(python3 -c "import json; print(json.load(open('/root/.openclaw/openclaw.json'))['channels']['telegram']['botToken'])")
CHAT_ID="866838380"
ISSUES=""

# 1. Check Telegram bot token
TG_RESULT=$(curl -sf "https://api.telegram.org/bot${BOT_TOKEN}/getMe" 2>/dev/null)
TG_OK=$(echo "$TG_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('ok', False))" 2>/dev/null)
if [ "$TG_OK" != "True" ]; then
  ISSUES="${ISSUES}🔴 Telegram bot token: INVALID\n"
fi

# 2. Check Slack bot token (if enabled)
SLACK_ENABLED=$(python3 -c "import json; c=json.load(open('/root/.openclaw/openclaw.json')); print(c.get('channels',{}).get('slack',{}).get('enabled', False))" 2>/dev/null)
if [ "$SLACK_ENABLED" = "True" ]; then
  SLACK_TOKEN=$(python3 -c "import json; print(json.load(open('/root/.openclaw/openclaw.json'))['channels']['slack']['botToken'])" 2>/dev/null)
  SLACK_RESULT=$(curl -sf -H "Authorization: Bearer ${SLACK_TOKEN}" "https://slack.com/api/auth.test" 2>/dev/null)
  SLACK_OK=$(echo "$SLACK_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('ok', False))" 2>/dev/null)
  SLACK_ERR=$(echo "$SLACK_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('error', 'none'))" 2>/dev/null)
  if [ "$SLACK_OK" != "True" ]; then
    ISSUES="${ISSUES}🔴 Slack bot token: ${SLACK_ERR}\n"
  fi

  # Check Slack app token
  SLACK_APP_TOKEN=$(python3 -c "import json; print(json.load(open('/root/.openclaw/openclaw.json'))['channels']['slack']['appToken'])" 2>/dev/null)
  SLACK_APP_RESULT=$(curl -sf -X POST -H "Authorization: Bearer ${SLACK_APP_TOKEN}" "https://slack.com/api/auth.test" 2>/dev/null)
  SLACK_APP_OK=$(echo "$SLACK_APP_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('ok', False))" 2>/dev/null)
  if [ "$SLACK_APP_OK" != "True" ]; then
    ISSUES="${ISSUES}🟡 Slack app token: may be invalid (non-critical)\n"
  fi
fi

# 3. Report
if [ -n "$ISSUES" ]; then
  curl -sf -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d "chat_id=${CHAT_ID}" \
    -d "text=🛡️ Weekly Token Health Check — ISSUES FOUND

${ISSUES}
Fix before next gateway restart to prevent crash." > /dev/null 2>&1
fi
