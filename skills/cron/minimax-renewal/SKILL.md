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
