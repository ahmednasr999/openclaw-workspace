#!/usr/bin/env python3
"""
Gmail Draft Creator - Uses Google API directly with saved credentials
"""
import json
import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configuration
CREDENTIALS_FILE = "/root/.config/gogcli/credentials.json"
TOKEN_FILE = "/root/.config/gogcli/keyring/token:ahmednasr999@gmail.com.backup"
SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

def decode_token(token_file):
    """Decode the JWT token file"""
    try:
        with open(token_file, 'r') as f:
            token = f.read().strip()
        
        # It's a JWT - split and decode
        parts = token.split('.')
        if len(parts) >= 2:
            # Decode payload
            payload = parts[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
            
            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

def create_gmail_service():
    """Create Gmail service with credentials"""
    # Load client secrets
    with open(CREDENTIALS_FILE, 'r') as f:
        client_config = json.load(f)
    
    # Check for existing token
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        # Need to do OAuth flow
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save for later
        with open('token.json', 'w') as f:
            f.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

def main():
    print("=" * 60)
    print("Gmail Draft Creator - Direct API")
    print("=" * 60)
    print()
    
    # Check files
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Credentials not found: {CREDENTIALS_FILE}")
        return
    
    if not os.path.exists(TOKEN_FILE):
        print(f"❌ Token not found: {TOKEN_FILE}")
        return
    
    print(f"✅ Found credentials: {CREDENTIALS_FILE}")
    print(f"✅ Found token: {TOKEN_FILE}")
    print()
    
    # Decode token
    token_info = decode_token(TOKEN_FILE)
    if token_info:
        print("Token info:")
        print(f"  Email: {token_info.get('email', 'unknown')}")
        print(f"  Expiry: {token_info.get('expiry', 'unknown')}")
        print()
    
    # Try to create service
    try:
        service = create_gmail_service()
        print("✅ Gmail service created!")
        print()
        print("Ready to create drafts...")
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Need to complete OAuth flow manually:")
        print("1. gog auth add you@gmail.com --services gmail")
        print("2. Complete in browser")
        print("3. Then run this script")

if __name__ == "__main__":
    main()
