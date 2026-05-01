# JobZoom cron timeout adjustment - 2026-05-01

## Reason

The 2026-05-01 JobZoom run completed scraping, scoring, CV generation, and report creation, but the isolated cron agent timed out at the end before delivery completed.

Evidence:

- Run row: 150/150 searches, 354 eligible jobs, 275 after dedup, 64 after Pass 1, 4 final matches, 4 CVs generated.
- Report exists: `/root/.openclaw/workspace-jobzoom/reports/JobZoom_Daily_2026-05-01.pdf`.
- Gateway log around 05:39:59 showed embedded run timeout for the JobZoom isolated run.
- `report_delivered` remained `0`, and no CV ZIP was created.

## Change made

Updated cron job:

- Job name: `JobZoom Daily Scan`
- Job id: `2a6d6e4f-0ea6-4836-935d-e4bc1fa8c2e3`
- Schedule: `0 5 * * *`, timezone `Africa/Cairo`
- Session target: `isolated`

Payload timeout changed to:

```json
"timeoutSeconds": 7200
```

This gives the run up to 2 hours, enough headroom for scraping, scoring, CV generation, report generation, zip creation, and Telegram delivery.

## Scope discipline

No JobZoom code, prompt, scan scope, thresholds, or protected lane logic was changed.

## Residual state

The 2026-05-01 run artifacts were generated but not delivered by the original cron run. This timeout adjustment protects future runs. Manual delivery of today's artifacts remains a separate action if needed.
