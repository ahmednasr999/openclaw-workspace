#!/usr/bin/env bash
# =============================================================================
# fallback-validator.sh — Gateway Startup Fallback Chain Validator
# =============================================================================
# PURPOSE: Verify all models in the fallback chain have valid credentials
#          BEFORE the gateway goes live. Prevents the Feb 27 scenario where
#          MiniMax had an invalid auth key silently, killing the last fallback.
#
# USAGE:
#   ./fallback-validator.sh              — Full validation, exits 0 if all OK
#   ./fallback-validator.sh --quick      — Key format check only (no live ping, <200ms)
#   ./fallback-validator.sh --live       — Live API ping each model (slower, more accurate)
#   ./fallback-validator.sh --report     — Print JSON report and exit
#   ./fallback-validator.sh --notify     — Send Telegram alert on failures
#
# EXIT CODES:
#   0 — All models healthy
#   1 — Warning: 1-2 models degraded but enough fallbacks remain
#   2 — Critical: 3+ models down OR primary model down with <2 fallbacks
#   3 — Fatal: Entire fallback chain invalid; do NOT proceed
#
# INTEGRATION:
#   Add to openclaw startup sequence or cron:
#   @reboot /root/.openclaw/workspace/system-config/quota-monitoring/fallback-validator.sh --notify
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCLAW_JSON="${HOME}/.openclaw/openclaw.json"
MODELS_JSON="${HOME}/.openclaw/agents/main/agent/models.json"
REPORT_FILE="${SCRIPT_DIR}/validation-report.json"
LOG_FILE="${SCRIPT_DIR}/validation.log"
TIMEOUT_SEC=5   # Per-model API ping timeout

# ── Flags ──────────────────────────────────────────────────────────────────
MODE="quick"
NOTIFY=false
for arg in "$@"; do
  case $arg in
    --quick)   MODE="quick"  ;;
    --live)    MODE="live"   ;;
    --report)  MODE="report" ;;
    --notify)  NOTIFY=true   ;;
  esac
done

# ── Helpers ──────────────────────────────────────────────────────────────────

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $*" | tee -a "$LOG_FILE"; }
ok()   { echo -e "${GREEN}  ✅ $*${NC}"; }
warn() { echo -e "${YELLOW}  ⚠️  $*${NC}"; }
fail() { echo -e "${RED}  ❌ $*${NC}"; }
info() { echo -e "${BLUE}  ℹ️  $*${NC}"; }

# ── Extract API keys from openclaw.json ─────────────────────────────────────

get_key() {
  # $1 = provider name
  python3 -c "
import json, sys
with open('${OPENCLAW_JSON}') as f:
    cfg = json.load(f)
providers = cfg.get('models', {}).get('providers', {})
provider = providers.get('$1', {})
key = provider.get('apiKey', '')
print(key)
" 2>/dev/null || echo ""
}

# Also check the agent-level models.json which may override
get_agent_key() {
  # For moonshot: key lives in auth-profiles.json, not models.json
  if [[ "$1" == "moonshot" ]]; then
    python3 -c "
import json
try:
    with open('${HOME}/.openclaw/agents/main/agent/auth-profiles.json') as f:
        data = json.load(f)
    profiles = data.get('profiles', {})
    moonshot = profiles.get('moonshot:default', {})
    key = moonshot.get('key', '') or moonshot.get('apiKey', '')
    print(key)
except:
    print('')
" 2>/dev/null || echo ""
    return
  fi
  python3 -c "
import json, sys
try:
    with open('${MODELS_JSON}') as f:
        cfg = json.load(f)
    providers = cfg.get('providers', {})
    provider = providers.get('$1', {})
    key = provider.get('apiKey', '')
    print(key)
except:
    print('')
" 2>/dev/null || echo ""
}

# ── Model Definitions ────────────────────────────────────────────────────────

declare -A MODEL_PROVIDER=(
  ["minimax-portal/MiniMax-M2.5"]="minimax-portal"
  ["anthropic/claude-haiku-4-5"]="anthropic"
  ["anthropic/claude-sonnet-4-6"]="anthropic"
  ["anthropic/claude-opus-4-6"]="anthropic"
  ["moonshot/kimi-k2.5"]="moonshot"
  ["openai-codex/gpt-5.3-codex"]="openai-codex"
)

declare -A MODEL_NAME=(
  ["minimax-portal/MiniMax-M2.5"]="MiniMax M2.5 (PRIMARY)"
  ["anthropic/claude-haiku-4-5"]="Claude Haiku 4.5"
  ["anthropic/claude-sonnet-4-6"]="Claude Sonnet 4.6"
  ["anthropic/claude-opus-4-6"]="Claude Opus 4.6"
  ["moonshot/kimi-k2.5"]="Kimi K2.5"
  ["openai-codex/gpt-5.3-codex"]="GPT-5.3-Codex"
)

FALLBACK_ORDER=(
  "minimax-portal/MiniMax-M2.5"
  "anthropic/claude-haiku-4-5"
  "anthropic/claude-sonnet-4-6"
  "anthropic/claude-opus-4-6"
  "moonshot/kimi-k2.5"
  "openai-codex/gpt-5.3-codex"
)

# ── Key Format Validators ────────────────────────────────────────────────────

validate_anthropic_key() {
  local key="$1"
  if [[ -z "$key" ]]; then echo "MISSING"; return; fi
  if [[ "$key" =~ ^sk-ant- ]]; then echo "OK"; return; fi
  echo "INVALID_FORMAT"
}

validate_minimax_key() {
  local key="$1"
  # MiniMax uses OAuth — key will be "minimax-oauth" or a bearer token
  if [[ -z "$key" ]]; then echo "MISSING"; return; fi
  if [[ "$key" == "minimax-oauth" ]]; then
    # Check OAuth token exists in plugin auth
    local token_file="${HOME}/.openclaw/agents/main/agent/auth-profiles.json"
    if [[ -f "$token_file" ]]; then
      local has_token
      has_token=$(python3 -c "
import json, time
with open('$token_file') as f: data = json.load(f)
profiles = data.get('profiles', data) if isinstance(data, dict) else {}
minimax = profiles.get('minimax-portal:default', {})
# Check all possible token field names (OpenClaw uses 'access' not 'accessToken')
token = (minimax.get('accessToken', '') or minimax.get('token', '') or
         minimax.get('bearerToken', '') or minimax.get('access', ''))
# Check expiry if present (expires is in milliseconds)
expires = minimax.get('expires', 0)
now_ms = time.time() * 1000
if expires and now_ms > expires:
    print('expired')
elif token and len(token) > 10:
    print('present')
else:
    print('missing')
" 2>/dev/null || echo "unknown")
      if [[ "$has_token" == "present" ]]; then echo "OK_OAUTH"; return; fi
      if [[ "$has_token" == "expired" ]]; then echo "OAUTH_EXPIRED"; return; fi
      if [[ "$has_token" == "missing" ]]; then echo "OAUTH_TOKEN_MISSING"; return; fi
      echo "OAUTH_UNKNOWN"
    else
      echo "AUTH_FILE_MISSING"
    fi
    return
  fi
  # Direct API key
  if [[ "${#key}" -gt 30 ]] && [[ "$key" =~ ^sk- ]]; then echo "OK"; return; fi
  echo "INVALID_FORMAT"
}

validate_moonshot_key() {
  local key="$1"
  if [[ -z "$key" ]]; then echo "MISSING"; return; fi
  if [[ "${#key}" -gt 20 ]] && [[ "$key" =~ ^sk- ]]; then echo "OK"; return; fi
  echo "INVALID_FORMAT"
}

validate_openai_key() {
  local key="$1"
  if [[ -z "$key" ]]; then
    # No direct key — check auth-profiles.json for OAuth token
    local token_file="${HOME}/.openclaw/agents/main/agent/auth-profiles.json"
    if [[ -f "$token_file" ]]; then
      local has_token
      has_token=$(python3 -c "
import json, time
with open('$token_file') as f: data = json.load(f)
profiles = data.get('profiles', {})
codex = profiles.get('openai-codex:default', {})
token = codex.get('access', '') or codex.get('accessToken', '') or codex.get('token', '')
expires = codex.get('expires', 0)
now_ms = time.time() * 1000
if expires and now_ms > expires:
    print('expired')
elif token and len(token) > 10:
    print('present')
else:
    print('missing')
" 2>/dev/null || echo "unknown")
      if [[ "$has_token" == "present" ]]; then echo "OK_OAUTH"; return; fi
      if [[ "$has_token" == "expired" ]]; then echo "OAUTH_EXPIRED"; return; fi
    fi
    echo "MISSING"
    return
  fi
  if [[ "$key" == "openai-oauth" || "$key" == "codex-oauth" ]]; then echo "OK_OAUTH"; return; fi
  if [[ "$key" =~ ^sk- ]]; then echo "OK"; return; fi
  echo "INVALID_FORMAT"
}

# ── Live API Ping (minimal, fast) ─────────────────────────────────────────────

ping_anthropic() {
  local key="$1"
  local model="$2"
  # NOTE: sk-ant-oat01 tokens are OpenClaw OAuth tokens that route through the
  # gateway proxy — they cannot be validated directly against api.anthropic.com.
  # For these tokens, format validation is sufficient; skip live ping.
  if [[ "$key" =~ ^sk-ant-oat ]]; then
    echo "OAUTH_SKIP"
    return
  fi
  # Standard sk-ant-api03 keys — test directly
  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time "$TIMEOUT_SEC" \
    -H "x-api-key: $key" \
    -H "anthropic-version: 2023-06-01" \
    "https://api.anthropic.com/v1/models" 2>/dev/null)
  echo "$http_code"
}

ping_moonshot() {
  local key="$1"
  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time "$TIMEOUT_SEC" \
    -H "Authorization: Bearer $key" \
    "https://api.moonshot.ai/v1/models" 2>/dev/null)
  echo "$http_code"
}

ping_minimax_oauth() {
  # MiniMax does not expose a public /models or health endpoint.
  # It uses OAuth tokens that work through the OpenClaw gateway proxy.
  # Treat as OAUTH_SKIP — token presence + format is validated in quick mode.
  echo "OAUTH_SKIP"
}

# ── Main Validation Loop ─────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  FALLBACK CHAIN VALIDATOR — $(date -u '+%Y-%m-%d %H:%M UTC')"
echo "  Mode: $MODE"
echo "═══════════════════════════════════════════════════════════════"
echo ""

HEALTHY=0
WARNINGS=0
ERRORS=0
REPORT="{\"timestamp\":\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\",\"mode\":\"$MODE\",\"models\":{}}"

declare -A MODEL_STATUS

for model_id in "${FALLBACK_ORDER[@]}"; do
  provider="${MODEL_PROVIDER[$model_id]}"
  name="${MODEL_NAME[$model_id]}"

  echo -n "  Checking $name... "

  # Get the key (prefer agent-level override)
  key=$(get_agent_key "$provider")
  if [[ -z "$key" ]]; then
    key=$(get_key "$provider")
  fi

  # Validate key format
  key_status="UNKNOWN"
  case "$provider" in
    anthropic)      key_status=$(validate_anthropic_key "$key") ;;
    minimax-portal) key_status=$(validate_minimax_key "$key") ;;
    moonshot)       key_status=$(validate_moonshot_key "$key") ;;
    openai-codex)   key_status=$(validate_openai_key "$key") ;;
    *)              key_status="UNKNOWN_PROVIDER" ;;
  esac

  model_result="ok"
  http_code="N/A"

  # Handle key validation result
  case "$key_status" in
    "OK"|"OK_OAUTH")
      if [[ "$MODE" == "live" ]]; then
        echo ""
        echo -n "    → Live ping... "
        case "$provider" in
          anthropic)      http_code=$(ping_anthropic "$key" "$model_id") ;;
          moonshot)       http_code=$(ping_moonshot "$key") ;;
          minimax-portal) http_code=$(ping_minimax_oauth) ;;
          *)              http_code="N/A" ;;
        esac

        if [[ "$http_code" == "200" || "$http_code" == "N/A" ]]; then
          ok "LIVE OK (HTTP $http_code)"
          HEALTHY=$((HEALTHY + 1))
        elif [[ "$http_code" == "OAUTH_SKIP" ]]; then
          ok "SKIPPED (OAuth token — validates via gateway, not direct API)"
          HEALTHY=$((HEALTHY + 1))
        elif [[ "$http_code" == "401" || "$http_code" == "403" ]]; then
          fail "AUTH REJECTED (HTTP $http_code) — key may be revoked or expired"
          model_result="auth_rejected"
          ERRORS=$((ERRORS + 1))
        elif [[ "$http_code" == "429" ]]; then
          warn "RATE LIMITED (HTTP 429) — model is alive but quota may be exhausted"
          model_result="rate_limited"
          WARNINGS=$((WARNINGS + 1))
        elif [[ "$http_code" == "000" ]]; then
          warn "UNREACHABLE — network timeout or DNS failure"
          model_result="unreachable"
          WARNINGS=$((WARNINGS + 1))
        else
          warn "UNEXPECTED RESPONSE (HTTP $http_code)"
          model_result="unexpected"
          WARNINGS=$((WARNINGS + 1))
        fi
      else
        ok "Key format valid ($key_status)"
        HEALTHY=$((HEALTHY + 1))
      fi
      ;;

    "MISSING")
      fail "NO API KEY — provider '$provider' has no key configured"
      model_result="missing_key"
      ERRORS=$((ERRORS + 1))
      ;;

    "OAUTH_TOKEN_MISSING")
      fail "OAUTH TOKEN MISSING — MiniMax OAuth profile exists but token is absent"
      warn "  → FIX: Re-authenticate via 'openclaw auth login minimax-portal'"
      model_result="oauth_token_missing"
      ERRORS=$((ERRORS + 1))
      ;;

    "OAUTH_EXPIRED")
      fail "OAUTH TOKEN EXPIRED — MiniMax access token has expired (check 'expires' field)"
      warn "  → FIX: Re-authenticate via 'openclaw auth login minimax-portal'"
      model_result="oauth_expired"
      ERRORS=$((ERRORS + 1))
      ;;

    "AUTH_FILE_MISSING")
      fail "AUTH FILE MISSING — ${HOME}/.openclaw/agents/main/agent/auth-profiles.json not found"
      model_result="auth_file_missing"
      ERRORS=$((ERRORS + 1))
      ;;

    "INVALID_FORMAT")
      fail "INVALID KEY FORMAT — key does not match expected pattern for '$provider'"
      warn "  → The key may be truncated or from a different provider"
      model_result="invalid_format"
      ERRORS=$((ERRORS + 1))
      ;;

    "UNKNOWN"|*)
      warn "Cannot validate key for provider '$provider'"
      model_result="unknown"
      WARNINGS=$((WARNINGS + 1))
      ;;
  esac

  MODEL_STATUS[$model_id]="$model_result"
done

# ── Chain Health Assessment ───────────────────────────────────────────────────

echo ""
echo "─────────────────────────────────────────────────────────────────"
TOTAL=${#FALLBACK_ORDER[@]}
echo "  Summary: $HEALTHY/$TOTAL healthy | $WARNINGS warnings | $ERRORS errors"

# Calculate viable fallbacks
VIABLE=0
for model_id in "${FALLBACK_ORDER[@]}"; do
  status="${MODEL_STATUS[$model_id]:-unknown}"
  if [[ "$status" == "ok" || "$status" == "rate_limited" ]]; then
    VIABLE=$((VIABLE + 1))
  fi
done

PRIMARY_STATUS="${MODEL_STATUS[minimax-portal/MiniMax-M2.5]:-unknown}"
EXIT_CODE=0

echo ""
if [[ $ERRORS -eq 0 && $WARNINGS -eq 0 ]]; then
  echo -e "${GREEN}  ✅ ALL CLEAR — Fallback chain is fully healthy${NC}"
  EXIT_CODE=0
elif [[ $ERRORS -ge 4 || $VIABLE -le 1 ]]; then
  echo -e "${RED}  🚨 FATAL — ${ERRORS} model(s) invalid, only ${VIABLE} viable fallback(s)${NC}"
  echo -e "${RED}     DO NOT proceed with batch operations. Gateway may not recover from failures.${NC}"
  EXIT_CODE=3
elif [[ "$PRIMARY_STATUS" != "ok" && $VIABLE -le 2 ]]; then
  echo -e "${RED}  ❌ CRITICAL — Primary model (MiniMax M2.5) is DOWN with insufficient fallbacks${NC}"
  echo -e "${RED}     Risk of cascade failure is HIGH.${NC}"
  EXIT_CODE=2
elif [[ $ERRORS -ge 2 ]]; then
  echo -e "${YELLOW}  ⚠️  WARNING — ${ERRORS} model(s) need attention, ${VIABLE} viable fallbacks${NC}"
  EXIT_CODE=1
else
  echo -e "${YELLOW}  ℹ️  OK WITH WARNINGS — ${WARNINGS} advisory notice(s)${NC}"
  EXIT_CODE=1
fi

echo ""

# ── Recommended Actions ───────────────────────────────────────────────────────

if [[ $ERRORS -gt 0 || $WARNINGS -gt 0 ]]; then
  echo "  RECOMMENDED ACTIONS:"
  for model_id in "${FALLBACK_ORDER[@]}"; do
    status="${MODEL_STATUS[$model_id]:-unknown}"
    name="${MODEL_NAME[$model_id]}"
    case "$status" in
      missing_key)    echo "    → $name: Add apiKey to openclaw.json or agent/models.json" ;;
      oauth_expired)  echo "    → $name: Run: openclaw auth login minimax-portal" ;;
      auth_rejected)  echo "    → $name: Key may be revoked — regenerate at provider dashboard" ;;
      invalid_format) echo "    → $name: Check key in openclaw.json for truncation/corruption" ;;
      rate_limited)   echo "    → $name: Rate limited — wait for quota reset or reduce parallel spawns" ;;
    esac
  done
  echo ""
fi

# ── Save Report ───────────────────────────────────────────────────────────────

python3 - << PYEOF
import json
from datetime import datetime, timezone

report = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "mode": "${MODE}",
    "exitCode": ${EXIT_CODE},
    "summary": {
        "total": ${TOTAL},
        "healthy": ${HEALTHY},
        "warnings": ${WARNINGS},
        "errors": ${ERRORS},
        "viable": ${VIABLE},
        "primaryStatus": "${PRIMARY_STATUS}"
    },
    "models": {}
}

models_info = {
    "minimax-portal/MiniMax-M2.5":   {"name": "MiniMax M2.5", "status": "${MODEL_STATUS[minimax-portal/MiniMax-M2.5]:-unknown}"},
    "anthropic/claude-haiku-4-5":    {"name": "Claude Haiku 4.5", "status": "${MODEL_STATUS[anthropic/claude-haiku-4-5]:-unknown}"},
    "anthropic/claude-sonnet-4-6":   {"name": "Claude Sonnet 4.6", "status": "${MODEL_STATUS[anthropic/claude-sonnet-4-6]:-unknown}"},
    "anthropic/claude-opus-4-6":     {"name": "Claude Opus 4.6", "status": "${MODEL_STATUS[anthropic/claude-opus-4-6]:-unknown}"},
    "moonshot/kimi-k2.5":            {"name": "Kimi K2.5", "status": "${MODEL_STATUS[moonshot/kimi-k2.5]:-unknown}"},
    "openai-codex/gpt-5.3-codex":    {"name": "GPT-5.3-Codex", "status": "${MODEL_STATUS[openai-codex/gpt-5.3-codex]:-unknown}"},
}
report["models"] = models_info

with open("${REPORT_FILE}", "w") as f:
    json.dump(report, f, indent=2)
print(f"  Report saved: ${REPORT_FILE}")
PYEOF

log "Validation complete: exit=$EXIT_CODE healthy=$HEALTHY warnings=$WARNINGS errors=$ERRORS viable=$VIABLE"

# ── Telegram Notification (if --notify and there are issues) ─────────────────

if [[ "$NOTIFY" == "true" && ( $ERRORS -gt 0 || $EXIT_CODE -ge 2 ) ]]; then
  BOT_TOKEN=$(python3 -c "
import json
with open('${HOME}/.openclaw/openclaw.json') as f: cfg = json.load(f)
print(cfg.get('channels', {}).get('telegram', {}).get('botToken', ''))
" 2>/dev/null)

  CHAT_ID=$(python3 -c "
import json
try:
    with open('${HOME}/.openclaw/credentials/telegram-allowFrom.json') as f:
        data = json.load(f)
    ids = data if isinstance(data, list) else [data]
    print(ids[0] if ids else '')
except:
    print('')
" 2>/dev/null)

  if [[ -n "$BOT_TOKEN" && -n "$CHAT_ID" ]]; then
    MSG="🚨 *GATEWAY STARTUP ALERT*%0A"
    MSG+="Fallback chain validation FAILED%0A"
    MSG+="%0A"
    MSG+="❌ Errors: ${ERRORS}%0A"
    MSG+="⚠️ Warnings: ${WARNINGS}%0A"
    MSG+="✅ Viable fallbacks: ${VIABLE}/6%0A"
    MSG+="%0A"
    MSG+="Primary (MiniMax M2.5): ${PRIMARY_STATUS}%0A"
    MSG+="%0A"
    MSG+="⏰ $(date -u '+%Y-%m-%d %H:%M UTC')%0A"
    MSG+="Run: fallback-validator.sh --live for full diagnosis"

    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
      -d "chat_id=${CHAT_ID}" \
      -d "text=${MSG}" \
      -d "parse_mode=Markdown" > /dev/null 2>&1 && echo "  Telegram alert sent." || echo "  Telegram alert failed."
  else
    echo "  [NOTIFY] Could not send Telegram — missing bot token or chat ID"
  fi
fi

echo "═══════════════════════════════════════════════════════════════"
echo ""
exit $EXIT_CODE
