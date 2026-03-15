# MEMORY.md: Cross-Session Cheat Sheet

*Last updated: 2026-03-15*
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

## No Fabrication Rule (LOCKED Mar 15, 2026)
- NEVER fabricate, invent, or reconstruct any content from memory
- If data lost: recover from revision history, backups, git first
- If recovery fails: tell Ahmed honestly "I can't recover this"
- Zero exceptions. Trust rule.

## Google Docs Standard (LOCKED Mar 12-15, 2026)
- Doc IDs: Briefing 1gtl5sXIsvXiXhODFs29FD9L09i9mGQlsBVIrZbVkTYs, Log 1Ti5kle0bq4fXBgF54arYO2C723LtHkDUhO2o2rmDAqU, LinkedIn Posts 1hhROckb3AVGnka0rXB5vh25zywXJFDLuQYGTRa7zp4g
- NEVER raw markdown. ALWAYS native API formatting via scripts/daily-briefing-generator.py
- Script is single source of truth. Models cannot deviate.
- Rules: never delete old content, prepend only, reverse chronological, no duplicates, backup first
- GOG_KEYRING_PASSWORD="" (empty string)
- For headless: use scripts/gdocs-create.py (direct API) not gog CLI
- gog CLI auth broken: nasr.ai.assistant@gmail.com token expired. Re-auth needs browser (not possible headless). Use direct API scripts instead.

## Job Scanner v3.0 (Mar 15, 2026)
- Three-criteria filter: executive title + GCC location + DT/Tech domain
- Fast mode: linkedin_fetch_description=False (no rate limiting)
- 55 search combos (10 primary titles x 3 countries + 5 secondary x 5)
- Output: Priority Picks + Executive Leads
- Dedup against notified jobs, applied companies, pipeline
- NEVER re-enable JD fetch (causes rate limiting)

## Search & Fetch Tools
- **Search:** DuckDuckGo (ddgs) primary, Jina Reader (r.jina.ai) for URL extraction
- **Tavily:** EXHAUSTED (HTTP 432), do not use
- **Page extraction:** Defuddle primary, Jina fallback, Camoufox last resort
- **here.now:** https://nasr.here.now/ (publish static content)

## LinkedIn Account Separation (HARD RULE)
- Ahmed's LinkedIn: Composio ONLY. Official API posting. NEVER scrape.
- NASR's account: Camoufox for job searches (120/day), JD fetching.
- NEVER MIX.

## CV & ATS Rules
- ATS floor: 82% (MiniMax M2.5 primary, Opus tie-breaker 82-87)
- Never use Haiku for ATS scoring (+4.0 drift)
- All CV generation MUST use Opus 4.6
- Master CV: memory/master-cv-data.md. Each app gets tailored version.

## Model Strategy
| Task | Model |
|------|-------|
| Deep strategy, CVs, interviews | Opus 4.6 |
| Drafting, LinkedIn content | Sonnet 4.6 |
| ATS scoring, crons, heartbeats | MiniMax M2.5 |
| Coding, agentic sub-agents | GPT-5.4 |
| Quick lookups | Haiku 4.5 |

Budget: ~$240/mo (~12,000 EGP): Claude Max EGP 9K + MiniMax $40 + ChatGPT $20

## Cron Sequence (Live)
- 6:00 AM: Jobs Scanner + Email
- 6:30 AM: Engagement Radar
- 7:30 AM: Morning Briefing (builds Google Doc)
- 9:30 AM: LinkedIn Post
- 4:00 AM: SIE (Self-Improvement Engine) daily

## Key Infrastructure
- VPS: Hostinger. Interface: Telegram + Slack
- Tailscale: srv1352768.tail945bbc.ts.net
- Google: ahmednasr999@gmail.com (OAuth client 583018818639)
- X/Twitter: @Nasr2030vision via camofox CLI (cookies at /root/.openclaw/cookies/x.txt)

## Where Things Live
- Active tasks: memory/active-tasks.md
- CV data: memory/master-cv-data.md
- Lessons: .learnings/LEARNINGS.md
- Daily logs: memory/YYYY-MM-DD.md

---
*Links: [[SOUL.md]] | [[AGENTS.md]] | [[USER.md]] | [[TOOLS.md]] | [[GOALS.md]]*
