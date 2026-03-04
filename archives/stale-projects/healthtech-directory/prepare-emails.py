#!/usr/bin/env python3
"""
HealthTech Directory - Email Sender
Prepares emails for manual sending
"""
import json
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace/healthtech-directory"
OUTREACH_DIR = f"{WORKSPACE}/outreach"

def create_email_file():
    """Create a simple email file for easy copy/paste"""
    
    # Load decision makers
    with open(f"{OUTREACH_DIR}/decision-makers.csv") as f:
        lines = f.readlines()
        headers = lines[0].strip().split(',')
        dms = []
        for line in lines[1:]:
            values = line.strip().split(',')
            dm = dict(zip(headers, values))
            dms.append(dm)
    
    # Create simple email list
    simple_emails = []
    for dm in dms:
        simple_emails.append({
            "company": dm['company'],
            "contact": dm['decision_maker'],
            "email": dm['email'],
            "subject": f"Executive PMO Leadership - {dm['company']}",
            "body": f"""Hi {dm['decision_maker'].split()[-1]},

I noticed {dm['company']} is leading digital transformation in the {dm['location'].split(',')[0]} healthcare sector.

I'm a Senior Technology Executive with 20+ years experience:
• SGH (Egypt): Led $50M transformation, reduced reporting by 97%
• Talabat (GCC): Scaled operations 233x in 18 months
• Network (8 countries): PMO for 300+ projects

I'm exploring senior leadership opportunities in HealthTech, particularly PMO, Digital Transformation, or CDO roles.

Would you have 15 minutes for a brief call this week?

Best regards,
Ahmed Nasr
Senior Technology Executive | PMO & AI Transformation"""
        })
    
    # Save simple JSON
    with open(f"{OUTREACH_DIR}/simple-emails.json", 'w') as f:
        json.dump(simple_emails, f, indent=2)
    
    # Create easy copy/paste markdown
    with open(f"{OUTREACH_DIR}/EASY_COPYPASTE.md", 'w') as f:
        f.write("# Easy Copy/Paste Emails\n\n")
        f.write("## Instructions\n\n")
        f.write("1. Open Gmail\n")
        f.write("2. Create label: `HealthTech Outreach`\n")
        f.write("3. Copy each email below\n")
        f.write("4. Send!\n\n")
        f.write("---\n\n")
        
        for i, email in enumerate(simple_emails, 1):
            f.write(f"## {i}. {email['company']}\n\n")
            f.write(f"**To:** {email['email']}\n\n")
            f.write(f"**Subject:** {email['subject']}\n\n")
            f.write("```\n")
            f.write(email['body'])
            f.write("\n```\n\n")
            f.write("---\n\n")
    
    print(f"✓ Created simple-emails.json ({len(simple_emails)} emails)")
    print(f"✓ Created EASY_COPYPASTE.md (ready to copy)")
    
    return simple_emails

def create_batch_files():
    """Create batch files for easy sending"""
    
    with open(f"{OUTREACH_DIR}/simple-emails.json") as f:
        emails = json.load(f)
    
    # Batch 1 (1-10)
    batch1 = emails[:10]
    with open(f"{OUTREACH_DIR}/BATCH1_1-10.txt", 'w') as f:
        for email in batch1:
            f.write(f"TO: {email['email']}\n")
            f.write(f"SUBJECT: {email['subject']}\n")
            f.write("-" * 50 + "\n")
            f.write(email['body'])
            f.write("\n\n" + "=" * 50 + "\n\n")
    
    # Batch 2 (11-20)
    batch2 = emails[10:20]
    with open(f"{OUTREACH_DIR}/BATCH2_11-20.txt", 'w') as f:
        for email in batch2:
            f.write(f"TO: {email['email']}\n")
            f.write(f"SUBJECT: {email['subject']}\n")
            f.write("-" * 50 + "\n")
            f.write(email['body'])
            f.write("\n\n" + "=" * 50 + "\n\n")
    
    # Batch 3 (21-30)
    batch3 = emails[20:30]
    with open(f"{OUTREACH_DIR}/BATCH3_21-30.txt", 'w') as f:
        for email in batch3:
            f.write(f"TO: {email['email']}\n")
            f.write(f"SUBJECT: {email['subject']}\n")
            f.write("-" * 50 + "\n")
            f.write(email['body'])
            f.write("\n\n" + "=" * 50 + "\n\n")
    
    # Batch 4 (31-40)
    batch4 = emails[30:40]
    with open(f"{OUTREACH_DIR}/BATCH4_31-40.txt", 'w') as f:
        for email in batch4:
            f.write(f"TO: {email['email']}\n")
            f.write(f"SUBJECT: {email['subject']}\n")
            f.write("-" * 50 + "\n")
            f.write(email['body'])
            f.write("\n\n" + "=" * 50 + "\n\n")
    
    # Batch 5 (41-47)
    batch5 = emails[40:]
    with open(f"{OUTREACH_DIR}/BATCH5_41-47.txt", 'w') as f:
        for email in batch5:
            f.write(f"TO: {email['email']}\n")
            f.write(f"SUBJECT: {email['subject']}\n")
            f.write("-" * 50 + "\n")
            f.write(email['body'])
            f.write("\n\n" + "=" * 50 + "\n\n")
    
    print(f"✓ Created BATCH1_1-10.txt (send today)")
    print(f"✓ Created BATCH2_11-20.txt")
    print(f"✓ Created BATCH3_21-30.txt")
    print(f"✓ Created BATCH4_31-40.txt")
    print(f"✓ Created BATCH5_41-47.txt")

if __name__ == "__main__":
    print("=" * 60)
    print("Email Preparation System")
    print("=" * 60)
    print()
    
    create_email_file()
    create_batch_files()
    
    print()
    print("=" * 60)
    print("Files Created")
    print("=" * 60)
    print()
    print("Easy options:")
    print("  1. GMAIL_TEMPLATES.md - Full templates with instructions")
    print("  2. EASY_COPYPASTE.md - Simple copy/paste format")
    print("  3. BATCH1_1-10.txt - First 10 emails to send today")
    print("  4. simple-emails.json - Programmatic access")
    print()
    print("Quick start:")
    print("  cat EASY_COPYPASTE.md")
