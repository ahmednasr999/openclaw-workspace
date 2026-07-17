---
name: agent-ops-loops
description: Bounded operational loop patterns for OpenClaw agents. Use when Ahmed asks to adapt or run repeatable AI-agent workflows for production/runtime error sweeps, recovery proof, repository cleanup, ticket-to-PR readiness, spec-build-review engineering, groundtruth audits, or when a task needs explicit evidence gates, tested-SHA approval, retry limits, and terminal stop states.
---

# Agent Ops Loops

Use this skill to turn broad agent work into bounded loops with evidence, approvals, and clear stop conditions. The patterns are adapted from the public MIT Loop Library catalog, but this skill is OpenClaw-specific and does not install or execute external prompts.

## Operating Rule

A loop is a control structure, not permission. Before acting, define the target, authority, evidence source, verification gate, stop states, and approval boundaries. Do not let a loop override existing OpenClaw, HR, LinkedIn, gateway, credential, public-posting, paid-action, or destructive-change rules.

## Pick The Loop

- `references/production-error-sweep.md` - runtime, cron, Telegram, agent, gateway, or app logs with possible actionable errors.
- `references/recovery-proof-loop.md` - backup, rollback, update recovery, restore testing, or disaster-recovery proof.
- `references/repository-cleanup-loop.md` - stale branches, worktrees, repos, generated research clones, or unclear local changes.
- `references/ticket-to-pr-ready-loop.md` - bug reports, failed behavior, tickets, regressions, or review-ready patches.
- `references/nasr-engineering-loop.md` - ticket-driven `/spec -> /build <-> /review -> approval -> merge` work with isolated branches, independent review, tested-SHA approval, and deterministic issue states.
- `references/groundtruth-audit-loop.md` - evidence-first audits of security, platform fit, runtime behavior, scheduled jobs, or system claims.

## Shared Loop Contract

For every loop:

1. Name the target and scope in one sentence.
2. Capture the authority boundary: read-only, reversible local edit, approved external action, or approval-required.
3. Identify source evidence before summarizing: logs, code, config, database rows, reports, primary docs, screenshots, or live probes.
4. Define terminal states before execution:
   - `success`: requested outcome verified against the source.
   - `clean-noop`: inspection found no actionable work, with evidence.
   - `blocked`: required access, approval, or external state is missing.
   - `approval-required`: next step would affect production, external parties, public surfaces, money, credentials, or destructive state.
   - `exhausted`: retry or time budget was reached without proof.
5. Use at most two repair attempts before escalating to diagnosis or a narrower plan, unless Ahmed explicitly asks to continue.
6. Preserve evidence for destructive or high-impact steps. Prefer archive/compress/disable over delete when rollback value remains.
7. Close with what changed, how it was verified, remaining risk, and where evidence lives.

## Approval Boundaries

Pre-approved only when already allowed by standing rules: local read-only inspection, reversible workspace edits, focused tests, reports, CV/report generation, and standard HR application-form submission when known information is sufficient.

Ask before email replies, recruiter/employer messages outside application forms, public posts, paid actions, credential changes, gateway/config/update/restart work unless Ahmed already approved that exact action, destructive cleanup, production data changes, unknown sensitive answers, MFA/OTP, or salary/terms outside confirmed rules.

## Done Means

- The relevant reference checklist was followed or a reason for skipping it is stated.
- Evidence came from the real source, not just a summary or successful command exit.
- Verification checks match the risk of the action.
- No warning, blocked state, or budget exhaustion is reported as success.
- The final report is short, operational, and names the next action only if useful.
