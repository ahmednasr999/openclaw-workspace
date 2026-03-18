---
name: monthly-maintenance
description: "Monthly system maintenance: log rotation, dependency updates, config audit, performance review."
---

# Monthly System Maintenance Report

First-of-month comprehensive system audit. Run every command. Report actual output.

## Steps

### Step 1: Log rotation
```bash
echo "=== LOG CLEANUP ==="
# Find old log files
find /tmp -name "*.log" -mtime +30 -exec ls -lh {} \; 2>/dev/null | head -10
find /root/.openclaw -name "*.log" -mtime +30 -exec ls -lh {} \; 2>/dev/null | head -10

# Count and size
OLD_LOGS=$(find /tmp /root/.openclaw -name "*.log" -mtime +30 2>/dev/null | wc -l)
echo "Old logs (>30d): $OLD_LOGS"

# Clean if any
if [ "$OLD_LOGS" -gt 0 ]; then
    find /tmp -name "*.log" -mtime +30 -delete 2>/dev/null
    echo "Cleaned old /tmp logs"
fi
```

### Step 2: Dependency check
```bash
echo "=== DEPENDENCIES ==="
echo "Node.js: $(node --version)"
echo "Python: $(python3 --version)"
echo "OpenClaw: $(openclaw --version 2>&1 | head -1 | grep -v '^\[plugins\]')"
echo "npm outdated (global):" && npm list -g --depth=0 2>/dev/null | head -10

# Check himalaya
echo "Himalaya: $(himalaya --version 2>/dev/null || echo 'not installed')"
```

### Step 3: Config audit
```bash
echo "=== CONFIG AUDIT ==="
# OpenClaw config size
echo "openclaw.json: $(wc -c < /root/.openclaw/openclaw.json) bytes"

# Count crons
echo "Crons: $(openclaw cron list 2>&1 | grep -v '^\[plugins\]' | tail -n +2 | wc -l)"

# API key validity - check files exist, NEVER print keys
echo "Notion token: $(python3 -c 'import json; d=json.load(open("/root/.openclaw/workspace/config/notion.json")); print("present" if d.get("token") else "MISSING")' 2>/dev/null)"
echo "Gmail auth: $(grep -q 'auth.type = \"password\"' ~/.config/himalaya/config.toml 2>/dev/null && echo 'configured' || echo 'MISSING')"
echo "LinkedIn cookies: $([ -f ~/.openclaw/cookies/linkedin.txt ] && echo "$(wc -l < ~/.openclaw/cookies/linkedin.txt) lines" || echo 'MISSING')"
```

### Step 4: Performance review
```bash
echo "=== PERFORMANCE ==="
# Uptime
echo "System uptime: $(uptime -p)"

# Disk trend
echo "Disk usage: $(df -h / | tail -1 | awk '{print $5}')"
echo "Workspace size: $(du -sh /root/.openclaw/workspace 2>/dev/null | cut -f1)"
echo "Sessions size: $(du -sh /root/.openclaw/agents/main/sessions 2>/dev/null | cut -f1)"
echo "LCM DB size: $(ls -lh /root/.openclaw/lcm.db 2>/dev/null | awk '{print $5}')"

# Memory
echo "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2 " used"}')"
```

### Step 5: Disk cleanup
```bash
echo "=== CLEANUP ==="
# npm cache
NPM_CACHE=$(du -sh ~/.npm 2>/dev/null | cut -f1)
echo "npm cache: $NPM_CACHE"

# pip cache
PIP_CACHE=$(du -sh ~/.cache/pip 2>/dev/null | cut -f1)
echo "pip cache: $PIP_CACHE"

# Temp files
TEMP=$(du -sh /tmp 2>/dev/null | cut -f1)
echo "/tmp usage: $TEMP"

# Old session backups
OLD_SESSIONS=$(find /root/.openclaw/agents/main/sessions -name "*.reset.*" 2>/dev/null | wc -l)
echo "Old session backups: $OLD_SESSIONS"
if [ "$OLD_SESSIONS" -gt 0 ]; then
    find /root/.openclaw/agents/main/sessions -name "*.reset.*" -delete 2>/dev/null
    echo "Cleaned $OLD_SESSIONS old session backups"
fi
```

### Step 6: Report
Compile all findings. Include specific numbers, not estimates.

## Error Handling
- If any command fails: Report the error, continue with remaining checks
- If cleanup fails: Report which step failed, don't retry destructive ops

## Quality Gates
- All dependency versions reported
- All API keys/tokens verified (existence, not values)
- Disk usage under 80%
- Session bloat under 50MB
- Zero old session backups after cleanup

## Output Rules
- No em dashes. Hyphens only.
- NEVER print passwords, tokens, or API keys
- Every number from actual command output
