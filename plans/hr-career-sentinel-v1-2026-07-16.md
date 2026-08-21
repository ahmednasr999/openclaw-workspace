# HR Career Sentinel v1 Engineering Plan

## Plan Metadata

- Status: complete
- Owner: NASR/main
- Planned at: commit `7599777` on `2026-07-16`
- Depends on: existing private Gmail Pub/Sub subscription and read-only Gmail OAuth credentials

> **Executor contract:** Read the full plan before editing. Stay inside scope, run each verification gate, and report evidence. If a stop condition is met or reality conflicts with the plan, stop and report the mismatch instead of improvising.

> **Drift check:** `git diff --stat 75997772a72bab22940bd4472dc6be1f587e1e50..HEAD -- scripts/hr-career-sentinel.py tests/test_hr_career_sentinel.py infrastructure/systemd/hr-career-sentinel.service docs/hr-career-sentinel.md`
> If an in-scope path changed, compare current source with the evidence anchors below. Refresh or supersede the plan before execution when the intended change or verification no longer matches.

## Task Contract

- Outcome: build an isolated, production-ready Gmail Pub/Sub workflow that alerts Ahmed only for career or recruitment email requiring attention.
- Constraints and non-goals: never send email; never enable legacy email jobs or the new service; remain silent for non-alerts; classify complete Gmail threads; preserve duplicate and failure state durably.
- Definition of done: dry-run, synthetic classification, duplicate alert, full-thread, silent-output, and failure-safe tests pass; service artifact exists but is not installed, enabled, or running.
- Evidence required: focused test output, source safety scan, systemd disabled/not-found proof, and measured test resources.
- Authority and approval boundary: local reversible files and tests are allowed; Gmail reads are allowed; Telegram test delivery, service installation/enabling, email sends, and other runtime changes are not.
- Stop condition: two failed verification attempts, missing Gmail read path, scope expansion, or a runtime/external write requirement.
- Owner: NASR/main.
- Review tier: high-risk, with a separate adversarial self-review because helper delegation was not requested.

## Objective

- Target outcome: an event-driven HR-only sentinel with durable intake, complete-thread classification, material-change deduplication, and Telegram-only alert delivery.
- User-visible success condition: silence for all non-actionable mail and one structured alert for each materially new actionable recruitment state.
- Why this matters: career email deserves immediate attention while generic inbox traffic must not consume Ahmed's attention.

## Evidence And Current State

- Source anchors: `scripts/gmail-pubsub-pull-worker.py:225` - the existing worker pulls the private Pub/Sub subscription but auto-acks before downstream success.
- Source anchors: `scripts/gmail-pubsub-pull-worker.py:195` - the existing worker's outbound path is Telegram-only.
- Source anchors: `scripts/gmail-pubsub-pull-worker.py:105` - the existing worker durably registers alerts before delivery, a safe pattern to preserve.
- Source anchors: `scripts/email-agent.py:666` - the broad email agent extracts individual-message MIME bodies, not complete Gmail threads.
- Source anchors: `scripts/email-agent.py:956` - the broad agent uses the OpenClaw gateway for structured model classification.
- Existing convention to follow: `scripts/gmail-pubsub-pull-worker.py:79` - write state through a temporary file and atomic replace.
- Reproduction or baseline: `gog gmail thread get <threadId> --full --json` returned a thread object containing every message and MIME payload.
- Raw evidence to preserve: focused test logs and `/usr/bin/time -v` resource output.

## Scope

- In scope: one isolated Python workflow, one isolated SQLite state database at runtime, one systemd unit artifact, tests, fixtures, and operating documentation.
- Files likely touched: `scripts/hr-career-sentinel.py`, `tests/test_hr_career_sentinel.py`, `tests/fixtures/hr-career-sentinel/*`, `infrastructure/systemd/hr-career-sentinel.service`, `docs/hr-career-sentinel.md`.
- Do not touch: all existing email scripts, email state/ledgers, Gmail watch renewal, legacy cron jobs, installed systemd units, Gmail labels/flags, and OpenClaw gateway configuration.
- Non-goals: replying to email, changing Gmail, starting services, and broad inbox triage.

## Authority And Safety

- Permission profile: local-write.
- Approval boundary: do not install, enable, or start the service; do not send Telegram test alerts; do not send or modify email.
- Rollback path: stop/disable the new unit if later installed, remove its installed unit file, reload user systemd, and retain or archive its isolated state directory.
- External/public/credential/paid/runtime action involved: no during implementation; the documented enable command is approval-required.

## Owner And Helpers

- Owning session/agent: NASR/main.
- Helpers, if explicitly permitted: none.
- Independent assignment and expected evidence for each helper: none; perform a separate adversarial self-review.
- Maximum concurrency: 1.

## Ordered Implementation Steps

### Step 1: Build isolated durable intake and full-thread retrieval

- Files: `scripts/hr-career-sentinel.py`.
- Change: persist Pub/Sub notifications before acknowledgement, recover pending work, resolve Gmail history, fetch full threads, and expose a dry-run path.
- Preserve: no email write/send code and no dependency on broad email state.
- Verify command/check: focused unit tests with mocked Pub/Sub and Gmail CLI runners.
- Expected result: notification survives failure and each classification receives all thread messages.

### Step 2: Add recruitment-only classification and alert materialization

- Files: `scripts/hr-career-sentinel.py`, fixtures.
- Change: deterministic noise guard plus medium/high structured classification, strict validation, active-process rejection rule, required alert fields, and material-state hash.
- Preserve: default silence and explicit-approval-only replies.
- Verify command/check: synthetic regression, full-thread, and silent-output tests.
- Expected result: only enumerated attention classes create alerts.

### Step 3: Add deduplicated Telegram delivery and failure-safe retries

- Files: `scripts/hr-career-sentinel.py`, tests.
- Change: persist pending alerts before Telegram delivery and deduplicate by Gmail message ID, thread ID, and material event state.
- Preserve: no email send or draft capabilities.
- Verify command/check: duplicate and delivery-failure tests.
- Expected result: unchanged events alert once; changed states alert once more; failures stay pending.

### Step 4: Add disabled production unit and runbook

- Files: `infrastructure/systemd/hr-career-sentinel.service`, `docs/hr-career-sentinel.md`.
- Change: define a hardened disabled service artifact, exact enable command, and rollback command.
- Preserve: legacy service/timer states and all installed units.
- Verify command/check: `systemd-analyze verify` plus live `systemctl` state checks.
- Expected result: valid unit artifact and no running/enabled HR Career Sentinel.

## Test Plan

- Existing tests to run: `python3 scripts/test-gmail-pubsub-pull-worker.py` as reuse-regression evidence.
- New or changed tests: `python3 -m unittest -v tests.test_hr_career_sentinel`.
- Original reproduction after implementation: fixture with a later rejection and earlier interview message in the same thread must alert; a pre-interview rejection must remain silent.
- Actual artifact or behavior to inspect: rendered alert fields, SQLite rows, empty stdout on silent paths, forbidden-capability source scan, and installed service state.

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

- Diff base and target: `7599777` to working tree, restricted to the in-scope files.
- Reviewer focus: false positives, full-thread proof, duplicate races, failure checkpoint order, email-send impossibility, and service disabled state.
- Known trade-offs: model classification depends on the local OpenClaw gateway; model failures remain silent and retry rather than guessing.
- Deliberately deferred work: production enablement and real Telegram delivery.

## Closeout

- Files/artifacts changed: `scripts/hr-career-sentinel.py`, `tests/test_hr_career_sentinel.py`, `infrastructure/systemd/hr-career-sentinel.service`, `docs/hr-career-sentinel.md`, and this plan.
- Commands/checks and results: 17/17 sentinel tests passed; existing Gmail Pub/Sub ledger test passed; Python compilation, `git diff --check`, plan validation, and systemd unit verification passed; focused test peak RSS was 27,520 KB.
- Deviations from plan: the first one-day live dry run attempted 190 recent threads and hit its 10-minute cap. Dry-run sampling and initial recovery were repaired to use a configurable limit and a two-sided Pub/Sub publish-time window. A second live dry run completed in 4.8 seconds and correctly suppressed a real newsletter. A live medium-reasoning synthetic interview classification returned an attention decision without delivery.
- Evidence of success: no installed unit exists; `hr-career-sentinel.service` is `not-found`/inactive; legacy `gog-gmail-watch.service` remains disabled/inactive; all alert, ignore, full-thread, dedupe, dry-run, reasoning-tier, source-safety, and failure tests pass.
- Residual risk: production Gmail and Telegram delivery remain intentionally untested because service activation and a real alert would cross the runtime/external-write boundary. Ambiguous Telegram success is held as `uncertain` instead of retried, prioritizing duplicate prevention over automatic recovery.

## Production Activation - 2026-07-17

- Ahmed explicitly approved enabling HR Career Sentinel.
- The activation preflight passed: 17/17 Sentinel tests, Gmail Pub/Sub ledger regression, systemd unit validation, and Memory Heist security suite 19/19.
- The pre-state check found the reviewed unit already installed, enabled, and active since 00:24:48 Cairo. Its installed checksum exactly matched the repository unit, so no blind overwrite or restart was performed.
- Live verification: active/running, zero restarts, SQLite integrity `ok`, 32 notifications completed, two messages and two thread states recorded, zero notification errors, zero alert errors, and no alerts emitted.
- Resource verification: peak memory 119,758,848 bytes under the 384 MB limit; one idle task and no warning-or-higher journal entries.
- Isolation verification: both legacy Email Agent schedules, Email Health Card, Email Hygiene, Email Synthetic Regression, OpenClaw Health Guard, `gog-gmail-watch.service`, and `gog-calendar-watch.service` remain disabled/inactive. The Gmail watch-renewal timer remains enabled.
- Model verification: Sentinel explicitly requests `openai/gpt-5.6-sol`; deterministic tests cover medium/high reasoning selection. No model, router, gateway, cron, or Telegram configuration was changed.
- Live model smoke verification classified a synthetic interview request as `interview_invited` with medium reasoning, 99% confidence, a Friday deadline, and attention required. The classifier was called directly; no Telegram message or Gmail mutation occurred.
- Post-activation security gate passed again at 19/19.
