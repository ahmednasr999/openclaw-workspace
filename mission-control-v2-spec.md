# Mission Control v2, Phase 1 Product Specification

## 1) Purpose
Build Mission Control v2 as a clean rebuild to improve execution visibility, handoff quality, and daily operating rhythm for operators and team leads.

## 2) Phase 1 Scope
Phase 1 delivers a production-ready MVP with these modules:
1. Task Board
2. Live Activity
3. Weekly Stats
4. Calendar and Cron
5. Projects
6. Memories
7. Docs
8. Team
9. Handoff Quality Gate

Out of scope for Phase 1:
- Advanced forecasting and AI auto-planning
- Multi-tenant white-labeling
- External marketplace integrations beyond approved connectors

## 3) Hard Delivery Policies
### 3.1 Codex-only execution policy
All implementation work for Phase 1 must be executed by Codex agents only. Planning, coding, tests, migrations, and refactors must stay within Codex execution.

### 3.2 Scratch rebuild policy
Phase 1 is a full rebuild:
- New frontend codebase from scratch
- New backend codebase from scratch
- New database schema from scratch
- No direct carry-over of legacy code paths

Legacy system may be used only as behavioral reference for parity checks.

## 4) Product Outcomes
- Reduce task drift by making board state and ownership explicit
- Provide real-time execution visibility through live feed
- Enforce handoff quality before work can be marked done
- Consolidate planning, documents, memory, and team collaboration in one dashboard

## 5) Functional Specification by Module
### 5.1 Task Board
- Kanban-first board with status columns
- Drag and drop task movement
- Task fields: title, owner, priority, due date, project, tags, checklist, dependencies
- WIP indicators per column
- Quick actions: assign, comment, block, complete

### 5.2 Live Activity
- Right-side live feed showing task events, comments, handoffs, approvals, and cron-triggered events
- Event filtering by module, user, project, and time
- Event detail drawer with linked entities

### 5.3 Weekly Stats
- Weekly throughput, completion rate, spillover, blocked time, handoff pass rate
- Team and project breakdowns
- Week-over-week comparison cards

### 5.4 Calendar and Cron
- Calendar view for deadlines, milestones, and scheduled automations
- Cron rule management with owner, cadence, next run, last result
- Cron execution logs and failure alerts

### 5.5 Projects
- Project registry with status, owner, goals, milestones, health, and risk level
- Project to task and project to docs linking
- Project summary panel on dashboard

### 5.6 Memories
- Structured operational memory entries with topic, date, source, and confidence level
- Pin critical decisions and lessons learned
- Memory linked to tasks, projects, and handoffs

### 5.7 Docs
- Rich text docs with version history
- Inline linking to tasks, projects, and memories
- Document status: draft, review, approved

### 5.8 Team
- Team directory with roles, ownership domains, and availability
- Workload visibility by active tasks and overdue load
- Permissions by role

### 5.9 Handoff Quality Gate
- Mandatory pre-close gate for selected task types
- Checklist validation before status can move to Done
- Reviewer assignment and approval log
- Rejection reason capture and rework loop

## 6) UI Parity Contract
Reference design target: kanban-first dark dashboard with right live feed.

Phase 1 parity contract:
1. Primary layout is dark theme dashboard
2. Task Board is the dominant center pane
3. Live Activity is persistent on the right side
4. Header includes global filters and quick create
5. Key stats visible above or adjacent to board without breaking board-first hierarchy
6. Interaction speed and visual hierarchy must match the reference feel

Allowed variance:
- Color tokens and spacing may be modernized
- Component library can differ if UX behavior remains equivalent or better

Not allowed:
- Converting to list-first home screen
- Removing persistent right live feed
- Hiding core board actions behind deep navigation

## 7) Transcript-Advice Compliance Checklist
Each advice item from stakeholder transcript must be explicitly mapped to a product feature and test.

| Advice ID | Transcript Advice | Feature Mapping | Validation Method |
|---|---|---|---|
| A1 | Keep execution board-first | Task Board + UI parity contract items 1 to 3 | Home screen layout audit |
| A2 | Keep a real-time pulse of work | Live Activity module | Event stream latency and completeness test |
| A3 | Track weekly performance, not just totals | Weekly Stats module | Week-over-week report verification |
| A4 | Connect schedule and automation to execution | Calendar and Cron module | Calendar to cron linkage test |
| A5 | Keep project context visible | Projects module + board project links | Cross-navigation test |
| A6 | Preserve institutional memory | Memories module | Memory create-link-retrieve test |
| A7 | Keep docs operational, not isolated | Docs module with entity links | Linked doc workflow test |
| A8 | Make ownership transparent | Team module + task owner fields | Ownership visibility test |
| A9 | Enforce quality at handoff | Handoff Quality Gate module | Gate pass and reject workflow test |

Release condition: no advice item may be marked complete without passing its mapped validation.

## 8) Acceptance Criteria
### 8.1 Core acceptance criteria
- All 9 modules are delivered and accessible from main navigation
- Dashboard opens to kanban-first dark layout with persistent right live feed
- Task lifecycle supports create, assign, move, block, handoff, close
- Handoff Quality Gate blocks Done transition when required fields are missing
- Weekly stats update from live task and handoff data
- Cron schedules execute and write observable run logs

### 8.2 Data acceptance criteria
- New schema supports all required entities and relationships
- Migration and seed scripts create a usable Phase 1 environment
- Audit logs capture key state transitions

### 8.3 Quality acceptance criteria
- Critical workflows covered by automated tests
- Zero P1 defects at release readiness sign-off
- UAT sign-off completed by product owner and operations lead

## 9) Non-Functional Requirements
- Availability target: 99.5 percent monthly for Phase 1
- P95 page load under 2.5 seconds on dashboard
- P95 API response under 400 ms for common reads
- Role-based access control for all sensitive actions
- Immutable audit trail for task status changes and handoff approvals
- Encrypted data in transit and at rest
- Structured logging with trace IDs
- Daily backup with restore drill evidence

## 10) Risk Register
| Risk | Impact | Likelihood | Mitigation | Owner |
|---|---|---|---|---|
| Scope expansion in Phase 1 | High | Medium | Freeze scope by module definition and change control | Product |
| UI parity drift from reference | Medium | Medium | Enforce UI parity contract in design and UAT | Design Lead |
| Data model misses edge cases | High | Medium | Early schema reviews and scenario-based testing | Backend Lead |
| Cron reliability issues | High | Medium | Idempotent jobs, retries, alerting, runbook | Platform Lead |
| Gate adoption resistance | Medium | Medium | Start with critical task types, coach teams, measure pass rate | Ops Lead |
| Performance degradation with live feed | Medium | Medium | Event batching, pagination, performance budgets | Frontend Lead |

## 11) Phased Milestones
### M1, Foundation and Architecture
- Finalize domain model and API contracts
- Set up frontend and backend scaffolds
- Establish CI, test harness, observability baseline

### M2, Core Execution Surface
- Deliver Task Board and Live Activity end to end
- Implement Task, Event, User, Project core entities
- Initial UI parity checkpoint

### M3, Control and Insight Layer
- Deliver Weekly Stats and Calendar and Cron
- Add metrics pipelines and cron management APIs
- Performance checkpoint

### M4, Context and Collaboration
- Deliver Projects, Memories, Docs, Team
- Entity linking and permissions completion

### M5, Quality Enforcement and Release Readiness
- Deliver Handoff Quality Gate
- Complete transcript-advice compliance checks
- UAT, hardening, release go-no-go

## 12) Definition of Done
Phase 1 is done when all conditions below are true:
1. All in-scope modules are shipped and usable in production environment
2. UI parity contract is met and signed off
3. Transcript-advice checklist is fully validated and marked passed
4. Acceptance criteria and non-functional targets are met
5. Risk mitigations for high risks are implemented and verified
6. Documentation, runbooks, and handoff materials are complete
7. Product owner issues formal release approval

## 13) Executive Go/No-Go Decision Inputs
- UAT sign-off report
- Performance and availability test report
- Security and audit trail verification
- Handoff Quality Gate pass-rate baseline from pilot usage
- Open defect list with severity breakdown and closure plan
