#!/usr/bin/env python3
"""
Google Calendar Push Notification Receiver

Receives webhook notifications from Google Calendar API,
fetches changed events, and forwards to Telegram via bot API.

Runs on port 8789, exposed via Tailscale Funnel at:
https://srv1352768.tail945bbc.ts.net/calendar-push
"""

import http.server
import json
import subprocess
import urllib.request
import os
import sys
from datetime import datetime, timezone, timedelta

PORT = 8789
BOT_TOKEN = "8213291111:AAHCk2J4XIRQaTsBkACl_Xpla7LFvVx1304"
CHAT_ID = "866838380"
SYNC_TOKEN_FILE = "/root/.openclaw/workspace/.watchdog/calendar-sync-token.json"

def send_telegram(text):
    """Send alert to Ahmed via Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = json.dumps({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Telegram send failed: {e}", file=sys.stderr)

def get_changed_events():
    """Fetch recent/changed calendar events using gog"""
    try:
        # Get events for next 7 days
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=7)
        result = subprocess.run(
            ["/usr/local/bin/gog", "calendar", "events",
             "--account", "ahmednasr999@gmail.com",
             "--from", now.strftime("%Y-%m-%dT%H:%M:%SZ"),
             "--to", end.strftime("%Y-%m-%dT%H:%M:%SZ"),
             "--json"],
            capture_output=True, text=True, timeout=15,
            env={**os.environ, "GOG_KEYRING_PASSWORD": ""}
        )
        if result.returncode == 0:
            return result.stdout
        print(f"gog error: {result.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"gog fetch failed: {e}", file=sys.stderr)
        return None

def load_known_events():
    """Load previously known events for diffing"""
    try:
        with open(SYNC_TOKEN_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"events": {}, "last_check": None}

def save_known_events(data):
    """Save known events state"""
    os.makedirs(os.path.dirname(SYNC_TOKEN_FILE), exist_ok=True)
    with open(SYNC_TOKEN_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def diff_and_notify(events_json):
    """Compare with known events and notify on changes"""
    if not events_json:
        return

    try:
        events = json.loads(events_json)
    except json.JSONDecodeError:
        # gog may output non-JSON, try line parsing
        return

    known = load_known_events()
    known_events = known.get("events", {})
    new_state = {}
    notifications = []

    # Handle different gog output formats
    event_list = events if isinstance(events, list) else events.get("items", events.get("events", []))

    for event in event_list:
        if not isinstance(event, dict):
            continue
        eid = event.get("id", "")
        summary = event.get("summary", "No title")
        start = event.get("start", {})
        start_time = start.get("dateTime", start.get("date", ""))
        updated = event.get("updated", "")
        creator = event.get("creator", {}).get("email", "")

        # Build a hash of the event state
        event_hash = f"{summary}|{start_time}|{updated}"
        new_state[eid] = event_hash

        if eid not in known_events:
            # New event
            notifications.append(f"📅 <b>New event:</b> {summary}\n   {start_time}\n   By: {creator}")
        elif known_events[eid] != event_hash:
            # Changed event
            notifications.append(f"📝 <b>Updated:</b> {summary}\n   {start_time}")

    # Check for deleted events
    for eid in known_events:
        if eid not in new_state:
            notifications.append(f"❌ <b>Cancelled:</b> (event removed)")

    if notifications:
        msg = "🔔 <b>Calendar Update</b>\n\n" + "\n\n".join(notifications[:5])  # max 5
        send_telegram(msg)

    # Save new state
    save_known_events({
        "events": new_state,
        "last_check": datetime.now(timezone.utc).isoformat()
    })

class CalendarHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle Google Calendar push notification"""
        # Google sends minimal info in push; we need to fetch events ourselves
        channel_id = self.headers.get("X-Goog-Channel-ID", "")
        resource_state = self.headers.get("X-Goog-Resource-State", "")

        print(f"[{datetime.now()}] Push received: state={resource_state}, channel={channel_id}")

        if resource_state == "sync":
            # Initial sync confirmation, ignore
            self.send_response(200)
            self.end_headers()
            return

        # Fetch changed events and notify
        events = get_changed_events()
        diff_and_notify(events)

        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        """Health check"""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Calendar push receiver OK\n")

    def log_message(self, format, *args):
        print(f"[{datetime.now()}] {format % args}")

if __name__ == "__main__":
    print(f"Calendar push receiver starting on port {PORT}")
    server = http.server.HTTPServer(("127.0.0.1", PORT), CalendarHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down")
        server.shutdown()
