#!/usr/bin/env python3
"""
Create complete folder hierarchy in Notion matching OpenClaw structure
Each folder becomes a Notion page with file listings
"""

from notion_client import Client
import os
import json
from datetime import datetime

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
WORKSPACE = '/root/.openclaw/workspace'

# Folders to include in hierarchy
INCLUDE_FOLDERS = [
    'agents',
    'coordination',
    'knowledge-base',
    'memory',
    'scripts',
    'skills',
    'marketing-skills',
    'healthtech-directory',
]

# Folders to skip
SKIP_FOLDERS = ['.git', 'node_modules', '__pycache__', '.openclaw', '.agents', 
                'docs', 'media', 'logs', 'archive', 'posted', 'reviewed', 
                'revised', 'drafts', 'approved', 'templates', 'reminders',
                'eval', 'config', 'github-profile-pics', 'diagrams', '.clawhub']

def get_folder_tree(path, depth=0, max_depth=4):
    """Build folder tree structure"""
    tree = {'name': os.path.basename(path), 'path': path, 'files': [], 'children': []}
    
    if depth >= max_depth:
        return tree
    
    try:
        items = sorted(os.listdir(path))
        for item in items:
            if item.startswith('.') or item in SKIP_FOLDERS:
                continue
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                if item in INCLUDE_FOLDERS or depth < 2:
                    tree['children'].append(get_folder_tree(full_path, depth + 1, max_depth))
            elif item.endswith(('.md', '.py', '.json', '.csv')):
                tree['files'].append(item)
    except:
        pass
    
    return tree

def tree_to_text(tree, indent=0):
    """Convert tree to readable text"""
    lines = [tree['name']]
    for f in tree['files'][:10]:  # Limit files shown
        lines.append(f"  📄 {f}")
    for child in tree['children']:
        for line in tree_to_text(child, indent + 1):
            lines.append(f"  {line}")
    return lines

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

def create_page(title, content, parent_id):
    """Create a Notion page"""
    try:
        page = notion.pages.create(
            parent={'page_id': parent_id},
            properties={'title': {'title': [{'text': {'content': title}}]}}
        )
        
        # Add content
        lines = content.strip().split('\n')[:100]
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
        return page['id']
    except Exception as e:
        print(f"  ❌ {title}: {str(e)[:40]}")
        return None

def create_folder_hierarchy(tree, parent_id, depth=0):
    """Recursively create folder pages"""
    icon = "📁" if depth > 0 else "📁"
    title = f"{icon} {tree['name']}"
    
    # Convert tree to text content
    lines = [f"📁 {tree['name']}", "="*40]
    
    # Files in this folder
    if tree['files']:
        lines.append("\n📄 Files:")
        for f in sorted(tree['files'])[:15]:
            lines.append(f"  • {f}")
    
    # Subfolders
    if tree['children']:
        lines.append("\n📂 Subfolders:")
        for child in tree['children']:
            lines.append(f"  📁 {child['name']}")
    
    content = '\n'.join(lines)
    
    # Create page
    page_id = create_page(title, content, parent_id)
    if page_id:
        print(f"{'  ' * depth}✅ {title}")
        
        # Recurse to children
        for child in tree['children']:
            create_folder_hierarchy(child, page_id, depth + 1)
    
    return page_id

def main():
    print("="*70)
    print("🏗️  CREATING COMPLETE FOLDER HIERARCHY IN NOTION")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Find parent
    parent_id = find_job_tracker()
    if not parent_id:
        print("❌ Could not find Ahmed's Job Tracker")
        return
    
    print(f"✅ Parent: Ahmed's Job Tracker\n")
    
    # Delete existing folder pages first
    print("🧹 Cleaning existing folder pages...")
    try:
        results = notion.search(
            query="📁 ",
            filter={'value': 'page', 'property': 'object'},
            page_size=100
        )
        for r in results.get('results', []):
            try:
                notion.pages.update(page_id=r['id'], archived=True)
            except:
                pass
    except:
        pass
    print("✅ Cleanup done\n")
    
    # Build folder tree
    print("📊 Building folder tree from OpenClaw...")
    tree = get_folder_tree(WORKSPACE, max_depth=4)
    print("✅ Tree built\n")
    
    # Create hierarchy
    print("🏗️  Creating hierarchy in Notion...")
    for child in tree['children']:
        if child['name'] in INCLUDE_FOLDERS:
            create_folder_hierarchy(child, parent_id, 0)
    
    print("\n" + "="*70)
    print("✅ FOLDER HIERARCHY CREATED")
    print("="*70)

if __name__ == '__main__':
    main()
