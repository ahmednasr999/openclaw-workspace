# HEARTBEAT.md — Periodic Tasks

*Fires every hour via OpenClaw heartbeat*
*Last updated: 2026-02-24*

---

## Heartbeat Rules

Do NOT fire if: Ahmed is actively in conversation.
Do NOT send noise: Only message if there's something actionable.
Model for heartbeat tasks: MiniMax M2.5 (free — never burn paid tokens on background checks)
Cost discipline: Each heartbeat costs tokens. Make it count or skip.

---

## Hourly Checks (Every Heartbeat)

### 1. Deadline Radar

Check memory/active-tasks.md for any task with a deadline within the next 48 hours.

If found → message Ahmed:
"🔴 Deadline Alert: [task] is due [date/time]. Action needed."

If nothing urgent → stay silent.

### 2. Staleness Check

Check last-modified timestamp on memory/active-tasks.md.

If > 48 hours since last update → message Ahmed:
"⚠️ active-tasks.md is [X] days stale. Worth a refresh?"

Fire this alert maximum once per day, not every hour.

---

## Daily Checks (Once Per Day — 8:00 AM Cairo Time / EST+2)

### Morning Briefing

Model: MiniMax M2.5

Read and summarize:
- GOALS.md — any deadlines today or tomorrow
- memory/active-tasks.md — what's urgent
- memory/pending-opus-topics.md — anything queued

Send to Ahmed:
"☀️ Morning Brief — [date]
🔴 Urgent: [items]
📋 Today's focus: [top 3]
⏳ Pending deep work: [queued items]"

### End of Day (9:00 PM Cairo Time / EST+2)

If no session flush detected today → message Ahmed:
"💾 No session flush detected today. Worth a 5-min memory update before you close?"

---

## Weekly Check (Every Sunday — 9:00 AM Cairo Time)

### GOALS.md Review Prompt

Message Ahmed:
"📊 Weekly Goals Review — [date]
GOALS.md was last updated [X] days ago. Worth 10 minutes to update pipeline and metrics?"

---

## Cost Guard (Every Heartbeat)

Check session_status for daily spend.

| Threshold | Action |
|-----------|--------|
| > $3.00 | Auto-switch non-critical tasks to MiniMax M2.5 or Kimi (no approval needed) |
| > $5.00 | Auto-switch + notify Ahmed: "💸 Cost alert: $[X] today. Shifted lighter tasks to MiniMax." |
| > $10.00 | Hard alert + auto-throttle: "🚨 High spend: $[X]. Opus tasks paused, running on Haiku/MiniMax." |

---

## Response Format

**When nothing needs action:** Reply exactly `HEARTBEAT_OK` — nothing else. No checks listed, no reasoning, no narration.

**When something needs action:** Use this format only:

```
⏰ HEARTBEAT — [HH:MM Cairo]

🔴 [Item]: [one line]
🟡 [Item]: [one line]
💸 [Item]: [one line]

Action needed: [what to do]
```

Never show the checking process. Never list what was checked and cleared. Output only what matters.

---

## Silence Rules

Never message for:
- Routine completions with no action needed
- Information Ahmed already knows
- Anything that can wait until he starts a session
- Heartbeat confirmation ("I'm alive" pings — useless noise)

When in doubt → stay silent. A quiet heartbeat is better than a noisy one.

---

**Links:** [[MEMORY.md]] | [[memory/active-tasks.md]] | [[AGENTS.md]] | [[GOALS.md]]
