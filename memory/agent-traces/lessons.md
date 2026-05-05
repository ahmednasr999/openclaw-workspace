# Agent Lessons Learned

*Auto-curated from agent traces. Updated: 2026-05-05*

## Communication
- ✅ CLI uses --target not --to — exit 0 does not mean success. Always verify actual delivery (CEO, 2026-03-30)

## Config System
- ✅ Never bulk-overwrite config bindings without understanding each binding's required schema. Always backup and validate after editing openclaw.json (CTO, 2026-03-27)

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

## Tool Integration
- ✅ Always check config/ directory and service-registry.md before initiating OAuth. Direct credentials exist for Notion, Telegram, Gmail (CTO, 2026-03-21)

