# Governed Quality and Evidence Phase

## Plan Metadata

- Status: complete
- Owner: NASR
- Planned at: commit `ef2a24863` on `2026-07-18`
- Depends on: `docs/agent-governance/governed-outcome-loops-2026-07-18.md`

> **Executor contract:** Read the full plan before editing. Stay inside scope, run each verification gate, and report evidence. If a stop condition is met or reality conflicts with the plan, stop and report the mismatch instead of improvising.

> **Drift check:** `git diff --stat ef2a24863..HEAD -- workspace-jobzoom/scripts workspace-jobzoom/tests workspace-cmo/scripts workspace-cmo/tests workspace-cmo/config plans/governed-quality-evidence-phase-2026-07-18.md`

## Objective

- Target outcome: start a 30-day quality-and-evidence phase with resilient JobZoom scoring, prospective application segmentation, a three-clean-run gate, a three-post weekly LinkedIn cadence, one six-post hook cohort, and weekly evidence review.
- User-visible success condition: production controls are installed and verified without reducing JobZoom scan coverage, publishing a post, changing scoring policy, or enabling automatic adaptation.
- Why this matters: the current evidence shows high activity but weak grounded outcomes, and the latest JobZoom run wasted 21 calls retrying a stale credential.

## Evidence And Current State

- Source anchors: `/root/.openclaw/workspace-jobzoom/scripts/daily_run.py:396` - gateway requests use one import-time token and record HTTP success before validating scoring JSON.
- Source anchors: `/root/.openclaw/workspace-jobzoom/scripts/daily_run.py:786` - every batch retries three times even when the error is repeated HTTP 401.
- Source anchors: `/root/.openclaw/workspace-jobzoom/scripts/jobzoom_governed_outcomes.py:145` - the verifier evaluates only the latest run and does not enforce a three-clean-run streak.
- Source anchors: `/root/.openclaw/workspace-cmo/scripts/cmo_governed_outcomes.py:111` - cadence is already measured against a maximum of four posts per seven days.
- Source anchors: `/root/.openclaw/workspace/config/root-crontab.managed:77` - the publisher runs daily but posts only when Notion contains an approved row for that date.
- Existing convention to follow: additive, idempotent evidence fields; manual-only adaptation; deterministic verification before scheduling.
- Reproduction or baseline: 21 JobZoom `batch_scoring` failures on 2026-07-18 were HTTP 401; the July 8-18 LinkedIn baseline has 11 posts and seven posts in seven days.
- Raw evidence to preserve: JobZoom SQLite database, Notion page IDs/status/date/title snapshot, LinkedIn metrics CSV, existing cron definition.

## Scope

- In scope: JobZoom gateway/token resilience, strict scoring-response validation, clean-run streak, derived prospective cohort segments, CMO experiment registry, metrics cohort attribution, Notion date spacing for six already-approved posts, and the existing weekly CMO review instructions.
- Files likely touched: JobZoom scorer/verifier/tests; CMO metrics/verifier/config/tests; one Notion reschedule utility; this plan; current memory note; the existing CMO weekly cron payload.
- Do not touch: JobZoom search titles/countries/150-search scope, scoring weights/prompts/thresholds, CV content rules, public LinkedIn posts, gateway configuration, model routing, credentials, application submission behavior, or automatic adaptation.
- Non-goals: dynamic graph rewriting, a new agent, a new model, historical causal claims, or automatic content optimization.

## Authority And Safety

- Permission profile: local-write plus the explicitly approved Notion cadence change and existing cron-message edit.
- Approval boundary: no public post, message to a third party, application, gateway restart/config edit, credential change, destructive action, or automatic optimization.
- Rollback path: restore changed source files from the pre-change diff; restore the six Notion page dates from the captured before snapshot; restore the previous cron message from `openclaw cron get` evidence.
- External/public/credential/paid/runtime action involved: yes, limited to reversible Notion date updates and one existing cron payload edit; both are within Ahmed's “Go ahead” authorization for the stated recommendations.

## Owner And Helpers

- Owning session/agent: NASR
- Helpers, if explicitly permitted: none
- Independent assignment and expected evidence for each helper: not applicable
- Maximum concurrency: 1

## Ordered Implementation Steps

### Step 1: Make JobZoom scoring fail boundedly and validate real output

- Files: `workspace-jobzoom/scripts/daily_run.py`, focused tests.
- Change: reload gateway credentials per request, retry once only when a rotated token is detected, circuit-break unchanged 401/403 failures, validate complete parseable score JSON, and retry malformed/non-JSON scoring responses at most twice.
- Preserve: full scan, model, prompt, score weights, threshold, quota behavior, and keyword fallback.
- Verify command/check: focused unit tests plus a mock stale-token recovery and malformed-response reproduction.
- Expected result: stale auth cannot create one failure per batch; HTTP 200 with invalid/incomplete scores is recorded as failure and rescored.

### Step 2: Add prospective job-outcome evidence and a three-clean-run gate

- Files: `workspace-jobzoom/scripts/jobzoom_governed_outcomes.py`, tests.
- Change: derive prospective cohort segments from existing canonical evidence and expose country, role family, source, ATS band, company type coverage, and CV version; require three consecutive clean daily runs before reliability is declared proven.
- Preserve: read-only verifier behavior and historical attribution evidence.
- Verify command/check: fixture tests and a real read-only report.
- Expected result: the current state remains warning until three clean runs exist, and missing segmentation is visible rather than fabricated.

### Step 3: Establish the six-post CMO hook experiment and 3-post weekly cadence

- Files: CMO experiment config, metrics sync, verifier, reschedule utility, tests; six existing Notion pages.
- Change: keep text bodies and visuals fixed, label the current executive-tension openings as one prospective cohort, space the six approved posts across Sunday/Tuesday/Thursday on 19, 21, 23, 26, 28, and 30 July, and auto-attribute published rows to the registry.
- Preserve: approval status, post order, one-post-per-day, publisher time, visual identity, and public posting gate.
- Verify command/check: dry-run, captured before snapshot, apply, live Notion re-read, publisher dry-runs, cohort sync fixture.
- Expected result: exactly three scheduled posts per seven-day cycle, no collisions, and no post published during implementation.

### Step 4: Make weekly evidence review operational

- Files: existing CMO weekly cron payload and local review artifacts.
- Change: instruct the Friday report to collect author-visible analytics through the approved Ahmed-Mac lane when available, skip rather than substitute when offline, run both CMO reports, and keep all recommendations manual-only.
- Preserve: schedule, model, reasoning level, delivery target, and no-publish/no-schedule boundary.
- Verify command/check: `openclaw cron get`, scheduler status, payload inspection, and local deterministic reports.
- Expected result: one owned weekly review requests/captures missing evidence without adding another agent or cron job.

## Test Plan

- Existing tests to run: all JobZoom tests and all CMO governed-outcome/post-approval tests.
- New or changed tests: auth refresh/circuit breaker, strict JSON completeness, clean streak, prospective segmentation, experiment registry attribution, cadence dates, and manual-only gates.
- Original reproduction after implementation: simulate unchanged 401 and confirm one scoring request then run-level fallback; simulate malformed HTTP 200 then valid JSON and confirm rescore.
- Actual artifact or behavior to inspect: real JobZoom governed report, real CMO governed report, live Notion schedule, existing weekly cron definition.

## Stop Conditions

- An evidence anchor or in-scope file has materially drifted.
- A required dependency or approval is missing.
- A verification gate fails twice after bounded repair.
- The smallest credible fix requires a gateway/config restart, a public post, a new credential, destructive action, or reduced JobZoom scan coverage.

## Done Criteria

- [x] Every ordered step completed or explicitly skipped with evidence.
- [x] Focused tests and original reproduction pass.
- [x] Actual user-visible or operational outcome inspected.
- [x] Changed files remain inside scope.
- [x] Accepted review findings repaired and reverified.
- [x] Remaining risk and rollback evidence recorded.

## Review Handoff

- Diff base and target: `ef2a24863` to working tree.
- Reviewer focus: fail-closed auth/JSON behavior, no reduced search scope, no automatic adaptation, exact Notion cadence, and no accidental public action.
- Known trade-offs: company type may remain unclassified until evidence exists; historical application cohorts remain mixed and are not used for causal optimization.
- Deliberately deferred work: automatic content/job targeting changes and dynamic graph rewriting.

## Closeout

- Files/artifacts changed: JobZoom runner, governed verifier, and focused tests; CMO experiment registry, Notion apply utility, publisher resolver, metrics/verifier, heartbeat policy, tests, weekly cron skill, and this plan. Six approved Notion rows were reversibly rescheduled; the existing Friday cron payload was updated without changing its schedule, model, owner, or delivery.
- Commands/checks and results: Python compilation passed; 19 focused JobZoom tests passed; 26 CMO tests passed; JobZoom SQLite integrity returned `ok`; six live publisher candidate checks returned valid Scheduled rows with page-specific assets and no post URL; CMO heartbeat returned no cadence or reconciliation incident; cron skill validation and scheduler status passed.
- Deviations from plan: the production scoring health probe timed out, so reliability remains warning at 0/3. Repository-wide JobZoom discovery also exposes five pre-existing stale v2-policy tests for functions absent before this phase; these were not expanded into this task.
- Evidence of success: stale-auth retries are bounded, malformed scoring output cannot count as success, three distinct clean days are required, the prospective cohort waits through its outcome-maturity window, six experiment posts are fixed at three weekly, metrics are cohort-attributed, and automatic adaptation remains disabled.
- Review: two isolated GPT-5.6 Sol structured passes found 18 concrete defects; all accepted findings were repaired. Deterministic suites were rerun after the final bounded repair.
- Residual risk: prove the controls on the next three production JobZoom days, complete the 6-post experiment and August 6 review, and wait through August 31 before any prospective targeting change. Rollback uses the captured Notion before snapshot, prior cron evidence, and source diffs.
