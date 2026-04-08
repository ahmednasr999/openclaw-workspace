# AGENTS.md - Sub-Agent Directory

Quick operating reference. Full historical detail moved to `docs/reference/AGENTS.full.md`.

## Core rules
- If the answer exists in a file, find it first.
- Log every task to Mission Control before work starts.
- Every external write triggers immediate CEO notification to topic 10.
- Read trace index before significant work, write traces after failures.
- All tool calls go through permission, effort, AFK, rate-limit, and core-file checks.

## C-suite layout
| Agent | Role | Thread | Workspace | Model |
|-------|------|--------|-----------|-------|
| CEO | Strategy, Ahmed DM | DM + Topic 10 | `~/.openclaw/workspace` | GPT-5.4, MiniMax-M2.7 fallback |
| HR | Jobs, CVs, interviews | Topic 9 | `~/.openclaw/workspace-hr` | GPT-5.4, MiniMax-M2.7 fallback |
| CTO | Infra, scripts, gateway | Topic 8 | `~/.openclaw/workspace-cto` | GPT-5.4, MiniMax-M2.7 fallback |
| CMO | LinkedIn, content, brand | Topic 7 | `~/.openclaw/workspace-cmo` | GPT-5.4, MiniMax-M2.7 fallback |

## Routing
- Topic 7 → CMO
- Topic 8 → CTO
- Topic 9 → HR
- DM or topic 10 → CEO

## Reporting chain
1. Write `workspace-X/reports/latest.md`
2. Alert CEO General for escalations and completed external actions
3. Write daily digest `workspace-X/reports/YYYY-MM-DD.md`

## Trace system
Files:
- `memory/agent-traces/trace-log.jsonl`
- `memory/agent-traces/index.json`
- `memory/agent-traces/lessons.md`
- `scripts/build-trace-index.py`

Read before task:
1. Load `index.json`
2. Filter by category
3. Apply last 3 relevant lessons

Write after failures for: external failures, logic errors, user corrections, skill failures, performance issues.

## Task board rule
POST before work:
`POST http://localhost:3001/api/tasks/agent`

Required fields:
- title
- agent
- status=In Progress
- priority
- category
- description

## Tool hook checkpoints
Pre-tool:
1. Permission
2. Effort gate
3. AFK guard
4. Rate limit
5. Core file guard
6. Verification flag

Post-tool:
7. Audit log
8. CEO notification
9. Dream tag
10. Error recovery

## Effort levels
| Effort | Use when | Model | Verify |
|--------|----------|-------|--------|
| Low | quick reads, small tweaks | MiniMax-M2.7 | skip |
| Medium | research, drafts, single-file work | GPT-5.4 | light |
| High | CVs, cron, multi-file changes | GPT-5.4 | full |
| Max | strategy, architecture, interview prep | GPT-5.4 | full + grill-me |

Never treat work touching `MEMORY.md`, `SOUL.md`, `TOOLS.md`, or `AGENTS.md` as below High.

## Sub-agent rules
Every spawn must include:
- do the work, do not delegate back
- never claim success with errors present
- report side findings
- timeout required, hard kill at 15 minutes max

## Fast mode
For cron/routine runs:
- minimal logging
- no grill-me
- no verbose verification unless 3+ files touched

## Auto-triggers
- Build or major modify anything → run grill-me after verification
- Non-trivial code or multi-file feature → use spec-driven development

## References
- Full AGENTS reference: `docs/reference/AGENTS.full.md`
- Tool permissions: `config/tool-permissions.yaml`
- Tool hooks: `config/tool-hooks.yaml`
- Session handoff template: `templates/session-handoff.md`
