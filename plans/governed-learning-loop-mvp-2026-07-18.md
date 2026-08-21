# Governed Learning Loop MVP

## Plan Metadata

- Status: complete
- Owner: NASR/main
- Planned at: commit `ef2a24863` on `2026-07-18`
- Depends on: none

> **Executor contract:** Read the full plan before editing. Stay inside scope, run each verification gate, and report evidence. If a stop condition is met or reality conflicts with the plan, stop and report the mismatch instead of improvising.

> **Drift check:** `git diff --stat ef2a24863..HEAD -- skills/governed-learning-loop tests/test_governed_learning_loop.py docs/agent-governance/governed-learning-loop-2026-07-18.md plans/governed-learning-loop-mvp-2026-07-18.md`
> If an in-scope path changed, compare current source with the evidence anchors below. Refresh or supersede the plan before execution when the intended change or verification no longer matches.

## Objective

- Target outcome: create a local, deterministic pipeline that records verified workflow observations, groups repeated evidence into reviewable candidates, validates candidate readiness, and blocks automatic promotion.
- User-visible success condition: a real workspace sample produces a candidate report without changing any active skill, runtime job, credential, or external system.
- Why this matters: useful work should compound into reusable organizational capability without allowing weak evidence or one session to rewrite operating behavior.

## Evidence And Current State

- Source anchors: `AGENTS.md:54` - repeated useful work should be promoted to the smallest durable form.
- Source anchors: `AGENTS.md:55` - recurring automation needs idempotency, bounded behavior, failure reporting, and a verified success condition before cron.
- Source anchors: `skills/cron/auto-lessons/SKILL.md:26` - daily capture already extracts corrections, errors, preferences, and better approaches.
- Source anchors: `scripts/weekly-agent-review.py:241` - the legacy weekly review can append directly to active skills and therefore lacks a candidate boundary.
- Existing convention to follow: scripts under a skill for deterministic behavior, tests under `tests/`, and local evidence under `data/` plus `reports/`.
- Reproduction or baseline: no governed candidate registry or manual promotion receipt exists.
- Raw evidence to preserve: existing `.learnings/`, daily memory, lesson files, skills, cron definitions, and the dirty worktree.

## Scope

- In scope: one OpenClaw skill, deterministic capture/build/validate/promote-request commands, JSON registry, Markdown review report, policy reference, focused tests, and one manual sample.
- Files likely touched: `skills/governed-learning-loop/`, `skills/cron/governed-learning-loop/`, `tests/test_governed_learning_loop.py`, `docs/agent-governance/governed-learning-loop-2026-07-18.md`, `data/learning-loop/`, `reports/learning-loop/`, this plan, and today's daily note.
- Do not touch: unrelated active skill bodies, gateway configuration, credentials, external services, JobZoom, CMO, or existing unrelated user changes.
- Non-goals: automatic skill generation, autonomous promotion, model-driven transcript mining, runtime scheduling, or credential brokering.

## Authority And Safety

- Permission profile: runtime-change
- Approval boundary: Ahmed approved the learning-loop implementation. The existing Saturday skill-autoresearch job may be converted from autonomous active-skill edits to the deterministic candidate build after the real sample passes. Promotion into an active rule or skill remains separately explicit and evidence-bound.
- Rollback path: remove only the new learning-loop files and generated sample artifacts; restore cron job `82dd85c2-9300-4083-98d7-fa5cff90b795` from the pre-change JSON captured in this task if Ahmed explicitly wants autonomous skill edits restored.
- External/public/credential/paid/runtime action involved: runtime cron edit only; no external, public, credential, paid, or gateway-lifecycle action.

## Owner And Helpers

- Owning session/agent: NASR/main
- Helpers, if explicitly permitted: none
- Independent assignment and expected evidence for each helper: not applicable
- Maximum concurrency: 1

## Ordered Implementation Steps

### Step 1: Build the governed skill and registry

- Files: `skills/governed-learning-loop/`
- Change: implement observation capture, deduplicated candidate building, readiness validation, and promotion-request receipts.
- Preserve: active skills and source evidence remain read-only.
- Verify command/check: run the skill validator and CLI help.
- Expected result: valid skill metadata and deterministic commands with no implicit promotion.

### Step 2: Add policy and focused tests

- Files: `docs/agent-governance/governed-learning-loop-2026-07-18.md`, `tests/test_governed_learning_loop.py`
- Change: document stages, gates, ownership, and stop rules; test idempotency, recurrence, distinct evidence, readiness, and promotion blocking.
- Preserve: no cron or active-skill mutation.
- Verify command/check: `python3 -m unittest -v tests.test_governed_learning_loop`
- Expected result: all focused tests pass.

### Step 3: Prove a real manual sample

- Files: `data/learning-loop/`, `reports/learning-loop/`
- Change: record two independently verified observations from existing completed workflow evidence and build the review report.
- Preserve: source artifacts remain unchanged.
- Verify command/check: validate the candidate, rerun build, compare counts/checksums, and inspect the report.
- Expected result: one reviewable candidate, idempotent rerun, zero active promotions.

### Step 4: Remove the live governance bypass

- Files: `skills/cron/governed-learning-loop/SKILL.md` and cron job `82dd85c2-9300-4083-98d7-fa5cff90b795`.
- Change: preserve the Saturday schedule but replace the agent turn that edits three active skills with the deterministic `build` command and silent success delivery.
- Preserve: model choice elsewhere, failure alert, schedule, active skills, and external state.
- Verify command/check: inspect the live cron JSON, run the command manually, and confirm registry idempotency plus zero active promotions.
- Expected result: the weekly job can update only the registry/report and cannot modify active skills.

## Test Plan

- Existing tests to run: skill quick validation and engineering-plan validation.
- New or changed tests: focused unit tests for the learning-loop CLI and registry.
- Original reproduction after implementation: the baseline absence of a governed registry becomes a real report and JSON candidate with a manual-only status.
- Actual artifact or behavior to inspect: generated candidate report, registry, and promotion-request receipt.

## Stop Conditions

- An evidence anchor or in-scope file has materially drifted.
- A required dependency or approval is missing.
- A verification gate fails twice after bounded repair.
- The smallest credible fix requires active-skill edits, a new cron, external access, or a runtime change beyond the approved conversion of the existing weekly skill-autoresearch job.

## Done Criteria

- [x] Every ordered step completed or explicitly skipped with evidence.
- [x] Focused tests and original reproduction pass.
- [x] Actual user-visible or operational outcome inspected.
- [x] Changed files remain inside scope.
- [x] Accepted review findings repaired and reverified.
- [x] Remaining risk and rollback evidence recorded.

## Review Handoff

- Diff base and target: `ef2a24863` to working tree, limited to in-scope paths.
- Reviewer focus: accidental active-skill mutation, weak evidence promotion, idempotency, path traversal, and secret leakage.
- Known trade-offs: v1 uses explicit observations instead of mining raw transcripts.
- Deliberately deferred work: scheduling, automatic drafting, credential brokering, and branchable remote sandboxes.

## Closeout

- Files/artifacts changed: added the governed skill, cron wrapper, policy, tests, registry, report, sample observations, and rollback JSON; converted the existing weekly job in place.
- Commands/checks and results: 8 focused unit tests passed; Python compile passed; both skill and plan validators passed; OpenClaw reports the skill ready and visible; candidate validation passed.
- Deviations from plan: the initial local-only plan was refreshed after live inspection found an existing weekly agent turn that directly edited active skills. The approved implementation converted that exact job to the deterministic build instead of leaving the governance bypass active.
- Evidence of success: two distinct governed-outcome observations produced one eligible candidate; repeated build preserved registry SHA-256 `ab886f38a955fc85fd014d31676fc6f878750b9070f978d4fd8bdc340d904ec5`; the live scheduled command completed `ok` in 150 ms with `created: 0`, `updated: 0`, and delivery not requested.
- Residual risk: observation capture is explicit in v1, so candidate quality depends on disciplined evidence entry. Model-assisted extraction, automatic drafting, branchable sessions, and stronger credential brokering remain deferred.
