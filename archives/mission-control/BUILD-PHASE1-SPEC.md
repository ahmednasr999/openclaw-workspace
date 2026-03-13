# Mission Control v3 — Phase 1+2: Live Data Engine + Module Wiring

## Objective
Replace ALL hardcoded/seed data with live parsing of OpenClaw workspace memory files. Every module must show real, current data.

## Architecture Decision
- **No SQLite** — overkill for single-user read-only dashboard
- **Direct file parsing** with in-memory cache + file mtime check
- Cache TTL: 30 seconds (re-read file only if mtime changed or 30s elapsed)
- All parsers in `lib/sync/` directory

## Workspace Root
The OpenClaw workspace is at: `/root/.openclaw/workspace/`
All file paths below are relative to that root.

## File Parsers Needed

### 1. active-tasks.md Parser
**Source:** `memory/active-tasks.md`
**Format:** Markdown with `## 🔴 URGENT`, `## 🟡 In Progress`, `## 🟢 Recurring`, `## ✅ Recently Completed` sections
**Each task has:** title (bold text), status line, next action
**Output:** Array of `{ id, title, status, priority, assignee, dueDate, section }`
**Maps to:** Task Board, Dashboard task count

### 2. MEMORY.md Parser
**Source:** `MEMORY.md`
**Sections to parse:**
- `## 🎯 Current Strategic Priorities` → priorities array
- `## 📚 Lessons Learned` → lessons array with dates
- `## ✅ Completed Milestones` → milestones array
- `## 💼 Work & Communication Preferences` → key decisions
**Output:** `{ priorities: [], lessons: [], milestones: [], decisions: [] }`
**Maps to:** Memory page, Dashboard

### 3. GOALS.md Parser
**Source:** `GOALS.md`
**Format:** Strategic objectives with progress indicators
**Output:** `{ objectives: [{ id, title, progress, status, keyResults: [] }] }`
**Maps to:** Dashboard progress bars, Intelligence page

### 4. pipeline.md Parser
**Source:** `jobs-bank/pipeline.md`
**Format:** Job applications table/list with stages
**Stages:** Identified → Applied → Interview → Offer → Closed
**Each entry:** company, role, stage, ATS score, applied date, follow-up date, notes
**Output:** Array of `{ id, company, role, stage, atsScore, appliedDate, followUpDate, notes, salary }`
**Maps to:** Job Radar, Dashboard active apps count, Handoff Gate

### 5. LinkedIn Content Parser
**Source:** `memory/linkedin_content_calendar.md` + files in `drafts/` directory
**Output:** Content items with stages (draft/review/approved/posted)
**Maps to:** Content Factory, Dashboard content due count

### 6. System Health Parser
**Source:** OpenClaw CLI commands (already partially implemented in ops-store.ts)
**Add:** RAM usage, disk usage, gateway health check (curl localhost:18789/health), Ollama status
**Output:** `{ ram: { used, total }, disk: { used, total }, gateway: { status, uptime }, ollama: { status } }`
**Maps to:** Office page, Dashboard automation health

### 7. Agent Activity Parser  
**Source:** Run `openclaw` CLI or read agent session files
**Output:** `{ agents: [{ name, lastAction, lastActionTime, status }] }`
**Maps to:** Team page

### 8. Docs Index Parser
**Source:** Scan `*.md` files in workspace root + `memory/` + `skills/`
**Output:** `{ docs: [{ id, title, category, path, updatedAt, sizeBytes }] }`
**Maps to:** Docs page

## Cache Layer (`lib/sync/cache.ts`)
```typescript
// Simple mtime-based cache
interface CacheEntry<T> {
  data: T;
  mtime: number;
  fetchedAt: number;
}

// getOrParse(filePath, parserFn, ttlMs = 30000) → T
// Checks file mtime, returns cached if unchanged, re-parses if stale
```

## API Route Updates

### `/api/modules?module=tasks` → use active-tasks.md parser
### `/api/modules?module=memory` → use MEMORY.md parser  
### `/api/modules?module=team` → use agent activity parser
### `/api/modules?module=office` → use system health parser
### `/api/modules?module=docs` → use docs index parser
### `/api/modules?module=projects` → derive from GOALS.md parser
### `/api/job-radar` → use pipeline.md parser
### `/api/content-factory` → use LinkedIn content parser
### `/api/cron-jobs` → KEEP existing (already live)
### `/api/system` → add system health endpoint

### NEW: `/api/sync-status`
Returns: `{ lastSync, fileCount, cacheHits, cacheMisses }`

## Dashboard Page Updates (`app/dashboard/page.tsx`)
Replace hardcoded stat cards with:
- **Open Tasks:** count from active-tasks.md (🔴 + 🟡 sections)
- **Active Applications:** count from pipeline.md (non-closed)
- **Content Due:** count from content calendar (items in draft/review)
- **System Health:** from system health check

Add below stats:
- **My Tasks:** top 5 urgent from active-tasks.md
- **Job Pipeline:** top 4 from pipeline.md with stage badges
- **Goal Progress:** from GOALS.md with progress bars

## Component Updates

### task-board.tsx
- Fetch from updated `/api/modules?module=tasks`
- Kanban columns: Urgent | In Progress | Recurring | Completed
- Each card: title, assignee badge, priority color, due date

### job-radar.tsx  
- Fetch from updated `/api/job-radar`
- Show real pipeline entries sorted by stage
- Stage badges with colors: Applied=blue, Interview=amber, Offer=green, Closed=gray

### module-panels.tsx
- MemoryPanels: show real decisions and open threads from MEMORY.md
- TeamPanel: show real agent status
- OfficePanel: show real system metrics
- DocsPanel: show real workspace docs index
- ProjectsPanels: show real GOALS.md objectives

### linkedin-factory.tsx
- Fetch from updated `/api/content-factory`  
- Show real content items from drafts/ and content calendar

## Files to Delete/Replace
- `lib/parity.ts` — seed data, delete
- `lib/module-store.ts` — replace entirely with sync-based reads
- `data/module-snapshot.json` — no longer needed
- `data/ops-snapshot.json` — keep only for cron cache, remove hardcoded leads/content

## Constraints
- **Read-only** — never write to workspace memory files
- **Cairo timezone** throughout (Africa/Cairo)
- **No breaking changes** to route structure — all existing URLs must work
- **Keep existing cron monitoring** — it works, don't touch it
- **All times displayed in Cairo timezone**
- **Error handling:** if a file doesn't exist or can't parse, show "No data" gracefully, never crash

## Testing
After implementation:
1. `npm run lint` must pass
2. `npm run build` must pass  
3. Every API endpoint must return real data
4. Dashboard must show accurate counts
5. No hardcoded fake data anywhere (except as graceful fallback if file missing)
