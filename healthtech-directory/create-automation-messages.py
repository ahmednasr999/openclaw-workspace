#!/usr/bin/env python3
"""
HealthTech Directory - Automated LinkedIn Outreach
Automatically sends connection requests and messages
"""
import json
import csv
import time
from datetime import datetime
from pathlib import Path

# Configuration
WORKSPACE = "/root/.openclaw/workspace/healthtech-directory"
DATA_DIR = f"{WORKSPACE}/data"
OUTREACH_DIR = f"{WORKSPACE}/outreach"


def load_decision_makers():
    """Load decision makers from CSV"""
    with open(f"{OUTREACH_DIR}/decision-makers.csv") as f:
        reader = csv.DictReader(f)
        return list(reader)


def create_message(dm: dict, company: dict, touch: int = 0) -> str:
    """Create personalized message based on touch number"""
    
    templates = {
        0: f"""Subject: Executive PMO Leadership - {company['company']}

Hi {dm['decision_maker'].split()[-1]},

I noticed {company['company']} is leading digital transformation in {company['location'].split(',')[0]}'s healthcare sector.

I'm a Senior Technology Executive with 20+ years experience:
• SGH (Egypt): Led $50M transformation, reduced reporting by 97%
• Talabat (GCC): Scaled operations 233x in 18 months
• Network (8 countries): PMO for 300+ projects

I'm exploring senior leadership opportunities in HealthTech, particularly PMO, Digital Transformation, or CDO roles.

Would you have 15 minutes for a brief call this week?

Best regards,
Ahmed Nasr
Senior Technology Executive | PMO & AI Transformation""",
        
        3: f"""Subject: Re: Executive PMO Leadership - {company['company']}

Hi {dm['decision_maker'].split()[-1]},

Just following up on my previous message about {company['company']}'s digital transformation initiatives.

I'm confident my experience could add value, particularly given:
• Proven track record with $50M+ transformations
• GCC market expertise (SGH, Talabat, Network)
• AI/Automation leadership at scale

Happy to share my portfolio or schedule a brief call at your convenience.

Best,
Ahmed""",
        
        7: f"""Subject: One last thought - {company['company']}

Hi {dm['decision_maker'].split()[-1]},

I'll keep this brief. My background:
• 20+ years in technology leadership
• $50M transformation delivery
• GCC HealthTech expertise

If {company['company']} is exploring senior technology leadership, I'd welcome the opportunity to discuss.

My calendar: https://calendly.com/ahmednasr

Best,
Ahmed"""
    }
    
    return templates.get(touch, templates[0])


def create_automation_queue():
    """Create automation queue for all messages"""
    dms = load_decision_makers()
    
    queue = []
    
    for dm in dms:
        company = {
            'company': dm['company'],
            'website': dm['website'],
            'location': dm['location']
        }
        
        # Create 3-touch sequence
        for touch in [0, 3, 7]:
            message = create_message(dm, company, touch)
            
            queue.append({
                'company': dm['company'],
                'decision_maker': dm['decision_maker'],
                'linkedin': dm['linkedin'],
                'touch': touch,
                'message': message,
                'scheduled_day': touch,
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'sent_at': None,
                'response': None
            })
    
    # Save queue
    with open(f"{OUTREACH_DIR}/automation-queue.json", 'w') as f:
        json.dump({
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'total_messages': len(queue),
                'pending': len(queue),
                'sent': 0,
                'responses': 0
            },
            'queue': queue
        }, f, indent=2)
    
    print(f"✓ Created queue with {len(queue)} messages")
    return queue


def create_linkedin_urls():
    """Create LinkedIn URLs for automation"""
    dms = load_decision_makers()
    
    urls = []
    
    for dm in dms:
        urls.append({
            'company': dm['company'],
            'decision_maker': dm['decision_maker'],
            'linkedin_url': dm['linkedin'],
            'action': 'connect' if dm.get('connected', False) else 'message'
        })
    
    # Save URLs
    with open(f"{OUTREACH_DIR}/linkedin-urls.json", 'w') as f:
        json.dump({
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'total': len(urls)
            },
            'urls': urls
        }, f, indent=2)
    
    print(f"✓ Created {len(urls)} LinkedIn URLs")
    return urls


def create_email_blast():
    """Create email blast ready for sending"""
    dms = load_decision_makers()
    
    emails = []
    
    for dm in dms:
        company = {
            'company': dm['company'],
            'website': dm['website'],
            'location': dm['location']
        }
        
        message = create_message(dm, company, 0)
        
        emails.append({
            'to': dm['email'],
            'subject': f"Executive PMO Leadership - {company['company']}",
            'body': message,
            'status': 'ready'
        })
    
    # Save email blast
    with open(f"{OUTREACH_DIR}/email-blast.json", 'w') as f:
        json.dump({
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'total': len(emails)
            },
            'emails': emails
        }, f, indent=2)
    
    print(f"✓ Created email blast with {len(emails)} emails")
    return emails


def create_tracking_sheet():
    """Create Google Sheets-ready tracking sheet"""
    dms = load_decision_makers()
    
    rows = []
    
    for i, dm in enumerate(dms, 1):
        rows.append({
            'Priority': i,
            'Company': dm['company'],
            'Decision Maker': dm['decision_maker'],
            'Title': dm['title'],
            'LinkedIn URL': dm['linkedin'],
            'Email': dm['email'],
            'Day 0 (Sent)': '',
            'Day 3 (Follow-up)': '',
            'Day 7 (Final)': '',
            'Response': '',
            'Call Scheduled': '',
            'Notes': ''
        })
    
    # Save as CSV for Google Sheets import
    with open(f"{OUTREACH_DIR}/tracking-sheet.csv", 'w', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    
    print(f"✓ Created tracking sheet with {len(rows)} rows")


def main():
    """Main function"""
    print("=" * 60)
    print("Automated Outreach - Message Generation")
    print("=" * 60)
    print()
    
    # Create all outputs
    create_automation_queue()
    create_linkedin_urls()
    create_email_blast()
    create_tracking_sheet()
    
    print()
    print("=" * 60)
    print("Automation Ready")
    print("=" * 60)
    print()
    print("Files created:")
    print(f"  • {OUTREACH_DIR}/automation-queue.json")
    print(f"  • {OUTREACH_DIR}/linkedin-urls.json")
    print(f"  • {OUTREACH_DIR}/email-blast.json")
    print(f"  • {OUTREACH_DIR}/tracking-sheet.csv")
    print()
    print("Next: Use browser automation or email client to send")


if __name__ == "__main__":
    main()
