# Notification Digest

## What
Collect low-priority cron outputs from the last 3 hours and send a single digest.

## Steps

### Step 1: Read Notifications Directory
Read `/root/.openclaw/workspace/.notifications/` directory

### Step 2: Collect Recent Files
Collect all .md files modified in the last 3 hours

### Step 3: Check for Empty
If no files found, reply "No notifications" and stop

### Step 4: Build Digest
Build a digest:
```
📋 3-Hour Digest (HH:MM - HH:MM Cairo)

[filename without .md]: [first 2 lines of content]
---
[next file]
```

### Step 5: Delete Processed Files
Delete processed files after sending

### Step 6: Length Check
Keep digest under 2000 chars

## Rules
- If only 1 notification, send it directly (no digest wrapper)
- If 0 notifications, reply with just "No notifications" - no extra text
- Critical files (containing "CRITICAL" or "URGENT") skip batching - those are sent immediately by their own scripts

## Error Handling
- If .notifications/ directory missing: create it, report "No notifications"
- If file read fails: skip that file, continue with others
- If all files fail: report "Digest failed - notification files unreadable"

## Quality Gates
- Digest under 2000 chars
- Processed files deleted after sending
- CRITICAL/URGENT items never batched (sent immediately by their own scripts)

## Manual Run
```bash
cd /root/.openclaw/workspace && openclaw cron run notification-digest
```

## Output Rules
- No em dashes - use hyphens only
- Digest header must include time window: "[HH:MM] - [HH:MM] Cairo"
- Keep total digest under 2000 chars for Telegram delivery
- If zero notifications: reply "No notifications" with no extra text
- Include count of files processed in footer
