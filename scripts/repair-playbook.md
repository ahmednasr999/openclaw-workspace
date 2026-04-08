# OpenClaw Gateway Repair Playbook
# Used by self-healing agent to diagnose and fix gateway failures

## Error Pattern → Fix Mapping

### 1. Channel Token Failures
**Pattern:** `account_inactive`, `invalid_auth`, `token_revoked`, `not_authed`
**Cause:** A channel (Slack/Telegram) token expired or was revoked
**Fix:**
```bash
# Identify which channel from the error context
# Disable the broken channel:
python3 -c "
import json
with open('/root/.openclaw/openclaw.json') as f:
    data = json.load(f)
data['channels']['slack']['enabled'] = False  # or whichever channel
with open('/root/.openclaw/openclaw.json', 'w') as f:
    json.dump(data, f, indent=2)
"
```
**Risk:** LOW (disabling a channel is safe, gateway will run without it)

### 2. Unknown Model
**Pattern:** `Unknown model:`, `FailoverError: Unknown model`
**Cause:** A model override references a model not available in the runtime
**Fix:**
```bash
# Replace the unknown model with MiniMax M2.5 (always available)
python3 -c "
import json
with open('/root/.openclaw/openclaw.json') as f:
    data = json.load(f)
mbc = data.get('channels', {}).get('modelByChannel', {}).get('slack', {})
for k, v in mbc.items():
    if 'gpt-5.4' in v:  # or whatever model is failing
        mbc[k] = 'minimax-portal/MiniMax-M2.5'
with open('/root/.openclaw/openclaw.json', 'w') as f:
    json.dump(data, f, indent=2)
"
```
**Risk:** LOW (fallback to working model)

### 3. Port Already in Use
**Pattern:** `EADDRINUSE`, `address already in use`
**Cause:** Previous gateway process didn't exit cleanly
**Fix:**
```bash
pkill -9 -f "openclaw.*gateway"
sleep 2
# Then restart
```
**Risk:** LOW

### 4. Disk Space
**Pattern:** `ENOSPC`, `No space left on device`
**Cause:** Disk full
**Fix:**
```bash
# Clean old logs
find /tmp/openclaw -name "*.log" -mtime +7 -delete
# Clean old session files
find /root/.openclaw/agents/main/sessions -name "*.jsonl" -mtime +30 -delete
```
**Risk:** MEDIUM (deleting old data)

### 5. Memory / OOM
**Pattern:** `JavaScript heap out of memory`, `ENOMEM`
**Cause:** Node.js ran out of memory
**Fix:**
```bash
# Kill and restart with more memory
export NODE_OPTIONS="--max-old-space-size=2048"
```
**Risk:** LOW

### 6. Unhandled Promise Rejection
**Pattern:** `UnhandledPromiseRejectionWarning`, `unhandledRejection`
**Cause:** Usually a downstream API error not caught properly
**Fix:** Check which API call failed (usually visible in the stack trace), then apply the relevant fix above.
**Risk:** Depends on root cause

### 7. SSL / Certificate Errors
**Pattern:** `UNABLE_TO_VERIFY_LEAF_SIGNATURE`, `certificate has expired`
**Cause:** SSL cert issue on Tailscale or external API
**Fix:** Usually resolves on its own. Restart gateway.
**Risk:** LOW

## Safety Rules
- NEVER delete openclaw.json
- NEVER change Telegram bot token
- NEVER disable Telegram channel (it's the escalation path)
- Always restart gateway after any config change
- If unsure about the fix: DO NOT apply it. Report to Ahmed instead.
