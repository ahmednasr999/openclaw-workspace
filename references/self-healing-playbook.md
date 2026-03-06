# Self-Healing Playbook

Reference file for the self-healing agent. Maps known failure patterns to automated fixes.

## Diagnosis Rules

### 1. Delivery Failures
**Pattern:** error contains "Message failed" or "delivery" or "channel"
**Diagnosis:** Delivery target unreachable (Slack channel, Telegram chat)
**Fix:**
- Check if job is targeting Slack → try re-delivering to Telegram instead
- Run: `openclaw channels status --probe` to verify channel health
- If channel is down, log warning and skip delivery (bestEffort should handle this)
- If persistent (3+ consecutive), escalate to Ahmed

### 2. File Edit/Write Failures
**Pattern:** error contains "Edit" or "Write" or "file" or "permission"
**Diagnosis:** File path issue, permissions, or disk space
**Fix:**
- Check disk space: `df -h /root/.openclaw/workspace/`
- If disk > 90% full, run cleanup: `find /tmp -type f -mtime +7 -delete`
- If file path in error, verify file exists
- Re-run the job: `openclaw cron run <jobId>`

### 3. Script/Playwright Timeout
**Pattern:** error contains "timeout" or "timed out" or "SIGTERM"
**Diagnosis:** Script took too long (common with Playwright/LinkedIn scraping)
**Fix:**
- Check if it's a Playwright job (linkedin-job-scout, linkedin-jd-fetcher)
- If Playwright: check if chromium process is zombie: `pgrep -a chromium | wc -l`
- Kill zombies if > 5: `pkill -f chromium`
- Re-run the job with note about timeout

### 4. Model/Auth Failures
**Pattern:** error contains "401" or "403" or "auth" or "token" or "rate limit" or "quota"
**Diagnosis:** Model credentials expired or rate limited
**Fix:**
- If rate limit: do NOT retry immediately, wait for next scheduled run
- If auth/token error on MiniMax: check OAuth status, alert Ahmed to re-auth
- If auth error on Anthropic: check API key validity
- Run: `openclaw doctor` for credential health check
- ESCALATE to Ahmed: auth fixes require human action

### 5. Gateway/System Failures
**Pattern:** error contains "gateway" or "ECONNREFUSED" or "spawn" or "memory"
**Diagnosis:** Gateway instability or resource exhaustion
**Fix:**
- Check gateway status: `systemctl status openclaw-gateway`
- Check memory: `free -m` (alert if available < 500MB)
- Check load: `uptime` (alert if load > 4.0)
- If gateway not running: `systemctl restart openclaw-gateway`
- If memory < 500MB: kill zombie processes, clear /tmp

### 6. Empty/No Output
**Pattern:** summary is empty, or "HEARTBEAT_OK" when it shouldn't be
**Diagnosis:** Job ran but produced wrong output (model confusion, wrong prompt)
**Fix:**
- Check if job has explicit model set (not falling back to default)
- Verify job message/prompt hasn't been corrupted
- Re-run once to see if it's intermittent
- If repeated, flag for prompt review

## Escalation Rules

| Risk Level | Action | Examples |
|-----------|--------|---------|
| LOW | Fix silently, log to healer history | File path fix, timeout retry, zombie cleanup |
| MEDIUM | Fix and notify Ahmed | Gateway restart, disk cleanup, delivery channel switch |
| HIGH | Do NOT fix, alert Ahmed immediately | Auth/credential issues, persistent failures (3+), data loss risk |

## Re-run Safety Rules

- Never re-run a job more than ONCE per healing cycle
- Never re-run jobs that touch external systems (email send, LinkedIn post, job application)
- Only re-run: scouts, briefings, monitors, indexers, system checks
- Safe to re-run job IDs: any job with sessionTarget=isolated

## Jobs That Should NEVER Be Auto-Fixed
- LinkedIn Daily Post (risk of double-posting)
- Email sends (risk of duplicate emails)
- Any job that applies to external platforms

## Proactive Health Checks (run every cycle even if no errors)

### Memory Check
```bash
AVAIL=$(free -m | awk '/Mem:/ {print $7}')
if [ "$AVAIL" -lt 500 ]; then
  echo "WARNING: Available memory ${AVAIL}MB (< 500MB threshold)"
fi
```

### Disk Check
```bash
USAGE=$(df /root/.openclaw/workspace/ | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$USAGE" -gt 85 ]; then
  echo "WARNING: Disk usage ${USAGE}% (> 85% threshold)"
fi
```

### Gateway Process Check
```bash
GATEWAY_MEM=$(ps -o rss= -p $(pgrep -f openclaw-gateway) 2>/dev/null | awk '{sum+=$1} END {print sum/1024}')
if [ $(echo "$GATEWAY_MEM > 1500" | bc 2>/dev/null) -eq 1 ]; then
  echo "WARNING: Gateway memory ${GATEWAY_MEM}MB (> 1.5GB threshold, restart recommended)"
fi
```

### Zombie Process Check
```bash
ZOMBIES=$(ps aux | awk '$8 ~ /Z/ {count++} END {print count+0}')
CHROMIUM=$(pgrep -c chromium 2>/dev/null || echo 0)
if [ "$ZOMBIES" -gt 3 ] || [ "$CHROMIUM" -gt 10 ]; then
  echo "WARNING: $ZOMBIES zombie processes, $CHROMIUM chromium instances"
fi
```

## Healing History Log
Location: /root/.openclaw/workspace/logs/healer-history.jsonl
Each fix attempt should append a line:
{"ts": "<ISO8601>", "jobId": "<id>", "error": "<summary>", "action": "<what was done>", "result": "fixed|escalated|failed"}
