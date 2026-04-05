---
description: "Mission Control Phase 2 design document: new features, UX changes"
type: reference
topics: [system-ops]
updated: 2026-03-14
---

# Mission Control Phase 2 — Design Spec

**ID:** MC-P2-DESIGN-20260222  
**Created:** 2026-02-22  
**Status:** Design Locked ✅ — Sonnet 4.6 Review Applied  
**Ready for Build:** After Delphi interview (Feb 24+)

---

## 1. Data Ownership — Hybrid Approach

**Canonical Source:** Database (SQLite)

**Data Flow:**
```
Local Markdown → [File Watcher, 15s debounce] → Database
Telegram Message → [Bot Parser] → Database
Database → [Reverse Sync] → Local Markdown
Mission Control → [Read] → Database
```

**Implementation:**
- File watcher: watches GOALS.md, active-tasks.md, memory/ for changes
- Telegram bot command: `/update-task` parses structured fields, writes to DB
- Reverse sync: after DB updates from Telegram, sync back to markdown files
- Mission Control: all reads from database (no markdown fallback)

### Telegram Bot Parser Format (LOCKED)
Strict structured field format — no ambiguous markdown:
```
/update-task title:Finalize CV status:blocked blockedBy:Task#41 blockerPriority:high
```
Or multi-line:
```
/update-task
title: Finalize CV for Delphi
status: blocked
blockedBy: Task #41
blockerPriority: high
unblockedETA: 2026-02-23 06:00
blockerNotes: Need 5-7 STAR stories ready
```

### Reverse Sync — Collision Strategy (LOCKED)
**Last-write-wins** (simple, pragmatic for solo use):
- Markdown edits and Telegram updates are serialized via DB timestamp
- DB write always overwrites markdown (DB is canonical)
- If editing markdown locally at same time as Telegram update: last write wins
- Note: This is safe for solo user. Revisit if multi-user later.

### File Watcher + Compaction (LOCKED)
- Pause file watcher during OpenClaw session compaction
- Resume after compaction complete
- Add compaction hook in watcher.ts to coordinate

---

## 2. Command Center Redesign

**Always Visible (Never Collapse):**
1. Alert Banner — deadlines within 48hrs
2. "Today's Focus" stat — single metric: active urgent tasks count
3. My Tasks (Ahmed) — personal urgent items, max 5, today/overdue only

**Today's Focus Formula (LOCKED):**
```sql
Active Urgent = (
  status IN ['To Do', 'In Progress', 'Blocked']
  AND priority = 'High'
  AND dueDate <= TODAY + 7 days
)
```

**Collapsible Sections (Hidden by default):**
4. Job Pipeline — top 4 jobs, expand on click
5. Agent Activity — last actions per agent
6. Interview Pipeline (PRIMARY trend only) — see Metrics below

**Layout:**
```
Alert Banner (if any)
─────────────────────────────
Today: X urgent tasks
─────────────────────────────
My Tasks
• Task 1 — due in 32hrs
• Task 2 — due tomorrow
─────────────────────────────
[Expand ▼] Job Pipeline
[Expand ▼] Agent Activity
[Expand ▼] Interview Pipeline (trend)
```

---

## 3. Mobile Support

**Approach:** Full dashboard, responsive layout (MVP)

**Breakpoints:**
- Mobile (375px): Stack all columns vertically, hamburger sidebar
- Tablet (768px): 2-column layout
- Desktop (1200px+): 3-4 column layout

**Touch Targets:** Min 40px for buttons/taps

**Phase 2.2 (Future):**
- Swipe tabs for sections
- Bottom navigation
- Gesture shortcuts
- Mobile wireframe before Phase 2.2 build

---

## 4. Performance Metrics — Trends

### Command Center (Primary Only)
Show **Interview Pipeline Velocity** only on Command Center:
- Jobs applied this week vs last week
- Avg days per stage trend line

All other metrics → dedicated **Metrics page** (drill-down)

### Metrics Page (Full)
Track over 7d + 30d average:

**1. Interview Pipeline Velocity (PRIMARY)**
```sql
jobs_applied_this_week: 
  SELECT COUNT(*) FROM job_pipeline 
  WHERE status='applied' AND updatedAt >= DATE('now', '-7 days')

avg_stage_duration:
  SELECT AVG(julianday(updatedAt) - julianday(createdAt)) 
  FROM job_pipeline GROUP BY status
```

**2. Task Completion Rate**
```sql
tasks_completed_this_week:
  SELECT COUNT(*) FROM tasks 
  WHERE status='done' AND completedDate >= DATE('now', '-7 days')

burndown:
  SELECT COUNT(*) FROM tasks 
  WHERE status != 'done' AND dueDate <= DATE('now', '+7 days')
```

**3. Content Output**
```sql
posts_published_this_week:
  SELECT COUNT(*) FROM content_pipeline 
  WHERE stage='published' AND published_date >= DATE('now', '-7 days')
```

**4. Memory Health**
```sql
file_count_trend: 
  SELECT COUNT(*) FROM daily_notes GROUP BY DATE(updatedAt)
  -- Trend: growing too fast?
```

**5. Sub-Agent Productivity**
```sql
runs_per_agent_per_day:
  -- Parse from sessions.json subagent entries
  -- Group by agent + date
```

---

## 5. OPS Blocker Tracking — Rich Schema

**5 New Fields on Tasks:**

1. `blockedBy` — task ID or free-text (e.g., "Task #42" or "Waiting for TopMed approval")
2. `blockerOwner` — who owns removing the blocker?
3. `blockerPriority` — high/medium/low
4. `unblockedETA` — ISO date (when will blocker be removed?)
5. `blockerNotes` — free-text context

**Circular Dependency Validation (LOCKED):**
- API rejects any `blockedBy` that creates a cycle
- Query: traverse blockedBy chain, reject if task ID appears twice
- Return HTTP 400 with message: "Circular dependency detected"
- UI: Show warning badge if cycle is detected on read

**Display on OPS Kanban:**
- Tasks in "Blocked" column show 🔴 BLOCKER badge
- Hover/expand shows full 5-field blocker details
- Filter: "Show blocked tasks" + "Show blockers" (tasks blocking others)

**Example Task Card:**
```
Title: Finalize CV for Delphi
Status: Blocked | Priority: 🔴 High
Assigned: Ahmed | Due: 2026-02-23

🔴 BLOCKER
├─ Blocked By: Prepare STAR stories (#41)
├─ Owner: Ahmed
├─ Priority: HIGH
├─ Unblock ETA: 2026-02-23 06:00
└─ Notes: Need 5-7 stories ready for interview
```

---

## Build Phases

### Phase 2.1: Core Infrastructure
- Implement hybrid data sync:
  - File watcher (15s debounce + compaction hook)
  - Telegram bot parser (structured field format)
  - Reverse sync (DB → markdown, last-write-wins)
- Rebuild Command Center (alert + Today's Focus + My Tasks + collapsibles)
- Add Interview Pipeline trend (Command Center only)
- Add Metrics page (all 5 metrics with SQL queries above)

### Phase 2.2: Mobile + Blockers
- Responsive layout (mobile/tablet/desktop breakpoints)
- OPS blocker schema + circular dependency validation + UI
- Mobile wireframe before build starts
- Enhanced metrics charts

### Phase 2.3: Polish
- Swipe tabs, bottom nav (after Phase 2.2)
- Gesture shortcuts
- Performance optimization (Meilisearch if >500 files)

---

## Critical Items Cleared (from Sonnet 4.6 Review)

| Issue | Decision |
|-------|----------|
| Telegram bot format | Structured fields — strict format locked |
| Reverse sync collisions | Last-write-wins — DB always canonical |
| Metrics data sources | SQL queries defined per metric |
| Today's Focus formula | Locked: High priority + non-done + due ≤7 days |
| File watcher + compaction | Pause watcher during compaction via hook |
| Circular blocker deps | API validation + HTTP 400 on cycle detection |
| Mobile responsive | Phase 2.2 with wireframe before build |
| Trends display | Interview Pipeline on Command Center; all others → Metrics page |

---

## Notes

- Interview: Feb 23, 5:00 PM IST — full focus, no build
- Design session: Feb 22 (complete)
- Sonnet 4.6 review: Feb 22 (complete, all recommendations accepted)
- Build start: Feb 24+
- Model for build: Sonnet 4.6
- Reference: memory/mission-control-phase2-feedback.md
