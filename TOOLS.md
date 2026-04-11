# TOOLS.md - Technical Configs & How-To

Quick technical reference. Full detail moved to `docs/reference/TOOLS.full.md`.

## Search and scraping
### LinkedIn job scraping
- Always use JobSpy with `linkedin_fetch_description=True`
- Script: `scripts/jobs-source-linkedin-jobspy.py`
- Never use Selenium/Playwright or authenticated scraping for LinkedIn job search

### Web search sources
- Exa: available via Composio for research-grade search
- Tavily: direct API key in `config/tavily.json`, primary search path
- SearXNG: self-hosted at `http://127.0.0.1:8090`, compose files in `services/searxng/`
- Search router: `skills/tavily-search/scripts/search.mjs` loads `config/tavily.json` automatically and falls back to local SearXNG on Tavily failure
- Research router: `skills/tavily-search/scripts/research-search.mjs` uses the local Composio config for Exa-style research search, with search-web fallback if the direct Exa path is unavailable
- Brave: not configured here, do not assume availability or plan around it
- Scraping order: `web_fetch` first, `crawlee` second, `skills/scrapling/` only for brittle or hostile public scraping, browser tools for login/click flows
- Scrapling pilot wrapper: `skills/scrapling/scripts/scrape.sh`
- Crawlee escalation helper: `skills/crawlee/scripts/scrape-or-escalate.sh` suggests Scrapling on JS walls, anti-bot pages, or tiny partial output

## LinkedIn engagement and posting
### Daily comments job
- Source must be Ahmed-Mac Chrome live feed
- Never fall back to Exa
- If Ahmed-Mac is offline, skip the day

### Posting
- Post tool: `LINKEDIN_CREATE_LINKED_IN_POST`
- Person URN: `urn:li:person:mm8EyA56mj`
- For image posts, upload image first and use returned `s3key`
- Never post text-only if image was expected

### Content calendar
- Notion DB: `3268d599-a162-814b-8854-c9b8bde62468`
- Auto-poster script: `scripts/linkedin-auto-poster.py`

## Model policy
- Primary model: GPT-5.4 via OpenAI Codex OAuth
- Fallback: MiniMax-M2.7
- Ahmed explicit model choices must never be silently reverted
- Disclose any model switch immediately
- Model Guardian also watches weekly GPT-5.4 quota and logs snapshots to `data/model-guardian-usage.jsonl` <!-- dream-promoted 2026-04-09 -->
- Alert thresholds: below 30% weekly quota → CEO General topic 10, below 15% → urgent alert with recommendation to temporarily switch Think to medium <!-- dream-promoted 2026-04-09 -->

## CV workflow
- Source of truth: `memory/master-cv-data.md`
- ATS rules: `memory/ats-best-practices.md`
- Filename format: `Ahmed Nasr - {Title} - {Company}.pdf`
- Never fabricate roles, titles, or achievements

## Credentials and integrations
- Notion: `config/notion.json`
- Tavily: `config/tavily.json`
- Gmail: `/root/.config/gmail-smtp.json`
- GitHub: `/root/.config/gh/hosts.yml`
- HuggingFace: `config/huggingface.json`
- LinkedIn browser cookies: `config/nasr-linkedin-cookies.txt`

## Browser automation
- Always use Ahmed-Mac Chrome first for browser tasks requiring login
- Avoid server-side browser fallback when account session matters

## Gateway safety
- Gateway restart is crash-prone here, never do it casually
- Do not edit `openclaw.json` blindly
- Validate config after config edits
- Cron jobs live in gateway DB, not `openclaw.json`
- Heredoc syntax is blocked by gateway security scanner

## Known operational gotchas
- `AGENTS.md` and `TOOLS.md` are bootstrap-sensitive, keep concise
- qmd duplicate collection warnings mean existing collection already covers the path
- Composio sandbox cannot reach VPS-local IPs for image fetches
- `openclaw` CLI messaging uses `--target`, not `--to`

## Key references
- Full TOOLS reference: `docs/reference/TOOLS.full.md`
- Service registry: `config/service-registry.md`
- Memory rules: `MEMORY.md`
- Workspace docs: `docs/`
