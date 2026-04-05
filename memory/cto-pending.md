# CTO Pending Issues — 2026-04-03

## Open Issues

1. **content-orchestrator.py missing** — archived at scripts/.archived/. Test file exists but can't run. Needs restore or test reference updated.

2. **CV test failures** — flagged April 1 morning. Details not captured. Needs manual investigation.

3. **exec-approvals.json reset by gateway** — defaults cleared again (changed to `security: full, ask: off`). Re-applied fix (`askFallback: allowlist`). Same pattern: gateway rewrites file on certain events. Need persistent fix via openclaw.json config or chattr +i (requires SSH).

4. **⚠️ Notion API token expired (401 Unauthorized)** — cron-dashboard-updater.py is getting repeated 401 errors from Notion API. Health dashboard not updating. Token rotation needed via Notion integration settings.

## Uncommitted Files

Many M files (data/logs/memory) — auto-generated, not auto-committed per policy. Untracked files include CV PDFs, session archives, temp scripts.

## Resolved

- exec-approvals.json fix re-applied (April 3 ~09:09 Cairo)
- All heartbeat checks passing (gateway live, cron running, 0 errors)
