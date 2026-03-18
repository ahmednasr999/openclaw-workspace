---
name: sie-360
description: "Self-Improvement Engine daily run: analyze learnings, detect patterns, check for unacted items, and enforce code/cron/SIE rules."
---

# SIE 360 Daily

Daily self-improvement audit that checks learnings enforcement, detects patterns, and ensures system quality.

## Prerequisites
- Script: `scripts/self-improvement-engine.py`
- Notion Learnings DB: `3268d599-a162-810f-9f1b-ffdc280ae96d`
- Script: `scripts/notion_sync.py` with `audit_learnings_staleness()` and `detect_repeated_learnings()`
- File: `.learnings/LEARNINGS.md`, `.learnings/ERRORS.md`

## Steps

### Step 1: Run SIE suggestions
```bash
cd /root/.openclaw/workspace && python3 scripts/self-improvement-engine.py --suggest
```
Capture output for analysis.

### Step 2: Audit learnings staleness
```python
from scripts.notion_sync import audit_learnings_staleness
stale = audit_learnings_staleness()
```
Flag any learnings marked "Unacted" for 48+ hours.

### Step 3: Detect repeated patterns
```python
from scripts.notion_sync import detect_repeated_learnings
patterns = detect_repeated_learnings()
```
If same error type appears 3+ times, escalate to "SIE Rule" enforcement level.

### Step 4: Triage new learnings
For each new learning, assign enforcement type:
- **Code Check**: Add guard/validation in the relevant script
- **SIE Rule**: Add to nightly audit checklist
- **Cron Constraint**: Add instruction to cron skill
- **Logged**: Informational only, no enforcement needed

### Step 5: Update Notion
- Update enforcement status in Learnings DB
- Add "Fix Applied In" field for Code Check items
- Sync results to System Log DB

### Step 6: Report
Output summary: "[X] learnings reviewed, [Y] unacted flagged, [Z] patterns detected"

## Error Handling
- If SIE script fails: Report error, check if scripts/self-improvement-engine.py exists
- If Notion unreachable: Save results locally to `.learnings/pending-sync.json`

## Quality Gates
- All "Code Check" items must have a "Fix Applied In" reference
- No learning should stay "Unacted" for more than 48 hours
- Repeated patterns (3+) must be escalated automatically

## Output Rules
- No em dashes. Use hyphens.
- Be specific about which learnings need action
