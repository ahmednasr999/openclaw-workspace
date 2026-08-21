# GBrain Design-Donor Pilot Plan

## Plan Metadata

- Status: complete
- Owner: NASR/main
- Planned at: commit `34f3b95` on `2026-08-13`
- Depends on: none

> **Executor contract:** Keep GBrain isolated from NASR production data, credentials, skills, config, cron, and runtime. Inspect and test only inside the temporary evaluation checkout. Stop before promotion into an active skill or core instruction file.

> **Drift check:** `git diff --stat 34f3b95..HEAD -- plans/gbrain-design-donor-pilot-2026-08-13.md docs/research/gbrain-design-donor-assessment-2026-08-13.md reports/gbrain-design-donor prototypes/gbrain-design-donor`

## Objective

- Target outcome: evaluate GBrain's correction pipeline, data-loss gate, fact-check gate, brain-ingest gate, and context audit as design donors for NASR.
- User-visible success condition: a verified adopt/adapt/reject decision for each component, isolated test evidence, bounded candidate amendments, and no competing production memory system.
- Why this matters: the useful controls may improve NASR's evidence, ingestion, and recovery discipline without importing GBrain's overlapping architecture and maintenance burden.

## Evidence And Current State

- Source anchors: `AGENTS.md:38` - destructive or irreversible actions already require approval; `SOUL.md:45` - user corrections are recorded, but the always-loaded rule does not require source tracing and propagation checks; `skills/nasr-knowledge-ingestion/SKILL.md:12` and `skills/nasr-knowledge-ingestion/SKILL.md:14` - external knowledge already lands in a sandbox or wiki, and core-memory promotion requires explicit review.
- Existing convention: `skills/governed-learning-loop/SKILL.md:43` - proposals require baseline-versus-candidate replay before promotion.
- Upstream snapshot: GBrain `v0.45.8.0`, commit `4dc77c39790d65f40a1560c888e4324ea5d9c5b3`, MIT license.
- Reproduction or baseline: NASR has policy-level destructive approval and sandboxed ingestion, but no shared producer-not-verifier rule and no semantic pre-write dedup contract in the ingestion skill.
- Raw evidence to preserve: isolated test results and component matrix in `docs/research/gbrain-design-donor-assessment-2026-08-13.md`.

## Scope

- In scope: isolated source/dependency review, focused upstream tests, component comparison, report-only context audit, and non-active candidate drafts.
- Files likely touched: this plan, one research report, report-only audit, prototype candidate packet, current daily note, and one operational error-log append.
- Do not touch: active skills, `AGENTS.md`, `SOUL.md`, `USER.md`, `TOOLS.md`, `MEMORY.md`, runtime config, gateway, cron, credentials, or external systems.
- Non-goals: installing GBrain, migrating NASR memory, enabling its MCP server, importing personal data, or promoting a candidate.

## Authority And Safety

- Permission profile: local-write
- Approval boundary: Ahmed approved the isolated design-donor assessment; active promotion still requires exact candidate and target approval after replay.
- Rollback path: remove only the new plan/report/prototype files; no production state depends on them.
- External/public/credential/paid/runtime action involved: no. The public repository was cloned read-only; locked dependencies were downloaded into `/tmp` with install scripts disabled and a credential-free environment.

## Owner And Helpers

- Owning session/agent: NASR/main
- Helpers, if explicitly permitted: none
- Independent assignment and expected evidence for each helper: not applicable
- Maximum concurrency: 1

## Ordered Implementation Steps

### Step 1: Verify provenance and isolate the donor

- Files: temporary checkout only
- Change: clone the public repository into `/tmp`, verify commit, license, lockfile, dependency surface, and suspicious-content indicators.
- Preserve: no credentials and no production data in the process environment.
- Verify command/check: `git log -1`, license inspection, dependency inspection, suspicious-pattern scan, symlink scan.
- Expected result: credible source with explicit risks documented and no installation into OpenClaw.

### Step 2: Test the relevant upstream controls

- Files: temporary checkout only
- Change: install locked dependencies with install scripts disabled; run focused destructive-guard, routing, reference, brain-first, and privacy checks.
- Preserve: no post-install hooks, no networked model calls, no database outside the temporary PGLite test database.
- Verify command/check: focused Bun test and repository checks recorded in the assessment.
- Expected result: tests pass or failures are retained as evidence.

### Step 3: Map donor value to NASR

- Files: `docs/research/gbrain-design-donor-assessment-2026-08-13.md`, `reports/gbrain-design-donor/context-audit-2026-08-13.md`
- Change: classify each component as adopt, adapt, retain, or reject; measure the editable always-loaded workspace context.
- Preserve: report-only treatment of core instruction files.
- Verify command/check: evidence citations, measured file sizes, and no core-file diff.
- Expected result: bounded decisions with explicit overlap, gap, and risk.

### Step 4: Stage non-active candidate amendments

- Files: `prototypes/gbrain-design-donor/`
- Change: draft the smallest reusable controls and representative evaluation cases outside active skill paths.
- Preserve: governed-learning promotion boundary and existing active behavior.
- Verify command/check: packet completeness, five-case matrices, and Git diff inspection.
- Expected result: promotion-ready concepts, not promoted behavior.

## Test Plan

- Existing tests to run: GBrain destructive guard, routing eval, brain-first guard, skill reference checker, and privacy checker.
- New or changed tests: representative candidate matrix covering happy path, incomplete input, hostile content, installed-capability overlap, and partial failure.
- Original reproduction after implementation: not applicable until an exact candidate is approved for promotion.
- Actual artifact or behavior to inspect: research report, context audit, candidate controls, and evaluation matrix.

## Stop Conditions

- An evidence anchor or in-scope file materially drifts.
- A required dependency or approval is missing.
- A verification gate fails twice after bounded repair.
- The smallest credible fix requires an active skill, core-file, runtime, credential, destructive, or external change.

## Done Criteria

- [x] Upstream source is isolated and provenance is recorded.
- [x] Focused upstream tests pass or failures are documented.
- [x] Component decisions and context audit are persisted.
- [x] Candidate packet and evaluation cases are persisted.
- [x] Changed files remain inside scope.
- [x] Closeout records residual risk and next approval boundary.

## Review Handoff

- Diff base and target: `34f3b95` to working tree, limited to the paths in this plan.
- Reviewer focus: whether the evidence justifies candidate promotion without duplicating existing controls.
- Known trade-offs: upstream narrative skills are routing conventions; only some destructive operations have mechanical enforcement.
- Deliberately deferred work: active skill edits, full GBrain test suite, MCP integration, and production data trials.

## Closeout

- Files/artifacts changed: this plan; the research assessment; report-only context audit; non-active candidate controls and evaluation matrix; `memory/2026-08-13.md`; one append to `.learnings/ERRORS.md`.
- Commands/checks and results: destructive guard 24/24; routing eval 282/282; brain-first guard passed; 169-file reference check passed with zero warnings; privacy check passed; plan validator passed; `git diff --check` passed; artifact presence check passed.
- Deviations from plan: the first credential-free Bun command omitted Bun's actual binary directory and failed before installation; it was corrected with a minimal explicit path and logged. The full upstream suite remained deliberately out of scope.
- Evidence of success: all promised artifacts are non-empty and inspected; active skills, core instructions, cron, gateway, runtime, credentials, and production data were not modified by the pilot.
- Residual risk: candidate behavior remains unproven in live NASR workflows until baseline-versus-candidate replay; Bun 1.3.9 is below GBrain's declared 1.3.10 minimum despite the focused checks passing.
