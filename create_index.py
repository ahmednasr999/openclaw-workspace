#!/usr/bin/env python3
"""
Create comprehensive Master Index page with all content organized
"""
from notion_client import Client
from datetime import datetime

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
parent_id = '30b8d599-a162-8067-9eb8-f229b473d25f'

print("="*60)
print("CREATING MASTER INDEX")
print("="*60)

# Find all synced pages
all_pages = notion.search(filter={'value': 'page', 'property': 'object'}, page_size=500).get('results', [])
children = [p for p in all_pages if p.get('parent', {}).get('page_id') == parent_id]

# Build page list
page_list = []
for p in children:
    title = p.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', '')
    if title and title not in ['🎯 Enhanced Dashboard', '📚 Enhancement Guide']:
        page_list.append(title)

# Create comprehensive index
index_content = """# 📋 MASTER INDEX

## Your Complete Second Brain

All content from OpenClaw workspace, organized and searchable.

---

## 📁 CORE FILES

### Operating System
| Page | Description |
|------|-------------|
| [[FILE: MEMORY.md]] | Long-term memory, CV workflow, model strategy |
| [[FILE: IDENTITY.md]] | Your name, creature, vibe, emoji |
| [[FILE: USER.md]] | About Ahmed - profile, work style |
| [[FILE: SOUL.md]] | Operating principles, proactive guidance |
| [[FILE: TOOLS.md]] | Technical configs, CV creation rules |
| [[FILE: AGENTS.md]] | Sub-agent directory, coordination |
| [[FILE: HEARTBEAT.md]] | Heartbeat configuration |

---

## 📋 CVs

### Main CVs
| Page | Description |
|------|-------------|
| [[CV: MASTER_CV]] | Complete 20-year career profile |
| [[CV: MASTER_CV_QUICKREF]] | Key metrics and highlights |
| [[CV: CV_CDO_Consumer_Electronics_Dubai]] | Consumer electronics leadership |

### Tailored CVs
| Page | Description |
|------|-------------|
| [[CV: TAILORED_CV_Director_Digital_Transformation]] | Director-level positioning |

---

## 🔗 LINKEDIN CONTENT

### Post Templates
| Page | Description |
|------|-------------|
| [[LI: linkedin_posts]] | General post templates |
| [[LI: linkedin-posts-healthtech]] | HealthTech-specific content |
| [[LI: linkedin_analytics_tracker]] | Engagement metrics |

---

## 📊 CASE STUDIES

| Page | Industry | Key Achievement |
|------|----------|-----------------|
| [[CASE: case-study-talabat]] | E-commerce | 233x platform growth |
| [[CASE: case-study-sgh]] | Healthcare | $50M transformation |
| [[CASE: case-study-network]] | FinTech | 300+ projects, 8 countries |

---

## 🎯 STRATEGY

| Page | Description |
|------|-------------|
| [[EXECUTIVE_TRANSFORMATION_PLAYBOOK.md]] | Leadership framework |
| [[MASTER_EXECUTION_KIT.md]] | Operational system |

---

## 📈 METRICS THAT MATTER

| Metric | Achievement | Source |
|--------|-------------|---------|
| $50M | Current transformation | Saudi German Hospital Group |
| 233x | Platform growth | Delivery Hero (Talabat) |
| 300+ | Concurrent projects | Network International |
| 8 | Countries coverage | Network International |
| 20+ | Years experience | Career |

---

## 🎯 QUICK ACTIONS

### Interview Preparation
1. [[CASE: case-study-talabat]] - Scale story
2. [[CASE: case-study-sgh]] - Healthcare transformation
3. [[CV: MASTER_CV]] - Full profile

### LinkedIn Content
1. [[LI: linkedin_posts]] - Post templates
2. [[LI: linkedin-posts-healthtech]] - HealthTech angle
3. [[CASE: case-study-talabat]] - Success story

### Job Search
1. [[CV: MASTER_CV]] - Your resume
2. [[CV: MASTER_CV_QUICKREF]] - Key metrics
3. [[STRATEGY: EXECUTIVE_TRANSFORMATION_PLAYBOOK]] - Positioning

---

## 🔍 SEARCH GUIDE

Looking for something specific?

| Search Term | Where to Look |
|-------------|---------------|
| CV/Resume | CVs section |
| Metrics | METRICS section |
| Transformation stories | Case Studies |
| Post templates | LinkedIn Content |
| Leadership | Strategy section |
| Technical setup | Core Files - TOOLS.md |

---

## 📅 LAST UPDATED

Updated: {date}

---

*Part of Nasr's Second Brain - OpenClaw + Notion Integration*
""".format(date=datetime.now().strftime("%B %d, %Y"))

# Create the index page
try:
    index = notion.pages.create(
        parent={'page_id': parent_id},
        properties={'title': {'title': [{'text': {'content': '📋 Master Index'}}]}}
    )
    index_id = index['id']
    print("Created: 📋 Master Index page")
    
    # Add content
    lines = index_content.strip().split('\n')
    added = 0
    for i in range(0, len(lines), 15):
        chunk = lines[i:i+15]
        text = '\n'.join(chunk)
        if text.strip():
            try:
                notion.blocks.children.append(index_id, children=[
                    {'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': text[:2000]}}]}}
                ])
                added += 1
            except:
                pass
    
    print(f"Added {added} content blocks")
    
except Exception as e:
    print(f"Error: {str(e)[:60]}")

print("="*60)
print("MASTER INDEX CREATED")
print("="*60)
