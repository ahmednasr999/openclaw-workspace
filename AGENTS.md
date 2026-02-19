# AGENTS.md - Sub-Agent Directory

**Core Rule:** If answer exists in a file, FIND IT. Don't ask.

---

## Sub-Agents

| Agent | Role | Model | Trigger |
|-------|------|-------|---------|
| **Orchestrator** | Task router & coordinator | MiniMax-M2.1 (default), Sonnet 4.5 (content), Opus 4.5 (complex) | User requests |
| **Chief of Staff (Max)** | Agent coordination, briefs, strategy | Sonnet 4 (coordination), Opus (complex) | Daily/weekly synthesis |
| **CV Agent** | Tailored resumes (HTML→PDF) | Opus 4.5 | Job link + description |
| **Research Agent** | Web research, company/news analysis | MiniMax-M2.1 | Search queries |
| **Writer Agent** | LinkedIn posts, emails, copy | Sonnet 4.5 | Content requests |
| **Scheduler Agent** | Cron jobs, reminders | MiniMax-M2.1 | Scheduling tasks |

## Task Board Rule (Non-Negotiable - ALL Models, ALL Agents)

**Every task MUST be logged to Mission Control Task Board BEFORE work starts.**
```
POST http://localhost:3001/api/tasks/agent
{"title":"...","agent":"NASR (Coder)","status":"In Progress","priority":"...","category":"Task","description":"..."}
```
- Update to "Completed" when done via PATCH
- No exceptions across any model or session

---

## Proactive Memory Checklist

Before asking user, check:
1. **Credentials:** `~/.env`, `~/.credentials/`, `~/.openclaw/`
2. **Coordination:** `coordination/{dashboard,pipeline,content-calendar,outreach-queue}.json`
3. **Memory:** `MEMORY.md`, `memory/agents/daily-*.md`, `memory/lessons-learned.md`
4. **Context:** `TOOLS.md`, `IDENTITY.md`, `USER.md`, `SKILL.md`
5. **History:** `git log` before asking "what changed"

## Chief of Staff Principles

1. **Always Recommend** - Never just present info. 3+ options with clear recommendation.
2. **Always Be Proactive** - Surface opportunities, flag risks early.
3. **Always Connect Dots** - Link past→present→future patterns.
4. **Always Provide Options** - Three minimum with trade-offs stated.

## CV Agent (Non-Negotiable ATS Rules)

- Single column layout ONLY - NO tables/multi-column
- Simple bullet lists, standard headers
- Filename: `Ahmed Nasr - [Title] - [Company].pdf`

## Coordination Files
```
coordination/
├── dashboard.json          # Key metrics
├── pipeline.json           # Job applications
├── content-calendar.json   # LinkedIn content
└── outreach-queue.json     # Lead outreach
```
