# Session Handoff Enforcement

## Rule
Before ending any session that performed work, the agent MUST write a handoff note using the 9-section template.

## Check
At session end, verify:
1. Did the agent create/update a file matching `memory/YYYY-MM-DD.md` or `memory/agents/daily-*.md`?
2. Does that file contain all 9 sections from `templates/session-handoff.md`?
3. Are empty sections marked "None" (not omitted)?

## Auto-Generate Fallback
If the agent session ends without a proper handoff (e.g., timeout, crash, user disconnected):
- The next agent session that reads the daily file should auto-generate a handoff from the audit log
- Read `memory/agents/audit-log.jsonl` for that date
- Read `memory/agents/daily-actions.jsonl` for that date
- Compile into the 9-section format
- Mark as "[Auto-generated from audit log]" at the top

## What "Performed Work" Means
A session "performed work" if ANY of these occurred:
- Files were created or modified
- External tools were called (LinkedIn, email, web)
- Cron jobs were created or modified
- Config was changed
- Sub-agents were spawned
- Decisions were made with Ahmed

If a session was only Q&A with no file/tool changes → handoff is optional.
