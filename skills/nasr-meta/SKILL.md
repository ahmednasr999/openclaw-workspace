---
name: nasr-meta
description: "Auto-inject behavioral instructions into sub-agent briefs based on task type. ALWAYS use when spawning ANY sub-agent for CV building, job scoring, content writing, or research. Ensures consistent quality, prevents improvised briefs, eliminates quality drift between sessions. NOT for direct execution by NASR main session. This skill routes to the correct agent behavioral file, not replaces NASR's judgment."
metadata: {"openclaw":{"emoji":"🧬"}}
---

# NASR Meta: Sub-Agent Behavioral Routing

Automatically loads the correct behavioral instructions when spawning sub-agents. Eliminates improvised briefs and prevents quality drift.

---

## When This Skill Triggers

ALWAYS when NASR (main session) is about to spawn a sub-agent for any of these task types:
- CV generation or tailoring
- Job link scoring or assessment
- LinkedIn content writing or drafting
- Research or company analysis

## Pre-Flight: Detect Task Type

Before spawning, classify the task:

| Task Contains | Agent Type | Behavioral File |
|---------------|-----------|-----------------|
| CV, resume, tailor, ATS, application document | cv-builder | `agents/cv-builder.md` |
| score, assess, rank jobs, job links, verdict | job-scorer | `agents/job-scorer.md` |
| LinkedIn post, draft content, write post, content | content-writer | `agents/content-writer.md` |
| research, company info, salary data, market analysis | researcher | `agents/researcher.md` |

If task doesn't match any type, skip this skill (ad-hoc briefs are fine for one-off tasks).

## Step 1: Load Behavioral File

Read the matching `agents/*.md` file. This file contains the complete behavioral instructions for the sub-agent role.

```
read agents/[agent-type].md
```

## Step 2: Build Brief

Every sub-agent brief MUST follow this structure:

```
TASK: [specific task description]

BEHAVIORAL INSTRUCTIONS:
[paste full contents of agents/[agent-type].md]

GLOBAL RULES (all agents):
- Quality Over Speed: NEVER prioritize delivery speed over quality. Zero exceptions.
- No Fabrication: If data is missing, say so. Never invent.
- Telegram-safe output only. No Markdown tables unless Ahmed explicitly asks.
- Do NOT update MEMORY.md, GOALS.md, or active-tasks.md.

COMPLETION RULES:
- You are NOT done until every part of the task is finished.
- Do not summarize what you "would do next." Do the work now.
- Do not stop because the task is "mostly done." 100% or not done.
- If you hit an error, fix it or try an alternative.
- When genuinely complete, end with: TASK_COMPLETE
- If TASK_COMPLETE is missing, the task is considered failed.

OUTPUT:
[specify exact output file path and format]
```

## Step 3: Set Model

| Agent Type | Required Model | Alias |
|------------|---------------|-------|
| cv-builder | Opus 4.6 (MANDATORY, no exceptions) | opus46 |
| job-scorer | MiniMax M2.5 (default), Opus for borderline | minimax-m2.5 |
| content-writer | Sonnet 4.6 | sonnet46 |
| researcher | Haiku 4.5 (default), Sonnet for synthesis | haiku |

CV builder on wrong model = STOP. Do not proceed.

## Step 4: Spawn and Monitor

Spawn the sub-agent with the built brief. After completion:
1. Check for `TASK_COMPLETE` token
2. If missing: steer with "You stopped before completing. Continue from where you left off."
3. If present: review output quality before delivering to Ahmed

## Hard Rules

| Rule | Detail |
|------|--------|
| Never skip behavioral file | Even under time pressure, even for "quick" tasks |
| Never modify behavioral files in-brief | If the file needs updating, update the source file, not the brief |
| Always include Completion Guard | Sub-agents quit early without it, especially lighter models |
| CV builder = Opus 4.6 only | Hardcoded. No exceptions. No fallbacks. |

## Common Failure Modes

| Failure | Cause | Prevention |
|---------|-------|------------|
| Quality drift across CVs | Improvised brief without behavioral file | This skill makes inclusion automatic |
| Sub-agent stops at 80% | Missing Completion Guard | Always included in brief template |
| Wrong model for CV | Time pressure, default model used | Pre-flight model check before spawn |
| Inconsistent scoring | Different scoring criteria per session | job-scorer.md has fixed weights |
| Off-voice LinkedIn posts | No voice guidelines in brief | content-writer.md has exact voice rules |

---

## References

- `agents/cv-builder.md`: CV generation behavioral instructions
- `agents/job-scorer.md`: Job scoring behavioral instructions
- `agents/content-writer.md`: LinkedIn content behavioral instructions
- `agents/researcher.md`: Research behavioral instructions
- `AGENTS.md`: System-wide rules and conventions
- `SOUL.md`: NASR identity and operating principles

**Links:** [[agents/cv-builder.md]] | [[agents/job-scorer.md]] | [[agents/content-writer.md]] | [[agents/researcher.md]] | [[AGENTS.md]]
