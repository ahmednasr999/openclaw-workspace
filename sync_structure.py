#!/usr/bin/env python3
"""
Sync OpenClaw structure to Notion - Simplified version
Creates pages with file listings, not full content
"""

from notion_client import Client
import os
from datetime import datetime

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
WORKSPACE = '/root/.openclaw/workspace'

# Folder structure to create in Notion
STRUCTURE = {
    '📁 docs': {
        'icon': '📄',
        'files': ['AGENTS.md', 'IDENTITY.md', 'USER.md', 'SOUL.md', 'TOOLS.md', 'MEMORY.md', 'HEARTBEAT.md'],
        'path': WORKSPACE
    },
    '📊 coordination': {
        'icon': '📊',
        'files': ['dashboard.json', 'pipeline.json', 'content-calendar.json', 'outreach-queue.json'],
        'path': f'{WORKSPACE}/coordination'
    },
    '📓 Daily Notes': {
        'icon': '📓',
        'files': [],  # Will list from memory/
        'path': f'{WORKSPACE}/memory'
    },
    '📁 skills': {
        'icon': '🛠️',
        'files': [],  # Will list from skills/
        'path': f'{WORKSPACE}/skills'
    },
    '📁 agents': {
        'icon': '🤖',
        'files': [],  # Will list from agents/
        'path': f'{WORKSPACE}/agents'
    },
    '📁 knowledge-base': {
        'icon': '🧠',
        'files': [],  # Will list from knowledge-base/
        'path': f'{WORKSPACE}/knowledge-base'
    },
    '📈 marketing-skills': {
        'icon': '📈',
        'files': [],  # Will list from marketing-skills/
        'path': f'{WORKSPACE}/marketing-skills'
    },
    '📁 healthtech-directory': {
        'icon': '🏥',
        'files': [],  # Will list from healthtech-directory/
        'path': f'{WORKSPACE}/healthtech-directory'
    },
}

def find_command_center():
    try:
        results = notion.search(query="Nasr's Command Center", filter={'value': 'page', 'property': 'object'}, page_size=5)
        for r in results.get('results', []):
            title = r.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '')
            if 'Command Center' in title:
                return r['id']
    except:
        pass
    return None

def list_files(path, extensions=('.md', '.py', '.json', '.csv')):
    try:
        files = []
        for f in sorted(os.listdir(path)):
            if f.startswith('.') or f == '__pycache__':
                continue
            if f.endswith(extensions):
                files.append(f"• {f}")
        return '\n'.join(files[:20])  # Limit to 20
    except:
        return "Unable to read"

def create_page(title, icon, content, parent_id):
    """Create a page with content"""
    full_title = f"{icon} {title}" if icon else title
    try:
        page = notion.pages.create(
            parent={'page_id': parent_id},
            properties={'title': {'title': [{'text': {'content': full_title}}]}}
        )
        
        # Add content
        lines = content.strip().split('\n')[:30]
        for line in lines:
            if line.strip():
                try:
                    notion.blocks.children.append(
                        page['id'],
                        children=[{'object': 'block', 'type': 'paragraph', 
                        'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': line}}]}}]
                    )
                except:
                    pass
        return True
    except Exception as e:
        print(f"  ❌ {title}: {str(e)[:40]}")
        return False

def main():
    print("="*70)
    print("🔄 SYNCING OPENCLAW STRUCTURE TO NOTION")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    parent_id = find_command_center()
    if not parent_id:
        print("❌ Could not find Nasr's Command Center")
        return
    
    print(f"✅ Found: Nasr's Command Center\n")
    
    created = 0
    
    for folder_name, info in STRUCTURE.items():
        icon = info['icon']
        path = info['path']
        files = info['files']
        
        # Get files from path if not specified
        if not files:
            files = list_files(path)
        
        content = f"""
# {folder_name}

## Files in this folder

{files}

---
*Synced from OpenClaw: {datetime.now().strftime('%Y-%m-%d')}*
"""
        
        if create_page(folder_name, icon, content, parent_id):
            print(f"  ✅ {folder_name}")
            created += 1
    
    print("\n" + "="*70)
    print(f"✅ CREATED {created} FOLDER PAGES")
    print("="*70)
    print("""
Files are listed in each folder.
Full content sync available on demand.
""")

if __name__ == '__main__':
    main()
