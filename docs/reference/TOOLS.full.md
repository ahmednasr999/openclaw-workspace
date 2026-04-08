# TOOLS.md - Technical Configs & How-To

*Technical configurations, troubleshooting, and environment-specific setup*

## ⚠️ NON-NEGOTIABLE: LinkedIn Job Scraping Method

**ALWAYS use JobSpy with `linkedin_fetch_description=True`. No exceptions. No alternatives.**

```python
from jobspy import scrape_jobs
jobs_df = scrape_jobs(
    site_name=["linkedin"],
    search_term=title,
    location=location,
    results_wanted=20,
    hours_old=168,
    linkedin_fetch_description=True,
    description_format="markdown",
    verbose=0,
)
```

**Why this works:** JobSpy hits LinkedIn's public `/jobs/view/` endpoint — returns full JDs without login, cookies, or proxies. Works from any VPS.

**NEVER use:**
- `requests` + BeautifulSoup scraping of `linkedin.com/jobs/search/`
- Selenium/Playwright LinkedIn automation for job search
- Composio LinkedIn tools for job scraping
- Any method requiring auth or cookies

**Script:** `scripts/jobs-source-linkedin-jobspy.py`
**Reference:** https://github.com/DaKheera47/job-ops

### SAYYAD Job Dedup Fix (Non-Negotiable) <!-- dream-promoted 2026-04-06 -->

**Problem:** Same jobs re-posted with new LinkedIn IDs (Atos CTO appeared SUBMIT twice, JCA Associates twice).

**Fix (2026-04-05):**
1. DB dedup query must use `WHERE applied_date IS NOT NULL` instead of `status IN ('applied','interview')` — catches all applied jobs regardless of current status
2. Stage 3c added: fuzzy dedup (88% threshold) by company+title against ALL historical jobs, skipping only same URL hash
3. This catches re-posts where LinkedIn assigns a new job ID but the role is identical

**Also:** Apply same pattern when debugging any dedup gap — check what the query actually excludes, not just what it includes.

## LinkedIn Engagement - Source Rules (NON-NEGOTIABLE)

**Morning briefing Exa engagement** - uses Exa to find posts by topic/hashtag. Separate system. Untouched.

**Daily comments job (11 AM)** - uses Ahmed-Mac Chrome ONLY to scrape his live LinkedIn feed.
- NEVER use Exa for the daily comments job
- NEVER add Exa as a fallback for the daily comments job
- Source is linkedin.com/feed/ via browser tool (node=Ahmed-Mac)
- If Ahmed-Mac is offline, skip that day - do NOT fall back to Exa

These are two separate systems. Keep them separate. Always.

## LinkedIn Engagement Agent

### Overview
Daily agent that finds the 5 best LinkedIn posts for Ahmed to comment on, drafts comments in his voice, and sends to Telegram for 1-tap approval before posting.

### Key Files
- **Script:** `scripts/linkedin-engagement-agent.py`
- **Pending state:** `data/linkedin-engagement-pending.json` (active posts awaiting approval)
- **Log:** `logs/linkedin-engagement.log`

### Cron Schedule
`0 7 * * 0-4` - 9 AM Cairo (Sun-Thu), before the working day starts

### Telegram Output
- **Chat:** Nasr Command Center (-1003882622947)
- **Thread:** topic_id=7 (CMO Desk)
- **Format:** 5 separate messages, each with [✅ Post It] [✏️ Edit] [❌ Skip] buttons

### Workflow
1. Load Ahmed's context (career, sectors, personas) from MEMORY.md + ontology graph
2. Discover 30-50 candidate posts via Exa search (fresh GCC/sector posts)
3. Score each post: career overlap + persona match + comment gap + brand fit (0-100)
4. Draft comments in Ahmed's voice for top 5
5. Send to Telegram thread for approval
6. On approval: browser posts comment + like on Ahmed-Mac
7. Updates ontology graph: Person entity gets `last_commented` field (14-day cooldown)

### Manual Run
```bash
# Dry run (no Telegram send, prints to console)
python3 scripts/linkedin-engagement-agent.py --dry-run

# Live run
python3 scripts/linkedin-engagement-agent.py
```

### Ontology Fields Used
- `Person.last_commented` (date) - prevents re-commenting within 14 days
- `Person.last_commented_post` (URL) - tracks which post was commented on
- New persons auto-created when commenting on someone not yet in graph

---

## CV Creation Workflow

### Models by Task
- **Default/Daily:** MiniMax-M2.7 (free tier)
- **CV Creation:** Claude Opus 4.6 (requires approval)
- **Analysis/Research:** Claude Sonnet 4.6

## Model Strategy (Verified Working - 2026-02-17)

### Available Models (Tested & Confirmed)

| Provider | Alias | Model | Use Case | Cost | Status |
|----------|-------|-------|----------|------|--------|
| **Anthropic** | `opus` | claude-opus-4-6 | Complex tasks, CV creation | 💎 Premium | ✅ Works |
| **Anthropic** | `sonnet` | claude-sonnet-4-6 | Balanced (troubleshooting, setup) | ⚡ Mid | ✅ Works |
| **Anthropic** | `opus-4.5` | claude-opus-4-5 | Legacy fallback | 💎 Premium | ✅ Works |
| **Anthropic** | `sonnet-4` | claude-sonnet-4 | Legacy fallback | ⚡ Mid | ✅ Works |
| **MiniMax** | `minimax-m2.7` | MiniMax-M2.7 | Daily tasks, default model | ✅ Free | ✅ Works |
| **MiniMax** | `minimax-m2.5` | MiniMax-M2.5 | Lightweight tasks | ✅ Free | ✅ Works |
| **MiniMax** | `minimax-m2.1` | MiniMax-M2.1 | Legacy fallback | ✅ Free | ✅ Works |
| **Moonshot** | `Kimi` | kimi-k2.5 | Alternative reasoning, research | ⚡ Mid | ✅ Works |

### Not Working (Do Not Use)

| Provider | Alias | Model | Issue |
|----------|-------|-------|-------|
| **Anthropic** | `haiku-3.5` | claude-3-5-haiku-20250520 | Legacy | ❌ 404 Error |
| **Anthropic** | `haiku-3` | claude-3-haiku-20240307 | Legacy | ❓ Untested |

### Model Selection Rules
1. **Default (ALL agents):** Claude Sonnet 4.6 — fallback MiniMax-M2.7
2. **CV Creation:** Claude Opus 4.6 — NON-NEGOTIABLE. Always spawn Opus sub-agent for CV tailoring. If Opus is slow or stalls (4+ minutes), kill and spawn a fresh Opus sub-agent. Do NOT fallback to Sonnet or MiniMax for CVs.
3. **Alternative Reasoning:** Kimi K2.5

### Model Change Protocol
- **Default:** Sonnet 4.6 (all agents, all sessions)
- **Fallback:** MiniMax-M2.7 (automatic if Sonnet unavailable)
- **Ask before changing:** Switching to Opus (premium)
- **Notify:** When switching to/from Opus

### Switching Models
- Use alias: `switch to opus`, `switch to sonnet`, `switch to Kimi`
- Always notify user when switching to paid models
- Switch back to MiniMax after completing expensive tasks

### File Naming Convention
See MEMORY.md "CV Design Rules" section (single source of truth).

### ATS Compliance
Full ATS rules: See MEMORY.md "CV Design Rules" section.

## LinkedIn Posting (via Composio)

### Connection
- **Status:** ✅ WORKING - Connected since 2026-03-13
- **Method:** Composio `LINKEDIN_CREATE_LINKED_IN_POST` tool
- **Person URN:** `urn:li:person:mm8EyA56mj`
- **Connected Account:** `ca_yGwr2ocbcRZi` (ACTIVE)

### How to Post
1. **Text-only post:** Call `COMPOSIO_SEARCH_TOOLS` for LinkedIn posting, then `COMPOSIO_MULTI_EXECUTE_TOOL` with:
   - tool_slug: `LINKEDIN_CREATE_LINKED_IN_POST`
   - arguments: `{"author": "urn:li:person:mm8EyA56mj", "commentary": "<post text>", "visibility": "PUBLIC"}`

2. **Post with image (TESTED WORKING 2026-03-25):**
   - Step 1: Download image locally
   - Step 2: Upload to Composio S3 via `upload_local_file("/tmp/image.png")` in REMOTE_WORKBENCH
   - Step 3: Get `s3key` from upload result
   - Step 4: Call `LINKEDIN_CREATE_LINKED_IN_POST` with `images: [{"name": "image.png", "mimetype": "image/png", "s3key": "<s3key>"}]`
   - **NEVER post text-only if image was expected** - always hold for review
   - Full docs: `docs/linkedin-image-post-flow.md`

3. **Bold text:** LinkedIn doesn't render markdown. Convert `**text**` to Unicode Mathematical Bold:
   - A-Z: U+1D5D4 to U+1D5ED, a-z: U+1D5EE to U+1D607, 0-9: U+1D7EC to U+1D7F5
   - Script helper: `scripts/linkedin-auto-poster.py` has `convert_bold_markdown()` function

### Auto-Poster Cron
- **Cron ID:** `7ba5f8f7-6eec-4301-bfa6-185dee16e778`
- **Schedule:** 9:30 AM Cairo, Sun-Thu
- **Script:** `scripts/linkedin-auto-poster.py`
- **SKILL.md:** `skills/cron/linkedin-daily-post/SKILL.md`
- **Flow:** Reads Notion Content Calendar (Status=Scheduled, Date=today) -> extracts text + image -> converts bold -> posts via Composio -> updates Notion to "Posted"

### Content Calendar (Notion)
- **DB ID:** `3268d599-a162-814b-8854-c9b8bde62468`
- **Properties:** Title, Hook, Status (Posted/Drafted/Scheduled), Planned Date, Draft, Post URL, Topic, Day
- **Image convention:** Stored as external image blocks in page body, hosted on GitHub raw URL

### LinkedIn API Limitations
- `LINKEDIN_GET_POST_CONTENT` requires URN format, returns 403 for own posts
- `LINKEDIN_GET_SHARE_STATS` only works for organization pages, not personal profiles
- Post commentary max: 3000 characters
- Images: up to 20 per post

### Manual LinkedIn Posting (Image Flow)
When manually posting to LinkedIn with an image:
1. **Source of truth = Notion** - always pull images from Notion page blocks (type `file` gives signed S3 URL)
2. Download from Notion to `/tmp/`
3. Upload to Composio S3 via `upload_local_file()` in REMOTE_WORKBENCH → get `s3key`
4. Post via `LINKEDIN_CREATE_LINKED_IN_POST` with `images: [{name, mimetype, s3key}]`
5. **NEVER use Google Drive links** - they may be stale/outdated versions

**⚠️ Composio Sandbox Cannot Reach Local IPs** <!-- dream-promoted 2026-04-06 -->

The Composio sandbox is network-isolated. It CANNOT reach VPS-local IPs (e.g., `76.13.46.115`). If an image is expected and the upload fails due to unreachable URL, **STOP and report to Ahmed immediately**. Never post text-only by default.

Workaround: Images must be served from a public URL (Notion CDN, GitHub raw, S3, or uploaded to Composio S3 first). The auto-poster script running on the VPS can reach local IPs directly.

### Image Generation Chain (Topic-Aware Routing, All Free)
- **Chain script:** `scripts/image-gen-chain.py` (ImageGenChain class + CLI)
- **Prompt builder:** `scripts/gemini-image-gen.py` (topic templates, Notion integration)
- **Text overlay:** `apply_text_overlay()` in chain script - adds headline + author + hashtags to raw images
- **Convenience:** `chain.generate_with_overlay()` - generates + overlays in one call (skips PIL since it already has text)

**Topic-Aware Routing (updated 2026-03-26, 6 sources):**
| Topic Category | Priority Order | Rationale |
|---|---|---|
| AI/Tech (AI, Digital Transformation, HealthTech, FinTech, Data, Innovation) | Gemini Flash → FLUX.1 → SD XL → Gemini Pro → Stock → PIL | Abstract/futuristic visuals, HF fallback before Pro |
| Business (PMO, Strategy, Leadership, Healthcare) | Stock → Gemini Flash → FLUX.1 → Gemini Pro → SD XL → PIL | Corporate imagery first, AI gen as fallback |
| Default/Other | Gemini Flash → FLUX.1 → Stock → SD XL → Gemini Pro → PIL | Balanced with HF models interleaved |

**Working Sources:**
1. `GEMINI_GENERATE_IMAGE` gemini-2.5-flash-image - 1344x768, ~10s, primary (Composio)
2. **`FLUX.1-schnell`** (HuggingFace) - 1024x1024, ~8s, fast, great quality (FREE)
3. **`Stable Diffusion XL`** (HuggingFace) - 1024x1024, ~15s, reliable (FREE)
4. `GEMINI_GENERATE_IMAGE` gemini-3-pro-image-preview - 5504x3072 4K, ~15s, fallback (Composio)
5. `COMPOSIO_SEARCH_IMAGE` - stock photos, ~2s, good for business topics
6. PIL branded templates via `content-factory-visuals.py` - <1s, always works, safety net

**HuggingFace Setup:**
- Token: `config/huggingface.json` → `{"token": "hf_..."}`
- Client: `scripts/huggingface-client.py` (image gen + chat via HF Inference API)
- Endpoint: `https://router.huggingface.co/hf-inference/models/{model}`
- Key win: Cron jobs now get AI-generated images without Composio (FLUX catches before PIL)

**Dead Sources (removed 2026-03-26):**
- Gemini 2.0 Flash Exp - model deprecated (404)
- DreamStudio SDXL - 0 credits, Stability no longer gives free credits
- Pollinations.ai - now requires auth (401)
- SD 3.5 Large - requires paid HF endpoint
- HuggingFace TTS (Bark/MMS/SpeechT5) - not on free inference tier

- **Topic templates:** 10 topics (Healthcare, HealthTech, AI, Digital Transformation, PMO, Strategy, FinTech, Leadership, Innovation, Data)
- **Flow in auto-poster:** Cron generates PIL template → sets `image_upgrade_available` flag with `preferred_source` (gemini or stock) → agent uses `image-gen-chain.py` with topic routing when posting
- **Note:** S3 URLs expire (1-6 hours) - download immediately after generation

### Available Composio LinkedIn Tools
- `LINKEDIN_CREATE_LINKED_IN_POST` - Create post (text + optional images)
- `LINKEDIN_INITIALIZE_IMAGE_UPLOAD` - Get upload URL for image
- `LINKEDIN_REGISTER_IMAGE_UPLOAD` - Alternative image upload method
- `LINKEDIN_GET_MY_INFO` - Get authenticated user info
- `LINKEDIN_GET_POST_CONTENT` - Read post content (limited)
- `LINKEDIN_DELETE_POST` - Delete a post

## Authentication & APIs

### Gmail (Himalaya)
- **Status:** ✅ WORKING - Full IMAP/SMTP access
- **Tool:** Himalaya email client
- **Auth:** Gmail App Password (`wvdklorwnunbyjir` in `/root/.config/gmail-smtp.json`)
- **Capabilities:** List, read, delete, move emails, folder management
- **Limitation:** Cannot access Gmail category tabs (Promotions, Social) directly via IMAP
- **Note:** GOG OAuth was abandoned due to persistent keyring issues

### Web Search
- **Status:** Missing Brave API key
- **Setup:** `openclaw configure --section web`
- **Fallback:** Use web_fetch for direct URL content

## File Locations

### Master Data
- **CV Data:** `/memory/master-cv-data.md` (source of truth)
- **Master PDFs:** `/media/inbound/file_99*.pdf` and `file_100*.docx`
- **ATS Guide:** `/memory/ats-best-practices.md`

### Marketing Skills
- **Location:** `/marketing-skills/`
- **Framework files:** linkedin-transformation-executive.md, transformation-consulting-positioning.md, etc.

### Content Analysis
- **Reviews:** `/docs/content-claw/caught/` (permanent)
- **Skips:** `/docs/content-claw/released/skip/` (14-day retention)

## Browser Automation (Non-Negotiable)

**ALWAYS use Ahmed-Mac Chrome FIRST for any browser task.**
- Node: `Ahmed-Mac`, profile: default (omit profile param)
- Ahmed is logged into YouTube, LinkedIn, Gmail, X, etc. on this browser
- Never attempt Camoufox or server-side curl/fetch first for sites requiring login or bot detection
- Only fall back to Camoufox/server tools if Ahmed-Mac is offline or task doesn't need login

**When this rule was added:** 2026-03-27 (Ahmed corrected me for forgetting)

## ⚠️ NON-NEGOTIABLE: X (Twitter) & YouTube Access Methods

### X (Twitter) - READING Public Tweets
- **Primary (server-side):** oEmbed API
  - Endpoint: `https://publish.twitter.com/oembed?url=<tweet-url>&dnt=true`
  - No auth needed, works from any server IP
  - Returns: author name, handle, date, full tweet text
  - Works for: any public tweet (no login required)
  - Script: `scripts/x-tweet-reader.py`
- **Fallback:** Ahmed-Mac Chrome via `browser.proxy` snapshot (when oEmbed fails or for logged-in views)
- **Known tab ID:** `14B716687B852F8A4F4CD87D7C5418CC`
- **NEVER:** Server-side curl of x.com directly (returns JS-heavy HTML, no content)

### X (Twitter) - ENGAGEMENT (Posting/Replying/Liking)
- Requires Ahmed-Mac Chrome (browser.proxy) or valid session cookies + working browser
- Camoufox NOT installed on VPS (missing `camoufox-js` dependency)
- Twitter API (v2) Bearer Token: VALID but account has zero credits

### YouTube
- **Primary:** Ahmed-Mac Chrome via `browser.proxy` snapshot (logged in)
- **For transcripts ONLY via Mac** - VPS IP is permanently blocked by YouTube
- **Known:** Camoufox also works for public video pages
- **Never:** Server-side yt-dlp, youtube-transcript-api, or any direct VPS fetch to YouTube
- **Can do:** Read video descriptions, extract transcripts/captions, navigate to videos

**Rule:** Any X or YouTube task → Ahmed-Mac Chrome first. No trials, no wasted time. If Mac is offline, flag it immediately and don't attempt server-side workarounds.

### Confirmed Working: YouTube Transcript via XHR Interception (2026-03-31)

**Extension v4.0** - intercepts YouTube's own /api/timedtext XHR/fetch calls.

```bash
# 1. Navigate to video
curl -s -X POST http://localhost:3010/navigate \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=VIDEO_ID","secret":"nasr-bridge-2026"}'

# 2. Wait 5s for page load, then fetch transcript (waits up to 30s for CC to trigger)
sleep 5 && curl -s -X POST http://localhost:3010/fetch_transcript \
  -H "Content-Type: application/json" \
  -d '{"secret":"nasr-bridge-2026"}' --max-time 35
```

**Why this works:** Overrides XHR/fetch in MAIN world before YouTube loads. When YouTube fetches its own captions internally, extension grabs a copy. No auth, no params, no API calls needed.

**Why nothing else works:**
- VPS IP blocked by YouTube (yt-dlp, youtube-transcript-api all fail)
- timedtext URLs contain ip=0.0.0.0 in signed sparams - can't replace without breaking signature
- Service worker fetch is cross-origin - cookies don't attach
- Chrome CSP blocks eval() - no string eval in extensions
- InnerTube get_transcript API returns 400 from outside browser context

**DO NOT attempt any other approach. This is the only one that works.**

---

### Confirmed Working Pattern: browser.proxy via nodes.invoke (2026-03-31)

**Only `/snapshot` path works.** Other paths (/navigate, /evaluate, /act, /json/new) return "Not Found".

```python
# Read page content (accessibility tree as text)
nodes.invoke(
    node="Ahmed-Mac",
    invokeCommand="browser.proxy",
    invokeParamsJson=json.dumps({
        "path": "/snapshot",
        "targetId": "14B716687B852F8A4F4CD87D7C5418CC",  # X tab
        "compact": True
    })
)

# Navigate to URL using search/type action
nodes.invoke(
    node="Ahmed-Mac",
    invokeCommand="browser.proxy",
    invokeParamsJson=json.dumps({
        "path": "/snapshot",
        "targetId": "...",
        "type": {"ref": "<search_box_ref>", "text": "search query", "pressEnter": True}
    })
)

# Click a link/button
nodes.invoke(
    node="Ahmed-Mac",
    invokeCommand="browser.proxy",
    invokeParamsJson=json.dumps({
        "path": "/snapshot",
        "targetId": "...",
        "click": "e36"  # ref from previous snapshot
    })
)
```

**Known Chrome tab IDs (Ahmed-Mac):**
- X/Twitter: `14B716687B852F8A4F4CD87D7C5418CC`
- LinkedIn: `825CE2A6B8DE6C48AD14DBAD6A017B00`

**Reading tweets (CONFIRMED WORKING - 2026-03-31):**
1. POST navigate command to bridge: `curl -X POST http://localhost:3010/navigate -d '{"url":"<tweet_url>","secret":"nasr-bridge-2026"}'`
2. Wait 4 seconds for page load
3. Snapshot the X tab: `browser.proxy /snapshot targetId=14B716687B852F8A4F4CD87D7C5418CC`
4. Parse tweet text, stats, and replies from accessibility tree

Extension v1.1 navigates EXISTING tab in-place - keeps same targetId, no new tab issues.
Extension zip: `browser-bridge/nasr-browser-bridge-extension.zip`

**Workflow for reading any site:**
1. Call `/snapshot` with targetId to get accessibility tree + current URL
2. Find refs for interactive elements (search box, links, etc.)
3. Use `type` or `click` params to navigate/interact
4. Call `/snapshot` again after interaction to read new page content

**Works for:** X/Twitter, YouTube (logged in), LinkedIn, any site Ahmed has open
**Does NOT support:** `/evaluate` (JS execution), `/navigate` (direct URL), `/screenshot` via this method

---

## Troubleshooting

### OAuth Issues
- GOG auth tends to fail on first setup
- Clear auth: `gog auth remove [email]`
- Use manual workarounds for Gmail/Calendar

### Model Switching
- Always ask before switching to paid models
- Notify when switching back to default
- Opus for CV creation only

### CV Files
- Filename rules: See MEMORY.md "CV Design Rules"
- Master CV data: `memory/master-cv-data.md`
- Never fabricate roles or achievements

## Environment Setup

### Cron Jobs
- GitHub backup: Daily
- Gmail monitoring: 8 AM Cairo (when working)
- Usage alerts: 9 AM Cairo

### Timezone
- User: Cairo (Africa/Cairo, UTC+2)
- System: UTC
- Always specify timezone for meetings/deadlines

## Ontology Knowledge Graph

### Daily Briefing (single command, replaces reading 4 JSON files)
```bash
python3 /root/.openclaw/workspace/scripts/ontology-briefing.py
```

### Common Queries
```bash
# Open applications
python3 skills/ontology/scripts/ontology.py list --type JobApplication

# Interviews only
python3 skills/ontology/scripts/ontology.py query --type JobApplication --where '{"status": "interview"}'

# High-priority outreach
python3 skills/ontology/scripts/ontology.py query --type Outreach --where '{"priority": "high"}'

# Scheduled content
python3 skills/ontology/scripts/ontology.py query --type LinkedInPost --where '{"status": "scheduled"}'

# Add new job application
python3 skills/ontology/scripts/ontology.py create --type JobApplication --props '{"title":"...","company":"...","status":"applied","date_applied":"YYYY-MM-DD"}'
```

### Graph Location
- Entities: `memory/ontology/graph.jsonl` (append-only)
- Schema: `memory/ontology/schema.yaml`
- Briefing script: `scripts/ontology-briefing.py`

---

## Knowledge Brain (Non-Negotiable for Knowledge Integrity)

**Built 2026-04-05 from Garry Tan's GBrain pattern.**

**Three components:**
1. `memory/entities/` — markdown entity files (people/companies/roles/projects/sources) with enforced compiled truth + timeline separation
2. `knowledge.db` — SQLite + FTS5 query layer on top of entity files
3. `scripts/knowledge-brain.py` — CLI for all brain operations

**Core principle: above-line / below-line**
- **Above the `---`** (compiled_truth): Always current. Rewritten when new info arrives. State, context, open threads.
- **Below the `---`** (timeline): Append-only. Never rewritten. Evidence base.

**Commands:**
```bash
python3 scripts/knowledge-brain.py init              # create brain.db
python3 scripts/knowledge-brain.py import            # import memory/entities/ → brain.db
python3 scripts/knowledge-brain.py search 'query'   # FTS5 full-text search
python3 scripts/knowledge-brain.py query 'question'  # ranked semantic search
python3 scripts/knowledge-brain.py get --slug people/lee-abrahams
python3 scripts/knowledge-brain.py list             # all entities
python3 scripts/knowledge-brain.py maintain         # lint + stale alerts
python3 scripts/knowledge-brain.py stats            # brain statistics
```

**Cron:** Daily 8 AM Cairo Sun-Thu (system crontab entry)
**Skill:** `skills/knowledge-brain/SKILL.md`

**Growth rule: Every significant interaction with a person, company, or role creates an entity page.**

---

## Gateway Restart = System Crash (Non-Negotiable) <!-- dream-promoted 2026-04-02 -->

**Confirmed 2026-04-02: Gateway restarts cause system instability/crashes on this VPS.**

- NEVER suggest `openclaw gateway stop`, `openclaw gateway restart`, or any variant as a troubleshooting step
- Treat the gateway as crash-prone in this environment
- If restart is genuinely needed, get explicit Ahmed approval first with full context of crash risk
- Note: `exec-approvals.json` is locked (upstream OpenClaw bug 2026.4.1) — cannot be modified until patch ships
- Safe diagnostic alternatives: check logs, restart individual scripts, use `process` tool to inspect sessions

---

## openclaw.json Config Edit Safety Rules (Non-Negotiable) <!-- dream-promoted 2026-04-02 -->

**Config corruption happened on 2026-03-27 (set wrong binding types, two stacked errors). These rules are permanent.**

1. NEVER modify `~/.openclaw/openclaw.json` without running `openclaw config validate` immediately after. If validation fails, do NOT restart.
2. NEVER bulk-overwrite fields across all bindings without understanding each binding's schema variant (AcpBindingSchema vs RouteBindingSchema have different required fields).
3. Always backup before editing: `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak.$(date +%s)`
4. Keep the file locked (`chattr +i`) at all times. Only: unlock → edit → validate → re-lock.
5. Don't trust Zod union error messages at face value - inspect the schema source when stuck.

---

## Heredoc Syntax Permanently Blocked (Non-Negotiable) <!-- dream-promoted 2026-04-03 -->

**Heredoc syntax (`<<EOF`, `<<'EOF'`, `<< 'SCRIPT'`) is permanently blocked by the gateway security scanner. Hardcoded in OpenClaw 2026.4.1 - no config change will unblock it.**

All agents notified 2026-04-02. Never use heredocs in any exec command.

**Alternatives (use these instead):**
1. Write files with the Write/Edit file tools directly (preferred)
2. `node -e "require('fs').writeFileSync('file.txt', 'content')"` for short content
3. `echo "line1" > file.txt && echo "line2" >> file.txt` for simple appends
4. Write a .py/.sh file via the Write tool first, then exec it separately

**Applies to:** All agents, all sessions, permanent.

---

## OpenClaw Cron CLI Gotchas (Non-Negotiable) <!-- dream-promoted 2026-04-03 -->

**Confirmed 2026-04-03: `openclaw cron add` CLI has no working subcommand syntax.**
- All variations fail: `--schedule`, `--schedule "expr"`, `--command`, `--cmd`, positional args
- `openclaw cron list` crashes the gateway — do NOT run it
- **Cron entries are stored in the gateway internal DB, NOT in `openclaw.json`**
- The `cron` key in openclaw.json is `{"enabled": true}` only — NOT an array of jobs

**Workarounds (in preference order):**
1. Use the `cron` tool in OpenClaw (gateway-native, does NOT require CLI)
2. Use system crontab (`crontab -e`) for one-shot or emergency schedules
3. Never try to parse/edit openclaw.json for cron entries — they don't live there

**Exec Security Config (Active as of 2026-04-03):**
- `ask=off`, `security=allowlist`, `strictInlineEval=false`, `safeBins=46`
- Config file locked with `chattr +i` — must unlock before any edit
- Source of truth: `~/.openclaw/openclaw.json`

---

## Workspace Bootstrap Bug (Known — Awaiting OpenClaw Fix) <!-- dream-promoted 2026-04-07 -->

`SELF_IMPROVEMENT_REMINDER.md` is being injected 30 times per session into the system prompt via a workspace file glob/dedup bug in the injection logic. Wastes ~5K tokens per session. Fix requires OpenClaw upstream patch — no local workaround available. Tagged for awareness in token budgets.

## Quick References

### Skill Activation
- Built-in: Just reference by name
- Custom: "Use the [skill-name] skill to help me with..."
- Always read the skill file when invoked

### Memory Search
- Use `memory_search` before answering questions about past work
- Check both MEMORY.md and memory/*.md files
- Include source citations when helpful
