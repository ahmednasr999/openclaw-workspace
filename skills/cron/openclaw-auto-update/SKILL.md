# OpenClaw Auto-Update Check

## What
Check if a new OpenClaw version is available. If yes, summarize changes and update.

## Steps
1. Run: `npm view openclaw version` to get latest
2. Run: `openclaw --version` to get current
3. If same version, reply: "OpenClaw is up to date (vX.X.X)" and stop
4. If different:
   a. Run: `npm view openclaw --json` and extract recent changelog/description
   b. Send summary to Telegram: "🔄 OpenClaw update available: vCurrent → vLatest\n\nChanges: [summary]"
   c. Ask: "Update now? This will restart the gateway."
   d. If auto-update is enabled: run `npm install -g openclaw@latest && openclaw gateway restart`
5. Report result

## Rules
- Do NOT auto-update without confirmation unless the cron prompt says "auto-update enabled"
- If update fails, report the error - do not retry
- Keep output under 500 chars
