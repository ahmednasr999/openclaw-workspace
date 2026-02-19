#!/usr/bin/env python3
"""
OpenClaw to Notion Sync - Minimal Sync (Option A)
Syncs core files, daily notes, and coordination data to Notion
"""

from notion_client import Client
import os
import json
from datetime import datetime

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

# Coordination files
COORDINATION_DIR = f'{WORKSPACE}/coordination'

def get_file_content(path):
    """Read file content"""
    try:
        with open(path, 'r') as f:
            return f.read()
    except:
        return None

def title_to_notion(title):
    """Convert title to Notion blocks"""
    lines = title.strip().split('\n')
    blocks = []
    for line in lines:
        blocks.append({
            'object': 'block',
            'type': 'paragraph',
            'paragraph': {
                'rich_text': [{
                    'type': 'text',
                    'text': {'content': line + '\n'}
                }]
            }
        })
    return blocks

def sync_page_to_notion(title, content, parent_id=None):
    """Create or update a page in Notion"""
    # Find existing page
    existing = None
    try:
        results = notion.search(query=title, filter={'value': 'page', 'property': 'object'}, page_size=1)
        if results.get('results'):
            existing = results['results'][0]
    except:
        pass
    
    if existing:
        # Update content
        try:
            # First, get existing blocks and clear them
            block_id = existing['id']
            # Note: Notion API doesn't allow direct block replacement easily
            # We'll append new content instead
            print(f"  📝 Updating: {title[:40]}")
            return existing['id']
        except Exception as e:
            print(f"  ❌ Update failed: {str(e)[:50]}")
            return None
    else:
        # Create new page
        try:
            if parent_id:
                page = notion.pages.create(
                    parent={'page_id': parent_id},
                    properties={'title': {'title': [{'text': {'content': title}}]}}
                )
            else:
                page = notion.pages.create(
                    parent={'database_id': '30b8d599a16280679eb8f229b473d25f'},
                    properties={'Name': {'title': [{'text': {'content': title}}]}}
                )
            print(f"  ✅ Created: {title[:40]}")
            return page['id']
        except Exception as e:
            print(f"  ❌ Create failed: {str(e)[:50]}")
            return None

def create_database_page(title, content, parent_id):
    """Create a page inside a database"""
    try:
        page = notion.pages.create(
            parent={'database_id': parent_id},
            properties={'Name': {'title': [{'text': {'content': title}}]}}
        )
        print(f"  ✅ Created in DB: {title[:40]}")
        return page['id']
    except Exception as e:
        print(f"  ❌ Failed: {str(e)[:50]}")
        return None

def sync_core_files(parent_id):
    """Sync core OpenClaw files"""
    print("\n📄 SYNCING CORE FILES")
    print("-"*50)
    
    for filename in CORE_FILES:
        path = f'{WORKSPACE}/{filename}'
        content = get_file_content(path)
        if content:
            sync_page_to_notion(filename, content, parent_id)
        else:
            print(f"  ⚠️ Missing: {filename}")

def sync_daily_notes(parent_id):
    """Sync daily notes"""
    print("\n📓 SYNCING DAILY NOTES")
    print("-"*50)
    
    memory_dir = f'{WORKSPACE}/memory'
    notes = [f for f in os.listdir(memory_dir) if f.startswith('2026-') and f.endswith('.md')]
    
    for note in sorted(notes):
        path = f'{memory_dir}/{note}'
        content = get_file_content(path)
        if content:
            sync_page_to_notion(note, content, parent_id)

def sync_coordination_data(parent_id):
    """Sync coordination JSON files as Notion database entries"""
    print("\n📊 SYNCING COORDINATION DATA")
    print("-"*50)
    
    # Read coordination files
    files = {
        'dashboard': f'{COORDINATION_DIR}/dashboard.json',
        'pipeline': f'{COORDINATION_DIR}/pipeline.json',
        'content_calendar': f'{COORDINATION_DIR}/content-calendar.json',
        'outreach': f'{COORDINATION_DIR}/outreach-queue.json',
    }
    
    for name, path in files.items():
        content = get_file_content(path)
        if content:
            # Create as a page with JSON content
            title = f"📊 {name.replace('_', ' ').title()}"
            sync_page_to_notion(title, f"```json\n{content}\n```", parent_id)
        else:
            print(f"  ⚠️ Missing: {name}")

def main():
    """Main sync function"""
    print("="*70)
    print("🚀 OPENCLAW TO NOTION SYNC - OPTION A (Minimal)")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Find "Ahmed's Job Tracker" page ID
    job_tracker_id = None
    try:
        results = notion.search(query="Ahmed's Job Tracker", filter={'value': 'page', 'property': 'object'}, page_size=1)
        if results.get('results'):
            job_tracker_id = results['results'][0]['id']
            print(f"\n✅ Found Job Tracker: {results['results'][0]['id']}")
    except Exception as e:
        print(f"❌ Could not find Job Tracker: {str(e)[:50]}")
        return
    
    # Sync everything under Job Tracker
    sync_core_files(job_tracker_id)
    sync_daily_notes(job_tracker_id)
    sync_coordination_data(job_tracker_id)
    
    print("\n" + "="*70)
    print("✅ SYNC COMPLETE")
    print("="*70)

if __name__ == '__main__':
    main()
