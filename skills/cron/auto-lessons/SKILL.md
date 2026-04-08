---
name: auto-lessons-cron
description: "Daily cron job at 11 PM Cairo to extract lessons from the day's sessions and append to memory/lessons-learned.md. Lightweight alternative to the heavy self-improvement skill — runs once per day instead of 12x per session."
metadata:
  schedule: "23:00 Cairo (Africa/Cairo)"
  skill_type: cron
---

# Auto Lessons Learned Cron

Runs daily at 11 PM Cairo to automatically capture lessons from the day's sessions.

## When to Use

- **Automatic:** Scheduled cron job (11 PM Cairo daily)
- **Manual:** After a particularly productive or challenging session

## What This Does

### Step 1: Find Sessions
Finds all sessions from today in `~/.openclaw/agents/main/sessions/`

### Step 2: Filter Trivial
Filters out trivial sessions (< 5 exchanges)

### Step 3: Extract Lessons
Uses LLM to extract:
- Corrections made by user
- Errors encountered
- Preferences learned
- Better approaches discovered
- Missed opportunities

### Step 4: Append to Memory
Appends structured entries to `memory/lessons-learned.md`

## Format

```markdown
## [Date]

### Category
- What happened → What to do differently
```

Categories: `correction`, `error`, `preference`, `improvement`, `missed_opportunity`

## Manual Run

```bash
python /root/.openclaw/workspace/scripts/auto-lessons-learned.py --all
```

## Dry Run (Preview)

```bash
python /root/.openclaw/workspace/scripts/auto-lessons-learned.py --all --dry-run
```

## Cron Setup

The cron job should:
1. Run at 23:00 Cairo (21:00 UTC)
2. Execute the Python script
3. Log output to a file for debugging

## Design Principles

- **Lightweight:** Only runs once per day (not after every session)
- **Low noise:** Skips trivial sessions with < 5 exchanges
- **Structured:** Uses consistent format for easy parsing
- **No duplicate entries:** Checks if lesson already exists before adding
- **Complementary:** Works alongside manual lesson capture (user saying "remember this")

## Integration with Self-Improvement Skill

This cron is a **replacement** for the frequent self-improvement hooks:
- Old: Self-improvement injected 12x per session → token waste
- New: Auto-lessons runs 1x per day → efficient

Both can coexist: manual captures immediate learnings, cron captures session-wide patterns.

## Error Handling
- If sessions directory missing: report "No sessions found" and stop
- If script fails: report error with stderr, do not retry
- If no lessons extracted: append "No lessons captured" entry with date

## Quality Gates
- No duplicate entries (check before appending)
- Each lesson has: date, category, what happened, what to do differently
- Categories must be one of: correction, error, preference, improvement, missed_opportunity
