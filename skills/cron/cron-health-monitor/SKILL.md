---
name: cron-health-monitor
description: "Detect partial cron failures (delivered to Telegram but missing Notion page) and auto-recover by creating missing pages."
---

# Cron Health Monitor

Runs 30 minutes after morning briefing to verify critical crons completed ALL steps - not just Telegram delivery. Auto-recovers partial failures.

## Why This Exists
Crons have a 270s timeout. If a cron delivers to Telegram but gets SIGTERM before Notion sync, the user gets a briefing but the Notion record is missing. This monitor catches that gap and fixes it.

## Steps

### Step 1: Check Morning Briefing Notion Page
```bash
cd /root/.openclaw/workspace && python3 << 'CHECK'
import json, urllib.request, ssl
from datetime import datetime, timezone

with open('config/notion.json') as f:
    token = json.load(f)['token']
ctx = ssl.create_default_context()

def notion_post(path, body):
    url = f"https://api.notion.com/v1{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method='POST', headers={
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    })
    with urllib.request.urlopen(req, context=ctx) as r:
        return json.loads(r.read())

today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
resp = notion_post('/databases/3268d599-a162-812d-a59e-e5496dec80e7/query', {
    'filter': {'property': 'Date', 'date': {'equals': today}},
    'page_size': 1
})
exists = len(resp.get('results', [])) > 0
print(f"BRIEFING_PAGE_EXISTS={exists}")
print(f"DATE={today}")
CHECK
```

### Step 2: Check Cron Run Status
```bash
openclaw cron runs --id 7ad73a82-c7a8-41d9-9488-50a6ce820088 2>&1 | python3 -c "
import sys, json, re
text = sys.stdin.read()
# Find JSON
for i, ch in enumerate(text):
    if ch == '{':
        try:
            data = json.loads(text[i:])
            break
        except:
            continue
else:
    print('CRON_STATUS=unknown')
    exit()

entries = data.get('entries', [])
if entries:
    latest = entries[0]
    print(f'CRON_STATUS={latest.get(\"status\",\"unknown\")}')
    print(f'CRON_DURATION={latest.get(\"durationMs\",0)}ms')
    summary = latest.get('summary','')[:200]
    print(f'CRON_SUMMARY={summary}')
else:
    print('CRON_STATUS=no_runs')
"
```

### Step 3: Auto-Recover If Missing
If BRIEFING_PAGE_EXISTS=False but the cron ran successfully (status=ok):

1. Extract the briefing summary from the cron run data
2. Create a Notion page with the recovered content
3. Mark it as "Recovered by health monitor" in the model field
4. Notify Ahmed via Telegram: "Morning briefing Notion page was missing (timeout). Recovered automatically."

If the cron itself failed (status != ok):
- Notify Ahmed: "Morning briefing cron failed entirely. Manual run needed."

### Step 4: Verify Dashboard Updates
Check if the Dashboard KPI and Stale Alerts blocks were updated today:
```bash
cd /root/.openclaw/workspace && python3 -c "
import sys; sys.path.insert(0, 'scripts')
from notion_sync import compute_stale_alerts, update_stale_alerts
alerts = compute_stale_alerts()
update_stale_alerts(alerts)
print(f'Dashboard stale alerts refreshed: {len(alerts)} items')
"
```

### Step 5: Report (Telegram only if issues found)
- If everything is fine: NO_REPLY (silent)
- If recovery was needed: Send brief Telegram message about what was recovered
- If cron failed entirely: Alert Ahmed with action items

## Error Handling
- If Notion API fails: Report error, don't try to recover
- If cron run data unavailable: Report "unable to verify", suggest manual check
- Keep this monitor lightweight - should complete in under 60s
