# HR Career Sentinel Scheduled Reconciliation Plan

## Plan Metadata

- Status: complete
- Owner: NASR/main
- Planned at: commit `f61afb3fa` on `2026-07-21`
- Depends on: `plans/hr-career-sentinel-v1-2026-07-16.md`

> **Executor contract:** Read the full plan before editing. Stay inside scope, run each verification gate, and report evidence. If a stop condition is met or reality conflicts with the plan, stop and report the mismatch instead of improvising.

> **Drift check:** `git diff --stat f61afb3fa..HEAD -- scripts/hr-career-sentinel.py tests/test_hr_career_sentinel.py infrastructure/systemd/hr-career-sentinel-reconcile.service infrastructure/systemd/hr-career-sentinel-reconcile.timer scripts/morning-brief.sh docs/hr-career-sentinel.md`
> If an in-scope path changed, compare current source with the evidence anchors below. Refresh or supersede the plan before execution when the intended change or verification no longer matches.

## Objective

- Target outcome: retain the live Pub/Sub career sentinel and add a bounded scheduled Gmail reconciliation at 08:00, 12:00, 16:00, and 20:00 Cairo.
- User-visible success condition: career email remains real-time when Pub/Sub is healthy, missed Pub/Sub events are caught within the scheduled fallback windows, duplicate alerts are prevented, and the morning brief no longer records a missing-scanner error.
- Why this matters: interview and recruiter messages must not depend on one delivery mechanism, while generic inbox traffic must remain silent.

## Evidence And Current State

- Source anchors: `scripts/hr-career-sentinel.py:895` - complete threads already pass through deterministic noise guards, strict model policy, and message/thread/material-state deduplication.
- Source anchors: `scripts/hr-career-sentinel.py:955` - pending Telegram alerts are durable and receipt-validated before being marked delivered.
- Source anchors: `scripts/hr-career-sentinel.py:1021` - the current CLI has Pub/Sub production and side-effect-free dry-run modes but no production reconciliation mode.
- Source anchors: `scripts/morning-brief.sh:46` - the morning brief invokes the absent `scripts/gmail-scan.js` and masks the resulting failure.
- Source anchors: `docs/hr-career-sentinel.md:97` - the broad legacy Email Agent remains intentionally disabled and must not be restored.
- Existing convention to follow: `infrastructure/systemd/hr-career-sentinel.service:1` - use the same Gmail credential environment, hardening, paths, and resource limits for the one-shot fallback.
- Reproduction or baseline: `scripts/gmail-scan.js` is absent; no scheduled reconciliation unit or crontab entry exists; the 2026-07-21 morning brief log contains the missing-module error while returning success.
- Raw evidence to preserve: pre-change service/timer state, SQLite integrity/counts, focused test output, live reconciliation log entry, installed unit checksums, and next timer elapse.

## Scope

- In scope: production reconciliation mode, cross-process cycle serialization, focused tests, one-shot service/timer artifacts, morning-brief health reporting, operating documentation, live installation, one controlled sentinel restart, and verification.
- Files likely touched: `scripts/hr-career-sentinel.py`, `tests/test_hr_career_sentinel.py`, `infrastructure/systemd/hr-career-sentinel-reconcile.service`, `infrastructure/systemd/hr-career-sentinel-reconcile.timer`, `scripts/morning-brief.sh`, `docs/hr-career-sentinel.md`, this plan, the high-risk evidence record, one canonical solution note, and today's daily note.
- Do not touch: legacy `email-agent.py` schedules/state, Gmail labels or messages, Gmail watch renewal, OpenClaw gateway/configuration, model selection, alert policy, Telegram target, unrelated cron jobs, or unrelated dirty-worktree changes.
- Non-goals: inbox triage, Notion email synchronization, email replies/drafts/sends, generic job-alert reporting, or restoring `gmail-scan.js`.

## Authority And Safety

- Permission profile: runtime-change.
- Approval boundary: Ahmed's `Go ahead` explicitly approves this named Gmail fallback repair. No email mutation, third-party message, gateway restart, public action, paid action, or destructive cleanup is authorized.
- Rollback path: disable and remove only the reconciliation timer/service, restore the pre-change sentinel source and installed unit from the dated backup, restart only `hr-career-sentinel.service`, and retain the SQLite database unless a separate data decision is made.
- External/public/credential/paid/runtime action involved: yes - read-only Gmail access, possible pre-approved Telegram alert to Ahmed when a real actionable thread is found, installation of two user-systemd units, timer enablement, and one sentinel service restart.

## Owner And Helpers

- Owning session/agent: NASR/main.
- Helpers, if explicitly permitted: none.
- Independent assignment and expected evidence for each helper: none; perform two distinct local review passes because delegation was not requested.
- Maximum concurrency: 1.

## Ordered Implementation Steps

### Step 1: Add a serialized reconciliation path

- Files: `scripts/hr-career-sentinel.py`, `tests/test_hr_career_sentinel.py`.
- Change: add an exclusive bounded cycle lock shared by live and scheduled processes; add a production reconciliation mode that searches up to 500 threads from the last day, processes only unseen messages through existing policy, continues across individual failures, logs a sanitized summary, and delivers durable alerts.
- Preserve: complete-thread classification, material-state dedupe, default silence, GPT-5.6 Sol, retry semantics, and absence of email-write capability.
- Verify command/check: focused unit tests, Python compilation, source safety scan, and a lock-contention test.
- Expected result: new messages are processed once, repeated reconciliation is a no-op, failures remain uncheckpointed and cause a non-zero one-shot result, and concurrent alert delivery is serialized.

### Step 2: Add the four-times-daily systemd fallback

- Files: `infrastructure/systemd/hr-career-sentinel-reconcile.service`, `infrastructure/systemd/hr-career-sentinel-reconcile.timer`, `docs/hr-career-sentinel.md`.
- Change: create a hardened one-shot service using the existing secure Gmail environment and a Cairo timer at 08:00/12:00/16:00/20:00 with persistence.
- Preserve: the continuous Pub/Sub service and daily watch-renewal timer.
- Verify command/check: `systemd-analyze --user verify`, `systemd-analyze calendar`, installed checksum comparison, enabled/active timer state, and next elapse.
- Expected result: one owner, bounded execution, persistent logs in the sentinel JSONL file and systemd journal, and no duplicate legacy schedules.

### Step 3: Remove the broken morning-brief dependency

- Files: `scripts/morning-brief.sh`.
- Change: replace the deleted scanner invocation with read-only health lines for the real-time sentinel and reconciliation timer.
- Preserve: job radar, calendar, memory append, and existing morning-brief delivery behavior.
- Verify command/check: Bash syntax check plus an isolated run of the Gmail health block.
- Expected result: the brief cannot emit the missing-module error and accurately distinguishes active versus unavailable monitor lanes.

### Step 4: Activate and verify production behavior

- Files: installed user-systemd units and the existing sentinel runtime; repository docs/evidence only.
- Change: back up the live SQLite database and installed service, install the two reviewed unit artifacts, reload user systemd, restart only the sentinel to load serialization, enable the timer, and run one controlled reconciliation.
- Preserve: gateway, Gmail watch renewal, other services/timers, and all mailbox content.
- Verify command/check: SQLite integrity/counts, service PID/start time, no warning-or-higher journal entries, reconciliation log summary, zero pending notification errors, timer next elapse, and current Gmail read path.
- Expected result: both lanes are healthy, the fallback completes successfully, and any alert is sent only through the existing validated policy.

## Test Plan

- Existing tests to run: `python3 -m unittest -v tests/test_hr_career_sentinel.py`; `python3 scripts/test-gmail-pubsub-pull-worker.py`.
- New or changed tests: reconciliation dedupe, per-thread failure handling, Gmail all-pages bounded search, CLI exclusivity, and cycle-lock contention.
- Original reproduction after implementation: run the morning-brief Gmail health block with `scripts/gmail-scan.js` still absent and confirm no missing-module text; run the live one-shot reconciliation and confirm a successful sanitized `reconciliation_completed` record.
- Actual artifact or behavior to inspect: installed unit contents/checksums, timer schedule/next run, live service state, SQLite integrity and pending rows, operational log tail, and morning-brief health text.

## Stop Conditions

- An evidence anchor or in-scope file has materially drifted.
- A required dependency or approval is missing.
- A verification gate fails twice after bounded repair.
- The smallest credible fix requires out-of-scope files or a new external/runtime/destructive action.
- A live reconciliation would require restoring legacy email code, changing the model, or mutating Gmail.

## Done Criteria

- [x] Every ordered step completed or explicitly skipped with evidence.
- [x] Focused tests and original reproduction pass.
- [x] Actual user-visible or operational outcome inspected.
- [x] Changed files remain inside scope.
- [x] Accepted review findings repaired and reverified.
- [x] Remaining risk and rollback evidence recorded.

## Review Handoff

- Diff base and target: `f61afb3fa` to working tree, restricted to the in-scope paths.
- Reviewer focus: cross-process duplicate prevention, retry/checkpoint ordering, scheduled coverage, timer timezone/persistence, credential handling, email-write impossibility, and rollback.
- Known trade-offs: the fallback fetches complete recent threads but dedupes already processed messages before model classification; it may temporarily serialize the live loop while reconciling.
- Deliberately deferred work: broad inbox summaries, Notion sync, Gmail mutations, and any revival of the legacy Email Agent.

## Closeout

- Files/artifacts changed: sentinel source/tests, two systemd artifacts, morning-brief health block, operating documentation, high-risk evidence, canonical solution note, and daily/error records. Two user-systemd artifacts were installed and the existing sentinel was restarted twice to load accepted repairs.
- Commands/checks and results: 22/22 sentinel tests passed twice; the Gmail Pub/Sub ledger regression passed twice; Python, Bash, systemd, calendar, plan, record, solution, and diff checks passed; the live Gmail query returned 110 inbox threads within the 500-thread cap.
- Deviations from plan: the first live catch-up surfaced a public-vacancy false positive in addition to a valid Cyberani verification alert. The delivered false alert was not deleted. A deterministic automated-vacancy veto was added, proved against the actual thread, and followed by the required live replay.
- Evidence of success: first reconciliation processed 110 threads with no failures and delivered two durable alerts; the post-repair replay scanned 108 already-processed threads, created no alerts, and exited successfully. The primary service is active with zero restarts, the timer is enabled/active with next elapse at 12:00 Cairo, installed checksums match, SQLite integrity is `ok`, and there are zero pending/failed notifications or pending/uncertain alerts.
- Residual risk: the initial backlog run took about 10.5 minutes and peaked at 339.4 MB because it classified 110 unseen threads and delivered two alerts. The steady-state replay took about 1.4 minutes and peaked at 36.9 MB. The 25-minute timeout, 384 MB cap, and 500-thread bound remain the stop limits to monitor.
