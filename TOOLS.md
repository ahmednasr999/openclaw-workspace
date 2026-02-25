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

*MiniMax pricing updated Feb 2026 based on Ahmed's account*

| Priority | Model | Alias | Cost | Context | Best For |
|----------|-------|-------|------|---------|----------|
| 1st | MiniMax M2.5-highspeed | minimax-m2.5 | $40/mo (300 prompts/5hrs) | 200K | Daily driver — flat rate, ~100 TPS |
| 2nd | Kimi K2.5 | kimi | $0.10/$0.60/$3.00 per 1M | 256K | Long context, cheap caching |
| 3rd | Claude Haiku 4.5 | haiku | $1/$5 per 1M | 200K | Fast, cheap, vision capable |
| 4th | Claude Sonnet 4.6 | sonnet46 | $3/$15 per 1M | 200K | Mid-tier reasoning, drafting |
| 5th | Claude Opus 4.6 | opus46 | $5/$25 per 1M | 200K | Heavy strategy, deep reasoning |

*Kimi K2.5: $0.10 input (cache hit) / $0.60 input (cache miss) / $3.00 output per 1M tokens*
*MiniMax account: Coding Plan Plus — M2.5-highspeed (~100 TPS, 3x faster than standard) — $40/mo*

---

## Model Routing Rules

| Task Type | Model | Alias | Reason |
|-----------|-------|-------|--------|
| Infrastructure decisions, post-mortems | Opus 4.6 | opus46 | Safety-critical reasoning |
| Interview prep, deep strategy | Opus 4.6 | opus46 | Best reasoning |
| CV tailoring, LinkedIn content, research | Sonnet 4.6 | sonnet46 | Balanced cost and quality |
| Quick formatting, lookups, simple transforms | Haiku 4.5 | haiku | Cheapest paid option, vision capable |
| Web search, email, calendar, cron, heartbeats | MiniMax M2.5 | minimax-m2.5 | Flat rate $40/mo |
| Long document analysis (256K+ context needed) | Kimi K2.5 | kimi | Largest context window |

### Cost Discipline (Non-Negotiable)
- Default: MiniMax M2.5 (flat rate, no per-token cost)
- Escalate to Sonnet: When task needs 150-500 tokens of reasoning
- Escalate to Opus: When task needs 500+ tokens of reasoning OR is safety-critical
- Use Kimi K2.5: When context exceeds 200K
- Never use Opus for what Sonnet can handle
- Never use Sonnet for what M2.5 can handle

### Monthly Cost Budget
| Model | Est. Usage | Est. Cost |
|-------|-----------|-----------|
| M2.5 | 65-75% of tasks | $40/mo (flat) |
| Opus | 5-10% of tasks | $0.75-$1.50/mo |
| Sonnet | 15-20% of tasks | $1.00-$2.00/mo |
| Haiku | 5-10% of tasks | $0.05/mo |
| **TOTAL** | **100%** | **~$42-$44/mo** |

Daily spend alert threshold: $5.00
If exceeded → NASR alerts Ahmed and auto-downgrades Sonnet tasks to M2.5.

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

| Agent | Folder | Default Model | Escalate To |
|-------|--------|--------------|-------------|
| CV Optimizer | cv-optimizer | sonnet46 | opus46 for senior roles |
| Job Hunter | job-hunter | minimax-m2.5 | haiku for screening |
| Researcher | researcher | kimi (long context) | sonnet46 for synthesis |
| Content Creator | content-creator | sonnet46 | minimax-m2.5 for drafts |

---

## Telegram Channel IDs

*(Populate with real values)*

| Channel | ID | Purpose |
|---------|----|---------| 
| Main chat | [YOUR_CHAT_ID] | Primary interaction |
| Alerts | [ALERT_CHANNEL_ID] | Urgent flags |

---

## 🤖 New Autonomous Capabilities (Feb 2026)

### Tavily Search
- **Status:** ✅ Active
- **API Key:** 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
- **Credits:** 1,000/month (free tier)

### Google Workspace
- **nasr.ai.assistant@gmail.com:** ✅ Gmail connected
- **ahmednasr999@gmail.com:** ✅ Gmail + Calendar connected
- **Credentials:** config/ahmed-google.json

### Job Radar
- **Script:** /root/.open/job-radar.shclaw/workspace/scripts
- **Output:** memory/job-radar.md

---

## Mac Node Pairing (Tailscale Method)

**Gateway Tailscale URL:** `srv1352768.tail945bbc.ts.net`
**WebSocket:** `wss://srv1352768.tail945bbc.ts.net`

### Setup (on Mac Terminal)

```bash
# 1. Install OpenClaw
npm install -g openclaw

# 2. Connect via Tailscale (HTTPS/WSS, port 443)
openclaw node run --host srv1352768.tail945bbc.ts.net --port 443 --tls --display-name "Ahmed-Mac"

# 3. Wait for "Waiting for approval" message

# 4. On VPS (NASR will do this):
openclaw nodes pending
openclaw nodes approve <requestId>

# 5. Install as permanent service (after approval)
openclaw node install --host srv1352768.tail945bbc.ts.net --port 443 --tls --display-name "Ahmed-Mac"
```

### Rules
- **NEVER** bind gateway to 0.0.0.0 (exposes to public internet)
- **ALWAYS** use Tailscale URL (encrypted, authenticated, private)
- **NEVER** change gateway config for node pairing
- Gateway stays on 127.0.0.1:18789, Tailscale proxies it securely

---

**Links:** [[MEMORY.md]] | [[AGENTS.md]] | [[SOUL.md]]
