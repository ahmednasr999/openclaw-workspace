# Slack Channel Reference

*Last updated: 2026-03-11*

## Channel Map

| Channel ID | Channel Name | Model Require | Purpose |
|------------|--------------|---------------|---------|
| C0AJLTEQTL3 | #ai-general | Sonnet 4.6 | Executive Intelligence Brief |
| C0AJX895U3E | #ai-jobs | Opus 4.6 | Job Radar reliability reports |
| C0AJM8PR0P5 | #ai-content | Sonnet 4.6 | LinkedIn content, posts, comments |
| C0AK6HSN2HX | #ai-system | MiniMax M2.5 | General / Job Radar |
| C0AJMCN64V9 | #ai-codex | GPT-5.4-Pro | fal.ai image generation |
| C0AKV41KF32 | #x-analysis | MiniMax M2.5 | X/Twitter analysis |
| C0AJQLE957H | #council | (incoming only) | Strategic council |
| C0AJBRTLK71 | #openclaw | (incoming only) | OpenClaw system |
| C0AKMHGFV40 | #random | (incoming only) | Random chat |

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

---

*Auto-generated from Slack API. Last sync: 2026-03-11*
