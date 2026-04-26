---
name: x-intelligence-crawler
summary: Cron skill for the weekly X Intelligence Crawler, including Ahmed-Mac browser preflight and Notion save behavior.
description: Use this when running or migrating the X Intelligence Crawler weekly cron. It preserves the existing enabled workflow while moving the operational prompt out of cron payload storage.
---

# X Intelligence Crawler

Run the weekly X Intelligence Crawler safely. This skill is the standing-order source for the `X Intelligence Crawler - Weekly` cron job.

## Purpose

Search X through the Ahmed-Mac Chrome browser and save high-engagement posts into the Notion RSS Intelligence database:

```text
32e8d599-a162-8180-9e3a-fbfc17a84e49
```

The implementation source is:

```text
/root/.openclaw/workspace/scripts/x-intelligence-crawler.py
```

## Non-negotiable rules

- Work from `/root/.openclaw/workspace`.
- Use the script as the control path. Do not reimplement scraping in the cron prompt.
- Do not use the retired `/api/browser` path.
- Do not run against a fallback browser if Ahmed-Mac Chrome is unavailable.
- Fail fast on node/browser preflight and report the preflight failure concisely.
- Do not print or expose the Notion token from `config/notion.json`.
- Save at most the top 3 new posts per category.
- Skip duplicates using the crawler state file.
- Report total saved and any errors to Ahmed in topic 10 through the cron delivery path.

## Categories

The crawler covers these categories:

1. Digital Transformation
2. Strategy
3. Healthcare
4. HealthTech
5. FinTech
6. PMO
7. Operation Excellence
8. AI

The exact query definitions live in `SEARCHES` inside `scripts/x-intelligence-crawler.py`.

## Workflow

1. Run preflight only:

   ```bash
   cd /root/.openclaw/workspace && python3 scripts/x-intelligence-crawler.py --preflight-only
   ```

2. If preflight exits non-zero, stop. Report that Ahmed-Mac and Chrome browser access are required.
3. If preflight passes, run the crawler:

   ```bash
   cd /root/.openclaw/workspace && python3 scripts/x-intelligence-crawler.py
   ```

4. Summarize the script result:
   - total posts collected
   - total saved to Notion
   - error count and short error details, if any
   - whether duplicate skipping occurred implicitly through the state file

## Optional verification commands

For file-only checks or maintenance, prefer non-live checks:

```bash
cd /root/.openclaw/workspace && python3 -m py_compile scripts/x-intelligence-crawler.py
```

Only use live smoke checks when explicitly authorized because they touch the browser and/or Notion paths:

```bash
cd /root/.openclaw/workspace && python3 scripts/x-intelligence-crawler.py --preflight-only
cd /root/.openclaw/workspace && python3 scripts/x-intelligence-crawler.py --dry-run --smoke-category AI
```

## Suggested slim cron prompt

Do not apply this from inside the skill. A future gateway edit can replace the large inline prompt with:

```text
Use the X Intelligence Crawler cron skill at `/root/.openclaw/workspace/skills/cron/x-intelligence-crawler/SKILL.md`. Execute the weekly crawl for this run.
```
