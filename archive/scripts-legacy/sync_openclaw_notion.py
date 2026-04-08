#!/usr/bin/env python3
"""
Sync OpenClaw to Notion - Complete folder mirroring
"""

from notion_client import Client
import os
from datetime import datetime

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
WORKSPACE = '/root/.openclaw/workspace'

# File mappings - where each OpenClaw file goes in Notion
FILE_MAPPINGS = {
    # Core files -> 📁 docs/
    'AGENTS.md': ('📁 docs', '📄'),
    'IDENTITY.md': ('📁 docs', '📄'),
    'USER.md': ('📁 docs', '📄'),
    'SOUL.md': ('📁 docs', '📄'),
    'TOOLS.md': ('📁 docs', '📄'),
    'MEMORY.md': ('📁 docs', '📄'),
    'HEARTBEAT.md': ('📁 docs', '📄'),
    
    # Coordination -> 📊 coordination/
    'dashboard.json': ('📊 coordination', '📊'),
    'pipeline.json': ('📊 coordination', '📊'),
    'content-calendar.json': ('📊 coordination', '📊'),
    'outreach-queue.json': ('📊 coordination', '📊'),
    
    # Daily Notes -> 📓 Daily Notes/
    '2026-02-15.md': ('📓 Daily Notes', '📓'),
    '2026-02-16.md': ('📓 Daily Notes', '📓'),
    '2026-02-17.md': ('📓 Daily Notes', '📓'),
    '2026-02-18.md': ('📓 Daily Notes', '📓'),
}

def find_command_center():
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

def get_all_pages():
    """Get all accessible pages"""
    try:
        results = notion.search(filter={'value': 'page', 'property': 'object'}, page_size=500)
        return results.get('results', [])
    except:
        return []

def find_page_id_by_title(title_substring, parent_id=None):
    """Find a page ID by partial title match"""
    pages = get_all_pages()
    for p in pages:
        p_title = p.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '')
        if title_substring in p_title:
            if parent_id is None or p.get('parent', {}).get('page_id') == parent_id:
                return p['id']
    return None

def read_file(filepath):
    """Read file content"""
    try:
        with open(filepath, 'r') as f:
            return f.read()[:10000]  # Limit to 10K chars
    except:
        return None

def sync_file_to_notion(filename, folder_mapping, parent_id):
    """Sync a single file to Notion"""
    folder_title, icon = folder_mapping
    folder_id = find_page_id_by_title(folder_title, parent_id)
    
    if not folder_id:
        print(f"  ❌ Folder not found: {folder_title}")
        return False
    
    # Read file content
    filepath = f"{WORKSPACE}/{filename.replace('📄 ', '').replace('📊 ', '').replace('📓 ', '')}"
    content = read_file(filepath)
    
    if not content:
        # Try alternate paths
        alt_paths = [
            f"{WORKSPACE}/{filename.split()[-1]}",
            f"{WORKSPACE}/coordination/{filename}",
            f"{WORKSPACE}/memory/{filename}",
        ]
        for alt in alt_paths:
            content = read_file(alt)
            if content:
                filepath = alt
                break
    
    if not content:
        print(f"  ⚠️ Could not read: {filename}")
        return False
    
    # Create page title
    page_title = f"{icon} {filename}"
    
    # Check if already exists
    existing = find_page_id_by_title(page_title, folder_id)
    
    try:
        if existing:
            print(f"  ⏭️  Exists: {filename}")
            return True
        
        # Create page
        page = notion.pages.create(
            parent={'page_id': folder_id},
            properties={'title': {'title': [{'text': {'content': page_title}}]}}
        )
        
        # Add content as blocks
        lines = content.strip().split('\n')[:50]
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
        
        print(f"  ✅ Synced: {filename} → {folder_title}")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {filename} - {str(e)[:50]}")
        return False

def main():
    print("="*70)
    print("🔄 SYNCING OPENCLAW TO NOTION")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Find Command Center
    command_center_id = find_command_center()
    if not command_center_id:
        print("❌ Could not find Nasr's Command Center")
        return
    
    print(f"✅ Found: Nasr's Command Center\n")
    
    # Sync files
    synced = 0
    failed = 0
    
    print("📤 Syncing files to Notion...")
    print("-"*50)
    
    for filename, mapping in FILE_MAPPINGS.items():
        if sync_file_to_notion(filename, mapping, command_center_id):
            synced += 1
        else:
            failed += 1
    
    print("-"*50)
    print(f"\n📊 SYNC COMPLETE")
    print(f"   Synced: {synced}")
    print(f"   Failed: {failed}")
    
    print("\n" + "="*70)
    print("✅ OPENCLAW → NOTION SYNC COMPLETE")
    print("="*70)

if __name__ == '__main__':
    main()
