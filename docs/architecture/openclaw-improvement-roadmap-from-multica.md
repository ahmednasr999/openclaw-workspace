# OpenClaw improvement roadmap inspired by Multica

Last updated: 2026-04-15
Owner: NASR
Purpose: translate the useful lessons from Multica into a concrete OpenClaw roadmap without collapsing OpenClaw into an issue-only product

## Executive summary

OpenClaw should not copy Multica wholesale.

It should steal the operational shell, not the soul.

OpenClaw's enduring advantage is:
- assistant identity
- channels and messaging
- memory and recall
- cron and proactive automation
- nodes and device integration
- broader multi-agent orchestration

The main gap is not core architecture. The main gap is operator ergonomics and team legibility.

So the roadmap should focus on making OpenClaw easier to understand, easier to operate, and easier to trust at a glance.

## Product principle

### Preserve
- personal assistant core
- cross-channel operation
- proactive behavior
- memory-first workflows
- plugin and skill extensibility
- device and node model

### Improve
- runtime visibility
- agent workload visibility
- assignment clarity
- progress transparency
- automation productization
- workspace legibility

### Avoid
- shrinking OpenClaw into a coding-task board only
- making issues the universal abstraction for everything
- turning the system into a thin wrapper around coding CLIs
- sacrificing proactive assistant behavior for team-task neatness

## Roadmap overview

## Phase 1 - Quick wins, 1 to 3 weeks

These are low-risk, high-clarity improvements.

### 1. Runtime registry view

Build a first-class runtime inventory.

#### Goal
Let the operator instantly see:
- what runtimes exist
- whether they are online
- which model/provider lanes they expose
- last heartbeat time
- current load / active tasks
- special capabilities like browser, node access, elevated execution

#### Why
Today too much of this is implicit, fragmented, or buried in logs/status output.

#### Deliverables
- `/runtimes` or `/fleet` style UI/CLI view
- runtime cards with status, last seen, host, capabilities
- per-runtime active sessions/tasks count
- stale runtime warning state

#### Success metric
An operator can answer "where is this work actually running?" in under 10 seconds.

### 2. Agent status board

Build a simple board for agent work state.

#### Goal
Make each agent's current state obvious:
- idle
- queued
- running
- blocked
- waiting on user
- failed recently

#### Deliverables
- board or table view of all agents
- current task title or session label
- started at / last update / last error
- click-through to session or task detail

#### Why
OpenClaw has the raw state, but not a clean control surface.

#### Success metric
Ahmed can glance once and know which agents need attention.

### 3. Standard progress schema

Define a shared progress vocabulary across agents.

#### Goal
Stop progress updates from being ad hoc prose.

#### Proposed shared states
- planning
- running
- waiting_external
- waiting_user
- blocked
- completed
- failed

#### Deliverables
- status schema in session/task metadata
- progress badge in UI/chat summaries
- standard timestamps for started, updated, blocked_since

#### Why
Humans trust systems they can parse quickly.

### 4. Better assignment UX

Make explicit delegation feel native.

#### Goal
Support an easy operator action like:
- send this to HR
- assign this to CTO
- let CMO handle this
- route this coding task to Codex agent on runtime X

#### Deliverables
- clearer `assign` action in UI/chat
- deterministic agent/routing confirmation
- optional override of runtime/model when needed

#### Why
Today this is possible, but not always legible.

## Phase 2 - Medium lifts, 3 to 8 weeks

These improve trust and daily usability.

### 5. Automation center

Turn cron and triggers into a real product surface.

#### Goal
Make recurring automation understandable to non-operators.

#### Deliverables
- list of automations with owner, schedule, target, last run, next run, last result
- run history with success/failure summaries
- disable, pause, test-run actions
- filter by workspace / agent / destination

#### Why
OpenClaw automations are powerful but too hidden.

#### Success metric
An operator can audit all active automations without opening raw config or job JSON.

### 6. Workspace and ownership boundaries

Make workspace scope more explicit.

#### Goal
Clarify what belongs to which workspace or context:
- agents
- skills
- automations
- sessions
- tools and secrets exposure

#### Deliverables
- workspace ownership badges
- clearer workspace scoping in agent/task/session views
- explicit visibility rules in UI and docs

#### Why
This matters much more as OpenClaw becomes multi-team.

### 7. Structured blocker handling

Blockers should become first-class objects, not buried in chat text.

#### Goal
When an agent is blocked, surface:
- blocker type
- what it needs
- urgency
- who owns the unblock
- whether it is waiting on time, auth, approval, or missing context

#### Deliverables
- blocker cards in status board
- blocker summaries in heartbeats/user-facing notifications
- queue of unresolved blockers

#### Why
This is one of the highest trust multipliers for autonomous systems.

### 8. Human-readable execution audit trail

Build a cleaner event timeline per task/session.

#### Goal
Show the operator a compact sequence like:
- assigned
- started on runtime X
- used tool Y
- hit blocker Z
- resumed
- completed

#### Deliverables
- task/session timeline UI
- collapse noisy raw logs behind summary rows
- link to underlying session history when needed

## Phase 3 - Major bets, 2 to 6 months

These are strategic, not cosmetic.

### 9. Work board for agents and tasks

Build a proper board view.

#### Goal
Give OpenClaw a native visual work surface without turning it into only a project board.

#### Lanes
- inbox
- queued
- running
- blocked
- review / waiting
- completed recently

#### Important constraint
This board should support assistant work, operational work, and coding work, not only issue tickets.

#### Why
Multica is right that visible work builds trust.
OpenClaw should have that too, but with broader object types.

### 10. Fleet orchestration layer

Add a higher-level control plane for many runtimes.

#### Goal
Answer questions like:
- which runtime should take coding-heavy work?
- which runtime has browser auth?
- which runtime is overloaded?
- which runtimes are safe for sensitive data?

#### Deliverables
- scheduling hints / constraints
- runtime tags and capability labels
- routing preferences by agent/task type
- health and saturation awareness

#### Why
As the system scales, routing cannot stay mostly implicit.

### 11. Productized multi-user collaboration

Move from "can support teams" to "feels built for teams".

#### Goal
Make shared operation natural.

#### Deliverables
- shared views for work ownership
- explicit mentions / escalations / handoffs
- role-aware surfaces for CEO, CTO, HR, CMO style agents or human operators
- auditability that does not require log-diving

#### Constraint
This must not break the personal-assistant-first experience in direct chat.

### 12. Unified operational dashboard

This is the major shell unification bet.

#### Goal
One control surface showing:
- runtimes
- agents
- automations
- blockers
- recent failures
- waiting approvals
- high-priority inbox items
- model/provider health

#### Why
This would close a large part of the ergonomics gap with products like Multica while preserving OpenClaw's broader mission.

## Recommended implementation order

### Tier A - do first
1. runtime registry view
2. agent status board
3. standard progress schema
4. assignment UX cleanup

### Tier B - do next
5. automation center
6. structured blocker handling
7. execution audit timeline

### Tier C - bigger strategic program
8. work board
9. fleet orchestration
10. multi-user collaboration shell
11. unified operational dashboard

## Highest ROI features

If only 3 things get built, build these:

### 1. Runtime registry
Because hidden infrastructure state creates confusion everywhere.

### 2. Agent status board
Because operators need a glanceable mental model of the system.

### 3. Automation center
Because recurring autonomy must be inspectable and controllable.

## What this would change for Ahmed specifically

### Immediate value
- faster diagnosis when something silently routes wrong
- clearer understanding of which agent is active or blocked
- easier trust in background automation
- less need to inspect raw logs, session files, or cron JSON

### Strategic value
- better path from personal assistant to team-operable system
- stronger demo story
- more product-like operating feel without losing OpenClaw depth

## Anti-goals

Do not ship these as the first response:
- issue-only board that ignores chat, reminders, and operational tasks
- heavyweight governance before visibility basics exist
- deep abstraction layer for every task type before common status schema exists
- Multica-style product mimicry that weakens OpenClaw's distinctiveness

## The core synthesis

The right move is:
- keep OpenClaw as the broader agent operating system
- add Multica-grade operator ergonomics around it

In plain terms:
- do not become Multica
- become easier to operate than Multica while remaining much broader

## Suggested next execution brief

If this roadmap becomes active, the first implementation brief should be:

### Project
OpenClaw Fleet Visibility MVP

### Scope
- runtime registry page/CLI view
- agent status board
- shared progress/blocker status schema
- lightweight links from board items to sessions/tasks

### Non-goals
- no issue-only board
- no full team permission system
- no deep scheduler rewrite

### Success definition
Ahmed can answer these in under 10 seconds without log diving:
- what is running right now?
- where is it running?
- what is blocked?
- what automation failed recently?
- what needs his approval?
