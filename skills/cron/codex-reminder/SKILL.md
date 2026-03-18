---
name: codex-reminder
description: "Remind Ahmed about OpenAI Codex subscription ending and actions needed."
---

# Codex Removal Reminder

## Steps

### Step 1: Check current status
```bash
# Verify if Codex is still in model config
grep -i "codex" /root/.openclaw/openclaw.json 2>/dev/null && echo "Codex still configured" || echo "Codex already removed"
```

### Step 2: Deliver reminder
Send to Telegram:
```
Reminder: OpenAI Codex subscription ends April 1.
Actions needed:
1. Remove Codex model references from openclaw.json
2. Update any crons using Codex models
3. Cancel subscription in OpenAI dashboard

Status: [configured/already removed]
```

## Error Handling
- If config file not found: Report error

## Quality Gates
- Must check actual config state, not assume

## Output Rules
- No em dashes. Hyphens only.
