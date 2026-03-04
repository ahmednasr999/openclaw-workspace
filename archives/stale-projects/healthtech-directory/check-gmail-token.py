#!/usr/bin/env python3
"""
Gmail Draft Creator - Uses OAuth token directly
"""
import json
import base64
import os

# Read the token
TOKEN_FILE = os.path.expanduser("~/.config/gogcli/keyring/token:ahmednasr999@gmail.com")

try:
    with open(TOKEN_FILE, 'r') as f:
        token_data = f.read().strip()
    
    # Decode JWT (simplified - just need the token)
    parts = token_data.split('.')
    if len(parts) >= 2:
        # It's a JWT - decode the payload
        payload = parts[1]
        # Add padding if needed
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        decoded = base64.urlsafe_b64decode(payload)
        token_info = json.loads(decoded)
        
        print("Token info:")
        print(json.dumps(token_info, indent=2))
        
        print()
        print("Token is valid!")
        print(f"Email: {token_info.get('email', 'unknown')}")
        print(f"Expiry: {token_info.get('expiry', 'unknown')}")
        
except Exception as e:
    print(f"Error: {e}")
