---
name: morning-briefing
description: "Daily morning briefing - run script only, never improvise."
---

# Morning Briefing

## CRITICAL: Execute this EXACT command. Nothing else.

```bash
cd /root/.openclaw/workspace && python3 scripts/morning-briefing-orchestrator.py 2>&1
```

Send the stdout output verbatim to Telegram chat 866838380.

## Rules (NON-NEGOTIABLE)

1. Run the command above. That's it.
2. Do NOT gather data yourself
3. Do NOT create Notion pages yourself
4. Do NOT write your own briefing
5. Do NOT add images, bookmarks, or engagement targets
6. Do NOT modify or "improve" the output
7. If the script fails, send: "⚠️ Briefing script failed: [paste stderr]"
8. The script handles EVERYTHING: Notion page, data, formatting, dashboard

## Why This Matters

The script creates a specific Notion page with toggle blocks, executive summary,
ATS-scored jobs, and auto-populated properties. If you improvise, the page will
be wrong. JUST RUN THE SCRIPT.

## Timeout: 300s
