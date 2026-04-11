# AGENTS.md - Sub-Agent Directory

Quick operating reference. Full historical detail moved to `docs/reference/AGENTS.full.md`.

## Core rules
- If the answer exists in a file, find it first.
- Mission Control task logging retired on 2026-04-09. Do not use it unless Ahmed explicitly re-enables it.
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
Mission Control is retired. Do not POST to `http://localhost:3001/api/tasks/agent` unless Ahmed explicitly re-enables it.

## Repeated work becomes a system
- If Ahmed asks for work likely to recur, do it manually first on a small real sample.
- Get approval on output quality before codifying it.
- Prefer extending an existing skill. Only create a new skill when there is no clear owner.
- Each workflow should have one owner skill, no overlap, no gaps.
- If the work is truly recurring and time-based, automate it with cron. If not, keep it as a reusable skill or checklist.
- Public, destructive, or sensitive actions remain approval-gated.
- If Ahmed has to ask repeatedly for the same operational workflow, codify it.

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

## Coding Tasks
### Dispatch tiers
- Simple: one-file or tiny obvious fixes, stay in current session, no ACP overhead.
- Medium: multi-file but obvious path, spawn ACP coding session with a short brief covering what, why, files, test case, and risk.
- Full: feature, refactor, or objective-level build, spawn ACP coding session and require plan → implement → self-review → report.
- Plan-only: if Ahmed asks to plan, review, or scope work without building, spawn ACP coding session to produce a saved plan only, no implementation.

### Spawn rules
- Always spawn ACP for non-trivial coding work instead of telling Ahmed to open another tool himself.
- Resolve the repo/cwd before spawning. If unclear, ask which repo.
- Append repo-specific instructions to existing `CLAUDE.md` / `AGENTS.md` guidance, never overwrite local project rules.
- Every coding spawn must include timeout, explicit success criteria, and "do the work, do not delegate back".

### Medium-tier brief
Use this brief structure for obvious multi-file coding work:
1. What is being changed
2. Why it matters
3. Which files are likely involved
4. How to test it
5. Main risk / thing to double-check

### Full-tier closeout
Every non-trivial coding session must report back with:
- files changed
- tests/checks run
- key decisions made
- anything still uncertain or risky

### Plan artifacts
- Plan-only sessions save plans under `plans/<project>-plan-YYYY-MM-DD.md` when the repo is writable.
- Later implementation sessions should reference the saved plan instead of replanning from scratch unless scope changed.

### Recommended methodology skills to mirror
- Office-hours: challenge framing before implementation
- CEO review: push on scope and strategic shape
- Investigate: no fix without root-cause pass
- Retro: capture what improved and what broke

### ACP preset files
- Compact spawn brief: `templates/acp-spawn-brief-template.md`
- Spawn command pattern: `templates/acp-spawn-command-pattern.md`
- Medium coding: `templates/acp-medium-coding-preset.md`
- Full build: `templates/acp-full-build-preset.md`
- Plan-only: `templates/acp-plan-only-preset.md`
- Implement-from-plan: `templates/acp-implement-from-plan-preset.md`

### ACP selection cheat sheet
- Use Simple when the task is an obvious one-file or tiny fix and no ACP session would add real value.
- Use Medium when the change is bounded, the path is mostly clear, and the likely blast radius is a few files.
- Use Full when the task is a feature, refactor, integration, or architecture-touching change, or when the path is not obvious.
- Use Plan-only when Ahmed wants scope, review, or implementation planning without code changes.
- Use Implement-from-plan when a saved plan already exists and scope has not materially changed.
- If the task is ambiguous between Medium and Full, default to Full.
- If repo or cwd is unclear, ask before spawning.
- If Ahmed explicitly says not to code yet, never upgrade Plan-only into implementation without fresh approval.

## References
- Full AGENTS reference: `docs/reference/AGENTS.full.md`
- Tool permissions: `config/tool-permissions.yaml`
- Tool hooks: `config/tool-hooks.yaml`
- Session handoff template: `templates/session-handoff.md`
