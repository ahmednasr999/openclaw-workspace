#!/usr/bin/env python3
"""
Enhance Notion Pages - Add properties, icons, structure
"""
from notion_client import Client
import json

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
print("ENHANCING NOTION PAGES")
print("="*60)
print(f"Command Center ID: {parent_id}")
print("="*60)

# Categories with icons and properties
CATEGORIES = {
    'Core Files': {
        'icon': '📁',
        'files': ['MEMORY.md', 'IDENTITY.md', 'USER.md', 'SOUL.md', 'TOOLS.md', 'AGENTS.md', 'HEARTBEAT.md'],
        'type': 'Core'
    },
    'CVs': {
        'icon': '📋',
        'files': ['MASTER_CV.md', 'MASTER_CV_QUICKREF.md', 'CV_CDO_Consumer_Electronics_Dubai.md', 
                  'TAILORED_CV_Director_Digital_Transformation.md', 'TAILORED_CV_Director_Digital_Transformation_v2.md'],
        'type': 'CV'
    },
    'LinkedIn': {
        'icon': '🔗',
        'files': ['linkedin_posts.md', 'linkedin-posts-healthtech.md', 'linkedin_analytics_tracker.md'],
        'type': 'Content'
    },
    'Case Studies': {
        'icon': '📊',
        'files': ['case-study-network.md', 'case-study-sgh.md', 'case-study-talabat.md'],
        'type': 'Case Study'
    },
    'Strategy': {
        'icon': '🎯',
        'files': ['EXECUTIVE_TRANSFORMATION_PLAYBOOK.md', 'MASTER_EXECUTION_KIT.md', 'STRATEGIC_PLAN.md'],
        'type': 'Strategy'
    }
}

print("\nCategories to enhance:")
for cat in CATEGORIES:
    print(f"  {CATEGORIES[cat]['icon']} {cat}: {len(CATEGORIES[cat]['files'])} files")

print("\n" + "="*60)
print("Note: Full enhancement requires manual Notion actions:")
print("- Add icons: Click page icon → Choose emoji")
print("- Add properties: Turn page into database")
print("- Add covers: Click cover area → Upload image")
print("="*60)
PYEOF