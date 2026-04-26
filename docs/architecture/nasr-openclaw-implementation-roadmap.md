# NASR / OpenClaw Implementation Roadmap

Last updated: 2026-04-21
Owner: NASR
Purpose: turn the current strategy into a concrete implementation plan for a more legible, reliable, operator-grade assistant system without bloating the architecture.

## Executive summary

The right next move is not more agents.

It is better operating structure.

OpenClaw already has the core primitives Ahmed actually needs:
- sessions
- tasks
- cron
- skills
- memory/recall
- channels
- sub-agents and ACP lanes
- trace events already landing in runtime code

The gap is that these primitives are still too implicit.

So the roadmap should focus on six things, in this order:
1. tracing UX
2. receipts and proof of work
3. front-facing vs worker-agent split
4. task ownership contract
5. model-routing hardening
6. memory retrieval cleanup

## Design principles

### Preserve
- OpenClaw as the main runtime
- Telegram-native operations
- proactive assistant behavior
- memory-first workflows
- cron as a useful execution layer, not just reminders
- skills as the main reusable behavior unit

### Improve
- operator visibility
- proof and verification
- delegation clarity
- runtime trust
- worker isolation for repeated background jobs
- retrieval quality with less bootstrap bloat

### Avoid
- building a fancy control plane before the core evidence model exists
- adding more agents without clear boundaries
- replacing working primitives with a rewrite
- turning NASR into a task board with personality pasted on top

## Current reality

The foundations already exist:
- task registry has status and progress summaries
- run-trace events already exist in `/root/openclaw/src/tasks/task-executor.ts`
- parent run correlation already exists via derived `parentRunId`
- cron jobs already encode ownership, run history, last errors, and delivery status
- memory retrieval already exists via lossless-claw/QMD

So this is not a greenfield architecture problem.
It is a packaging, visibility, and execution-discipline problem.

## Phase 1 - Trust and visibility, 1 to 2 weeks

### 1. Trace viewer on top of existing run-trace events

#### Goal
Make run traces human-usable instead of code-only.

#### Build
- Add a first-class `tasks trace` or equivalent trace-focused output on top of existing trace storage.
- Show:
  - run id
  - parent run id
  - task/session owner
  - started / progress / success / failure events
  - compact summary per event
- Default to compact tree view.
- Allow optional verbose event expansion.

#### Why first
OpenClaw already writes the events. Surfacing them is the fastest path to real operator trust.

#### Success metric
Ahmed can answer:
- what ran
- where it ran
- who spawned it
- where it failed
within 15 seconds.

### 2. Receipt standard for external side effects

#### Goal
No important action should end at “tool succeeded.”

#### Receipt schema
Every side-effecting workflow should produce a receipt with:
- action type
- owner agent/session
- target system
- target identifier
- created artifact or URL
- verification result
- timestamp
- failure reason if unverified

#### Start with these flows
- LinkedIn posting
- Telegram outbound sends triggered by jobs
- file exports
- gateway/config changes
- issue creation/update

#### Why
This directly fixes a recurring weakness: completion gets claimed too early unless proof is explicit.

#### Success metric
For every external action, the system can show proof or explicitly show that proof is missing.

### 3. Task state vocabulary cleanup

#### Goal
Use one shared language across tasks and agents.

#### Standard states
- planning
- running
- waiting_external
- waiting_user
- blocked
- completed
- failed

#### Additions
- blocked reason
- blocked owner
- proof required
- proof received

#### Why
The raw task system already has useful status fields, but not a sufficiently legible operator contract.

## Phase 2 - Cleaner delegation, 2 to 4 weeks

### 4. Split front-facing agents from worker agents

#### Goal
Separate conversation identity from background execution.

#### Front-facing agents
Use for:
- Ahmed interaction
- strategic reasoning
- summarization back to user
- approval-sensitive actions

#### Worker agents
Use for:
- cron jobs
- bounded research runs
- export/render pipelines
- audits
- publishing preflight and verification
- repetitive tool-heavy jobs

#### Rules
- workers should have minimal personality overhead
- workers should return structured outcomes
- front-facing agents should synthesize and decide

#### Why
This reduces context bloat and makes failure modes easier to interpret.

### 5. Task ownership contract

#### Goal
Every meaningful task should have explicit ownership and completion conditions.

#### Contract fields
- requester
- owner
- runtime
- expected output
- verification rule
- handoff target
- blocked reason if incomplete

#### Implementation direction
- store with task/session metadata first
- surface in task status and run trace outputs
- require it for cron jobs that affect external systems

#### Why
This is the cleanest way to stop “something ran” from being confused with “the work is done.”

### 6. Cron job grading

#### Goal
Differentiate low-risk checks from high-risk work.

#### Classes
- monitor jobs: check and report only
- maintenance jobs: safe internal changes
- production jobs: publish, send, mutate, or sync external state

#### Policy
- production jobs require proof/receipt output
- production jobs should prefer worker lanes
- monitor jobs can stay light-context and silent when unchanged

#### Why
Not all cron jobs deserve the same execution contract.

## Phase 3 - Reliability and cost discipline, 3 to 6 weeks

### 7. Model-routing by task type

#### Goal
Make model choice explicit and tested.

#### Recommended routing policy
- GPT-5.4:
  - architecture
  - coding
  - agent coordination
  - judgment-heavy summaries
  - production-critical write paths
- cheaper/faster model lane:
  - classification
  - extraction
  - rote summarization
  - repetitive checks with bounded outputs
- fallback lane:
  - only for tested workflows with verified behavior

#### Why
Fallbacks should be operating policy, not wishful thinking.

### 8. Failure pattern audit for cron and followup runs

#### Goal
Turn recurring generic failures into categorized failure classes.

#### Focus areas
- agent could not generate a response
- request failed
- delivery failed
- verification failed
- tool-side success but agent-side completion failure

#### Build
- map recurring failure strings to stable classes
- attach remediation hint
- expose counts in cron/task views

#### Why
Right now too many failures collapse into generic noise.

## Phase 4 - Memory and operator ergonomics, 4 to 8 weeks

### 9. Memory retrieval cleanup

#### Goal
Reduce dependence on giant bootstrap context and improve precision recall.

#### Work
- keep LCM/QMD as core lane
- prefer query-based recall over broad file stuffing
- classify recurring memory types:
  - durable preference
  - operating rule
  - recent work artifact
  - ephemeral session detail
- reduce what must live in always-loaded bootstrap files

#### Why
A memory-rich assistant should retrieve, not constantly preload.

### 10. Operator view for active work

#### Goal
Provide one compact surface for:
- active workers
- blocked tasks
- recent failures
- production jobs awaiting proof
- last successful external actions

#### Important constraint
Do this after receipts and task ownership exist, otherwise the board becomes cosmetic.

## Concrete implementation backlog

## Now

### A. Finish the run-trace vertical slice and land it cleanly
- use existing task trace events and parentRunId derivation
- keep CLI/task surface integration
- verify tree rendering, compact default, verbose optional
- commit only after clean test evidence

### B. Define a receipt JSON shape
Suggested fields:
- `receiptType`
- `owner`
- `runId`
- `targetSystem`
- `targetRef`
- `artifactPaths`
- `verificationStatus`
- `verificationEvidence`
- `createdAt`
- `notes`

### C. Apply receipts to top 3 risky workflows
1. LinkedIn publish
2. gateway/config change
3. cron jobs that send or mutate external systems

### D. Introduce worker-lane guidance
- cron and bounded automation should default to worker style
- front-facing sessions should synthesize, not babysit tool chatter

## Next

### E. Add failure classification to cron history
At minimum classify:
- agent-response failure
- transport/delivery failure
- tool execution failure
- verification failure
- timeout

### F. Add blocked/proof-required fields to task metadata
- do not overbuild UI first
- persist the contract first

### G. Write a small operator guide
A short doc explaining:
- what a task receipt is
- what counts as verified completion
- when to use worker vs front-facing lanes
- how to interpret trace trees

## Recommended file targets

### Source/runtime likely touched
- `/root/openclaw/src/tasks/task-executor.ts`
- `/root/openclaw/src/tasks/task-registry.ts`
- `/root/openclaw/src/tasks/task-status.ts`
- `/root/openclaw/src/auto-reply/reply/commands-tasks.*`
- existing run-trace source files under `/root/openclaw/src/agents/`

### Docs
- this file: `/root/.openclaw/workspace/docs/architecture/nasr-openclaw-implementation-roadmap.md`
- follow-up operator spec: `docs/architecture/task-receipts-and-proof.md`
- follow-up policy spec: `docs/architecture/worker-vs-frontfacing-agents.md`

## What not to do yet

Do not do these before trace + receipts are real:
- big board UI
- runtime fleet dashboard
- new agent explosion
- abstract orchestration layer rewrite
- separate control plane product

Those are tempting, but premature.

## Recommendation

If Ahmed wants the highest-ROI next build, it should be:

### Priority 1
Land the trace viewer slice.

### Priority 2
Define and apply receipts to LinkedIn posting and other proof-sensitive workflows.

### Priority 3
Formalize worker-vs-front-facing agent rules for cron and bounded automation.

That sequence gives the biggest trust improvement with the least architectural risk.
