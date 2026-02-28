# Tools & Methods Knowledge Bank

*Auto-indexed by QMD. Search with: memory_search("framework method [topic]")*

---

## Claude Code Remote Control (Mobile) | 2026-02-28
**Source:** https://www.youtube.com/watch?v=L36aPV6g2II (Alex Finn, 133K subs, 13K views, 1 day old)
**Type:** YouTube Video / Tutorial

**Key Insights:**
- Anthropic released `/remote-control` for Claude Code: run code sessions from your phone while execution continues locally on your computer. No SSH, no terminal emulation needed.
- Workflow: Start project on computer, type `/remote-control` in Claude Code, session is pushed to Claude mobile app. You keep prompting from phone, code builds on your local machine.
- No cloud execution, no merge conflicts, no pulling down code. Everything stays in one local environment.
- Two phone options: (1) browser link or (2) Claude iOS/Android app (auto-loads the active session)
- Alex Finn's verdict: Claude Code Remote Control = deep technical builds. OpenClaw = autonomous agents running while you sleep. Different tools, different purposes.

**Actionable for Ahmed:**
- Directly relevant to your setup: Claude Code mobile lets you continue prompting your VPS agent from your iPhone without Telegram friction.
- LinkedIn content angle: "The future of work isn't your laptop. It's your laptop doing the work while you're at the gym." Frame around mobile-first executive productivity.
- Interview signal: Knowing this at release week shows you track AI developer tools at the frontier. Valuable for VP/CTO-adjacent roles.

**Tags:** #claude-code #mobile #remote-control #openclaw #ai-tools #productivity

---

## Least-to-Most + Plan-and-Solve Prompting | 2026-02-26
**Source:** Prompt Guy newsletter (thinkaiprompt.beehiiv.com)
**Type:** Newsletter / Technique Guide

**Key Insights:**
- Complex single prompts spread attention across all parts, producing breadth without depth
- Task overload: AI covers everything in the same thin layer
- Least-to-Most: List sub-problems first, solve sequentially, paste previous outputs as context
- Plan-and-Solve: Exact phrasing matters — "let's first understand the problem fully and make a plan" outperforms standard "think step by step"
- The sequencing is the skill, not the individual prompt

**Least-to-Most Template:**
- Phase 1: "I need to accomplish [task]. List the sub-problems in order. Don't solve yet."
- Phase 2: "Now solve sub-problem 1 only. Specific and thorough. Output feeds next."

**Plan-and-Solve Template:**
- Task: [specific]
- Context: [background + constraints]
- Instructions: "Let's first understand the problem fully and make a plan. Then carry out step by step."

**Actionable for Ahmed:**
- Apply to agent task design (CV Optimizer, Job Hunter, Researcher, Content Creator)
- Better prompt sequences = better agent outputs
- Use for LinkedIn content frameworks, job application analysis, research synthesis
- Next module covers Tree-of-Thought for multi-path reasoning

**Tags:** #prompting #ai-techniques #workflow-design #agent-optimization

---

## Save Thousands on OpenClaw: Claude Subscription Instead of APIs | 2026-02-26
**Source:** YouTube (Andrew from Cloud Code meetup + Caleb Hodes from God Mode)
**Type:** Video / Tutorial

**Key Insights:**
- Use Claude subscriptions ($20-$200/month) instead of pay-per-token API fees
- Connect Claude Code (VS Code extension) to your subscription token
- Process: Install Claude Code in VS Code → Get token from Anthropic → Nuke old API keys → Reconnect OpenClaw to use subscription
- OpenClaw has 430,000 lines of code, so switching LLMs can be complicated (need to nuke old configs)
- Can use Sonnet or Opus 4.6 with the subscription
- $20/month plan works for demos, $200/month for heavy use
- This bypasses API token pay-per-token pricing

**Actionable for Ahmed:**
- Consider switching from MiniMax pay-per-token to Claude subscription for cost predictability
- Current MiniMax: $40/mo + API usage
- Claude subscription: $20-$200/month flat, unlimited use within limit
- Alternative: Keep MiniMax for daily ops, use Claude subscription for heavy tasks

---

## Using Claude Subscription with OpenClaw - Full Guide | 2026-02-26
**Source:** The Next New Thing (Andrew Warner) - n.thenextnewthing.ai
**Type:** Tutorial / Guide

**Key Insights:**
- Use Claude Max subscription ($20-$200/month) instead of pay-per-token Anthropic API
- Step-by-step: Get token → Nuke API keys → Add OAuth → Restart → Set Opus 4.6 as default
- VS Code required (free download)
- Process:
  1. Terminal: `claude setup-token` to get token
  2. VS Code: Nuke old API keys (delete ~/.openclaw/auth-profiles.json, remove ANTHROPIC_API_KEY from .env)
  3. Terminal: `openclaw models auth add` → select anthropic → paste token
  4. Restart gateway: `openclaw gateway restart`
  5. Edit openclaw.json to add Opus 4.6 with proper config (baseUrl WITHOUT /v1)
- baseUrl must be "https://api.anthropic.com" (no /v1)
- Set agents.defaults.model.primary to "anthropic/claude-opus-4-6"

**Actionable for Ahmed:**
- Could switch from MiniMax to Claude subscription for cost predictability
- Would give unlimited Opus/Sonnet usage within $200/month
- Alternative: Keep MiniMax for cheap tasks, Claude subscription for heavy Opus work

**Tags:** #claude #subscription #costoptimization #openclaw #anthropic

---

## Using OpenAI Subscription with OpenClaw | 2026-02-26
**Source:** The Next New Thing (Andrew Warner)
**Type:** Video / Tutorial

**Key Insights:**
- Anthropic Claude subscriptions are NOT allowed with OpenClaw (official as of Feb 18, 2026)
- OpenAI ChatGPT subscriptions ARE allowed
- Use $20/month or $200/month ChatGPT Pro instead of pay-per-token API
- Two simple commands to switch:
  1. `openclaw onboard --auth-choice openai-codex`
  2. `openclaw models set openai-codex/gpt-5.3-codex`
- Verify with: `openclaw models status --plain`
- Why use VS Code for config changes: safer than doing it inside OpenClaw (avoids "self-surgery" issues)
- God Mode (Caleb Hodes' company) helps entrepreneurs set this up as a concierge service

**Pricing Comparison:**
- OpenAI subscription: $20/month (Plus) or $200/month (Pro)
- Anthropic subscription: NOT ALLOWED anymore
- API pricing: Pay-per-token (can get expensive)

**Actionable for Ahmed:**
- Could switch to OpenAI subscription for cost predictability
- Keep MiniMax for cheap daily ops, use OpenAI for GPT-4o/GPT-5 when needed
- Alternative to Claude subscription (which is banned)

**Tags:** #openai #chatgpt #subscription #openclaw #costoptimization

<!-- end -->

## Claude Code Mobile (Remote Control) vs OpenClaw | 2026-02-27
**Source:** https://www.youtube.com/watch?v=L36aPV6g2II
**Type:** Video / Tutorial

**Key Insights:**
- Anthropic released `/remote control` command in Claude Code — sends active terminal session to your phone via the Claude iOS/Android app
- Code runs **locally on your computer**, not in the cloud — no merging, no pulling, no conflicts. Phone is just the interface
- Workflow: Start project on desktop → type `/remote control` → continue from phone → come back to computer with fully working code
- This is Anthropic's direct response to OpenClaw's mobile-on-the-go capability
- Two access methods: (1) copy link into mobile browser, (2) native Claude app auto-picks up the session

**Claude Code vs OpenClaw — When to Use Each:**

| Scenario | Use Claude Code | Use OpenClaw |
|----------|----------------|--------------|
| Big complex projects (hands-on, step-by-step) | ✅ | |
| Deep focused work (no multitasking) | ✅ | |
| Quick bug fixes to ship | ✅ | |
| Quick prototypes from mobile/Telegram | | ✅ |
| Building tooling for your own agent setup | | ✅ (has full context + memory) |
| Passive/overnight work (sleep and wake to results) | | ✅ (Claude Code can't do this) |

**Actionable for Ahmed:**
- OpenClaw remains superior for your use case: passive job processing, overnight CV generation, memory-aware work
- Claude Code Mobile is valuable for focused deep-work coding sessions when you want to stay hands-on
- The `/remote control` feature is worth testing if you ever do active coding on the go
- OpenClaw's key advantage: context + memory + passive work. Claude Code's key advantage: nuanced step-by-step guidance, interactive Q&A

**Tags:** #claude-code #openclaw #mobile #ai-tools #productivity #vibe-coding

## 336 OpenClaw Use Cases — Community Research | 2026-02-27
**Source:** https://www.youtube.com/watch?v=miJLo234L9s
**Type:** Video / Research Compilation (Jay, RoboNuggets)

**Key Insights:**
- Jay scraped 336 OpenClaw use cases from YouTube, GitHub, Reddit, X — categorized and put in a searchable database
- OpenClaw is the fastest-growing open-source project in GitHub history
- OpenAI hired the creator of OpenClaw — mass-market version expected eventually
- Biggest trap: "productivity procrastination" — people spend more time perfecting their agent setup than doing actual work (Notion parallel)

**The 6 Use Case Categories (ranked by volume):**

| Category | % of Use Cases | Key Examples |
|----------|---------------|--------------|
| Setup & Configuration | Largest | SOUL.md, memory systems, mission control dashboard, morning briefings, model fallback chains |
| Coding & Development | Large | PR reviews, Kanban boards, prototype builds while away from keyboard |
| Life Admin | Large | Medication reminders, recycling schedules, email summarization, meeting prep, job search alerts |
| Content & Marketing | Large | Trending video research, Reddit digests, podcast guest research, Meta ads automation |
| Finance | Small | Bank statement audits, investment alerts, trading automation (HIGH RISK — do not recommend) |
| Making Money | Small | Managed service providers, template economy, setup-as-a-service (SimpleClaw, SetupClaw) |

**Critical Insight — Role vs Task Mindset:**
- WRONG: "Task to be done" mindset (ask it to do one-off tasks)
- RIGHT: "Role to be filled" mindset (Admin, Developer, Marketer, Assistant — like hiring a team)
- This is exactly how Ahmed's ecosystem is structured (NASR, CV Optimizer, Job Hunter, Researcher, Content Creator)

**OpenClaw vs Claude Code (from previous video + this one):**
- OpenClaw wins: passive work, overnight automation, memory/context, convenience on the go
- Claude Code wins: complex full-stack apps, production-grade security, interactive step-by-step guidance

**Business Opportunity (Emerging):**
- Managed service providers for AI agent deployment (Accenture/Infosys parallel — businesses need accountability)
- Template economy: SOUL.md templates, Mission Control dashboards, skill packs people will pay for
- Industry-specific OpenClaw deployment (healthcare, legal, real estate) — human accountability still required

**Limitations Flagged:**
- Doesn't have proprietary databases (e.g., MyFitnessPal food database)
- Security risks if you don't know what you're doing
- Token costs can get expensive without model routing discipline
- Only ~1 month old — not yet trusted for finance/health critical decisions

**Actionable for Ahmed:**
- Ahmed's setup is already ahead of 95% of users — multi-agent ecosystem, mission control, memory system, model fallback chain all in place
- "Role to be filled" mindset = exactly what NASR does (strategic consultant, not a task runner)
- Template/skill economy opportunity: Ahmed could monetize his OpenClaw setup (SOUL.md, CV pipeline, job search agent) as the ecosystem matures
- Healthcare AI agent deployment = direct intersection with Ahmed's TopMed HealthTech expertise — positioning opportunity as GCC AI transformation leader
- Morning briefings, job search alerts, email automation = all already live in Ahmed's setup

**Tags:** #openclaw #ai-agents #use-cases #productivity #automation #business-opportunity #healthtech #template-economy

## Tree-of-Thought Prompting Framework | 2026-02-27
**Source:** Prompt Guy Newsletter (thinkaiprompt@mail.beehiiv.com) — Module 4
**Type:** Prompt Engineering Framework

**Core Insight:**
Tree-of-Thought separates **generation from evaluation**. Most prompts collapse these two steps, committing to the first viable path. ToT forces structured branching before committing.

**The 4-Step Template:**
1. **Generate branches:** 3 genuinely distinct approaches (not variations of the same idea) — Label A, B, C
2. **Evaluate each:** What makes it viable, real weaknesses given YOUR specific context, what success looks like at 90 days, biggest risk
3. **Compare + recommend:** Which is strongest for YOUR constraints specifically (not in general)
4. **Go deep:** First 3 concrete steps for the recommended option

**Related Techniques:**
- **Skeleton-of-Thought:** Outline first, fill in parallel. Faster but less evaluative depth.
- **Metacognitive Prompting:** 5-step warm-up — clarify question, preliminary judgment, evaluate, confirm direction, assess confidence.

**Actionable for Ahmed:**
- Job search 90-day strategy decisions (aggressive vs. selective vs. hybrid)
- LinkedIn content angle testing before committing to a direction
- Interview behavioral question preparation (3 approaches, evaluated against hiring criteria)
- Executive career path comparison (C-suite track vs. consulting vs. scale-up)

**Tags:** #prompting #tree-of-thought #decision-making #frameworks #interview-prep #strategy

## OpenClaw Troubleshooting: Claude Code Recovery Method | 2026-02-27
**Source:** https://www.youtube.com/watch?v=pmbftRnW4Yc
**Type:** Tutorial / Troubleshooting

**Common OpenClaw errors and what they mean:**
- Disconnected / Internal error: Gateway stopped or crashed
- Device identity required / Gateway token missing: Auth config issue
- Device token mismatch: Identity files corrupted or regenerated
- Pairing required: Node connection lost

**The Claude Code recovery method (for non-VPS users):**
1. Open terminal, type `claude`
2. Tell it: "My OpenClaw died. Check 127.0.0.1, identify the error and fix it."
3. Let it diagnose and restart automatically

**For Ahmed's VPS setup (faster path):**
- `openclaw doctor` — built-in diagnostic, catches most issues
- `openclaw gateway status` — check if gateway is running
- `systemctl --user restart openclaw-gateway.service` — restart gateway
- Check logs: `openclaw logs --follow`

**Bonus tool: Whisper Flow**
- Voice-to-text app for Mac/phone
- Transcribes speech into text for any AI interface (OpenClaw, Claude Code, ChatGPT)
- Useful for faster input on mobile, more creative/articulate prompts

**Tags:** #openclaw #troubleshooting #claude-code #gateway #whisper-flow #recovery

## Matthew Berman: 21 Insane OpenClaw Use Cases | 2026-02-27
**Source:** https://youtu.be/8kNv3rjQaVA
**Type:** Video / Advanced Use Cases

**Key Insights:**

### The 21 Use Cases Covered

| # | Use Case | What It Does | Priority for Ahmed |
|---|----------|--------------|-------------------|
| 1 | Personal CRM | Ingests Gmail, Calendar, Fathom meetings into SQLite. Natural language search. Relationship health scores. Action item tracking. | 🔴 High |
| 2 | Fathom Meeting Pipeline | Pulls meeting transcripts every 5 min, matches to CRM contacts, extracts action items, sends to Todoist | 🟡 Medium |
| 3 | Knowledge Base (RAG) | Drop any URL/PDF/tweet, vectorizes it, natural language search across everything saved | ✅ Already have this |
| 4 | Business Advisory Council | 8 parallel expert agents (finance, marketing, growth, etc.) analyze all business data nightly, synthesize ranked recommendations | 🔴 High (adapt for job search) |
| 5 | Security Council | Nightly at 3:30 AM, 4-perspective security review (offensive, defensive, privacy, operational). Opus summarizes, sends to Telegram | 🟡 Medium |
| 6 | Social Media Tracker | Daily snapshots of YouTube, Instagram, X, TikTok into SQLite. Feeds morning brief + business council | 🟡 Medium (LinkedIn only for Ahmed) |
| 7 | Video Idea Pipeline | Slack mention triggers full research, X trends, knowledge base query, creates Asana card with outline | ⬜ Low |
| 8 | Daily Briefing | Nightly scan of CRM, email, calendar, social stats. Morning brief to Telegram | ✅ Already have this |
| 9 | Three Councils | Business, Security, Platform councils running nightly | 🔴 High |
| 10 | Cron Automation | Full schedule: email every 30 min, Fathom every 5 min, security 3 AM, memory synthesis weekly, hourly git backup | ✅ Partially done |
| 11 | Security Layers | Prompt injection defense, permission restrictions, secret redaction, DM-only for financial data | ✅ Should review |
| 12 | Encrypted Backups | SQLite DBs encrypted + Google Drive. Git autosync hourly. Alert on failure. | 🔴 High |
| 13 | Image/Video Gen | Nano Banana Pro for images, V3 for video clips via Telegram | ⬜ Low |
| 14 | Self-Updates | Nightly check for OpenClaw updates, show changelog, auto-update on approval | ✅ Already have this |
| 15 | Usage + Cost Tracking | Track all LLM API calls, tokens, costs per model | 🔴 High (ties to quota system) |
| 16 | Prompt Engineering | Download frontier lab prompting guides per model, store locally, reference when editing prompts | 🟡 Medium |
| 17 | Sub-agents | Background workers for complex tasks, sub-sub-agents in new update | ✅ Already using |
| 18 | Coding Delegation | Simple tasks = OpenClaw. Medium/major = Cursor agent CLI | ✅ Using Sonnet sub-agents |
| 19 | Food Journal | Photo-based food tracking, symptom correlation, weekly analysis, pattern detection | ⬜ Low |
| 20 | SOUL.md Personality | Context-aware personality: informal with friends, formal in Slack/business settings | ✅ Already done |
| 21 | Self-Evolving Prompts | Action item rejection teaches the system to improve its extraction filter automatically | 🔴 High |

**Critical Insights:**

1. **Personal CRM** is the biggest gap in Ahmed's current setup. Gmail is being monitored but contacts, relationship health, and meeting action items are not being structured and stored.

2. **Business Advisory Council pattern** is directly applicable to Ahmed's job search: 8 parallel agents analyzing job market data, application pipeline, LinkedIn performance, and interview prep every night would be powerful.

3. **Encrypted backups** are not confirmed for Ahmed's setup. SQLite databases + Google Drive encryption should be verified.

4. **Self-evolving prompts**: When NASR gets something wrong (e.g., flags a non-urgent email as urgent), that rejection should train future behavior. Not currently implemented.

5. **Security layers**: External content should be treated as potentially malicious. The prompt injection defense pattern (summarize, don't parrot) is worth reviewing against current Gmail hook setup.

6. **Model-specific prompting guides**: Download Anthropic's Opus/Sonnet prompting best practices and store locally. Reference when writing sub-agent task briefs.

**Actionable for Ahmed (Priority Order):**
1. Build a lightweight personal CRM (contacts from Gmail, relationship tracking, TopMed + job search contacts)
2. Adapt Business Advisory Council for job search intelligence (market pulse, pipeline analysis, LinkedIn performance)
3. Verify encrypted backup system is in place (SQLite + Google Drive)
4. Add self-evolving prompt feedback loop to NASR's email filtering
5. Download model-specific prompting guides (Opus 4.6, Sonnet 4.6)

**Tags:** #openclaw #use-cases #matthew-berman #crm #knowledge-base #security #backups #self-evolving #business-intelligence
