---
description: "Mission Control technical specification: API endpoints, data sources, UI components"
type: reference
topics: [system-ops]
updated: 2026-03-14
---

# Mission Control — Full Build Spec

*Received: 2026-02-21*
*Model for build: Sonnet 4.6*
*Status: Sync engine built ✅ — UI phases pending*

---

## Project Context

Rebuild Mission Control (~/.openclaw/workspace/mission-control/) as a read-only visual dashboard fed by OpenClaw memory files.

Existing stack: Next.js 14, SQLite, React, Tailwind, Lucide React.

---

## Design Language

- Background: #080C16
- Surfaces: #0D1220
- Primary accent: #4F8EF7 (blue) → #7C3AED (violet) gradient
- Typography: Syne (headings/numbers), DM Sans (body), DM Mono (timestamps/data)
- 8px grid, 10px card radius, subtle border #1E2D45
- No white backgrounds anywhere

---

## Sync Architecture

- Node.js file watcher on ~/.openclaw/workspace/memory/
- 30-second debounce before sync fires
- Sync converts markdown files → JSON → SQLite
- Every 5 minutes cron as fallback
- Manual sync button in UI
- Sync status indicator: pulsing dot top right (green=synced, amber=syncing, red=error)
- All times in Cairo timezone (Africa/Cairo)

### Sync Engine Status — BUILT ✅

Files at ~/.openclaw/workspace/mission-control/lib/sync/:
- schema.sql — 6 new tables
- parser.ts — markdown parsers for all memory files
- writer.ts — SQLite upsert writer
- watcher.ts — chokidar file watcher with 30s debounce
- index.ts — sync orchestrator
- test-write.js — test script

---

## Navigation Structure

Sidebar (220px) + gear icon top right for Settings

| Section | Icon | Route |
|---------|------|-------|
| Command Center | grid/HR | / |
| HR | briefcase/hr | /hr |
| Marketing | trending-up/marketing | /marketing |
| OPS | layers/ops | /ops |
| Intelligence | search/intelligence | /intelligence |
| Team | users/team | /team |
| Lab | flask/lab | /lab |
| Settings | gear icon only | /settings |

---

## Page Specs

### 1. Command Center (/)
- Live Cairo time clock (top right topbar)
- Interview/deadline alert banner (auto-shows if deadline within 48hrs from GOALS.md)
- 4 stat cards: Active Applications, Avg ATS Score, Content Due, Open Tasks
- 3-column grid: My Tasks (Ahmed-assigned, urgent first) | Job Pipeline snapshot (top 4) | Agent Activity (last action per agent)
- Bottom 2-column: Content Pipeline kanban preview | Q1 Goals progress bars
- Data: active-tasks.md, GOALS.md, job-pipeline.md, content-pipeline.md, memory/YYYY-MM-DD.md

### 2. HR (/hr)
- Kanban: Identified → Applied → Interview → Offer → Closed
- Each card: company logo (auto-fetch favicon), role title, ATS score badge, salary vs target, next action
- CV History table below kanban: company, role, ATS score, date, outcome
- Archive: closed applications >30 days auto-archive, "View Archive" button
- Data: job-pipeline.md, memory/cv-history.md, memory/cv-output-*.md

### 3. Marketing (/marketing)
- Full kanban: Ideas → Draft → Review → Scheduled → Published
- Each card: title, pillar tag, word count, assigned agent, date
- Published cards show performance notes
- Archive: published posts >30 days
- Data: memory/content-pipeline.md, memory/linkedin-drafts/

### 4. OPS (/ops)
- Kanban: To Do → In Progress → Blocked → Done
- Each task card: title, priority flag (🔴🟡🟢), assigned to, deadline, category
- Filter bar: by assignee, by priority, by category
- Done column: auto-archives after 7 days
- Data: memory/active-tasks.md

### 5. Intelligence (/intelligence)
- Global search (Ctrl+K): searches across ALL 42+ memory files
- Results grouped by source file with excerpt and relevance
- Memory Highlights section: key decisions from MEMORY.md
- Lessons Learned: positive (green) and negative (red)
- Goals dashboard: full Q1 objectives with progress
- Data: all memory/*.md files, MEMORY.md, GOALS.md

### 6. Team (/team)
- Agent hierarchy diagram: NASR → 4 sub-agents
- Click agent card → expands chat log below
- Chat log: last 20 interactions, monospace timestamps, "Load More"
- Sub-agent run history table: task, model, duration, output file, status
- Data: ~/.openclaw/agents/*/sessions/, runs.json

### 7. Lab (/lab)
- Two-column layout
- Left: Ideas & Recommendations (NASR proactive suggestions + memory)
- Right split: What's Working (green) / What Went Wrong (red)
- Lessons Learned condensed log (searchable)
- Tools Radar: Adopt / Trial / Reject
- Data: memory/lessons-learned.md, memory/second_brain.md

### 8. Settings (/settings — gear icon)
- Current model routing rules (read-only)
- GitHub backup status + last pushed timestamp
- Manual sync trigger button
- Memory index trigger button
- File count and size stats

---

## Global Components

- **Search (Ctrl+K):** full-width modal, instant results, keyboard navigable, grouped by section
- **Sync indicator:** pulsing dot top right, tooltip shows last sync time
- **Alert banner:** auto-surfaces from GOALS.md deadlines within 48hrs
- **Archive:** consistent across HR, Marketing, OPS — hidden but recoverable

---

## Build Order

1. ✅ Sync engine — file watcher + markdown parser + SQLite writer
2. ⏳ Layout shell — sidebar, topbar, routing
3. ⏳ Command Center — most complex, proves data pipeline
4. ⏳ HR + OPS — kanban components (reusable)
5. ⏳ Marketing, Intelligence, Team, Lab, Settings

---

## Constraints

- **Read-only Phase 1** — no write operations to OpenClaw files
- Cairo timezone throughout (Africa/Cairo)
- Do NOT modify any OpenClaw memory files
- Do NOT touch MEMORY.md, GOALS.md, active-tasks.md directly — read only via sync layer
