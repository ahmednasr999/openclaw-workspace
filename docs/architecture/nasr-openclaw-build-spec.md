# NASR / OpenClaw Build Spec

Last updated: 2026-04-21
Owner: NASR
Status: implementation-ready
Purpose: convert the strategic roadmap into an execution package with concrete source targets, data shape changes, tests, and rollout order.

## Outcome we want

Ahmed should be able to answer four questions fast:
- what is running right now
- what happened in this run tree
- what external actions actually completed
- what is blocked and why

The implementation package below is scoped to produce that outcome with minimal architectural risk.

## Build order

### Commit 1
Trace viewer on top of the existing run-trace system

### Commit 2
Receipt schema and persistence for proof-sensitive actions

### Commit 3
Task contract extensions: blocked reason, proof required, proof received

### Commit 4
Worker-vs-front-facing execution policy for cron and bounded automation

### Commit 5
Failure classification for task and cron surfaces

Do not skip the order. Trace and receipts should exist before operator-board work.

## Commit 1 - Trace viewer

### Goal
Expose the existing run-trace data through the current task command surface and/or a trace-specific command with compact tree output.

### Existing usable foundations
- `/root/openclaw/src/tasks/task-executor.ts`
  - already emits `task_started`, `task_progress`, `task_succeeded`, `task_failed`
  - already derives `parentRunId`
- `/root/openclaw/src/agents/run-trace-reader.ts`
  - already reads trace JSONL
  - already resolves run tree from parent/child run ids
- `/root/openclaw/src/agents/run-trace-render.ts`
  - already renders timeline and grouped tree output
- `/root/openclaw/src/auto-reply/reply/commands-tasks.ts`
  - current `/tasks` surface exists and already summarizes active work

### Required implementation

#### 1. Add trace-aware command path
Preferred path:
- extend `/tasks` to support subcommands:
  - `/tasks` -> current summary behavior
  - `/tasks trace <runId>` -> compact grouped run tree
  - `/tasks trace <runId> verbose` -> expanded event stream

Alternative acceptable path:
- add a separate `/trace <runId>` command

Recommendation: keep it under `/tasks` first to avoid command sprawl.

#### 2. Resolve run id from visible tasks when possible
Allow:
- explicit run id
- optional future enhancement: `/tasks trace latest`

Initial version can require explicit run id if that lands faster.

#### 3. Show grouped tree by default
Use grouped output from `renderGroupedRunTraceTimeline`.

Default behavior:
- collapse long progress runs
- show run headline with runtime and session
- show child runs indented under parent

Verbose behavior:
- pass `verboseEvents: true`

### Source files to touch
- `/root/openclaw/src/auto-reply/reply/commands-tasks.ts`
- `/root/openclaw/src/auto-reply/reply/commands-tasks.test.ts`
- possibly helper extraction if command parsing gets noisy

### Tests required
Add tests for:
- `/tasks trace <runId>` returns grouped timeline
- verbose flag expands collapsed progress entries
- missing run id returns clear usage
- unknown run id returns `(no trace events)` or a clearer not-found message
- unauthorized sender remains blocked

### Acceptance criteria
- trace output works against real emitted task traces
- grouped tree renders parent and child runs correctly
- no regression in plain `/tasks`

## Commit 2 - Receipts / proof of work

### Goal
Every proof-sensitive external action should generate a structured receipt.

### First workflows to support
1. LinkedIn publishing
2. gateway/config changes
3. cron jobs that send messages or mutate external systems

### Receipt shape
Create a canonical type first.

#### Proposed type
```ts
export type TaskReceipt = {
  receiptId: string;
  receiptType: string;
  ownerKey?: string;
  sessionKey?: string;
  agentId?: string;
  runId?: string;
  taskId?: string;
  targetSystem: string;
  targetRef?: string;
  artifactPaths?: string[];
  verificationStatus: "verified" | "unverified" | "failed";
  verificationEvidence?: string[];
  createdAt: number;
  metadata?: Record<string, unknown>;
};
```

### Storage recommendation
Do not overbuild storage first.

Phase 1 storage options, in order of preference:
1. persist alongside task records in the task registry store
2. or persist as JSONL in a dedicated receipts log if registry changes are too invasive for first landing

Recommendation:
- first landing: JSONL receipt log, then attach references from task records
- second landing: registry-native receipt summary fields

### Minimum task linkage
Add lightweight receipt summary fields to `TaskRecord` only after receipt writing works:
- `proofRequired?: boolean`
- `proofStatus?: "missing" | "verified" | "failed"`
- `latestReceiptId?: string`

### Source files likely touched
- `/root/openclaw/src/tasks/task-registry.types.ts`
- `/root/openclaw/src/tasks/task-registry.ts`
- `/root/openclaw/src/tasks/task-domain-views.ts`
- new helper module, recommended:
  - `/root/openclaw/src/tasks/task-receipts.ts`
  - `/root/openclaw/src/tasks/task-receipts.store.ts`
  - `/root/openclaw/src/tasks/task-receipts.test.ts`

### Delivery policy changes
Update task-facing summaries so proof-sensitive completions can reflect verification state.

Example:
- before: `Background task done: LinkedIn post published.`
- after verified: `Background task done: LinkedIn post published. Proof verified.`
- after unverified: `Background task done: LinkedIn post published. Proof not yet verified.`

### Acceptance criteria
- at least one real workflow can emit a receipt object
- receipt is queryable from logs or task detail
- user-facing success copy stops implying proof when proof is missing

## Commit 3 - Task contract extensions

### Goal
Extend task metadata so blocked state and proof state are first-class, not prose-only.

### Additions to TaskRecord
Recommended additions:
```ts
blockedReason?: string;
blockedOwner?: string;
proofRequired?: boolean;
proofStatus?: "missing" | "verified" | "failed";
latestReceiptId?: string;
expectedOutput?: string;
verificationRule?: string;
```

### Why these first
These fields support:
- blocked visibility
- proof visibility
- operator readability
without forcing full workflow-engine redesign

### Source files to touch
- `/root/openclaw/src/tasks/task-registry.types.ts`
- `/root/openclaw/src/tasks/task-registry.ts`
- `/root/openclaw/src/tasks/task-status.ts`
- `/root/openclaw/src/tasks/task-domain-views.ts`
- `/root/openclaw/src/tasks/task-registry.summary.ts` if proof/blocked counts are added

### UI/text behavior
Update `formatTaskStatusDetail` precedence roughly to:
1. blocked reason when task is blocked outcome
2. error when failed
3. proof-needed/proof-missing note for completed proof-sensitive tasks
4. terminal/progress summary fallback

### Acceptance criteria
- blocked work has explicit machine-readable reason
- proof-sensitive work surfaces proof state clearly
- existing tasks without the new fields continue to render cleanly

## Commit 4 - Worker vs front-facing execution policy

### Goal
Create a stable operating contract for when work should happen in worker-style runs versus front-facing sessions.

### Policy

#### Front-facing lane
Use when:
- Ahmed is interacting directly
- approval is needed
- synthesis or judgment is the primary value
- the run needs personality continuity

#### Worker lane
Use when:
- task is bounded and tool-heavy
- cron is driving the run
- proof or export is the main deliverable
- intermediate tool chatter is not useful to Ahmed

### Runtime implications
This is mostly policy and routing, not a new runtime.

Practical first landing:
- document the rule
- bias cron and automation toward worker/subagent style where safe
- keep front-facing session responsible for summary and decision-making

### Source files likely touched
- docs first
- then selected cron/task dispatch points after policy is proven

Potential code surfaces later:
- cron payload construction
- task creation helpers
- background task notify policy defaults

### Acceptance criteria
- at least one production automation path follows worker-style execution by default
- user receives summary/result, not noisy tool chatter

## Commit 5 - Failure classification

### Goal
Turn generic failure blobs into stable classes.

### Initial failure classes
- `agent_response_failure`
- `transport_failure`
- `tool_execution_failure`
- `verification_failure`
- `timeout`
- `session_resume_failure`
- `delivery_failure`

### First implementation
Do not re-architect errors globally.

Add a classifier helper that maps known strings/patterns into classes for task/cron display.

Recommended module:
- `/root/openclaw/src/tasks/task-failure-classifier.ts`
- `/root/openclaw/src/tasks/task-failure-classifier.test.ts`

### Surfaces to update
- task status detail
- cron run summaries
- future operator board

### Acceptance criteria
- common recurring errors are grouped into stable operator-facing classes
- raw error text remains accessible for debugging

## Recommended file-by-file plan

### File: `/root/openclaw/src/auto-reply/reply/commands-tasks.ts`
Add:
- `/tasks trace <runId> [verbose]`
- usage/help branch
- helper to call `renderGroupedRunTraceTimelineForRunId`

### File: `/root/openclaw/src/auto-reply/reply/commands-tasks.test.ts`
Add:
- trace command success tests
- verbose trace test
- missing arg usage test
- no-regression tests for plain `/tasks`

### File: `/root/openclaw/src/tasks/task-registry.types.ts`
Add:
- receipt/proof fields
- blocked metadata fields
- optional expected-output and verification-rule fields
- optional receipt type definitions if kept here

### File: `/root/openclaw/src/tasks/task-registry.ts`
Add:
- persistence for new optional fields
- update paths for proof/blocked metadata
- helper for attaching latest receipt id

### File: `/root/openclaw/src/tasks/task-status.ts`
Add:
- proof-aware detail rendering
- blocked-reason precedence
- keep current sanitization behavior intact

### File: `/root/openclaw/src/tasks/task-domain-views.ts`
Add:
- new task fields to API/domain views

### New file: `/root/openclaw/src/tasks/task-receipts.ts`
Add:
- receipt creation helper
- minimal validation

### New file: `/root/openclaw/src/tasks/task-receipts.store.ts`
Add:
- simple append/read storage for receipts

### New file: `/root/openclaw/src/tasks/task-receipts.test.ts`
Add:
- write/read roundtrip
- invalid receipt rejection
- task-link metadata behavior if included

### New file: `/root/openclaw/src/tasks/task-failure-classifier.ts`
Add:
- pattern mapping from raw failures to classes

### New file: `/root/openclaw/src/tasks/task-failure-classifier.test.ts`
Add:
- fixtures for known recurring failure strings

## Suggested rollout sequence

### Day 1
- land `/tasks trace`
- tests green

### Day 2
- land receipt store and type
- no workflow integration yet

### Day 3
- integrate receipts into one workflow, ideally LinkedIn publish path or another already-proven proof-sensitive lane

### Day 4
- extend task fields for proof/blocked metadata
- update task rendering

### Day 5
- add failure classification
- polish output text

## Definition of done

This package is done when:
- Ahmed can inspect run trees from chat
- proof-sensitive tasks can show whether completion is verified
- blocked tasks have explicit machine-readable reasons
- recurring failures collapse into stable categories instead of noisy blobs
- none of this breaks the current `/tasks` happy path

## What not to build yet

Not yet:
- big visual operator board
- runtime fleet UI
- broad workflow-engine rewrite
- generalized issue/work-control-plane clone
- many new agent identities

These become much easier after trace + receipts + task contract are real.
