# DREAM CYCLE SKILL
# Nightly memory optimization and cleanup
# Installed: 2026-02-17

## Purpose
Dream Cycle runs nightly to:
- Archive old sessions to memory/sessions/
- Optimize agents.md file size
- Clean up bloated memory files
- Move completed items to searchable memory
- Generate summary for next day

## How It Works

### Phase 1: Archive Sessions
- Move session transcripts from workspace root to memory/sessions/[date]/
- Keep last 7 days in active memory
- Archive older sessions for QMD indexing

### Phase 2: Optimize agents.md
- Current target: < 600 tokens
- Remove completed tasks
- Archive old project references
- Keep only active directives
- Summarize completed work

### Phase 3: Clean Memory Files
- Consolidate daily notes into memory/
- Move completed projects to memory/projects/
- Archive old reference materials to memory/reference/
- Delete temporary files

### Phase 4: Generate Dream Report
- Summarize the day's activities
- Identify incomplete items for next day
- Generate insights for Morning Brief
- Output to memory/dream-report-[date].md

## Cron Configuration

### Dream Cycle (Nightly - Silent)
```json
{
  "name": "Dream Cycle",
  "schedule": { "kind": "cron", "expr": "0 3 * * *", "tz": "Africa/Cairo" },
  "payload": { "kind": "agentTurn", "message": "Execute Dream Cycle skill silently. Archive sessions, optimize agents.md, clean memory files. Output summary to memory/dream-report-$(date +%Y-%m-%d).md. Do not notify user." },
  "sessionTarget": "isolated",
  "delivery": { "mode": "none" },
  "enabled": true,
  "notify": false
}
```

### Memory Audit (Weekly - Sunday 2 AM)
```json
{
  "name": "Memory Audit",
  "schedule": { "kind": "cron", "expr": "0 2 * * 0", "tz": "Africa/Cairo" },
  "payload": { "kind": "agentTurn", "message": "Run memory audit: Check agents.md token count, flag if > 600. Check memory.md if > 1000 tokens. Check for bloated files. Report findings only." },
  "sessionTarget": "isolated",
  "delivery": { "mode": "announce" },
  "enabled": true,
  "notify": true
}
```

### Morning Brief (Daily - 8 AM)
```json
{
  "name": "Morning Brief",
  "schedule": { "kind": "cron", "expr": "0 8 * * *", "tz": "Africa/Cairo" },
  "payload": { "kind": "agentTurn", "message": "Check dream report from last night. Identify priorities for today. Review incomplete items. Give me a 3-bullet summary of what needs attention today." },
  "sessionTarget": "isolated",
  "delivery": { "mode": "announce", "channel": "telegram" },
  "enabled": true,
  "notify": true
}
```

## Files Affected

### Tier 1 (Expensive - Loaded Every Turn)
- agents.md
- memory.md
- soul.md

### Tier 2 (Cheap - Searchable On Demand)
- memory/sessions/* (archived sessions)
- memory/projects/* (completed projects)
- memory/reference/* (reference materials)
- memory/archive/* (older items)

### Tier 3 (Free - Full Read When Needed)
- Any file in workspace

## Optimization Rules

1. **Never delete information** - Move to searchable memory
2. **Keep agents.md < 600 tokens** - Critical for performance
3. **Archive sessions weekly** - Reduces context bloat
4. **Use QMD for recall** - Files in memory/ are indexed
5. **Summarize, don't eliminate** - Preserve key insights

## Installation

To install Dream Cycle:
1. Copy this skill to skills/dream-cycle/
2. Add cron jobs via OpenClaw
3. Enable morning brief for daily guidance

## Notes

- Dream Cycle runs silently (no notification)
- Morning Brief delivers to Telegram
- Memory Audit reports weekly
- All archives are searchable via QMD
