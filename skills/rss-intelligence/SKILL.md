# RSS Intelligence Skill

## What it does
Weekly crawler that fetches curated RSS/Atom feeds, deduplicates articles, saves them to Notion, generates a ranked content brief, creates the strongest Content Calendar ideas, and sends a compact Telegram summary.

## System Components

### Config
`/root/.openclaw/workspace/config/rss-intelligence.json`

### Crawler Script
`/root/.openclaw/workspace/scripts/rss-intelligence-crawler.py`

### State File
`/root/.openclaw/workspace/data/rss-intelligence-state.json` — tracks seen URLs for deduplication

### Notion Database
`32e8d599-a162-8180-9e3a-fbfc17a84e49` — RSS Intelligence DB (under Content Factory page)
Properties: Name (title), Category (multi-select: 8 options), Source (rich_text), URL (url), Published (date), Summary (rich_text), Status (select: New/Read/Archived)

## Confirmed Feeds (8 categories, 8 sources)

| Category | Feed URL | Items Verified |
|----------|----------|---------------|
| FinTech | https://connectingthedotsinfin.tech/rss/ | 15 |
| Healthcare | https://www.healthcareittoday.com/feed/ | 10 |
| HealthTech | https://www.digitalhealth.net/news/feed/ | 10 |
| Digital Transformation | https://sloanreview.mit.edu/tag/digital-transformation/feed/ | 20 |
| Strategy | https://fs.blog/feed/ | 20 |
| PMO | https://pmo.zalando.com/atom.xml | 46 |
| Operation Excellence | https://www.leanblog.org/feed/ | 8 |
| AI | https://venturebeat.com/category/ai/feed/ | 7 |

## Run manually
```bash
python3 /root/.openclaw/workspace/scripts/rss-intelligence-crawler.py
# Backfill recent RSS archive into a content brief without waiting for new feed items:
python3 /root/.openclaw/workspace/scripts/rss-intelligence-crawler.py --rescore-recent 50
```

## Cron
ID: `d93228ad-b2b2-4c17-b1b5-210f87df9608`
Schedule: Friday 13:00 Cairo
Check status: `openclaw cron list | grep RSS`

## Add new feed
1. Find RSS/Atom URL
2. Verify it parses:
```python
import urllib.request, ssl, xml.etree.ElementTree as ET
ctx = ssl.create_default_context()
req = urllib.request.Request('URL', headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
    root = ET.fromstring(r.read())
items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
print(len(items), 'items')
```
3. Add to `/root/.openclaw/workspace/config/rss-intelligence.json` → `feeds` dict
4. Done — next cron run will pick it up

## Key Implementation Notes
- Notion API token: `~/.openclaw/workspace/config/notion.json` — use direct API, NOT Composio
- HealthTech moved from MobiHealthNews to Digital Health on 2026-06-05 because MobiHealthNews returns HTTP 403 from the VPS.
- Deduplication: URL-based, stored in state file (last 50k URLs)
- Telegram: skips if 0 new feed articles; backfill can still create local/Notion content ideas.
- Content outputs: `data/rss-content-brief-latest.md`, dated brief, and `data/rss-content-candidates-latest.json`.
- Content Calendar: creates up to three `Idea` rows per run, favoring distinct content angles and tracking duplicate source URLs in state.
- PMO feed (Zalando) uses Atom format — handled by parser
- Parse errors: try ET.fromstring with namespace fix; if still fails, try regex stripping of broken namespace declarations
