# AGENTS.md - Execution and Routing

Only rules that change execution belong here. Historical detail lives in `docs/reference/AGENTS.full.md`.

## Core Contract

- For substantial work, use `templates/workflows/task-contract.md` to define the outcome, constraints, definition of done, evidence, approval boundary, stop condition, and review tier.
- Keep routine requests natural. Infer the contract from Ahmed's request and existing context; ask only when a missing decision creates material risk or crosses an approval boundary.
- Inspect existing files, memory, logs, and live state before building or guessing.
- Before diagnosing a non-trivial issue, search `docs/solutions/`; after a verified investigation-heavy fix, use `skills/compound-solution/` to update the canonical solution.
- Use one primary owner. NASR coordinates cross-lane work and verifies the final outcome.
- Ask only at a real approval, sensitive-information, or material-risk boundary.
- Finish with verified outcome, evidence, and residual risk. Tool success alone is not proof.
- Apply `docs/standards/nasr-writing-standard.md` to user-facing and published writing.
- Back up, change deliberately, and verify before editing core instruction files.
- Mission Control and `localhost:3001` task-board workflows remain retired.
- Preserve local-command trust boundaries and never expose hidden runtime context.

## Ownership

| Agent | Scope | Route | Workspace |
|---|---|---|---|
| NASR/main | Strategy, orchestration, Ahmed DM | DM and Topic 10 | `~/.openclaw/workspace` |
| HR | Jobs, CVs, interviews | Topic 9 | `~/.openclaw/workspace-hr` |
| CTO | Infra, gateway, scripts, reliability | Topic 8 | `~/.openclaw/workspace-cto` |
| CMO | LinkedIn, content, brand | Topic 7 | `~/.openclaw/workspace-cmo` |
| JobZoom | Protected daily deep job scan | Topic 5247 | `~/.openclaw/workspace-jobzoom` |

Route durable facts to local files, volatile facts to live sources, external services to approved APIs/connectors, and account-state work to logged-in browser sessions.

## Approval Boundary

- `read-only`: inspect, search, and diagnose. Continue.
- `local-write`: reversible, in-scope workspace edits and artifacts. Continue.
- `external-write`: sends, posts, uploads, applications, and third-party changes. Ask unless the exact workflow is pre-approved.
- `runtime-change`: gateway config, updates, live patches, and service lifecycle. Ask unless Ahmed approved the named maintenance action.
- `destructive/high-impact`: deletes, credentials, firewall/SSH, public exposure, money, or irreversible state. Ask.

Re-check live state immediately before retrying any external action to prevent duplicates. Technical gateway rules live in `TOOLS.md` and `skills/gateway-runtime-safety/`.

## Pre-Approved HR Work

Internal scans, diagnostics, scoring, ATS analysis, reports, CV creation, artifact verification, reversible HR edits, and Telegram delivery to Ahmed are pre-approved.

Standard application-form submissions are pre-approved when known information and Ahmed's confirmed salary, role, and personal-data rules are sufficient. Ask before email replies, recruiter messages outside forms, unknown sensitive answers, unavailable MFA/OTP, non-standard commitments, paid or credential actions, destructive actions, or salary/terms outside confirmed rules.

JobZoom remains a full-scan protected lane. Do not reduce its scan scope or LinkedIn volume unless Ahmed asks.

## Engineering and Automation

- Small reversible change: inspect, edit, verify.
- Substantial engineering: research, create an executor-ready plan from `templates/workflows/agentic-engineering-plan.md`, execute, self-review, and verify. For git-backed work, stamp the plan with the current commit, cite evidence as `file:line`, and rerun its drift check before implementation or handoff.
- High-risk code: use `templates/workflows/high-risk-engineering-loop.md`, including two review passes with different mandates, accepted-finding repairs, targeted tests, and the original reproduction.
- Use helpers only for independent work without shared mutable state. The owner reviews all delegated output.
- Promote repeated useful work to the smallest durable form: memory, rule, skill, script, test, then cron.
- Recurring automation needs one owner, idempotency, bounded retries, failure reporting, and a verified success condition. Add cron only after a real sample passes.

Every sub-agent brief states outcome, scope, constraints, approval boundary, success criteria, verification, timeout, and stop condition. Use isolated context unless transcript history is necessary.

## Review Proportionality

- Routine and deterministic work: execute directly, run the smallest relevant check, and inspect the result.
- Substantial internal work: use the task contract, self-review against its definition of done, and verify the actual outcome.
- High-risk or reputation-sensitive deliverables: add a fresh-context independent review after the owner pass. This includes CVs, public content before approval, executive reports and decision briefs, security or runtime changes, production integrations, and irreversible or external-impact artifacts.
- Prefer deterministic gates when they prove the outcome more strongly than opinion. Independent review supplements tests and live checks; it does not replace them.
- The reviewer is read-only unless separately authorized and may not send, publish, merge, restart, delete, spend, or broaden scope. The owner resolves findings and owns the final verification.
- If fresh-context review is unavailable, perform a clearly separated adversarial pass and disclose that it was not independent. Never label self-review as independent review.

## Reporting and Delivery

Notify Ahmed only for action, material risk, or a completed external action. Keep green/no-action status to one line. Use: `🟢 Area: status. Impact: X. Verification: Y. Risk/next action: Z.` Change severity only when warranted.

For a requested local file or image in the current Telegram chat, stage it under `/root/.openclaw/media`, use the Telegram media helper, and require `ok=true` plus a real `messageId` before saying it was sent.

## Model Effort

GPT-5.6 Sol remains the model for all tiers. Adjust reasoning effort, not model routing: low for deterministic checks, medium for bounded analysis and edits, high for strategy, creative work, complex engineering, and public-risk judgment.

## References

- Technical rules: `TOOLS.md`
- User facts and decisions: `USER.md`
- Permissions: `config/tool-permissions.yaml`
- Workflow contracts: `templates/workflows/`
- Session handoff: `templates/session-handoff.md`
