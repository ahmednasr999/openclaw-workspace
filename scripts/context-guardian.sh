#!/bin/bash
# context-guardian.sh
# EXTERNAL watchdog. Runs from an isolated cron (NOT the main session).
# Checks main session context %. If >= 75%:
#   1. Writes a flush summary directly to memory files (no NASR needed)
#   2. Commits to git
#   3. Sends Telegram alert to Ahmed
#   4. Writes a human-readable marker so next session knows what happened
#
# This script is intentionally simple: no Python, no JSON parsing beyond grep.
# It must work even when all LLM models are down.

THRESHOLD=75
ALERT_THRESHOLD=80
WORKSPACE="/root/.openclaw/workspace"
MEMORY="$WORKSPACE/memory"
ALERT_LOCK="/tmp/nasr-context-guardian.lock"
LOCK_TTL=600  # 10 min between alerts
LOG="$MEMORY/context-guardian.log"
DATE=$(date -u +%Y-%m-%d)
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
CAIRO=$(TZ="Africa/Cairo" date +"%Y-%m-%d %H:%M")

# ── 1. Get context % ─────────────────────────────────────────────────────────
# Extract % from the "agent:main:main" line only (first session, actual context)
# Pattern: "agent:main:main" ... "XXk/200k (YY%)" where YY is the percentage
PCT=$(openclaw status 2>/dev/null | grep "agent:main:main" | grep -oP '(?<=\()(\d+)(?=%\))' | head -1)

if [ -z "$PCT" ]; then
  echo "[$TS] ERROR: could not read context %" >> "$LOG"
  exit 1
fi

echo "[$TS] Context: ${PCT}%" >> "$LOG"

# ── 2. Below threshold — clean exit ──────────────────────────────────────────
if [ "$PCT" -lt "$THRESHOLD" ]; then
  # Remove stale lock if context recovered
  rm -f "$ALERT_LOCK"
  exit 0
fi

# ── 3. Check cooldown (alerts only) ─────────────────────────────────────────
CAN_ALERT=1
if [ -f "$ALERT_LOCK" ]; then
  LOCK_AGE=$(( $(date +%s) - $(stat -c%Y "$ALERT_LOCK" 2>/dev/null || echo 0) ))
  if [ "$LOCK_AGE" -lt "$LOCK_TTL" ]; then
    CAN_ALERT=0
    echo "[$TS] Context ${PCT}% — alert cooldown (${LOCK_AGE}s < ${LOCK_TTL}s)" >> "$LOG"
  fi
fi

echo "[$TS] THRESHOLD HIT: ${PCT}% >= ${THRESHOLD}% — executing external flush" >> "$LOG"

# ── 4. Write flush marker to daily log ───────────────────────────────────────
DAILY_LOG="$MEMORY/${DATE}.md"
cat >> "$DAILY_LOG" << EOF

---
## [AUTO-FLUSH] Context Guardian Triggered — $CAIRO Cairo

Context reached ${PCT}% (threshold: ${THRESHOLD}%).
External watchdog (context-guardian.sh) executed at $TS.

**Action taken:** Guardian committed memory state and alerted Ahmed.
**Status:** Session needs rotation. Start a fresh Telegram session to reset context.

### What was in flight at flush time:
- Review memory/active-tasks.md for current task state
- Review MEMORY.md for latest strategic context
- Check memory/${DATE}.md (this file) for today's session log

### Next session startup checklist:
1. Read SOUL.md, USER.md, MEMORY.md
2. Read memory/active-tasks.md
3. Read memory/pending-opus-topics.md
4. Read memory/${DATE}.md (today's log)
5. Confirm: "Session loaded fresh after context-guardian flush"
EOF

echo "[$TS] Wrote flush marker to $DAILY_LOG" >> "$LOG"

# ── 5. Commit everything to git ──────────────────────────────────────────────
cd "$WORKSPACE" && \
  git add -A && \
  git commit -m "auto-flush: context guardian triggered at ${PCT}% — $TS" \
    --author="NASR Context Guardian <nasr@openclaw>" \
    2>/dev/null && \
  git push 2>/dev/null

if [ $? -eq 0 ]; then
  echo "[$TS] Git commit + push OK" >> "$LOG"
else
  echo "[$TS] Git push failed (commit may still be local)" >> "$LOG"
fi

# ── 6. Send Telegram alert to Ahmed only at higher urgency ───────────────────
TELEGRAM_BOT_TOKEN=$(jq -r '.channels.telegram.botToken // empty' ~/.openclaw/openclaw.json 2>/dev/null)
TELEGRAM_CHAT_ID="866838380"

if [ "$PCT" -ge "$ALERT_THRESHOLD" ] && [ "$CAN_ALERT" -eq 1 ] && [ -n "$TELEGRAM_BOT_TOKEN" ]; then
  touch "$ALERT_LOCK"
  MSG="🚨 Context Guardian — Auto-Flush

Session context hit ${PCT}% (alert threshold: ${ALERT_THRESHOLD}%, flush threshold: ${THRESHOLD}%).

I've saved memory state and committed to git. Your session needs a fresh start.

Action: Start a new message to NASR in Telegram. The next session will load clean.

Time: $CAIRO Cairo"

  curl -sf -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    -d "text=${MSG}" \
    -d "parse_mode=HTML" \
    >> /dev/null 2>&1

  echo "[$TS] Telegram alert sent" >> "$LOG"
elif [ "$PCT" -lt "$ALERT_THRESHOLD" ]; then
  echo "[$TS] Flush executed at ${PCT}% without Telegram alert (<${ALERT_THRESHOLD}%)" >> "$LOG"
else
  echo "[$TS] Telegram alert skipped (cooldown or missing token)" >> "$LOG"
fi

echo "[$TS] Guardian flush complete" >> "$LOG"
exit 0
