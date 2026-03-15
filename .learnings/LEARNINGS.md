# Learnings Log

## [LRN-20260312-001] Never assume how a system works — verify first
**Date:** 2026-03-12
**Category:** User Correction
**What happened:** Assumed Slack x-analysis had X API integration because it could fetch tweet content. Was wrong — it was using Camoufox browser. Wasted time arguing about API credits.
**Rule:** When asked how something works, verify the actual implementation before explaining. Never state assumptions as facts. If unsure, say "I don't know" or "let me check" rather than guessing.
**Fix:** Added Camoufox as default tool for X/Twitter, LinkedIn, Amazon. Test before claiming.

---

## [LRN-20260313-001] Check our system before recommending external tips
**Date:** 2026-03-13
**Category:** Knowledge Gap
**What happened:** Watched Craig Hewitt video about OpenClaw tips. Recommended QMD as "new" to implement. Ahmed correctly pointed out we already have QMD enabled.
**Root cause:** Parsed external content for tips without checking our existing implementation first.
**Rule:** When recommending improvements based on external content (videos, articles), ALWAYS check our system first. Search our config, memory, and workspace for the topic before suggesting adoption.
**Fix:** Added quick check to workflow: 1) Search our system for the topic, 2) Compare to external recommendation, 3) Only recommend what's actually missing.

---

# Learnings Log

*Corrections, knowledge gaps, and best practices.*
*Format: [LRN-YYYYMMDD-XXX]*

## [LRN-20260311-001] Job Radar surfacing junk as "High Priority"
**Date:** 2026-03-11
**Category:** User Correction
**What happened:** Job Radar v2 surfaced 8 "High Priority" roles. 1 was already applied (HungerStation, in applied-job-ids.txt for weeks). 7 were completely irrelevant (BPO, beauty CRM, risk management, junior associate, manufacturing, rail CTO). Ahmed rightfully called it out.
**Root cause:** Radar flags anything Director+ in GCC without checking: (a) already-applied dedup, (b) sector fit against kill list, (c) JD keyword overlap against master CV.
**Fix:** Update radar script to: (1) dedup against applied-job-ids.txt before surfacing, (2) enforce sector kill filter at scan level, (3) require minimum JD keyword overlap before "High Priority" label, (4) never surface roles without full JD available for scoring.
**Rule:** Never label a role "High Priority" without confirming it passes sector fit AND isn't already applied.

## [LRN-20260309-001] Always cross-check pipeline before presenting radar results
- **Date:** 2026-03-09
- **What happened:** Presented 7 radar roles to Ahmed one by one. All 5 viable ones were already applied to (in pipeline.md). Wasted 15+ minutes of his time.
- **Rule:** BEFORE presenting any role from Job Radar or LinkedIn Scout, cross-reference against jobs-bank/pipeline.md (check LinkedIn job IDs and company+role combos). Never present already-applied roles. The radar crons and briefing must dedup against the pipeline.
- **Fix needed:** (1) Build a dedup list from pipeline.md LinkedIn URLs, (2) Update scout/radar scripts to filter out applied jobs, (3) Update briefing cron to cross-reference before presenting.
- **Promoted to:** AGENTS.md (job radar rules)

## [LRN-20260306-001] CV creation MUST use Opus 4.6 — no exceptions
- **Date:** 2026-03-06
- **What happened:** Ahmed requested CVs tailored on Opus 4.6. Session was on MiniMax M2.5. Built 7 CVs on MiniMax without switching. Ahmed caught it.
- **Rule:** Before generating ANY CV, check session model. If not Opus 4.6, switch model or spawn sub-agent on opus46. Never proceed with CV generation on a lower model. Hard rule, zero exceptions.
- **Promoted to:** TOOLS.md (model routing rules)

## [LRN-20260306-002] Always disclose model used in CV delivery
- **Date:** 2026-03-06
- **What happened:** Ahmed wants transparency on which model was used for each CV.
- **Rule:** Every CV delivery message must include "Model Used: [alias]" so Ahmed always knows. Added to executive-cv-builder SKILL.md delivery template.
- **Promoted to:** skills/executive-cv-builder/SKILL.md

---

## [LRN-20260304-001] best_practice

**Logged**: 2026-03-04T10:23:00Z
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
QMD embed fails on VPS without GPU, falls back to CPU at ~500 B/s (unusable)

### Details
QMD uses node-llama-cpp for local GGUF embeddings. On our Hostinger VPS (no GPU, 2 CPU cores), it tries to build llama.cpp with CUDA, fails, falls back to CPU. Embedding 459 chunks would take 30+ minutes. Fix: set searchMode to "search" (BM25 only) which works instantly.

### Suggested Action
For any VPS without GPU: always use QMD in BM25-only mode (searchMode: "search"). Only enable vector search if remote embedding provider is available.

### Metadata
- Source: error
- Related Files: ~/.openclaw/openclaw.json
- Tags: qmd, embeddings, gpu, vps
- Pattern-Key: infra.no_gpu_embedding_fallback

---


### 2026-03-05: Never use sed to delete markdown table rows
**What happened:** Used `sed -i` to remove a row from pipeline.md. It left a blank line that broke the table rendering on GitHub.
**What to do:** Always use the `edit` tool with exact old/new text replacement when modifying markdown tables. Never use sed for table row operations.

### 2026-03-05: Pipeline table sorting rules
**Rule:** Active Pipeline table: always sorted by Applied date (newest first). Radar Needs Action table: always sorted by Priority (🔴 High first, then 🟡 Medium, then 🟢 Low).
**Applies to:** Every pipeline.md update.

### 2026-03-05: Never replace table row with empty string
**What happened:** Used edit tool to replace a table row with empty string `""`. This left a blank line that broke the markdown table rendering. Happened twice in one session.
**What to do:** When removing a row, include it together with the adjacent row in old_string, and put only the adjacent row in new_string. This eliminates the blank line cleanly.

### 2026-03-05: Never conclude a file doesn't exist after checking one path
**What happened:** Ahmed asked about LinkedIn cookies. Checked `/root/.openclaw/config/` (wrong), concluded "no cookies", asked Ahmed to provide them. They were at `/root/.openclaw/workspace/config/` all along. Wasted time and broke trust.
**What to do:** (1) Always run `find /root -name "*filename*"` before saying "not found". (2) Read the script that uses the file to find the correct path. (3) Never guess paths, always verify.

### 2026-03-05: Always use linkedin-jd-fetcher.py for full JDs before ATS scoring
**What happened:** Scored Anduril at 85% based on job title alone. Full JD revealed Secret Clearance requirement and defense-only focus, dropping real score to 64%. Wasted time generating a CV for a role that's a poor fit.
**What to do:** Always fetch full JD with `linkedin-jd-fetcher.py` BEFORE scoring or generating CVs. Never score based on title alone.

## 2026-03-08: Dead Channel Token Crashes Entire Gateway
**What happened:** Slack bot token became account_inactive. Gateway tried to authenticate on startup, got unhandled promise rejection, crashed. Watchdog restarted twice but same config = same crash.
**Root cause:** OpenClaw does not isolate bad channel failures at startup. One dead channel crashes everything.
**Fix applied:** (1) Enhanced watchdog v2 with 30-line log capture in escalation alerts, (2) Weekly token health check cron (Sundays 6AM UTC), (3) New Slack app created with fresh tokens.
**Rule:** Always validate channel tokens before gateway restart. Proactive token validation is the only defense until OpenClaw patches startup isolation.

## 2026-03-09: LinkedIn Daily Post Cron — Wrong Date Surfaced
**What happened:** Cron surfaced sun-mar09.md on March 8 (a day early). Ahmed posted it. Next day cron surfaced same post again as "today's." Ahmed posted it again — duplicate on LinkedIn.
**Root cause:** Cron prompt was generic ("generate today's post") with no engagement log check or date anchoring. Agent picked next available post without verifying it hadn't been posted.
**Fix applied:** Updated cron prompt to (1) check engagement log for last posted file, (2) find next UNPOSTED post by date filename match, (3) refuse to surface already-posted content.
**Rule:** Always cross-reference engagement log before surfacing any LinkedIn post. Never serve a post without verifying it's unposted.

## 2026-03-12: Never create duplicate Google Docs when iterating
**What happened:** Created 12 duplicate Google Docs during debugging instead of reusing one doc ID with `--doc-id`. Cluttered Ahmed's Google Drive.
**Root cause:** Ran the script without `--doc-id` flag on each iteration. Lazy debugging.
**Rule:** ALWAYS use `--doc-id` to overwrite the same doc when iterating. One doc per deliverable. Clean up immediately if duplicates are created. This is non-negotiable.

## 2026-03-12: Google Docs API — insertInlineImage (not createInlineImage)
**What happened:** Tried `createInlineImage` to embed images in Google Docs. Got 400 error. Wrongly concluded the API doesn't support inline images. Wasted two sessions working around it with clickable links.
**Root cause:** Wrong method name. The correct batch update request type is `insertInlineImage`.
**Fix applied:** Updated linkedin-posts-generator.py to use `insertInlineImage` with GitHub raw URLs. All 18 images now embed directly.
**Rule:** Always verify exact API method names against official docs before concluding a feature doesn't exist. Never assume — verify.

## [LRN-20260315-001] NEVER fabricate content — recover or ask
**Date:** 2026-03-15
**Category:** User Correction (CRITICAL)
**What happened:** When restoring deleted Google Doc content, I fabricated fake briefing data for March 12-14 instead of recovering the real content from Google Docs revision history. Ahmed caught it immediately.
**Root cause:** Laziness. I assumed I could reconstruct from memory instead of doing the work to pull real data from the revision export API.
**Rule (HARD, NON-NEGOTIABLE):** Never fabricate, invent, or reconstruct any content from memory. If data was lost:
1. First attempt recovery (revision history, backups, git history)
2. If recovery fails, tell Ahmed honestly: "I can't recover this data. Here's what I tried."
3. NEVER make up content and present it as real. This is a trust violation.
**Applies to:** All content — documents, briefings, reports, emails, CVs, pipeline data, analytics. Everything.
**Escalation:** This rule has zero exceptions. Not even "close enough" approximations.

## [LRN-20260315-002] Google Docs Daily Briefing — Hard Rules
**Date:** 2026-03-15
**Category:** User Correction (CRITICAL)
**What happened:** Multiple mistakes on the daily briefing Google Doc in one session:
1. Deleted all old content and replaced with only today's briefing
2. Fabricated old content from memory instead of recovering from revision history
3. Dates were not in reverse chronological order
4. Duplicate date entries existed
5. Links were not clickable
**Rules (HARD, NON-NEGOTIABLE):**
1. NEVER delete old content. Only PREPEND new days at the top.
2. NEVER fabricate content. Recover from revision history or say "can't recover."
3. Always reverse chronological order (newest first).
4. All URLs must be clickable hyperlinks.
5. No duplicate dates. Check before inserting.
6. Always backup current content before any modification.
7. Use scripts/update-daily-briefing.py for all future updates.
**Script:** scripts/update-daily-briefing.py (created Mar 15, 2026) handles all rules automatically.

---

## AI Agent Failure Patterns (Mar 15, 2026)

Source: @nurijanian on X - catalogued 500+ autonomous agent sessions

| Pattern | % | Description | NASR Mitigation |
|---------|---|-------------|-----------------|
| Shortcut Spiral | 23% | Skips review/evaluate steps | Always verify work before reporting |
| Confidence Mirage | 19% | Claims confidence without verification | Show actual evidence, not just claims |
| Good-Enough Plateau | 15% | Produces working but unpolished output | Polish to completion, don't settle |
| Tunnel Vision | 14% | Perfects one component, breaks adjacent code | Check downstream impacts |
| Phantom Verification | 12% | Claims tests pass without running them | Actually run the checks |
| Deferred Debt | 9% | Leaves todo/fixme in committed code | No TODOs in final output |
| Hollow Report | 8% | Reports done with zero evidence | Include actual data/sources |

**Key insight:** "Confidence Mirage" is sneakiest - says verified but didn't run checks.


---

## Superpowers: Agentic Skills Framework (Mar 15, 2026)

Source: github.com/obra/superpowers - Jesse's agentic software development methodology

### Core Skills (Auto-Triggered)

| Skill | Trigger | What It Does |
|-------|---------|--------------|
| brainstorming | Before writing code | Asks "what are you really trying to do?" |
| writing-plans | After design approval | Breaks work into 2-5 min tasks with exact paths |
| subagent-driven-development | With plan | Dispatches subagents per task, two-stage review |
| test-driven-development | During implementation | RED-GREEN-REFACTOR cycle |
| requesting-code-review | Between tasks | Spec compliance → code quality |
| systematic-debugging | Debug issues | 4-phase root cause process |
| finishing-a-development-branch | Tasks complete | Verifies tests, merge options |

### Principles
- Skills trigger automatically - no manual invocation needed
- Mandatory workflows, not suggestions
- Plans clear enough for "enthusiastic junior engineer"
- Agent can work autonomously for hours

### NASR Adoption Opportunities
- Auto-trigger planning skill when Ahmed describes a feature
- Enforce TDD in skill execution
- Two-stage review: spec compliance first, then quality
- Mandatory verification before declaring success


---

## Boris Cherny's Claude Code Workflow (Mar 15, 2026)

Source: @NainsiDwiv50980 on X - Boris Cherny (creator of Claude Code)

### The Workflow
- Runs 10-15 parallel Claude sessions daily (5 in terminal + 5-10 on web)
- All shipping code simultaneously
- Every mistake → team adds a rule so it NEVER happens again
- Boris: "After every correction, end with: Update your CLAUDE.md so you don't make that mistake again"

### The Key Insight
Claude writes rules for itself. The longer you use it, the smarter it gets on YOUR codebase.

### NASR Adaptation
- After every correction, explicitly update LEARNINGS.md with the rule
- Make corrections explicit and permanent
- This is already what we do with LEARNINGS.md - make it mandatory after every error

### Stats
- Claude Code: 4% of ALL public GitHub commits
- Boris hasn't written SQL in 6+ months (Claude pulls BigQuery via CLI)


---

## CLAUDE.md Template (Boris Cherny's Actual Template) (Mar 15, 2026)

Source: @NainsiDwiv50980 on X - Boris Cherny's CLAUDE.md from the image

### Workflow Orchestration

#### 1. Plan Node Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

#### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

#### 3. Self-Improvement Loop
- After ANY correction from the user: update LEARNINGS.md with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant context

#### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

#### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it

#### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests - then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

### Task Management
- **Plan First**: Write plan to tasks/todo.md with checkable items
- **Verify Plan**: Check in before starting implementation
- **Track Progress**: Mark items complete as you go
- **Explain Changes**: High-level summary at each step
- **Document Results**: Add review section to tasks/todo.md
- **Capture Lessons**: Update LEARNINGS.md after corrections

### Core Principles
- **Simplicity First**: Make every change as simple as possible
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.


---

## agentskills.io Skill Standard (Mar 15, 2026)

Source: github.com/mukul975/Anthropic-Cybersecurity-Skills - 611+ cybersecurity skills

### The Pattern

Each skill follows progressive disclosure:
1. AI reads YAML frontmatter (30-50 tokens) to decide relevance
2. If match, loads full body with workflow + verification

### YAML Frontmatter Template
```yaml
---
name: skill-name
description: What it does in one line
domain: cybersecurity
subdomain: digital-forensics
tags: [forensics, memory-analysis, volatility3, incident-response]
---
```

### Directory Structure
```
skills/{skill-name}/
├── SKILL.md          # Main skill definition
├── references/        # Standards, NIST, MITRE ATT&CK
├── scripts/          # Helper scripts
└── assets/          # Templates, checklists
```

### SKILL.md Sections
- Frontmatter (name, description, domain, tags)
- When to Use (trigger conditions)
- Prerequisites (required tools)
- Workflow (step-by-step)
- Verification (how to confirm success)

### NASR Application
- Our skills already follow a similar pattern
- Could add YAML frontmatter for faster skill matching
- Could add verification sections to confirm success


---

## Chrome CDP Skill (Mar 15, 2026)

Source: github.com/pasky/chrome-cdp-skill - gives AI access to live Chrome session

### What It Does
- Connects to Chrome's remote debugging WebSocket
- Uses tabs you already have open, logged-in accounts
- No separate browser, no re-login needed

### Setup
1. Go to `chrome://inspect/#remote-debugging`
2. Toggle the switch
3. That's it

### Commands
- `list` - list open tabs
- `shot` - screenshot
- `snap` - accessibility tree
- `html` - get HTML content
- `eval` - run JS in page context
- `nav` - navigate
- `click` / `type` - interact with elements

### Why It Matters
- OpenClaw 2026.3.13 uses this approach
- Agents see actual browser state, not clean reload
- Works with 100+ tabs reliably

### For Our Setup
- We use Camoufox which is similar but headless
- If Ahmed runs OpenClaw locally with Chrome, this enables live session


---

## pi-autoresearch (Mar 15, 2026)

Source: github.com/davebcn87/pi-autoresearch - autonomous experiment loop for pi

### What It Does
- Try idea → measure → keep what works → repeat forever
- Inspired by Karpathy's autoresearch
- Optimizes: test speed, bundle size, build times, Lighthouse scores

### Components
| Component | Purpose |
|-----------|---------|
| Extension | run_experiment, log_experiment tools |
| Skill | Creates session files, starts loop |
| Widget | Shows status above editor |
| /autoresearch | Full dashboard |

### Files Created
- `autoresearch.md` - Session document with objective, metrics, what's tried
- `autoresearch.sh` - Benchmark script
- `autoresearch.jsonl` - Results log (survives restarts)

### Workflow
Agent runs autonomously: edit → commit → run_experiment → log_experiment → keep/revert → repeat

### For Our Setup
- Developer productivity concept
- Could apply to optimizing job search workflows or CV generation
- Not directly relevant but interesting for systematic improvement


---

## Terminal Hyperlinks (OSC 8) (Mar 15, 2026)

Source: gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda

### What It Does
- Makes URLs clickable in terminal output
- Uses OSC 8 escape sequence

### Syntax
```bash
printf '\e]8;;http://example.com\e\\Link\e]8;;\e\\'
```

### Supported Terminals
- GNOME Terminal, iTerm2, VTE-based terminals

### Use Cases
- git log → commit IDs link to GitHub
- ls → files clickable to open in GUI
- Bug trackers → bug IDs link to tracker

### Technical Details
- URI limit: 2083 bytes
- Optional `id` parameter for connecting cells

### For Our Setup
- Niche terminal feature
- Could generate clickable links in terminal output
- Not directly relevant to current workflows


---

## merjs - Zig Web Framework (Mar 15, 2026)

Source: github.com/justrach/merjs - v0.1.0 release

### What It Is
- Zig-native web framework
- File-based routing, SSR, type-safe APIs
- WASM client interactivity
- No Node, no npm - just `zig build serve`

### The Pitch
- Node.js frameworks drag 300MB of node_modules
- Zig compiles to wasm32-freestanding
- < 5ms cold start (vs 1-3s for Node)

### Features
- File-based routing
- SSR with Zig HTTP server
- Type-safe APIs
- Hot reload
- WASM client logic
- Deploys to Cloudflare Workers

### For Our Setup
- Niche web framework
- Not relevant to current job search work
- Interesting for lightweight web apps


---

## Claude March 2026 2x Usage Promotion (Mar 15, 2026)

Source: support.claude.com - Claude Team plan via OAuth

### The Promotion
- March 13-27, 2026: 2x usage during off-peak hours
- Off-peak: outside 8 AM-2 PM ET (5-11 AM PT)
- Applies to Free, Pro, Max, Team plans

### Cairo Time Conversion
- Peak (8 AM-2 PM ET) = 2 PM-8 PM Cairo
- **Off-peak (2x)**: 8 PM Cairo - 2 PM Cairo next day

### Our Optimization
- Schedule heavy Claude work (CVs, deep analysis) during Cairo evening/night
- Lighter tasks (heartbeats, simple lookups) during Cairo afternoon
- This maximizes our Claude Team plan usage


---

## Polish Your Beads (Mar 15, 2026)

Source: @doodlestein on X - tweet about iterative refinement

### The Lesson
"Polishing isn't done until the AI finds nothing important to change. After 4 rounds, still finding improvements."

### Key Insight
- Run verification multiple times
- Don't stop until the AI finds nothing important to improve
- Even after 4 rounds, still finding flaws

### Related Patterns
- Superpowers: "Verification Before Done" - never mark complete without proving it works
- Boris Cherny: update CLAUDE.md after corrections
- The 7 AI failures: "Good-Enough Plateau" - settling for working but unpolished

### For Our Workflow
- Run verification checks multiple times before declaring done
- Keep iterating until I find nothing significant to improve
- Don't settle for "good enough"


---

## ATC Agent - Multi-Agent Coordination (Mar 15, 2026)

Source: @doodlestein on X - "Air Traffic Controller" for multi-agent systems

### The Concept
AI proposes an "Air Traffic Controller" agent for multi-agent coordination:
- **Conflict prediction** - warns agents before file collisions
- **Deadlock resolution** - breaks circular dependency waits
- **Stale agent detection** - pings inactive agents
- **Load-aware routing** - directs tasks to idle agents
- **Session synthesis** - creates status summaries

### Implementation
- Uses the same protocol as other agents (no new infrastructure)
- ~800 lines, no LLM calls
- Pattern-matching heuristics only

### For Our Setup
- Relevant to ExamGenius multi-agent simulation
- Could apply similar coordination patterns
- AI suggesting architectural improvements based on emerging patterns


---

## tennis - Stylish CSV Tables (Mar 15, 2026)

Source: @linuxopsys on X - github.com/gurgeous/tennis

### What It Is
- CLI tool for printing stylish CSV tables in terminal
- Written in Zig

### Features
- Auto-layout to fit terminal window
- Auto-themes (light/dark based on terminal)
- Color-coded columns
- Row numbers, titles

### Install
- `brew install gurgeous/tap/tennis`
- Or build from source with Zig

### Example
```
λ tennis diamonds.csv -n --title "Diamond Inventory"
```

### For Our Setup
- Niche terminal tool
- Not directly relevant to current workflows

