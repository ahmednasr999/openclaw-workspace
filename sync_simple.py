#!/usr/bin/env python3
"""
OpenClaw to Notion Sync - Simple Sequential Version
Syncs core files one at a time with proper error handling
"""

from notion_client import Client
import os
import time

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
WORKSPACE = '/root/.openclaw/workspace'

# Core files to sync
CORE_FILES = [
    'MEMORY.md',
    'IDENTITY.md', 
    'USER.md',
    'SOUL.md',
    'TOOLS.md',
    'AGENTS.md',
    'HEARTBEAT.md',
]

def read_file(path):
    try:
        with open(path, 'r') as f:
            return f.read()[:5000]  # Limit to 5K chars
    except:
        return None

def create_page(title, content, parent_id):
    """Create a page in Notion"""
    try:
        page = notion.pages.create(
            parent={'page_id': parent_id},
            properties={'title': {'title': [{'text': {'content': title}}]}}
        )
        return page['id']
    except Exception as e:
        print(f"    ❌ Failed: {str(e)[:50]}")
        return None

def add_content(page_id, content):
    """Add content blocks to a page"""
    try:
        lines = content.strip().split('\n')[:50]  # Limit lines
        for line in lines:
            if line.strip():
                notion.blocks.children.append(
                    page_id,
                    children=[{
                        'object': 'block',
                        'type': 'paragraph',
                        'paragraph': {
                            'rich_text': [{'type': 'text', 'text': {'content': line}}]
                        }
                    }]
                )
                time.sleep(0.2)  # Rate limit
        return True
    except Exception as e:
        print(f"    ⚠️ Content failed: {str(e)[:30]}")
        return True  # Page created, content optional

def find_job_tracker():
    """Find Ahmed's Job Tracker page ID"""
    try:
        results = notion.search(
            query="Ahmed's Job Tracker",
            filter={'value': 'page', 'property': 'object'},
            page_size=5
        )
        for r in results.get('results', []):
            title = r.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '')
            if 'Job Tracker' in title:
                return r['id']
    except Exception as e:
        print(f"❌ Find failed: {str(e)[:50]}")
    return None

def sync():
    print("="*60)
    print("🚀 OPENCLAW → NOTION SYNC")
    print("="*60)
    
    # Find parent
    parent_id = find_job_tracker()
    if not parent_id:
        print("❌ Could not find Job Tracker")
        return
    print(f"✅ Parent: Ahmed's Job Tracker\n")
    
    # Sync core files
    print("📄 CORE FILES")
    for filename in CORE_FILES:
        path = f'{WORKSPACE}/{filename}'
        content = read_file(path)
        if content:
            print(f"  Creating: {filename}...", end=" ")
            page_id = create_page(filename, content, parent_id)
            if page_id:
                print("✅")
                add_content(page_id, content)
        else:
            print(f"  ⚠️ Missing: {filename}")
        time.sleep(0.5)
    
    # Sync daily notes
    print("\n📓 DAILY NOTES")
    memory_dir = f'{WORKSPACE}/memory'
    notes = sorted([f for f in os.listdir(memory_dir) if f.startswith('2026-') and f.endswith('.md')])
    for note in notes[-5:]:  # Last 5 notes
        path = f'{memory_dir}/{note}'
        content = read_file(path)
        if content:
            print(f"  Creating: {note}...", end=" ")
            page_id = create_page(note, content, parent_id)
            if page_id:
                print("✅")
                add_content(page_id, content)
        time.sleep(0.5)
    
    # Sync coordination
    print("\n📊 COORDINATION")
    coord_dir = f'{WORKSPACE}/coordination'
    files = ['dashboard.json', 'pipeline.json', 'content-calendar.json']
    for f in files:
        path = f'{coord_dir}/{f}'
        content = read_file(path)
        if content:
            title = f"📊 {f.replace('.json', '').replace('_', ' ').title()}"
            print(f"  Creating: {title}...", end=" ")
            page_id = create_page(title, content, parent_id)
            if page_id:
                print("✅")
        time.sleep(0.5)
    
    print("\n" + "="*60)
    print("✅ SYNC COMPLETE")
    print("="*60)

if __name__ == '__main__':
    sync()
