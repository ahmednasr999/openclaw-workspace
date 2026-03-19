# Notification Digest

## What
Collect low-priority cron outputs from the last 3 hours and send a single digest.

## Steps
1. Read `/root/.openclaw/workspace/.notifications/` directory
2. Collect all .md files modified in the last 3 hours
3. If no files found, reply "No notifications" and stop
4. Build a digest:
   ```
   📋 3-Hour Digest (HH:MM - HH:MM Cairo)
   
   [filename without .md]: [first 2 lines of content]
   ---
   [next file]
   ```
5. Delete processed files after sending
6. Keep digest under 2000 chars

## Rules
- If only 1 notification, send it directly (no digest wrapper)
- If 0 notifications, reply with just "No notifications" - no extra text
- Critical files (containing "CRITICAL" or "URGENT") skip batching - those are sent immediately by their own scripts
