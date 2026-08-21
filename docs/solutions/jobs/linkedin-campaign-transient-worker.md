---
title: "LinkedIn campaign reported active while transient worker was absent"
status: verified
verified_on: 2026-07-19
area: jobs
tags: [linkedin, systemd, campaign-worker, exactly-once]
---

# Replace a Missing Transient LinkedIn Campaign Worker

## Summary

The LinkedIn +30 campaign repeatedly reported an active worker even though its transient systemd unit had unloaded. Recreating the transient unit caused ownership races and did not preserve trustworthy heartbeat or in-flight state. The verified remedy is one installed user service with a single-instance lock, atomic checkpoints, a systemd watchdog, append-only logs, explicit recovery holds, and a shared strict-ledger audit.

## Symptoms

- Campaign reports claim sourcing is active, but the named unit is `not-found`, inactive, and has no supervisor PID.
- The verified ledger count is unchanged for hours while transient units repeatedly appear and disappear.
- Multiple recovery paths can stop or recreate the same dated unit, making status reports stale and risking duplicate candidate work.

## Root cause

The active recovery path used `systemd-run` to create a dated transient service. Stopping that service removed its unit definition, so there was no installed owner for boot persistence, durable status, or a stable restart contract. The supervisor streamed child events but did not persist them, and its counter replayed mechanical gates without the current hard title-level role guard. These were verified from the former restart helper, live unit state, process tree, ledger audit, and pre-change source snapshot.

## Failed approaches

- Recreating the same transient unit: it restored work temporarily but the unit vanished after stop and competing recovery actions could recreate it again.
- Trusting report prose as runtime proof: the report remained optimistic after the service was absent.
- Creating the append-log directory in `ExecStartPre`: systemd opens `StandardOutput=append:` before the pre-start command, producing `209/STDOUT` when the directory does not already exist.

## Verified solution

1. Stop the transient worker only after checking that no candidate is at an application stage. Recheck the ledger hash and process tree immediately afterward.
2. Back up the supervisor, runner, counter, tests, ledgers, cursor, and current unit state to a timestamped directory with a hash manifest.
3. Reconcile the strict count from the campaign ledger. Preserve every factual application, but count only unique rows with submitted proof, ATS at or above 82, a 15-50 KB tailored CV, eligible employment type, and no unambiguous hard role-family rejection.
4. Install `workspace-hr/config/systemd/linkedin-plus30-campaign.service`. Provision `workspace-hr/logs/` and `workspace-hr/state/` before starting because the append target is opened before service commands run.
5. Keep one stable unit and one stable restart helper. The supervisor must use a non-blocking file lock, atomic JSON state, 30-second heartbeat, systemd watchdog notification, child-event checkpoints, and a recovery hold for an interrupted candidate that lacks final ledger proof.
6. Run two bounded `--canary` cycles. Require both to pass and require ledger, blocked-ledger, and cursor hashes to remain unchanged.
7. Start production and verify the installed unit is active/running, enabled, `Restart=on-failure`, watchdog-enabled, and has exactly one supervisor. Require the live `cycle_start.verified` and runner `already_submitted` values to match strict status before accepting recovery.

Stop and roll back if a canary mutates production state, a second supervisor appears, the counter sources disagree, an interrupted candidate lacks proof reconciliation, or any ATS, CV, employment, salary, duplicate, or role-fit gate would need to be weakened.

## Evidence

- `workspace-hr/tools/linkedin-plus30-supervisor.py` contains the lock, heartbeat, checkpoint, canary, recovery-hold, and watchdog-notification behavior.
- `workspace-hr/tools/linkedin_plus30_continue_nasr.py` owns the shared strict-ledger audit and injects recovery holds into duplicate protection.
- `workspace-hr/config/systemd/linkedin-plus30-campaign.service` is the canonical persistent unit.
- `workspace-hr/reports/linkedin-plus30-reliability-record-2026-07-19.md` records the 2/2 canaries, unchanged hashes, live unit proof, reviews, and rollback evidence.
- Live verification on 2026-07-19 showed active/running, zero automatic restarts, a three-minute watchdog, fresh heartbeat, one supervisor, one runner, matching 11/30 counters, and a safely held interrupted candidate with live non-submission proof.

## Prevention

- Never report campaign activity from prose alone. Require unit state, PID, heartbeat freshness, and matching ledger/runner counters.
- Keep the campaign restart helper argument-safe so `--help` and `--status` cannot restart work.
- Search timers, cron, processes, and non-backup source for retired unit names before declaring single ownership.
- Keep interrupted candidates on recovery hold until live submission proof or a safe non-submission state is established.

## When to revisit

Revisit this design if the application runner gains a transactional external idempotency key, LinkedIn exposes a reliable submission-status API, or the campaign is migrated to a workflow engine that natively persists each external-action stage.
