# AGENTS.md - Operating and Routing Reference

Full historical detail lives in `docs/reference/AGENTS.full.md`.

## Core Rules

- If the answer exists in a file, find it first.
- Mission Control task logging is retired. Do not use `localhost:3001` task-board workflows unless Ahmed explicitly re-enables them.
- External writes, public posts, and third-party messages require the correct approval path and follow-up notification.
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

## Tool Discipline

Before tool use:
1. Permission and approval needs.
2. Effort/risk level.
3. AFK/user-impact guard.
4. Rate-limit risk.
5. Core-file safety.
6. Verification plan.

After tool use:
1. Confirm actual outcome, not just exit code.
2. Log or trace if failure/lesson occurred.
3. Notify/escalate only when useful.
4. Recover automatically when safe.

## Effort Levels

| Effort | Use when | Verification |
|---|---|---|
| Low | quick reads, small reversible checks | minimal |
| Medium | research, drafts, single-file edits | light |
| High | CVs, cron, core files, multi-file changes | full |
| Max | strategy, architecture, interview prep, public-risk workflows | full + stress test |

## Sub-Agent Rules

Every spawn brief must include:
- do the work, do not delegate back
- never claim success with errors present
- report side findings
- timeout required, hard kill at 15 minutes max unless explicitly justified
- success criteria and verification

Use isolated context by default. Use forked context only when the child truly needs this transcript.

## Coding Dispatch

- **Simple:** one-file/tiny obvious fixes. Stay in current session.
- **Medium:** bounded multi-file change with clear path. Spawn ACP coding session if available.
- **Full:** feature, refactor, integration, architecture, or unclear path. Spawn ACP and require plan -> implement -> self-review -> report.
- **Plan-only:** when Ahmed asks to scope/review/plan without coding. Save plan under `plans/` when repo is writable.
- **Implement-from-plan:** use saved plan if scope has not changed.

Resolve repo/cwd before spawning. If unclear, ask once.

Full coding closeout must include:
- files changed
- tests/checks run
- key decisions
- remaining uncertainty/risk

## References

- Full AGENTS reference: `docs/reference/AGENTS.full.md`
- Tool permissions: `config/tool-permissions.yaml`
- Tool hooks: `config/tool-hooks.yaml`
- Session handoff: `templates/session-handoff.md`
- ACP presets: `templates/acp-*-preset.md`
