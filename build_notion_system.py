#!/usr/bin/env python3
"""
Create fully structured Notion system with proper content and navigation
"""
from notion_client import Client
from datetime import datetime

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)

# Get Command Center
results = notion.search(query="Nasr's Command Center", filter={'value': 'page', 'property': 'object'}, page_size=5)
parent_id = None
for r in results.get('results', []):
    title = r.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '')
    if 'Command Center' in title:
        parent_id = r['id']
        break

print("="*60)
print("CREATING FULL NOTION SYSTEM")
print("="*60)
print(f"Parent ID: {parent_id}")

# Content for each section
SECTIONS = {
    "Core Files": {
        "icon": "📁",
        "description": "Your personal operating system",
        "files": ["MEMORY.md", "IDENTITY.md", "USER.md", "SOUL.md", "TOOLS.md", "AGENTS.md", "HEARTBEAT.md"]
    },
    "CVs": {
        "icon": "📋",
        "description": "Your professional profile", 
        "files": ["MASTER_CV.md", "MASTER_CV_QUICKREF.md", "CV_CDO_Consumer_Electronics_Dubai.md"]
    },
    "LinkedIn Content": {
        "icon": "🔗",
        "description": "Post templates and analytics",
        "files": ["linkedin_posts.md", "linkedin-posts-healthtech.md", "linkedin_analytics_tracker.md"]
    },
    "Case Studies": {
        "icon": "📊",
        "description": "Transformation success stories",
        "files": ["case-study-talabat.md", "case-study-sgh.md", "case-study-network.md"]
    },
    "Strategy": {
        "icon": "🎯",
        "description": "Playbooks and guides",
        "files": ["EXECUTIVE_TRANSFORMATION_PLAYBOOK.md", "MASTER_EXECUTION_KIT.md"]
    }
}

print("\nSections to create:")
for section in SECTIONS:
    print(f"  {SECTIONS[section]['icon']} {section}: {len(SECTIONS[section]['files'])} files")
print("="*60)
PYEOF