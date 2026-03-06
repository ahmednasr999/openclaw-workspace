# OpenClaw + Codex Agent Swarm - Elvis's Setup

*Source: @elvissun (Elvis, building PR stack)*
*Tweet: https://x.com/elvissun/status/2025920521871716562*
*Date: Feb 23, 2026*

---

## The Core Pattern

> "I don't use Codex or Claude Code directly anymore. I use OpenClaw as my orchestration layer."

**Orchestrator:** Zoe (OpenClaw)
- Holds all business context (Obsidian vault)
- Translates context into precise prompts
- Spawns agents, picks models, monitors progress
- pings on Telegram when PRs ready

**Proven Results:**
- 94 commits in one day (avg ~50)
- 7 PRs in 30 minutes
- ~$190/month cost
- One-shots most small-medium tasks

---

## The 8-Step Workflow

### Step 1: Customer Request → Scoping with Zoe
- Meeting notes sync to Obsidian automatically
- Zoe pulls context, scopes feature together
- Three things Zoe does:
  1. Tops up credits (has admin API access)
  2. Pulls customer config from prod DB (read-only)
  3. Spawns Codex agent with detailed prompt

### Step 2: Spawn the Agent
- Each agent gets isolated worktree + tmux session
- Mid-task redirection: don't kill, just redirect
- Tracked in `.clawdbot/active-tasks.json`

### Step 3: Monitoring Loop (every 10 min)
- Doesn't poll agents directly (expensive)
- Checks JSON registry:
  - tmux sessions alive?
  - Open PRs on tracked branches?
  - CI status via gh cli?
  - Auto-respawn failed agents (max 3 attempts)
  - Only alerts if human attention needed

### Step 4: Agent Creates PR
- Commits, pushes, opens PR via `gh pr create --fill`
- NOT notified yet — PR alone isn't "done"

**Definition of Done:**
- PR created
- Branch synced to main
- CI passing
- Codex review passed
- Claude Code review passed
- Gemini review passed
- Screenshots included (if UI)

### Step 5: Automated Code Review
Three AI models review each PR:

| Reviewer | Strength |
|----------|----------|
| Codex | Edge cases, logic errors, false positives very low |
| Gemini | Security, scalability, suggests fixes |
| Claude Code | Validates others, rarely critical |

### Step 6: Automated Testing
- Lint + TypeScript
- Unit tests
- E2E tests
- Playwright (preview env)
- **Rule:** If UI changes, screenshot required or CI fails

### Step 7: Human Review
- Telegram notification: "PR #341 ready"
- 5-10 min review
- Many PRs merged without reading code — screenshot shows everything

### Step 8: Merge
- Daily cron cleans up orphaned worktrees + task registry

---

## The Ralph Loop V2 (Improved)

**Old pattern:** Same prompt each cycle, static

**New pattern:** When agent fails, Zoe adapts:
- Context ran out? → "Focus only on these three files"
- Wrong direction? → "Stop, customer wanted X not Y. Here's what they said."
- Needs clarification? → "Here's customer's email and what they do"

**Proactive work finding:**
- Morning: Scans Sentry → spawns 4 agents to fix errors
- After meetings: Scans notes → spawns 3 agents for feature requests
- Evening: Scans git log → spawns Claude Code to update docs

**Reward signals:** CI passing + all 3 AI reviews + human merge

---

## Agent Selection

| Agent | Best For | % Usage |
|-------|----------|---------|
| Codex | Backend logic, complex bugs, multi-file refactors | 90% |
| Claude Code | Frontend, git operations, faster | Decreased |
| Gemini | UI design, generates HTML/CSS spec first | Design |

---

## Key Insights

### Two-Tier Context (Zero-Sum)
> "Context windows are zero-sum. Fill with code → no room for business context."

| Layer | Holds | Focus |
|-------|-------|-------|
| Zoe (OpenClaw) | Business context, customer data, meeting notes | Strategy |
| Codex/Claude | Code only | Execution |

**Specialization through context, not through different models.**

### Hardware Bottleneck
> "My Mac Mini 16GB tops out at 4-5 agents before swapping"

Bought Mac Studio M4 Max 128GB ($3,500) to scale.

### Vision
> "One-person million-dollar companies in 2026. An AI orchestrator as an extension of yourself delegating to specialized agents."

---

## OpenClaw Application

| Pattern | Current State | Improvement |
|---------|--------------|-------------|
| Orchestrator (Zoe) | NASR | Already have |
| Business context (Obsidian) | Workspace files | Could integrate Obsidian |
| tmux isolation | Sub-agents | Could use more isolation |
| Multi-reviewer pipeline | Not implemented | Add CV reviewer |
| Proactive work finding | Limited | Could improve |
| Cron monitoring (10 min) | Heartbeat | Align intervals |

---

## Action Items

1. [ ] Consider Obsidian integration for business context
2. [ ] Add tmux-like isolation for sub-agents
3. [ ] Build multi-reviewer pipeline (for CVs)
4. [ ] Improve proactive work finding
5. [ ] Align heartbeat interval (consider 10 min like Elvis)

---

## Related

- [[agent-tool-design-lessons.md]] - Claude Code tool design
- [[eval-suite/README.md]] - Skill evaluation framework
- [[memory/2026-03-06.md]] - Today's session

---

## Quotes

> "My git history looks like I just hired a dev team. In reality it's just me going from managing Claude Code, to managing an OpenClaw agent that manages a fleet of other Claude Code and Codex agents."

> "We're going to see a ton of one-person million-dollar companies starting in 2026. The leverage is massive for those who understand how to build recursively self-improving agents."
