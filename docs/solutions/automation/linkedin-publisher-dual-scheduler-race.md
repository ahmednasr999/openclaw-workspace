---
title: "LinkedIn publisher dual-scheduler race"
status: verified
verified_on: 2026-07-21
area: automation
tags: [linkedin, publishing, cron, concurrency, idempotency]
---

# LinkedIn Publisher Dual-Scheduler Race

## Summary

The same approved LinkedIn post was published twice because an OS cron and an OpenClaw cron started the same publisher at 09:30. Both processes passed the ledger and Notion duplicate checks before either process completed writeback. The remedy was to disable the duplicate OpenClaw scheduler, retain one OS-cron owner, and serialize the publisher's full check-to-writeback transaction with a shared file lock.

## Symptoms

- Two LinkedIn share IDs are created for the same title, text, image, page ID, and planned date within seconds.
- The success ledger contains two entries for the same page and date.
- Scheduler inspection shows two enabled jobs calling `post_scheduled_notion_linkedin.py` at the same minute.

## Root cause

This was a proven time-of-check/time-of-use race. The OS crontab and OpenClaw cron job `165989bc-b630-48a7-b097-169f7d75967d` both invoked the same script at 09:30 Cairo. The existing duplicate guard checked the success ledger and Notion before publication, but those checks were not protected by a lock shared across both scheduler systems. Both processes therefore observed a publishable row and performed the external write.

## Failed approaches

- Scheduler-level locking alone was incomplete. The OS wrapper had its own lock, but the OpenClaw command job did not use that lock, so the two scheduler systems could still run concurrently.
- Ledger and Notion prechecks alone were insufficient because both processes could read the same pre-write state.

## Verified solution

1. Identify every scheduler that calls the publisher using `openclaw cron list --all --json` and `crontab -l`.
2. Keep one authoritative scheduler. In this incident, the OS cron remained active and the duplicate OpenClaw job was disabled. Re-enable the disabled job only if the OS owner is deliberately retired.
3. Hold `/var/lock/openclaw/cmo-notion-linkedin-post.publisher.lock` across the complete ledger check, Notion resolution, external publish, and writeback transaction. The guard is implemented in `workspace-cmo/scripts/post_scheduled_notion_linkedin.py:184`.
4. Verify syntax, run a non-publishing invocation for an already-posted date, confirm exactly one scheduler remains enabled, and verify the source row points to the intended canonical post.
5. Treat deletion of an already-live duplicate as a separate destructive public action. Obtain Ahmed's explicit approval before deletion.

Rollback: remove the in-script lock only if the publisher moves to a transactional single-owner queue that provides an equivalent cross-trigger concurrency guarantee. If the lock cannot be created or acquired, stop publishing rather than bypass it.

## Evidence

- The OS cron log recorded share `7485219557943644161`; the OpenClaw cron diagnostics recorded share `7485219556194512896` from the same script and scheduled minute.
- The success ledger recorded both shares for the same page and planned date one second apart.
- `openclaw cron get 165989bc-b630-48a7-b097-169f7d75967d` verified `enabled: false` after remediation.
- `crontab -l` showed exactly one remaining `cmo-notion-linkedin-post` entry.
- `python3 -m py_compile` passed, and a dry run for 2026-07-21 returned `already_published_for_date` without an external write.
- The live Notion preflight reported the row as `Posted` with canonical share `7485219557943644161`.

## Prevention

- Enforce one scheduler owner per external publishing workflow.
- Keep the transaction-wide file lock even when a scheduler wrapper also has a lock.
- During cron audits, flag multiple enabled jobs whose payloads resolve to the same external publisher.
- Keep the success ledger and Notion writeback checks inside the lock; neither is a substitute for concurrency control.

## When to revisit

Revisit when publishing moves away from local Linux processes, when more than one host can publish, or when the workflow gains a transactional queue or distributed lock. A local `flock` does not coordinate across hosts.
