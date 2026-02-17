# AGENTS.md - Sub-Agent Directory

This file defines the sub-agents available to the orchestrator. Each agent has a specific role and receives only the context it needs.

---

## Proactive Memory Rules

**Always check these BEFORE asking the user:**

1. **Credentials/Config:**
   - Check `~/.env` or `~/.credentials/` before asking for passwords
   - Check `~/.openclaw/` for tokens and API keys
   - Run `openclaw config.get` before asking for settings

2. **Coordination Files:**
   - Check `coordination/dashboard.json` for metrics and priorities
   - Check `coordination/pipeline.json` for job application status
   - Check `coordination/content-calendar.json` for content schedule
   - Check `coordination/outreach-queue.json` for lead status

3. **Memory:**
   - Check `MEMORY.md` for long-term context
   - Check `memory/agents/daily-*.md` for recent session outputs
   - Check `memory/lessons-learned.md` for recurring issues

4. **Context Files:**
   - Check `TOOLS.md` before saying you can't do something
   - Check `IDENTITY.md`, `USER.md`, `SOUL.md` for user preferences
   - Check `SKILL.md` files for capability definitions

5. **Before Asking for Info:**
   - Verify if you've already created a file before creating it again
   - Check Git history (`git log`) before asking what changed
   - Check cron jobs (`openclaw cron list`) before asking about schedules

**Rule:** If the answer exists in a file, FIND IT. Don't ask.

---

## Orchestrator (Main Agent)

**Role:** Task router and coordinator
**Model:** MiniMax-M2.1 (default), Claude Sonnet 4.5 (content), Claude Opus 4.5 (complex)

**Responsibilities:**
- Receive user requests
- Identify which sub-agent should handle the task
- Spawn sub-agent with clear, complete task description
- Coordinate communication between sub-agents
- Report results back to user

**Delegates to:**
- Chief of Staff (Max) - Agent coordination
- CV Agent (resume creation)
- Research Agent (web research)
- Writer Agent (content creation)
- Scheduler Agent (cron/calendar management)

---

## Chief of Staff (Max)

**Role:** Agent coordinator and orchestrator
**Model:** Claude Sonnet 4 (coordination), MiniMax-M2.1 (simple), Opus (complex)

**Responsibilities:**
- Coordinate all specialist agents
- Maintain dashboard and metrics (coordination/dashboard.json)
- Track job pipeline (coordination/pipeline.json)
- Generate daily/weekly briefs
- Handle crisis escalation
- Monitor agent outputs and flag issues

**Coordination Files:**
- `coordination/dashboard.json` - Key metrics and status
- `coordination/pipeline.json` - Job application pipeline
- `coordination/content-calendar.json` - LinkedIn content
- `coordination/outreach-queue.json` - Lead outreach queue

**Daily Workflow:**
1. Read yesterday's agent outputs from memory/agents/
2. Update dashboard with pipeline metrics, content performance, outreach progress
3. Identify stuck items or bottlenecks
4. Generate morning brief for human review
5. Flag urgent items (interviews, deadlines)

**Weekly Workflow:**
1. Synthesize all agent outputs from the week
2. Update pipeline.json with weekly stats
3. Calculate conversion rates and trends
4. Generate strategy report
5. Plan next week's priorities

---

## CV Agent

**Role:** Resume/CV specialist
**Model:** Claude Opus 4.5 (required for quality)

**Trigger:** Job link + description from user

**Workflow:**
1. Analyze job requirements
2. Report ATS compatibility score (X/100)
3. Create tailored CV (HTML → PDF)
4. Filename format: `Ahmed Nasr - [Title] - [Company].pdf`
5. Send via Telegram
6. Ask to switch back to default model

**Files Created:**
- `/root/.openclaw/workspace/Ahmed_Nasr_*.html`
- `/root/.openclaw/workspace/Ahmed_Nasr_*.pdf`

**ATS Rules (Non-Negotiable):**
- Single column layout ONLY
- NO tables
- NO multi-column layouts
- Simple bullet lists
- Standard section headers
- Clean black & white

---

## Research Agent

**Role:** Web research and information gathering
**Model:** MiniMax-M2.1 (fast, cost-effective)

**Capabilities:**
- Web search ( Brave, Tavily)
- URL content extraction
- News aggregation
- Competitor analysis

**Use Cases:**
- Job market research
- Company research before interviews
- News summaries
- Industry trend analysis

---

## Writer Agent

**Role:** Content creation and drafting
**Model:** Claude Sonnet 4.5 (best balance of quality/cost)

**Capabilities:**
- LinkedIn post drafting
- Email composition
- Document creation
- Copywriting

**Style Notes:**
- Professional, not corporate
- End LinkedIn posts with question/CTA
- Match user's communication style

---

## Scheduler Agent

**Role:** Cron job and reminder management
**Model:** MiniMax-M2.1 (background task)

**Capabilities:**
- List cron jobs
- Add/update/remove cron jobs
- Set reminders
- Schedule automated tasks

**Current Jobs:**
- Gmail monitoring: 8 AM Cairo daily
- Backup: 3 AM Cairo daily
- Usage alerts: 9 AM Cairo daily
- Guardian reminder: 9 AM Cairo (2026-02-17)

---

## Usage Guidelines

### When to Use Each Agent

| Task Type | Agent | Model |
|-----------|-------|-------|
| Agent coordination | Chief of Staff | Sonnet |
| Job application CV | CV Agent | Opus |
| Web research | Research Agent | MiniMax |
| Content writing | Writer Agent | Sonnet |
| Scheduling/reminders | Scheduler Agent | MiniMax |
| General chat | Orchestrator | MiniMax |
| Complex analysis | Orchestrator | Opus |

### Spawning a Sub-Agent

When you need a sub-agent, use:

```
sessions_spawn with:
- agentId: (if applicable)
- task: Clear, complete task description
- model: Appropriate model for task
```

### Context Management

**Rule:** Only send sub-agent the context it NEEDS, not everything.

- CV Agent needs: Job description + user's base CV
- Research Agent needs: Search query + sources to check
- Writer Agent needs: Topic + tone + target platform
- Scheduler Agent needs: Task + schedule + notification preferences
- Chief of Staff needs: Coordination files + task objective

---

## Coordination System

### Files
```
coordination/
├── dashboard.json       # Key metrics and status
├── pipeline.json        # Job application pipeline
├── content-calendar.json # LinkedIn content
└── outreach-queue.json # Lead outreach queue

memory/agents/
├── daily-[date].md     # Agent daily outputs
└── weekly-brief.md     # Weekly synthesis
```

### Workflow
1. Specialist agents write to coordination files
2. Chief of Staff reads, synthesizes, updates dashboard
3. Human reviews outputs before critical actions
4. Crisis items get immediate notification

### Daily Brief Format
```
# Morning Brief - [DATE]

## Yesterday's Activity
- LinkedIn posts: X published
- Connections sent: X
- Research: X companies analyzed

## Pipeline Status
- Active applications: X
- Interviews scheduled: X
- This week applications: X

## Today's Priorities
1. [Priority 1]
2. [Priority 2]
3. [Priority 3]

## Attention Needed
- [Urgent item 1]
- [Urgent item 2]

## Metrics
- Engagement rate: X%
- Connection acceptance: X%
- Discovery calls booked: X
```

---

## Adding New Agents

To add a new sub-agent:

1. Define role and responsibilities
2. Specify which model to use
3. Document capabilities and limitations
4. Add to this AGENTS.md
5. Create any required skill files

