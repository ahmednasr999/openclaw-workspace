#!/usr/bin/env python3
"""
HealthTech Directory - Automated Research & Outreach System
Automatically processes companies and creates outreach campaigns
"""
import json
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
WORKSPACE = "/root/.openclaw/workspace/healthtech-directory"
DATA_DIR = f"{WORKSPACE}/data"
RESEARCH_DIR = f"{WORKSPACE}/research"
OUTPUT_DIR = f"{WORKSPACE}/outreach"


def load_targets():
    """Load job search targets"""
    with open(f"{DATA_DIR}/job-search-targets.json") as f:
        data = json.load(f)
        return data.get("companies", data)


def create_auto_outreach():
    """Create automated outreach sequences for all companies"""
    companies = load_targets()
    
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Automated Outreach System")
    print("=" * 60)
    print()
    
    # Create outreach sequences
    sequences = []
    
    for i, company in enumerate(companies, 1):
        name = company.get("company_name", "Unknown")
        website = company.get("website", "")
        location = company.get("location", {})
        country = location.get("country", "")
        city = location.get("city", "")
        category = company.get("category", "")
        pmo_score = company.get("pmo_maturity", {}).get("score", 0)
        
        # Create outreach sequence
        sequence = {
            "company": name,
            "website": website,
            "location": f"{city}, {country}",
            "category": category,
            "pmo_score": pmo_score,
            "priority": i,
            "sequence": [
                {
                    "day": 0,
                    "action": "Research",
                    "template": f"""Subject: Executive PMO Leadership - {name}

Hi [Name],

I noticed {name} is leading digital transformation in {country}'s healthcare sector.

I'm a Senior Technology Executive with 20+ years experience:
• SGH (Egypt): Led $50M transformation, reduced reporting by 97%
• Talabat (GCC): Scaled operations 233x in 18 months
• Network (8 countries): PMO for 300+ projects

I'm exploring senior leadership opportunities in HealthTech, particularly PMO, Digital Transformation, or CDO roles.

Would you have 15 minutes for a brief call this week?

Best regards,
Ahmed Nasr
Senior Technology Executive | PMO & AI Transformation
""",
                    "status": "pending"
                },
                {
                    "day": 3,
                    "action": "Follow-up",
                    "template": f"""Subject: Re: Executive PMO Leadership - {name}

Hi [Name],

Just following up on my previous message about {name}'s digital transformation initiatives.

I'm confident my experience could add value, particularly given:
• Proven track record with $50M+ transformations
• GCC market expertise (SGH, Talabat, Network)
• AI/Automation leadership at scale

Happy to share my portfolio or schedule a brief call at your convenience.

Best,
Ahmed
""",
                    "status": "pending"
                },
                {
                    "day": 7,
                    "action": "Final",
                    "template": f"""Subject: One last thought - {name}

Hi [Name],

I'll keep this brief. My background:

• 20+ years in technology leadership
• $50M transformation delivery
• GCC HealthTech expertise

If {name} is exploring senior technology leadership, I'd welcome the opportunity to discuss.

My calendar: https://calendly.com/ahmednasr

Best,
Ahmed
""",
                    "status": "pending"
                }
            ],
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }
        
        sequences.append(sequence)
        
        # Save individual sequence
        safe_name = name.replace(" ", "-").replace("/", "-")
        with open(f"{OUTPUT_DIR}/{i:02d}-{safe_name}-sequence.json", 'w') as f:
            json.dump(sequence, f, indent=2)
        
        print(f"  ✓ {i:2}. {name}")
    
    # Create master outreach CSV
    with open(f"{OUTPUT_DIR}/master-outreach.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'priority', 'company', 'website', 'location', 'category',
            'pmo_score', 'day0_status', 'day3_status', 'day7_status',
            'decision_maker', 'linkedin', 'notes'
        ])
        writer.writeheader()
        
        for s in sequences:
            writer.writerow({
                'priority': s['priority'],
                'company': s['company'],
                'website': s['website'],
                'location': s['location'],
                'category': s['category'],
                'pmo_score': s['pmo_score'],
                'day0_status': 'pending',
                'day3_status': 'pending',
                'day7_status': 'pending',
                'decision_maker': '',
                'linkedin': '',
                'notes': ''
            })
    
    # Save complete sequence file
    with open(f"{OUTPUT_DIR}/all-sequences.json", 'w') as f:
        json.dump({
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "total_companies": len(sequences)
            },
            "sequences": sequences
        }, f, indent=2)
    
    print()
    print(f"✓ Created {len(sequences)} outreach sequences")
    print(f"✓ Master CSV: {OUTPUT_DIR}/master-outreach.csv")
    print(f"✓ All sequences: {OUTPUT_DIR}/all-sequences.json")
    
    return sequences


def create_cron_schedule():
    """Create cron job for automated follow-ups"""
    cron_content = """# HealthTech Outreach Automation
# Automated follow-up reminders

# Daily follow-up check (9 AM Cairo)
0 9 * * * cd /root/.openclaw/workspace/healthtech-directory && python3 check-followups.py >> outreach/followup.log 2>&1

# Weekly outreach report (Monday 9 AM)
0 9 * * 1 cd /root/.openclaw/workspace/healthtech-directory && python3 outreach-report.py >> outreach/report.log 2>&1
"""
    
    with open(f"{OUTPUT_DIR}/outreach-cron.txt", 'w') as f:
        f.write(cron_content)
    
    print()
    print("✓ Cron schedule created: outreach/outreach-cron.txt")


def check_followups():
    """Check for pending follow-ups"""
    print("Checking follow-ups...")
    
    # Load sequences
    with open(f"{OUTPUT_DIR}/all-sequences.json") as f:
        data = json.load(f)
    
    today = datetime.now()
    pending = []
    
    for sequence in data["sequences"]:
        company = sequence["company"]
        for step in sequence["sequence"]:
            # Calculate due date
            created = datetime.fromisoformat(sequence["created_at"])
            due_date = created + timedelta(days=step["day"])
            
            if step["status"] == "pending" and due_date <= today:
                pending.append({
                    "company": company,
                    "action": step["action"],
                    "day": step["day"],
                    "template": step["template"]
                })
    
    if pending:
        print(f"Found {len(pending)} pending follow-ups:")
        for p in pending[:5]:  # Show top 5
            print(f"  • {p['company']} - {p['action']} (Day {p['day']})")
    else:
        print("No pending follow-ups")
    
    return pending


def main():
    """Main function"""
    print()
    print("=" * 60)
    print("HealthTech Directory - Automated Outreach System")
    print("=" * 60)
    print()
    
    # Create outreach sequences
    create_auto_outreach()
    
    # Create cron schedule
    create_cron_schedule()
    
    print()
    print("=" * 60)
    print("Outreach System Ready")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review outreach sequences in outreach/")
    print("2. Add decision maker names to master-outreach.csv")
    print("3. Set up outreach cron jobs")
    print("4. Run: python3 check-followups.py")


if __name__ == "__main__":
    main()
