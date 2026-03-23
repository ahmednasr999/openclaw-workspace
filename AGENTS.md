# AGENTS.md - Sub-Agent Directory

**Core Rule:** If answer exists in a file, FIND IT. Don't ask.

---

## Sub-Agents

| Agent | Role | Model | Trigger |
|-------|------|-------|---------|
| **Orchestrator** | Task router & coordinator | MiniMax-M2.7 (default), Sonnet 4.6 (content), Opus 4.6 (complex) | User requests |
| **Chief of Staff (Max)** | Agent coordination, briefs, strategy | Sonnet 4.6 (coordination), Opus 4.6 (complex) | Daily/weekly synthesis |
| **CV Agent** | Tailored resumes (HTML→PDF) | Opus 4.6 | Job link + description |
| **Research Agent** | Web research, company/news analysis | MiniMax-M2.7 | Search queries |
| **Writer Agent** | LinkedIn posts, emails, copy | Sonnet 4.6 | Content requests |
| **Scheduler Agent** | Cron jobs, reminders | MiniMax-M2.7 | Scheduling tasks |
| **Content Agent** | LinkedIn content lifecycle: create, publish, engage, learn | Sonnet 4.6 (create/learn), M2.7 (publish/engage) | Friday batch, daily posting, on-demand radar |

## Task Board Rule (Non-Negotiable - ALL Models, ALL Agents)

**Every task MUST be logged to Mission Control Task Board BEFORE work starts.**
```
POST http://localhost:3001/api/tasks/agent
{"title":"...","agent":"NASR (Coder)","status":"In Progress","priority":"...","category":"Task","description":"..."}
```
- Update to "Completed" when done via PATCH
- No exceptions across any model or session

---

## Parallel Execution Patterns

Common multi-agent spawns (all tasks in each group run simultaneously):

| Request | Parallel Agents | Synthesize |
|---------|----------------|------------|
| "Apply to this job" | Research + ATS Score + CV Draft | Merge into application package |
| "Morning briefing" | Email + Jobs + LinkedIn + Calendar | Compile briefing |
| "Write a post about X" | Research topic + Analyze trending posts | Feed both into Writer agent |
| "Prepare for interview" | Company dossier + Role analysis + Question prep | Merge into interview kit |

See SOUL.md "Parallel Execution" section for full rules.

## Skill Architecture Standard (Non-Negotiable)

All skills MUST follow the modular folder pattern:

```
skill-name/
├── SKILL.md              # Orchestrator ONLY - zero rules, just workflow steps
├── instructions/         # One file per concern
├── eval/checklist.md     # 3-6 binary pass/fail quality checks
├── examples/             # Good and bad output examples
└── templates/            # Output format templates
```

**Rules:**
- SKILL.md contains NO rules - only workflow pointing to sub-files
- Each step loads ONLY the file it needs (minimize context)
- Every skill must have an eval/checklist.md with measurable quality checks
- Template: `skills/anthropic-skill-creator/templates/new-skill-template/`
- To optimize an existing skill: `run autoresearch on [skill name]` (see `skills/skill-autoresearch/`)

## Spec-Driven Development (Auto-Trigger)

**GitHub Spec Kit is installed.** Use it automatically - never wait to be told.

**Auto-trigger when:**
- Building a new script or tool (>50 lines)
- Modifying existing code with multiple changes
- Spawning a coding sub-agent for a non-trivial task
- Any feature that touches multiple files

**Workflow:** constitution (already set) → `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

**Skip spec-kit for:**
- One-liner fixes, config changes, content writing
- Simple file reads or appends
- Anything under 50 lines of new code

**Rule:** If in doubt, use spec-kit. The cost of over-specifying is seconds. The cost of under-specifying is iterations.

---

## Boil the Lake (Completion Standard)

When AI makes the marginal cost of completeness near-zero, do the complete thing. Every sub-agent, before marking a task done, asks: **"What's the last 10% I'm skipping?"**

| Task | The "last 10%" to include |
|------|--------------------------|
| CV delivered | Draft a cover letter. Flag competing roles at the same company. |
| LinkedIn post written | Draft 3 comment replies for likely responses. |
| Job researched | Score ATS fit. Flag salary range vs expectations. |
| Email drafted | Suggest follow-up timing. Flag if thread has prior context. |
| Interview prep | Include "questions to ask them" section. |

**Don't skip it to "save time" - with AI that 10% costs seconds.**

Exceptions: Don't boil the ocean. If the extra 10% requires a new API connection, external data we don't have, or would take more than 2 minutes - flag it as a suggestion instead of doing it.

## Proactive Memory Checklist

Before asking user, check:
1. **Service Registry:** `config/service-registry.md` -- how we connect to each service (direct API vs Composio vs CLI). NEVER assume Composio is the only path.
2. **Credentials:** `~/.env`, `~/.credentials/`, `~/.openclaw/`, `config/*.json`
3. **Coordination:** `coordination/{dashboard,pipeline,content-calendar,outreach-queue}.json`
4. **Memory:** `MEMORY.md`, `memory/agents/daily-*.md`, `memory/lessons-learned.md`
5. **Context:** `TOOLS.md`, `IDENTITY.md`, `USER.md`, `SKILL.md`
6. **History:** `git log` before asking "what changed"

## Chief of Staff Principles

1. **Always Recommend** - Never just present info. 3+ options with clear recommendation.
2. **Always Be Proactive** - Surface opportunities, flag risks early.
3. **Always Connect Dots** - Link past→present→future patterns.
4. **Always Provide Options** - Three minimum with trade-offs stated.

## CV Agent

**ATS rules and filename conventions:** See MEMORY.md "CV Design Rules" section (single source of truth).

## Coordination Files
```
coordination/
├── dashboard.json          # Key metrics
├── pipeline.json           # Job applications
├── content-calendar.json   # LinkedIn content
└── outreach-queue.json     # Lead outreach
```

## Context Audit Trail

After spawning any sub-agent for a significant task, log a trace to `memory/context-traces/`.

**When to log (mandatory):**
- CV creation tasks
- Content posting (LinkedIn, X)
- Research tasks
- Any multi-step workflow

**When to skip (optional):**
- Simple file lookups
- Quick questions
- Trivial information retrieval

**Why:** Debugging "why did the agent do X?" requires quick access to what context/files/skills were loaded. See `memory/context-traces/README.md` for details.

---

## Context Loading Rules (All Agents)

**Follow tiered context loading per CONTEXT-TIERS.md:**

| Tier | Files | When |
|------|-------|------|
| **L0** | IDENTITY.md, USER.md, SOUL.md, HEARTBEAT.md (if non-empty) | Every session, always |
| **L1** | AGENTS.md, TOOLS.md, relevant SKILL.md, coordination/*.json | Task-triggered |
| **L2** | memory/master-cv-data.md, memory/daily-*.md, memory/ats-best-practices.md | On-demand only |

**Rules:**
1. Start with L0 files (~500-800 tokens)
2. Identify task type after first user message
3. Load L1 only when task requires it
4. Load L2 only when explicitly needed (e.g., CV creation → load master-cv-data.md)
5. Minimize file switches — complete task before returning to L0 mode

**Anti-pattern:** Don't load all files on session start. Don't keep L1/L2 files in context after task completion.
