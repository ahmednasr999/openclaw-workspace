#!/usr/bin/env python3
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

print("="*60)
print("SYNCING CORE FILES")
print("="*60)

files = ['MEMORY.md', 'IDENTITY.md', 'USER.md', 'SOUL.md', 'TOOLS.md', 'AGENTS.md', 'HEARTBEAT.md']
synced = 0

for filename in files:
    filepath = WORKSPACE + "/" + filename
    if not os.path.exists(filepath):
        print("  SKIP: %s not found" % filename)
        continue
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    title = "FILE: " + filename
    
    try:
        page = notion.pages.create(
            parent={'page_id': parent_id},
            properties={'title': {'title': [{'text': {'content': title}}]}}
        )
        
        lines = content.strip().split('\n')
        for i in range(0, len(lines), 10):
            chunk = lines[i:i+10]
            text = '\n'.join(chunk)
            if text.strip():
                try:
                    notion.blocks.children.append(page['id'], children=[
                        {'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': text[:1800]}}]}}
                    ])
                except:
                    pass
        
        print("  OK: %s" % filename)
        synced += 1
    except Exception as e:
        print("  ERR: %s - %s" % (filename, str(e)[:30]))

print("")
print("="*60)
print("DONE: %d/7 files synced" % synced)
print("="*60)
