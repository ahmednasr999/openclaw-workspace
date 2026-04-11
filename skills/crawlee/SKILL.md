---
name: "crawlee"
description: "Scrape any website with full data extraction, structured output, and no setup needed. Use when asked to scrape a URL, extract data from a webpage, crawl a site, or get structured content from any link. Triggers on 'scrape this', 'extract from', 'crawl site', 'get data from URL', 'what's on this page'. NOT for: simple page reads (use web_fetch), browser automation with clicks/forms (use browser tools), or API calls."
---

# Crawlee - Web Scraper Skill

Scrape any website. Full data extraction, structured output, no setup needed.

## Workflow

1. **Identify the target:** URL(s) to scrape and what data the user wants.
2. **Choose the approach:**
   - Single page content → `--depth 0 --max 1` (default)
   - Specific elements → use `--selector` with CSS selector
   - Multi-page crawl → set `--depth` and `--max`
   - Link extraction → add `--links`
3. **Run the scraper:**
   ```bash
   node ~/.openclaw/workspace/skills/crawlee/scripts/scrape.mjs <url> [options]
   ```
   For unknown or brittle targets, prefer the helper wrapper:
   ```bash
   bash ~/.openclaw/workspace/skills/crawlee/scripts/scrape-or-escalate.sh <url> [options]
   ```
   Or auto-run the fallback when needed:
   ```bash
   bash ~/.openclaw/workspace/skills/crawlee/scripts/scrape-or-escalate.sh --auto <url> [options]
   ```
4. **Process results:** Parse output, summarize, or save to file.

## CLI Reference

```
node scrape.mjs <url> [options]

Options:
  --depth N        Max crawl depth (default: 0 = single page)
  --max N          Max pages to crawl (default: 1)
  --selector CSS   CSS selector to extract specific elements
  --output FILE    Save results to file
  --format FMT     json | text | markdown (default: markdown)
  --links          Also extract all links
  --headers        Include HTTP response headers
  --glob PATTERN   Only follow links matching glob
  --exclude PAT    Exclude links matching pattern
```

## Common Patterns

### Scrape a single page
```bash
node scrape.mjs https://example.com
```

### Extract specific elements (e.g., headlines)
```bash
node scrape.mjs https://news.ycombinator.com --selector ".titleline > a" --format json
```

### Crawl a site (depth 2, max 20 pages)
```bash
node scrape.mjs https://example.com --depth 2 --max 20 --format json --output site-data.json
```

### Get all links from a page
```bash
node scrape.mjs https://example.com --links --format json
```

### Scrape multiple pages matching a pattern
```bash
node scrape.mjs https://blog.example.com --depth 3 --max 50 --glob "*/blog/*" --format markdown
```

## Decision Rules

- **Simple page read** (no extraction needed) → use `web_fetch` instead (lighter)
- **Need JavaScript rendering** → first decide if Scrapling `fetch` is enough, use browser tools only when real interaction or login is required
- **Structured data extraction** → use `--selector` with CSS selectors
- **Full site crawl** → set `--depth` and `--max` appropriately
- **Large outputs** → always use `--output` to save to file
- **Unknown or likely-hostile public target** → start with `scrape-or-escalate.sh` so JS walls and anti-bot pages suggest Scrapling automatically

## Output Formats

- **markdown** (default): Clean readable format with headings and links
- **json**: Structured data with url, title, text, headings, paragraphs, elements
- **text**: Plain text, minimal formatting

## Dependencies

Installed in `skills/crawlee/scripts/node_modules/`:
- `crawlee` - Core scraping framework
- `cheerio` - HTML parsing

## Limitations

- HTTP-only for the core `scrape.mjs` path. If the page is JS-heavy but still public, escalate to `skills/scrapling/` before jumping to full browser automation.
- Respects robots.txt by default.
- Max recommended: ~100 pages per crawl to avoid timeouts.

## Escalation helper
Use:
```bash
bash ~/.openclaw/workspace/skills/crawlee/scripts/scrape-or-escalate.sh <url> [options]
```
It runs Crawlee first, then warns when the output looks like a JS wall, anti-bot page, tiny partial page, or hard failure.

Flags:
- `--suggest-only` - print the fallback suggestion only
- `--auto` - execute the suggested Scrapling fallback automatically

Environment fallback:
- `SCRAPLING_AUTO_RUN=1` still works, but prefer the explicit flags for normal use.
