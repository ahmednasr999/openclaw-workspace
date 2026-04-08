#!/usr/bin/env python3
"""
Setup Google Calendar Watch
Creates a push notification channel for calendar changes
"""

import os
import sys
import json
import subprocess

# Config
PROJECT_ID = "openclaw-automation-487610"
ACCOUNT = "ahmednasr999@gmail.com"
WEBHOOK_URL = "https://srv1352768.tail945bbc.ts.net/calendar-pubsub"
CALENDAR_ID = "primary"

def get_access_token():
    """Get OAuth access token from gcloud"""
    try:
        result = subprocess.run(
            ['gcloud', 'auth', 'print-access-token'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"Error getting token: {e}")
    return None

def setup_calendar_watch():
    """Create a watch channel for calendar changes"""
    token = get_access_token()
    if not token:
        print("Failed to get access token. Run: gcloud auth login")
        return False
    
    import urllib.request
    import uuid
    
    channel_id = str(uuid.uuid4())
    
    # Create watch request
    data = json.dumps({
        "id": channel_id,
        "type": "web_hook",
        "address": WEBHOOK_URL
    }).encode()
    
    req = urllib.request.Request(
        f"https://www.googleapis.com/calendar/v3/calendars/{CALENDAR_ID}/events/watch",
        data=data,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            print(f"✅ Calendar watch created!")
            print(f"   Channel ID: {result.get('id')}")
            print(f"   Resource ID: {result.get('resourceId')}")
            print(f"   Expiration: {result.get('expiration')}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ Failed to create watch: {e.code}")
        print(f"   Error: {error_body}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    print("Setting up Google Calendar watch...")
    print(f"Calendar: {CALENDAR_ID}")
    print(f"Webhook: {WEBHOOK_URL}")
    print()
    
    if setup_calendar_watch():
        print("\n✅ Calendar webhook is ready!")
        print("Calendar changes will now trigger instant notifications.")
    else:
        print("\n❌ Setup failed. Check errors above.")
        sys.exit(1)
