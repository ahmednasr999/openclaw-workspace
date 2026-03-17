#!/usr/bin/env python3
"""
HealthTech Directory - Gmail Integration
Creates email templates ready for Gmail
"""
import json
import csv
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace/healthtech-directory"
OUTREACH_DIR = f"{WORKSPACE}/outreach"

def create_gmail_templates():
    """Create Gmail-ready templates"""
    dms = load_decision_makers()
    
    print("=" * 60)
    print("Gmail Template Creator")
    print("=" * 60)
    print()
    
    templates_dir = f"{OUTREACH_DIR}/gmail-templates"
    Path(templates_dir).mkdir(exist_ok=True)
    
    # Create CSV for Gmail Import
    gmail_csv = []
    
    for i, dm in enumerate(dms, 1):
        company = dm['company']
        contact = dm['decision_maker']
        email = dm['email']
        first_name = contact.split()[0] if contact else 'there'
        
        subject = f"Executive PMO Leadership - {company}"
        body = f"""Hi {first_name},

I noticed {company} is leading digital transformation in the GCC healthcare sector.

I'm a Senior Technology Executive with 20+ years experience:
• SGH (Egypt): Led $50M transformation, reduced reporting by 97%
• Talabat (GCC): Scaled operations 233x in 18 months
• Network (8 countries): PMO for 300+ projects

I'm exploring senior leadership opportunities in HealthTech, particularly PMO, Digital Transformation, or CDO roles.

Would you have 15 minutes for a brief call this week?

Best regards,
Ahmed Nasr
Senior Technology Executive | PMO & AI Transformation"""
        
        gmail_csv.append({
            'to': email,
            'subject': subject,
            'body': body,
            'company': company,
            'status': 'pending'
        })
        
        # Save individual template
        template_file = f"{templates_dir}/{i:02d}_{company.replace(' ', '_')}.txt"
        with open(template_file, 'w') as f:
            f.write(f"TO: {email}\n")
            f.write(f"SUBJECT: {subject}\n")
            f.write("-" * 50 + "\n")
            f.write(body)
        
        print(f"  {i:2}. {company} -> {email}")
    
    # Save Gmail Import CSV
    gmail_csv_file = f"{OUTREACH_DIR}/gmail-import.csv"
    with open(gmail_csv_file, 'w', newline='', encoding='utf-8') as f:
        if gmail_csv:
            writer = csv.DictWriter(f, fieldnames=gmail_csv[0].keys())
            writer.writeheader()
            writer.writerows(gmail_csv)
    
    # Save JSON for automation
    templates_json = {
        'metadata': {
            'created_at': '2026-02-17',
            'total': len(gmail_csv),
            'pending': len(gmail_csv)
        },
        'templates': gmail_csv
    }
    
    with open(f"{OUTREACH_DIR}/gmail-templates.json", 'w') as f:
        json.dump(templates_json, f, indent=2)
    
    print()
    print(f"✓ Created {len(gmail_csv)} templates")
    print(f"✓ Gmail Import CSV: {gmail_csv_file}")
    print(f"✓ Templates folder: {templates_dir}/")
    print()
    
    return gmail_csv


def create_quick_send_list():
    """Create a simple list for quick copy/paste sending"""
    dms = load_decision_makers()
    
    output = []
    
    for i, dm in enumerate(dms, 1):
        company = dm['company']
        email = dm['email']
        first_name = dm['decision_maker'].split()[0]
        
        subject = f"Executive PMO Leadership - {company}"
        body = f"""Hi {first_name},

I noticed {company} is leading digital transformation in the GCC healthcare sector.

I'm a Senior Technology Executive with 20+ years experience:
• SGH (Egypt): Led $50M transformation, reduced reporting by 97%
• Talabat (GCC): Scaled operations 233x in 18 months
• Network (8 countries): PMO for 300+ projects

Would you have 15 minutes for a brief call this week?

Best,
Ahmed"""
        
        output.append({
            'number': i,
            'company': company,
            'email': email,
            'subject': subject,
            'body': body,
            'status': 'pending'
        })
    
    # Save simple list
    with open(f"{OUTREACH_DIR}/quick-send-list.json", 'w') as f:
        json.dump(output, f, indent=2)
    
    # Create markdown version
    with open(f"{OUTREACH_DIR}/QUICK_SEND_LIST.md", 'w') as f:
        f.write("# Quick Send List\n\n")
        f.write("## Instructions\n\n")
        f.write("1. Open Gmail\n")
        f.write("2. Compose new email\n")
        f.write("3. Copy from below\n")
        f.write("4. Send!\n\n")
        f.write("---\n\n")
        
        for item in output:
            f.write(f"## {item['number']}. {item['company']}\n\n")
            f.write(f"**To:** {item['email']}\n\n")
            f.write(f"**Subject:** {item['subject']}\n\n")
            f.write("```\n")
            f.write(item['body'])
            f.write("\n```\n\n")
            f.write("---\n\n")
    
    print(f"✓ Created QUICK_SEND_LIST.md")
    print(f"✓ Created quick-send-list.json")
    
    return output


def load_decision_makers():
    """Load decision makers"""
    with open(f"{OUTREACH_DIR}/decision-makers.csv") as f:
        reader = csv.DictReader(f)
        return list(reader)


def main():
    """Main function"""
    print("=" * 60)
    print("Gmail Integration")
    print("=" * 60)
    print()
    
    create_gmail_templates()
    create_quick_send_list()
    
    print()
    print("=" * 60)
    print("Files Created")
    print("=" * 60)
    print()
    print("1. gmail-import.csv - Import to Gmail (File > Import)")
    print("2. QUICK_SEND_LIST.md - Copy/paste format")
    print("3. gmail-templates/ - Individual template files")
    print("4. quick-send-list.json - Programmatic access")
    print()
    print("Next:")
    print("  1. Open QUICK_SEND_LIST.md")
    print("  2. Copy/paste emails to Gmail")
    print("  3. Review and send!")


if __name__ == "__main__":
    main()
