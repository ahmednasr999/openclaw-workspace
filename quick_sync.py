#!/usr/bin/env python3
"""
Quick sync: Core files only
Run this to sync the 7 essential files from OpenClaw to Notion
"""

from notion_client import Client
import os

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
WORKSPACE = '/root/.openclaw/workspace'

# Find Command Center
results = notion.search(query="Nasr's Command Center", filter={'value': 'page', 'property': 'object'}, page_size=5)
parent_id = None
for r in results.get('results', []):
    title = r.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '')
    if 'Command Center' in title:
        parent_id = r['id']
        break

if not parent_id:
    print("❌ Command Center not found")
    exit()

# Core files
FILES = ['MEMORY.md', 'IDENTITY.md', 'USER.md', 'SOUL.md', 'TOOLS.md', 'AGENTS.md', 'HEARTBEAT.md']

print("="*60)
print("SYNCING 7 CORE FILES")
print("="*60)

for filename in FILES:
    path = f"{WORKSPACE}/{filename}"
    if not os.path.exists(path):
        continue
    
    with open(path, 'r') as f:
        content = f.read()[:3000]
    
    # Create page
    try:
        page = notion.pages.create(
            parent={'page_id': parent_id},
            properties={'title': {'title': [{'text': {'content': f"📄 {filename}"}}]}}
        )
        
        for line in content.strip().split('\n')[:20]:
            if line.strip():
                try:
                    notion.blocks.children.append(
                        page['id'],
                        children=[{'object': 'block', 'type': 'paragraph',
                        'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': line}}]}}]
                    )
                except:
                    pass
        print(f"  ✅ {filename}")
    except Exception as e:
        print(f"  ❌ {filename}: {str(e)[:40]}")

print("\nDone!")
