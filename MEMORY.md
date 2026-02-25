# MEMORY.md — Long-Term Context

*Last updated: 2026-02-24*
*Maintained by: NASR*
*Rule: If it's not here, it doesn't exist across sessions.*

---

## 🧠 Who Ahmed Is — The Non-Negotiables

- Senior tech executive, 20+ years, GCC & Egypt
- Currently: Acting PMO at TopMed (Saudi German Hospital Group)
- Managing $50M digital transformation, 15-hospital network
- Target: VP / C-Suite in Dubai — Q3 2026
- Salary floor: 50,000 AED/month
- MBA in progress: Paris ESLSCA (2025-2027)
- Location: Cairo, Egypt — Africa/Cairo (UTC+2)
- Certifications: PMP, CSM, CSPO, Lean Six Sigma, CBAP + technical stack

---

## 🎯 Current Strategic Priorities

*(Update weekly — owned by NASR)*

1. Land executive role — Dubai, Q3 2026
2. Follow up on Delphi interview — completed Feb 24, 2026 (awaiting feedback)
3. Complete OpenClaw system review and gap fixes
4. LinkedIn executive positioning — 2-3 posts/week
5. TopMed PMO delivery — $50M transformation on track

---

## 🎯 NASR's Three Non-Negotiables

1. **Always Proactive** — Surface risks, opportunities, deadlines without being asked. Silence = failure.
2. **Always Connect the Dots** — Cross-reference job pipeline ↔ LinkedIn ↔ interview prep ↔ TopMed ↔ MBA. Call out connections Ahmed shouldn't have to ask about.
3. **Always Recommend** — Never deliver information without a clear recommendation. Lead with "here's what I'd do and why."

## 💼 Work & Communication Preferences

### How Ahmed Thinks

- Strategic over operational — always zoom out first
- Impatient with repetition — never re-ask what's in memory
- Wants to be challenged — don't just validate
- Expects proactive surfacing of risks and opportunities
- Three options > one recommendation

### Communication Style

- Direct and concise — lead with the insight
- Time-sensitive items go to the TOP, never buried
- Label options clearly: Option A / B / C
- No hand-holding, no over-explaining, no empty enthusiasm

### Red Lines — Never Do These

- Waste his time with generic advice
- Repeat context he's already given
- Soften feedback to protect feelings
- Suggest solutions that require starting over
- Let deadlines slip without flagging 48hrs in advance

---

## 🤖 AI Automation Ecosystem

### OpenClaw Agent Registry

| Agent | Folder | Role | Status |
|-------|--------|------|--------|
| NASR 🎯 | main | Main strategic consultant | Active |
| CV Optimizer | cv-optimizer | ATS-optimized CVs, 85%+ score | Active |
| Job Hunter | job-hunter | Executive job sourcing & pipeline | Active |
| Researcher | researcher | Deep intelligence & research | Active |
| Content Creator | content-creator | LinkedIn content & positioning | Active |

### Infrastructure

- VPS: Hostinger
- Interface: Telegram
- Memory: Markdown files on disk + semantic search (local embeddings)
- Models: Hybrid strategy (cost-optimized)
- Deprecated (remove): M2.1, M2.1-highspeed

### Key File Locations

| File | Purpose |
|------|---------|
| SOUL.md | NASR personality and operating rules |
| USER.md | Ahmed's profile and preferences |
| AGENTS.md | Operating manual and safety rules |
| GOALS.md | Live strategic objectives |
| MEMORY.md | This file — long-term context |
| memory/active-tasks.md | Current task tracker |
| memory/pending-opus-topics.md | Queued deep work |
| memory/master-cv-data.md | CV source of truth |
| memory/ats-best-practices.md | ATS optimization rules |
| memory/lessons-learned.md | Mistake log |
| memory/YYYY-MM-DD.md | Daily journals |

---

## 📄 CV & Job Search Rules

### CV Design Rules

- ATS score floor: 85% before any submission
- Positioning: Digital Transformation Executive — NOT consultant
- Master CV location: memory/master-cv-data.md
- Each application gets a tailored version — never submit the master raw

### Application Standards

- Match job keywords explicitly — ATS reads literally
- Quantify everything: scale, budget, team size, % improvement
- Lead with impact, not responsibility
- Salary target: 50,000-55,000 AED/month — don't anchor low

### Active Job Pipeline

*(Sync with GOALS.md — source of truth lives there)*

- Delphi Consulting — Senior AI PM — Interview completed Feb 24, 2026 — awaiting feedback (days)

---

## 🧩 Model Strategy

*(Cost-optimization rules)*

| Task Type | Model | Reason |
|-----------|-------|--------|
| Deep strategy, interview prep | Opus | Best reasoning |
| CV tailoring, drafting | Sonnet | Balanced cost/quality |
| Quick lookups, formatting | Haiku | Fast and cheap |
| Local tasks | Local model | Zero API cost |

Rule: Match model to task complexity. Never use Opus for what Haiku can do.

---

## 📚 Lessons Learned

*(Running log — add don't delete)*

- 2026-02-24: **NEVER run raw heavy installs (npm, apt, pip) during active sessions.** Starves VPS CPU/RAM → all LLM requests timeout. If install needed: (1) non-urgent → off-hours cron, (2) needed now → detached tmux `tmux new-session -d -s install '...'`, (3) urgent → throttle with `nice -n 19 ionice -c 3 npm install`. Always warn Ahmed first. Rule applies ALL models, ALL sessions.
- 2026-02-24: LLM timeout bumped from 60s → 120s in openclaw.json for better resilience on large-context / Opus tasks.
- 2026-02-24: **memory/ is KNOWLEDGE-ONLY.** Sub-agent installed playwright inside memory/ (14MB, 546 files). Fixed: .gitignore + README + AGENTS.md rule added. Never install packages or create code files in memory/.
- 2026-02-24: Agent names changed — no more personal names. Now: CV Optimizer, Job Hunter, Researcher, Content Creator (NASR stays).
- 2026-02-24: All crons + heartbeats → MiniMax-M2.5 only. Reasoning disabled globally.
- 2026-02-24: Monthly maintenance cron created (1st of month, 9AM Cairo) — runs full 6-step cleanup + system checks automatically.
- 2026-02-24: Mission Control gateway WebSocket integration complete — auth uses Ed25519 challenge-response with device keys from ~/.openclaw/identity/. Use `require("ws")` not `import WebSocket from "ws"` in Next.js (TypeScript type issue with ws package).
- 2026-02-24: Mission Control full data audit — fixed 10 issues: model costs, deprecated models, active jobs count, priorities parsing, Lab tool names, My Tasks contradiction, Memory Highlights parsing, agent names, sync alert threshold, Tailscale port.
- 2026-02-24: Tailscale Serve now points to Mission Control (port 3005) not gateway (port 18789). URL: https://srv1352768.tail945bbc.ts.net
- 2026-02-24: Delphi interview completed (strong, no tricky questions) — awaiting feedback "in days".

- 2026-02-21: Session compaction before flush = context loss.
  Fix: Mandatory flush protocol added to SOUL.md and AGENTS.md
- 2026-02-21: active-tasks.md went 4 days stale — missed Delphi deadline
  Fix: Staleness alerts added to AGENTS.md (48hr threshold)
- 2026-02-21: Full system overhaul — rebuilt all core files, cleaned models, created agent configs, set up GitHub backup, added sub-agent timeout (300s), configured auto-injection of active-tasks + pending-opus + GOALS
- 2026-02-21: airllm.md polluted every memory_search query — dense keyword files poison the small embedding model
  Fix: Deleted file, re-indexed, added Memory Hygiene Rules to AGENTS.md
- 2026-02-22: Sub-agents can delete critical files silently during rewrites (MC Phase 2 deleted layout.tsx, globals.css). Fix: always check git diff after sub-agent build tasks and verify no deletions before declaring done.
- 2026-02-21: Sub-agents don't auto-send deliverables — had to be asked
  Fix: Delegation protocol updated — send PDF immediately on completion with link + ATS score
- 2026-02-21: PDF naming now standard: "Ahmed Nasr - [Role] - [Company].pdf"
- 2026-02-21: Ahmed prefers tables over bullets for comparisons
- 2026-02-21: Silence rule established — no-action items = no notification to Ahmed
- 2026-02-17: pending-opus-topics.md items lost in session reset
  Fix: pending-opus-topics.md now mandatory in startup sequence

---

## ✅ Completed Milestones

*(Archive of wins — context for future decisions)*

- Gmail fully automated via Himalaya
- Memory system implemented and operational
- ATS best practices guide created
- AI Marketing Toolkit (4 skills created)
- Discord community research (Feb 21, 2026)
- Multiple CVs created: IT Section Head, IT Director, Strategy Consultant
- OpenClaw system architecture review (Feb 21, 2026)
- Full system overhaul: all core files rebuilt, models cleaned, backup to GitHub, sub-agent architecture documented (Feb 21, 2026)
- Delphi CV created: ATS 91% (Feb 21, 2026)
- 7 CVs created and sent in one session: Payfuture, FAB, Carter Murray, Citco, 3x Confidential Riyadh
- Mission Control Phase 1 COMPLETE — all 8 pages (Command Center, HR, Marketing, OPS, Intelligence, Team, Lab, Settings) + sync engine + layout shell, live on port 3005, pushed to GitHub (Feb 22, 2026)
- Mission Control permanently accessible via Tailscale: https://srv1352768.tail945bbc.ts.net (port 3005, PM2 managed, auto-starts on reboot). Available on all devices — Mac, iPhone, iPad. No SSH tunnel needed.
- Mission Control Phase 2 COMPLETE (Feb 22, 2026) — mobile support, sync monitoring (15s debounce), data consistency (markdown canonical), Command Center collapsible stats + 7-day alerts, trending indicators, blocker tracking in OPS. GitHub @ 6483ebf.
- Two GitHub repos: openclaw-nasr (workspace) + openclaw-config (config)
- Delphi interview completed Feb 24, 2026 — strong performance, awaiting feedback
- Mission Control Phase 3 COMPLETE (Feb 24, 2026) — gateway WebSocket integration, full data audit (10 fixes), Tailscale redirected to port 3005, model costs corrected, all fake data eliminated. GitHub pushed.
- Mission Control Phase 4 COMPLETE (Feb 24, 2026) — 3-level navigation implemented. Level 1: dashboard cards. Level 2: slide-in panels (5 panels: Jobs, Tasks, Agents, Content, Goals). Level 3: existing full pages linked via "View All". SlidePanel.tsx reusable component created. Mobile responsive.

---

## 🔄 Memory Maintenance Rules

| Trigger | Action |
|---------|--------|
| Decision made | Write to this file under relevant section |
| Preference learned | Add to Work & Communication Preferences |
| Lesson learned | Add to Lessons Learned with date |
| Milestone completed | Move to Completed Milestones |
| Session ends | Flush daily log to memory/YYYY-MM-DD.md |
| active-tasks.md > 48hrs old | Flag to Ahmed immediately |

NASR Rule: Update this file at session close. Always. Text > Brain. If it's not written, it's already forgotten.

---

**Links:** [[USER.md]] | [[SOUL.md]] | [[AGENTS.md]] | [[TOOLS.md]] | [[GOALS.md]] | [[memory/active-tasks.md]] | [[memory/pending-opus-topics.md]] | [[memory/master-cv-data.md]] | [[memory/lessons-learned.md]]

---

## 📚 Knowledge Index — All Connected Notes

### Core System Files
- [[USER.md]] — Ahmed's profile and preferences
- [[SOUL.md]] — My personality and rules
- [[AGENTS.md]] — Operating manual
- [[TOOLS.md]] — Tool reference
- [[IDENTITY.md]] — My identity
- [[HEARTBEAT.md]] — Periodic task rules

### Goals & Tasks
- [[GOALS.md]] — Strategic objectives
- [[memory/active-tasks.md]] — Current tasks
- [[memory/pending-opus-topics.md]] — Queued deep work

### CV & Job Search
- [[memory/master-cv-data.md]] — CV source of truth
- [[memory/cv-history.md]] — CV applications history
- [[memory/ats-best-practices.md]] — ATS optimization
- [[memory/interview-prep-protocol.md]] — Interview prep
- [[memory/job-pipeline.md]] — Active job pipeline

### Daily Memory
- [[memory/2026-02-24.md]] — Latest daily log
- [[memory/2026-02-23.md]] — Feb 23 session
- [[memory/2026-02-22.md]] — Feb 22 session
- [[memory/2026-02-21.md]] — Feb 21 session
- [[memory/2026-02-20.md]] — Feb 20 session
- [[memory/2026-02-19.md]] — Feb 19 session
- [[memory/2026-02-18.md]] — Feb 18 session
- [[memory/2026-02-17.md]] — Feb 17 session
- [[memory/2026-02-16.md]] — Feb 16 session
- [[memory/2026-02-15.md]] — Feb 15 session

### Case Studies
- [[case-study-talabat.md]] — Talabat experience
- [[case-study-sgh.md]] — Saudi German Hospital
- [[case-study-network.md]] — Network International

### Content & LinkedIn
- [[linkedin_posts.md]] — LinkedIn posts
- [[memory/linkedin_content_calendar.md]] — Content calendar
- [[memory/content-ideas.md]] — Content ideas
- [[drafts/2026-02-24-linkedin-ai-pmo.md]] — Latest draft

### Skills & Tools
- [[skills/linkedin-writer/SKILL.md]] — LinkedIn writing skill
- [[skills/resume-optimizer/SKILL.md]] — CV optimization skill
- [[skills/job-search-mcp/SKILL.md]] — Job search skill
- [[skills/content-claw/SKILL.md]] — Content analysis skill

### Mission Control
- [[memory/mission-control-spec.md]] — Mission Control spec
- [[memory/mission-control-concept.md]] — Concept document
- [[memory/mission-control-phase2-design.md]] — Phase 2 design

### Learning
- [[memory/lessons-learned.md]] — Mistakes and lessons
- [[memory/agentic-levels.md]] — Agent maturity levels
- [[PRINCIPLES.md]] — Core principles

### Other Key Docs
- [[MASTER_CV.md]] — Master CV document
- [[EXECUTIVE_TRANSFORMATION_PLAYBOOK.md]] — Transformation playbook
- [[LINKEDIN_DEEP_ANALYSIS.md]] — LinkedIn strategy
- [[email-templates.md]] — Email templates
- [[job-application-tracker.md]] — Job tracker
