---
name: gateway-health
description: "Weekly gateway health restart to prevent reliability decay. Check plugins, connections, and service status."
---

# Weekly Gateway Health Restart

Preventive maintenance restart of OpenClaw gateway.

## Steps

### Step 1: Pre-restart health check
```bash
openclaw gateway status
```
Note current uptime, any errors in logs.

### Step 2: Restart gateway
```bash
openclaw gateway restart
```

### Step 3: Post-restart verification
- Verify gateway is running
- Check all plugins loaded (LCM, Composio, Camofox)
- Verify Telegram bot responsive
- Check cron scheduler active

### Step 4: Report
"🔄 Gateway restarted. Uptime was [X]. All [Y] plugins loaded. Status: healthy"

## Error Handling
- If restart fails: Check systemd logs, report error, attempt manual restart
- If plugins fail to load: Report which plugin failed, check config

## Output Rules
- No em dashes. Hyphens only.
- Include plugin count and names in report
