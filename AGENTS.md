# AGENTS.md - Your Workspace (CORE)

This folder is home. Treat it that way.

## Mandatory Session Startup: Read in Order
1. SOUL.md: who I am
2. USER.md: who I'm helping
3. MEMORY.md (main session only): long-term context
4. STATE.yaml: project state + alerts
5. memory/active-tasks.md: urgent RIGHT NOW
6. memory/pending-opus-topics.md: queued work
7. memory/last-session.md: prior context
8. memory/cv-pending-updates.md: approved CV changes not yet applied
9. memory/YYYY-MM-DD.md (today + yesterday): session log
10. GOALS.md: strategic north star (when it exists)
11. jobs-bank/handoff/*.trigger check for NASR_REVIEW_NEEDED
12. .learnings/LEARNINGS.md: past mistakes and corrections (never repeat them)

**Confirm startup:** "✅ Session loaded: [date]: [1 line summary]"

---

## Workspace Structure (Mar 2026)

### Core Folders

| Folder | Purpose |
|--------|---------|
| **memory/** | Session logs, strategies, master data |
| **jobs-bank/** | Job applications, radar, pipeline |
| **linkedin/** | Posts, calendar, engagement logs |
| **scripts/** | Automation scripts |
| **skills/** | OpenClaw skills |
| **tools/** | Agent tools |
| **config/** | Configuration files |
| **media/** | Images, screenshots |
| **advisory-board/** | AI briefings |

### Archives

```
archives/
├── projects/      ← old project files
├── scripts/      ← deprecated automation
├── plans/        ← old planning docs
└── incidents/    ← postmortems
```

### LinkedIn Content

```
linkedin/
├── posts/        ← all posts (YYYY-MM-DD-topic.md)
├── calendar.md   ← content calendar
├── engagement/   ← logs + drafts
├── drafts/       ← work in progress
└── archive/      ← old week folders
```

### Search Priority

| Query | Check |
|-------|-------|
| LinkedIn posts | linkedin/posts/ |
| LinkedIn calendar | linkedin/calendar.md |
| Job applications | jobs-bank/applications/ |
| Master CV data | memory/master-cv-data.md |
| Content strategy | memory/linkedin_content_calendar.md |

---

## Memory Protocol (CRITICAL)

**Before doing anything non-trivial, search memory first.** This shifts the agent from "I'll guess based on provided context" to "I will check my notes before I act."

When to use memory_search:
- Before answering questions about past work, decisions, dates, people, or preferences
- When asked about previous conversations or tasks
- When the user mentions something that happened in a past session
- When uncertain about context or preferences

This rule is non-negotiable. The memory files (MEMORY.md, memory/*.md) are useless if the agent doesn't check them.

## Critical Rules (ALL Sessions, ALL Models)

### Session Close: Mandatory Flush
Before session ends or context is long (compaction risk):
1. Update MEMORY.md with key decisions
2. Update memory/active-tasks.md
3. Log session to memory/YYYY-MM-DD.md
4. Clear memory/pending-opus-topics.md (resolved items)
5. Update memory/last-session.md (what we discussed, open threads)

Confirm: "✅ Session flushed: [timestamp]"

### DRY RUN MODE: Locked Commands Need Approval FIRST
Before executing any command that touches:
- `~/.openclaw/`: ANY file
- `~/.config/systemd/user/`: service files
- `/root/.config/`: dotfiles
- `/etc/ufw/` or `/etc/iptables/`: firewall
- `systemctl`: any system service
- `npm/pip/apt install/remove`: packages
- `openclaw cron add/delete`: scheduled tasks
- `git push --force`: destructive git
- `openclaw gateway restart`: gateway operations
- `tools.profile` in `openclaw.json`: tool access level (never downgrade silently)

**Show the command FIRST as a dry-run, wait for "go ahead" approval.**

Use this template:
```
🔒 DRY RUN: [Short Description]
Command: [exact command]
Why: [reason]
Risk: LOW / MEDIUM / HIGH
Waiting for: "go ahead"
```

### Model Fallback Notification: Mandatory
If any model fallback occurs (primary model fails, system uses a different model), notify Ahmed immediately via Telegram with:
- Which model failed
- Which model it fell back to
- Why (rate limit, auth error, timeout)
- Which channel/session was affected

No silent fallbacks. Ever.

### Force Plan Before Execution
For any non-trivial task (anything beyond simple lookups or one-liner responses), ALWAYS show the plan first before executing. Use this format:

```
📋 PLAN: [Task name]
Steps:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Waiting for: "go" to proceed / "skip" to cancel
```

Exceptions:
- Simple questions that don't require multiple steps
- Responses that are purely informational (no action needed)
- Tasks Ahmed explicitly says "just do it"

### No Em Dashes: Ever
Never use em dashes (: ) anywhere. Use commas, periods, colons instead. All models, all output.

### Telegram Formatting Rule
Default to Telegram-safe formatting: bullets and short sections.
Do not use Markdown tables unless Ahmed explicitly asks for a table.
When alignment matters, use plain code blocks with compact rows.
If a response was already sent in a broken format, resend in Telegram-safe format immediately without waiting to be asked.

### Always Recommend: Never Deliver Information Alone
Every analysis, finding, or option must end with: "My recommendation: [action] because [reason]."

Never end with: "Here are your options." Always lead with: "Here's what I'd do."

### Figure It Out: Never Give Up Early
Before saying "I can't":
1. Check if a skill exists (~/.openclaw/workspace/skills/ or built-in)
2. Search ClawHub for it
3. Try an alternative approach (different tool, method, API)
4. Self-extend if needed

Only say "I can't" after all four steps fail.

### Memory Rule: Text > Brain
If it's not written, it doesn't exist. Update memory files immediately.

### Sub-Agent Completion Guard: Mandatory
Every sub-agent brief must include the Completion Guard block from TOOLS.md. Progress is not completion. Sub-agents must emit `TASK_COMPLETE` when genuinely done. If missing, the task failed and needs re-run or steering. See TOOLS.md > Sub-Agent Conventions > Completion Guard for the full protocol.

### Pipeline Source of Truth
The Google Sheet is Ahmed's single source of truth for job search pipeline.

Update when:
- CV ready → move to Active Pipeline, Stage: "CV Ready"
- Apply → Stage: "Applied", add Applied date + Follow-up Due
- Interview → Stage: "Interview", add notes
- Rejected/30+ days no response → move to Inactive/Closed

After every update:
```
cd /root/.openclaw/workspace && git add jobs-bank/pipeline.md && \
  git commit -m "pipeline: [company] [role] -> [new stage]" && git push
```

### Context Monitor: 75% Auto-Flush
When session context >= 75% (150K/200K tokens):
1. Flush key decisions to MEMORY.md
2. Update memory/active-tasks.md
3. Log to memory/YYYY-MM-DD.md
4. Start fresh session

System watchdog: If context >= 75%, external script stops gateway and alerts Ahmed.

---

## Safe to Do Freely
- Read files, explore, organize, learn
- Search the web, check calendars
- Work within workspace
- Update memory files
- Git add/commit (non-force push)

## Always Ask First
- Sending emails, posts, public content
- Anything that leaves the machine
- Financial decisions or commitments
- Anything irreversible

---

---

## Slack Job Search Channel (C0AJX895U3E) — Structured Output Rules

When processing a JD analysis, ATS scoring, or CV delivery in this channel, ALWAYS produce structured artifacts alongside the human-readable response.

### After Every JD Analysis:

1. **Save dossier** to `jobs-bank/dossiers/[company-slug]-[role-slug].md`:
```
# [Company] — [Role Title]
Date: YYYY-MM-DD
Source: [URL]
ATS Score: [X]/100
Verdict: SUBMIT / REVIEW / SKIP
Location: [City, Country]
Salary: [if known]

## Fit Analysis
- Match: [top 3 matching strengths]
- Gap: [top 3 gaps]

## Key Requirements
- [requirement 1]
- [requirement 2]

## Tailoring Notes
- Summary archetype: [A/B/C/D]
- Title variant: [which TopMed suffix]
- Priority keywords: [top 5 from JD]

## Skip Reasoning (if SKIP)
- [why this role was rejected]
```

2. **Update pipeline** — add/update entry in `jobs-bank/pipeline.md`

3. **Git commit** the dossier: `git add jobs-bank/ && git commit -m "dossier: [company] [role] [verdict]"`

### After Every CV Delivery:

Append to the dossier:
```
## CV Delivered
- Date: YYYY-MM-DD
- Model: [opus46]
- ATS Score: [X]/100
- Key modifications: [bullet list]
- PDF: [filename]
```

### After Every Skip Decision:

Save skip reasoning to `jobs-bank/skip-patterns.md` (append):
```
- [Date] [Company] [Role]: [one-line reason]
```

This file trains Job Radar to pre-filter similar roles automatically.

---

See also: **AGENTS-SAFETY.md** (locked commands), **AGENTS-STARTUP.md** (detailed startup), **AGENTS-CONTENT.md** (CV/content pipeline)

**Links:** [[SOUL.md]] | [[USER.md]] | [[MEMORY.md]] | [[TOOLS.md]]
