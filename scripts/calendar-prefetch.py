#!/usr/bin/env python3
"""
calendar-prefetch.py — Fetch today's Google Calendar events via Composio
and cache them for the morning briefing.

Output: /tmp/calendar-events-YYYY-MM-DD.json
"""
import json, os, sys, ssl
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

CAIRO = timezone(timedelta(hours=2))
today = datetime.now(CAIRO).strftime("%Y-%m-%d")
output_path = f"/tmp/calendar-events-{today}.json"

def main():
    # This script is a FALLBACK that just writes an empty file
    # The actual calendar fetch happens via Composio in the cron agent
    # This ensures briefing-agent always has a file to read
    
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        if size > 2:  # More than just "[]"
            print(f"Calendar cache already populated: {output_path} ({size} bytes)")
            return
    
    # Write empty array as fallback
    with open(output_path, 'w') as f:
        json.dump([], f)
    print(f"Calendar fallback: {output_path} (empty - no events or prefetch didn't run)")

if __name__ == "__main__":
    main()
