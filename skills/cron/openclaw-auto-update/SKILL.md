# OpenClaw Auto-Update Check

## What
Check if a new OpenClaw version is available. If yes, summarize changes and update.

## Steps

### Step 1: Get Latest Version
Run: `npm view openclaw version` to get latest

### Step 2: Get Current Version
Run: `openclaw --version` to get current

### Step 3: Compare Versions
If same version, reply: "OpenClaw is up to date (vX.X.X)" and stop

### Step 4: Handle Update Available
If different:
a. Run: `npm view openclaw --json` and extract recent changelog/description
b. Send summary to Telegram: "🔄 OpenClaw update available: vCurrent → vLatest\n\nChanges: [summary]"
c. Ask: "Update now? This will restart the gateway."
d. If auto-update is enabled: run `npm install -g openclaw@latest && openclaw gateway restart`

### Step 5: Report Result
Report result of the update or version check

## Rules
- Do NOT auto-update without confirmation unless the cron prompt says "auto-update enabled"
- If update fails, report the error - do not retry
- Keep output under 500 chars

## Error Handling
- If npm view fails: report "Unable to check latest version" and stop
- If version check fails: report current version, skip comparison
- If update fails: report error, do not retry

## Quality Gates
- Version comparison uses semver (not string compare)
- Never auto-update without confirmation (unless cron says "auto-update enabled")
- Output under 500 chars

## Manual Run
```bash
cd /root/.openclaw/workspace && openclaw cron run openclaw-auto-update
```

## Output Rules
- No em dashes - use hyphens only
- Keep output under 500 chars for Telegram delivery
- Always include current version and latest version in report
- If up to date: "OpenClaw is up to date (vX.X.X) - checked [timestamp]"
- If update available: show changelog summary before asking to update
