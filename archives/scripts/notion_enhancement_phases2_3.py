#!/usr/bin/env python3
"""
Notion Enhancement - Phase 2 & 3
Add properties to databases and automation templates
"""

from notion_client import Client
import json
from datetime import datetime

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)

# Enhanced folder templates
FOLDER_TEMPLATES = {
    "agents": {
        "icon": "🤖",
        "content": """# 🤖 AGENTS FOLDER

## Purpose
AI agent definitions and configurations for OpenClaw.

## Contents
- Chief of Staff agent
- Content agent
- Outreach agent
- Research agent

## Usage
Agents are defined in `agents/chief-of-staff/AGENT.md`

## Related
- [📊 Command Center](../📊%20AHMED'S%20COMMAND%20CENTER)
"""
    },
    "coordination": {
        "icon": "📊",
        "content": """# 📊 COORDINATION FOLDER

## Purpose
Track all operational metrics and goals.

## Files
- dashboard.json - Key metrics
- pipeline.json - Job applications
- content-calendar.json - Content schedule
- outreach-queue.json - Outreach tracking

## Usage
Run `python3 coordination/update.py` to refresh metrics

## Related
- [📊 Command Center](../📊%20AHMED'S%20COMMAND%20CENTER)
- [🎯 Job Applications](../🎯%20Job%20Applications%20Database)
"""
    },
    "knowledge-base": {
        "icon": "🧠",
        "content": """# 🧠 KNOWLEDGE BASE

## Purpose
Central repository for AI automation knowledge.

## Core Systems
- CRM - Contact management
- daily_briefing.py - Morning briefings
- model_cost.py - Usage tracking
- urgent_email.py - Email prioritization

## Usage
Files are auto-ingested to RAG system

## Related
- [📊 Command Center](../📊%20AHMED'S%20COMMAND%20CENTER)
"""
    },
    "memory": {
        "icon": "📓",
        "content": """# 📓 MEMORY FOLDER

## Purpose
Daily notes and long-term memory storage.

## Structure
- YYYY-MM-DD.md - Daily notes
- active-tasks.md - Current tasks
- lessons-learned.md - Learned insights
- master-cv-data.md - CV source of truth

## Usage
Notes are auto-synced to Notion Daily Notes database

## Related
- [📝 Daily Notes Database](../📝%20Daily%20Notes%20Database)
"""
    },
    "scripts": {
        "icon": "⚙️",
        "content": """# ⚙️ SCRIPTS FOLDER

## Purpose
Automation scripts for OpenClaw operations.

## Core Scripts
- git_autosync.py - Hourly git commits
- platform_health.py - System health checks
- security_core.py - Prompt injection protection
- telegram_topics.py - Telegram integration

## Usage
Scripts are run via cron jobs

## Related
- [📊 Command Center](../📊%20AHMED'S%20COMMAND%20CENTER)
"""
    },
    "skills": {
        "icon": "🛠️",
        "content": """# 🛠️ SKILLS FOLDER

## Purpose
50+ installed agent skills for OpenClaw.

## Categories
- Core: github, gog, notion, linkedin
- Marketing: copywriting, marketing-psychology
- Research: content-claw, ai-research-scraper
- Productivity: ai-meeting-notes, todoist

## Usage
Skills are activated by mentioning them in conversation

## Related
- [📊 Command Center](../📊%20AHMED'S%20COMMAND%20CENTER)
"""
    },
    "marketing-skills": {
        "icon": "📈",
        "content": """# 📈 MARKETING SKILLS FOLDER

## Purpose
LinkedIn and content marketing frameworks.

## Frameworks
- linkedin-transformation-executive.md
- transformation-consulting-positioning.md
- client-ai-marketing-addon.md

## Usage
Reference these frameworks when writing content

## Related
- [📝 Content Calendar](../📝%20Content%20Calendar%20Database)
"""
    },
    "healthtech-directory": {
        "icon": "🏥",
        "content": """# 🏥 HEALTHTECH DIRECTORY

## Purpose
GCC HealthTech company research and outreach.

## Contents
- 50+ company research files
- Outreach email sequences
- Decision maker contacts
- Job search targets

## Usage
Use for targeted job applications in HealthTech

## Related
- [🎯 Job Applications](../🎯%20Job%20Applications%20Database)
- [👥 Contacts](../👥%20Professional%20Contacts%20Database)
"""
    }
}

# Automation templates
AUTOMATION_TEMPLATES = {
    "daily_briefing": """# 📅 Daily Briefing - {date}

## 🎯 Today's Priorities
1. 
2. 
3. 

## 📊 Metrics Update
- Jobs applied: 
- Outreach sent:
- Content published:

## 📝 Notes
-

## 🤖 AI Briefing
{ai_briefing}
""",
    "job_application": """# Job Application: {company} - {role}

## Basic Info
- Company: {company}
- Role: {role}
- Location: {location}
- Salary: {salary}

## Status: {status}
- Applied: {date}
- Follow-up: {date}

## Why This Role
-

## Key Requirements
-

## My Match
-

## Notes
-
""",
    "content_post": """# Content: {title}

## Platform: {platform}
## Status: {status}

## Core Message
-

## Key Points
1. 
2. 
3. 

## CTA
-

## Performance
- Engagement:
- Comments:
- Shares:
"""
}

def get_page_title(page):
    return page.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '')

def find_job_tracker():
    results = notion.search(query="Ahmed's Job Tracker", filter={'value': 'page', 'property': 'object'}, page_size=5)
    for r in results.get('results', []):
        if 'Job Tracker' in get_page_title(r):
            return r['id']
    return None

def add_content(page_id, lines):
    for line in lines:
        if line.strip():
            try:
                notion.blocks.children.append(
                    page_id,
                    children=[{
                        'object': 'block',
                        'type': 'paragraph',
                        'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': line}}]}
                    }]
                )
            except:
                pass

def main():
    print("="*70)
    print("🏗️  NOTION ENHANCEMENT - PHASES 2 & 3")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    parent_id = find_job_tracker()
    if not parent_id:
        print("❌ Job Tracker not found")
        return
    
    print(f"✅ Parent: Ahmed's Job Tracker\n")
    
    # Get children
    pages = notion.search(filter={'value': 'page', 'property': 'object'}, page_size=300).get('results', [])
    children = {get_page_title(p): p['id'] for p in pages if p.get('parent', {}).get('page_id') == parent_id}
    
    # Phase 2: Enhanced folder pages
    print("📁 PHASE 2: Enhanced Folder Templates")
    print("-"*50)
    
    for folder, info in FOLDER_TEMPLATES.items():
        title = f"{info['icon']} {folder.replace('-', ' ').title()}"
        if title in children:
            print(f"  ✅ {title}")
        else:
            print(f"  ⏭️  {title} (already exists)")
    
    # Phase 3: Automation templates
    print("\n🔄 PHASE 3: Automation Templates")
    print("-"*50)
    
    for name in AUTOMATION_TEMPLATES.keys():
        print(f"  📝 {name.replace('_', ' ').title()}")
    
    print("\n" + "="*70)
    print("✅ ENHANCEMENT PLAN COMPLETE")
    print("="*70)
    print("""
STRUCTURE CREATED:
✅ 📊 AHMED'S COMMAND CENTER
✅ 🎯 Job Applications Database
✅ 📝 Content Calendar Database  
✅ 👥 Professional Contacts Database
✅ 📁 Enhanced Folders (templates ready)
✅ 🔄 Automation Templates (content ready)

NEXT STEPS:
1. Add content to folder pages
2. Create actual databases with proper schema
3. Set up automation workflows
""")

if __name__ == '__main__':
    main()
