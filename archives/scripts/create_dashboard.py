#!/usr/bin/env python3
from notion_client import Client
from datetime import datetime

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
WORKSPACE = '/root/.openclaw/workspace'
parent_id = '30b8d599-a162-8067-9eb8-f229b473d25f'

print("="*60)
print("CREATING ENHANCED DASHBOARD PAGE")
print("="*60)

dashboard_content = """# 🎯 Nasr's Command Center - Enhanced Dashboard

## Welcome
Your Second Brain is now fully synced and organized.

---

## 📊 Quick Stats
- Core Files: 7
- CVs: 5
- LinkedIn Content: 3
- Case Studies: 3
- Strategy Docs: 5+
- Total Pages: 50+

---

## 📁 Navigation

### Core Files
- [[MEMORY.md]] - Long-term memory & workflow
- [[IDENTITY.md]] - Who you are
- [[USER.md]] - Profile & preferences
- [[SOUL.md]] - Operating principles
- [[TOOLS.md]] - Technical configs
- [[AGENTS.md]] - Sub-agent directory
- [[HEARTBEAT.md]] - Heartbeat configuration

### CVs
- [[MASTER_CV.md]] - Full profile
- [[MASTER_CV_QUICKREF.md]] - Quick reference
- [[Tailored CVs]] - Specific roles

### LinkedIn Content
- [[linkedin_posts.md]] - Post templates
- [[linkedin-posts-healthtech.md]] - HealthTech posts
- [[linkedin_analytics_tracker.md]] - Metrics

### Case Studies
- [[case-study-talabat.md]] - E-commerce (233x growth)
- [[case-study-sgh.md]] - Healthcare
- [[case-study-network.md]] - FinTech

---

## Priority Actions

### Immediate
- [ ] Prepare for Delphi interview
- [ ] Send 5 LinkedIn connection requests
- [ ] Publish 1 post this week

### This Week
- [ ] Follow up with warm leads
- [ ] Draft 3 new posts
- [ ] Research Jeddah healthtech companies

### This Month
- [ ] Land senior PM/Director role in Jeddah
- [ ] Publish 8+ LinkedIn posts
- [ ] Build 10+ new connections

---

## Metrics That Matter

| Metric | Value | Source |
|--------|-------|--------|
| $50M | Current transformation | Saudi German |
| 233x | Platform growth | Talabat |
| 300+ | Projects managed | Network International |
| 8 | Countries covered | Network International |
| 20+ | Years experience | Career |

---

Last updated: {date}""".format(date=datetime.now().strftime("%B %d, %Y"))

try:
    dashboard = notion.pages.create(
        parent={'page_id': parent_id},
        properties={'title': {'title': [{'text': {'content': '🎯 Enhanced Dashboard'}}]}}
    )
    dashboard_id = dashboard['id']
    print("Created: Enhanced Dashboard page")
    
    lines = dashboard_content.strip().split('\n')
    for i in range(0, len(lines), 15):
        chunk = lines[i:i+15]
        text = '\n'.join(chunk)
        if text.strip():
            try:
                notion.blocks.children.append(dashboard_id, children=[
                    {'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': text[:2000]}}]}}
                ])
            except:
                pass
    
    print("Added content blocks")
    print("\n" + "="*60)
    print("DASHBOARD CREATED SUCCESSFULLY")
    print("="*60)
    
except Exception as e:
    print("Error: " + str(e)[:80])
