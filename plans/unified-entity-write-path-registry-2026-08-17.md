# Unified Entity and Write-Path Registry

## Plan Metadata

- Status: complete
- Owner: NASR/main
- Planned at: commit `71c0740d5989c0d19fc851fdb3c8a492ff6892e7` on `2026-08-17`
- Depends on: Ahmed's approval in Telegram message 63549

> **Executor contract:** Read the full plan before editing. Stay inside scope, run each verification gate, and report evidence. If a stop condition is met or reality conflicts with the plan, stop and report the mismatch instead of improvising.

> **Drift check:** `git diff --stat 71c0740d5989c0d19fc851fdb3c8a492ff6892e7..HEAD -- config/entity-write-path-registry.json docs/architecture/entity-write-path-registry-2026-08-17.md scripts/check-entity-write-path-registry.py tests/test_entity_write_path_registry.py plans/unified-entity-write-path-registry-2026-08-17.md`
> If an in-scope path changed, compare current source with the evidence anchors below. Refresh or supersede the plan before execution when the intended change or verification no longer matches.

## Objective

- Target outcome: Establish one declared authoritative owner and controlled write path for each core entity while keeping the existing federated systems in place.
- User-visible success condition: Ahmed can see which system owns jobs, applications, contacts, content, tasks, calendar events, email, knowledge, and runtime operations; a deterministic audit rejects missing ownership, ambiguous writers, absent governance gates, and incomplete workflow measurement contracts.
- Why this matters: It prevents duplicate systems and unsafe automation while making cross-workflow handoffs explicit.

## Evidence And Current State

- Source anchors: `scripts/pipeline_db.py:3` declares the single access point for the main career SQLite database; `scripts/pipeline_db.py:29` provides its kill switch; `/root/.openclaw/workspace-jobzoom/scripts/mark_run_applied.py:9` defines the JobZoom applied-ledger bridge; `docs/content-claw/nasr-campaign-graph.md:9` declares Notion as the content source of truth; `docs/hr-career-sentinel.md:16` proves the email lane has no mailbox-write path; `scripts/calendar-prefetch.py:3` declares Google Calendar as the upstream and the local file as a cache; `MEMORY.md:33` defines durable memory capture; `AGENTS.md:24` defines owner workspaces and approval boundaries.
- Existing convention to follow: `config/service-registry.md:20` documents service ownership and connection methods; `docs/agent-governance/context-contracts-2026-06-17.md:1` uses explicit source, boundary, verification, and stop contracts.
- Reproduction or baseline: There is a service registry and multiple domain-specific source-of-truth statements, but no single machine-readable entity/write-path registry or validator.
- Raw evidence to preserve: Existing production databases, Notion databases, Gmail, Google Calendar, OpenClaw runtime state, owner workspaces, and all current write entry points remain unchanged.

## Scope

- In scope: A machine-readable registry, architecture note, fail-closed structural and live-evidence validator, focused tests, an audit report, and today's durable decision note.
- Files likely touched: `config/entity-write-path-registry.json`, `docs/architecture/entity-write-path-registry-2026-08-17.md`, `scripts/check-entity-write-path-registry.py`, `tests/test_entity_write_path_registry.py`, `reports/entity-write-path-registry-audit-latest.json`, this plan, `memory/active-tasks.md`, `memory/2026-08-17.md`, and `.learnings/ERRORS.md` if a verification failure exposes a reusable gotcha.
- Do not touch: Live databases, sibling-workspace code, Notion records, Gmail, Google Calendar, OpenClaw configuration, gateway state, cron schedules, systemd units, public content, or third-party services.
- Non-goals: No all-in-one database, no data migration, no agent creation, no cheaper-model routing, no production writer changes, and no automated external action.

## Authority And Safety

- Permission profile: local-write
- Approval boundary: Ahmed approved the architecture implementation; external writes, runtime/config changes, service lifecycle actions, migrations, and destructive cleanup remain outside authority.
- Rollback path: Remove only the newly added registry, documentation, checker, tests, report, plan, and the appended daily-note section; no production state requires restoration.
- External/public/credential/paid/runtime action involved: no

## Owner And Helpers

- Owning session/agent: NASR/main
- Helpers, if explicitly permitted: None; delegation was not requested.
- Independent assignment and expected evidence for each helper: No helpers.
- Maximum concurrency: 1

## Ordered Implementation Steps

### Step 1: Encode authoritative ownership and write direction

- Files: `config/entity-write-path-registry.json`, `docs/architecture/entity-write-path-registry-2026-08-17.md`
- Change: Define the core entities, canonical systems, read models, allowed writer entry points, sync direction, governance gates, and the five workflow measurement contracts.
- Preserve: Existing federated systems and current approval boundaries.
- Verify command/check: `python3 -m json.tool config/entity-write-path-registry.json >/dev/null`
- Expected result: Valid JSON with no credentials and one owner per entity.

### Step 2: Add deterministic structural and evidence validation

- Files: `scripts/check-entity-write-path-registry.py`, `tests/test_entity_write_path_registry.py`
- Change: Fail closed on missing entities, duplicate identifiers, weak write-path declarations, incomplete governance, missing measurement fields, or failed local path/SQLite evidence checks.
- Preserve: Read-only audit behavior; no database, service, or config mutation.
- Verify command/check: `python3 -m unittest -v tests/test_entity_write_path_registry.py`
- Expected result: Focused positive and negative tests pass.

### Step 3: Run the live audit and record the decision

- Files: `reports/entity-write-path-registry-audit-latest.json`, `memory/2026-08-17.md`, this plan
- Change: Produce the current evidence report, append the approved architecture decision, complete the plan, and inspect the final diff.
- Preserve: Dirty-worktree changes outside the scoped files.
- Verify command/check: `python3 scripts/check-entity-write-path-registry.py --live --output reports/entity-write-path-registry-audit-latest.json && git diff --check -- config/entity-write-path-registry.json docs/architecture/entity-write-path-registry-2026-08-17.md scripts/check-entity-write-path-registry.py tests/test_entity_write_path_registry.py plans/unified-entity-write-path-registry-2026-08-17.md memory/2026-08-17.md`
- Expected result: Audit returns success, output is parseable JSON, and scoped diff has no whitespace errors.

## Test Plan

- Existing tests to run: `python3 scripts/check-agentic-engineering-plan.py plans/unified-entity-write-path-registry-2026-08-17.md`
- New or changed tests: Valid registry acceptance; missing entity; duplicate owner/identifier ambiguity; missing governance gate; unauthorized direct writer; incomplete workflow measurement; failed SQLite table evidence.
- Original reproduction after implementation: Run the checker against the production registry and confirm the previously missing unified contract now produces a complete audit.
- Actual artifact or behavior to inspect: Read the generated registry audit and manually compare the documented owner/write directions with the source anchors.

## Stop Conditions

- An evidence anchor or in-scope file materially drifts.
- An authoritative source cannot be established without changing a production workflow.
- A verification gate fails twice after bounded repair.
- The smallest credible fix requires a sibling-workspace mutation, external write, runtime/config change, migration, or destructive action.

## Done Criteria

- [x] Every ordered step completed or explicitly skipped with evidence.
- [x] Focused tests and original reproduction pass.
- [x] Actual user-visible or operational outcome inspected.
- [x] Changed files remain inside scope.
- [x] Accepted review findings repaired and reverified.
- [x] Remaining risk and rollback evidence recorded.

## Review Handoff

- Diff base and target: `71c0740d5989c0d19fc851fdb3c8a492ff6892e7` to working tree, scoped to this plan's files.
- Reviewer focus: Conflicting sources of truth, direct writer loopholes, false claims of external authority, missing rollback/kill-switch gates, and invented measurement values.
- Known trade-offs: The first release defines measurement contracts but does not fabricate historical manual-time baselines; those require observed samples.
- Deliberately deferred work: Production enforcement in individual writers and a seven-day workflow baseline are deferred until this read-only registry proves accurate.

## Closeout

- Files/artifacts changed: Added the registry, architecture contract, checker, focused tests, and latest audit report; updated the active-task register, daily note, and this plan.
- Commands/checks and results: JSON parsing and Python compilation passed; seven focused unit tests passed; the live read-only audit passed 23/23 declared evidence checks; the plan validator and scoped whitespace checks passed.
- Deviations from plan: The first live audit exposed the actual Notion config nesting as `databases.content_calendar.id`; the key path was corrected and the reusable fail-closed schema-check lesson was appended to `.learnings/ERRORS.md`.
- Evidence of success: `reports/entity-write-path-registry-audit-latest.json` records nine entities, five workflows, seven governance gates per entity, zero errors, and 23/23 live checks passing.
- Residual risk: The governance layer documents and verifies current authority but does not yet enforce it inside every producer. Manual-touch baselines remain intentionally pending observed data through 25 August 2026.
