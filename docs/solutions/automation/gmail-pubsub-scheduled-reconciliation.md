---
title: "Gmail Pub/Sub sentinel missing scheduled reconciliation"
status: verified
verified_on: 2026-07-21
area: automation
tags: [gmail, pubsub, reconciliation, systemd]
---

# Gmail Pub/Sub Sentinel Missing Scheduled Reconciliation

## Summary

The real-time HR Career Sentinel was healthy, but it depended on Pub/Sub alone and had no scheduled recovery scan. The morning brief separately invoked a deleted scanner and masked its failure. The verified remedy is a serialized, deduplicated inbox reconciliation inside the focused sentinel, scheduled by user systemd at 08:00, 12:00, 16:00, and 20:00 Cairo, plus health-only morning reporting.

## Symptoms

- `hr-career-sentinel.service` is active and its Gmail watch renews, but no cron or timer independently reconciles recent inbox threads.
- `scripts/morning-brief.sh` reports success while its Gmail section contains `Cannot find module .../scripts/gmail-scan.js`.
- Broad legacy Email Agent jobs remain intentionally disabled, so they are not a valid fallback.

## Root cause

The focused Pub/Sub sentinel replaced the legacy broad email workflow, but scheduled reconciliation was not carried forward. The morning brief retained an obsolete direct dependency on `gmail-scan.js`; because the shell script did not fail on that command, the wrapper still recorded a successful brief. These were two separate gaps: missing recovery coverage and misleading health output.

## Failed approaches

- Restoring `gmail-scan.js` would revive an obsolete credential-coupled scanner and would not provide complete-thread policy, durable deduplication, or validated alert delivery.
- Re-enabling `email-agent.py` would violate the focused sentinel architecture and reintroduce broad, noisy inbox processing.
- Running reconciliation concurrently without a shared lock would leave a duplicate-delivery race between the live and scheduled processes.

## Verified solution

1. Add a production `--reconcile` path to `scripts/hr-career-sentinel.py` that searches `in:inbox newer_than:1d`, caps the result at 500, fetches complete threads, and reuses existing policy/state/delivery.
2. Use one exclusive bounded file lock around both live Pub/Sub cycles and scheduled reconciliation (`scripts/hr-career-sentinel.py:178`, `scripts/hr-career-sentinel.py:1179`).
3. Continue past individual thread failures, leave failed messages uncheckpointed, log only sanitized evidence, and return non-zero after the bounded scan (`scripts/hr-career-sentinel.py:1050`).
4. Install `infrastructure/systemd/hr-career-sentinel-reconcile.service` and `.timer`; verify the Cairo calendar before enabling.
5. Replace the morning brief's deleted scanner call with read-only service/timer health (`scripts/morning-brief.sh:46`).
6. Keep the legacy Email Agent disabled. Never add Gmail send, draft, reply, label, flag, trash, or delete capabilities.
7. Before activation, back up the live SQLite database with `.backup` and retain a narrow rollback that removes only the new fallback units.

Stop if the Gmail read path is unavailable, tests fail twice, the timer cannot be verified, or the repair would require Gmail mutation, gateway changes, or revival of legacy email code.

## Evidence

- Source tests passed 22/22, including lock contention, repeated reconciliation dedupe, all-page bounded search, failure continuation, and email-write absence.
- The existing Pub/Sub delivery-ledger regression passed.
- User-systemd verification and the schedule parser confirmed 08:00/12:00/16:00/20:00 `Africa/Cairo`.
- The first live reconciliation processed 110 threads with zero failures and verified two Telegram receipts. Quality review caught one generic public-vacancy false positive; the deterministic sender/subject veto at `scripts/hr-career-sentinel.py:132` and `scripts/hr-career-sentinel.py:362` now suppresses the actual thread.
- The required post-repair live replay scanned 108 already-processed threads, created zero alerts, attempted zero deliveries, and exited 0.
- SQLite integrity was `ok`; zero notifications or alerts were pending, failed, or uncertain; installed unit checksums matched.

## Prevention

- Keep reconciliation tests in `tests/test_hr_career_sentinel.py` and require the existing email-write safety scan.
- Morning reporting should describe owned monitor health, not run a second scanner.
- Every new Gmail ingestion lane must share the sentinel cycle lock or implement an equivalent atomic delivery claim.
- Review the first real catch-up sample for alert quality before treating timer activation as complete.

## When to revisit

Revisit when the one-day inbox exceeds 500 threads, a run approaches the 25-minute or 384 MB limits, Gmail CLI pagination semantics change, Pub/Sub is replaced, or scheduled steady-state runs create new false-positive classes.
