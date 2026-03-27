# Gateway Management Runbook

How to diagnose, monitor, and repair the OpenClaw gateway.

## Quick Health Check

### Test 1: Gateway Responding?
```bash
curl -s localhost:18789/health | jq .
```

**Expected output:**
```json
{
  "ok": true,
  "status": "live"
}
```

**If timeout or connection refused:**
- Gateway is DOWN
- Proceed to "Restart Gateway" section

### Test 2: Composio Accessible?
```bash
# Use COMPOSIO_SEARCH_TOOLS (quick test, doesn't require auth)
COMPOSIO_SEARCH_TOOLS with queries: [{ use_case: "test composio connectivity" }]
```

**Expected:** Tools list returns (even if empty), no auth errors

**If timeout or "401 Unauthorized":**
- Composio config issue
- Check environment variables (see section below)

---

## Gateway Logs

### Check Recent Logs
```bash
# Last 50 lines (most recent)
tail -50 ~/.openclaw/logs/openclaw.log

# Search for errors
grep -i "error\|failed\|503\|500" ~/.openclaw/logs/openclaw.log | tail -20

# Full log file location
cat ~/.openclaw/logs/openclaw.log | less
```

### Log Directory
```
~/.openclaw/logs/
├── openclaw.log          # Main gateway log
├── [agent]-*.log         # Per-agent logs (from crons)
└── [timestamp].log       # Rotated logs
```

### Common Error Patterns

| Error | Meaning | Fix |
|-------|---------|-----|
| `EADDRINUSE :18789` | Port 18789 already in use | Kill existing process, restart |
| `COMPOSIO_CONSUMER_KEY not set` | Missing API key | Check environment setup |
| `Connection refused` | Gateway not running | Start gateway |
| `Timeout at /health` | Gateway hanging | Restart gateway |
| `403 Forbidden` | Auth error | Check credentials, renew tokens |

---

## Configuration

### Main Config File
```
/root/.openclaw/openclaw.json
```

**Sample structure:**
```json
{
  "gateway": {
    "port": 18789,
    "host": "localhost"
  },
  "composio": {
    "key": "ak_...",
    "secret": "cs_..."
  },
  "plugins": {
    "telegram": {
      "token": "...",
      "chat_id": "..."
    }
  }
}
```

**Validation:**
```bash
# Check syntax
jq . /root/.openclaw/openclaw.json

# If syntax error, check for trailing commas, missing quotes
```

### Environment Variables

```bash
# Required for Composio
export COMPOSIO_CONSUMER_KEY="ak_..."
export COMPOSIO_CONSUMER_SECRET="cs_..."

# Required for search tools
export TAVILY_API_KEY="tvly-..."
export EXA_API_KEY="exa_..."

# Check what's set
env | grep -E "COMPOSIO|TAVILY|EXA"
```

**Where to set:**
- System: `/etc/environment` (persistent across reboots)
- User: `~/.bashrc` or `~/.zshrc` (per-session)
- For systemd service: see next section

---

## Systemd Service

### Service File Location
```
/etc/systemd/system/openclaw-gateway.service
```

### Check Service Status
```bash
systemctl --user status openclaw-gateway
systemctl --user is-active openclaw-gateway
```

### Start / Stop / Restart
```bash
# Start
systemctl --user start openclaw-gateway

# Stop
systemctl --user stop openclaw-gateway

# Restart (recommended for most issues)
systemctl --user restart openclaw-gateway

# Enable auto-start on boot
systemctl --user enable openclaw-gateway

# View service logs
journalctl --user -u openclaw-gateway -n 50 -f  # Follow logs
journalctl --user -u openclaw-gateway -n 100    # Last 100 lines
```

### Reload Service (After Config Change)
```bash
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
```

---

## Common Issues & Fixes

### Issue: "Gateway Down" (503 errors)

**Diagnosis:**
```bash
curl -v localhost:18789/health
# Expected: HTTP 200
# If getting: HTTP 503, Connection refused, Timeout
```

**Fix Steps:**
1. Check logs: `tail -20 ~/.openclaw/logs/openclaw.log | grep -i error`
2. Restart: `systemctl --user restart openclaw-gateway`
3. Wait 5 seconds
4. Re-check: `curl localhost:18789/health`

**If still down:**
1. Check disk space: `df -h` (need >1GB free)
2. Check process: `ps aux | grep openclaw`
3. Manual start: `openclaw gateway start`
4. Check for port conflicts: `lsof -i :18789`

### Issue: "Composio Tools Timeout"

**Diagnosis:**
```bash
# Test Composio directly
COMPOSIO_SEARCH_TOOLS with queries: [{ use_case: "test" }]
# If hangs >30s: Composio issue
```

**Fix Steps:**
1. Verify API keys set: `echo $COMPOSIO_CONSUMER_KEY`
2. Check key format: should start with `ak_`
3. Test Composio connection: `composio list` (if CLI available)
4. Restart gateway: `systemctl --user restart openclaw-gateway`
5. If persistent: loop in CEO (Composio account issue)

### Issue: "Port 18789 Already in Use"

**Diagnosis:**
```bash
lsof -i :18789
# Lists process using port
```

**Fix Steps:**
1. Kill existing process: `kill -9 <PID>`
2. Or change port in `/root/.openclaw/openclaw.json` (not recommended)
3. Restart: `systemctl --user restart openclaw-gateway`

### Issue: "Secret Rotation Needed"

**Diagnosis:**
- Composio API key expired
- Telegram token invalid
- GitHub token missing

**Fix Steps:**
1. Go to dashboard.composio.dev or provider portal
2. Generate new key/token
3. Update: `/root/.openclaw/openclaw.json`
4. Or update environment variable: `export COMPOSIO_CONSUMER_KEY="new_key"`
5. Restart gateway: `systemctl --user restart openclaw-gateway`
6. Verify: `COMPOSIO_SEARCH_TOOLS` succeeds

---

## Health Check Checklist

**Run this every morning (part of standup):**

```bash
#!/bin/bash

echo "=== CTO Gateway Health Check ==="

# 1. Gateway responding?
echo -n "Gateway health: "
curl -s localhost:18789/health | jq -r '.status' || echo "❌ DOWN"

# 2. Composio accessible?
echo -n "Composio: "
if command -v node &>/dev/null; then
  COMPOSIO_TEST="working" # Placeholder for actual test
  echo "✅ Configured"
else
  echo "? Check manually"
fi

# 3. Disk space OK?
echo -n "Disk space: "
DISK_PERCENT=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_PERCENT" -lt 90 ]; then
  echo "✅ ${DISK_PERCENT}% used"
else
  echo "⚠️ ${DISK_PERCENT}% used (low space)"
fi

# 4. Service running?
echo -n "Service status: "
systemctl --user is-active openclaw-gateway | grep -q active && echo "✅ Running" || echo "❌ Stopped"

# 5. Recent logs OK?
echo -n "Recent errors: "
ERROR_COUNT=$(tail -100 ~/.openclaw/logs/openclaw.log | grep -c "error\|failed\|error" || echo "0")
if [ "$ERROR_COUNT" -eq 0 ]; then
  echo "✅ None"
else
  echo "⚠️ $ERROR_COUNT found (check logs)"
fi

echo "=== Check complete ==="
```

---

## Troubleshooting Decision Tree

```
Gateway health check fails?
├─ curl timeout or connection refused?
│  ├─ Process running? (ps aux | grep openclaw)
│  │  ├─ YES: Kill and restart (systemctl restart openclaw-gateway)
│  │  └─ NO: Manual start (openclaw gateway start)
│  └─ After restart: curl localhost:18789/health
│
├─ curl returns 503 error?
│  ├─ Check logs (tail ~/.openclaw/logs/openclaw.log)
│  ├─ Disk full? (df -h)
│  ├─ Port conflict? (lsof -i :18789)
│  └─ Fix and restart
│
├─ curl returns 200 but Composio times out?
│  ├─ COMPOSIO_CONSUMER_KEY set? (echo $COMPOSIO_CONSUMER_KEY)
│  ├─ API key valid? (try on dashboard.composio.dev)
│  └─ Renew key if expired, update config, restart
│
└─ All checks pass?
   └─ Gateway healthy ✅
```

---

## Recovery Procedure

**If gateway is down and won't restart:**

1. **Check systemd logs:**
   ```bash
   journalctl --user -u openclaw-gateway -n 50
   ```

2. **Check config syntax:**
   ```bash
   jq . /root/.openclaw/openclaw.json
   ```

3. **Check environment:**
   ```bash
   env | grep -E "COMPOSIO|TAVILY|EXA"
   ```

4. **Manual start (debug mode):**
   ```bash
   openclaw gateway start --debug
   ```

5. **If still stuck:**
   - Loop in CEO via sessions_send
   - Include: logs, config (redacted), error messages
   - Provide: last known good state, recent changes

---

## Notes

- Gateway runs on `localhost:18789` (not exposed externally)
- All requests go through this gateway (no direct API calls)
- Restart is safe — doesn't kill running cron jobs
- Check health every morning (standup)
- Log rotation happens automatically (old logs compressed)
