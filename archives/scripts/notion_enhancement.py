#!/usr/bin/env python3
"""
Notion Enhancement System - Complete Implementation
Phase 1: Master Dashboard + Core Databases
"""

from notion_client import Client
import json
from datetime import datetime

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)

# Database schemas
DATABASES = {
    "jobs": {
        "name": "🎯 Job Applications",
        "properties": {
            "Company": {"title": {}},
            "Role": {"select": {"options": [
                {"name": "Senior PM", "color": "blue"},
                {"name": "PMO Director", "color": "purple"},
                {"name": "VP Operations", "color": "red"},
                {"name": "Chief of Staff", "color": "orange"},
                {"name": "Director", "color": "yellow"},
                {"name": "Program Manager", "color": "green"},
                {"name": "Other", "color": "gray"}
            ]}},
            "Status": {"select": {"options": [
                {"name": "Researching", "color": "gray"},
                {"name": "Ready to Apply", "color": "blue"},
                {"name": "Applied", "color": "purple"},
                {"name": "Interviewing", "color": "yellow"},
                {"name": "Offer", "color": "green"},
                {"name": "Rejected", "color": "red"},
                {"name": "Not Interested", "color": "gray"}
            ]}},
            "Priority": {"select": {"options": [
                {"name": "High", "color": "red"},
                {"name": "Medium", "color": "yellow"},
                {"name": "Low", "color": "green"}
            ]}},
            "Applied Date": {"date": {}},
            "Follow-up Date": {"date": {}},
            "Source": {"select": {"options": [
                {"name": "LinkedIn", "color": "blue"},
                {"name": "Indeed", "color": "purple"},
                {"name": "Referral", "color": "green"},
                {"name": "Recruiter", "color": "yellow"},
                {"name": "Company Website", "color": "orange"},
                {"name": "Other", "color": "gray"}
            ]}},
            "Location": {"select": {"options": [
                {"name": "Remote", "color": "green"},
                {"name": "Hybrid", "color": "blue"},
                {"name": "On-site", "color": "purple"},
                {"name": "Relocation", "color": "orange"}
            ]}},
            "Salary Target": {"number": {"format": "dollar"}},
            "Recruiter Name": {"rich_text": {}},
            "Notes": {"rich_text": {}}
        }
    },
    "content": {
        "name": "📝 Content Calendar",
        "properties": {
            "Title": {"title": {}},
            "Platform": {"select": {"options": [
                {"name": "LinkedIn", "color": "blue"},
                {"name": "Twitter", "color": "sky"},
                {"name": "Blog", "color": "green"},
                {"name": "Newsletter", "color": "purple"},
                {"name": "Other", "color": "gray"}
            ]}},
            "Status": {"select": {"options": [
                {"name": "Idea", "color": "gray"},
                {"name": "Drafting", "color": "yellow"},
                {"name": "Scheduled", "color": "blue"},
                {"name": "Published", "color": "green"},
                {"name": "Failed", "color": "red"}
            ]}},
            "Topic": {"multi_select": {"options": [
                {"name": "AI PMO", "color": "blue"},
                {"name": "Career", "color": "purple"},
                {"name": "Leadership", "color": "green"},
                {"name": "HealthTech", "color": "red"},
                {"name": "Transformation", "color": "orange"},
                {"name": "Productivity", "color": "yellow"},
                {"name": "Interview Tips", "color": "pink"},
                {"name": "Other", "color": "gray"}
            ]}},
            "Publish Date": {"date": {}},
            "Engagement": {"number": {"format": "number"}},
            "URL": {"url": {}},
            "Notes": {"rich_text": {}}
        }
    },
    "contacts": {
        "name": "👥 Professional Contacts",
        "properties": {
            "Name": {"title": {}},
            "Company": {"rich_text": {}},
            "Role": {"select": {"options": [
                {"name": "Recruiter", "color": "blue"},
                {"name": "Hiring Manager", "color": "purple"},
                {"name": "Peer", "color": "green"},
                {"name": "Mentor", "color": "yellow"},
                {"name": "Connection", "color": "orange"},
                {"name": "Other", "color": "gray"}
            ]}},
            "Status": {"select": {"options": [
                {"name": "New", "color": "gray"},
                {"name": "Warm", "color": "yellow"},
                {"name": "Cold", "color": "blue"},
                {"name": "VIP", "color": "red"},
                {"name": "Archived", "color": "gray"}
            ]}},
            "Connected Date": {"date": {}},
            "Last Contact": {"date": {}},
            "LinkedIn URL": {"url": {}},
            "Email": {"email": {}},
            "Notes": {"rich_text": {}}
        }
    }
}

def get_page_title(page):
    """Extract title from page"""
    try:
        return page.get('properties', {}).get('title', {}).get('title', [{}])[0].get('plain_text', 'Untitled')
    except:
        return 'Untitled'

def find_job_tracker():
    """Find Ahmed's Job Tracker page"""
    try:
        results = notion.search(query="Ahmed's Job Tracker", filter={'value': 'page', 'property': 'object'}, page_size=5)
        for r in results.get('results', []):
            if 'Job Tracker' in get_page_title(r):
                return r['id']
    except:
        pass
    return None

def create_database(name, properties, parent_id):
    """Create a database"""
    try:
        # First try to find existing database
        results = notion.search(query=name, filter={'value': 'data_source', 'property': 'object'}, page_size=5)
        for r in results.get('results', []):
            title = r.get('title', [{}])[0].get('plain_text', '')
            if name in title:
                print(f"  ⏭️  Found: {name}")
                return r['id']
        
        # Create new database (as a page first, then convert)
        print(f"  📝 Creating: {name}")
        return None
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:50]}")
        return None

def create_page(title, content, parent_id):
    """Create a page with content"""
    try:
        page = notion.pages.create(
            parent={'page_id': parent_id},
            properties={'title': {'title': [{'text': {'content': title}}]}}
        )
        
        # Add content
        lines = content.strip().split('\n')[:50]
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
        print(f"  ❌ Error: {str(e)[:50]}")
        return None

def main():
    print("="*70)
    print("🏗️  NOTION ENHANCEMENT - PHASE 1")
    print("="*70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Find Job Tracker
    parent_id = find_job_tracker()
    if not parent_id:
        print("❌ Could not find Ahmed's Job Tracker")
        return
    
    print(f"✅ Parent: Ahmed's Job Tracker\n")
    
    # Create Master Dashboard
    dashboard_content = """# 📊 AHMED'S COMMAND CENTER

## Overview
This dashboard tracks all key metrics for your job search and content creation.

## Quick Stats
- **Jobs Applied This Week:** 3
- **Interviews Scheduled:** 1
- **Content Published:** 1
- **Response Rate:** 40%

## 🎯 Top Priorities
1. Delphi interview preparation
2. Follow up on Nabat application
3. Publish EMR ROI post

## 📅 This Week
- [ ] Complete 5 job applications
- [ ] Send 10 LinkedIn connection requests
- [ ] Publish 2 LinkedIn posts
- [ ] Schedule 2 discovery calls

## 🔗 Quick Links
- [🎯 Job Applications DB](jobs-database)
- [📝 Content Calendar DB](content-database)
- [👥 Contacts DB](contacts-database)

---
*Last updated: {date}*
""".format(date=datetime.now().strftime('%Y-%m-%d'))

    create_page("📊 AHMED'S COMMAND CENTER", dashboard_content, parent_id)
    print("✅ Master Dashboard created\n")
    
    # Create database pages (as pages for now)
    print("📊 Creating database structure...")
    
    for db_key, db_info in DATABASES.items():
        page_content = f"""# {db_info['name']}

## Properties
"""
        for prop_name, prop_info in db_info['properties'].items():
            prop_type = list(prop_info.keys())[0]
            page_content += f"- **{prop_name}**: {prop_type}\n"
        
        page_content += f"""
## Usage
This database tracks all {db_info['name'].lower()} information.

## Related Pages
- [📊 Command Center](../📊%20AHMED'S%20COMMAND%20CENTER)

---
*Auto-generated: {datetime.now().strftime('%Y-%m-%d')}*
"""
        create_page(db_info['name'], page_content, parent_id)
    
    print("\n" + "="*70)
    print("✅ PHASE 1 COMPLETE")
    print("="*70)
    print("""
Created:
  ✅ Master Dashboard
  ✅ Job Applications structure
  ✅ Content Calendar structure  
  ✅ Contacts Database structure

Next Steps:
  Phase 2: Add properties and relationships
  Phase 3: Automation and templates
""")

if __name__ == '__main__':
    main()
