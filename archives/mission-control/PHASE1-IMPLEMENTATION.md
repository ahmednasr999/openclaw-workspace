# Mission Control v3 — Phase 1+2: Live Data Engine Implementation

**Status:** ✅ COMPLETE
**Date:** 2026-03-04
**Build:** Passing (0 errors, 1 pre-existing warning)

## Summary

Mission Control v3 Phase 1+2 replaces all hardcoded/seed data with live parsing of OpenClaw workspace memory files. Every module now displays real, current data from:

- `memory/active-tasks.md` - live task pipeline
- `MEMORY.md` - strategic priorities and decisions
- `GOALS.md` - objectives with progress tracking
- `jobs-bank/pipeline.md` - job applications and stages
- `memory/linkedin_content_calendar.md` - content calendar items
- `memory/cv-history.md` - CV application history

## Architecture

### 1. Cache Layer (`lib/sync/cache.ts`)
- Generic mtime-based file cache
- 30-second TTL (configurable)
- In-memory Map storage
- Automatic re-parse on file modification or TTL expiration

### 2. Parsers (`lib/sync/parsers.ts`)
Six markdown parsers with graceful fallback:

| Parser | Source File | Output Type |
|--------|-------------|------------|
| `parseActiveTasks()` | `memory/active-tasks.md` | `ParsedTask[]` |
| `parseMemory()` | `MEMORY.md` | `ParsedMemory` |
| `parseGoals()` | `GOALS.md` | `ParsedGoals` |
| `parsePipeline()` | `jobs-bank/pipeline.md` | `PipelineEntry[]` |
| `parseContentCalendar()` | `memory/linkedin_content_calendar.md` | `ContentItem[]` |
| `parseCvHistory()` | `memory/cv-history.md` | `CvHistoryEntry[]` |

All parsers handle missing files gracefully, returning empty arrays instead of crashing.

### 3. Sync Layer (`lib/sync/index.ts`)
High-level functions combining cache + parsers:

- `getTasks()` - live tasks from active-tasks.md
- `getMemory()` - decisions and priorities from MEMORY.md
- `getGoals()` - strategic objectives with progress
- `getPipeline()` - job applications with stages
- `getContentItems()` - content in various stages (draft/review/approved/posted)
- `getCvHistory()` - past CV customizations
- `getSystemHealth()` - RAM, disk, gateway, Ollama status
- `getOfficeMetrics()` - system metrics as dashboard cards
- `getAgentActivity()` - active agents from workspace
- `getDocsIndex()` - workspace documentation index
- `getSyncStatus()` - cache statistics and status

## API Routes

### `/api/modules?module=<name>`
Returns real data from workspace files:
- `tasks` - 15+ live tasks from active-tasks.md
- `memory` - 10+ decisions and threads from MEMORY.md
- `projects` - 6 objectives from GOALS.md
- `team` - 5+ agent entries
- `office` - system metrics (RAM, disk, gateway health)
- `docs` - workspace documentation index

**Response:**
```json
{
  "data": [...],
  "fetchedAt": "2026-03-04T13:12:55.488Z"
}
```

### `/api/job-radar`
Real job pipeline from `jobs-bank/pipeline.md`:
- 66 total applications
- Sorted by stage (Interview > Offer > Applied > CV Ready)
- Real ATS scores, applied dates, follow-up dates
- Decision classification (qualified/watch/dropped)

**Response:**
```json
{
  "leads": [...],
  "total": 66,
  "thresholdPolicy": "qualified >= 80",
  "fetchedAt": "2026-03-04T13:12:55.488Z"
}
```

### `/api/tasks`
Live tasks from `memory/active-tasks.md` + manual task creation:
- GET: 15 tasks from markdown
- POST: Create new manual task (saved to data/tasks.json)
- PATCH: Update task status

### `/api/content-factory`
Content items from `memory/linkedin_content_calendar.md`:
- 20+ items in various stages
- Fallback to ops-store.json if calendar empty
- Stage advancement (draft → review → approved → posted)

### `/api/sync-status` (NEW)
Cache and file sync statistics:
```json
{
  "lastSync": "2026-03-04T13:12:55.488Z",
  "fileCount": 5,
  "cacheEntries": 5,
  "cacheKeys": [
    "/root/.openclaw/workspace/memory/active-tasks.md",
    "/root/.openclaw/workspace/jobs-bank/pipeline.md",
    "/root/.openclaw/workspace/MEMORY.md",
    "/root/.openclaw/workspace/GOALS.md",
    "/root/.openclaw/workspace/memory/linkedin_content_calendar.md"
  ]
}
```

## Dashboard Page (`app/dashboard/page.tsx`)

Now a **server component** with real data:

### Stat Cards
- **Open tasks**: count from active-tasks.md (in_progress + backlog + review)
- **Active applications**: count from pipeline.md (non-closed entries)
- **Content due**: count from content calendar (draft + review items)
- **System health**: percentage score (RAM, disk, gateway, Ollama)

### Lower Grid
1. **Priority tasks** (top 5): High priority first, non-completed
2. **Job pipeline** (top 4): Interview entries first, sorted by stage
3. **Goal progress** (top 4): Objectives with progress bars

All data updates every 30 seconds (revalidate: 30).

## Components

### `task-board.tsx`
- Real tasks from `/api/tasks` (active-tasks.md)
- Kanban columns: Recurring | Backlog | In Progress | Review | Done
- WIP limits enforced
- Task creation saves to data/tasks.json
- Section badges for task organization
- Health, progress, open count telemetry

### `job-radar.tsx`
- Real pipeline from `/api/job-radar`
- 66 active applications displayed
- Stage badges (Interview=amber, Applied=blue, Closed=gray)
- Filter by decision (qualified/watch/dropped)
- Age labels (fresh/warm/aging)
- Applied dates and follow-up dates shown

### `module-panels.tsx`
- **DocsPanel**: workspace documentation index
- **MemoryPanels**: strategic priorities and open threads
- **TeamPanel**: active agents with status
- **OfficePanel**: system metrics (RAM, disk, gateway)
- **ProjectsPanels**: goal objectives with progress bars

### `linkedin-factory.tsx`
- Real content items from `/api/content-factory`
- Stage summary cards (draft/review/approved/posted)
- Filterable by stage
- SLA tracking (on track / near breach / breached)
- Stage advancement buttons

## Breaking Changes

**NONE.** All existing route URLs remain unchanged:
- `/api/modules` - still works, now returns live data
- `/api/job-radar` - still works, now returns live pipeline
- `/api/tasks` - still works, hybrid (live + manual)
- `/api/content-factory` - still works, live first then fallback
- `/dashboard`, `/tasks`, `/job-radar`, etc. - all work with live data

## Cleanup

✅ **Removed dependencies:**
- `lib/parity.ts` - seed data imports removed from task-store
- Hardcoded `radarLeads` from ops-store.ts (kept cron monitoring)
- Hardcoded `contentItems` from ops-store.ts (kept cron monitoring)
- Seeded tasks no longer auto-populate tasks.json

✅ **Files simplified:**
- `lib/module-store.ts` - now a thin wrapper using sync layer
- `lib/task-store.ts` - empty seed, only CRUD operations
- `lib/ops-store.ts` - empty defaults, cron monitoring unchanged

## Features

✅ **Real-time data**
- File mtime checking ensures fresh data
- 30s TTL balances performance vs freshness
- Automatic re-parse on file changes

✅ **Graceful degradation**
- Missing files return empty arrays, never crash
- Fallback from calendar to ops-store for content items

✅ **Cairo timezone**
- All timestamps support Africa/Cairo timezone
- Components format dates with `timeZone: "Africa/Cairo"`

✅ **System health**
- RAM usage monitoring
- Disk usage tracking
- Gateway reachability check
- Ollama status detection
- Health score 0-100

✅ **No em dashes**
- All string literals verified
- Parser output clean
- Components render clean text

## Testing

### Build Status
```
✓ Compiled successfully in 13.4s
✓ TypeScript passed
✓ 36/36 pages generated
✓ Build artifacts in .next/
✓ Next.js 16.1.6 ready
```

### Lint Status
```
✓ 0 errors
✗ 1 warning (pre-existing in proxy.ts, unrelated)
```

### API Test Results
```
GET /api/modules?module=tasks      → 15 tasks ✓
GET /api/job-radar                 → 66 applications ✓
GET /api/modules?module=memory     → 10 memory items ✓
GET /api/modules?module=projects   → 6 objectives ✓
GET /api/content-factory           → 20 content items ✓
GET /api/sync-status               → 5 cached files ✓
```

### Live Dashboard
```
Open tasks: 15
Active applications: 66
Content due: 20
System health: 85%
(Real data from workspace files)
```

## Next Steps

1. Monitor cron health (already integrated, no changes needed)
2. Create `/api/system` endpoint if deeper health monitoring needed
3. Add real-time file watchers if sub-second sync required
4. Integrate with agenda/BullMQ if task queuing needed

## File Locations

### New Files
- `lib/sync/cache.ts` (1.1 KB)
- `lib/sync/parsers.ts` (21.7 KB)
- `lib/sync/index.ts` (10.1 KB)
- `app/api/sync-status/route.ts` (0.3 KB)

### Modified Files
- `lib/module-store.ts` (0.8 KB, simplified)
- `lib/task-store.ts` (1.8 KB, no seeds)
- `lib/ops-store.ts` (11.5 KB, hardcoded arrays removed)
- `app/api/modules/route.ts` (2.1 KB, sync layer)
- `app/api/job-radar/route.ts` (2.3 KB, sync layer)
- `app/api/tasks/route.ts` (2.2 KB, sync layer)
- `app/api/content-factory/route.ts` (1.3 KB, sync layer)
- `app/dashboard/page.tsx` (6.3 KB, server component)
- `components/task-board.tsx` (9.4 KB, real data)
- `components/job-radar.tsx` (6.1 KB, real data)
- `components/module-panels.tsx` (7.9 KB, real data)
- `components/linkedin-factory.tsx` (6.2 KB, real data)

**Total New Code: ~80 KB**

## Deployment

1. ✅ Build: `npm run build` (13.4s)
2. ✅ Lint: `npm run lint` (0 errors)
3. ✅ Start: `next start -p 3100` (ready in 854ms)
4. ✅ Test: All APIs responding with live data

**Status: Ready for production**

---

**Implemented by:** Subagent (mc-phase1)
**Timestamp:** 2026-03-04T13:12:55.488Z
**Requester:** main:main
