#!/usr/bin/env python3
"""
Full Sync: OpenClaw → Notion
Mirrors entire workspace structure
"""

from notion_client import Client
import os
import json
from datetime import datetime

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
WORKSPACE = '/root/.openclaw/workspace'

# File mappings - OpenClaw paths to Notion destinations
FILE_MAPPINGS = {
    # Core files -> docs/
    'MEMORY.md': ('docs', '📄'),
    'IDENTITY.md': ('docs', '📄'),
    'USER.md': ('docs', '📄'),
    'SOUL.md': ('docs', '📄'),
    'TOOLS.md': ('docs', '📄'),
    'AGENTS.md': ('docs', '📄'),
    'HEARTBEAT.md': ('docs', '📄'),
    
    # Coordination files
    'coordination/dashboard.json': ('coordination', '📊'),
    'coordination/pipeline.json': ('coordination', '📊'),
    'coordination/content-calendar.json': ('coordination', '📊'),
    'coordination/outreach-queue.json': ('coordination', '📊'),
}

# Folder structures
OPENCLAW_FOLDERS = {
    'docs': {
        'icon': '📁',
        'files': ['MEMORY.md', 'IDENTITY.md', 'USER.md', 'SOUL.md', 'TOOLS.md', 'AGENTS.md', 'HEARTBEAT.md']
    },
    'coordination': {
        'icon': '📊',
        'files': ['dashboard.json', 'pipeline.json', 'content-calendar.json', 'outreach-queue.json']
    },
    'memory': {
        'icon': '📓',
        'files': []  # Will scan
    },
    'agents': {
        'icon': '🤖',
        'files': []  # Will scan
    },
    'skills': {
        'icon': '🛠️',
        'files': []  # Will scan
    },
    'knowledge-base': {
        'icon': '🧠',
        'files': []  # Will scan
    },
    'marketing-skills': {
        'icon': '📈',
        'files': []  # Will scan
    },
    'healthtech-directory': {
        'icon': '🏥',
        'files': []  # Will scan
    },
}

def get_command_center_id():
    """Find Nasr's Command Center"""
    try:
        results = notion.search(
            query="Nasr's Command Center",
            filter={'value': 'page', 'property': 'object'},
            page_size=5
        )
        for r in results.get('results', []):
            title = r.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '')
            if 'Command Center' in title:
                return r['id']
    except:
        pass
    return None

def find_folder_id(folder_name, parent_id):
    """Find a folder page ID"""
    try:
        results = notion.search(
            query=folder_name,
            filter={'value': 'page', 'property': 'object'},
            page_size=10
        )
        for r in results.get('results', []):
            ptitle = r.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '')
            if folder_name in ptitle and r.get('parent', {}).get('page_id') == parent_id:
                return r['id']
    except:
        pass
    return None

def create_folder(folder_name, icon, parent_id):
    """Create a folder page"""
    try:
        page = notion.pages.create(
            parent={'page_id': parent_id},
            properties={'title': {'title': [{'text': {'content': f"{icon} {folder_name}"}}]}}
        )
        return page['id']
    except Exception as e:
        print(f"  ❌ Failed to create {folder_name}: {str(e)[:50]}")
        return None

def read_file(filepath):
    """Read file content"""
    try:
        with open(filepath, 'r') as f:
            return f.read()[:5000]  # Limit for API
    except:
        return None

def create_page(title, content, folder_id, icon=''):
    """Create a page in Notion"""
    try:
        full_title = f"{icon} {title}" if icon else title
        
        # Check if exists
        results = notion.search(query=title, filter={'value': 'page', 'property': 'object'}, page_size=5)
        for r in results.get('results', []):
            ptitle = r.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '')
            if title in ptitle and r.get('parent', {}).get('page_id') == folder_id:
                return r['id'], 'exists'
        
        # Create page
        page = notion.pages.create(
            parent={'page_id': folder_id},
            properties={'title': {'title': [{'text': {'content': full_title}}]}}
        )
        
        # Add content
        if content:
            lines = content.strip().split('\n')[:30]
            for line in lines:
                if line.strip():
                    try:
                        notion.blocks.children.append(
                            page['id'],
                            children=[{
                                'object': 'block',
                                'type': 'paragraph',
                                'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': line}}]}
                            }]
                        )
                    except:
                        pass
        
        return page['id'], 'created'
    except Exception as e:
        return None, f'error: {str(e)[:50]}'

def scan_folder(path, extensions=('.md', '.py', '.json', '.csv')):
    """Scan folder and return files"""
    files = []
    try:
        for f in sorted(os.listdir(path)):
            if f.startswith('.') or f == '__pycache__':
                continue
            full_path = os.path.join(path, f)
            if os.path.isfile(full_path) and f.endswith(extensions):
                files.append(f)
    except:
        pass
    return files

def main():
    print("="*70)
    print("🔄 FULL SYNC: OPENCLAW → NOTION")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Find Command Center
    command_center_id = get_command_center_id()
    if not command_center_id:
        print("❌ Could not find Nasr's Command Center")
        return
    
    print(f"✅ Found: Nasr's Command Center\n")
    
    results = {'created': 0, 'exists': 0, 'failed': 0, 'folders_created': 0}
    
    # Step 1: Ensure all folders exist
    print("📁 CREATING FOLDERS")
    print("-"*50)
    
    folder_ids = {}
    for folder_name, info in OPENCLAW_FOLDERS.items():
        icon = info['icon']
        folder_id = find_folder_id(folder_name, command_center_id)
        if folder_id:
            print(f"  ✅ {icon} {folder_name} (exists)")
            folder_ids[folder_name] = folder_id
        else:
            new_id = create_folder(folder_name, icon, command_center_id)
            if new_id:
                folder_ids[folder_name] = new_id
                print(f"  ✅ Created: {icon} {folder_name}")
                results['folders_created'] += 1
            else:
                print(f"  ❌ Failed: {folder_name}")
    
    # Step 2: Sync files
    print("\n📄 SYNCING FILES")
    print("-"*50)
    
    for folder_name, info in OPENCLAW_FOLDERS.items():
        folder_path = f"{WORKSPACE}/{folder_name}"
        icon = info['icon']
        files = info['files']
        
        # Scan folder if no explicit files
        if not files:
            files = scan_folder(folder_path)
        
        if not files:
            print(f"  📁 {folder_name}: No files found")
            continue
        
        folder_id = folder_ids.get(folder_name)
        if not folder_id:
            print(f"  ❌ {folder_name}: Folder not found")
            continue
        
        print(f"\n  📁 {folder_name}:")
        
        for filename in files:
            filepath = f"{folder_path}/{filename}"
            content = read_file(filepath)
            
            if not content:
                continue
            
            page_id, status = create_page(filename, content, folder_id, icon)
            
            if status == 'created':
                print(f"    ✅ {filename}")
                results['created'] += 1
            elif status == 'exists':
                print(f"    ⏭️  {filename} (exists)")
                results['exists'] += 1
            else:
                print(f"    ❌ {filename}: {status}")
                results['failed'] += 1
    
    # Summary
    print("\n" + "="*70)
    print("📊 FULL SYNC COMPLETE")
    print("="*70)
    print(f"""
Folders Created: {results['folders_created']}
Pages Created: {results['created']}
Pages Existed: {results['exists']}
Failed: {results['failed']}
""")
    print("="*70)

if __name__ == '__main__':
    main()
