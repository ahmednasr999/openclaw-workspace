# NASR Loop Engineering Checklist - 2026-06-24

Purpose: convert Loop Engineering from a LinkedIn idea into an operating standard for NASR workflows.

Operational status, 2026-07-14: engineering ticket-to-merge work is now governed by `skills/agent-ops-loops/references/nasr-engineering-loop.md`, with a fail-closed record validator at `scripts/check-nasr-engineering-loop.py`. This checklist remains the broader recurring-workflow standard.

Source note: use credible wording such as "IEEE-style working note" or "working note on Loop Engineering." Do not call the uploaded PDF an IEEE paper unless a real IEEE publication source is verified.

## Core Thesis

Prompting is one move inside the system. The advantage is the loop around it:

Discover -> Isolate -> Build -> Verify -> Persist -> Schedule

A loop is not permission. It is a bounded control structure with evidence, stop states, and approval boundaries.

## Universal Loop Checklist

Before any recurring agent workflow runs, define:

- Target: one sentence describing the outcome.
- Authority: read-only, reversible local edit, approved external action, or approval-required.
- Discovery source: the real signal that creates work, not a human-written task list when a source exists.
- Isolation: workspace, database scope, artifact path, and owner agent boundaries.
- Builder: the agent or script that performs the work.
- Verifier: an independent check that starts from the assumption that the result may be wrong.
- Persistence: where evidence, output, decisions, and blockers are written.
- Schedule: trigger, cadence, retry limit, and quiet/no-alert condition.
- Stop state: success, clean-noop, blocked, approval-required, or exhausted.

## Verification Rule

A loop is not complete because it ran. It is complete only when the outcome is inspected against the source:

- Report exists and content is checked.
- CV exists and facts match source CV and job description.
- Visual exists and passes the reference-style quality gate.
- Email alert was body-read and classified.
- Gateway health was verified against live status/probe.
- Public post was inspected live after publishing.

## Reviewer Agent Rule

Any workflow that produces externally visible, reputation-sensitive, or decision-driving output needs a reviewer layer that can say no.

Reviewer stance:

- Assume the output is wrong until evidence proves otherwise.
- Check source evidence, not the builder's summary.
- Fail closed on fabricated facts, missing approvals, broken artifacts, duplicate actions, weak visual quality, or unverifiable claims.
- Write a short rejection reason and the smallest fix required.

## JobZoom First Hardening Map

Target: daily executive-job scan that produces a reliable report, application-ready CVs, and persistent duplicate exclusion.

Loop contract:

- Discover: full 150 LinkedIn JobSpy searches, applied ledger, latest run DB, failure logs.
- Isolate: JobZoom workspace only, `data/jobzoom.db`, reports directory, generated CV paths.
- Build: scrape, deduplicate, pass1, pass2 scoring, CV generation, daily report.
- Verify: independent JobZoom reviewer checks run counts, failed searches, parseable AI scoring JSON, selected records, applied suppression, generated PDFs, and report content.
- Persist: `runs`, `jobs`, `gpt_api_calls`, applied ledger, report PDF, CV PDFs, diagnostics report.
- Schedule: 05:00 Cairo daily cron, with warning-only delivery for partial failures and critical alert only for real failure.
- Stop states: delivered, clean zero-match report, warning report, failed run, approval-required application blocker.

Immediate hardening targets:

1. Add a read-only daily closeout checker that validates the latest run after cron.
2. Treat non-JSON AI scoring as degraded until rescored, not success.
3. Confirm every 70+ report job has saved description/provisional flag and a CV path if required.
4. Confirm 82+ jobs are application-ready unless already applied or blocked by unknown sensitive answer.
5. Keep applied-job exclusion as a permanent persistence gate before CV resend or application.

## CMO First Hardening Map

Target: content workflow that drafts, designs, reviews, and publishes only approved high-quality LinkedIn posts.

Loop contract:

- Discover: Notion pipeline, scheduled date, content gap signals, approved queue, duplicate/published logs.
- Isolate: CMO workspace, pipeline item, draft path, visual path, and publishing attempt state.
- Build: post draft, visual asset, approval card, pipeline update, publishing package.
- Verify: independent CMO reviewer checks Ahmed voice, source claim, approval state, duplicate state, visual reference concept, media delivery, and live post after publish.
- Persist: Notion item, draft/report path, visual file path, publish attempt result, LinkedIn URL when published.
- Schedule: weekly drafting, daily approval checks, publishing watchdog, content gap monitor.
- Stop states: Review-ready, approved-awaiting-publish, published-verified, blocked for approval, clean-noop calendar healthy.

Immediate hardening targets:

1. Add a visual quality gate that compares every LinkedIn visual to Ahmed's hand-drawn sketchnote reference before delivery.
2. Never mark media done from generation success or message-send success alone; inspect artifact and confirm delivery state.
3. Keep public posting gated unless Ahmed explicitly asks to post or the pipeline item is already approved for publishing.
4. Add a duplicate check before publish and a live post inspection after publish.
5. Persist a compact handoff packet: item, draft text/path, visual path, approval state, duplicate check, publish state.

## What We Should Not Automate Yet

Do not automate public posting decisions, email replies, recruiter messages, salary/terms commitments, credential changes, runtime changes, destructive cleanup, or application answers that require unknown sensitive facts.

## First Implementation Sequence

1. Manual closeout checklist for JobZoom latest run.
2. Manual closeout checklist for one CMO draft-to-review item.
3. Capture two real failures or near-misses prevented by the checklist.
4. Convert only the proven checks into read-only scripts.
5. Add reviewer-agent handoff only after read-only scripts are stable.

## Minimum Closeout Card

Every loop closeout should say:

- State: success, clean-noop, warning, blocked, approval-required, or exhausted.
- Evidence: source path, DB row/run id, report path, message id, or URL.
- Verification: what was inspected.
- Action: next decision needed, or no action.
- Risk: remaining warning if any.
