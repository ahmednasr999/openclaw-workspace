#!/usr/bin/env python3
"""
HealthTech Directory - Gmail Draft Creator
Creates drafts in Gmail for review and confirmation
"""
import json
import csv
from pathlib import Path

# Configuration
WORKSPACE = "/root/.openclaw/workspace/healthtech-directory"
OUTREACH_DIR = f"{WORKSPACE}/outreach"
DRAFTS_FILE = f"{OUTREACH_DIR}/drafts-status.json"


def load_decision_makers():
    """Load decision makers from CSV"""
    with open(f"{OUTREACH_DIR}/decision-makers.csv") as f:
        reader = csv.DictReader(f)
        return list(reader)


def create_gmail_drafts():
    """Create Gmail drafts for all decision makers"""
    dms = load_decision_makers()
    
    print("=" * 60)
    print("Gmail Draft Creator")
    print("=" * 60)
    print()
    
    drafts = []
    
    for i, dm in enumerate(dms, 1):
        company = dm['company']
        contact = dm['decision_maker']
        email = dm['email']
        first_name = contact.split()[0] if contact else 'there'
        
        # Create email content
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
        
        draft = {
            "id": i,
            "company": company,
            "contact": contact,
            "email": email,
            "subject": subject,
            "body": body,
            "status": "pending_review",  # pending_review, approved, sent
            "created_at": "2026-02-17",
            "reviewed_by": None,
            "reviewed_at": None,
            "notes": None
        }
        
        drafts.append(draft)
        
        print(f"  {i:2}. {company}")
        print(f"      → {email}")
    
    # Save drafts status
    with open(DRAFTS_FILE, 'w') as f:
        json.dump({
            "metadata": {
                "created_at": "2026-02-17",
                "total": len(drafts),
                "pending_review": len(drafts),
                "approved": 0,
                "sent": 0
            },
            "drafts": drafts
        }, f, indent=2)
    
    print()
    print(f"✓ Created {len(drafts)} drafts")
    print(f"✓ Saved to: {DRAFTS_FILE}")
    print()
    
    return drafts


def list_drafts():
    """List all drafts with status"""
    with open(DRAFTS_FILE) as f:
        data = json.load(f)
    
    print("=" * 60)
    print("Draft Status")
    print("=" * 60)
    print()
    
    drafts = data['drafts']
    metadata = data['metadata']
    
    print(f"Total: {metadata['total']}")
    print(f"Pending Review: {metadata['pending_review']}")
    print(f"Approved: {metadata['approved']}")
    print(f"Sent: {metadata['sent']}")
    print()
    
    # Show pending
    pending = [d for d in drafts if d['status'] == 'pending_review']
    for d in pending[:5]:
        print(f"  ⏳ {d['company']} - {d['email']}")
    
    if len(pending) > 5:
        print(f"  ... and {len(pending) - 5} more")
    
    print()
    
    # Show approved
    approved = [d for d in drafts if d['status'] == 'approved']
    if approved:
        print("Ready to send:")
        for d in approved[:5]:
            print(f"  ✅ {d['company']} - {d['email']}")
        if len(approved) > 5:
            print(f"  ... and {len(approved) - 5} more")
    
    print()
    
    return data


def approve_draft(draft_id: int, notes: str = None):
    """Approve a draft for sending"""
    with open(DRAFTS_FILE) as f:
        data = json.load(f)
    
    for draft in data['drafts']:
        if draft['id'] == draft_id:
            draft['status'] = 'approved'
            draft['reviewed_by'] = 'Ahmed'
            draft['reviewed_at'] = '2026-02-17'
            draft['notes'] = notes
            break
    
    data['metadata']['pending_review'] -= 1
    data['metadata']['approved'] += 1
    
    with open(DRAFTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Draft {draft_id} approved")
    return data


def approve_all():
    """Approve all drafts"""
    with open(DRAFTS_FILE) as f:
        data = json.load(f)
    
    approved = 0
    for draft in data['drafts']:
        if draft['status'] == 'pending_review':
            draft['status'] = 'approved'
            draft['reviewed_by'] = 'Ahmed'
            draft['reviewed_at'] = '2026-02-17'
            approved += 1
    
    data['metadata']['pending_review'] = 0
    data['metadata']['approved'] = approved
    
    with open(DRAFTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Approved {approved} drafts")
    return data


def mark_sent(draft_id: int):
    """Mark a draft as sent"""
    with open(DRAFTS_FILE) as f:
        data = json.load(f)
    
    for draft in data['drafts']:
        if draft['id'] == draft_id:
            draft['status'] = 'sent'
            break
    
    data['metadata']['approved'] -= 1
    data['metadata']['sent'] += 1
    
    with open(DRAFTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Draft {draft_id} marked as sent")
    return data


def get_approved_drafts():
    """Get all approved drafts ready to send"""
    with open(DRAFTS_FILE) as f:
        data = json.load(f)
    
    return [d for d in data['drafts'] if d['status'] == 'approved']


def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'create':
            create_gmail_drafts()
        elif command == 'list':
            list_drafts()
        elif command == 'approve':
            draft_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
            notes = sys.argv[3] if len(sys.argv) > 3 else None
            if draft_id:
                approve_draft(draft_id, notes)
        elif command == 'approve_all':
            approve_all()
        elif command == 'sent':
            draft_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
            if draft_id:
                mark_sent(draft_id)
        elif command == 'get_approved':
            drafts = get_approved_drafts()
            print(f"Approved: {len(drafts)}")
            for d in drafts:
                print(f"  {d['id']}: {d['company']} -> {d['email']}")
    else:
        # Default: create drafts and show status
        create_gmail_drafts()
        list_drafts()


if __name__ == "__main__":
    main()
