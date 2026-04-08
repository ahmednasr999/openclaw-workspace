#!/usr/bin/env python3
"""
Incremental sync - creates files in correct folders, archives old ones
Works in batches to avoid timeouts
"""

from notion_client import Client
import os
from datetime import datetime

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
WORKSPACE = '/root/.openclaw/workspace'

# File to folder mapping
FILE_MAP = {
    # docs/
    'AGENTS.md': ('docs', '📄'),
    'IDENTITY.md': ('docs', '📄'),
    'USER.md': ('docs', '📄'),
    'SOUL.md': ('docs', '📄'),
    'TOOLS.md': ('docs', '📄'),
    'MEMORY.md': ('docs', '📄'),
    'HEARTBEAT.md': ('docs', '📄'),
    
    # coordination/
    'dashboard.json': ('coordination', '📊'),
    'pipeline.json': ('coordination', '📊'),
    'content-calendar.json': ('coordination', '📊'),
    'outreach-queue.json': ('coordination', '📊'),
}

def read_file(path):
    try:
        with open(path, 'r') as f:
            return f.read()[:5000]
    except:
        return None

def get_command_center_id():
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
    """Find folder ID by name"""
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

def find_page_by_title(title, parent_id=None):
    """Find a page by title"""
    try:
        results = notion.search(
            query=title.replace('.md', '').replace('.json', ''),
            filter={'value': 'page', 'property': 'object'},
            page_size=10
        )
        for r in results.get('results', []):
            ptitle = r.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '')
            if title in ptitle:
                if parent_id is None or r.get('parent', {}).get('page_id') == parent_id:
                    return r['id']
    except:
        pass
    return None

def sync_file(filename, folder_name, icon, command_center_id):
    """Sync one file to Notion"""
    folder_id = find_folder_id(folder_name, command_center_id)
    if not folder_id:
        return 'folder_not_found'
    
    # Check if already exists in folder
    page_title = f"{icon} {filename}"
    existing = find_page_by_title(page_title, folder_id)
    if existing:
        return 'exists'
    
    # Read file
    filepath = f"{WORKSPACE}/{filename}"
    content = read_file(filepath)
    if not content:
        return 'file_not_found'
    
    # Create page
    try:
        page = notion.pages.create(
            parent={'page_id': folder_id},
            properties={'title': {'title': [{'text': {'content': page_title}}]}}
        )
        
        # Add content
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
        
        return 'created'
    except Exception as e:
        return f'error: {str(e)[:30]}'

def archive_duplicate(filename, icon, command_center_id):
    """Archive old page at root level"""
    page_title = f"{icon} {filename}"
    old_id = find_page_by_title(page_title, command_center_id)
    if old_id:
        try:
            notion.pages.update(page_id=old_id, archived=True)
            return 'archived'
        except:
            return 'archive_failed'
    return 'not_found'

def main():
    print("="*70)
    print("🔄 INCREMENTAL SYNC - FILES TO FOLDERS")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    command_center_id = get_command_center_id()
    if not command_center_id:
        print("❌ Could not find Nasr's Command Center")
        return
    
    print(f"✅ Found: Nasr's Command Center\n")
    
    results = {'created': [], 'archived': [], 'exists': [], 'failed': []}
    
    # Process files
    for filename, (folder, icon) in FILE_MAP.items():
        print(f"Processing: {filename} -> {folder}/", end=" ")
        
        # Try to sync
        status = sync_file(filename, folder, icon, command_center_id)
        
        if status == 'created':
            print("✅ Created")
            results['created'].append(filename)
        elif status == 'exists':
            print("⏭️  Exists")
            results['exists'].append(filename)
        elif status == 'folder_not_found':
            print("❌ Folder not found")
            results['failed'].append(filename)
        else:
            print(f"❌ {status}")
            results['failed'].append(filename)
    
    print("\n" + "="*70)
    print("📊 SYNC RESULTS")
    print("="*70)
    print(f"Created: {len(results['created'])}")
    print(f"Exists: {len(results['exists'])}")
    print(f"Failed: {len(results['failed'])}")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    main()
