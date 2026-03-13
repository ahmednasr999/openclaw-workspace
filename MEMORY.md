# MEMORY.md: Cross-Session Cheat Sheet

*Last updated: 2026-03-12*
*Rule: < 100 lines. Not a journal. Findable via search = doesn't belong here.*

---

## Ahmed: Quick Reference
- Senior tech exec, 20+ years, GCC & Egypt. Acting PMO at TopMed ($50M DT, 15 hospitals)
- Target: VP/C-Suite GCC, Q3 2026. Salary floor: 50,000 AED/mo. Dubai preferred.
- MBA in progress: Paris ESLSCA (2025-2027). Certs: PMP, CSM, CSPO, LSS, CBAP
- Positioning: Digital Transformation Executive (NOT consultant)

## Current Priorities
1. Land executive role in GCC, Q3 2026
2. LinkedIn executive positioning: 2-3 posts/week (content engine live, Sun-Thu)
3. OpenClaw system optimization (memory architecture, cron hardening)
4. TopMed PMO delivery on track

## Google Docs Quality Standard (LOCKED Mar 12, 2026)
- Doc ID: 1gtl5sXIsvXiXhODFs29FD9L09i9mGQlsBVIrZbVkTYs
- Template script: scripts/google-docs-briefing.py
- NEVER use raw markdown dump. ALWAYS use Google Docs API with proper:
  - TITLE + SUBTITLE header
  - HEADING_1 for date, HEADING_2 for sections, HEADING_3 for sub-items
  - Bold labels (Company:, Location:, ATS Score:, etc.)
  - Unicode bullets, checkbox items for actions
  - Italic grey footer
  - Document Outline must be navigable
- GOG_KEYRING_PASSWORD="" (empty string)

## Web Fetching Tools

### Jina Reader (Mar 12, 2026)
- **URL:** https://r.jina.ai/{URL}
- **What:** Returns clean Markdown from any URL
- **Free tier:** 10M tokens/month
- **Use when:** Tavily fails, need fallback for article/job page extraction
- **Example:** `https://r.jina.ai/https://x.com/user/status/123`
- **Function:** `scripts/morning-briefing-orchestrator.py` → `jina_fetch()`

### Search Hierarchy (LOCKED Mar 13, 2026)
1. **DuckDuckGo (ddgs)** → primary for ALL search (free, no API key, no quota)
2. **Tavily API** → fallback only (free tier exhausted, 1K credits/month)
3. No Brave. Never had it, won't add it.

### Page Content Extraction
1. Defuddle → primary (`defuddle.md/[url]`, clean markdown, zero cost, no API key)
2. Jina Reader → fallback (`r.jina.ai/[url]`, 10M tokens/month free)
3. Camoufox → last resort (complex JS, interactive only)

### here.now (Mar 12, 2026)
- **URL:** https://nasr.here.now/
- **API Key:** f9020182961ef02b3621dda6f77aa72949c35549dc8cf7fd5afe06a979e3a27e
- **Skill:** /root/.openclaw/skills/here-now
- **Use:** Publish static content instantly (HTML, PDFs, dashboards)

### Google Workspace
- Account: ahmednasr999@gmail.com
- OAuth client: 583018818639 (backup client, working)

## LinkedIn Account Separation (HARD RULE, Mar 13 2026)
- **Ahmed's LinkedIn** (real profile): Composio ONLY. Official API posting. NEVER scrape, NEVER automate via browser, NEVER use Camoufox. Reputation is sacred.
- **NASR's account** (agent): Camoufox/browser automation for job searches (120/day), JD fetching, scraping. Acceptable risk on bot account.
- **NEVER MIX.** No scraping on Ahmed's account. No posting from NASR's account.

## Communication Rules
- Direct, concise. Lead with insight, not preamble. No Markdown tables unless Ahmed explicitly asks.
- Time-sensitive items at TOP. Label options A/B/C. No hand-holding.
- Auto-capture content Ahmed shares (unless told not to)
- Analysis order: (1) full extraction, (2) map to Ahmed stack, (3) recommendation
- NEVER use em dashes. Use commas, periods, colons. Hard rule, all output, all sub-agents.
- Credentials shared in DM: accept and use. Flag only expired/invalid ones.

## Job Radar Rules (Mar 10, 2026)
- Pre-filter: tech/DT/PMO leadership only. Kill sales, HR, supply chain, admin, beauty, construction.
- Seniority: Director+ only. No coordinators, no managers.
- ATS pre-score against master CV: only surface 82+ to Ahmed.
- Borderline 80-84: hold in buffer, mention count. Below 80: auto-skip silently.
- Freshness: 7 days max.

## CV & ATS Rules
- ATS floor: 82% (MiniMax M2.5 primary scorer, Opus tie-breaker for 82-87 range)
- Never use Haiku for ATS scoring (+4.0 drift, inflates scores)
- All CV generation MUST use Opus 4.6. No exceptions.
- Disclose model used in every CV delivery message.
- Master CV: memory/master-cv-data.md. Each app gets tailored version.
- Pipeline source of truth: Google Sheet (not pipeline.md)
- Full JD check BEFORE ATS scoring (never score by title alone)
- All 33 background crons run on MiniMax (0 Claude crons) for cost efficiency

## ORP State Machine (Hard Rule)
- NEW > TRIAGED > READY > IN_PROGRESS > VALIDATED > DELIVERED > LOGGED > CLOSED
- Pipeline update BEFORE CV delivery (Gate D)

## Model Strategy
| Task | Model | Why |
|------|-------|-----|
| Deep strategy, interviews, CVs | Opus 4.6 | Best reasoning, CV quality |
| Drafting, LinkedIn content | Sonnet 4.6 | Balanced quality |
| ATS scoring, crons, heartbeats | MiniMax M2.5 | Free, conservative |
| Coding, agentic sub-agents | GPT-5.4 | 1M context, best coding, separate quota |
| Quick lookups, lightweight | Haiku 4.5 | Fast, cheap |
| Long context (budget) | Kimi K2.5 | Free, 256K window |

Budget: EGP 9,000/mo (Claude Max 20x) + $40 (MiniMax) + $20 (ChatGPT Plus, GPT-5.4)

## Critical Operational Rules
- Model fallback notification: ALWAYS notify Ahmed when any fallback happens (which model failed, what replaced it, why)
- Max 10 parallel agents. 70% usage = downgrade to MiniMax. 90% = block spawns.
- Session auto-flush at 75% context. Start fresh session after flush.
- Never run heavy installs during active sessions (starves VPS).
- memory/ is knowledge-only. No packages, no code files.
- Sub-agents: write to output files only. NASR merges. Never touch MEMORY.md/GOALS.md.
- After sub-agent builds: check git diff for accidental deletions.
- PDF naming: "Ahmed Nasr - [Role] - [Company].pdf"
- Silence rule: no-action items = no notification.
- KillMode=mixed + TimeoutStopSec=15 for systemd services.

## Key Infrastructure
- VPS: Hostinger. Interface: Telegram + Slack (app rebuilt Mar 8, bot: openclaw2)
- GPT-5.4-Pro: manually registered in openclaw.json (custom provider entry)
- Self-healing agent: system cron every 2 min, Claude Code CLI repair
- modelByChannel doesn't override cached sessions: use /model command or delete session
- Git repos: openclaw-nasr (workspace), openclaw-config (config)
- Tailscale: srv1352768.tail945bbc.ts.net
- Google OAuth: ahmednasr999@gmail.com (Gmail + Calendar)
- Job Radar: official employer sources first, aggregators discovery-only
- LinkedIn discovery: hashtag + whitelist priority, own-feed fallback only
- **X/Twitter Full Access (Mar 12, 2026):** @Nasr2030vision account fully accessible via Camoufox CLI on VPS. Cookies at `/root/.openclaw/cookies/x.txt`. USE CLI, NOT browser tool:
  - `camofox-browser open <url>` — open URL, returns tabId
  - `camofox-browser snapshot <tabId>` — get page content
  - `camofox-browser screenshot <tabId>` — screenshot
  - DO NOT use browser tool (port conflicts). USE camofox-browser CLI directly.

## Google Docs Briefing Standard (Mar 12, locked)
- NEVER raw markdown in Google Docs. Always native API formatting.
- Python script `scripts/daily-briefing-generator.py` is single source of truth for quality.
- Models cannot deviate from formatting. Script is deterministic.
- All links must be clickable (hyperlink pass built in).
- LinkedIn posts: individual authors only, sorted by freshness (activity ID).
- Comments: ready-to-post, drafted by Sonnet 4.6.
- Daily Briefing Doc ID: 1gtl5sXIsvXiXhODFs29FD9L09i9mGQlsBVIrZbVkTYs
- System Log Doc ID: 1Ti5kle0bq4fXBgF54arYO2C723LtHkDUhO2o2rmDAqU
- OAuth: backup client 583018818639 (active), GOG_KEYRING_PASSWORD=""

## Where Things Live
- Active tasks: memory/active-tasks.md
- Queued deep work: memory/pending-opus-topics.md
- CV data: memory/master-cv-data.md
- Lessons: .learnings/LEARNINGS.md
- Completed milestones: memory/completed-milestones.md
- Knowledge index: memory/knowledge-index.md
- Daily logs: memory/YYYY-MM-DD.md

---
*Links: [[SOUL.md]] | [[AGENTS.md]] | [[USER.md]] | [[TOOLS.md]] | [[GOALS.md]]*
