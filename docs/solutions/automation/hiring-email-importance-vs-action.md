---
title: "Hiring email alerts require separate action delivery and grounded pipeline matching"
status: verified
verified_on: 2026-07-15
area: automation
tags: [gmail, pubsub, telegram, hiring-alerts, delivery-ledger]
---

# Separate Hiring-Email Importance From Required Action

## Summary

The real-time Gmail watcher first suppressed an important active-pipeline interview update because the email required no reply. After structured update delivery was added, a second defect surfaced: compact substring matching let active company `TP` match the joined boundary in `It - Pilot`, turning a CNN newsletter into a false hiring update. The verified repair now covers both ends of the alert path: structured durable delivery for genuine hiring updates, plus boundary-aware and corroborated pipeline matching that rejects the exact CNN and `TP-Link` false positives.

## Symptoms

- A high-confidence email tied to an active interview pipeline appears in `data/email-history.jsonl`, but no Telegram alert is delivered.
- `logs/gmail-pubsub-pull.log` records `no_urgent_alert` after a Gmail notification even though the classifier recorded a pipeline match.
- A later scheduled scan reports zero new messages because the mailbox UID checkpoint already advanced.
- This failure mode differs from delayed ingress: Pub/Sub and classification both complete within seconds.

## Root cause

The formatter correctly interpreted `no_action` as “do not ask Ahmed to reply,” but removed the email from all actionable output. The worker then treated only text beginning with `🚨 Email alert` as deliverable. Therefore, a high-importance hiring-process update with no required reply was silently discarded. Mailbox UID state and Telegram delivery state were not coupled through a durable outbox or ledger.

A recurrence on 2026-07-15 exposed a separate classifier defect. `_normalize_key` removed every separator and `_match_pipeline_company` used unrestricted substring tests. Company `TP` therefore matched the characters spanning `It - Pilot`, scoring the CNN newsletter as an active-pipeline message. The sender-noise list also covered `newsletter.` and `newsletters@`, but not the plural subdomain form `newsletters.`.

## Failed approaches

- Relying on later scheduled scans cannot recover the alert because the classifier has already advanced the UID checkpoint.
- Checking only a fixed recent-message window is not reliable in a high-volume inbox.
- Treating a successful classifier run as delivery proof confuses processing with user-visible notification.

## Verified solution

1. Keep body-aware classification and active-pipeline matching as the source of hiring relevance, but match company/recruiter/title text as complete adjacent tokens. Treat company aliases shorter than four normalized characters as corroborating evidence only; they must combine with an exact tracked role or recruiter identity before reaching the pipeline threshold.
2. Recognize plural newsletter subdomains such as `newsletters.cnn.com` as noise before scoring or escalation.
3. Produce structured envelopes in `scripts/format-email-alert.py`:
   - `action_required`, high importance, `action_required=true`;
   - `hiring_process_update`, high importance, `action_required=false`;
   - no envelope for routine acknowledgements, job alerts, newsletters, marketing, or noise.
4. Use stable email keys and chunk envelopes so every notifiable email is represented.
5. In `scripts/gmail-pubsub-pull-worker.py`, register each envelope as pending before Telegram delivery.
6. Mark delivery complete only when the Telegram response contains `payload.ok=true` and a non-empty `messageId`.
7. Keep failed entries pending with bounded exponential retry. Reconcile the latest email summary at startup and periodically to recover a crash after classification but before registration.
8. Keep the worker Telegram-only. It must not contain any email compose, reply, forward, SMTP, or send path. Sending or replying to email always requires Ahmed's separate clear approval.
9. Restart only `gog-gmail-watch.service` when the long-running worker itself changes. Classifier-only changes need no restart because every notification launches a fresh classifier subprocess. Never restart the OpenClaw gateway for this repair.

Rollback: restore the two runtime scripts from the repair backup or reverse the scoped diff, rerun focused tests, and restart only `gog-gmail-watch.service`. Stop if the ledger is unreadable, formatter JSON is invalid, or receipt verification fails; do not erase the ledger or mark delivery successful.

## Evidence

- `scripts/format-email-alert.py:273` separates high-importance active-pipeline updates from action items.
- `scripts/format-email-alert.py:380` emits structured envelopes with importance, action state, pipeline matches, and stable email keys.
- `scripts/gmail-pubsub-pull-worker.py:105` persists envelopes before delivery.
- `scripts/gmail-pubsub-pull-worker.py:156` requires a proven Telegram receipt.
- `scripts/gmail-pubsub-pull-worker.py:171` retries pending delivery with bounded backoff.
- `scripts/gmail-pubsub-pull-worker.py:254` reconciles the latest classified summary after a crash or restart.
- The missed Sprinklr replay now yields one `hiring_process_update` envelope with `importance=high`, `action_required=false`, pipeline `Sprinklr`, and email key `id:364923`.
- `python3 scripts/test-email-agent.py` passed 59/59; `python3 scripts/email-synthetic-harness.py --verbose` passed update, reschedule, cancellation, feedback, rejection, action-request, noise, medium-priority pipeline, and batch-coverage cases; `python3 scripts/test-gmail-pubsub-pull-worker.py` passed pending, receipt, dedupe, failure, and recovery checks.
- After the controlled restart, `gog-gmail-watch.service` was active with a new PID; `data/gmail-pubsub-pull-state.json` reported `status=healthy`, `last_event=idle`, and zero pending alerts. The OpenClaw gateway remained healthy and was not restarted.
- `scripts/email-agent.py:308` now preserves token boundaries; `scripts/email-agent.py:368` gives short aliases only corroborating weight; `scripts/email-agent.py:245` recognizes plural newsletter subdomains.
- The exact CNN replay now yields `noise_sender=true`, no pipeline match, category `other`, score zero, and zero delivery envelopes. `TP-Link` is also rejected, while `TP` plus the exact tracked role and full `Teleperformance` references still match.
- The expanded core suite passed 66/66, the synthetic harness passed the exact classifier-to-envelope regression, and the delivery-ledger worker suite remained green.

## Prevention

- Never use rendered text or emoji as control flow; delivery decisions use structured fields.
- Keep a durable pending/delivered ledger and validate real delivery receipts.
- Preserve the scheduled IMAP scan as fallback, but make its wording describe only the current scan.
- Run the synthetic suite for interview updates, reschedules, cancellations, feedback, rejections, action requests, and noise before deploying formatter or watcher changes.
- Include real active-pipeline aliases in negative fixtures. At minimum, test cross-word boundaries, hyphenated product names, newsletter subdomains, short-alias-only input, and a corroborated positive case.
- Keep the no-email-send static guard in the worker test.

## When to revisit

Revisit this solution if Gmail ingress stops using Pub/Sub, Telegram gains a first-class idempotency key, the active-pipeline matching schema changes, or delivery responsibility moves into the classifier transaction itself.

# Grounding checklist

- [x] The symptom is observable and distinguishes this failure mode.
- [x] The root cause is proven by current evidence or explicitly labeled as inference.
- [x] The remedy was applied successfully to real state.
- [x] Recovery checks test the outcome, not merely command exit status.
- [x] Commands are safe, scoped, and include stop or rollback conditions when needed.
- [x] Referenced paths, configuration keys, and source lines exist.
- [x] Secrets, tokens, personal data, and hidden runtime instructions are absent.
- [x] An overlap search found no better canonical document to update.
- [x] Prevention addresses the cause rather than only the symptom.
