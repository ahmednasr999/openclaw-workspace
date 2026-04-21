# OpenClaw Tier A build brief

Last updated: 2026-04-15
Owner: NASR
Audience: Codex / Claude Code / implementation agent
Status: Ready for handoff

## Objective

Build the first operator-ergonomics layer for OpenClaw without changing its core identity.

This phase should make the system easier to inspect and operate at a glance.

## Scope

Deliver exactly 4 things:

1. runtime registry view
2. agent status board
3. shared progress/blocker schema
4. cleaner assignment UX

## Non-goals

Do not build:
- an issue-only task board
- a Multica-style product clone
- a team permissions system
- a scheduler rewrite
- deep model-router changes
- a new persistent orchestration framework

## Product constraints

Preserve OpenClaw's identity:
- assistant-first, not issue-first
- cross-channel, not dev-only
- memory and cron remain first-class
- device/node ecosystem remains intact
- operators must be able to drill from summary to real session/task evidence

## Existing code touchpoints

Use these as the main insertion points.

### Task and status surfaces
- `/root/openclaw/src/tasks/task-registry.summary.ts`
- `/root/openclaw/src/tasks/task-status.ts`
- `/root/openclaw/src/status/status-text.ts`

### Session and gateway surfaces
- `/root/openclaw/src/gateway/server-methods/sessions.ts`
- `/root/openclaw/src/gateway/server-methods/cron.ts`
- `/root/openclaw/src/gateway/server-methods/agent.ts`
- `/root/openclaw/src/gateway/server-methods/agents.ts`
- `/root/openclaw/src/gateway/server-methods/usage.ts`

### Existing runtime/task abstractions
- `/root/openclaw/src/tasks/`
- `/root/openclaw/src/sessions/`
- `/root/openclaw/src/cron/`
- `/root/openclaw/src/agents/`
- `/root/openclaw/src/acp/runtime/`

### Web or UI-adjacent surfaces to inspect before coding
- `/root/openclaw/src/channels/web/`
- `/root/openclaw/src/web/`
- `/root/openclaw/src/gateway/server/`
- `/root/openclaw/src/gateway/server-methods/`

## Deliverable 1 - Runtime registry view

### Goal
Let Ahmed answer, in under 10 seconds:
- what runtimes exist?
- are they online?
- what are they running?
- what capabilities do they expose?
- when were they last seen?

### Functional requirements
Create a new summary surface, CLI or gateway-backed UI or both, that shows per runtime:
- runtime id
- host or device label
- runtime type or execution lane
- online / stale / offline state
- last heartbeat or last activity timestamp
- active task count
- queued task count if derivable
- supported runtime class or capabilities, for example:
  - acp
  - subagent
  - cli
  - cron
  - browser-capable
  - node/device-capable
  - elevated-capable when safely knowable

### Implementation note
Do not invent a separate runtime database unless necessary. First try to derive this from existing task/session/runtime state.

### Suggested output shape
```ts
{
  id: string,
  label: string,
  status: "online" | "stale" | "offline",
  lastSeenAt?: number,
  activeTasks: number,
  queuedTasks: number,
  runtimes: string[],
  capabilities: string[],
  currentSummary?: string,
}
```

### Acceptance criteria
- operator can list all visible runtimes
- stale runtimes are visually distinct from active ones
- each runtime shows at least one useful workload summary line
- summary links through to underlying sessions/tasks where possible

## Deliverable 2 - Agent status board

### Goal
Show every agent in one place with a compact status card.

### Per-agent card requirements
- agent id and label
- current effective model if available
- current status:
  - idle
  - queued
  - running
  - blocked
  - waiting_user
  - failed_recently
- active task count
- most relevant task title
- most relevant detail line
- last update timestamp
- click-through or command path to session/task detail

### Data source hints
Reuse existing task snapshot logic where possible:
- `buildTaskStatusSnapshot(...)`
- `formatTaskStatusTitle(...)`
- `formatTaskStatusDetail(...)`

These already provide a decent base for focus-task summaries.

### Acceptance criteria
- all main agents show on one screen
- agents with no current work clearly show idle
- agents with failures or blockers stand out
- agent status is derived, not hand-maintained in a second store

## Deliverable 3 - Shared progress and blocker schema

### Goal
Standardize task state across agents so status surfaces stop depending on prose luck.

### Required normalized states
At minimum support:
- planning
- queued
- running
- waiting_external
- waiting_user
- blocked
- completed
- failed

### Required structured fields
For each active or recently finished task/session, support these when available:
- `status`
- `progressSummary`
- `blockerType`
- `blockerSummary`
- `needsUserAction`
- `startedAt`
- `lastEventAt`
- `endedAt`
- `runtime`
- `ownerAgentId`
- `sessionKey`

### Blocker types
Use a small enum first:
- approval
- auth
- missing_context
- external_service
- tool_failure
- waiting_time
- unknown

### Implementation approach
Do not rewrite every agent first.

Instead:
1. define a normalization layer over existing task/session metadata
2. map current known states into the new schema
3. render from normalized state
4. only then backfill richer emission where needed

### Acceptance criteria
- status board does not rely only on arbitrary free-text status strings
- blockers can be detected and surfaced consistently
- user-facing summaries can say *why* something is stuck

## Deliverable 4 - Cleaner assignment UX

### Goal
Make deterministic delegation feel native.

### Supported user actions
At minimum support a clean operator path for:
- assign this to agent X
- send this session/task to agent X
- optionally specify runtime or model override when relevant

### Requirements
- explicit confirmation of target agent
- if runtime/model override is used, display it clearly
- assignment should create a visible task/session change on the agent board
- assignment must not silently override Ahmed's explicit model choices

### Technical hint
Prefer building on top of existing session/task routing rather than inventing a second delegation system.

## Suggested implementation order

### Step 1
Create a new internal summary builder module for runtime and agent board data.

Suggested new file(s):
- `src/tasks/runtime-status.ts`
- `src/tasks/agent-status-board.ts`
- or equivalent under `src/status/`

### Step 2
Add gateway server methods to expose these summaries.

Candidate method names:
- `fleet.status`
- `agents.board`
- `runtimes.list`

Do not overfit the names, but keep them narrow and inspectable.

### Step 3
Add a CLI surface for quick operator inspection.

Candidate commands:
- `openclaw fleet status`
- `openclaw agents board`

### Step 4
Add UI surface only after the summary payload is stable.

The data contract should exist before UI polish.

## Proposed data contract

### Runtime registry response
```ts
{
  generatedAt: number,
  runtimes: Array<{
    id: string,
    label: string,
    status: "online" | "stale" | "offline",
    lastSeenAt?: number,
    activeTasks: number,
    queuedTasks: number,
    capabilities: string[],
    activeAgents: string[],
    currentSummary?: string,
  }>
}
```

### Agent board response
```ts
{
  generatedAt: number,
  agents: Array<{
    agentId: string,
    label: string,
    model?: string,
    status: "idle" | "queued" | "running" | "blocked" | "waiting_user" | "failed_recently",
    activeTasks: number,
    totalVisibleTasks: number,
    focusTaskTitle?: string,
    focusTaskDetail?: string,
    runtime?: string,
    sessionKey?: string,
    updatedAt?: number,
  }>
}
```

## UX rules

- one glance must reveal what needs attention
- active work outranks historical work
- blockers outrank generic running state
- failures should stay visible for a short recent window, not vanish instantly
- every summary item should have a drill-down path
- do not flood the surface with logs or token stats first

## Testing requirements

### Unit tests
Add or extend tests around:
- task snapshot aggregation
- runtime summary aggregation
- blocker normalization
- status priority ordering

### Integration tests
Add gateway method tests for:
- empty state
- mixed runtime state
- queued plus running tasks
- stale runtime handling if implemented

### Manual verification checklist
Confirm these questions can be answered quickly:
- what is running right now?
- where is it running?
- which agent is blocked?
- what is waiting for Ahmed?
- what failed recently?

## Definition of done

This Tier A brief is complete when Ahmed can inspect OpenClaw and answer the following in under 10 seconds, without log-diving:
- what is running?
- where is it running?
- which agent owns it?
- what is blocked?
- what needs his decision?

## Important anti-patterns

Do not:
- create a second source of truth for task state
- build UI first and invent data shape later
- make everything issue-centric
- hide ambiguity by guessing runtime or blocker state
- silently coerce explicit model choices

## Recommended next handoff

After this brief, the implementation agent should produce:
1. a short design note with exact files to add or modify
2. the response schema
3. tests before UI polish
4. a minimal working CLI or gateway surface before dashboard work
