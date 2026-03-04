# TOOLS.md — Environment & Tool Reference

*Last updated: 2026-03-04*

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

*Updated Mar 1, 2026. All three primary providers are flat-fee subscriptions, not per-token.*

| Priority | Model | Alias | Plan | Cost/mo | Context | Limit | Best For |
|----------|-------|-------|------|---------|---------|-------|----------|
| 1st | MiniMax M2.5-highspeed | minimax-m2.5 | Coding Plus | $40 | 200K | 300 prompts/5hrs | Default: crons, heartbeats, quick tasks |
| 2nd | GPT-5.3-Codex | gpt53codex | ChatGPT Plus | $20 | 266K | 45-225 msgs/5hrs | Sub-agents, coding, mid-tier reasoning |
| 3rd | Claude Sonnet 4.6 | sonnet46 | Claude Max 20x | (incl) | 200K | 20x Pro/5hrs | Drafting, research, LinkedIn content |
| 4th | Claude Opus 4.6 | opus46 | Claude Max 20x | (incl) | 200K | 20x Pro/5hrs | Deep strategy, CV tailoring, interviews |
| 5th | Claude Haiku 4.5 | haiku | Claude Max 20x | (incl) | 200K | 20x Pro/5hrs | Fast, vision, lightweight fallback |
| 6th | Kimi K2.5 | kimi | API key | ~free | 256K | n/a | Long context (256K+) |

**Monthly budget: ~EGP 9,000 + $60/mo total**
- Claude Max 20x: EGP 9,000/mo (Opus + Sonnet + Haiku, shared 20x Pro limit per 5hrs)
- MiniMax Coding Plus: $40/mo (300 prompts/5hrs, ~100 TPS)
- ChatGPT Plus: $20/mo (GPT-5.3-Codex, 45-225 msgs/5hrs)

**Key: All limits reset every 5 hours. Spread load across providers to avoid hitting any single limit.**

**Fallback chain:** MiniMax M2.5 (default) -> Claude Sonnet 4.6 -> Claude Haiku 4.5 -> GPT-5.3-Codex (until Apr 1) -> Kimi K2.5

**Auth:** Claude via API key, MiniMax via OAuth, Codex via OAuth (token expires ~June 2026)

---

## Model Routing Rules

| Task Type | Model | Alias | Reason |
|-----------|-------|-------|--------|
| Infrastructure decisions, post-mortems | Opus 4.6 | opus46 | Best reasoning, safety-critical |
| Interview prep, deep strategy | Opus 4.6 | opus46 | Best reasoning |
| CV tailoring, LinkedIn content | Sonnet 4.6 | sonnet46 | Quality drafting |
| Sub-agent work, coding tasks | Haiku 4.5 | haiku | Fast, lightweight, default sub-agent |
| Quick formatting, lookups, vision | Haiku 4.5 | haiku | Fast, lightweight |
| Crons, heartbeats, email, calendar | MiniMax M2.5 | minimax-m2.5 | Flat rate default |
| Long document analysis (256K+) | Kimi K2.5 | kimi | Largest context window |

### Quota Discipline (Non-Negotiable)
- All three providers are flat-fee. Optimization = spreading load, not saving money.
- Default: MiniMax M2.5 (background noise, highest prompt count)
- Sub-agents: prefer Codex (separate quota pool from Claude)
- Claude: reserve for main session conversations and quality-critical output
- Principle: never burn one provider's quota when another can handle it
- Monitor: if any provider approaches 80% of 5hr limit, shift load to others

### Monthly Cost Budget (Fixed)
| Provider | Plan | Cost |
|----------|------|------|
| Claude Max 20x | Opus + Sonnet + Haiku | EGP 9,000/mo |
| MiniMax Coding Plus | M2.5-highspeed | $40/mo |
| ChatGPT Plus | GPT-5.3-Codex | $20/mo |
| **TOTAL** | | **EGP 9,000 + $60/mo** |

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
| CV Optimizer | cv-optimizer | **opus46** | Never downgrade CVs |
| Job Hunter | job-hunter | haiku | sonnet46 if quality insufficient |
| Researcher | researcher | haiku | sonnet46 for synthesis |
| Content Creator | content-creator | sonnet46 | opus46 for strategic pieces |

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
