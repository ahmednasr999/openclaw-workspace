#!/usr/bin/env python3
"""
Gmail OAuth Authenticator - Alternative method
Uses Google OAuth device flow
"""
import json
import os
import time
import webbrowser
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system("pip install requests")
    import requests

# Configuration - Use environment variables or defaults (override via env vars)
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "your-client-id.apps.googleusercontent.com")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "your-client-secret")
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

def get_device_code():
    """Get device code for OAuth"""
    url = "https://oauth2.googleapis.com/device/code"
    data = {
        "client_id": CLIENT_ID,
        "scope": " ".join(SCOPES)
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.text}")
        return None

def exchange_code(code):
    """Exchange device code for tokens"""
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "http://oauth.net/grant_type/device/1"
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.text}")
        return None

def main():
    print("=" * 60)
    print("Gmail OAuth Setup")
    print("=" * 60)
    print()
    
    # Step 1: Get device code
    print("Step 1: Getting device code...")
    device_data = get_device_code()
    
    if not device_data:
        print("❌ Failed to get device code")
        return
    
    print("✅ Got device code")
    print()
    
    # Step 2: Show instructions
    print("Step 2: Complete authentication")
    print()
    print(f"📱 Visit: {device_data['verification_url']}")
    print(f"🔑 Enter code: {device_data['user_code']}")
    print()
    
    # Open browser
    try:
        webbrowser.open(device_data['verification_url'])
        print("✅ Opened browser")
    except:
        print("⚠️  Could not open browser automatically")
    
    print()
    print("Waiting for authentication...")
    print("(Press Ctrl+C to cancel)")
    print()
    
    # Step 3: Poll for token
    print("Step 3: Waiting for authentication...")
    interval = device_data.get('interval', 5)
    expires_in = device_data.get('expires_in', 1800)
    start_time = time.time()
    
    while time.time() - start_time < expires_in:
        time.sleep(interval)
        tokens = exchange_code(device_data['device_code'])
        
        if tokens:
            print()
            print("✅ Authentication successful!")
            print()
            print("Tokens received:")
            print(json.dumps(tokens, indent=2))
            return tokens
        
        print(".", end="", flush=True)
    
    print()
    print("❌ Authentication timed out")
    return None

if __name__ == "__main__":
    main()
