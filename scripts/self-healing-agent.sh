#!/bin/bash
# ============================================================
# OpenClaw Self-Healing Repair Agent v2
# ============================================================
# Runs via system cron every 2 minutes.
# Detects gateway down > attempts repair > alerts Ahmed if stuck.
#
# v2 Changes:
# - Max 2 repair attempts per incident, then alert-only
# - Config backup/restore instead of live editing
# - Explicit NEVER CHANGE protections for Claude Code
# - Proper cooldown enforcement
#
# Created: 2026-03-08 | Updated: 2026-03-08
# ============================================================

set -euo pipefail

# --- Config ---
HEALTH_URL="http://127.0.0.1:18789/health"
CONFIG_FILE="/root/.openclaw/openclaw.json"
CONFIG_BACKUP="/root/.openclaw/openclaw.json.lastgood"
LOG_DIR="/tmp/openclaw"
LOG_FILE="${LOG_DIR}/openclaw-$(date -u +%Y-%m-%d).log"
REPAIR_LOG="${LOG_DIR}/repair-agent.log"
PLAYBOOK="/root/.openclaw/workspace/scripts/repair-playbook.md"
LOCKFILE="/tmp/openclaw/repair-agent.lock"
COOLDOWN_FILE="/tmp/openclaw/repair-agent.cooldown"
ATTEMPT_FILE="/tmp/openclaw/repair-agent.attempts"
COOLDOWN_SECONDS=600
MAX_ATTEMPTS=2

# Telegram
TG_TOKEN=$(python3 -c "import json; print(json.load(open('${CONFIG_FILE}'))['channels']['telegram']['botToken'])" 2>/dev/null || echo "")
TG_CHAT="866838380"

# --- Functions ---
log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%S)] $1" >> "$REPAIR_LOG"
}

send_telegram() {
  if [ -n "$TG_TOKEN" ]; then
    curl -sf -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
      -d "chat_id=${TG_CHAT}" \
      -d "parse_mode=HTML" \
      -d "text=$1" > /dev/null 2>&1 || true
  fi
}

cleanup_lock() {
  rm -f "$LOCKFILE"
}

# --- Guards ---
mkdir -p "$LOG_DIR"

# Cooldown check (hard enforcement)
if [ -f "$COOLDOWN_FILE" ]; then
  LAST=$(cat "$COOLDOWN_FILE" 2>/dev/null || echo 0)
  NOW=$(date +%s)
  ELAPSED=$((NOW - LAST))
  if [ "$ELAPSED" -lt "$COOLDOWN_SECONDS" ]; then
    exit 0
  fi
fi

# Lock to prevent parallel runs
if [ -f "$LOCKFILE" ]; then
  LOCK_AGE=$(( $(date +%s) - $(stat -c %Y "$LOCKFILE" 2>/dev/null || echo 0) ))
  if [ "$LOCK_AGE" -lt 300 ]; then
    exit 0
  fi
  rm -f "$LOCKFILE"
fi

# --- Health Check ---
HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
  # Gateway healthy. Reset attempt counter and save config as known-good.
  if [ -f "$ATTEMPT_FILE" ]; then
    rm -f "$ATTEMPT_FILE"
  fi
  # Save known-good config backup (only if config is valid JSON)
  if python3 -c "import json; json.load(open('${CONFIG_FILE}'))" 2>/dev/null; then
    cp -f "$CONFIG_FILE" "$CONFIG_BACKUP" 2>/dev/null || true
  fi
  exit 0
fi

# --- Gateway is DOWN ---
log "Gateway DOWN (HTTP: $HTTP_CODE). Checking attempt count."
touch "$LOCKFILE"
trap cleanup_lock EXIT

# Check attempt count
ATTEMPTS=0
if [ -f "$ATTEMPT_FILE" ]; then
  ATTEMPTS=$(cat "$ATTEMPT_FILE" 2>/dev/null || echo 0)
fi

if [ "$ATTEMPTS" -ge "$MAX_ATTEMPTS" ]; then
  log "Max attempts ($MAX_ATTEMPTS) reached. Alert only."
  send_telegram "🚨 Gateway DOWN — max repair attempts reached.

I tried $MAX_ATTEMPTS times and failed. Manual intervention needed.

Quick fixes:
1. <code>openclaw gateway stop; openclaw gateway start</code>
2. Check logs: <code>journalctl --user -u openclaw-gateway --since '10 min ago'</code>
3. Restore config: <code>cp ~/.openclaw/openclaw.json.lastgood ~/.openclaw/openclaw.json</code>"

  # Set cooldown so we don't spam alerts
  date +%s > "$COOLDOWN_FILE"
  exit 0
fi

# Increment attempt counter
ATTEMPTS=$((ATTEMPTS + 1))
echo "$ATTEMPTS" > "$ATTEMPT_FILE"
log "Repair attempt $ATTEMPTS of $MAX_ATTEMPTS"

# --- Step 1: Simple restart ---
log "Step 1: Simple restart..."
systemctl --user restart openclaw-gateway.service 2>/dev/null || true
sleep 8

HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
  log "Step 1 SUCCESS."
  send_telegram "🔧 Self-Healing: Gateway restarted successfully ✅ (attempt $ATTEMPTS)"
  rm -f "$ATTEMPT_FILE"
  date +%s > "$COOLDOWN_FILE"
  exit 0
fi

# --- Step 2: Try restoring last-good config ---
log "Step 1 FAILED. Step 2: Restoring last-good config..."
if [ -f "$CONFIG_BACKUP" ]; then
  cp -f "$CONFIG_BACKUP" "$CONFIG_FILE"
  systemctl --user restart openclaw-gateway.service 2>/dev/null || true
  sleep 8

  HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ]; then
    log "Step 2 SUCCESS: Restored last-good config."
    send_telegram "🔧 Self-Healing: Gateway restored from last-good config ✅ (attempt $ATTEMPTS)"
    rm -f "$ATTEMPT_FILE"
    date +%s > "$COOLDOWN_FILE"
    exit 0
  fi
fi

# --- Step 3: Claude Code diagnosis (LAST RESORT) ---
log "Step 2 FAILED. Step 3: Invoking Claude Code for diagnosis..."

LAST_30_LINES=$(tail -30 "$LOG_FILE" 2>/dev/null || echo "No log file found")
JOURNAL_LINES=$(journalctl --user -u openclaw-gateway --since "5 min ago" --no-pager 2>/dev/null | tail -30 || echo "No journal")

PROMPT="You are a repair agent for OpenClaw gateway. The gateway is down and simple restart + config restore both failed.

LAST 30 LINES OF GATEWAY LOG:
${LAST_30_LINES}

LAST 30 LINES OF JOURNAL:
${JOURNAL_LINES}

REPAIR PLAYBOOK:
$(cat "$PLAYBOOK" 2>/dev/null || echo "No playbook found")

YOUR TASK:
1. Diagnose the root cause from the logs
2. Apply a MINIMAL fix (smallest change possible)
3. Restart: systemctl --user restart openclaw-gateway.service
4. Verify: curl -sf http://127.0.0.1:18789/health
5. Output a one-line summary

ABSOLUTE RULES (VIOLATION = FAILURE):
- NEVER change the Telegram bot token or disable Telegram
- NEVER change channels.slack.botToken or channels.slack.appToken
- NEVER change the default model (agents.defaults.model.primary)
- NEVER change model fallback chain
- NEVER make openclaw.json read-only (chmod 444)
- NEVER add new keys to openclaw.json (no hooks, no new sections)
- NEVER delete openclaw.json or any session files
- ONLY allowed config changes: disable a broken channel, change a specific model override
- If you cannot identify the cause: output 'REPAIR_FAILED: [reason]' and DO NOTHING
- When in doubt, do nothing. Alert the user instead of guessing."

REPAIR_OUTPUT=$(claude --print --permission-mode bypassPermissions "$PROMPT" 2>&1 | tail -50)
log "Claude Code output: ${REPAIR_OUTPUT}"

# --- Verify ---
sleep 5
HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
  log "Step 3 SUCCESS."
  SUMMARY=$(echo "$REPAIR_OUTPUT" | tail -5 | head -c 500)
  send_telegram "🔧 Self-Healing: Claude Code repaired gateway ✅ (attempt $ATTEMPTS)

<b>Fix:</b>
<pre>$(echo "$SUMMARY" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')</pre>"
  rm -f "$ATTEMPT_FILE"
else
  log "Step 3 FAILED."
  SUMMARY=$(echo "$REPAIR_OUTPUT" | tail -10 | head -c 500)
  send_telegram "⚠️ Self-Healing: REPAIR FAILED (attempt $ATTEMPTS of $MAX_ATTEMPTS)

<b>Diagnosis:</b>
<pre>$(echo "$SUMMARY" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')</pre>

$([ "$ATTEMPTS" -ge "$MAX_ATTEMPTS" ] && echo "Max attempts reached. Waiting for manual fix." || echo "Will retry in 10 minutes.")"
fi

date +%s > "$COOLDOWN_FILE"
