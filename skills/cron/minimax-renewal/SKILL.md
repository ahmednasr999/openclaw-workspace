---
name: minimax-renewal
description: "Remind Ahmed about MiniMax OAuth token renewal before expiry."
---

# MiniMax OAuth Renewal Reminder

## Steps

### Step 1: Check token status
```bash
# Check if MiniMax is configured and responding
grep -i "minimax" /root/.openclaw/openclaw.json 2>/dev/null | grep -v "^\s*//" | head -3
echo "---"
# Test a simple model call would work (don't actually call)
echo "MiniMax config present: $(grep -c 'minimax' /root/.openclaw/openclaw.json 2>/dev/null) references"
```

### Step 2: Deliver reminder
```
MiniMax OAuth token expires in ~30 days.
Action: Renew at MiniMax portal before expiry.
Current status: [configured/missing]
```

## Error Handling
- If config not found: Report that MiniMax is not configured

## Quality Gates
- Must verify config exists before reminding

## Output Rules
- No em dashes. Hyphens only.

### Step 3: Verify and Log
Log the reminder outcome to cron recovery log:
```bash
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) minimax-renewal: config_present=$(grep -c 'minimax' /root/.openclaw/openclaw.json 2>/dev/null) reminder_sent=yes" >> /root/.openclaw/workspace/memory/cron-recovery.log
```
If reminder delivery failed, retry once. If MiniMax config is missing, escalate immediately rather than sending a renewal reminder for a non-existent config.

## Manual Run
```bash
cd /root/.openclaw/workspace && openclaw cron run minimax-renewal
```

## Output Rules
- No em dashes - use hyphens only
- Keep reminder under 200 chars for Telegram delivery
- Include days-until-expiry if known, or "~30 days" if estimated
- State current config status: configured or missing
