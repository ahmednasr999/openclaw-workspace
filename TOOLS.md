# TOOLS.md - Technical Configs & How-To

*Technical configurations, troubleshooting, and environment-specific setup*

## CV Creation Workflow

### Models by Task
- **Default/Daily:** MiniMax-M2.1 (free tier)
- **CV Creation:** Claude Opus 4.5 (requires approval)
- **Analysis/Research:** Claude Sonnet 4

## Model Strategy (Verified Working - 2026-02-17)

### Available Models (Tested & Confirmed)

| Provider | Alias | Model | Use Case | Cost | Status |
|----------|-------|-------|----------|------|--------|
| **Anthropic** | `opus` | claude-opus-4-6 | Complex tasks, CV creation | 💎 Premium | ✅ Works |
| **Anthropic** | `sonnet` | claude-sonnet-4-6 | Balanced (troubleshooting, setup) | ⚡ Mid | ✅ Works |
| **Anthropic** | `opus-4.5` | claude-opus-4-5 | Legacy fallback | 💎 Premium | ✅ Works |
| **Anthropic** | `sonnet-4` | claude-sonnet-4 | Legacy fallback | ⚡ Mid | ✅ Works |
| **MiniMax** | `minimax-m2.1` | MiniMax-M2.1 | Daily tasks, bulk operations | ✅ Free | ✅ Works |
| **Moonshot** | `Kimi` | kimi-k2.5 | Alternative reasoning, research | ⚡ Mid | ✅ Works |

### Not Working (Do Not Use)

| Provider | Alias | Model | Issue |
|----------|-------|-------|-------|
| **Anthropic** | `haiku-3.5` | claude-3-5-haiku-20250520 | ❌ 404 Error |
| **Anthropic** | `haiku-3` | claude-3-haiku-20240307 | ❓ Untested |

### Model Selection Rules
1. **Default:** MiniMax-M2.1 (free, good for routine tasks)
2. **CV Creation:** Claude Opus 4.5 (always ask first)
3. **Complex Setup:** Claude Sonnet 4
4. **Alternative Reasoning:** Kimi K2.5

### Switching Models
- Use alias: `switch to opus`, `switch to sonnet`, `switch to Kimi`
- Always notify user when switching to paid models
- Switch back to MiniMax after completing expensive tasks

### File Naming Convention
- Format: `Ahmed Nasr - {Title} - {Company}.pdf/html`
- No underscores, use spaces and dashes
- If company confidential: `Ahmed Nasr - {Title}.pdf`

### ATS Compliance Checklist
- Single column layout only
- No tables, multi-column, images, special bullets
- Standard headers: Professional Summary, Experience, Education, Skills, Certifications
- AVR bullet pattern: Action + Value + Result

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

### File Naming Issues
- Check MEMORY.md for filename rules
- Master CV data has exact titles and dates
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
