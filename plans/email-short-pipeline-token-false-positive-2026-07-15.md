# Email Short Pipeline Token False-Positive Repair

## Plan Metadata

- Status: complete
- Owner: NASR/main
- Planned at: commit `f3f54c443` on `2026-07-15`
- Depends on: `plans/email-hiring-update-alert-repair-2026-07-14.md`

> **Executor contract:** Read the full plan before editing. Stay inside scope, run each verification gate, and report evidence. If a stop condition is met or reality conflicts with the plan, stop and report the mismatch instead of improvising.

> **Drift check:** `git diff --stat f3f54c443..HEAD -- scripts/email-agent.py scripts/test-email-agent.py scripts/email-synthetic-harness.py`
> The repository HEAD still equals `f3f54c443`. The working tree already contains the approved prior email repair and an unrelated model/rejection diff in `scripts/email-agent.py`; preserve those hunks and inspect the scoped diff before and after this repair.

## Objective

- Target outcome: prevent short active-pipeline company names such as `TP` from matching across word boundaries in unrelated email subjects or bodies.
- User-visible success condition: the exact CNN newsletter produces no pipeline match, stays category `other`, and creates no Telegram delivery envelope; valid standalone `TP` and full company-name matches continue to work.
- Why this matters: a false pipeline match bypasses newsletter/noise expectations and creates a misleading hiring-process alert.

## Evidence And Current State

- Source anchors: `scripts/email-agent.py:288` removes all non-alphanumeric separators in `_normalize_key`.
- Source anchors: `scripts/email-agent.py:343` checks `company_norm in subject_norm` without token boundaries or a minimum company length.
- Source anchors: `scripts/email-agent.py:582` treats any pipeline match as hiring context and later promotes it to `recruiter_reach`.
- Existing convention to follow: `scripts/email-agent.py:292` already extracts alphanumeric tokens for safe token-level checks.
- Reproduction or baseline: with one active job whose company is `TP`, the CNN subject `In Case You Missed It - Pilot...` returns match `('TP', 8)`, categories `['recruiter_reach']`, and score `(7, 'TP')`.
- Raw evidence to preserve: `data/email-history.jsonl:15405` and the delivered ledger entry; do not rewrite either.

## Scope

- In scope: active-pipeline text matching in `scripts/email-agent.py`, exact regression tests, synthetic no-envelope verification, plan/record, learning, and canonical solution update after proof.
- Files likely touched: `scripts/email-agent.py`, `scripts/test-email-agent.py`, `scripts/email-synthetic-harness.py`, this plan, the high-risk record, `.learnings/LEARNINGS.md`, today's memory note, and the existing email-alert solution.
- Do not touch: credentials, SMTP/email-send paths, mailbox UID history, delivery ledger history, gateway, unrelated dirty files.
- Non-goals: redesigning all email classification, changing active pipeline records, or altering Telegram receipt/retry behavior.

## Authority And Safety

- Permission profile: local-write plus the previously approved runtime change for `gog-gmail-watch.service` only.
- Approval boundary: the named email watcher repair remains approved; no email send/reply is authorized.
- Rollback path: reverse only this matcher/test diff, rerun focused tests, and restart only `gog-gmail-watch.service` if it was restarted for deployment.
- External/public/credential/paid/runtime action involved: one controlled watcher-service restart after all gates; no email or third-party message.

## Owner And Helpers

- Owning session/agent: NASR/main
- Helpers, if explicitly permitted: none
- Independent assignment and expected evidence for each helper: none
- Maximum concurrency: 1

## Ordered Implementation Steps

### Step 1: Make pipeline text matching boundary-aware

- Files: `scripts/email-agent.py`
- Change: preserve text token boundaries and require short names/acronyms to match complete tokens; allow normalized phrase matching only for sufficiently specific multi-character names.
- Preserve: exact recruiter email/name matching, domain-token matching, scoring thresholds, and all unrelated current diffs.
- Verify command/check: exact CNN reproduction plus positive `TP` standalone and `Teleperformance` company-name cases.
- Expected result: CNN returns no match while legitimate pipeline references still match.

### Step 2: Lock the real regression into automated tests

- Files: `scripts/test-email-agent.py`, `scripts/email-synthetic-harness.py`
- Change: add the exact CNN subject/sender fixture with active company `TP`; assert no pipeline match, category `other`, low score, and no structured hiring update.
- Preserve: existing Sprinklr/Miriam and delivery-ledger coverage.
- Verify command/check: core email suite and synthetic harness.
- Expected result: all suites pass and would fail under the prior matcher.

### Step 3: Review, deploy, and inspect real state

- Files: high-risk record and service process only.
- Change: perform correctness and adversarial reviews, repair accepted findings within two rounds, restart only the watcher, inspect status/log/state, then update the canonical solution.
- Preserve: gateway process/configuration and the historical false alert evidence.
- Verify command/check: record validator, solution validator, service active state, healthy watcher state, zero pending alerts, and no post-restart errors.
- Expected result: corrected matcher is live and the exact false positive is permanently covered.

## Test Plan

- Existing tests to run: `python3 scripts/test-email-agent.py`; `python3 scripts/email-synthetic-harness.py --verbose`; `python3 scripts/test-gmail-pubsub-pull-worker.py`.
- New or changed tests: short-token cross-boundary rejection and legitimate standalone/full-name positives.
- Original reproduction after implementation: rerun the exact CNN subject with active company `TP` and inspect matcher, categories, score, and formatter envelopes.
- Actual artifact or behavior to inspect: watcher health and logs after the approved narrow service restart.

## Stop Conditions

- An in-scope file changes unexpectedly after this plan is validated.
- The fix suppresses exact recruiter-email matches or legitimate standalone company references.
- A verification gate fails twice after bounded repair.
- The smallest credible fix requires credentials, gateway work, mailbox-history rewriting, or any email send/reply.

## Done Criteria

- [x] Every ordered step completed or explicitly skipped with evidence.
- [x] Focused tests and original reproduction pass.
- [x] Actual user-visible or operational outcome inspected.
- [x] Changed files remain inside scope.
- [x] Accepted review findings repaired and reverified.
- [x] Remaining risk and rollback evidence recorded.

## Review Handoff

- Diff base and target: working-tree diff from the pre-repair snapshot, limited to matcher/test/documentation hunks.
- Reviewer focus: boundary semantics and false negatives first; alert safety, deployment, and rollback second.
- Known trade-offs: short company aliases now require standalone token evidence unless stronger recruiter identity evidence exists.
- Deliberately deferred work: broader classifier redesign and cleanup of unrelated pre-existing diffs.

## Closeout

- Files/artifacts changed: `scripts/email-agent.py`, `scripts/test-email-agent.py`, `scripts/email-synthetic-harness.py`, this plan, the high-risk record, `.learnings/LEARNINGS.md`, `memory/2026-07-15.md`, and the existing canonical email-alert solution.
- Commands/checks and results: Python compilation passed; core email suite passed 66/66; synthetic harness passed; delivery-ledger worker test passed; scoped `git diff --check` passed; exact CNN replay produced no match, category `other`, score zero, and no envelope.
- Deviations from plan: no watcher restart was needed because the long-running worker launches a fresh `email-agent-gated.py` subprocess for every notification. The corrected classifier was already live for the next event; the watcher remained healthy and processed later notifications without alerts.
- Evidence of success: CNN sender is now recognized as newsletter noise, `TP` cannot match across `It - Pilot`, `TP-Link` does not qualify, a short alias alone stays below threshold, and `TP` plus the exact tracked role still matches.
- Residual risk: company names of four or more characters can still coincide with unrelated non-newsletter text. Sender-noise checks and recruiter/domain/title evidence reduce this risk, but future real false positives should be added as exact fixtures.
