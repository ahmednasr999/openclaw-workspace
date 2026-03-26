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

## Task Board Rule (Non-Negotiable)

**Every task MUST be logged to the Mission Control Task Board BEFORE work starts.**
- No exceptions. No model exceptions. Applies to ALL models, ALL agents, ALL sessions.
- Use `POST http://localhost:3001/api/tasks/agent` with agent name, title, description
- Status starts as "In Progress", update to "QA" or "Completed" when done
- This includes: sub-agent spawns, cron jobs, manual work, code changes, research, content
- If it's work, it's on the board. Period.

---

## Model Strategy

| Task | Model | Notes |
|------|-------|-------|
| Default / daily | MiniMax-M2.7 | Free tier |
| Background / cron | MiniMax-M2.7 | Free tier |
| CV creation/review | Claude Opus 4.6 | Always - no approval needed |

**Rule:** Always ask before switching to paid models. Notify after any switch.

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

## Preferences

- **Timezone:** Cairo (Africa/Cairo, UTC+2)
- **Relocation:** Open to relocating to Jeddah, Saudi Arabia (confirmed Feb 18, 2026)
- **LinkedIn posts:** Always end with question/CTA for engagement
- **Backups:** Keep last 7, daily at 3 AM Cairo
- **Gmail check:** Daily at 8 AM Cairo
- **Formatting:** Never use em dashes (—) anywhere. Use hyphens (-) or commas instead.

---

## Notion Access (Critical Rule)

**Notion has a direct API token. Composio Notion connection is NOT required.**

Token lives at: `~/.openclaw/workspace/config/notion.json` → `{"token": "ntn_..."}`
Used by: ALL workspace scripts (morning-briefing-orchestrator.py, linkedin-auto-poster.py, email-agent.py, pipeline-agent.py, etc.)

**When Composio/meta-tool says "no active connection" for any app:**
1. STOP generating OAuth/reconnection flows
2. IMMEDIATELY grep workspace scripts for that app's token/credentials
3. If token found in scripts → use direct API, bypass Composio entirely
4. Only if no token exists → then try OAuth connection

This applies to EVERY app: Notion, Gmail, LinkedIn, Slack, Calendar, etc.
The workspace scripts are always the ground truth for what credentials exist.

## HuggingFace (Added 2026-03-26)
- **Token:** `config/huggingface.json` (hf_NPea...pnC)
- **Client:** `scripts/huggingface-client.py`
- **Working free:** FLUX.1-schnell (image), SD XL (image), Llama 3.3 70B (text via router/v1)
- **Not free:** SD 3.5, Bark TTS, MMS TTS, SpeechT5, NLLB translation, DistilBERT
- **Endpoint changed:** Old `api-inference.huggingface.co` → New `router.huggingface.co`

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
