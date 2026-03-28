#!/usr/bin/env python3
"""
calendar-prefetch.py — Fetch today's Google Calendar events via Composio
and cache them for the morning briefing.

Output: /tmp/calendar-events-YYYY-MM-DD.json
"""
import json, os, sys, subprocess
from datetime import datetime, timezone, timedelta

CAIRO = timezone(timedelta(hours=2))
now = datetime.now(CAIRO)
today = now.strftime("%Y-%m-%d")
output_path = f"/tmp/calendar-events-{today}.json"

# Cairo is UTC+2
time_min = f"{today}T00:00:00+02:00"
time_max = f"{today}T23:59:59+02:00"

OPENCLAW_INVOKE = [
    "node", "-e", """
const { ComposioToolSet } = require('/usr/lib/node_modules/openclaw/node_modules/@composio/core');
const toolset = new ComposioToolSet();
async function main() {
    const client = toolset.getComposioClient();
    const result = await client.actionsV2.execute({
        actionName: 'GOOGLECALENDAR_EVENTS_LIST_ALL_CALENDARS',
        requestBody: {
            input: {
                time_min: process.env.TIME_MIN,
                time_max: process.env.TIME_MAX,
                single_events: true,
                summary_only: true
            }
        }
    });
    console.log(JSON.stringify(result));
}
main().catch(e => { console.error(e.message); process.exit(1); });
"""
]

def fetch_via_composio():
    """Fetch calendar events using Composio Google Calendar integration."""
    env = os.environ.copy()
    env["TIME_MIN"] = time_min
    env["TIME_MAX"] = time_max
    
    try:
        result = subprocess.run(
            OPENCLAW_INVOKE,
            capture_output=True, text=True, timeout=30, env=env
        )
        if result.returncode != 0:
            print(f"Composio call failed: {result.stderr[:200]}", file=sys.stderr)
            return None
        
        data = json.loads(result.stdout)
        summary = data.get("data", {}).get("summary_view", [])
        return summary
    except Exception as e:
        print(f"Composio fetch error: {e}", file=sys.stderr)
        return None


def fetch_via_openclaw_api():
    """Fetch via OpenClaw local API (port 3001) which has Composio credentials."""
    import urllib.request
    
    payload = json.dumps({
        "tool": "GOOGLECALENDAR_EVENTS_LIST_ALL_CALENDARS",
        "params": {
            "time_min": time_min,
            "time_max": time_max,
            "single_events": True,
            "summary_only": True
        }
    }).encode()
    
    req = urllib.request.Request(
        "http://localhost:3001/api/composio/execute",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data.get("data", {}).get("summary_view", [])
    except Exception as e:
        print(f"OpenClaw API fetch error: {e}", file=sys.stderr)
        return None


def main():
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        if size > 2:  # More than just "[]"
            print(f"Calendar cache already populated: {output_path} ({size} bytes)")
            return

    # Try Composio fetch
    events = fetch_via_openclaw_api()
    
    if events is None:
        events = []
        print(f"Calendar prefetch: 0 events (Composio unavailable - writing empty cache)")
    else:
        print(f"Calendar prefetch: {len(events)} events for {today}")
        for ev in events:
            title = ev.get("title", "(No title)")
            if ev.get("is_all_day"):
                print(f"  ALL-DAY: {title}")
            else:
                start = ev.get("start", "")
                end = ev.get("end", "")
                st = start.split("T")[1][:5] if "T" in start else start
                en = end.split("T")[1][:5] if "T" in end else end
                print(f"  {st}-{en}: {title}")

    with open(output_path, "w") as f:
        json.dump(events, f, indent=2)
    print(f"Cached to: {output_path}")


if __name__ == "__main__":
    main()
