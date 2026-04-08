# Dream Mode - Memory Consolidation Agent

## Problem
Memory maintenance is manual. Daily notes pile up, lessons-learned.md grows unreviewed, patterns go unnoticed, stale entries stay forever. Ahmed shouldn't have to remind me to clean up my own memory.

## Solution
A scheduled cron job (agentTurn, isolated session) that runs during off-hours, reviews recent memory artifacts, and consolidates them. Four phases, same as Claude Code's dream mode: Orient → Gather → Consolidate → Prune.

## Schedule
- **When:** Daily at 4:00 AM Cairo (02:00 UTC), Sun-Thu
- **Why 4 AM:** Low activity window, before 5:45 AM intel generation, before morning briefing

## Four Phases

### Phase 1: Orient
- Read MEMORY.md, SOUL.md, TOOLS.md, AGENTS.md (current state)
- Read `memory/lessons-learned.md`
- Identify what's already captured vs what's new

### Phase 2: Gather
- Scan `memory/agents/daily-*.md` from last 7 days
- Scan `memory/2026-*.md` daily notes from last 7 days
- Scan `memory/context-traces/` for recurring patterns
- Collect: decisions made, preferences expressed, corrections given, tools that failed, workflows that worked

### Phase 3: Consolidate
- **Promote to MEMORY.md:** Recurring patterns (3+ occurrences), new stable preferences, important decisions
- **Promote to TOOLS.md:** Technical learnings, tool gotchas, working configurations
- **Promote to SOUL.md:** Behavioral corrections (only if pattern confirmed 3+ times)
- **Promote to AGENTS.md:** Workflow improvements, routing changes
- **Deduplicate:** Merge entries that say the same thing in different words
- **Format:** Every promotion includes `<!-- dream-promoted YYYY-MM-DD -->` tag

### Phase 4: Prune
- **Archive:** Move daily notes older than 14 days to `memory/archive/YYYY-MM/`
- **Remove from MEMORY.md:** Entries tagged `<!-- completed -->` or referencing closed tasks
- **Flag stale:** Entries not referenced in 30+ days get `<!-- stale-check YYYY-MM-DD -->` tag
- **Never delete:** Only move to archive. Never lose data.

## Output
After each run, write a brief report to `memory/agents/dream-report-YYYY-MM-DD.md`:
```
# Dream Report - YYYY-MM-DD

## Promoted (X items)
- [item] → [target file] (reason)

## Deduplicated (X items)
- [merged entries]

## Archived (X files)
- [files moved]

## Flagged Stale (X items)
- [items needing review]

## Skipped
- [items reviewed but no action needed]
```

## Notify CEO
Post summary to CEO General (topic 10): "🌙 Dream consolidation complete - X promoted, Y archived, Z flagged stale"

## Safety Rails
- Never modify master-cv-data.md
- Never delete, only archive
- Max 5 promotions per run (avoid flooding core files)
- If MEMORY.md exceeds 200 lines after promotion, flag for manual review instead of writing
- Dry-run mode: `--dry-run` flag that reports what it WOULD do without writing

## Implementation
- **Type:** OpenClaw cron job (agentTurn, isolated session)
- **No script needed** - the agent prompt IS the implementation
- **Prompt contains:** All four phases as step-by-step instructions with file paths
- **Delivery:** announce to CEO General (topic 10)
