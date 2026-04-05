---
name: knowledge-brain-briefing
description: |
  Compile a daily briefing from the knowledge brain state.
  What changed, what's coming, who's waiting, what needs attention.
  Uses: python3 scripts/knowledge-brain.py stats + maintain + list
---

# Knowledge Brain Briefing Skill

## What It Produces
Daily briefing: entity status changes, open threads needing action, stale entities, today's schedule context.

## Workflow

### Step 1: Run Stats + Maintenance
```bash
python3 scripts/knowledge-brain.py stats
python3 scripts/knowledge-brain.py maintain
python3 scripts/knowledge-brain.py list
```

### Step 2: Pull From Source Files
Check these for today's context:
- `memory/YYYY-MM-DD.md` — yesterday's daily notes
- `memory/entities/people/` — all people with open threads
- `memory/entities/roles/` — all active job applications
- `coordination/job-applications.json` — application tracker

### Step 3: Structure the Briefing

**Section 1: Hot Topics (From maintenance alerts)**
- Stale entities needing update
- Timeline gaps (no activity in 14+ days)
- Open threads with deadlines

**Section 2: People in Play (Active contacts)**
- People with interviews scheduled
- Recruiters with active conversations
- Networking contacts at target companies

**Section 3: Active Applications**
- Applications with status = interview
- Applications needing follow-up (>14 days since last contact)
- Any new applications this week

**Section 4: Today's Work**
- From open threads in entity files
- From Notion Content Pipeline (today's scheduled post)
- From agent reports

### Step 4: Output Format
```
🧠 DAILY BRIEFING — [Date]

🔥 HOT (needs attention today)
- [item]

👥 PEOPLE IN PLAY
- [person]: [status + context]

💼 APPLICATIONS
- [company]: [role] — [status] — [next action]

📋 TODAY
- [action item]
```

## Entry Criteria
Run automatically at 05:45 Cairo daily (before daily intel). Results written to `intel/DAILY-INTEL.md`.

## Quality Rules
- Never hallucinate entity status. Quote from the brain.
- If entity has no timeline entries in 30+ days: mark as "cold" and flag for review.
- Always surface the single most urgent item at the top.
