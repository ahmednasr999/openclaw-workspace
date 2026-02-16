# AGENTS.md - Sub-Agent Directory

This file defines the sub-agents available to the orchestrator. Each agent has a specific role and receives only the context it needs.

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
- CV Agent (resume creation)
- Research Agent (web research)
- Writer Agent (content creation)
- Scheduler Agent (cron/calendar management)

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

---

## Adding New Agents

To add a new sub-agent:

1. Define role and responsibilities
2. Specify which model to use
3. Document capabilities and limitations
4. Add to this AGENTS.md
5. Create any required skill files

