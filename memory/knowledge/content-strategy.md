# Content Strategy — LinkedIn Intelligence

*Last updated: March 7, 2026*

## HIGH PRIORITY: Why your OpenClaw agent forgets everything (and how to fix it)
**Source:** https://youtu.be/oN__gKJnPls
**Author:** VelvetShark
**What:** 15-second teaser on OpenClaw memory/context issues and the 3-layer memory system that fixes it. Covers: built-in settings most users never tune + advanced semantic search across knowledge base.
**Relevance:** CRITICAL for our current issues: (1) Telegram messaging broken - can't resolve chat IDs, (2) Memory Index cron failing - timeout after 300s, (3) session context management
**Comments:** "masterclass", "changes strategies in a major way", "I now know why my OpenClaw does what it does"
**Status:** HIGH PRIORITY. Must watch and apply fixes to our system.

## Banked: Shape Up Skills for AI Agents (Mar 6, 2026)
**Source:** https://x.com/nurijanian/status/2024804843689582711 + https://github.com/rjs/shaping-skills
**Author:** Ryan Singer (@rjs, Shape Up creator), promoted by George Nurijanian (41K, prodmgmt.world)
**Engagement:** 751 likes, 1,765 bookmarks (158K views)
**What:** Claude skills for Shape Up: /shaping, /breadboarding, /framing-doc, /kickoff-doc
**Use for Ahmed:** (1) OpenClaw skill for scoping transformation programs at next role, (2) LinkedIn angle: Shape Up + AI + $50M healthcare transformation, (3) Hook pattern for pipeline ripple-effect checks
**Status:** Banked. Trigger: new role start or content gap

## Implemented: Taskmaster Completion Guard (Mar 6, 2026)
**Source:** https://x.com/blader/status/2021102830933643775 + https://github.com/blader/taskmaster
**Author:** Siqi Chen (@blader, CEO of Runway)
**Engagement:** 622 likes, 62 replies
**What:** Stop hook for Claude Code/Codex that blocks agents from stopping until task is 100% complete. Uses deterministic DONE token, compliance prompts, same-session recovery.
**Action taken:** Adapted pattern for OpenClaw. Added Completion Guard protocol: TASK_COMPLETE token required in all sub-agent output. Missing token = failed task. Added to TOOLS.md (full protocol), AGENTS.md (rule reference), SOUL.md (enforcement).
**Status:** IMPLEMENTED. Active in all future sub-agent spawns.

## Banked: Mission Control by crshdn (Mar 6, 2026)
**Source:** https://x.com/tom_doerr/status/2025880482760507780 + https://github.com/crshdn/mission-control
**Author:** Tom Dörr (@tom_doerr), now rebranded as Autensa
**Engagement:** 401 likes, 18 replies
**What:** Open-source AI agent orchestration dashboard for OpenClaw. Kanban board, multi-agent pipeline (Planning→Inbox→Assigned→In Progress→Testing→Review→Verification→Done), fail-loopback routing, Learner agent that captures lessons and injects into future dispatches, Docker-ready, WebSocket gateway integration.
**Use for Ahmed:** (1) Reference architecture if rebuilding MC v4 post-job-search, (2) Steal: fail-loopback routing pattern for sub-agents, (3) Steal: Learner agent auto-injecting LEARNINGS.md into sub-agent briefs, (4) Fork candidate for proper task orchestration in new executive role.
**Status:** Banked. Trigger: MC v4 rebuild or new role requiring team-scale agent orchestration.

## Deployed: Camofox Anti-Detection Browser (Mar 6, 2026)
**Source:** https://x.com/pradeep24/status/2021319785947316490 + npm camofox-browser
**What:** OpenClaw plugin wrapping Camoufox engine for stealth browsing. REST API + CLI.
**Action taken:** Installed v2.0.4, systemd service running on port 9377, rewrote JD fetcher + scout to use it, Playwright fallback retained. LinkedIn auth confirmed working.
**Status:** DEPLOYED. First real scout test: Monday Mar 9.

## Banked: Awesome CTO Resource Repo (Mar 6, 2026)
**Source:** https://x.com/Franc0Fernand0/status/2021544169085313076 + https://github.com/kuchin/awesome-cto
**Author:** Fernando (@Franc0Fernand0), repo by @kuchin
**Engagement:** 2,424 likes, 25 replies
**What:** Curated GitHub repo of CTO/VP-level resources: software dev processes, technical hiring, software architecture, product/project management, career growth.
**Use for Ahmed:** Interview prep resource for tech-heavy roles (FAB VP Tech, Aiwozo, similar). Cherry-pick specific articles to prep talking points on architecture decisions, scaling engineering orgs, technical hiring frameworks.
**Status:** Banked. Trigger: pre-interview prep for CTO/VP Technology roles.

## Banked: Self-Optimizing AI Agents / Repo Optimizer (Mar 6, 2026)
**Source:** https://x.com/koushik77/status/2021972025372553444 + https://github.com/ksenxx/kiss_ai
**Author:** Koushik Sen (@koushik77), KISS AI framework creator
**Engagement:** 258 likes, 14 replies
**What:** 69-line Python script that points a coding agent at its own repo. Agent self-optimized overnight, cut its own cost by 98%. Key concepts: GEPA prompt optimizer (auto-tunes prompts for cost/quality), RelentlessAgent (self-evolved to reduce cost over time), "point the agent at itself" pattern.
**Use for Ahmed:** (1) LinkedIn post angle: "I let my AI optimize itself overnight" mapped to real OpenClaw self-healing agent + model routing audit story, (2) Technique: automated prompt tuning loop for cron/sub-agent briefs (run 10 ways, pick cheapest that maintains quality), (3) Expands our self-healing pattern from error recovery to cost optimization
**Status:** Banked. Trigger: LinkedIn content gap or when optimizing cron fleet prompts.

## Core Positioning
- **Ahmed's angle**: Digital Transformation Executive with real execution credibility (not consultant)
- **Differentiation**: $50M PMO across 15 hospitals, HealthTech implementation, GCC-scale delivery
- **Voice**: First-person, direct, data-backed, execution-obsessed

## Winning Hooks (Proven)
1. "I just spent [time] with [executive type]. Here's what I learned." — First-person authority + insider observation
2. "[Number] things I see in [industry] exec meetings" — Insider credibility + curiosity gap
3. "We inherited [problem]. Here's how we turned it around." — Transformation story with specific results
4. "Most people think [common belief]. They're wrong." — Contrarian take, challenges assumptions
5. "Question for the network:" — Direct engagement, algorithm-friendly

## Dominant Formats (Current)
- **First-person transformation stories**: "We fixed X in Y days" with specific numbers. 35%
- **Contrarian takes**: Calling out AI hype and transformation theater. "10x" debunking gaining momentum
- **Data-driven lists**: 5-item numbered lists with GCC-specific data. 25%
- **Question-led engagement**: Ending with direct questions to network. 15%

## Hot Topics (Ride These)
- **Agentic AI in enterprise**: Salesforce's Agentforce $800M ARR signals agentic wave hitting enterprise
- **Healthcare data unification**: Health Catalyst + KLAS implementations at enterprise scale
- **Value-based care execution**: GCC shifting from ambition to measurable outcomes
- **PMO as AI leader**: "PMOs Must Lead AI Adoption" positioning continues strong
- **Family office hiring**: Dubai family offices paying $50K+/month for digital transformation leaders

## Oversaturated (Avoid)
- **"AI 10x revenue" posts**: Already called out as viral lie
- **Generic transformation vision statements**: Need specific execution stories
- **Pure AI tool tutorials**: Without GCC/regional context, too generic

## Post Templates

### Transformation Story
"We inherited [problem]. Here's how we turned it around."
- Lead with specific pain: "6 months behind schedule"
- Show the turnaround: "90 days"
- Add proof point: "Health Catalyst + KLAS"
- End with lesson or question

### Insider List
"[Number] things I see in [industry] exec meetings"
- First-person authority: "I've sat through 12 steering committees"
- Numbered insights: 3-5 specific observations
- GCC data: Saudi 96% e-gov, $38B investment
- Engagement: "Thoughts? Drop yours below."

### Contrarian Take
"Most people think [common belief]. They're wrong."
- Challenge the myth: "IT drives transformation"
- Flip the script: "It's governance + data quality first"
- Prove with evidence: specific PMO lesson from TopMed
- Invite debate: "Agree or disagree?"

### Observation Hook
"I just spent [time] with [executive type]"
- Credibility: "12 executive steering committees in the last month"
- Insight: "Here's what's actually driving decisions"
- GCC context: regional specifics
- CTA: question to network

---

## Historical Top Posts (Reference)

### Week of March 16, 2026
1. Anas Hidaoui — "The most viral LinkedIn lie in 2026: I replaced my entire team with AI and 10x'd revenue" — debunking hook
2. Hussain Bandukwala — "PMOs Must Lead AI Adoption in 2026" — PMO positioning
3. Rebecca Farooq — "Digital Shift in UAE and GCC: 2026 Priorities" — 96% e-gov, $38B
4. Mustafa Al Usaji — "Transformation in the GCC is no longer about vision, it's about execution"

### Week of March 9, 2026
1. Anas Hidaoui — "The most viral LinkedIn lie in 2026" — viral debunking
2. Kane Macey — "UAE Business Leaders in 2026" — 84% CEO optimism
3. Hussain Bandukwala — "PMOs Must Lead AI Adoption" — governance angle
4. Michael Masset — "I have just spent a few days in Dubai" — first-person

### Week of March 2, 2026
1. Kane Macey — "UAE Business Leaders in 2026: AI, Sustainability, and Transformation"
2. Michael Masset — "I have just spent a few days in Dubai"
3. Oliver Wyman — "5 Trends That Will Redefine the Region's Health Landscape in 2026"

---

## Weekly Intelligence Archive
- [[weekly-content-brief.md]] — Current week brief
- [[weekly-content-brief.md|2026-W12]] — Week of March 16
- [[weekly-content-brief.md|2026-W11]] — Week of March 9
- [[weekly-content-brief.md|2026-W10]] — Week of March 2

### Week of March 5, 2026 (Current)
1. Anas Hidaoui — "The most viral LinkedIn lie in 2026: I replaced my entire team with AI and 10x'd revenue" — debunking hook (continuing strong)
2. Hussain Bandukwala — "PMOs Must Lead AI Adoption in 2026" — PMO positioning continues resonating
3. Oliver Wyman — "5 Trends That Will Redefine the Region's Health Landscape in 2026" — HealthTech focus
4. Mustafa Al Usaji — "Transformation in the GCC is no longer about vision, it's about execution"
5. Emerging: Agentic AI posts gaining traction as Salesforce Agentforce $800M ARR signal spreads

---

## Intelligence Sources
- **Primary**: LinkedIn feed monitoring (requires auth)
- **Backup**: Web search for GCC/HealthTech/AI trends
- **Key voices**: @AnasHidaoui @HussainBandukwala @KaneMacey @MustafaAlUsaji @OliverWyman @RebeccaFarooq

## Configuration Needed
- [ ] Brave Search API key for automated discovery
- [ ] LinkedIn browser automation session

## Captured Source Links
- 2026-03-06: YouTube, "OpenAI just dropped GPT-5.4 and WOW...." by Matthew Berman, https://youtu.be/rvdUBieefR0?si=W4bxrMHLNe3-9Dea
