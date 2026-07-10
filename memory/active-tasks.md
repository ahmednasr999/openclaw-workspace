# Active Tasks

## 2026-07-10 - JobZoom application-package quality gate shadow rollout
- Priority: high
- Status: active, historical replay passed; live streak 0/3
- Context: Ahmed approved upgrading JobZoom with the stronger validation and packaging controls from the Hermes workflow while keeping JobZoom as the single daily system.
- Implemented:
  - isolated shadow evaluator at `/root/.openclaw/workspace-jobzoom/scripts/jobzoom_quality_gate.py`
  - additive `quality_gate_runs` and `quality_gate_decisions` tables in the canonical JobZoom database
  - report, ZIP, manifest, CV text/page, applied-ledger, JD completeness, LinkedIn identity, eligibility, salary-potential, and exactly-once delivery-marker checks
  - current-state old-package suppression for roles applied after the original run
  - read-only promotion checker at `/root/.openclaw/workspace-jobzoom/scripts/jobzoom_quality_gate_acceptance.py`
  - direct OS cron at 07:15 Cairo, after the unchanged 05:00 production run
- Verification:
  - five historical runs, 5-9 July, passed; 30 decisions evaluated
  - 9 July shadow decision: 2 application-ready, 1 blocked at 82 due salary-floor evidence, 7 watchlist
  - current-state 9 July replay: 10/10 excluded as already applied, 0 ready
  - database integrity passed; jobs/applied/runs counts unchanged
  - production daily runner, launcher, and safe-runner checksums match the pre-change backup
  - clean-room restore from `/root/.openclaw/workspace-jobzoom/backups/quality-gate-20260710-031951` passed and was destroyed after verification
- Next steps:
  1. Collect three consecutive live shadow runs beginning with the 10 July 07:15 evaluation.
  2. Run `python3 scripts/jobzoom_quality_gate_acceptance.py --required 3` in the JobZoom workspace.
  3. Review current-versus-shadow decision differences before any production promotion. Do not auto-promote.

## 2026-06-17 - OpenClaw context-engineering improvement track
- Priority: high
- Status: open, first control artifacts created
- Context: Ahmed approved turning the context-engineering recommendation into an OpenClaw improvement track focused on long workflow drift, not adding more agents/tools.
- Artifacts:
  - `docs/agent-governance/context-contracts-2026-06-17.md`
  - `docs/agent-governance/long-run-context-evals-2026-06-17.md`
  - `scripts/check-context-contracts.py`
- Scope: JobZoom, CMO, email scan, and gateway maintenance contracts define required sources, allowed memory, ignored context, approval boundaries, verification gates, handoff packets, and stop rules.
- Verification: `python3 scripts/check-context-contracts.py` passed, and the new docs were checked for smart quotes/em dashes. First manual eval passed for Gateway Maintenance, report: `reports/context-evals/gateway-maintenance-2026-06-17.md`.
- Next steps:
  1. Run the next manual eval on Email Scan or JobZoom.
  2. Run one manual eval against CMO after that before automating judgment.
  3. If a contract prevents a real failure twice, promote the smallest durable rule into the owner skill, AGENTS.md, or TOOLS.md.
  4. Build only a read-only closeout checker first; do not automate decisions until manual eval evidence is stable.

## 2026-05-29 - OpenClaw ecosystem adoption execution
- Priority: high
- Status: open
- Context: Ahmed approved moving from ecosystem analysis into execution after the OpenClaw ecosystem deep-dive. Created the adoption register at `docs/architecture/openclaw-ecosystem-adoption-register-2026-05-29.md`.
- Live baseline: OpenClaw `2026.5.27 (27ae826)`, 118 skills installed, 79 visible to model, 78 command-available, 15 enabled plugins.
- Created agent skill matrix: `docs/agent-governance/openclaw-agent-skill-matrix-2026-05-29.md`.
- 2026-05-29 progress: installed `gitcrawl` and `telecrawl` to `/root/go/bin` and symlinked both into `/usr/local/bin`. `gitcrawl` pilot passed by syncing `openclaw/openclaw` PR #1 into an isolated SQLite DB under `/tmp/openclaw-crawler-pilots/gitcrawl-home`. Added reusable read-only digest script `scripts/openclaw-gitcrawl-digest.py`, verified by producing `reports/openclaw-gitcrawl-digest-2026-05-29.md`. `telecrawl` CLI/status/doctor worked against an isolated DB, but import is source-blocked because the VPS has no Telegram Desktop `tdata` path. Pilot report: `docs/research/openclaw-crawler-pilots-2026-05-29.md`.
- Current runtime gap: LCM reports `runtime.llm.complete` unavailable, so plugin-side autonomous summarization/compaction should wait for an OpenClaw build with Plugin SDK runtime LLM support.
- 2026-05-29 release-gate progress: extended `scripts/openclaw-update-guard.py` with read-only release footprint checks: install size, direct dependency count, duplicate nested dependency tree, native optional package count, optional cold/warm gateway turn latency, and `runtime.llm.complete` evidence. Latest guard report: `reports/openclaw-update-guard-20260529-030746.txt`, verdict WARN only because `runtime.llm.complete` has no explicit availability evidence.
- Next steps:
  1. CTO: investigate the runtime build path for Plugin SDK `runtime.llm.complete` support.
  2. NASR/CTO: review the first agent skill matrix and convert it into config/agent allowlists if approved.
  3. CTO: decide whether to schedule `scripts/openclaw-gitcrawl-digest.py` weekly after one more manual review run.
  4. CTO: check Ahmed-Mac or a copied archive for Telegram Desktop `tdata`, then run limited telecrawl import only after `doctor` passes.
  5. HR/JobZoom: review document-extract plugin against CV/job workflows before enabling.


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

## 2026-06-24 - NASR Loop Engineering hardening
- Priority: high
- Status: open, control artifacts created
- Context: Ahmed approved converting the Loop Engineering note into practical workflow hardening, starting with JobZoom and CMO.
- Artifacts:
  - `docs/agent-governance/nasr-loop-engineering-checklist-2026-06-24.md`
  - `/root/.openclaw/workspace-jobzoom/docs/loop-engineering-checklist.md`
  - `/root/.openclaw/workspace-cmo/docs/loop-engineering-checklist.md`
- Initial scope: manual closeout/reviewer checklist first, then read-only scripts after two real checks prove the gates reduce failure/noise.
- Approval boundary: loop automation does not approve public posts, email replies, recruiter messages, credentials, runtime changes, paid actions, destructive cleanup, or unknown sensitive application answers.
- Next steps:
  1. Run JobZoom checklist against the next live daily run.
  2. Run CMO checklist against the next draft-to-review visual workflow.
  3. Convert stable gates into read-only closeout scripts only after manual evidence.

### 2026-06-24 manual pass 1 - JobZoom
- Status: completed with warnings.
- Added `/root/.openclaw/workspace-jobzoom/scripts/jobzoom_closeout_check.py` as a read-only validator.
- Latest checked run: `83` / `2026-06-24`.
- Result: 12 PASS, 2 WARN, 0 FAIL.
- Repeat on next daily run before automation. Watch repeated warnings for empty `search_log` table and stale report wording that says delivery verification is pending.
