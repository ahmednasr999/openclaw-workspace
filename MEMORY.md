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
3. Create tailored CV matching keywords & requirements (GPT-5.4 handles everything)
4. Export as PDF
5. **Filename:** `Ahmed Nasr - {Title} - {Company Name}.pdf`
6. Send PDF via Telegram

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

## Verify Before Reporting (Non-Negotiable) <!-- dream-promoted 2026-04-02 -->

**Exit code 0 ≠ success. Subprocess ran ≠ message delivered. API returned 200 ≠ content correct.**

This has caused 3+ incidents (Mar 23: LinkedIn truncation, Mar 29: wrong image posted, Mar 30: alerts never delivered).

**Rule:** Before saying "done" or "it worked":
1. Check the ACTUAL OUTCOME - not the script log, not the exit code
2. For Telegram: was the message received in the correct chat/thread?
3. For LinkedIn: was the full content posted correctly (not truncated)?
4. For scripts using `openclaw` CLI: use `--target` not `--to` (verify params before running)
5. When in doubt, quote actual output - don't paraphrase success

**Specific gotcha:** `openclaw` CLI uses `--target` for recipient. Using `--to` fails silently (exit 0, no delivery).

---

## Task Board Rule (Historical)

Previous workflow used Mission Control task logging at `http://localhost:3001/api/tasks/agent`.

**Override from Ahmed on 2026-04-09:** No more Mission Control.
- Do not log tasks to Mission Control
- Do not treat localhost:3001 task-board failures as blockers
- Only resume this workflow if Ahmed explicitly asks to re-enable it

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

## Model Override Reversion (Confirmed Apr 6, 2026) <!-- dream-promoted 2026-04-07 -->

Ahmed manually switched to Opus 4.6 on Apr 6 — it kept reverting every new Telegram message turn to MiniMax/Qwen. Had to say "opus 4.6" 5+ times in one session. Dist-patch fix applied to reply-CxEVitwF.js + model-selection-CDZG0zcK.js. Rule: If Ahmed sets a model, DON'T revert it. Treat his model choice as final until he changes it himself.

---

## Service Credentials (Non-Negotiable) <!-- dream-promoted 2026-04-02 -->

**This rule has been violated TWICE (Mar 21 + Mar 27). It is permanent and non-negotiable.**

Before initiating ANY OAuth/Composio connection flow for ANY service:
1. **STOP** — do not generate auth links or reconnection flows
2. Check `config/service-registry.md` (master credential map)
3. Check `config/` directory for existing token files
4. Grep workspace scripts for API calls to that service
5. If credentials exist → use direct API. **Never use Composio for Notion or Telegram.**
6. Only if NOTHING found → then consider OAuth

**Known direct credentials (no Composio needed):**
- **Notion:** `config/notion.json` → `{"token": "ntn_..."}`
- **Telegram:** bot token in scripts or `config/telegram.json`
- **Gmail:** App Password in `/root/.config/gmail-smtp.json`
- **LinkedIn:** Composio `ca_yGwr2ocbcRZi` IS required (no direct creds)

The workspace scripts and `config/` directory are always the ground truth. Asking Ahmed to authenticate before checking is a failure.

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

## Operating Baseline (Confirmed 2026-04-07)

### Model Stack
- Primary (all agents): `openai-codex/gpt-5.4` via ChatGPT Pro OAuth
- Fallback: `minimax-portal/MiniMax-M2.7`
- No Anthropic, no Moonshot, no OpenRouter free tier

### What Was Fixed Today
1. All 4 agents migrated from dead Claude/OpenRouter to GPT-5.4
2. 20 cron jobs re-pinned to GPT-5.4
3. Duplicate user-level systemd gateway service disabled
4. Tavily env override cleaned
5. `AGENTS.md` trimmed from ~24K to ~3K chars
6. `TOOLS.md` trimmed from ~26K to ~2.5K chars
7. Slack reverted to socket mode (stable config)
8. `SOUL.md` and `AGENTS.md` updated for GPT-5.4 references
9. All auth cooldowns cleared
10. Gateway startup spam eliminated
11. `config/model-router.json` default_model changed from MiniMax-M2.7 to GPT-5.4; all rule references updated; dead Claude models removed; `after_task_completion` kept as MiniMax fallback

### Model Router Config (CRITICAL — Do Not Reset)
**File:** `/root/.openclaw/workspace/config/model-router.json`
- `default_model` MUST be `openai-codex/gpt-5.4`
- `after_task_completion` is DISABLED (no auto-switch to MiniMax)
- This file overrides per-session model choices. If session keeps falling back to MiniMax, check this file first.
- This file was reset on 2026-04-07 after a restart — it had MiniMax as default again.

### Standing Rule: Post-Restart Model Router Check
**After any gateway restart, immediately verify `config/model-router.json` `default_model` is `openai-codex/gpt-5.4`.**
If it reverted, fix it before doing anything else. This has happened twice (Apr 6 and Apr 7).

### Model Guardian Cron (Created 2026-04-07)
**Job ID:** `068f8a9b-00e3-4bc3-85b5-9d31220a4859`
**Schedule:** Every 6 hours (0 */6 * * *), Cairo timezone
**Script:** `/tmp/model-guardian-check.py`
**What it checks:**
1. model-router.json default is GPT-5.4
2. OpenAI Codex token is valid (via log evidence + API probe)
**Alert:** Sends Telegram to 866838380 if either check fails
**Last run result:** ALL_OK (model-router correct, 118 GPT-5.4 calls in today's log)

### Watchlist
- OpenAI Codex OAuth token — monitor expiry and confirm auto-refresh works
- MiniMax is retired, do not use it unless Ahmed explicitly asks
- Slack pong timeouts may still appear, monitor but don't act unless they cause message drops
- stale `plugins.allow` entries (`auth`, `send`) are cosmetic, remove when convenient

### Standing Order
- Do not silently switch models. If GPT-5.4 fails, notify Ahmed immediately.
- If OpenClaw gets updated and GPT-5.4 stops working, restore from the `.WORKING-GPT54` backup files immediately, then alert Ahmed.
- Critical GPT-5.4 config: the `openai-codex` provider must use `baseUrl` `"https://chatgpt.com/backend-api"` with `api` `"openai-codex-responses"`. If this is ever overwritten, restore it immediately and alert Ahmed.
- Resume normal operations: heartbeats, cron jobs, daily intel, job hunting, content pipeline.
- Run a self-health-check every Sunday morning and post results to CEO General thread.

