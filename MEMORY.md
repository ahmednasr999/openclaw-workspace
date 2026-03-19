# MEMORY.md - Long-Term Memory

## Content Pipeline Workflow (Confirmed Feb 19, 2026)

**Mission Control has two boards:**
1. **Task Board** - High-level tracking (jobs, networking, applications, PMO tasks)
2. **Content Pipeline** - LinkedIn/X content creation (drafts, review, published)

**Workflow Option A (Confirmed):**
- Content Pipeline IS the work. Task Board is for tracking.
- Task = "Create LinkedIn post about X" → Create content post in Pipeline → Mark task complete
- Content Pipeline stores actual posts, drafts, and published content
- Task Board reminds us what needs to happen

**Content Pipeline Columns:**
- 💡 Ideas → 📝 Outline → ✍️ Draft → 🎨 Design → 👀 Review → ✅ Published

**Approval Flow:**
1. OpenClaw creates draft → moves to Review
2. Ahmed reviews in Content Pipeline → approves or requests edits
3. Ahmed moves to Published when ready to post

**Trigger:** Ahmed shares job link + description

**Steps:**
1. Analyze job requirements
2. Report ATS compatibility score (X/100)
3. Recommend model switch to Opus (wait for approval)
4. Create tailored CV matching keywords & requirements
5. Export as PDF
6. **Filename:** `Ahmed Nasr - {Title} - {Company Name}.pdf`
7. Send PDF via Telegram
8. Ask if switch back to MiniMax

**Filename Rules:**
- Format: `Ahmed Nasr - {Title} - {Company Name}` (spaces and dashes, NO underscores)
- Apply to BOTH HTML and PDF files
- Always use actual company name, not recruiter name
- If company is confidential/unnamed, use format: `Ahmed Nasr - {Title}` (no company suffix)
- Title should match the job title exactly

**Example filenames:**
- `Ahmed Nasr - Senior Program Manager - Nabat.html`
- `Ahmed Nasr - Senior Program Manager - Nabat.pdf`
- `Ahmed Nasr - Director of Business Excellence - Equinix.html`
- `Ahmed Nasr - Director of Business Excellence - Equinix.pdf`

---

## CV Design Rules (Permanent — Lessons Learned)

**Full ATS guide:** `memory/ats-best-practices.md`

### ATS-Friendly (Non-Negotiable)
- ❌ NO tables — ATS scrambles them
- ❌ NO multi-column layouts — ATS reads left-to-right across columns
- ❌ NO text boxes or floating elements
- ❌ NO headers/footers (often ignored by ATS)
- ❌ NO images, icons, or graphics
- ❌ NO special bullet characters (● ► ★)
- ✅ Single column layout ONLY
- ✅ Simple bullet lists (use - or •)
- ✅ Standard section headers (Professional Summary, Experience, Education, Skills, Certifications)
- ✅ Reverse chronological order
- ✅ Consistent date format (MMM YYYY – Present)

### Bullet Writing (AVR Pattern)
Every bullet: **Action Verb + Value/What + Result/Metric**
- ✅ "Led digital transformation across 15-hospital network, managing $50M budget"
- ❌ "Responsible for digital transformation projects"

### Keyword Strategy
- Mirror exact JD phrases (not synonyms)
- Top 5 JD keywords must appear in Summary + most recent role
- Include both acronyms AND full terms: "Project Management Professional (PMP)"
- Critical keywords: 2-3x across CV (naturally distributed)

---

**Task Board Rule:** See AGENTS.md (single source of truth).
**Model Strategy:** See TOOLS.md (single source of truth).

---

## Strategic Intelligence Framework (Optional)

**Activation:** Only when Ahmed explicitly requests it

**Triggers:**
- "use the framework"
- "think strategically about..."
- "apply the 10-step system"
- Any explicit request for multi-agent debate

**Implementation: Hybrid A + B**

| Request Type | Approach |
|--------------|----------|
| Quick strategic request | Internal simulation (fast) |
| High-stakes, complex | Spawn sub-agents for true debate |
| Routine tasks | Skip framework (direct output) |

**Default:** Efficient direct response for everything else

---

## Memory System Protocol

### Session Startup (Every Session)
1. **Read MEMORY.md** (this file) — Long-term context
2. **Check active-tasks.md** — Resume any interrupted work  
3. **Read today's daily notes** if they exist (memory/YYYY-MM-DD.md)

### During Session (Immediate Capture)
Write to daily notes immediately when:
- ✅ Complete something important
- 🎯 Learn a user preference  
- 📋 A decision gets made
- 💡 Something worth remembering happens

### Finding Things
- **Search:** Use `memory_search "terms"` across all memory files
- **Specific sections:** Use `memory_get` to pull exact content

### Maintenance
- **Weekly:** Move important daily notes to MEMORY.md
- **Monthly:** Move technical learnings to TOOLS.md  
- **Quarterly:** Remove outdated content

### Principle
**Text beats brain.** If you want to remember it, write it down.

### Lessons Learned Log

Store in: `memory/lessons-learned.md`

Format:
```
## [Date]
### What I Missed
[Specific example]
### Why
[Root cause]
### Fix
[What I'll do differently]
```

---

## Context Tiering

**See CONTEXT-TIERS.md for full documentation.**

Brief summary: Use tiered context loading to reduce token usage:
- **L0** (always): IDENTITY.md, USER.md, SOUL.md, HEARTBEAT.md (if non-empty)
- **L1** (task-triggered): AGENTS.md, TOOLS.md, SKILL.md, coordination/*.json
- **L2** (on-demand): memory/master-cv-data.md, memory/daily-*.md, memory/ats-best-practices.md

Don't load all files every session. Load only what's needed for the task.

---

## Context Audit Trail

**Purpose:** Debug sub-agent behavior by tracking what context/files/skills were loaded.

**Location:** `memory/context-traces/`

**When to use:**
- After spawning a sub-agent for CV creation, content posting, or research tasks
- When debugging unexpected agent behavior
- Review traces to understand what context influenced the agent's output

See `memory/context-traces/README.md` for full system details.

---

## Auto Lessons Learned

**Lightweight automatic lesson capture — runs daily at 11 PM Cairo.**

The old self-improvement skill was disabled because it injected 12x per session, wasting tokens. This new system runs once per day instead.

### How It Works

1. **Cron job** (`scripts/auto-lessons-learned.py`) runs at 11 PM Cairo daily
2. **Scans** all sessions from `~/.openclaw/agents/main/sessions/`
3. **Filters** trivial sessions (< 5 user exchanges)
4. **Extracts** lessons via LLM:
   - Corrections made by user
   - Errors encountered
   - Preferences learned
   - Better approaches discovered
   - Missed opportunities
5. **Appends** to `memory/lessons-learned.md`

### Format

```markdown
## [Date]

### Category
- What happened → What to do differently
```

Categories: `correction`, `error`, `preference`, `improvement`, `missed_opportunity`

### Files

- **Script:** `scripts/auto-lessons-learned.py`
- **Skill:** `skills/cron/auto-lessons/SKILL.md`
- **Log:** `memory/lessons-learned.md`

### Manual Run

```bash
python scripts/auto-lessons-learned.py --all  # Process today's sessions
python scripts/auto-lessons-learned.py       # Latest session only
python scripts/auto-lessons-learned.py --dry-run  # Preview
```

### Coexists with Manual Capture

- **Manual:** User says "remember this" → log immediately to daily notes
- **Auto:** Captures session-wide patterns at end of day
- Both feed into `memory/lessons-learned.md`

---

## Preferences

- **Timezone:** Cairo (Africa/Cairo, UTC+2)
- **Relocation:** Open to relocating to Jeddah, Saudi Arabia (confirmed Feb 18, 2026)
- **LinkedIn posts:** Always end with question/CTA for engagement
- **LinkedIn posting:** See TOOLS.md "LinkedIn Posting" section for full technical details.
- **LinkedIn daily post:** Auto-post allowed (9:30 AM cron, no approval needed)
- **LinkedIn comments:** NEVER post without Ahmed's explicit approval. Always draft and present for review first. No exceptions.
- **Backups:** Keep last 7, daily at 3 AM Cairo
- **Gmail check:** Daily at 8 AM Cairo
- **Formatting:** Never use em dashes (—) anywhere. Use hyphens (-) or commas instead.

---

## Key Files

### Core Memory
- **MEMORY.md** — This file, long-term context (read every session)
- **TOOLS.md** — Technical configs and how-tos
- **memory/active-tasks.md** — In-progress work (check on startup)
- **memory/YYYY-MM-DD.md** — Daily notes (immediate capture)
- **memory/master-cv-data.md** — CV source of truth

### Master CV Files
- **Master CV PDF:** `/root/.openclaw/media/inbound/file_99---61a97145-01ba-402f-b33b-5915c31c8daf.pdf`
- **Master CV DOCX:** `/root/.openclaw/media/inbound/file_100---a1dce511-4dda-481f-aff5-c9093298c040.docx`

### Skills & Frameworks
- **ATS Best Practices:** `memory/ats-best-practices.md`
- **Marketing Skills:** `marketing-skills/` directory
- **Content Analysis:** `docs/content-claw/caught/` directory

## CV Creation Rule (Critical)
**ALWAYS read `memory/master-cv-data.md` before creating any CV.**
Never fabricate roles, titles, or achievements. Use exact titles and dates from master CV.
