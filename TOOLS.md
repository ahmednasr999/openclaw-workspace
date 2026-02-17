# TOOLS.md - Technical Configs & How-To

*Technical configurations, troubleshooting, and environment-specific setup*

## CV Creation Workflow

### Models by Task
- **Default/Daily:** MiniMax-M2.1 (free tier)
- **CV Creation:** Claude Opus 4.5 (requires approval)
- **Analysis/Research:** Claude Sonnet 4

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

### GOG (Gmail/Calendar)
- **Status:** Setup attempted, OAuth crashing
- **Workaround:** Manual Gmail cleanup instructions
- **Issue:** Keyring password conflicts
- **Alt approach:** Use web interface + guided instructions

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
