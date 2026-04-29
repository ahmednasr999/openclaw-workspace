# Active Tasks

## 2026-04-28 - Gulf jobs scanner blocked by Exa credits
- Priority: high
- Status: blocked on search provider credits/access
- Context: `jobs-bank/scraped/qualified-jobs-2026-04-28.md` reported 0 jobs, 0 picks/leads, and 56/56 failed searches.
- Verification: a direct `EXA_SEARCH` call through Composio failed with HTTP 402 `NO_MORE_CREDITS`: "You have exceeded your credits limit. Please top up to keep using Exa at dashboard.exa.ai".
- Impact: LinkedIn/Gulf jobs scanner v4.0 depends on external search. Regular daily output is unreliable while Exa credits are exhausted and fallback search is challenged/rate-limited.
- 2026-04-28 heartbeat progress: added a credit-safe fallback in `scripts/linkedin-gulf-jobs.py` using `openclaw infer web search --provider duckduckgo --json`. Exa/LinkedIn searches now retry through the fallback when they return no jobs, the scanner can continue fallback-only if Composio/MCP is unavailable, and it circuit-breaks Composio/Exa calls after detecting a 402/`NO_MORE_CREDITS` response. Verified with `python3 -m py_compile`, direct fallback function calls returning Riyadh CTO results, and a targeted circuit-breaker assertion.
- 2026-04-29 heartbeat verification: reran `python3 scripts/linkedin-gulf-jobs.py`. Exa still returns 402. DuckDuckGo fallback is now returning bot-detection/403 challenges, and Tavily CLI testing hits pay-as-you-go limit 433. Patched the scanner so `pipeline_db` import works, fallback search circuit-breaks after repeated provider failures, metadata marks high-error runs as `degraded`, and fallback diagnostics are written to `scanner-meta-YYYY-MM-DD.json`. Latest verified run completed in 47s with 0 jobs, 56/56 failed searches, and `fallback_circuit_open: true`.
- 2026-04-29 later heartbeat: a single DuckDuckGo CLI probe worked, but a full scanner rerun still hit Exa 402 and DuckDuckGo bot-detection after the first fallback batch. It produced 54/56 failed searches and noisy VP false positives (JD Vance/social/Wikipedia/VP Racing). Patched `scripts/linkedin-gulf-jobs.py` to reject non-job source domains, generic job-index pages, and false bare-`VP` matches before they become leads. Also moved validation before Slack delivery and changed degraded runs to send only a degraded alert rather than a Slack lead list. Verified with `python3 -m py_compile` and helper tests against the noisy raw results.
- 2026-04-29 19:02 Cairo heartbeat check: probed the first-class `web_search` tool directly for a Gulf CTO LinkedIn query. It failed with `missing_brave_api_key`, confirming Brave is not configured in Gateway yet. This leaves Exa 402, Tavily quota/pay-go, DuckDuckGo bot detection, and Brave missing-key as the current provider blockers; no full scanner rerun attempted.
- Next steps:
  1. restore/top up Exa credits, or configure a working Brave/Tavily search key/quota for OpenClaw CLI fallback,
  2. after provider access is restored, rerun `PYTHONUNBUFFERED=1 python3 scripts/linkedin-gulf-jobs.py` and verify `scanner-meta-YYYY-MM-DD.json` has low errors and `degraded: false`.

## 2026-04-17 - JobZoom scorer reliability check
- Priority: medium
- Status: mitigated, needs next live-run verification
- Context: ad hoc pass2 scoring of today's reconstructed 60-job pass1 pool initially appeared hung around batch 1/6 before later completing. This could silently suppress surfaced jobs if the same behavior happens in the live daily run.
- Immediate evidence:
  - delayed/no visible output for an extended period at batch 1/6
  - later completion with all 6 batches scored and 6 jobs >=70
- Risk: intermittent stall, gateway/API latency, or weak batch-run observability could cause missed surfaced jobs or misleading operator reads.
- 2026-04-29 heartbeat progress: inspected the latest live cron run in `/root/.openclaw/workspace-jobzoom/data/jobzoom.db`. The 2026-04-29 run completed successfully: 150/150 searches, 70 pass1 jobs, 7 pass2 matches, 7/7 batch-scoring calls succeeded. Batch call timestamps were steady at about 41-44 seconds apart, so no live scoring stall was visible today. Added timing instrumentation to `/root/.openclaw/workspace-jobzoom/scripts/daily_run.py`: gateway calls now record `elapsed_ms` in `gpt_api_calls.note`; batch scoring logs attempt start, timeout budget, per-attempt duration, total batch duration, scores, and keyword-fallback duration. Verified with `python3 -m py_compile`.
- 2026-04-29 13:03 Cairo heartbeat check: re-queried the live DB with the actual schema. Run 24 completed at 05:28 with 150/150 successful searches, 70 pass1 jobs, and 7 pass2 matches. The pre-scoring `scoring_health_check` timed out once at 05:20, but all 7 `batch_scoring` calls succeeded afterward, so this is diagnostic noise rather than evidence of a live scoring stall. Current pending code changes already make batch-scoring outcome the source of truth for AI health.
- Next steps:
  1. after the next 05:00 Cairo JobZoom cron, inspect `gpt_api_calls.note` for `elapsed_ms` and confirm batch logs show clear start/end timings,
  2. if any batch exceeds the 180s timeout or falls back, surface it as a real warning.

## 2026-04-17 - JobZoom scraper path drift guard
- Priority: low
- Status: resolved, monitor only
- Context: `workspace-jobzoom/scripts/daily_run.py` calls `/root/.openclaw/workspace/scripts/jobs-source-linkedin-jobspy.py` instead of a separate JobZoom-local copy.
- 2026-04-29 heartbeat verification: `/root/.openclaw/workspace-jobzoom/scripts/jobs-source-linkedin-jobspy.py` is a symlink to `/root/.openclaw/workspace/scripts/jobs-source-linkedin-jobspy.py`, so there is no separate local copy to drift. `daily_run.py` also calls `preflight_jobspy_path()` before scraping and verifies the expected script path, realpath, venv Python, and `jobspy` import. Current state is therefore guarded.
- Residual note: if future work wants JobZoom to be isolated from the main workspace scraper, create a true local copy and update `JOBSPY_SCRIPT`/`JOBSPY_EXPECTED_SCRIPT` together. Until then, treat the shared symlink as intentional.
