# Active Tasks

## 2026-08-19 - Governed product-learning shadow pilot
- Priority: medium
- Status: Daily Executive Intelligence shadow trial active; observation 1/7 captured
- Outcome: convert aggregated usage evidence into one reviewable lesson, one controlled intervention, and a measured terminal outcome without automatic workflow changes.
- Implemented:
  - deterministic bridge at `scripts/governed-product-learning.py`
  - locked analysis thresholds at `config/governed-product-learning.json`
  - sanitized snapshot and experiment templates under `templates/workflows/`
  - governance contract at `docs/agent-governance/governed-product-learning-pilot-2026-08-19.md`
  - focused tests covering privacy rejection, single-variable staging, explicit production approval, stage-hash binding, success, inconclusive, insufficient-evidence, and rollback-required states
- Verification: 8/8 focused tests passed; Python compilation, JSON parsing, and diff checks passed.
- Hardening: intentional editorial exits are explicitly excluded from friction scoring, and evaluation now requires a paired control/treatment or matched pre/post comparator.
- First live aggregate replay: 38 paired candidates, 9 current selections, 0 candidates corroborated by two credible distinct source domains, and 0 strict-gate treatment selections. This is not an outcome; the seven-day window is incomplete.
- Focused verification after hardening: 14/14 tests passed plus Python compilation and JSON parsing.
- Boundaries: no PostHog connection, production mutation, cron, runtime change, external action, or automatic promotion was activated.
- Next:
  1. Capture one local aggregate replay per day through 2026-08-25 without changing the live workflow.
  2. Evaluate only after exactly seven daily windows and at least 50 paired candidates.
  3. Treat a coverage/diversity guardrail breach as rollback-required; do not weaken the gates after seeing results.
  4. Promote a successful method into the existing governed learning registry only after an independent repeat and Ahmed's explicit approval.

## 2026-08-17 - Entity/write-path registry observation window
- Priority: high
- Status: active; registry implemented and seven-day workflow baseline observation pending
- Outcome: preserve federated systems while enforcing one accountable owner, one declared write direction, and seven governance gates per core entity.
- Implemented:
  - machine-readable registry at `config/entity-write-path-registry.json`
  - architecture contract at `docs/architecture/entity-write-path-registry-2026-08-17.md`
  - fail-closed read-only checker at `scripts/check-entity-write-path-registry.py`
  - live audit passed 23/23 evidence checks across nine entities and five workflows
  - measurement contracts cover volume, manual touch minutes, cycle time, and exception count
- Next:
  1. Observe 18-25 August 2026 using existing timestamps plus bounded manual-touch samples.
  2. Review the five workflow baselines on 25 August and identify the highest-value deterministic replacement candidate.
  3. Do not add production enforcement, migrations, new agents, or cron changes until the owner review accepts the registry and evidence.

## 2026-08-12 - NASR Doctor sandbox-awareness and runtime config review
- Priority: high
- Status: runtime privilege repair completed; NASR Doctor sandbox-awareness and CTO owner-side heartbeat commit remain pending
- Context: the 07:00 NASR Doctor failures were produced by sandbox restrictions and are not authoritative evidence of a runtime outage.
- Verified evidence:
  - a current `/tmp/openclaw` log confirms the Gateway is live
  - DNS and network checks are blocked in the Doctor namespace
  - the pipeline database is present and passes immutable read-only `integrity_check=ok` with 4,869 jobs; a normal SQLite open is denied by the sandbox
  - main-workspace critical instruction files are clean
  - cron dashboard tail contains 0 `ERROR` entries
  - disk usage is 68%
  - daily backup remains intentionally disabled per Ahmed's standing decision
- Real warning: `/root/.openclaw/openclaw.json` has uncommitted execution-policy changes. The file is schema-valid, but the two `mode: "full"` additions are not approved for closeout and require Ahmed's explicit runtime-config decision before any edit, commit, or rollback.
- Resolution (2026-08-16): Ahmed approved the recommended narrow repair. Global `tools.exec.mode` was restored to `auto`; the CMO `mode: "full"` override was removed while its Windows node target was preserved. The same controlled maintenance activated the first lossless-claw prompt-efficiency pilot variable (`freshTailMaxTokens=8000`, summarized-prefix target still `12000`). The detached restart completed successfully; gateway health is `ok=true` and not degraded, config is valid, the Memory Heist suite passes 19/19, runtime patches pass, and `openai/gpt-5.6-sol` remains active.
- Latest CTO recheck (2026-08-12 13:53 Africa/Cairo): `/root/.openclaw/openclaw.json` remains modified and still needs explicit review. The Gateway log is current, the cron dashboard has 0 `ERROR` lines in its last 100 lines, disk usage remains 68%, and backup is disabled as intended. No CTO-side mutation of the main workspace was made.
- Latest CTO heartbeat (2026-08-12 15:46 Africa/Cairo): `/root/.openclaw/openclaw.json` remains modified and requires review. The Gateway log is current, the cron dashboard has 0 `ERROR` lines in its last 100 lines, disk usage is 68%, daily backup remains intentionally disabled, and there are no untracked files at the main workspace root.
- Latest CTO heartbeat handoff (2026-08-12 17:49 Africa/Cairo): `/root/.openclaw/openclaw.json` remains modified and is an unresolved critical-path change requiring explicit review. The Gateway log is active, cron errors are 0, disk usage is 68%, and the backup job remains intentionally disabled. No runtime configuration action was authorized or taken.
- Review of 19:46 CTO handoff (2026-08-12):
  - `/root/.openclaw/openclaw.json` is schema-valid. Its CMO node target now resolves to the current `Windows Node (AHMEDNASR)` OpenClaw node with `browser.proxy`, which aligns with the approved Windows-only LinkedIn account-state lane.
  - The same diff adds `mode: "full"` to CMO node execution and changes global `tools.exec.mode` from `auto` to `full`. The live schema defines `full` as trusted operation, while `auto` classifier-reviews approval misses. No durable approval or change record was found for these two privilege elevations, and the global change directly reverses the security hardening recorded on 2026-08-09.
  - Recommendation: preserve the Windows node target, restore global `tools.exec.mode` to `auto`, and remove the CMO `mode: "full"` override unless Ahmed explicitly approves that broader trust boundary. No runtime/config mutation was made during this review.
  - `/root/.openclaw/workspace-cto/HEARTBEAT.md` contains only the owner-boundary repair Ahmed approved on 2026-08-11: CTO must hand off main-workspace pending-note updates to NASR/main and use a CTO-local fallback. The content is reviewed and accepted; the remaining dirty-path resolution is an owner-side CTO commit, not a main-workspace edit.
  - Latest CTO recheck (2026-08-12 21:46 Africa/Cairo): both paths remain modified with no substantive diff change from the 19:46 review. Gateway log activity is current, cron-dashboard errors remain 0, disk usage remains 68%, and daily backup remains disabled by Ahmed's standing decision. No runtime/config mutation was authorized or made.
  - Main-workspace review of the 2026-08-13 07:45 CTO handoff: the `openclaw.json` diff is unchanged and the prior verdict stands. The Windows node target is intentional; the CMO and global `mode: "full"` elevations remain unapproved and should be removed unless Ahmed explicitly accepts that trust-boundary expansion. Config validation passed. The live Gateway probe returned `ok=true`, `degraded=false`, and Telegram connected; the Gateway log is fresh and disk usage is 69%. The 07:00 NASR Doctor failures were reconciled as sandbox artifacts: its `--fix` backup could not write, but the pipeline DB independently passes `integrity_check=ok` with 4,869 jobs and an August 11 latest update. No runtime/config mutation was authorized or made.
- Next:
  1. Make NASR Doctor sandbox-aware so blocked DNS/network and normal SQLite-open probes are classified as namespace limitations rather than production failures.
  2. Preserve immutable read-only database integrity checking as the authoritative fallback inside the sandbox.
  3. Have the CTO workspace owner commit the already approved `HEARTBEAT.md` governance repair.

## 2026-07-20 - Unified open-work Resolver pilot
- Priority: high
- Status: active read-only pilot; LinkedIn +30 is the first tracked outcome
- Outcome contract: `owner -> target -> verified progress -> next action -> evidence -> blocker -> stale deadline -> verified close`
- Implemented:
  - deterministic Resolver at `/root/.openclaw/workspace/scripts/open-work-resolver.py`
  - single-item pilot registry at `/root/.openclaw/workspace/config/open-work-resolver.json`
  - internal audit and briefing views under `/root/.openclaw/workspace/reports/open-work-resolver/`
  - transition history under `/root/.openclaw/workspace/data/open-work-resolver/`
  - read-only five-minute OS cron; it cannot call the executor or change campaign state
  - existing morning brief consumes only progress, intervention, and verified-closure cards from the Resolver feed
- Evidence contract: strict campaign ledger, supervisor heartbeat/counter, systemd service state, and live PID must agree; a fresh strict-ledger advance may lead the supervisor checkpoint during an active cycle, but a supervisor overclaim fails closed.
- Live baseline: 9/30 strict verified LinkedIn applications, 21 remaining, active/running service, fresh heartbeat, no blocker. The supervisor was one checkpoint behind the strict ledger during the first live run, correctly classified as verified progress.
- Verification: 10 Resolver unit tests passed, including blocked-to-healthy recovery and fail-closed target overclaim; Python compilation and diff checks passed; managed and installed crontab hashes match; a stripped cron-like wrapped run and an untouched scheduled run completed rc=0 and produced the three-bucket briefing view.
- Next:
  1. Keep the pilot read-only through campaign closure.
  2. Accept closure only at 30/30 in the strict ledger.
  3. Review false-positive/false-negative stale classifications before adding a second workflow.

## 2026-07-11 - GPT-5.6 Sol reasoning-tier optimization
- Priority: medium
- Status: narrow production pilot active; four deterministic wrappers moved from medium to low
- Scope: reasoning effort only. Model remains `openai/gpt-5.6-sol`; no fallback or cheaper model introduced.
- Evidence:
  - isolated low-versus-medium benchmark covers email classification, funding-structure parsing, fintech ranking, and operational triage
  - refined deterministic suite passed 4/4 at both low and medium, with no model fallback
  - low was not faster in the sample, so no broad downgrade was approved
  - live low-effort Daily Intel verification completed successfully and wrote both expected files
- Production changes:
  - Daily Intel Sweep: medium -> low
  - Email Agent (Fri-Sat): medium -> low
  - Email Agent (Sun-Thu): medium -> low
  - Weekly Pipeline Audit: medium -> low
  - all judgment-heavy, browser, content, CV, and executive-review jobs retained their prior tiers
- Tool decision: did not enable experimental OpenClaw `tools.toolSearch`; Codex-harness runs already use stable native code mode, deferred tools, and nested calls. Programmatic orchestration is limited to bounded filtering, ranking, deduplication, validation, aggregation, and read-only retrieval.
- Verification: policy checker passed; enabled agent-turn distribution is 16 low, 7 medium, 2 high; config valid; gateway healthy and not degraded; Telegram connected; current interactive session remains GPT-5.6 Sol/high.
- Rollback: `/root/.openclaw/backups/reasoning-effort-20260711T004340/`
- Next: inspect the next scheduled runs of the four changed jobs. Restore medium for any output or delivery regression.

## 2026-07-11 - Global Fintech Executive Radar MVP
- Priority: medium
- Status: manual internal MVP implemented; automation intentionally withheld pending multi-day quality proof
- Context: Ahmed approved building a worldwide fintech intelligence wire with fundraising as a core lane, plus M&A, regulation, payments, digital banking, infrastructure, leadership, and a GCC relevance overlay.
- Implemented:
  - deterministic collector at `/root/.openclaw/workspace/scripts/fintech-radar.py`
  - source and ranking policy at `/root/.openclaw/workspace/config/fintech-radar.json`
  - internal evidence contract at `/root/.openclaw/workspace/docs/fintech-radar-mvp.md`
  - Markdown and JSON outputs under `/root/.openclaw/workspace/intel/fintech-radar/`
  - evidence labels: Primary, Corroborated, Trusted Reporting, and Discovery
  - worldwide capital ledger with amount/stage extraction and balanced executive queue across non-capital lanes
- Verification:
  - first noisy search sample failed and was not promoted; retrieval was tightened to Google News RSS plus strict fintech/category relevance gates
  - 10 unit tests passed
  - live sample contains 18 relevant stories across Capital, Regulation, Payments, Digital Banking, and Leadership
  - top 8 links returned HTTP 200
  - JSON parsed successfully and the latest Markdown brief is non-empty
- Next steps:
  1. Manually review the current sample with Ahmed.
  2. Run manually for several days and tune duplicate/primary-source resolution.
  3. Add deterministic daily scheduling only after output quality is proven. Do not publish publicly or auto-send externally without separate approval.

## 2026-07-10 - JobZoom application-package quality gate shadow rollout
- Priority: high
- Status: active, salary-first report v2 implemented; package-gate live streak 1/3
- Context: Ahmed approved upgrading JobZoom with the stronger validation and packaging controls from the Hermes workflow while keeping JobZoom as the single daily system.
- Implemented:
  - isolated shadow evaluator at `/root/.openclaw/workspace-jobzoom/scripts/jobzoom_quality_gate.py`
  - additive `quality_gate_runs` and `quality_gate_decisions` tables in the canonical JobZoom database
  - report, ZIP, manifest, CV text/page, applied-ledger, JD completeness, LinkedIn identity, eligibility, salary-potential, and exactly-once delivery-marker checks
  - current-state old-package suppression for roles applied after the original run
  - read-only promotion checker at `/root/.openclaw/workspace-jobzoom/scripts/jobzoom_quality_gate_acceptance.py`
  - direct OS cron at 07:15 Cairo, after the unchanged 05:00 production run
  - production report v2 decision layer: Apply now, Verify compensation, Blocked, Watchlist, Ineligible, Already applied, and Insufficient JD
  - nationality restrictions, including `UAEN`, excluded before scoring and CV generation
  - unified fresh + still-open salary-first action queue on page one; scan coverage moved to an appendix
  - approved human-readable CV filename format for newly generated CVs
  - read-only replay utility at `/root/.openclaw/workspace-jobzoom/scripts/regenerate_report_v2.py`
- Verification:
  - five historical runs, 5-9 July, passed; 30 decisions evaluated
  - 9 July shadow decision: 2 application-ready, 1 blocked at 82 due salary-floor evidence, 7 watchlist
  - current-state 9 July replay: 10/10 excluded as already applied, 0 ready
  - database integrity passed; jobs/applied/runs counts unchanged
  - production daily runner, launcher, and safe-runner checksums match the pre-change backup
  - clean-room restore from `/root/.openclaw/workspace-jobzoom/backups/quality-gate-20260710-031951` passed and was destroyed after verification
  - 10 July live shadow passed, streak 1/3: 0 ready, 1 blocked, 6 watchlist
  - 10 July v2 replay generated and visually inspected: 0 apply now, 11 compensation checks, 1 blocked, 6 watchlist, 1 excluded; MedNet blocked and Mackenzie Jones UAEN excluded
  - 11 unit tests passed; raw scrape eligibility test detected 14 restricted listings before scoring
- Next steps:
  1. Collect the remaining two consecutive live shadow runs on 11-12 July.
  2. Run `python3 scripts/jobzoom_quality_gate_acceptance.py --required 3` in the JobZoom workspace.
  3. Review current-versus-shadow package-integrity differences before promoting the shadow package gate. Do not auto-promote that gate.

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
- Status: operationalized; 30-day JobZoom and CMO quality-and-evidence phase active
- Context: Ahmed approved converting the Loop Engineering note into practical workflow hardening, starting with JobZoom and CMO.
- Artifacts:
  - `docs/agent-governance/nasr-loop-engineering-checklist-2026-06-24.md`
  - `/root/.openclaw/workspace-jobzoom/docs/loop-engineering-checklist.md`
  - `/root/.openclaw/workspace-cmo/docs/loop-engineering-checklist.md`
  - `skills/agent-ops-loops/references/nasr-engineering-loop.md`
  - `templates/workflows/nasr-engineering-loop-record.json`
  - `scripts/check-nasr-engineering-loop.py`
  - `scripts/run-nasr-engineering-loop-pilot.py`
  - `reports/nasr-engineering-loop-pilot-2026-07-14.md`
- 2026-07-14 pilot: isolated Git fixture reached `ready_for_approval`; 19 control tests and 5 fixture acceptance tests passed. Emoji-only approval, stale-SHA approval, duplicate events, builder self-review, and failed-test progression were rejected. No merge, external write, runtime change, or Linear dependency was introduced.
- 2026-07-18 governed-outcome rollout:
  - added the shared contract at `docs/agent-governance/governed-outcome-loops-2026-07-18.md`
  - added independent read-only verifiers at `/root/.openclaw/workspace-jobzoom/scripts/jobzoom_governed_outcomes.py` and `/root/.openclaw/workspace-cmo/scripts/cmo_governed_outcomes.py`
  - expanded the CMO manual metrics ledger with saves, sends, qualified profile visits, relevant followers, qualified inbound conversations, format, and cohort fields
  - real JobZoom shadow baseline stopped at `repair-evidence`: latest run kept 150/150 coverage and 9/9 CVs but had 21 failed scoring calls before recovery; 90-day application attribution into the career pipeline is 41.3%
  - real CMO shadow baseline stopped at `repair-evidence`: 10 posts in 30 days, 0% public/outcome metrics capture, and six posts in the last seven days versus the configured 3-4 target
  - new verifier tests passed 5/5; unaffected JobZoom gate tests passed 6/6 and CMO post-approval tests passed 5/5
  - no cron, prompt, scoring, cadence, approval, publishing, application, runtime, or external behavior changed
- 2026-07-18 evidence repair:
  - reconciled the 90-day JobZoom applied ledger into the career pipeline: 899/899 eligible applications now attributed, 525 pipeline rows inserted, 370 existing rows repaired, and six explicit `unapplied_marked` rows excluded
  - added an idempotent sync bridge and connected it to confirmed non-dry-run `mark_run_applied.py` updates; final dry-run showed 899 matched, 0 inserts, and 0 updates
  - captured author-visible LinkedIn analytics for the 11-post July 8-18 cohort; public-metric coverage is 100% and grounded-outcome field coverage is 78.2%
  - CMO recommendation moved from `repair-evidence` to `continue-baseline`, but remains warning because seven posts in seven days exceeds the 3-4 target
  - JobZoom attribution is repaired, but the overall recommendation remains `repair-evidence` because the latest execution recorded 21 failed scoring calls before recovery
- 2026-07-18 quality-and-evidence phase:
  - hardened JobZoom authentication and response validation without changing its 150-search scope, prompts, scoring weights, threshold, model, or application behavior
  - reliability promotion requires three distinct clean production days; current streak is 0/3 and remains `repair-evidence`
  - prospective applications are segmented by role family, country, canonical source, ATS band, company type, and CV version from July 19-August 17; outcome review is gated until August 31
  - activated a six-post opening-hook experiment at fixed Sun/Tue/Thu cadence on July 19, 21, 23, 26, 28, and 30; three direct-thesis controls alternate with three executive-tension treatments
  - the experiment is `shadow-manual-only`, comparison remains 0/6, and review is after August 6; no automatic change or public post occurred during setup
  - reused the existing Friday 17:00 Cairo CMO report cron for weekly author-analytics capture through Ahmed-Mac and governed review; no new agent or cron was added
  - focused verification passed 19 JobZoom and 26 CMO tests; five unrelated legacy JobZoom v2-policy tests remain stale and are deferred
- Initial scope: manual closeout/reviewer checklist first, then read-only scripts after two real checks prove the gates reduce failure/noise.
- Approval boundary: loop automation does not approve public posts, email replies, recruiter messages, credentials, runtime changes, paid actions, destructive cleanup, or unknown sensitive application answers.
- Next steps:
  1. Observe the next three distinct JobZoom daily runs; do not declare reliability before 3/3 clean runs.
  2. Complete all six LinkedIn experiment posts and weekly evidence captures; review hook variants after August 6 without automatic adaptation.
  3. Complete the application cohort through August 17 and wait through the August 31 outcome-maturity gate before changing targeting.
  4. When a real non-critical GitHub repository is selected, reuse the validated record for one ticket-to-PR pilot; keep preview deployment and merge separately approval-gated.

### 2026-06-24 manual pass 1 - JobZoom
- Status: completed with warnings.
- Added `/root/.openclaw/workspace-jobzoom/scripts/jobzoom_closeout_check.py` as a read-only validator.
- Latest checked run: `83` / `2026-06-24`.
- Result: 12 PASS, 2 WARN, 0 FAIL.
- Repeat on next daily run before automation. Watch repeated warnings for empty `search_log` table and stale report wording that says delivery verification is pending.

## 2026-07-27 - Production workflow contract and LinkedIn Radar reference implementation

- Priority: high
- Status: implemented and isolated verification complete; one unlocked live full-pack proof remains
- Outcome: recurring production workflows gain persisted stages, bounded attempts, resumability, immutable evidence, deterministic judges, and explicit terminal states without adding a graph framework.
- Implemented:
  - reusable contract at `scripts/production_workflow_contract.py`
  - governance decision at `docs/agent-governance/production-workflow-contract-2026-07-27.md`
  - radar stages `source -> extract -> validate -> rank -> approval`
  - automatic and explicit resume, safe identifiers, two-attempt exhaustion, 30-second shared-browser lock timeout, and immutable artifact hashes
  - standalone radar judge at `/root/.openclaw/workspace-cmo/scripts/judge_linkedin_comment_radar_run.py`
- Verification: 33 focused tests passed. Valid five-card evidence passed; missing URL, duplicate candidate, context mismatch, corrupt stage evidence, and missing approval pack failed closed. Injected extract failure resumed without rerunning `source`.
- Live contention proof: run `2026-07-27-1500-recovery-2` recorded `source=failed`, `attempts=1`, `failure_classification=TimeoutError`, terminal `blocked`, and zero artifacts while the approved LinkedIn +30 campaign owned the shared browser lock.
- Approval boundary: this workflow may source, validate, rank, and create internal approval artifacts. It may not comment, like, message, post, alter cron/runtime, or bypass Ahmed's approval.
- LinkedIn publishing and engagement cadence resumed by Ahmed on 2026-08-07: 09:15 publishing preflight, 09:30 Notion-approved publisher, and Comment Radar at 11:00 and 15:00 Cairo. Comments remain approval-gated. Keep the VPS LinkedIn browser and retired +30 application campaign disabled; all authenticated LinkedIn reads and writes use only the Windows OpenClaw-managed Chrome profile through `browser.proxy`, without the extension, and stop without fallback when it is unavailable.
- Next:
  1. After the LinkedIn +30 campaign releases the lock, resume `2026-07-27-1500-recovery-2` read-only and require `approval_required` plus a passing standalone judge.
  2. Observe one normal scheduled radar run.
  3. Only then select the next migration lane; content publishing is the likely second candidate.
