# Weekly Agent Review Skill

**Trigger:** Every Sunday 10:00 AM Cairo (UTC+2)
**Script:** `scripts/weekly-agent-review.py`
**Cron:** `0 8 * * 0` (UTC) → 10:00 AM Cairo

---

## Purpose

Automatically review the past week's agent failures and corrections, identify recurring patterns, apply targeted skill improvements, and log a summary to `memory/lessons-learned.md`.

---

## Workflow

### Step 1 — Parse Recent Lessons
Load `memory/lessons-learned.md`. Extract all level-2 (`## YYYY-MM-DD`) sections from the past 7 days.

### Step 2 — Signal Detection
Scan each section for failure/correction keywords:
`failed`, `error`, `bug`, `fix`, `wrong`, `missed`, `correction`, `partial`, etc.

### Step 3 — Pattern Grouping
Map signals to known skill names using the alias table in the script.
Group signals by skill. Count occurrences.

### Step 4 — Threshold Decision
- **≥ 2 occurrences of same pattern** → auto-patch skill file
- **< 2 occurrences or unclear pattern** → flag for human review
- **0 occurrences** → log "system healthy"

### Step 5 — Apply Patches
For each auto-patchable skill:
1. Read current SKILL.md
2. Append a dated `## 🔧 Auto-Improvement` block with targeted suggestion
3. Do NOT rewrite the file — only append; human must integrate the fix

### Step 6 — Log Weekly Review
Append a `## Weekly Review (YYYY-MM-DD → YYYY-MM-DD)` block to `memory/lessons-learned.md` listing:
- Auto-patched skills with what changed
- Flagged skills with reason
- Inventory of active skills checked

### Step 7 — Print Summary
Output to stdout for cron monitoring.

---

## Rules

| Rule | Detail |
|------|--------|
| Conservative | Only auto-fix patterns with ≥ 2 matching occurrences in 7 days |
| No fabrication | Suggestions must be grounded in actual snippets from lessons-learned |
| Append-only | Never rewrite a skill file — only append improvement notes |
| Flag > guess | When pattern is ambiguous, always flag for Ahmed rather than guess |
| No duplicate blocks | Skip if weekly review block for same date range already exists |
| One concern per fix | Each patch block addresses one specific failure mode |

---

## Cron Registration

To register this cron, run:
```bash
openclaw cron add \
  --name "weekly-agent-review" \
  --schedule "0 8 * * 0" \
  --command "python3 /root/.openclaw/workspace/scripts/weekly-agent-review.py" \
  --timezone "Africa/Cairo"
```

Or add to the crontab manually:
```cron
0 8 * * 0 python3 /root/.openclaw/workspace/scripts/weekly-agent-review.py >> /root/.openclaw/workspace/memory/cron-recovery.log 2>&1
```

---

## Output Files Modified

| File | Change |
|------|--------|
| `memory/lessons-learned.md` | Appends `## Weekly Review` block |
| `skills/<name>/SKILL.md` | Appends `## 🔧 Auto-Improvement` block (per skill patched) |

---

## Monitoring

Check results in:
- `memory/lessons-learned.md` → Weekly Review section at bottom
- `memory/cron-recovery.log` → stdout/stderr from cron runs
- Manually review any 🚩 Flagged items each Monday

---

## Related

- `scripts/weekly-agent-review.py` — main script
- `memory/lessons-learned.md` — source of truth for errors
- `skills/self-improvement/` — captures individual learnings
- `skills/clawback/` — git discipline for skill file changes
