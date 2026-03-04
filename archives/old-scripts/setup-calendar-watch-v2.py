#!/usr/bin/env python3
"""
Setup Calendar Watch using gog's authentication
"""

import os
import sys
import json
import subprocess
import urllib.request
import uuid

# Get token using gog's credential helper
def get_gog_token():
    """Get OAuth token from gog's keyring"""
    try:
        # Try to use gog's credential helper
        env = os.environ.copy()
        env['GOG_KEYRING_PASSWORD'] = 'pass@123'
        
        # Use gog to get an access token
        result = subprocess.run(
            ['gog', 'auth', 'token', 'ahmednasr999@gmail.com'],
            capture_output=True,
            text=True,
            env=env
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
            
        # Alternative: try to use gog's internal storage
        # Check if there's a way to extract the token
        result = subprocess.run(
            ['cat', '/root/.config/gogcli/credentials.json'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            creds = json.loads(result.stdout)
            # Look for calendar token
            for client_name, client_data in creds.get('clients', {}).items():
                for account_name, account_data in client_data.get('accounts', {}).items():
                    if account_name == 'ahmednasr999@gmail.com':
                        tokens = account_data.get('tokens', {})
                        return tokens.get('access_token')
                        
    except Exception as e:
        print(f"Error getting token: {e}")
    
    return None

def setup_watch_with_token(token):
    """Create calendar watch with the token"""
    if not token:
        print("No token available")
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
            print(f"   Expiration: {result.get('expiration')}")
            
            # Save watch info
            watch_info = {
                "account": "ahmednasr999@gmail.com",
                "channel_id": result.get('id'),
                "resource_id": result.get('resourceId'),
                "expiration": result.get('expiration'),
                "webhook_url": webhook_url
            }
            
            os.makedirs('/root/.config/gogcli/state/calendar-watch', exist_ok=True)
            with open('/root/.config/gogcli/state/calendar-watch/ahmednasr999_gmail_com.json', 'w') as f:
                json.dump(watch_info, f, indent=2)
            
            return True
            
    except urllib.error.HTTPError as e:
        error = e.read().decode()
        print(f"❌ HTTP {e.code}: {error}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    print("Getting gog token...")
    token = get_gog_token()
    
    if token:
        print(f"Token found: {token[:20]}...")
        print("\nSetting up calendar watch...")
        setup_watch_with_token(token)
    else:
        print("❌ Could not get token from gog")
        print("Alternative: Use service account or re-authenticate")
