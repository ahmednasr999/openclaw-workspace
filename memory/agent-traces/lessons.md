# Agent Lessons Learned

*Auto-curated from agent traces. Updated: 2026-05-18*

## Communication
- ✅ CLI uses --target not --to — exit 0 does not mean success. Always verify actual delivery (CEO, 2026-03-30)

## Config System
- ✅ Never bulk-overwrite config bindings without understanding each binding's required schema. Always backup and validate after editing openclaw.json (CTO, 2026-03-27)
- ❌ For active-memory live replies, auth-correct helper models are not sufficient evidence. Verify hook elapsed logs after hot reload, and disable active-memory if it still times out in the live lane. For JobZoom delivery, parse send confirmation structurally, not substring-match only. (NASR/CTO maintenance, 2026-05-06)
- ❌ OpenClaw update recovery must verify binary path alignment, service ExecStart, Codex harness/plugin registration, lossless-claw dependency health, stale paired node versions, and a real Telegram /new then hi response before declaring success. (NASR/CTO recovery, 2026-05-15)
- ❌ For monitor health checks, verify the scheduler entry, the expected log file, and the monitor's own dry-run behavior before trusting documentation or stale summary JSON. (CTO, 2026-05-15)
- ❌ For OpenClaw binary-drift cleanup, do not use npm uninstall -g unless npm prefix has been verified. Remove duplicate non-active OpenClaw installs by explicit path after confirming the active service binary, then immediately verify /usr/bin/openclaw and /usr/local/bin/openclaw versions. (NASR/CTO cleanup, 2026-05-15)
- ❌ After OpenClaw updates, do not treat gateway health as enough. Run the runtime patch checker, back up current hashed dist bundles, patch the active hashed files only, reload the gateway, and verify health dashboard OK before saying done. (NASR/CTO repair, 2026-05-15)
- ❌ For model guardian checks, distinguish configured provider IDs from user-facing model status IDs, and remove stale plugin allowlist entries only after confirming the channel is disabled and backing up openclaw.json. (NASR/CTO repair, 2026-05-15)
- ❌ For kernel CVE closeout, package installation is not completion. Verify the rebooted running kernel, apt health, mitigations/listeners, OpenClaw health, model guardian health, and remove stale one-shot/watch crons only after the patched kernel is actually running. (NASR/CTO repair, 2026-05-15)
- ❌ For workspace hygiene heartbeat checks, separate root-only untracked entries from nested untracked work products before declaring a blocker. Ignore or move generated scratch state, but leave nested source-like artifacts for owner review. (CTO, 2026-05-16)
- ❌ When Ahmed approves workspace hygiene cleanup, commit source-like archive/docs/templates after secret scanning, remove empty placeholder directories, and verify both normal status and broad ls-files --directory are clean without touching unrelated modified runtime files. (CTO, 2026-05-16)
- ❌ For generic Telegram DM processing failures, inspect the concrete session JSON for modelOverride/providerOverride and stop duplicate gateway supervisors before assuming the default model config is active. (CTO, 2026-05-16)
- ❌ For Telegram gateway failures after provider/session cleanup, check both command sync and probe watchdog paths. A healthy default model does not prove Telegram API probes have enough timeout budget under event-loop load. (CTO, 2026-05-16)
- ❌ For LCM nightly compaction checks, verify the processor's runtime dependency paths and the force-compact threshold before treating queue creation as self-heal completion. (CTO, 2026-05-17)
- ❌ For offline LCM compaction, ignore declaration-only .d.ts files when deciding whether TypeScript compilation is required; if no implementation .ts sources exist, use the bundled dist runtime. (CTO, 2026-05-17)
- ❌ For Telegram DM processing failures, check the target session for stale active tool calls and verify a real later delivery before declaring recovery; also inspect host-level restart storms when gateway liveness reports CPU or event-loop delay. (CTO, 2026-05-17)
- ❌ For Model Guardian, slow OpenClaw CLI probes should use longer bounded timeouts, cache the expensive status JSON inside a run, and suppress the first transient timeout-only probe failure while still alerting immediately on config, model, or provider errors. (CTO, 2026-05-17)
- ❌ For LCM force-compact closeout, verify remaining zero-summary candidate count and duplicate session rows, not just exit status or failed=0; the processor needs conversation_id targeting or duplicate-session reconciliation before declaring the backlog processed. (CTO, 2026-05-18)
- ❌ For cron dashboard discovery, use `openclaw cron list --json` with a bounded load-tolerant timeout; do not parse the human table output or treat system-only discovery as complete. (CTO, 2026-05-18)

## Content Post
- ✅ Always validate LinkedIn post length against 3000 char limit before posting (CMO, 2026-03-23)
- ✅ Never use Google Drive links for LinkedIn images — they may be stale. Always pull from Notion page blocks (CEO, 2026-03-29)
- ❌ Check for duplicate posts before celebrating success. Verify actual posted content, not just script logs (CEO, 2026-04-02)

## Cv Creation
- ❌ ATS-compliant single-column HTML CV written, converted to PDF via weasyprint (21KB). Key tailoring: greenfield PMO build at SGH, Talabat logistics/fulfillment scale (7M orders/day), cross-functional stakeholder alignment matching JD. Sent to Ahmed via Telegram (msg 40770). Also saved to data/cvs/. (HR, 2026-04-06)

## External Publish Failure
- ❌ Add final duplicate guard against linkedin-posting-success.jsonl and live/tool state immediately before any external LinkedIn publish call. (CMO/main recovery, 2026-05-02)
- ❌ For LinkedIn autoposter assets, normalize file:// approved asset URIs to decoded local filesystem paths before Path.exists, and after a payload-prep failure mark the exact Notion page failed without sending duplicate Telegram alerts. (CMO, 2026-05-18)

## Jobzoom Daily Scan
- ❌ Investigate scoring endpoint response body before changing thresholds; keep fallback visible in daily summary. Use first-class message tool for delivery recovery when script CLI delivery fails. (JobZoom/HR lane, 2026-05-05)
- ❌ For JobZoom scoring, do not trust HTTP 200 or report existence. Keep prompts small enough to avoid LCM/file-reference substitution, persist raw bad scoring responses, and verify batch outputs parse before allowing fallback results to stand. (NASR/JobZoom, 2026-05-05)

## Memory Hygiene
- ❌ For memory hygiene cron audits, do not use command substitution with {} inside find -exec echo; run per-file line counting inside sh -c or a loop, then verify post-archive active-directory counts. (CTO, 2026-05-17)

## Tool Integration
- ✅ Always check config/ directory and service-registry.md before initiating OAuth. Direct credentials exist for Notion, Telegram, Gmail (CTO, 2026-03-21)

## Tool Usage
- ❌ When passing Markdown-heavy patches through the exec JavaScript wrapper, avoid raw backticks in the patch payload or escape them before calling apply_patch. (HR, 2026-05-17)
- ❌ For LCM nightly reporting, use aggregate subqueries or CTEs for active/stale conversation counts, keep raw join output only as optional audit parity, and wrap SQLite health checks with explicit timeouts to avoid orphaned cron processes. (CTO, 2026-05-18)

