#!/usr/bin/env python3
"""
Gmail Contact Extractor for Personal CRM
Scans Gmail via Himalaya to discover contacts from the past year
"""

import subprocess
import json
import sqlite3
import re
from datetime import datetime, timedelta
from collections import defaultdict

DB_PATH = "/root/.openclaw/workspace/knowledge-base/kb.db"

# Noise patterns to filter
NOISE_PATTERNS = [
    r"newsletter",
    r"newsletter@",
    r"@newsletter",
    r"marketing",
    r"marketing@",
    r"promotions",
    r"deals",
    r"discount",
    r"unsubscribe",
    r"no-reply",
    r"noreply@",
    r"automated",
    r"system@",
    r"support@",
    r"help@",
    r"info@",
    r"hello@",  # Generic hello@ emails are often noise
]

def is_noise_email(email):
    """Check if email is likely noise (newsletter, marketing, etc.)"""
    email_lower = email.lower()
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, email_lower):
            return True
    return False

def extract_name_from_email(email):
    """Extract potential name from email"""
    local = email.split('@')[0]
    # Remove common patterns
    local = re.sub(r'\d+', '', local)
    local = re.sub(r'[._-]', ' ', local)
    return local.title().strip()

def get_gmail_emails(days_back=90):
    """Get recent emails from Himalaya (last N days)"""
    cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    try:
        result = subprocess.run(
            ["himalaya", "envelope", "list", "--output", "json", f"after {cutoff_date}"],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error: {e}")
                print(f"Raw output: {result.stdout[:500]}")
                return []
        else:
            print(f"❌ Himalaya error: {result.stderr}")
            return []
    except Exception as e:
        print(f"❌ Error running himalaya: {e}")
        return []

def scan_gmail_for_contacts():
    """Main function to scan Gmail and extract contacts"""
    print("📧 Scanning Gmail for contacts...")
    
    emails = get_gmail_emails(500)
    print(f"📬 Retrieved {len(emails)} emails")
    
    # Group by sender
    senders = defaultdict(lambda: {
        "emails": set(),
        "names": set(),
        "subjects": [],
        "dates": [],
        "domains": set()
    })
    
    cutoff_date = datetime.now() - timedelta(days=365)
    
    for email in emails:
        # Parse sender
        from_field = email.get("from", "")
        date_str = email.get("date", "")
        
        # Extract email and name
        match = re.match(r'"?([^"<]*)"?\s*<([^>]+)>', from_field)
        if match:
            name = match.group(1).strip()
            email_addr = match.group(2).strip().lower()
        else:
            # Just email or just name
            if "@" in from_field:
                email_addr = from_field.strip().lower()
                name = extract_name_from_email(email_addr)
            else:
                name = from_field.strip()
                email_addr = None
        
        if not email_addr:
            continue
        
        # Skip noise
        if is_noise_email(email_addr):
            continue
        
        # Parse date
        try:
            email_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if email_date < cutoff_date:
                continue
        except:
            continue
        
        # Extract company from domain
        domain = email_addr.split('@')[-1] if '@' in email_addr else ""
        
        # Add to senders
        senders[email_addr]["emails"].add(email_addr)
        if name:
            senders[email_addr]["names"].add(name)
        senders[email_addr]["subjects"].append(email.get("subject", ""))
        senders[email_addr]["dates"].append(date_str)
        senders[email_addr]["domains"].add(domain)
    
    print(f"👥 Found {len(senders)} unique contacts (past year, excluding noise)")
    
    # Store in database
    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    
    added = 0
    updated = 0
    
    for email_addr, data in senders.items():
        names = list(data["names"])
        domains = list(data["domains"])
        
        # Determine role based on email pattern
        role = "unknown"
        if any(x in email_addr for x in ['recruiter', 'talent', 'hr', 'hiring']):
            role = "recruiter"
        elif any(x in email_addr for x in ['manager', 'lead', 'director', 'head']):
            role = "hiring_manager"
        elif any(x in email_addr for x in ['ceo', 'cto', 'cfo', 'vp', 'founder']):
            role = "executive"
        elif 'linkedin' in domains:
            role = "linkedin"
        
        # Check if exists
        cursor = conn.execute("SELECT id, name, company FROM contacts WHERE email = ?", (email_addr,))
        existing = cursor.fetchone()
        
        if existing:
            # Update
            conn.execute("""
                UPDATE contacts SET 
                    name = ?, company = ?, role = ?, source = 'gmail',
                    last_contact_date = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (", ".join(names) if names else None, domains[0] if domains else None, role, 
                  max(data["dates"]) if data["dates"] else None, existing[0]))
            updated += 1
        else:
            # Insert
            conn.execute("""
                INSERT INTO contacts (email, name, company, role, source, last_contact_date, is_noisy)
                VALUES (?, ?, ?, ?, 'gmail', ?, 0)
            """, (email_addr, ", ".join(names) if names else None, 
                  domains[0] if domains else None, role, 
                  max(data["dates"]) if data["dates"] else None))
            added += 1
    
    conn.commit()
    
    # Print summary
    cursor = conn.execute("SELECT COUNT(*) FROM contacts WHERE source = 'gmail'")
    total = cursor.fetchone()[0]
    
    cursor = conn.execute("SELECT COUNT(*) FROM contacts WHERE is_noisy = 1")
    noisy = cursor.fetchone()[0]
    
    print(f"\n📊 CRM Contact Summary:")
    print(f"   Total Gmail contacts: {total}")
    print(f"   Marked as noise: {noisy}")
    print(f"   Added this run: {added}")
    print(f"   Updated: {updated}")
    
    # Show some contacts
    print(f"\n👤 Sample contacts:")
    cursor = conn.execute("""
        SELECT name, email, company, role, last_contact_date 
        FROM contacts 
        WHERE source = 'gmail' AND is_noisy = 0
        ORDER BY last_contact_date DESC 
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(f"   • {row[0]} | {row[1]} | {row[2]} | {row[3]}")
    
    conn.close()
    
    return senders

if __name__ == "__main__":
    scan_gmail_for_contacts()
