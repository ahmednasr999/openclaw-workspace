# Last Session
Updated: 2026-03-10 11:27 UTC

## Mar 10 — MiniMax Rate Limit Fix + Advisory Board v3 (Opus 4.6)
**Focus:** Cron concurrency burning MiniMax quota, Advisory Board rebuild

### What We Did
- MiniMax rate limit root cause: gmail monitor every 30min + overlapping morning crons
- Fixed: gmail monitor -> every 4hr, staggered morning crons (6:00/6:15/6:30/7:00/7:30)
- Built Advisory Board v3 engine (897 lines, change detection, 14 input sources, dynamic recs)
- Re-enabled Advisory Board crons on v3
- Disk monitor timeout 60s -> 120s

### Open Threads
- Monitor rate limits after stagger fix
- Review v3 Advisory Board first output (tomorrow 7 AM Cairo)
- Job Radar v3 filter upgrade (DONE)
- LinkedIn Comment Poster test (Mar 11)

---

## Mar 8 — Slack Setup Overhaul + Self-Healing Agent (Opus 4.6)
**Focus:** Slack app rebuild after accidental deletion, GPT-5.4-Pro registration, self-healing deployment

**What happened:**
- Full Slack evaluation: 10 channels mapped, cron delivery audited
- Ahmed accidentally deleted Slack app mid-session
- Rebuilt app, configured event subscriptions + socket mode
- Registered GPT-5.4-Pro as custom model in OpenClaw (was missing from registry)
- Set #x-analysis and #ai-codex to GPT-5.4-Pro
- Deployed self-healing repair agent (system cron, Claude Code CLI, repair playbook)
- Weekly token health check cron added
- Cleared all stale Slack sessions to force correct model pickup

**Open threads:**
- Verify all Slack channels using correct models after session clear
- #openclaw and #random need manual archive from Slack
- Self-healing agent may trigger false restarts (needs tuning)

---

## Mar 7 Evening — Job Applications + Calibration (Opus 4.6)
**Focus:** Search Policy calibration run, 2 email-based CV applications

**What happened:**
- Calibration run_cal_001 completed: 64 raw results, 12 executive kept, 81% noise reduction. Policy validated.
- #57 HybridGlobal Sr PM DT Banking (Dubai, ATS 89%) — emailed sajna.jaleel@hybridglobal.ae
- #58 Confidential SDM (RAK/Sharjah, ATS 65%) — emailed enk77@hotmail.com
- Total today: 7 applications (#52-58). Pipeline at 58.

**Open threads:**
- Tomorrow: first production morning scan under new search policy
- Nuxera.AI: waiting on Amin's salary reply
- Model Council Room MVP: approved, not built
- CDO role (Valkyrie): confirmed closed, dropped

---

## Mar 6 X-Analysis Session (MiniMax, 71% context)
**Focus:** Deep dive into 25+ high-signal X posts on OpenClaw and AI agent systems
**Outcomes:**
- Analyzed 25+ X posts on OpenClaw architecture, cost optimization, self-healing
- Installed summarize.sh (v0.11) - AI content summarization
- Installed gws (Google Workspace CLI) - 42 skills for Gmail, Calendar, Drive
- Created eval-suite framework for skill evaluation
- Saved Claude Code prompt reference (13KB) + tools (49KB)
- Cloned system-prompts-and-models-of-ai-tools repo (30K+ lines)
- Explored OpenClaw Map tools: Clawzempic, AgentActa, BackupClaw, OpenClaw-RL
- Cleaned sessions.json: 82 old cron sessions deleted, 5.1MB→2.9MB

**Key Patterns Identified:**
1. Freshman Rule - One task per agent, clear instructions
2. Fewer agents - 2-4 better than 9
3. Local heartbeats - Save API limits
4. Compounding - Every failure = rule, every success = formula
5. Prompt caching - 90% savings

**Action Items:**
1. Enable prompt caching in openclaw.json
2. Create CLAUDE.md with execution discipline
3. Run eval suite on CV Optimizer
4. Consider BackupClaw for data safety

**Open Threads:** None

## Mar 6 Evening Session (Opus, 77% context at close)
**Focus:** Infrastructure hardening + skill framework overhaul (triggered by 4 X articles Ahmed shared)
**Outcomes:**
- 33 cron jobs hardened: bestEffort, failure alerts on 9 critical, models pinned, light-context on 11
- Self-healing agent deployed: every 2h, auto-diagnoses cron failures, playbook-driven fixes
- 15 dead skills archived (42→28), 4 skill descriptions optimized (cv-builder, linkedin-writer, spreadsheet, resume-optimizer)
- CV builder: Step 0 pre-flight gates + post-gen quality gate from 56 CV analysis
- KillMode=mixed + TimeoutStopSec=15 applied (Feb 25 post-mortem fix was missing)
- Weekly gateway restart cron + Anthropic skill-creator framework installed
- Claude Max/ToS risk noted (sk-ant-oat01 = OAuth token)
- Shape Up skills banked for later
**Open threads:** None

## What We Did (Mar 6)
- Checked GPT-5.4 availability: announced publicly, still not allowed in current runtime entitlement
- Diagnosed Gmail integration issue: token had read-only mailbox scope for automation operations
- Guided Google Cloud OAuth consent fix step-by-step
- Completed OAuth callback token exchange and enabled writable Gmail scopes
- Deployed Gmail automation end-to-end:
  - Labels: JOB-ACTIONS, JOB-RECEIPTS, MARKET-NEWS
  - Filters for LinkedIn alerts/newsletters/receipts and Workable/Teamtailor priority
  - Retro cleanup: 2,652 alerts + 145 newsletters + 650 receipts archived, 84 recruiting threads prioritized

## Open Threads
- Nuxera CEO (Amin Elhemaily): awaiting response
- 24h Gmail impact validation, then optional filter tightening
- GPT-5.4 entitlement watch remains active

---

## Previous Session (Mar 5, session 2 - 15:00-15:45 UTC)
Updated: 2026-03-05 15:45 UTC

## What We Did (Mar 5, session 2 - 15:00-15:45 UTC)
- Scored all 27 unique jobs from scout v2 run (full JD + composite ATS)
- Generated 2 more CVs: Confidential Gov Riyadh (70%) + EDB Field CTO (66%)
- Ahmed applied to Confidential Gov Riyadh
- Today total: 3 applications, 6 CVs generated

## Open Threads
- Sheet row 16 "Applied" update pending (API timeout)
- EDB + eMagine CVs ready, pending apply
- Nuxera CEO messaged, watching for response
- LinkedIn Content Weeks 3-5 due Mar 7

## Previous Session (Mar 5, session 1)
- Generated 3 tailored CVs using HTML→WeasyPrint pipeline
- eMagine (96% ATS): CV complete, pending apply
- Anduril: Full JD revealed Secret Clearance required, real ATS 64%, SKIP
- Dubai Holding: CV done but Ahmed reported job closed
- Fixed learning: LinkedIn cookies exist at workspace/config/, not openclaw/config/
- Fixed learning: Always fetch full JD before scoring (prevents wasted CV generation)
- Logged both learnings to .learnings/LEARNINGS.md

## Open Threads
- Run fresh job scout to replace closed/skipped jobs
- Ahmed to apply to eMagine (CV ready)
- Cron job linkedin-job-scout set for Mon/Wed/Fri 6AM UTC, needs testing
- ATS scorer script has path-length bug on long strings

## Earlier (Mar 5, morning-midday)
- Discussed JobSpy, Crawlee, LinkedIn scraping approaches
- Built LinkedIn JD Fetcher: Playwright + li_at cookie, runs 100% on VPS, no Mac needed
- Built linkedin-add-to-sheet.py: auto-adds GO jobs (>=82%) to Google Sheet via gog
- Tested pipeline on 5 jobs: 4 SKIP (Dalil IT 58%, Talan CTO 68%, Insurance CTO 35%, IT Director Riyadh 66%), 1 GO (Senior Director Tech UAE 87% - added to Sheet row 7)
- CV build for Senior Director Tech (Confidential UAE) spawned as Opus sub-agent (in progress)
- Context hit 86% - session flushed

## Open Threads
1. CV build for Senior Director Technology - Opus sub-agent running, will auto-announce
2. Ahmed triaging more LinkedIn jobs - pipeline continues
3. Monthly model routing audit cron: still not created
4. "Process sheet" on-demand trigger: discussed, not yet built
5. Bayt integration into Job Radar: recommended, not yet done

## Key Decisions
- Google Sheet = primary pipeline tracker (not pipeline.md)
- LinkedIn URL workflow: send URL → VPS fetches JD → ATS score → auto-add if >=82%
- Cookie: li_at stored in config/linkedin-cookies.json (gitignored)
- ATS threshold: 82% (MiniMax calibrated)

## State
- Pipeline: 47 applied + 1 new GO (Senior Director Tech, row 7)
- LinkedIn cookie: active, months before expiry
- Scripts committed: linkedin-jd-fetcher.py, linkedin-cookie-setup.py, linkedin-add-to-sheet.py


Updated: 2026-03-05 10:27 UTC

## What We Did
- ATS scoring model benchmark (MiniMax vs Haiku vs Opus): MiniMax won, locked as primary scorer
- Claude quota full audit: all crons moved to MiniMax, 0 Claude background tasks remaining
- Google Sheet enhanced: CV GitHub Link (M), Ready to Apply (N), Duplicate Check (O)
- Built 2 CVs end-to-end: Director DT (87%) and Head PMO (88%), both ready to apply
- Borderline tie-breaker protocol automated (no manual approval)

## Open Threads
- Monthly model routing audit cron: needs to be created
- "Process sheet" on-demand trigger: discussed, not yet built
- Context hit 70%: session flushed Context

*Updated: 2026-03-05 07:31 UTC*

## What We Were Doing
Morning maintenance + job pipeline triage session with Ahmed.

## Key Decisions
- Brave Search fully removed (no API key, never had one)
- Job Radar rebuilt with JobSpy (replaces Tavily)
- Pipeline sorting rules locked: Active by date, Radar by priority
- Ahmed reviewing radar jobs one by one, skipping medium priority items
- Ahmed about to send fresh LinkedIn jobs for review/CV tailoring

## Open Threads
1. Ahmed sending fresh LinkedIn job links (in progress when session ended)
2. 11 radar items remaining (medium/low priority, can triage later)
3. Morning briefing cron had wrong post for today (showed yesterday's Salesforce post instead of today's compound growth post)

## State
- Pipeline: 47 applied, 11 radar remaining
- Fugro applied (ATS 90%)
- 4 radar items skipped (Michael Page duplicate, Bosperous PHP, The IN Group recruitment, Careem ML)
