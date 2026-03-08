# Slack Channel Reference

*Last updated: 2026-03-08*

## Channel Map

| Channel ID | Model Require | Purpose | Mention |
|------------|-------|---------|-----------------|
| C0AJLTEQTL3 | Sonnet 4.6 | Executive Intelligence Brief | No |
| C0AJX895U3E | Opus 4.6 | Job Radar reliability reports | No |
| C0AJM8PR0P5 | Sonnet 4.6 | General /备用 | No |
| C0AK6HSN2HX | MiniMax M2.5 | General / Job Radar | No |
| C0AJMCN64V9 | GPT-5.4-Pro | fal.ai image generation | No |
| C0AKV41KF32 | MiniMax M2.5 | General | No |

## Config Details

- **Bot token:** Active (xoxb-1064...)
- **App token:** Active (xapp-1-A0A...)
- **User token:** Read-only (limited write)
- **Mode:** Socket (real-time)
- **DM policy:** Open
- **Group policy:** Open

## Active Cron Jobs to Slack

**None** — all cron jobs currently route to Telegram or run headless. No outgoing Slack crons configured.

## Notes

- Channel IDs are Slack-native (start with C0)
- All channels set to `requireMention: false` — mentions not required to trigger
- Model overrides apply per-channel for incoming messages
- GPT-5.4-Pro (C0AJMCN64V9) is the only Codex channel — used for image generation tasks
