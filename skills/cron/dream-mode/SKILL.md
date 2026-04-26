---
name: dream-mode
description: "Cron skill for Dream Mode memory consolidation. Use this when running the nightly Dream Mode job, converting Dream Mode cron prompts, or auditing memory promotion, pruning, stale tagging, and dream reports."
---

# Dream Mode Memory Consolidation

Run the nightly memory consolidation safely and conservatively. The goal is to preserve durable lessons, reduce active memory clutter, and produce a concise report. Do not create busywork.

## Operating rules

- Work in `/root/.openclaw/workspace`.
- Do not use Mission Control task logging.
- Never modify `memory/master-cv-data.md`.
- Never delete files. Archive old daily notes instead.
- Do not touch credentials, configs, gateway state, cron definitions, or external services.
- Be conservative with core files: `MEMORY.md`, `SOUL.md`, `TOOLS.md`, `AGENTS.md`.
- Total promotions across all target files: max 5 per run.
- Promotions to `MEMORY.md`: max 3 per run.
- Promotions to `TOOLS.md`: max 1 per run.
- Promotions to `SOUL.md`: max 1 per run and only for behavior corrections confirmed 3 or more times.
- If `MEMORY.md` would exceed 200 lines after a promotion, skip that promotion and flag it in the report.
- Tag every promotion with `<!-- dream-promoted YYYY-MM-DD -->`.
- Do not use em dashes. Use commas or hyphens.

## Phase 1: Orient

Read these baseline files before changing anything:

- `MEMORY.md`
- `SOUL.md`
- `TOOLS.md`
- `AGENTS.md`
- `memory/lessons-learned.md`

Identify what is already captured so you do not duplicate it.

## Phase 2: Gather recent evidence

Inspect recent artifacts from the last 7 days. Use exact file reads for anything you may promote.

Suggested commands:

```bash
cd /root/.openclaw/workspace

# Daily notes
ls -la memory/2026-*.md 2>/dev/null | tail -7

# Agent daily logs
ls -la memory/agents/daily-*.md 2>/dev/null | tail -7

# Context traces
ls -la memory/context-traces/ 2>/dev/null | tail -10

# Recent lessons
tail -100 memory/lessons-learned.md 2>/dev/null || true

# Recent git activity
git log --oneline --since='7 days ago' | head -30
```

Collect only evidence-backed findings:

- Decisions made
- Stable preferences expressed by Ahmed
- Corrections from Ahmed, especially "no", "wrong", "actually", or repeated quality challenges
- Tools or workflows that failed
- Tools or workflows that worked well
- Recurring patterns seen 3 or more times

## Phase 3: Consolidate

For each finding, decide whether it belongs in a durable file.

### Promote to `MEMORY.md`

Use for:

- Recurring patterns with 3 or more occurrences
- Stable user preferences
- Important decisions that affect future work
- Job search, content, memory, or operating facts that should survive sessions

Before editing, check whether the same point is already present. Prefer improving a precise existing entry over adding a duplicate.

### Promote to `TOOLS.md`

Use for:

- Tool gotchas
- Working command patterns
- Integration constraints
- Configuration facts that affect future technical work

### Promote to `SOUL.md`

Use rarely. Only promote behavioral rules when Ahmed has corrected or reinforced the behavior 3 or more times and the rule should shape future judgment.

### Deduplicate `MEMORY.md`

If two entries say the same thing, keep the more precise one and remove or merge the weaker duplicate. Do not delete meaning.

## Phase 4: Prune and archive

Find daily notes older than 14 days:

```bash
cd /root/.openclaw/workspace
find memory/ -maxdepth 1 -name '2026-*.md' -mtime +14 -type f
```

For each old daily note:

1. Create the month archive directory, for example `memory/archive/2026-04/`.
2. Move the file into that archive directory.
3. List every moved file in the report.

For `MEMORY.md` entries:

- Remove entries tagged `<!-- completed -->` only if the content is truly no longer needed.
- For entries not referenced in any file from the last 30 days, add `<!-- stale-check YYYY-MM-DD -->` instead of deleting.

## Report

Write the report to:

`memory/agents/dream-report-YYYY-MM-DD.md`

Use this exact structure:

```markdown
# Dream Report - YYYY-MM-DD

## Promoted (X items)
- [item] -> [target file] (reason: seen N times in [sources])

## Deduplicated (X items)
- Merged: [old entry 1] + [old entry 2] -> [kept version]

## Archived (X files)
- [filename] -> memory/archive/YYYY-MM/

## Flagged Stale (X items)
- [item in MEMORY.md] (last referenced: [date])

## Skipped (X items)
- [item reviewed but no action needed] (reason)
```

If nothing needed action, still write the report with:

`No changes needed - memory is clean.`

## Final response

The cron job may announce the final response. Keep it short:

- Report path
- Counts for promoted, deduplicated, archived, flagged stale, skipped
- Any safety skips or blockers
