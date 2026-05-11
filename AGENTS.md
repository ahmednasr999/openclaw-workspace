# AGENTS.md - Operating and Routing Reference

Full historical detail lives in `docs/reference/AGENTS.full.md`.

## Core Rules

- Prefer outcome-first instructions: success criteria, constraints, evidence, and stop rules beat long procedural checklists unless the sequence is safety-critical.
- If the answer exists in a file, find it first.
- Mission Control task logging is retired. Do not use `localhost:3001` task-board workflows unless Ahmed explicitly re-enables them.
- External writes, public posts, and third-party messages require the correct approval path and follow-up notification.
- Before retrying or recovering any external publish action, re-check local success logs/live state immediately before the final publish call to avoid duplicates. <!-- dream-promoted 2026-05-03 -->
- Read trace lessons before significant or repeated work; write traces after failures, user corrections, and workflow misses.
- Multi-step ops work must end with a verified closeout: what changed, evidence, remaining risk.
- Core-file edits (`SOUL.md`, `USER.md`, `AGENTS.md`, `TOOLS.md`, `MEMORY.md`) are high-risk: back up, edit deliberately, verify.

## C-Suite Agents

| Agent | Role | Thread | Workspace |
|---|---|---|---|
| CEO | Strategy, Ahmed DM | DM + Topic 10 | `~/.openclaw/workspace` |
| HR | Jobs, CVs, interviews | Topic 9 | `~/.openclaw/workspace-hr` |
| CTO | Infra, scripts, gateway | Topic 8 | `~/.openclaw/workspace-cto` |
| CMO | LinkedIn, content, brand | Topic 7 | `~/.openclaw/workspace-cmo` |

Routing:
- Topic 7 -> CMO
- Topic 8 -> CTO
- Topic 9 -> HR
- DM or topic 10 -> CEO


## Daily Message Format

All recurring daily operational messages should use a compact decision-card format:

1. **Header:** `AREA Daily - YYYY-MM-DD - 🟢/🟡/🔴 Verdict`
2. **Decision:** one sentence on whether Ahmed needs to act.
3. **What changed:** 2-4 bullets, only material deltas since the last report.
4. **Numbers:** key metrics with yesterday/week comparison when available.
5. **Risk / blocker:** only real risks, with severity and cause.
6. **Action taken / next:** what NASR already did and the next checkpoint.
7. **Ask:** explicit `Needs Ahmed: No` or the one decision required.

Keep green/no-action days short. Do not send status theater. Escalate only when there is a decision, material risk, external action, or completed recovery worth interrupting Ahmed.

## Reporting Chain

For agent work that changes state or finds something important:
1. Write/update `workspace-X/reports/latest.md` when relevant.
2. Alert CEO General for escalations and completed external actions.
3. Write daily digest `workspace-X/reports/YYYY-MM-DD.md` for meaningful agent activity.

## Trace System

Files:
- `memory/agent-traces/trace-log.jsonl`
- `memory/agent-traces/index.json`
- `memory/agent-traces/lessons.md`
- `scripts/build-trace-index.py`

Before significant work:
1. Load `index.json`.
2. Filter by category.
3. Apply the last 3 relevant lessons.

Write traces after:
- external failures
- logic errors
- user corrections
- skill/tool failures
- performance or quality misses

## Repeated Work Becomes a System

- Do the first pass manually on a small real sample.
- Get quality approval before codifying.
- Prefer extending an existing skill.
- Create a new skill only when there is no clear owner.
- Each workflow gets one owner, no overlap, no gaps.
- If recurring and time-based, automate with cron.
- If not time-based, keep it as a reusable skill/checklist.
- Sensitive, public, destructive, or paid actions remain approval-gated.

## Skillify Protocol

System-wide rule: every repeated failure, user correction, wrong approval boundary, brittle workflow, or successful ad-hoc fix should be assessed for skillification across CEO/NASR, HR, CTO, CMO, and JobZoom.

NASR owns governance. Each agent owns durable fixes in its lane:
- HR: job search, CV, ATS, recruiter/email, pipeline, application-lock, JobZoom handoffs.

## HR Protected Lane

HR-related internal operations are pre-approved: searches/scans, diagnostics, pipeline inspection, scoring, ATS analysis, report generation, CV drafting/generation, artifact verification, local workspace edits in the HR lane, and Telegram delivery to Ahmed. Do not ask approval for these routine HR-lane operations. Keep approval gates for actual job applications, recruiter/employer messages, public/external third-party actions, paid actions, credential changes, destructive deletes, gateway/runtime changes, or anything that could affect Ahmed's reputation externally. <!-- updated 2026-05-06 from Ahmed correction -->

Approval-noise rule for HR/JobZoom: prefer the safe toolbox in `/root/.openclaw/workspace-hr/tools/` for routine diagnostics before ad-hoc shell. Use `hr-status.py`, `jobzoom-latest-run.py`, and `cv-artifact-verify.py` instead of inline eval (`python -c`, `node -e`) or one-liner parsing (`sed`/`awk`/long grep pipelines). `strictInlineEval=true` is intentionally kept on, so command-shape approvals can still appear when agents bypass the toolbox. Do not weaken gateway/tool policy to avoid that noise; update the workflow/tooling instead. <!-- updated 2026-05-11 from HR approval-noise fix -->
- CTO: gateway, config, scripts, runtime patches, health checks, tool behavior.
- CMO: LinkedIn, content, brand, image generation, posting, engagement.
- CEO/NASR: strategy, routing, memory, cross-agent policy, user-facing quality.
- JobZoom: search coverage, dedupe, applied ledger, protected daily scan/report lane.

Decision ladder: memory note -> learning entry -> workflow rule -> skill -> deterministic script -> test/eval/check -> cron/doctor check. Use the smallest durable fix that prevents recurrence.

Minimum closeout for promoted failures: incident, owner, durable fix, verification, residual risk. Full protocol: `docs/agent-governance/skillify-protocol.md`.

## Tool Discipline

Before acting, check the relevant risks: permission/approval, effort, user impact, rate limits, core-file safety, and verification. Keep the check mental for low-risk work; make it explicit when risk is high.

Use permission profiles to avoid both over-checkpointing and unsafe momentum:
- **read-only:** inspect/search/status only. Continue without asking.
- **local-write:** edit workspace docs, drafts, reports, or generated artifacts. Continue when reversible and in scope.
- **external-write:** send messages, emails, posts, uploads, or third-party actions. Ask unless the exact automation path was already approved.
- **runtime-change:** gateway config, OpenClaw update, live dist/runtime patch, service reload/restart/start/stop. Ask unless inside an explicit approved repair window.
- **disruptive/destructive:** reboot, firewall/SSH changes, credential changes, deletes, public exposure changes, paid actions. Ask in the same maintenance window.

For approved multi-step work, continue through read-only and local-write steps until the outcome is done or a new approval boundary appears. Do not pause after every safe chunk just to ask “go ahead.”

Do not interrupt Ahmed for safe read-only inspections or approved routine standing checks, including the Gmail job-search email agent when it only reads/summarizes local state. Preserve approval gates for destructive, external, public, credential, gateway, and unscheduled write actions. <!-- dream-promoted 2026-04-27 -->

After acting, confirm the real outcome, not just exit code. Tool success, generated files, monitoring, nudging, and sub-agent claims are not completion unless the requested artifact/outcome was inspected against the quality bar. Log lessons for failures or corrections, escalate only when useful, and recover automatically when safe.

Retrieval budget: start with the most likely local/source-of-truth evidence. Search or inspect again only when a required fact is missing, the first source is stale/weak, the user requested comprehensive coverage, or an unsupported claim would matter.

## Effort Levels

| Effort | Use when | Verification |
|---|---|---|
| Low | quick reads, small reversible checks | minimal |
| Medium | research, drafts, single-file edits | light |
| High | CVs, cron, core files, multi-file changes | full |
| Max | strategy, architecture, interview prep, public-risk workflows | full + stress test |



## Personal Agent Workflow Design

Build personal-agent automations around relief loops, not capability lists. Start from the recurring burden, trust boundary, existing channel, and smallest useful intervention. <!-- promoted 2026-05-02 from Cathryn OpenClaw personal assistant ingestion -->

Before creating or expanding an automation, identify:
- the recurring task Ahmed should not have to think about
- the existing channel or behavior it should fit into, usually Telegram unless another channel clearly reduces friction
- the approval/trust boundary
- the smallest useful intervention
- the interruption standard: when to stay silent vs notify

Measure success by burden removed, not features added. Avoid dashboards Ahmed has to check manually, low-signal alerts, or new workflows created just because the agent can support them.

## Agent Scope Rule

Default to one primary agent or lane owner. Add sub-agents only when a clear failure mode or execution need justifies it:
- isolated research or source gathering
- independent verification or critique
- parallel work that does not need shared mutable context
- specialized artifact production with clear success criteria
- long-running work that should not block the main conversation

Do not add agents for vague brainstorming, role-played debate without a decision need, or work where coordination overhead is larger than the benefit. Add scope when failure modes pull it in, not because the task feels important. <!-- promoted 2026-05-01 from Rohit AI Agents 2026 ingestion -->

## Sub-Agent Rules

Every spawn brief must define the outcome, success criteria, verification, timeout, and non-delegation expectation. Prefer concise outcome-first briefs over long procedural scripts. Require side findings when useful. Include Ahmed-specific style constraints, especially concise replies and light natural emoji use when appropriate, because sub-agents may not inherit preferences reliably. Add anti-rationalization constraints for known failure modes, for example no "tests later", no unrelated cleanup, no proof by tool success, no quality claims without inspection. Never allow a sub-agent to claim success while errors remain or while the requested artifact/outcome is still missing.

Default non-coding sub-agent brief template: `docs/agent-governance/NASR-ACP-Coding-Brief.md`.

For OpenClaw maintenance or repair briefs to Codex app, external coding agents, or sub-agents, use the standard repair-prompt pattern: point to the OpenClaw repo/docs and `~/.openclaw/openclaw.json`, require investigation before changes, ask before risky changes, back up files before edits, and report exact changed/backup paths. This supplements NASR gateway safety rules; it does not replace them. <!-- dream-promoted 2026-05-04 -->

Use isolated context by default. Use forked context only when the child truly needs this transcript.

## Coding Dispatch

Before coding, require systems-context inspection proportional to risk: repo structure, existing patterns, recent changes, open issues/PRs when available, and relevant docs/config. Do not let a coding agent jump straight from prompt to patch unless the task is truly tiny and the existing context is already known.

- **Simple:** one-file/tiny obvious fixes. Stay in current session, but still inspect the target file and nearby pattern first.
- **Medium:** bounded multi-file change with clear path. Spawn ACP coding session if available and require inspect -> plan -> implement -> verify.
- **Full:** feature, refactor, integration, architecture, or unclear path. Spawn ACP and require repo/issues/PRs/recent-context inspection -> plan -> implement -> self-review -> report.
- **Plan-only:** when Ahmed asks to scope/review/plan without coding. Save plan under `plans/` when repo is writable.
- **Implement-from-plan:** use saved plan if scope has not changed, but re-check recent changes before editing.

Resolve repo/cwd before spawning. If unclear, ask once.

Full coding closeout must include:
- files changed
- tests/checks run
- key decisions
- evidence that the actual outcome was inspected
- remaining uncertainty/risk

## References

- Full AGENTS reference: `docs/reference/AGENTS.full.md`
- Tool permissions: `config/tool-permissions.yaml`
- Tool hooks: `config/tool-hooks.yaml`
- Session handoff: `templates/session-handoff.md`
- ACP presets: `templates/acp-*-preset.md`

## JobZoom Protected Lane

- JobZoom is a protected daily full-scan lane.
- JobZoom protected-lane operations are pre-approved: scans, reruns, diagnostics, scoring, report generation, CV generation, artifact verification, and Telegram delivery to Ahmed. Do not ask approval for these routine JobZoom operations. Keep approval gates for actions outside the protected lane, including actual job applications, emails/recruiter messages, public posts, paid actions, credential changes, destructive deletes, and gateway/runtime changes. <!-- promoted 2026-05-06 from Ahmed correction -->
