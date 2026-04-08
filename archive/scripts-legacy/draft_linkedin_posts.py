#!/usr/bin/env python3
"""
Draft LinkedIn posts based on Ahmed's content
"""
from notion_client import Client
from datetime import datetime

NOTION_KEY = open('/root/.config/notion/api_key').read().strip()
notion = Client(auth=NOTION_KEY)
parent_id = '30b8d599-a162-8067-9eb8-f229b473d25f'

print("="*60)
print("DRAFTING LINKEDIN POSTS")
print("="*60)

# Draft posts based on Ahmed's content
DRAFTS = [
    {
        "title": "POST: 233x Growth Story",
        "content": """🚀 233x growth in 18 months.

When I joined Delivery Hero (Talabat), we were processing 30,000 daily orders.

18 months later? 7 MILLION.

Here's what I learned about scaling:

1. PROCESS > TOOLS
We implemented lean methodologies across 5 countries before adding any new tech.

2. CUSTOMER-CENTRIC FEATURES
Every feature had to pass one test: "Does this help the driver or the customer?"

3. CROSS-FUNCTIONAL ALIGNMENT
Berlin HQ, GCC, and Egypt teams had daily syncs. No silos.

4. DATA-DRIVEN DECISIONS
Every KPI was visible. Every team knew their numbers.

The result: 233x growth. 🏆

What scaling lesson has shaped your career?

#Scaling #Growth #Leadership #Ecommerce #DigitalTransformation""",
        "category": "Growth Story"
    },
    {
        "title": "POST: $50M Healthcare Transformation",
        "content": """🏥 Leading a $50M digital transformation across 15 hospitals.

Here are 3 things I've learned about healthcare IT:

1. PATIENT SAFETY FIRST
Every technology decision goes through a "Does this improve patient outcomes?" filter.

2. REGULATORY COMPLIANCE IS NON-NEGOTIABLE
JCI. HIMSS. MOH. You can't cut corners.

3. CLINICIAN BUY-IN IS EVERYTHING
The best technology fails if doctors and nurses won't use it.

We're implementing AI-powered clinical decision support systems, telemedicine, and enterprise data warehouses.

The goal: Better patient outcomes, not just better technology.

What's your experience with healthcare transformation?

#HealthcareIT #DigitalTransformation #AI #PatientSafety""",
        "category": "Healthcare"
    },
    {
        "title": "POST: PMO at Scale",
        "content": """📊 Managing 300+ concurrent projects across 8 countries.

When I built the PMO at Network International, I learned that scale is a mindset, not a number.

Key principles that worked:

1. STANDARDIZED METHODOLOGY
Every project followed the same framework. No exceptions.

2. YOUNG, HUNGRY TALENT
I hired 16 Project Managers and trained them myself. Culture matters.

3. REGULAR GOVERNANCE
Weekly steering committees. Monthly reviews. No surprises.

4. AUTOMATION
We automated status reporting. PMs focused on delivery, not documentation.

Result: 300+ banking clients served across Egypt, UAE, Jordan, Kenya, Nigeria, Ghana, Mauritius, and South Africa.

What PMO lessons have shaped your career?

#PMO #ProjectManagement #Leadership #Scale""",
        "category": "PMO"
    },
    {
        "title": "POST: Why I Relocate to Saudi Arabia",
        "content": """🇸🇦 After 20 years in Egypt and UAE, I'm ready for my next chapter: Saudi Arabia.

Why KSA?

1. VISION 2030
The most ambitious transformation story in the region.

2. HEALTHCARE INVESTMENT
$65B+ being invested in health infrastructure. This is where healthcare innovation is happening.

3. OPPORTUNITY
Senior leadership roles. Digital transformation programs. Meaningful impact.

4. QUALITY OF LIFE
For my family. For my career. For the future.

I'm looking for Senior Program Director / Digital Transformation Lead roles in Jeddah or Riyadh.

If you know of opportunities, let's connect.

Who else is building their career in Saudi Arabia?

#SaudiArabia #Vision2030 #Healthcare #DigitalTransformation #Relocation""",
        "category": "Job Search"
    },
    {
        "title": "POST: Leadership Lesson",
        "content": """💡 The best Project Managers don't manage projects. They manage outcomes.

20 years in program management taught me this:

→ Don't ask: "Are we on schedule?"
→ Ask: "Are we delivering value?"

→ Don't ask: "Did we hit the milestone?"
→ Ask: "Did we move the business forward?"

→ Don't ask: "Is the team busy?"
→ Ask: "Is the team effective?"

This mindset shift changed everything for me.

What leadership lesson has transformed your career?

#Leadership #ProjectManagement #CareerAdvice #Management""",
        "category": "Leadership"
    },
    {
        "title": "POST: HealthTech Opportunity",
        "content": """🏥 HealthTech is the most exciting space in Middle East tech right now.

Here's why:

→ Saudi Arabia investing $65B+ in health infrastructure
→ AI-powered diagnostics are becoming standard
→ Telemedicine is finally mainstream
→ Electronic Medical Records adoption accelerating

I'm a Digital Transformation Executive with 20 years of experience—and I'm looking for my next opportunity in Saudi healthcare.

My background:
• $50M current transformation program (15 hospitals)
• 233x platform growth (Talabat)
• 300+ projects, 8 countries (Network International)
• Healthcare, FinTech, E-commerce expertise

If you're building the future of healthcare in KSA, let's connect.

#HealthTech #SaudiArabia #DigitalTransformation #HealthcareInnovation""",
        "category": "HealthTech"
    }
]

# Create drafts in Notion
print("\nCreating draft posts...")

for draft in DRAFTS:
    try:
        page = notion.pages.create(
            parent={'page_id': parent_id},
            properties={'title': {'title': [{'text': {'content': draft['title']}}]}}
        )
        
        # Add content
        notion.blocks.children.append(page['id'], children=[
            {'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': [{'type': 'text', 'text': {'content': draft['content']}}]}}
        ])
        
        print(f"✅ {draft['title']}")
    except Exception as e:
        print(f"❌ {draft['title']}: {str(e)[:30]}")

print("\n" + "="*60)
print("6 DRAFT POSTS CREATED")
print("="*60)
PYEOF