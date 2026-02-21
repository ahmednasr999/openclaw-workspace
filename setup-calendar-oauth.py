#!/usr/bin/env python3
"""
Direct Google OAuth for Calendar API
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import uuid

# OAuth config
CLIENT_ID = "583018818639-4buj8s1j7bh3l5cqooejbbr8oko85mld.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REDIRECT_URI = "http://127.0.0.1:8080/oauth2callback"
SCOPES = "https://www.googleapis.com/auth/calendar"

def get_auth_url():
    """Generate OAuth authorization URL"""
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES,
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(code):
    """Exchange auth code for access token"""
    data = urllib.parse.urlencode({
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI
    }).encode()
    
    req = urllib.request.Request(
        'https://oauth2.googleapis.com/token',
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Token exchange failed: {e.read().decode()}")
        return None

def setup_calendar_watch(token_data):
    """Create calendar push notification watch"""
    access_token = token_data.get('access_token')
    if not access_token:
        print("No access token")
        return False
    
    channel_id = str(uuid.uuid4())
    webhook_url = "https://srv1352768.tail945bbc.ts.net:8790/calendar-webhook"
    
    data = json.dumps({
        "id": channel_id,
        "type": "web_hook",
        "address": webhook_url
    }).encode()
    
    req = urllib.request.Request(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events/watch",
        data=data,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            print(f"\n✅ Calendar watch created!")
            print(f"   Channel ID: {result.get('id')}")
            print(f"   Resource ID: {result.get('resourceId')}")
            print(f"   Expiration: {result.get('expiration')}")
            
            # Save token and watch info
            save_data = {
                "token": token_data,
                "watch": result,
                "webhook_url": webhook_url
            }
            
            with open('/root/.openclaw/workspace/calendar-auth.json', 'w') as f:
                json.dump(save_data, f, indent=2)
            
            return True
            
    except urllib.error.HTTPError as e:
        error = json.loads(e.read().decode())
        print(f"\n❌ Failed: {error.get('error', {}).get('message', 'Unknown error')}")
        return False

if __name__ == '__main__':
    print("=== Calendar Webhook Setup ===\n")
    
    if len(sys.argv) > 1:
        # Got auth code
        code = sys.argv[1]
        print(f"Exchanging code for token...")
        token_data = exchange_code_for_token(code)
        
        if token_data:
            print(f"✅ Got access token")
            print(f"Setting up calendar watch...")
            setup_calendar_watch(token_data)
        else:
            print("❌ Token exchange failed")
    else:
        # Show auth URL
        auth_url = get_auth_url()
        print("Step 1: Open this URL in Safari:\n")
        print(auth_url)
        print("\nStep 2: After authorizing, you'll get a 'localhost' URL that won't load.")
        print("Step 3: Copy the CODE from that URL (after 'code=' and before '&')")
        print("Step 4: Run: python3 setup-calendar-oauth.py 'PASTE_CODE_HERE'")
