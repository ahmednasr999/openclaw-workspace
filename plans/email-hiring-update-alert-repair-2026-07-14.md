# Email Hiring-Update Alert Repair

## Plan Metadata

- Status: complete
- Owner: NASR/main
- Planned at: commit `f3f54c443` on `2026-07-14`
- Depends on: none

> **Executor contract:** Read the full plan before editing. Stay inside scope, run each verification gate, and report evidence. If a stop condition is met or reality conflicts with the plan, stop and report the mismatch instead of improvising.

> **Drift check:** `git diff --stat f3f54c443..HEAD -- scripts/format-email-alert.py scripts/gmail-pubsub-pull-worker.py scripts/test-email-agent.py scripts/email-synthetic-harness.py`
> If an in-scope path changed, compare current source with the evidence anchors below. Refresh or supersede the plan before execution when the intended change or verification no longer matches.

## Objective

- Target outcome: surface high-importance hiring-process emails immediately on Telegram even when no email reply is required, using structured delivery fields and a durable retry ledger.
- User-visible success condition: Miriam's real failure pattern becomes a `📌 Hiring process update` alert; action requests remain `🚨`; noise stays silent; failed Telegram delivery remains pending and is retried.
- Why this matters: the current watcher detects important hiring mail but discards it when `action=no_action`, then advances the mailbox UID and later reports a misleading all-clear status.

## Evidence And Current State

- Source anchors: `scripts/gmail-pubsub-pull-worker.py:81` - the watcher branches on formatted text starting with `🚨 Email alert`.
- Source anchors: `scripts/gmail-pubsub-pull-worker.py:87` - the worker's only delivery path is Telegram through `openclaw message send`.
- Source anchors: `scripts/format-email-alert.py:153` - `no_action` and `read_and_file` items are vetoed from actionable alerts.
- Source anchors: `scripts/format-email-alert.py:289` - an empty actionable set is rendered as `all clear` regardless of a high-importance pipeline update.
- Existing convention to follow: `scripts/format-email-alert.py:129` - normalize and deduplicate items before presentation.
- Reproduction or baseline: a synthetic summary matching email `364923`, high priority, Sprinklr pipeline match, and LLM `action=no_action` renders `📬 Email scan: all clear`.
- Raw evidence to preserve: `data/email-history.jsonl` and `logs/gmail-pubsub-pull.log`; do not rewrite either.

## Scope

- In scope: structured action/update/no-notification output, accurate scan wording, durable Telegram delivery ledger, receipt validation, bounded retry, regression tests, watcher restart and verification.
- Files likely touched: `scripts/format-email-alert.py`, `scripts/gmail-pubsub-pull-worker.py`, `scripts/test-email-agent.py`, `scripts/email-synthetic-harness.py`, this plan, the high-risk record, daily memory, and one canonical solution document after verification.
- Do not touch: Gmail credentials, SMTP configuration, email compose/reply/send paths, gateway configuration, mailbox UID history, unrelated dirty files.
- Non-goals: redesigning the classifier, sending or drafting email, changing cron schedules, changing the OpenClaw gateway.

## Authority And Safety

- Permission profile: local-write and approved runtime-change for `gog-gmail-watch.service` only.
- Approval boundary: Ahmed explicitly approved implementing the repair and controlled watcher restart; any email send/reply remains forbidden without separate clear approval.
- Rollback path: restore the pre-change copies of the two runtime scripts, rerun focused tests, and restart only `gog-gmail-watch.service`.
- External/public/credential/paid/runtime action involved: yes, Telegram alerts to Ahmed and one approved watcher-service restart; no email or third-party messaging.

## Owner And Helpers

- Owning session/agent: NASR/main
- Helpers, if explicitly permitted: none
- Independent assignment and expected evidence for each helper: none
- Maximum concurrency: 1

## Ordered Implementation Steps

### Step 1: Produce structured notification envelopes

- Files: `scripts/format-email-alert.py`
- Change: classify outputs as `action_required`, `hiring_process_update`, or `none`; include `importance`, `action_required`, `pipeline_match`, stable email keys, and Telegram text; preserve plain-text CLI compatibility.
- Preserve: body-aware noise veto, MIME cleanup, existing urgent action behavior, and no email delivery code.
- Verify command/check: run formatter unit tests and replay Miriam, reschedule, cancellation, feedback, rejection, action-request, and newsletter fixtures.
- Expected result: important pipeline updates are surfaced even when no reply is needed, while noise remains non-notifiable.

### Step 2: Add durable alert delivery and recovery

- Files: `scripts/gmail-pubsub-pull-worker.py`
- Change: consume formatter JSON instead of text prefixes, persist pending alerts before Telegram delivery, validate `ok=true` plus a non-empty `messageId`, mark delivered only after proof, and retry pending alerts with bounded backoff.
- Preserve: Pub/Sub polling, IMAP scan gate, Telegram-only outbound delivery, and scheduled IMAP fallback.
- Verify command/check: isolated temp-ledger tests with mocked command results for success, failure, dedupe, and recovery.
- Expected result: mailbox state advancement cannot erase an undelivered high-importance alert.

### Step 3: Verify and deploy the narrow runtime change

- Files: service process only; no service-unit change expected.
- Change: back up runtime scripts, run syntax and focused tests, perform two local review passes, restart `gog-gmail-watch.service`, and inspect status/log/state.
- Preserve: OpenClaw gateway process and configuration.
- Verify command/check: `systemctl --user is-active gog-gmail-watch.service`, MainPID/start timestamp change, worker state healthy, and no new service errors.
- Expected result: repaired worker is live without a gateway restart.

## Test Plan

- Existing tests to run: `python3 scripts/test-email-agent.py`; `python3 scripts/email-synthetic-harness.py --verbose`.
- New or changed tests: structured formatter envelopes; real missed-email replay; hiring update variants; ledger pending/delivered/retry/dedupe; receipt validation; static no-email-send guard.
- Original reproduction after implementation: replay UID `364923` summary and assert `type=hiring_process_update`, `action_required=false`, `pipeline_match=Sprinklr`, and text begins `📌 Hiring process update`.
- Actual artifact or behavior to inspect: ledger JSON in a temporary test directory and live watcher service health after restart; no test sends Telegram or email.

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

- Diff base and target: `f3f54c443` to working tree, limited to in-scope files.
- Reviewer focus: correctness/deduplication first; permissions/recovery/observability second.
- Known trade-offs: pipeline-match is the deterministic proxy for an active hiring process; the classifier remains responsible for establishing that match.
- Deliberately deferred work: classifier redesign and cron schedule changes.

## Closeout

- Files/artifacts changed: formatter, watcher, formatter/core/synthetic/ledger tests, plan, high-risk record, daily note, and canonical solution document. Runtime state added the new delivery ledger and refreshed watcher health state.
- Commands/checks and results: Python compilation passed; worker ledger test passed; synthetic harness passed; core email suite passed 59/59; plan, high-risk record, and solution validators passed; systemd and gateway checks passed.
- Deviations from plan: added a dedicated isolated worker-ledger test and periodic summary reconciliation after Review A exposed a crash-gap recovery risk.
- Evidence of success: missed Sprinklr replay produced `hiring_process_update`, `importance=high`, `action_required=false`, `pipeline_matches=[Sprinklr]`, and `email_keys=[id:364923]`; watcher restarted with a new PID and reached healthy idle with zero pending alerts.
- Residual risk: no synthetic Telegram alert was sent to Ahmed to avoid a false user-visible notification; the real Telegram receipt schema is already proven by prior deliveries and is now fail-closed in code. The next genuine qualifying email will exercise the new live branch.
