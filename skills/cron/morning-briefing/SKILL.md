---
name: morning-briefing
description: "Daily morning briefing delivered via Telegram and Notion."
---

# Morning Briefing

## What To Do

Run the orchestrator script. It handles EVERYTHING: data gathering, Notion page, Telegram format, Dashboard update.

```bash
cd /root/.openclaw/workspace && python3 scripts/morning-briefing-orchestrator.py
```

The script outputs a Telegram-formatted briefing to stdout. Deliver it as-is.

## Delivery

1. The script prints the Telegram message to stdout - send it to chat 866838380
2. If the script fails, report the error instead

## Rules
- Do NOT gather data yourself - the script does it
- Do NOT create a Notion page yourself - the script does it
- Do NOT call any other scripts - this one script is self-contained
- Do NOT add commentary or reformatting - deliver the output verbatim
- If script exits non-zero, send: "⚠️ Briefing script failed: [error]"

## Timeout: 300s
The script completes in under 60 seconds. 300s is generous safety margin.
