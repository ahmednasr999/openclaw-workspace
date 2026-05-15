# Agent Lessons Learned

*Auto-curated from agent traces. Updated: 2026-05-15*

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

## Content Post
- ✅ Always validate LinkedIn post length against 3000 char limit before posting (CMO, 2026-03-23)
- ✅ Never use Google Drive links for LinkedIn images — they may be stale. Always pull from Notion page blocks (CEO, 2026-03-29)
- ❌ Check for duplicate posts before celebrating success. Verify actual posted content, not just script logs (CEO, 2026-04-02)

## Cv Creation
- ❌ ATS-compliant single-column HTML CV written, converted to PDF via weasyprint (21KB). Key tailoring: greenfield PMO build at SGH, Talabat logistics/fulfillment scale (7M orders/day), cross-functional stakeholder alignment matching JD. Sent to Ahmed via Telegram (msg 40770). Also saved to data/cvs/. (HR, 2026-04-06)

## External Publish Failure
- ❌ Add final duplicate guard against linkedin-posting-success.jsonl and live/tool state immediately before any external LinkedIn publish call. (CMO/main recovery, 2026-05-02)

## Jobzoom Daily Scan
- ❌ Investigate scoring endpoint response body before changing thresholds; keep fallback visible in daily summary. Use first-class message tool for delivery recovery when script CLI delivery fails. (JobZoom/HR lane, 2026-05-05)
- ❌ For JobZoom scoring, do not trust HTTP 200 or report existence. Keep prompts small enough to avoid LCM/file-reference substitution, persist raw bad scoring responses, and verify batch outputs parse before allowing fallback results to stand. (NASR/JobZoom, 2026-05-05)

## Tool Integration
- ✅ Always check config/ directory and service-registry.md before initiating OAuth. Direct credentials exist for Notion, Telegram, Gmail (CTO, 2026-03-21)

