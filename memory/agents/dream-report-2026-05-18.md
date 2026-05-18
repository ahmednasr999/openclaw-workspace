# Dream Report - 2026-05-18

## Promoted (2 items)
- Pre-compaction flushes should append only to `memory/YYYY-MM-DD.md` and avoid timestamped variants/core-file edits unless explicitly requested -> `MEMORY.md` (reason: seen in timestamped May 15/16 flush artifacts and reinforced in `memory/2026-05-17.md`)
- LCM/offline compaction closeout must verify dependency paths, force-compact thresholds, remaining zero-summary candidates, duplicate session rows, and bounded aggregate SQLite health checks -> `TOOLS.md` (reason: seen 4 times in `memory/agent-traces/lessons.md`, 2026-05-17 to 2026-05-18)

## Deduplicated (0 items)
- None.

## Archived (0 files)
- None.

## Flagged Stale (0 items)
- None.

## Skipped (4 items)
- JobZoom applied-ledger rule (already promoted in `MEMORY.md`, no duplicate needed)
- Telegram command-menu scope verification (already promoted in `TOOLS.md`, no duplicate needed)
- Model Guardian transient probe handling (kept in trace lessons for now, not promoted because the current durable tool slot was used for recurring LCM compaction failures)
- Old daily-note archive pass (no `memory/2026-*.md` files older than 14 days were found by mtime)
