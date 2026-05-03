# Dream Report - 2026-05-03

## Promoted (3 items)
- Salary remains a primary GCC executive-role decision factor -> MEMORY.md (reason: explicit profile-drip answer seen 1 time in memory/2026-05-01.md; detailed baseline already lives in USER.md)
- Re-check success logs/live state before external publish recovery -> AGENTS.md (reason: duplicate LinkedIn publish incident seen 1 time in memory/2026-05-03.md)
- Force `/usr/bin/openclaw` or `/usr/bin` PATH before package updates on this host -> TOOLS.md (reason: stale `/usr/local/bin/openclaw` checkout hijacked the first update attempt, seen 1 time in memory/2026-05-03.md)

## Deduplicated (1 items)
- Merged: duplicate opening LinkedIn/Composio publish block in memory/2026-05-03.md -> kept one canonical copy

## Archived (0 files)
- None; `find memory/ -maxdepth 1 -name '2026-*.md' -mtime +14 -type f` returned no candidates.

## Flagged Stale (0 items)
- None.

## Skipped (3 items)
- Composio LinkedIn image-post lane details (reason: compact TOOLS.md already has the required true `s3key` rule and docs/reference/TOOLS.full.md contains the detailed workbench flow; source detail remains in memory/2026-05-03.md)
- JobZoom still-open review lane (reason: fresh code change needs the next scheduled run verification before durable promotion beyond the protected JobZoom lane)
- Duplicate hashed bundle post-update patch detail (reason: checker script was already updated and the package-path gotcha was the higher-risk compact TOOLS promotion for this run)
