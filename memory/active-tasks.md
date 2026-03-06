# Active Tasks

*Last updated: 2026-03-05 13:37 UTC*

## 🔴 URGENT
- [x] ~~Retry Sheet row 16 update: K16="Applied", L16="2026-03-05"~~ ✅ Done Mar 6
- [x] ~~Apply to remaining CV-ready jobs: EDB Field CTO, eMagine Head of AI Advisory~~ ✅ Both applied Mar 6
- [ ] **Nuxera.AI — Sr PM AI Healthcare (Cairo):** CEO Amin Elhemaily responded directly on LinkedIn. Ahmed messaged salary-oriented stance. Awaiting Amin's reply. If positive, push for in-person meeting during Ramadan (both in Cairo). Research Nuxera before any meeting.

## 🟡 Follow-up Policy
- No proactive follow-ups for standard LinkedIn applications.
- Follow-up only when: (1) post-interview silence, or (2) active recruiter thread goes quiet.

## 🟡 In Progress

### Advisory Board Implementation
- **Status:** ✅ STARTED Mar 2
- **Progress:** Phase 2 daily and weekly engines executed successfully
- **Next:** Monitor scheduled runs and tune stale inputs

### LinkedIn Content Engine
- **Status:** ✅ LIVE (Sun-Thu at 11:30 AM Cairo)
- **Week 2 (Mar 2-6):** Complete on GitHub
- **Weeks 3-5:** Drafting and image production in progress, due Mar 7
- **Next:** Ahmed review and posting flow continues

### LinkedIn Job Scout CVs
- **Status:** 3 of 4 GO jobs processed + Fresh scout run Friday 6 AM
- **eMagine Head of AI Advisory (96%):** CV ready, pending Ahmed apply (HIGH PRIORITY)
- **Anduril Sr. Manager PM (64% real):** SKIP, Secret Clearance required
- **Dubai Holding Director PM (75%):** ❌ Job closed
- **Fresh Results (Fri Mar 6):** 56 unique jobs from 60 searches (10 keywords × 6 GCC countries)
- **Top Candidates for Next Round:**
  - Roblox General Manager MENA (Remote)
  - EDB Field CTO EMEA (Remote)
  - ALDAR Senior VP Master Planning Projects (Abu Dhabi)
  - Mashreq Manager GTB Digital Transformation PMO (UAE)
  - The Cigna Group Head of Transformation (Dubai)
- **Alert:** Playwright script timed out at search 29/60; previous day completed successfully. Need reliability fix.
- **Next:** Score top 5 new opportunities, prioritize eMagine application

### Knowledge Bank
- **Status:** Active
- **Location:** `memory/knowledge/content-strategy.md`
- **Next:** Continue banking frameworks from new content

### Gmail Optimization (Mar 6)
- **Status:** ✅ LIVE
- **Done:** OAuth fixed to writable scopes (gmail.modify + gmail.settings.basic + gmail.settings.sharing)
- **Done:** Auto-labels created (`JOB-ACTIONS`, `JOB-RECEIPTS`, `MARKET-NEWS`)
- **Done:** Filters created for LinkedIn alerts/newsletters/receipts + Workable/Teamtailor priority
- **Backlog cleanup:** 2,652 LinkedIn alerts archived, 145 newsletters archived, 650 LinkedIn receipts archived, 84 recruiting-system threads labeled priority
- **Next:** 24h impact check, then tighten rules only if needed

### Cron Hardening (NEW — Mar 6)
- **Status:** ✅ COMPLETE
- **Done:** bestEffort on all 32 jobs, failure alerts on 8 critical jobs, models pinned, KillMode=mixed applied, weekly gateway restart cron added
- **Triggered by:** Kevin Simback's OpenClaw cron troubleshooting article

### Skill Framework Overhaul (NEW — Mar 6)
- **Status:** ✅ COMPLETE (Phase 1-3)
- **Phase 1:** Archived 15 dead skills, optimized descriptions on 4 key skills, installed Anthropic skill-creator
- **Phase 2:** Eval-driven improvements to executive-cv-builder (Step 0 pre-flight, quality gates, failure modes table)
- **Phase 3:** OpenClaw adapter for Anthropic framework, new skill template
- **Next:** Use framework for any future skill creation/improvement

### OpenClaw System Review
- **Status:** In progress with Ahmed
- **Completed:** Round 1 and Round 2
- **Next:** Round 3 plus gap fixes

### Mission Control v3
- **Status:** ✅ COMPLETE Mar 4, 2026
- **Phase 1+2:** Live data from all workspace files (tasks, pipeline, content, memory, goals)
- **Phase 3:** Full UX overhaul (glassmorphism, command palette Ctrl+K, sync indicator, heartbeat, cron traffic lights)
- **Access:** https://srv1352768.tail945bbc.ts.net:4443/dashboard
- **Build:** Lint + Build passing
- **Next:** None - mission complete

### CV Creation Pipeline
- **Status:** Active
- **Master CV:** `memory/master-cv-data.md`
- **Pending updates:** none
- **Latest:** Fugro Head of Project Excellence (ATS 90%, Applied Mar 5)

### LinkedIn JD Fetcher (NEW — Mar 5)
- **Status:** ✅ LIVE
- **How:** Send any LinkedIn job URL in Telegram → VPS fetches full JD via Playwright + cookie → ATS score + Go/Skip verdict returned
- **No Mac needed** — runs 100% on VPS
- **Cookie:** `config/linkedin-cookies.json` (gitignored) — expires in months, refresh via `linkedin-cookie-setup.py`
- **Scripts:** `scripts/linkedin-jd-fetcher.py`, `scripts/linkedin-cookie-setup.py`

### Job Radar v3 (JobSpy)
- **Status:** ✅ LIVE
- **Engine:** python-jobspy (LinkedIn, Indeed, Google Jobs)
- **Cron:** Daily 7 AM Cairo
- **Auto-pipeline:** Executive matches auto-added as 🆕 Discovered
- **Radar triage:** Down from 15 to 11 (4 skipped with Ahmed)

## 🟢 Recurring
- Daily job radar checks
- Daily OpenAI entitlement check: test GPT-5.4 availability in runtime, alert Ahmed immediately when allowed
- Update memory after each session
- Daily notes in `memory/YYYY-MM-DD.md`

## ✅ Recently Completed
- Delphi: Closed Mar 4 (no response after follow-up)
- LinkedIn Weeks 3-5: ✅ COMPLETED Mar 4. 15 posts + 15 images pushed to GitHub.
- OpenAI Codex JWT risk resolved (OAuth active)
- GitHub 2FA completed
- Delphi follow-up sent to Kritika Chhabra
- Threads bio updated
- Cooper Fitch application already submitted and confirmed
- Delphi interview prep and interview completed
- Gmail cleanup automation
- ATS best practices guide
- Memory system implementation

---

**Links:** [[../GOALS.md]] | [[../MEMORY.md]] | [[pending-opus-topics.md]] | [[lessons-learned.md]]
