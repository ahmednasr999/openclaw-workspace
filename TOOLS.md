# TOOLS.md — Environment & Tool Reference

*Last updated: 2026-02-21*

---

## Infrastructure

| Item | Detail |
|------|--------|
| VPS | Hostinger |
| OS | Ubuntu (Linux) |
| Interface | Telegram |
| OpenClaw config | ~/.openclaw/ |
| Agent config | ~/.openclaw/agents/main/ |
| Memory location | memory/*.md |
| Models config | models.json |

---

## Tool Reference — When to Use What

### File Operations

| Tool | Use When |
|------|----------|
| read | Loading any file — memory, config, docs |
| write | Creating new files or full overwrites |
| edit | Surgical updates — prefer over write to avoid data loss |

Rule: Always use edit over write for existing files. write overwrites silently. edit is precise.

### Execution

| Tool | Use When |
|------|----------|
| exec | Git, system checks, installs, scripts |
| process | Long-running tasks that need monitoring |

Rule: Always use trash before rm. Recoverable beats gone.

### Web & Research

| Tool | Use When |
|------|----------|
| web_search | Quick lookups, job searches, fact-checking |
| web_fetch | Full article or JD content needed |
| browser | Form filling, scraping, screenshots |

Rule: web_fetch before browser. Browser is expensive and slow.

### Memory Tools

| Tool | Use When |
|------|----------|
| memory_search | Don't know which file — search semantically |
| memory_get | Know the file and line range — pull directly |

Rule: memory_search first on any question about past context.

### Agent Orchestration

| Tool | Use When |
|------|----------|
| sessions_spawn | Delegating a contained, specific task |
| sessions_send | Steering an already-running sub-session |
| sessions_list | Checking what's running |
| sessions_history | Reading sub-agent output |
| subagents | Managing delegated work |
| agents_list | Checking available agent IDs |
| session_status | Checking cost and model usage |

Rule: Sub-agents write to output files only. NASR merges into shared memory. Never let sub-agents touch MEMORY.md, GOALS.md, or active-tasks.md directly.

### Communication

| Tool | Use When |
|------|----------|
| message | Proactive alerts, session results, urgent flags |
| tts | Voice summaries (use sparingly — cost) |

### Visual

| Tool | Use When |
|------|----------|
| image | Analyzing uploaded images or screenshots |
| canvas | Dashboards, visual explainers, HTML output |

---

## Model Registry — Clean Lineup

*Deprecated models removed: M2.1 (all 3 instances), M2.1-highspeed, Sonnet 4*

| Priority | Model | Alias | Cost | Context | Best For |
|----------|-------|-------|------|---------|----------|
| 1st | MiniMax M2.5 | minimax-m2.5 | Free | 200K | Daily driver — zero cost tasks |
| 2nd | Kimi K2.5 | kimi | Free | 256K | Long context, free alternative |
| 3rd | Claude Haiku 4.5 | haiku | $1/$5 per 1M | 200K | Fast, cheap, vision capable |
| 4th | Claude Sonnet 4.6 | sonnet46 | $3/$15 per 1M | 200K | Mid-tier reasoning, drafting |
| 5th | Claude Opus 4.6 | opus46 | $5/$25 per 1M | 200K | Heavy strategy, deep reasoning |

Removed from registry:
- MiniMax M2.1 — duplicated 3x, superseded by M2.5
- MiniMax M2.1 Highspeed — redundant
- Claude Sonnet 4 — superseded by Sonnet 4.6 at same price
- Claude Opus 4.5 — superseded by Opus 4.6 at 3x lower cost

---

## Model Routing Rules

| Task Type | Model | Alias | Reason |
|-----------|-------|-------|--------|
| Interview prep, deep strategy, system architecture | Opus 4.6 | opus46 | Best reasoning at lowest Opus cost |
| CV tailoring, content drafting, analysis | Sonnet 4.6 | sonnet46 | Balanced cost and quality |
| Quick formatting, lookups, simple transforms | Haiku 4.5 | haiku | Cheapest paid option, vision capable |
| Bulk processing, repetitive tasks, first drafts | MiniMax M2.5 | minimax-m2.5 | Free — use aggressively |
| Long document analysis (256K+ context needed) | Kimi K2.5 | kimi | Largest context window, free |

Cost discipline rules:
- Default to MiniMax M2.5 for anything that doesn't need Claude quality
- Use Kimi K2.5 when context exceeds 200K or as free Sonnet alternative
- Never use Opus 4.6 for tasks Sonnet 4.6 can handle
- Never use Sonnet 4.6 for tasks Haiku can handle
- Never use paid models for tasks free models can handle

Daily spend alert threshold: $5.00
If exceeded → NASR alerts Ahmed and switches lighter tasks to free models.

---

## Sub-Agent Conventions

*(Since agents share the same workspace with no isolation)*

When spawning a sub-agent task, always:
1. Specify the model explicitly using alias
2. Scope the task narrowly — one output, one file
3. Tell it exactly where to write output
4. Explicitly include: "Do NOT update MEMORY.md, GOALS.md, or active-tasks.md"
5. NASR reviews and merges output after task completes

### Recommended Model per Agent Role

| Agent | Default Model | Escalate To |
|-------|--------------|-------------|
| CV Optimizer | sonnet46 | opus46 for senior roles |
| Job Hunter | minimax-m2.5 | haiku for screening |
| Researcher | kimi (long context) | sonnet46 for synthesis |
| Content Creator | sonnet46 | minimax-m2.5 for drafts |

---

## Telegram Channel IDs

*(Populate with real values)*

| Channel | ID | Purpose |
|---------|----|---------| 
| Main chat | [YOUR_CHAT_ID] | Primary interaction |
| Alerts | [ALERT_CHANNEL_ID] | Urgent flags |
