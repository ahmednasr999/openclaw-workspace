# Service Registry - Single Source of Truth

**RULE (NON-NEGOTIABLE): Before calling Composio, before asking the user to authenticate, before saying "I can't access X" -- READ THIS FILE.**

Last updated: 2026-03-21

---

## How to Use This File

1. User asks to do something with an external service
2. Check this file: is the service listed?
3. If YES: use the method listed here. Period.
4. If NO: check `config/` directory for credentials/tokens, then Composio, then ask user.
5. **NEVER ask the user to re-authenticate a service that's already listed here as ACTIVE.**

## When Adding New Tools/Services

Any time a new integration is set up (new API key, new Composio connection, new CLI tool, new skill), ADD IT HERE. This file must stay current.

---

## External Services

### Notion
- **Method:** Direct API
- **Token:** `config/notion.json`
- **Client:** `scripts/notion_client.py` (import NotionClient)
- **Databases:** `config/notion-databases.json`
- **Status:** ACTIVE

### LinkedIn (Posting)
- **Method:** Composio
- **Tool:** `LINKEDIN_CREATE_LINKED_IN_POST`
- **Person URN:** `urn:li:person:mm8EyA56mj`
- **Status:** ACTIVE

### LinkedIn (Browser Automation - Profile, Messaging, Scraping)
- **Method:** Cookies + Camoufox browser
- **Cookies:** `config/nasr-linkedin-cookies.txt` (Netscape format)
- **Alt cookies:** `config/linkedin-cookies.json`
- **Skill:** `skills/linkedin/SKILL.md`
- **Status:** ACTIVE

### Gmail
- **Method:** Himalaya CLI (IMAP/SMTP)
- **Config:** `/root/.config/gmail-smtp.json`
- **CLI:** `himalaya`
- **Skill:** `skills/himalaya/SKILL.md`
- **Status:** ACTIVE

### Google Calendar
- **Method:** Composio
- **Skill:** `skills/gog-calendar/`
- **Status:** ACTIVE

### GitHub
- **Method:** `gh` CLI (authenticated)
- **Account:** ahmednasr999
- **CLI:** `gh`
- **Skill:** `skills/github/SKILL.md`
- **Status:** ACTIVE

### Web Search (Exa)
- **Method:** Composio
- **Status:** ACTIVE

### Web Search (Tavily)
- **Method:** Direct API key
- **Config:** `config/tavily.json`
- **Skill:** `skills/tavily-search/SKILL.md`
- **Status:** ACTIVE

### X/Twitter (Scraping)
- **Method:** Cookies + Camoufox browser
- **Cookies:** `config/x-cookies.txt`
- **Status:** ACTIVE

### YouTube (Scraping/Transcripts)
- **Method:** Cookies + yt-dlp
- **Cookies:** `config/youtube-cookies.txt`
- **Skill:** `skills/youtube-transcript/`
- **Status:** ACTIVE

---

## Internal Tools & CLIs

### Brave Search
- **Method:** OpenClaw built-in `web_search` tool
- **Status:** ACTIVE

### PDF Analysis
- **Method:** Built-in `pdf` tool
- **Status:** ACTIVE

### Image Analysis
- **Method:** Built-in `image` tool
- **Status:** ACTIVE

### Browser Automation
- **Method:** Camoufox (preferred) or built-in `browser` tool
- **Status:** ACTIVE

---

## Config Files Reference

| File | Purpose |
|------|---------|
| `config/notion.json` | Notion API token |
| `config/notion-databases.json` | Notion DB IDs and root page |
| `config/tavily.json` | Tavily search API key |
| `config/linkedin-cookies.json` | LinkedIn session cookies (JSON) |
| `config/nasr-linkedin-cookies.txt` | LinkedIn cookies (Netscape) |
| `config/x-cookies.txt` | X/Twitter cookies |
| `config/youtube-cookies.txt` | YouTube cookies |
| `config/model-router.json` | Model routing rules |
| `config/firehose.json` | Firehose monitoring config |
| `config/mcporter.json` | MCP server config |
| `config/linkedin-comment-targets.json` | LinkedIn comment engagement targets |
| `/root/.config/gmail-smtp.json` | Gmail IMAP/SMTP credentials |
| `/root/.config/gh/hosts.yml` | GitHub CLI auth |
| `/root/.config/gog/config.json` | Google Workspace CLI auth |

---

## Skills Reference

| Skill | External Service | Connection Method |
|-------|-----------------|-------------------|
| `himalaya` | Gmail | CLI + app password |
| `linkedin` | LinkedIn | Cookies + browser |
| `linkedin-writer` | LinkedIn | Composio (posting) |
| `linkedin-comment-radar` | LinkedIn | Cookies + browser |
| `github` | GitHub | `gh` CLI |
| `tavily-search` | Tavily | Direct API key |
| `gog-calendar` | Google Calendar | Composio |
| `google-analytics` | Google Analytics | OAuth (managed) |
| `crawlee` | Web scraping | Direct (no auth) |
| `hubspot` | HubSpot | API key (if configured) |
| `todoist` | Todoist | API key (if configured) |
| `job-search-mcp` | JobSpy | MCP server |
| `executive-cv-builder` | Local only | No external service |
| `slides` | Local only | No external service |
| `spreadsheet` | Local only | No external service |
| `doc` | Local only | No external service |
| `diagram-generator` | Local only | No external service |
| `transcribe` | Local only | No external service |

---

## Cron Scripts & Their Dependencies

| Cron Script | External Services Used | Connection Method |
|-------------|----------------------|-------------------|
| `run-briefing-pipeline.sh` | Notion, web search | Direct API, Tavily/Exa |
| `linkedin-auto-poster.py` | LinkedIn, Notion | Composio (post), Direct API (Notion) |
| `linkedin-engagement-collector.py` | LinkedIn | Cookies + browser |
| `linkedin-autoresearch.py` | LinkedIn | Cookies + browser |
| `github-radar.sh` | GitHub | `gh` CLI |
| `x-radar.sh` | X/Twitter | Cookies + browser |
| `jobs-source-*.py` | Various job boards | Direct scraping |
| `daily-backup.sh` | Local only | No external service |
| `cron-watchdog-v3.sh` | Local only | No external service |
| `auto-lessons-learned.py` | Local only | No external service |
| `sie-360-checks.py` | Notion | Direct API |

---

## Decision Tree: How to Connect

```
Need to use a service?
  |
  +--> Is it in this file? 
  |      YES --> Use the method listed. Done.
  |      NO  --> Continue below.
  |
  +--> Check config/ directory for tokens/keys
  |      FOUND --> Use it. Add to this file.
  |      NOT FOUND --> Continue below.
  |
  +--> Check if Composio has an active connection
  |      ACTIVE --> Use Composio. Add to this file.
  |      NOT ACTIVE --> Continue below.
  |
  +--> NOW (and only now) ask the user.
```
