#!/usr/bin/env bash
# OpenClaw Self-Healing Watchdog
# Layer 1: Bash restarts (free, handles 90% of failures)
# Layer 2: Claude Code CLI repair (Sonnet, pay-per-token, complex failures only)
#
# Install: cron every 3 minutes
# Dependencies: claude CLI (@anthropic-ai/claude-code), curl, jq
# Created: 2026-03-04

set -euo pipefail

# --- Config ---
GATEWAY_URL="http://127.0.0.1:18789"
HEALTH_ENDPOINT="${GATEWAY_URL}/health"
STATE_DIR="/root/.openclaw/workspace/logs/watchdog"
FAIL_COUNTER="${STATE_DIR}/consecutive-failures"
REPAIR_LOG="${STATE_DIR}/repair-history.jsonl"
LOCK_FILE="${STATE_DIR}/repair.lock"
MAX_BASH_RETRIES=2          # After this many failed restarts, escalate to Claude
COOLDOWN_SECONDS=300        # 5 min cooldown between Claude repairs
TELEGRAM_BOT_TOKEN=""       # Filled from openclaw config if available
TELEGRAM_CHAT_ID="866838380"

# Extract Anthropic API key from openclaw config
ANTHROPIC_API_KEY=$(grep -oP '"apiKey"\s*:\s*"(sk-ant[^"]+)"' /root/.openclaw/openclaw.json 2>/dev/null | head -1 | cut -d'"' -f4 || echo "")

mkdir -p "$STATE_DIR"

# --- Functions ---

log() {
    echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] $1" >> "${STATE_DIR}/watchdog.log"
}

notify_telegram() {
    local msg="$1"
    # Try to extract bot token from openclaw config
    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
        TELEGRAM_BOT_TOKEN=$(grep -oP '"botToken"\s*:\s*"([^"]+)"' /root/.openclaw/openclaw.json 2>/dev/null | head -1 | cut -d'"' -f4 || echo "")
    fi
    if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${TELEGRAM_CHAT_ID}" \
            -d "text=${msg}" \
            -d "parse_mode=HTML" > /dev/null 2>&1 || true
    fi
}

check_health() {
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$HEALTH_ENDPOINT" 2>/dev/null || echo "000")
    if [ "$http_code" = "200" ]; then
        return 0
    fi
    # Fallback: check if process is running
    if pgrep -f "openclaw-gateway" > /dev/null 2>&1; then
        # Process alive but not responding, still unhealthy
        return 1
    fi
    return 1
}

get_fail_count() {
    if [ -f "$FAIL_COUNTER" ]; then
        cat "$FAIL_COUNTER"
    else
        echo "0"
    fi
}

set_fail_count() {
    echo "$1" > "$FAIL_COUNTER"
}

bash_restart() {
    log "BASH RESTART: Attempting gateway restart (attempt $1)"
    
    # Kill any zombie processes first
    pkill -f "openclaw-gateway" 2>/dev/null || true
    sleep 2
    
    # Restart via openclaw CLI
    openclaw gateway start > /dev/null 2>&1 &
    sleep 5
    
    # Verify
    if check_health; then
        log "BASH RESTART: Success after attempt $1"
        notify_telegram "🟢 <b>Watchdog:</b> Gateway recovered after bash restart (attempt $1)"
        set_fail_count 0
        return 0
    fi
    return 1
}

claude_repair() {
    log "CLAUDE REPAIR: Escalating to Claude Code CLI"
    
    # Check cooldown
    if [ -f "$LOCK_FILE" ]; then
        local last_repair
        last_repair=$(cat "$LOCK_FILE")
        local now
        now=$(date +%s)
        local diff=$((now - last_repair))
        if [ "$diff" -lt "$COOLDOWN_SECONDS" ]; then
            log "CLAUDE REPAIR: Cooldown active (${diff}s/${COOLDOWN_SECONDS}s). Skipping."
            return 1
        fi
    fi
    
    # Set lock
    date +%s > "$LOCK_FILE"
    
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        log "CLAUDE REPAIR: No API key found. Cannot proceed."
        notify_telegram "🔴 <b>Watchdog:</b> Claude repair needed but no API key configured"
        return 1
    fi
    
    # Collect diagnostic context
    local diag_file="${STATE_DIR}/diagnostic-context.txt"
    {
        echo "=== GATEWAY STATUS ==="
        openclaw status 2>&1 || echo "openclaw status failed"
        echo ""
        echo "=== PROCESS LIST ==="
        ps aux | grep -E "openclaw|node|gateway" | grep -v grep
        echo ""
        echo "=== RECENT LOGS ==="
        journalctl -u openclaw-gateway --no-pager -n 50 2>/dev/null || echo "No journalctl logs"
        echo ""
        echo "=== DISK SPACE ==="
        df -h / /root
        echo ""
        echo "=== MEMORY ==="
        free -h
        echo ""
        echo "=== OPENCLAW CONFIG (redacted) ==="
        cat /root/.openclaw/openclaw.json 2>/dev/null | sed 's/"apiKey"[^,]*/"apiKey": "REDACTED"/g; s/"botToken"[^,]*/"botToken": "REDACTED"/g; s/"token"[^,]*/"token": "REDACTED"/g'
    } > "$diag_file" 2>&1
    
    # Invoke Claude Code with repair prompt
    local repair_output="${STATE_DIR}/last-repair-output.txt"
    
    ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" claude -p \
        "You are the OpenClaw emergency repair agent on an Ubuntu VPS.

The OpenClaw gateway is DOWN and bash restart attempts have failed.

RULES:
- Diagnose the root cause from the context below
- Fix the issue: config errors, port conflicts, zombie processes, disk full, OOM, whatever it is
- Restart the gateway with: openclaw gateway start
- Do NOT modify memory files, MEMORY.md, or any markdown in /root/.openclaw/workspace/memory/
- Do NOT git push
- Do NOT install new packages unless absolutely required for the fix
- After fix, verify health at http://127.0.0.1:18789/health
- Be surgical: fix only what's broken

DIAGNOSTIC CONTEXT:
$(cat "$diag_file")

Fix the gateway and confirm it's healthy." \
        --max-turns 10 \
        --allowedTools "Bash(command:*)" "Read" \
        > "$repair_output" 2>&1
    
    local exit_code=$?
    
    # Check if repair worked
    sleep 5
    if check_health; then
        log "CLAUDE REPAIR: Success! Gateway restored."
        notify_telegram "🟢 <b>Watchdog:</b> Claude Code repaired the gateway successfully. See repair log for details."
        set_fail_count 0
        
        # Log repair event
        echo "{\"time\":\"$(date -u -Iseconds)\",\"type\":\"claude_repair\",\"result\":\"success\",\"exit_code\":$exit_code}" >> "$REPAIR_LOG"
        return 0
    else
        log "CLAUDE REPAIR: Failed. Manual intervention needed."
        notify_telegram "🔴 <b>Watchdog:</b> Claude Code repair FAILED. Gateway still down. Manual intervention required."
        
        echo "{\"time\":\"$(date -u -Iseconds)\",\"type\":\"claude_repair\",\"result\":\"failed\",\"exit_code\":$exit_code}" >> "$REPAIR_LOG"
        return 1
    fi
}

# --- Main ---

# Health check
if check_health; then
    # Healthy: reset counter, exit silently
    if [ "$(get_fail_count)" != "0" ]; then
        set_fail_count 0
    fi
    exit 0
fi

# Unhealthy: increment counter
fail_count=$(get_fail_count)
fail_count=$((fail_count + 1))
set_fail_count "$fail_count"

log "UNHEALTHY: Consecutive failure #${fail_count}"

# Layer 1: Bash restart (attempts 1-2)
if [ "$fail_count" -le "$MAX_BASH_RETRIES" ]; then
    if bash_restart "$fail_count"; then
        exit 0
    fi
    exit 1
fi

# Layer 2: Claude Code repair (attempt 3+)
if [ "$fail_count" -eq $((MAX_BASH_RETRIES + 1)) ]; then
    notify_telegram "⚠️ <b>Watchdog:</b> Gateway down after ${MAX_BASH_RETRIES} restart attempts. Escalating to Claude Code repair."
    claude_repair
    exit $?
fi

# Already tried Claude, still failing
if [ "$fail_count" -gt $((MAX_BASH_RETRIES + 2)) ]; then
    # Only notify once every 10 failures to avoid spam
    if [ $((fail_count % 10)) -eq 0 ]; then
        notify_telegram "🔴 <b>Watchdog:</b> Gateway still down after ${fail_count} checks. All auto-repair failed. Manual fix needed."
    fi
fi

exit 1
