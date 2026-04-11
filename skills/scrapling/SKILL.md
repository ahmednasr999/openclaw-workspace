---
name: scrapling
description: Use this skill for harder scraping jobs when `web_fetch` is too light and the `crawlee` skill is likely to be brittle or insufficient. Trigger on requests to scrape hostile sites, JS-heavy pages without login, selector drift, recurring extraction from changing layouts, multi-page crawls that need stronger session handling, or when simpler scraping already failed. Do NOT use for simple page reads, logged-in browser flows, or LinkedIn job scraping.
---

# Scrapling

Tier-3 specialist scraper. Use it when the normal stack is not enough.

## Routing
Read `references/routing.md` before using this skill.

Default order:
1. `web_fetch` for simple page reads
2. `crawlee` for normal static structured crawls
3. `scrapling` for brittle, hostile, or session-heavy scraping
4. Browser tools for login, clicks, forms, or account-bound flows

## Hard boundaries
- Do not use this skill for LinkedIn job scraping. Use JobSpy.
- Do not use this skill when Ahmed-Mac browser context is required.
- Do not jump to Scrapling for documentation pages or one-page reads.
- Prefer saving large outputs to files, then summarizing.

## Modes
### 1) Fast static fetch
Use when the page is public HTML and you mainly need stronger request fingerprinting.

```bash
bash skills/scrapling/scripts/scrape.sh get <url> <output-file> [css-selector]
```

### 2) Dynamic fetch
Use when the site needs browser rendering but not full manual interaction.

```bash
bash skills/scrapling/scripts/scrape.sh fetch <url> <output-file> [css-selector]
```

### 3) Stealthy fetch
Use when lighter approaches fail and the target looks anti-bot sensitive.

```bash
bash skills/scrapling/scripts/scrape.sh stealthy-fetch <url> <output-file> [css-selector]
```

## Typical workflow
1. Decide whether Scrapling is justified using `references/routing.md`.
2. Pick the lightest mode that can work.
3. Save output to `.md` or `.txt` unless raw HTML is truly needed.
4. If a selector is needed, pass it explicitly.
5. For large jobs, write to a file under `/tmp/` or the workspace, then post-process.
6. If Scrapling fails, report whether the failure is dependency, anti-bot, or target-specific. Do not pretend the site is scrapeable.

## Examples
### Public page, text capture
```bash
bash skills/scrapling/scripts/scrape.sh get https://example.com /tmp/example.txt
```

### Extract only product cards
```bash
bash skills/scrapling/scripts/scrape.sh get https://example.com/shop /tmp/products.md '.product-card'
```

### Rendered page with wait
```bash
SCRAPLING_WAIT_MS=2000 bash skills/scrapling/scripts/scrape.sh fetch https://example.com/app /tmp/app.md '.results'
```

### Harder target
```bash
SCRAPLING_WAIT_MS=3000 bash skills/scrapling/scripts/scrape.sh stealthy-fetch https://example.com/protected /tmp/protected.md '.listing'
```

## Pilot status
- Scrapling is installed in an isolated skill venv at `skills/scrapling/.venv/`.
- The wrapper prefers that venv and falls back to the host CLI only if needed.
- Pilot result: Scrapling did not beat Crawlee on easy pages or normal GitHub release pages, but `fetch` clearly beat Crawlee on a JS-heavy X post where Crawlee only returned a JS-disabled wall.
- Treat this as a pilot skill until a few real target sites have been benchmarked against Crawlee.
- Use `bash skills/scrapling/scripts/smoke-test.sh` for a quick health check before relying on it.

## Output expectations
Return:
- what mode was used
- where the output file was saved
- whether content quality beat `web_fetch` or `crawlee`
- any target-specific caveats
