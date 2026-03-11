#!/usr/bin/env python3
"""
Create top-level folder pages in Notion to mirror OpenClaw structure
"""

from notion_client import Client
import os
import json
from datetime import datetime

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
WORKSPACE = '/root/.openclaw/workspace'

FOLDERS = {
    'agents': {
        'icon': '🤖',
        'description': 'AI agent definitions and configurations',
        'path': f'{WORKSPACE}/agents'
    },
    'coordination': {
        'icon': '📊',
        'description': 'Dashboard, pipeline, content calendar, outreach queue',
        'path': f'{WORKSPACE}/coordination'
    },
    'knowledge-base': {
        'icon': '🧠',
        'description': 'CRM, daily briefing, model cost tracking, urgent email',
        'path': f'{WORKSPACE}/knowledge-base'
    },
    'memory': {
        'icon': '📓',
        'description': 'Daily notes, active tasks, lessons learned, master CV',
        'path': f'{WORKSPACE}/memory'
    },
    'scripts': {
        'icon': '⚙️',
        'description': 'Git autosync, platform health, security core',
        'path': f'{WORKSPACE}/scripts'
    },
    'skills': {
        'icon': '🛠️',
        'description': '50+ installed skills (notion, linkedin, github, etc.)',
        'path': f'{WORKSPACE}/skills'
    },
    'marketing-skills': {
        'icon': '📈',
        'description': 'LinkedIn positioning, transformation consulting frameworks',
        'path': f'{WORKSPACE}/marketing-skills'
    },
}

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
    except:
        pass
    return None

def list_files(path, max_files=15):
    """List files in a directory"""
    try:
        files = []
        for f in sorted(os.listdir(path)):
            if f.startswith('.') or f == 'node_modules':
                continue
            full_path = os.path.join(path, f)
            if os.path.isdir(full_path):
                files.append(f"📁 {f}/")
            elif f.endswith(('.md', '.py', '.json', '.csv')):
                files.append(f"📄 {f}")
        return files[:max_files]
    except:
        return []

def create_folder_page(folder_name, info, parent_id):
    """Create a Notion page for a folder"""
    # Check if exists
    try:
        results = notion.search(
            query=f"{info['icon']} {folder_name}",
            filter={'value': 'page', 'property': 'object'},
            page_size=5
        )
        for r in results.get('results', []):
            parent = r.get('parent', {}).get('page_id')
            if parent == parent_id:
                print(f"  ⏭️  Exists: {info['icon']} {folder_name}")
                return r['id']
    except:
        pass
    
    # Get file listing
    files = list_files(info['path'])
    file_list = '\n'.join([f'• {f}' for f in files])
    
    content = f"""# {info['icon']} {folder_name.upper()}

**Path:** `{info['path']}`

## Description
{info['description']}

## Files & Subfolders
{file_list}

---
*Auto-generated from OpenClaw workspace*
"""
    
    try:
        page = notion.pages.create(
            parent={'page_id': parent_id},
            properties={'title': {'title': [{'text': {'content': f"{info['icon']} {folder_name}"}}]}}
        )
        
        # Add content
        lines = content.strip().split('\n')[:40]
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
        
        print(f"  ✅ Created: {info['icon']} {folder_name}")
        return page['id']
    except Exception as e:
        print(f"  ❌ Failed: {info['icon']} {folder_name} - {str(e)[:40]}")
        return None

def main():
    print("="*70)
    print("🏗️  CREATING NOTION FOLDER STRUCTURE")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    parent_id = find_job_tracker()
    if not parent_id:
        print("❌ Could not find Ahmed's Job Tracker")
        return
    
    print(f"✅ Parent: Ahmed's Job Tracker\n")
    
    created = 0
    for folder_name, info in FOLDERS.items():
        print(f"Creating {folder_name}...")
        if create_folder_page(folder_name, info, parent_id):
            created += 1
    
    print("\n" + "="*70)
    print(f"✅ CREATED {created} FOLDER PAGES")
    print("="*70)

if __name__ == '__main__':
    main()
