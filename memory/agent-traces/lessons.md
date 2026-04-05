# Agent Lessons Learned

*Auto-curated from agent traces. Updated: 2026-04-03*

## Communication
- ✅ CLI uses --target not --to — exit 0 does not mean success. Always verify actual delivery (CEO, 2026-03-30)

## Config System
- ✅ Never bulk-overwrite config bindings without understanding each binding's required schema. Always backup and validate after editing openclaw.json (CTO, 2026-03-27)

## Content Post
- ✅ Always validate LinkedIn post length against 3000 char limit before posting (CMO, 2026-03-23)
- ✅ Never use Google Drive links for LinkedIn images — they may be stale. Always pull from Notion page blocks (CEO, 2026-03-29)
- ❌ Check for duplicate posts before celebrating success. Verify actual posted content, not just script logs (CEO, 2026-04-02)

## Cron Automation
- ❌ OpenClaw cron tool can fail silently. For critical one-shot reminders, system crontab is more reliable (CEO, 2026-04-02)

## Tool Integration
- ✅ Always check config/ directory and service-registry.md before initiating OAuth. Direct credentials exist for Notion, Telegram, Gmail (CTO, 2026-03-21)

