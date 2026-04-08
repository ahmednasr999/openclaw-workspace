#!/usr/bin/env python3
"""
Google Docs creator using direct API calls.
Bypasses gog CLI keyring encryption issue on headless VPS.
Uses refresh token from config/ahmed-google.json.

Usage: python3 scripts/gdocs-create.py <title> <file_path>
"""
import json, sys, urllib.request, urllib.parse, os

def get_access_token():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ahmed-google.json')
    with open(config_path) as f:
        creds = json.load(f)
    
    data = urllib.parse.urlencode({
        'client_id': creds['client_id'],
        'client_secret': creds['client_secret'],
        'refresh_token': creds['refresh_token'],
        'grant_type': 'refresh_token'
    }).encode()
    
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())['access_token']

def create_doc(title, content, access_token):
    # Create doc
    create_body = json.dumps({"title": title}).encode()
    req = urllib.request.Request(
        'https://docs.googleapis.com/v1/documents',
        data=create_body,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    )
    resp = urllib.request.urlopen(req)
    doc = json.loads(resp.read())
    doc_id = doc['documentId']
    
    # Insert content
    insert_body = json.dumps({
        "requests": [{
            "insertText": {
                "location": {"index": 1},
                "text": content
            }
        }]
    }).encode()
    
    req = urllib.request.Request(
        f'https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate',
        data=insert_body,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    )
    urllib.request.urlopen(req)
    return doc_id

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 gdocs-create.py <title> <file_path>")
        sys.exit(1)
    
    title = sys.argv[1]
    file_path = sys.argv[2]
    
    with open(file_path) as f:
        content = f.read()
    
    token = get_access_token()
    doc_id = create_doc(title, content, token)
    print(f"https://docs.google.com/document/d/{doc_id}/edit")
