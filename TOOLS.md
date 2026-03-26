# TOOLS.md - Technical Configs & How-To

*Technical configurations, troubleshooting, and environment-specific setup*

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
| **Anthropic** | `haiku` | claude-haiku-4-5 | Fast, cheap tasks | 💚 Budget | ✅ Works |
| **Anthropic** | `haiku-3.5` | claude-3-5-haiku-20250520 | Legacy | ❌ 404 Error |
| **Anthropic** | `haiku-3` | claude-3-haiku-20240307 | Legacy | ❓ Untested |

### Model Selection Rules
1. **Default:** MiniMax-M2.7 (free, good for routine tasks)
2. **CV Creation:** Claude Opus 4.6 (requires approval)
3. **Complex Setup:** Claude Sonnet 4.6
4. **Content Drafting:** Claude Sonnet 4.6
5. **Alternative Reasoning:** Kimi K2.5

### Model Change Protocol
- **Default:** MiniMax M2.7 (always)
- **Ask before changing:** Any model switch
- **Notify:** When switching to/from paid models
- **Switch back:** After completing expensive tasks

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

## Quick References

### Skill Activation
- Built-in: Just reference by name
- Custom: "Use the [skill-name] skill to help me with..."
- Always read the skill file when invoked

### Memory Search
- Use `memory_search` before answering questions about past work
- Check both MEMORY.md and memory/*.md files
- Include source citations when helpful
