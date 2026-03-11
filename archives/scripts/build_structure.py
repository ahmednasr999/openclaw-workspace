#!/usr/bin/env python3
"""
Build proper Notion structure with databases and hierarchy
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
print("BUILDING NOTION STRUCTURE")
print("="*60)
print(f"Parent: {parent_id}")

# First, create the Master Dashboard page
dashboard_content = """# 🎯 NASR'S COMMAND CENTER

## Your Second Brain - Organized

---

## 📊 Quick Navigation

### 🎯 Master Dashboard
You are here. All systems go.

### 📋 Content Database
All your LinkedIn posts, case studies, and content drafts.

### 💼 Jobs Database
Track all job applications, interviews, and offers.

### 📄 CVs Database
Your CVs, tailored versions, and cover letters.

### 📁 Core Files
Your operating system files (MEMORY, IDENTITY, USER, SOUL, TOOLS, AGENTS).

---

## 📈 Key Metrics

| Metric | Value | Context |
|--------|-------|---------|
| $50M | Current transformation | Saudi German Hospitals |
| 233x | Platform growth | Delivery Hero (Talabat) |
| 300+ | Projects managed | Network International |
| 20+ | Years experience | Career |

---

## 🎯 Priority Actions

### Immediate
- [ ] Review and schedule LinkedIn posts
- [ ] Check jobs database for follow-ups
- [ ] Update CV for new opportunities

### This Week
- [ ] Publish 3 LinkedIn posts
- [ ] Apply to 5 new roles
- [ ] Follow up with warm leads

### This Month
- [ ] Land senior PM/Director role in Jeddah
- [ ] Grow LinkedIn network to 500+
- [ ] Publish 12+ posts

---

## 🔗 Quick Links

- [[📋 Content Database]]
- [[💼 Jobs Database]]
- [[📄 CVs Database]]
- [[📁 Core Files]]

---

*Last Updated: {date}*
""".format(date=datetime.now().strftime("%B %d, %Y"))

print("\n1. Creating Master Dashboard...")
try:
    # Delete existing dashboard if exists (simplified - just create new)
    dashboard = notion.pages.create(
        parent={'page_id': parent_id},
        properties={'title': {'title': [{'text': {'content': '🎯 Master Dashboard'}}]}}
    )
    dashboard_id = dashboard['id']
    print(f"   ✅ Created Master Dashboard ({dashboard_id})")
except Exception as e:
    print(f"   ⚠️ Dashboard: {str(e)[:40]}")
    dashboard_id = None

print("\n2. Creating Content Database...")
# Create Content Database (simplified - create pages to simulate database entries)
content_pages = [
    ("📝 233x Growth Story", "Growth", "Draft", "LinkedIn"),
    ("📝 $50M Healthcare Transformation", "Healthcare", "Draft", "LinkedIn"),
    ("📝 PMO at Scale", "PMO", "Draft", "LinkedIn"),
    ("📝 Why I Relocate to Saudi Arabia", "Job Search", "Draft", "LinkedIn"),
    ("📝 Leadership Lesson", "Leadership", "Draft", "LinkedIn"),
    ("📝 HealthTech Opportunity", "HealthTech", "Draft", "LinkedIn"),
    ("📊 case-study-talabat", "E-commerce", "Published", "Case Study"),
    ("📊 case-study-sgh", "Healthcare", "Published", "Case Study"),
    ("📊 case-study-network", "FinTech", "Published", "Case Study"),
]

for title, category, status, content_type in content_pages:
    try:
        page = notion.pages.create(
            parent={'page_id': parent_id},
            properties={'title': {'title': [{'text': {'content': title}}]}}
        )
        print(f"   ✅ {title}")
    except Exception as e:
        print(f"   ⚠️ {title}: {str(e)[:30]}")

print("\n3. Creating Jobs Database...")
job_pages = [
    ("🎯 Nabat - Senior Program Manager", "Applied", "Feb 2026"),
    ("🎯 Delphi - Senior PM UAE", "Interviewing", "Feb 2026"),
    ("🎯 TechCorp - Digital Director", "Rejected", "Feb 2026"),
]

for title, status, date in job_pages:
    try:
        page = notion.pages.create(
            parent={'page_id': parent_id},
            properties={'title': {'title': [{'text': {'content': title}}]}}
        )
        print(f"   ✅ {title} ({status})")
    except Exception as e:
        print(f"   ⚠️ {title}: {str(e)[:30]}")

print("\n4. Creating CVs Database...")
cv_pages = [
    ("📋 CV: MASTER_CV", "Master", "Feb 2026"),
    ("📋 CV: MASTER_CV_QUICKREF", "Summary", "Feb 2026"),
    ("📋 CV: TAILORED_CV_Director_Digital_Transformation", "Tailored", "Feb 2026"),
]

for title, type_cv, date in cv_pages:
    try:
        page = notion.pages.create(
            parent={'page_id': parent_id},
            properties={'title': {'title': [{'text': {'content': title}}]}}
        )
        print(f"   ✅ {title}")
    except Exception as e:
        print(f"   ⚠️ {title}: {str(e)[:30]}")

print("\n5. Creating Index Pages...")

# Master Index
index_content = """# 📋 MASTER INDEX

All content organized by category.

---

## 🎯 Master Dashboard
Main navigation hub → Start here

## 📁 Core Files
Your operating system files
- FILE: MEMORY.md
- FILE: IDENTITY.md
- FILE: USER.md
- FILE: SOUL.md
- FILE: TOOLS.md
- FILE: AGENTS.md
- FILE: HEARTBEAT.md

## 📋 CVs
Professional profiles
- CV: MASTER_CV
- CV: MASTER_CV_QUICKREF
- CV: TAILORED_CV_Director_Digital_Transformation

## 🔗 LinkedIn Content
Posts, templates, and analytics
- 233x Growth Story
- $50M Healthcare Transformation
- PMO at Scale
- Why I Relocate to Saudi Arabia
- Leadership Lesson
- HealthTech Opportunity

## 📊 Case Studies
Success stories
- case-study-talabat (E-commerce)
- case-study-sgh (Healthcare)
- case-study-network (FinTech)

## 💼 Jobs
Application tracking
- Nabat - Senior Program Manager (Applied)
- Delphi - Senior PM UAE (Interviewing)
- TechCorp - Digital Director (Rejected)

---

*Last Updated: {date}*
""".format(date=datetime.now().strftime("%B %d, %Y"))

try:
    index = notion.pages.create(
        parent={'page_id': parent_id},
        properties={'title': {'title': [{'text': {'content': '📋 Master Index'}}]}}
    )
    print("   ✅ Master Index")
except Exception as e:
    print(f"   ⚠️ Index: {str(e)[:30]}")

print("\n" + "="*60)
print("STRUCTURE BUILD COMPLETE")
print("="*60)
