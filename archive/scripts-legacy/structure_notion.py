#!/usr/bin/env python3
"""
Create Notion structure to match OpenClaw exactly
"""

from notion_client import Client
import os
from datetime import datetime

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
WORKSPACE = '/root/.openclaw/workspace'

# OpenClaw folder structure to mirror
OPENCLAW_STRUCTURE = {
    'agents': {
        'icon': '🤖',
        'subfolders': ['chief-of-staff']
    },
    'coordination': {
        'icon': '📊',
        'subfolders': []
    },
    'knowledge-base': {
        'icon': '🧠',
        'subfolders': []
    },
    'memory': {
        'icon': '📓',
        'subfolders': ['agents', 'projects', 'reference']
    },
    'scripts': {
        'icon': '⚙️',
        'subfolders': []
    },
    'skills': {
        'icon': '🛠️',
        'subfolders': []
    },
    'marketing-skills': {
        'icon': '📈',
        'subfolders': []
    },
    'healthtech-directory': {
        'icon': '🏥',
        'subfolders': ['data', 'outreach', 'research']
    },
    'cvs': {
        'icon': '📄',
        'subfolders': []
    },
    'tools': {
        'icon': '🔧',
        'subfolders': []
    },
    'docs': {
        'icon': '📚',
        'subfolders': []
    }
}

def get_page_title(page):
    try:
        return page.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', 'Untitled')
    except:
        return 'Untitled'

def find_command_center():
    """Find Nasr's Command Center"""
    try:
        results = notion.search(
            query="Nasr's Command Center",
            filter={'value': 'page', 'property': 'object'},
            page_size=5
        )
        for r in results.get('results', []):
            if 'Command Center' in get_page_title(r):
                return r['id']
    except:
        pass
    return None

def create_page(title, parent_id, icon=''):
    """Create a page in Notion"""
    try:
        full_title = f"{icon} {title}" if icon else title
        page = notion.pages.create(
            parent={'page_id': parent_id},
            properties={'title': {'title': [{'text': {'content': full_title}}]}}
        )
        return page['id']
    except Exception as e:
        print(f"  ❌ Failed to create {title}: {str(e)[:50]}")
        return None

def list_files_recursive(path, max_depth=3, depth=0):
    """List files recursively"""
    items = []
    try:
        for item in sorted(os.listdir(path)):
            if item.startswith('.') or item in ['__pycache__', '.git', 'node_modules']:
                continue
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                if depth < max_depth:
                    items.append(('folder', item, full_path))
                    items.extend(list_files_recursive(full_path, max_depth, depth + 1))
            elif item.endswith(('.md', '.py', '.json', '.csv')):
                items.append(('file', item, full_path))
    except:
        pass
    return items

def main():
    print("="*70)
    print("🏗️  CREATING NOTION STRUCTURE - MIRRORING OPENCLAW")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Find Command Center
    command_center_id = find_command_center()
    if not command_center_id:
        print("❌ Could not find Nasr's Command Center")
        return
    
    print(f"✅ Found: Nasr's Command Center\n")
    
    # Create folder structure
    created_count = 0
    
    for folder_name, info in OPENCLAW_STRUCTURE.items():
        folder_path = f"{WORKSPACE}/{folder_name}"
        icon = info['icon']
        subfolders = info['subfolders']
        
        # Create main folder
        print(f"📁 Creating: {icon} {folder_name}")
        folder_id = create_page(folder_name, command_center_id, icon)
        
        if folder_id:
            created_count += 1
            
            # Create subfolders
            for subfolder in subfolders:
                sub_path = f"{folder_path}/{subfolder}"
                sub_icon = '📂'
                print(f"  ├── Creating: {sub_icon} {subfolder}")
                sub_id = create_page(subfolder, folder_id, sub_icon)
                if sub_id:
                    created_count += 1
        else:
            print(f"  ⚠️  Folder exists or failed")
    
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"\nCreated {created_count} folder pages")
    print(f"\nNext steps:")
    print(f"  1. Move existing pages into folders")
    print(f"  2. Add content descriptions to each folder")
    print(f"  3. Sync files from OpenClaw")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    main()
