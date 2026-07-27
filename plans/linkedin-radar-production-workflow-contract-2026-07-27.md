# LinkedIn Radar Production Workflow Contract

## Plan Metadata

- Status: complete
- Owner: NASR
- Planned at: commit `65da9b107451b09fb93d8dd8340b7d2f6d8f4763` on `2026-07-27`
- Depends on: `plans/governed-quality-evidence-phase-2026-07-18.md`

> **Executor contract:** Read the full plan before editing. Stay inside scope, run each verification gate, and report evidence. If a stop condition is met or reality conflicts with the plan, stop and report the mismatch instead of improvising.

> **Drift check:** `git diff --stat 65da9b107451b09fb93d8dd8340b7d2f6d8f4763..HEAD -- scripts/production_workflow_contract.py tests/test_production_workflow_contract.py docs/agent-governance/production-workflow-contract-2026-07-27.md && git -C /root/.openclaw diff --stat -- workspace-cmo/scripts/run_linkedin_comment_radar.py workspace-cmo/scripts/judge_linkedin_comment_radar_run.py workspace-cmo/tests/test_linkedin_comment_radar.py workspace-cmo/tests/test_linkedin_comment_radar_judge.py`
> If an in-scope path changed, compare current source with the evidence anchors below. Refresh or supersede the plan before execution when the intended change or verification no longer matches.

## Objective

- Target outcome: establish a reusable persisted-stage workflow contract and make LinkedIn Comment Radar its first resumable, independently judged implementation.
- User-visible success condition: a radar run persists `source -> extract -> validate -> rank -> approval`, resumes without rerunning completed stages, exposes explicit terminal states, and refuses to report a full pack when the independent judge detects broken artifacts.
- Why this matters: the recurring radar must recover from browser, process, and artifact failures without duplicating work or presenting an invalid approval pack.

## Evidence And Current State

- Source anchors: `workspace-cmo/scripts/run_linkedin_comment_radar.py:2333` - the current orchestration is one monolithic run with no persisted stage boundary.
- Existing convention to follow: `workspace-cmo/scripts/run_linkedin_comment_radar.py:2076` - artifact IDs are allocated to avoid overwriting delivered reports and cards.
- Additional source anchor: `workspace-cmo/scripts/run_linkedin_comment_radar.py:1446` - the existing quality gate already classifies candidates and is the ranking-stage implementation to preserve.
- Additional source anchor: `workspace-cmo/scripts/run_linkedin_comment_radar.py:2136` - approval cards already enforce the five-card integrity gate.
- Additional source anchor: `AGENTS.md:55` - recurring automation requires ownership, idempotency, bounded retries, failure reporting, and a verified success condition.
- Reproduction or baseline: the existing focused radar suite passes 13 tests, but it has no checkpoint-resume or independent artifact-judge coverage.
- Raw evidence to preserve: current radar reports, cards, approval packs, handled-URL ledgers, and the existing live-validation fields on each card.

## Scope

- In scope: reusable local workflow-state helper, radar-specific five-stage orchestration, explicit resume CLI/automatic same-slot recovery, deterministic independent judge, fault-injection tests, governance documentation, and local evidence.
- Files likely touched: `scripts/production_workflow_contract.py`, `tests/test_production_workflow_contract.py`, `workspace-cmo/scripts/run_linkedin_comment_radar.py`, `workspace-cmo/scripts/judge_linkedin_comment_radar_run.py`, `workspace-cmo/tests/test_linkedin_comment_radar.py`, `workspace-cmo/tests/test_linkedin_comment_radar_judge.py`, `docs/agent-governance/production-workflow-contract-2026-07-27.md`, this plan, and `memory/2026-07-27.md`.
- Do not touch: cron, gateway/runtime configuration, LinkedIn approval/posting handlers, Notion, JobZoom, browser profile configuration, credentials, or existing delivered radar artifacts.
- Non-goals: introducing a graph framework, adding agents, changing candidate scoring/content policy, posting comments, or migrating other workflows in this change.

## Authority And Safety

- Permission profile: local-write
- Approval boundary: local reversible code, docs, state fixtures, and tests are authorized; public LinkedIn actions, cron changes, gateway/runtime changes, credential changes, and destructive cleanup remain approval-required.
- Rollback path: revert the scoped commit or restore the pre-change versions from commit `65da9b107451b09fb93d8dd8340b7d2f6d8f4763`; new state directories are additive and ignored by older code.
- External/public/credential/paid/runtime action involved: no

## Owner And Helpers

- Owning session/agent: NASR `/root`
- Helpers, if explicitly permitted: none; current instructions prohibit delegation unless explicitly requested.
- Independent assignment and expected evidence for each helper: no helper assignment.
- Maximum concurrency: 1

## Ordered Implementation Steps

### Step 1: Add the reusable persisted-stage contract

- Files: `scripts/production_workflow_contract.py`, `tests/test_production_workflow_contract.py`, `docs/agent-governance/production-workflow-contract-2026-07-27.md`
- Change: implement atomic manifest/stage-output persistence, ordered transitions, idempotent completed-stage reads, bounded attempts, artifact hashes, terminal states, and same-input resume selection.
- Preserve: local-only behavior, deterministic JSON, no workflow-specific business judgment.
- Verify command/check: `python3 -m unittest tests.test_production_workflow_contract -v`
- Expected result: all contract tests pass, including retry exhaustion, completed-stage reuse, corrupt-output rejection, and input-mismatch rejection.

### Step 2: Convert radar orchestration into five resumable stages

- Files: `workspace-cmo/scripts/run_linkedin_comment_radar.py`, `workspace-cmo/tests/test_linkedin_comment_radar.py`
- Change: allocate/resume a run before discovery, persist each stage output, load completed outputs on resume, classify terminal state, and expose `--resume` plus `--no-auto-resume`.
- Preserve: live source policy, existing candidate scoring/gating, immutable delivered artifacts, approval-only output, and no LinkedIn write action.
- Verify command/check: `python3 -m unittest discover -s workspace-cmo/tests -p 'test_linkedin_comment_radar.py' -v`
- Expected result: all existing tests plus stage-resume and injected-failure tests pass without browser access.

### Step 3: Add and wire the independent radar judge

- Files: `workspace-cmo/scripts/judge_linkedin_comment_radar_run.py`, `workspace-cmo/tests/test_linkedin_comment_radar_judge.py`, `workspace-cmo/scripts/run_linkedin_comment_radar.py`
- Change: validate completed stage hashes, final status, five unique approval cards, live-validation evidence, commands, report/card/pack consistency, and run terminal state; make the executor fail closed if the judge rejects.
- Preserve: the judge is read-only and cannot invoke discovery, approval handlers, or posting.
- Verify command/check: `python3 -m unittest discover -s workspace-cmo/tests -p 'test_linkedin_comment_radar_judge.py' -v`
- Expected result: the judge accepts a valid fixture and rejects missing URL, duplicate candidate, broken context hash, missing pack, and corrupted stage evidence.

### Step 4: Run adversarial and full focused verification

- Files: all in-scope files
- Change: compile code, run both new suites and the existing radar tests, inspect one isolated end-to-end fixture, run the standalone judge, and confirm only scoped files changed.
- Preserve: no live browser call and no external action during automated verification.
- Verify command/check: `python3 -m py_compile scripts/production_workflow_contract.py workspace-cmo/scripts/run_linkedin_comment_radar.py workspace-cmo/scripts/judge_linkedin_comment_radar_run.py && python3 -m unittest tests.test_production_workflow_contract -v && python3 -m unittest discover -s workspace-cmo/tests -p 'test_linkedin_comment_radar*.py' -v`
- Expected result: compilation and all focused tests pass; the fixture manifest ends in `approval_required` only when the judge passes.

## Test Plan

- Existing tests to run: the complete current `workspace-cmo/tests/test_linkedin_comment_radar.py` suite.
- New or changed tests: reusable contract tests, source-stage failure and resume, completed-stage non-reexecution, max-attempt exhaustion, valid artifact judgment, and deliberately broken artifact rejection.
- Original reproduction after implementation: simulate a crash after `extract`, resume the same run, and assert `source` and `extract` attempt counts stay unchanged while later stages complete.
- Actual artifact or behavior to inspect: checkpoint manifest, five stage-output JSON files, report, card JSON, approval pack, judge JSON, and terminal-state consistency.

## Stop Conditions

- An evidence anchor or in-scope file has materially drifted.
- A required dependency or approval is missing.
- A verification gate fails twice after bounded repair.
- The smallest credible fix requires out-of-scope files or a new external/runtime/destructive action.

## Done Criteria

- [x] Every ordered step completed or explicitly skipped with evidence.
- [x] Focused tests and original reproduction pass.
- [x] Actual user-visible or operational outcome inspected.
- [x] Changed files remain inside scope.
- [x] Accepted review findings repaired and reverified.
- [x] Remaining risk and rollback evidence recorded.

## Review Handoff

- Diff base and target: `65da9b107451b09fb93d8dd8340b7d2f6d8f4763` to the final scoped commit.
- Reviewer focus: fail-closed state transitions, safe resume semantics, artifact immutability, independent-judge separation, and absence of external action.
- Known trade-offs: stage outputs add local JSON storage; stage-level resume deliberately reuses prior same-run evidence instead of refreshing it.
- Deliberately deferred work: cron rollout evidence, node-level metrics dashboard, and migration of JobZoom/content publishing/daily intelligence.

## Closeout

- Files/artifacts changed: reusable contract, contract tests, governance document, radar executor, standalone judge, radar/judge tests, operational memory, and this plan.
- Commands/checks and results: Python compilation passed; 7 reusable-contract tests and 26 radar/judge tests passed; plan structure validation passed; whitespace scan passed.
- Deviations from plan: the first live proof exposed an unbounded browser-lock wait before checkpoint allocation. The lock was moved inside `source`/`validate`, bounded at 30 seconds, covered by a regression test, and reverified. CMO shell verification used absolute paths because it is a sibling workspace despite parent-repository path names.
- Evidence of success: valid five-card fixture and standalone CLI judge passed; five broken evidence classes failed closed; injected `extract` crash resumed without rerunning `source`; live run `2026-07-27-1500-recovery-2` persisted lock contention as `blocked` with zero downstream artifacts.
- Residual risk: the approved LinkedIn +30 campaign still owns the authenticated-browser lock, so an unlocked live `approval_required` full-pack sample is deferred until that campaign releases the shared resource. The isolated valid artifact path and live blocked path are both proven.
