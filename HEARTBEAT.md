# HEARTBEAT.md — Periodic Tasks

*Fires every hour via OpenClaw heartbeat*
*Last updated: 2026-03-03*

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

## Daily Checks (Once Per Day, 8:00 AM Cairo Time)

### Morning Briefing — REPLACED BY EXECUTIVE INTELLIGENCE BRIEFING CRON

The old morning brief is replaced by "Executive Intelligence Briefing" cron job (runs daily 6 AM Cairo).
It covers: job market pulse, company intel, LinkedIn status, calendar + deadlines, daily new idea, strategic recommendation.
Do NOT duplicate this in heartbeat. The cron handles it.

### End of Day (9:00 PM Cairo Time / EST+2)

If no session flush detected today → message Ahmed:
"💾 No session flush detected today. Worth a 5-min memory update before you close?"

---

## Monthly Check (1st of Each Month — 9:00 AM Cairo Time)

### Workspace Health Audit

Scan the workspace structure and flag:
- Root file count > 20 (should be ~12 core files + folders)
- Any PDFs, HTMLs, PNGs, or temp files in root
- Any new directories that don't fit the established structure
- .gitignore gaps (venvs, build artifacts, temp files)
- Stale folders with no recent changes (> 60 days)

If issues found → message Ahmed with specific cleanup recommendations.
If clean → silent.

---

## Weekly Check (Every Sunday — 9:00 AM Cairo Time)

### GOALS.md Review Prompt

Message Ahmed:
"📊 Weekly Goals Review — [date]
GOALS.md was last updated [X] days ago. Worth 10 minutes to update pipeline and metrics?"

---

## Usage Guard (Every Heartbeat)

Check `session_status` for 5-hour and weekly usage pressure.

| Threshold | Action |
|-----------|--------|
| 5h remaining <= 30% | Auto-shift non-critical work to MiniMax M2.5/Kimi |
| 5h remaining <= 20% | Notify Ahmed and pause optional heavy jobs |
| Weekly remaining <= 20% | Reserve premium models for critical tasks only |

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
