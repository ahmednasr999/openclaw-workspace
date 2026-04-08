# Pre-Tool Check - Quick Reference

## Decision Tree (evaluate top to bottom, STOP at first denial)

```
Tool Call Incoming
  │
  ├── Is tool in my deny_names or deny_prefixes? → DENY + escalate
  │
  ├── Does tool target a core file? → Check effort gate
  │     └── Effort too low? → DENY + suggest upgrade
  │
  ├── Is it 00:00-06:00 Cairo? → AFK mode
  │     ├── Is tool in afk deny list? → QUEUE to afk-queue.jsonl
  │     └── Is it a cron_scheduled exception? → ALLOW
  │
  ├── Is tool rate-limited? → Check audit-log.jsonl counts
  │     └── Over limit? → DENY + report cooldown
  │
  ├── Will this be file #3+ in this task? → FLAG for verification
  │
  └── PROCEED with tool call
```

## File Checksum Protocol (for core files only)

Before editing any protected file:
1. Read current content
2. Note the last-modified line count or first 100 chars as a lightweight checksum
3. After editing, verify the file wasn't modified by another agent between your read and write
4. If it was → abort your edit, re-read, re-apply your changes to the new version

This prevents the race condition where CEO edits MEMORY.md while HR is also editing it.

## AFK Queue Format

```json
{
  "timestamp": "2026-04-01T02:15:00Z",
  "agent": "CMO",
  "tool": "LINKEDIN_CREATE_LINKED_IN_POST",
  "args_summary": "Post about AI in healthcare, 1200 chars",
  "reason": "AFK mode - queued for morning review",
  "priority": "normal",
  "auto_approve": false
}
```

Morning briefing reads `afk-queue.jsonl` and presents queued items to Ahmed for approval.
