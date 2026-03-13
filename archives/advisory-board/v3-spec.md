# Advisory Board v3 Engine — Specification

## Problem with v2
- Scores static items from files, produces identical output daily
- Same recommendation every day ("Execute top priority first...")
- No change detection — doesn't know what's NEW
- No real-time signals — doesn't check emails, calendar, LinkedIn
- No cross-domain dot-connecting

## v3 Design Principles
1. **Change-first**: Only surface what CHANGED since last run
2. **Real-time inputs**: Pull from actual data sources, not just static markdown
3. **Dynamic recommendations**: Context-aware, never templated
4. **Cross-domain connections**: Link job search + content + calendar + market signals
5. **Concise output**: 15 lines max daily, 25 lines max weekly

## Input Sources (v3)

### Static (read from files)
- memory/active-tasks.md — current tasks
- jobs-bank/pipeline.md — job pipeline
- memory/linkedin_content_calendar.md — content schedule
- GOALS.md — strategic goals

### Dynamic (computed at runtime)
- memory/2026-*.md — recent daily logs (last 3 days)
- advisory-board/outputs/ — previous briefs (for change detection)
- jobs-bank/dossiers/ — recent dossier activity
- jobs-bank/handoff/*.trigger — pending review items
- memory/recruiter-responses.md — recruiter activity
- memory/linkedin-job-scout.md — latest job scout results
- memory/job-hunter-weekly-*.md — latest job hunter report
- memory/content-creator-weekly-*.md — latest content report
- memory/knowledge/weekly-content-brief.md — content intelligence

## Change Detection Algorithm

1. Load previous daily brief output
2. Load current scored items
3. Diff: what items are NEW, what items CHANGED score, what items RESOLVED
4. Only surface: new items, score changes >10%, resolved items, and stale items that became critical

## Output Format — Daily Brief

```
🎯 ADVISORY BOARD DAILY BRIEF — [Date]

WHAT CHANGED:
- [NEW/MOVED/RESOLVED]: [item] — [why it matters]

TOP 3 TODAY:
1. [item]: [specific action]
2. [item]: [specific action]  
3. [item]: [specific action]

🔗 CONNECTION: [cross-domain insight linking 2+ signals]

📌 DO THIS: [one specific recommendation with reasoning]
```

## Output Format — Weekly Report

```
📊 WEEKLY STRATEGY REPORT — [Week]

THIS WEEK'S MOVEMENT:
- [X] items advanced, [X] stalled, [X] new, [X] resolved

🔴 BIGGEST RISK: [specific risk with evidence]
🟢 BIGGEST OPPORTUNITY: [specific opportunity with next step]

PIPELINE: [X] active, [X] interview stage, [X] stale
CONTENT: [X] posts published, next week [READY/NEEDS WORK]
CALENDAR: [upcoming meetings/deadlines]

🔗 PATTERNS:
- [cross-domain pattern 1]
- [cross-domain pattern 2]

📌 TOP 3 MOVES NEXT WEEK:
1. [specific action + expected outcome]
2. [specific action + expected outcome]
3. [specific action + expected outcome]
```

## Technical Requirements
- Pure Python, no external dependencies beyond stdlib
- Read all inputs from filesystem (no API calls)
- Save output to advisory-board/outputs/
- Save state snapshot to advisory-board/state/ for change detection
- CLI: python3 phase3_engine.py --mode daily|weekly [--date YYYY-MM-DD]
- Must handle missing files gracefully (skip, don't crash)
