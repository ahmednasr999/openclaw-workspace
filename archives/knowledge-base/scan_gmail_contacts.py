#!/usr/bin/env python3
"""
Gmail Multi-Folder Contact Scanner
Scans key folders (not all mail) for speed and reliability
"""

import subprocess, json, sqlite3, re
from datetime import datetime
from collections import defaultdict

DB_PATH = "/root/.openclaw/workspace/knowledge-base/kb.db"
MY_EMAIL = "ahmednasr999@gmail.com"

# Folders to scan (high-signal only)
FOLDERS = ["INBOX", "Sent", "[Gmail]/Sent Mail", "Jobs", "FollowUp.cc", "LinkedIN"]
PAGE_SIZE = 50

# Noise domains/patterns
NOISE = [
    "noreply", "no-reply", "newsletter", "marketing", "notifications@",
    "info@", "support@", "help@", "automated", "skool.com", "substack.com",
    "jobs@", "invitations@linkedin", "github.com", "gulftalent", "bayt.com",
    "donotreply", "do-not-reply", "alerts@", "updates@", "digest@"
]

def is_noise(email):
    e = email.lower()
    return any(n in e for n in NOISE)

def scan_folder(folder, pages=3):
    """Scan a folder, up to N pages"""
    results = []
    for page in range(1, pages + 1):
        try:
            r = subprocess.run(
                ["himalaya", "envelope", "list",
                 "--folder", folder,
                 "--page-size", str(PAGE_SIZE),
                 "--page", str(page),
                 "--output", "json"],
                capture_output=True, text=True, timeout=30
            )
            raw = r.stdout
            lines = [l for l in raw.split('\n') if l.strip().startswith('[') or l.strip().startswith('{')]
            if not lines:
                break
            data = json.loads('\n'.join(lines))
            if not data:
                break
            results.extend(data)
            print(f"  📂 {folder} page {page}: {len(data)} emails")
            if len(data) < PAGE_SIZE:
                break  # Last page
        except Exception as e:
            print(f"  ⚠️  {folder} page {page}: {e}")
            break
    return results

def extract_contacts(emails, direction="inbound"):
    """Extract contacts from email list"""
    contacts = defaultdict(lambda: {"names": set(), "dates": [], "subjects": [], "direction": direction})
    
    for email in emails:
        if direction == "inbound":
            person = email.get("from", {})
        else:
            # Sent mail — extract recipient
            person = email.get("to", {})
        
        addr = (person.get("addr") or "").lower().strip()
        name = (person.get("name") or "").strip()
        
        if not addr or addr == MY_EMAIL:
            continue
        if is_noise(addr):
            continue
        
        contacts[addr]["names"].add(name)
        contacts[addr]["dates"].append(email.get("date", ""))
        contacts[addr]["subjects"].append(email.get("subject", ""))
    
    return contacts

def infer_role(email_addr, names):
    e = email_addr.lower()
    n = " ".join(names).lower()
    combined = e + " " + n
    if any(x in combined for x in ["recruit", "talent", "hr@", "hiring"]):
        return "recruiter"
    if any(x in combined for x in ["ceo", "cto", "cfo", "vp ", "founder", "president"]):
        return "executive"
    if any(x in combined for x in ["manager", "director", "head of", "lead"]):
        return "manager"
    return "contact"

def infer_company(email_addr):
    domain = email_addr.split("@")[-1] if "@" in email_addr else ""
    # Strip common email providers
    generic = ["gmail.com","yahoo.com","hotmail.com","outlook.com","icloud.com","me.com"]
    if domain in generic:
        return None
    # Clean company name from domain
    company = domain.split(".")[0].replace("-","").title()
    return company

def save_to_db(all_contacts):
    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    try:
        conn.execute("SELECT load_extension('/usr/local/lib/python3.13/dist-packages/sqlite_vec/vec0.so')")
    except:
        pass  # Vec extension optional for now

    added = updated = interactions = 0

    for email_addr, data in all_contacts.items():
        names = [n for n in data["names"] if n]
        best_name = max(names, key=len) if names else email_addr.split("@")[0].title()
        latest_date = max(data["dates"]) if data["dates"] else None
        role = infer_role(email_addr, names)
        company = infer_company(email_addr)
        domain = email_addr.split("@")[-1] if "@" in email_addr else ""
        direction = data["direction"]

        # Upsert contact
        cur = conn.execute("SELECT id FROM contacts WHERE email=?", (email_addr,))
        row = cur.fetchone()

        if row:
            conn.execute("""
                UPDATE contacts SET name=?, company=?, role=?, domain=?,
                last_contact_date=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (best_name, company, role, domain, latest_date, row[0]))
            contact_id = row[0]
            updated += 1
        else:
            cur = conn.execute("""
                INSERT INTO contacts (email, name, company, role, domain, source, last_contact_date, is_noisy)
                VALUES (?,?,?,?,?,'gmail',?,0)
            """, (email_addr, best_name, company, role, domain, latest_date))
            contact_id = cur.lastrowid
            added += 1

        # Log interactions (deduplicated by subject)
        for i, subj in enumerate(data["subjects"]):
            date = data["dates"][i] if i < len(data["dates"]) else latest_date
            cur = conn.execute(
                "SELECT id FROM interactions WHERE contact_id=? AND subject=? AND date=?",
                (contact_id, subj, date)
            )
            if not cur.fetchone():
                conn.execute("""
                    INSERT INTO interactions (contact_id, type, direction, subject, date, source)
                    VALUES (?, 'email', ?, ?, ?, 'gmail')
                """, (contact_id, direction, subj, date))
                interactions += 1

    conn.commit()
    conn.close()
    return added, updated, interactions

def main():
    print("🚀 Gmail Multi-Folder Contact Scanner\n")

    all_contacts = defaultdict(lambda: {"names": set(), "dates": [], "subjects": [], "direction": "inbound"})

    folder_map = {
        "INBOX": "inbound",
        "Sent": "outbound",
        "[Gmail]/Sent Mail": "outbound",
        "Jobs": "inbound",
        "FollowUp.cc": "inbound",
        "LinkedIN": "inbound",
    }

    for folder, direction in folder_map.items():
        print(f"\n📁 Scanning: {folder}")
        emails = scan_folder(folder, pages=5)
        contacts = extract_contacts(emails, direction)
        print(f"  👥 {len(contacts)} contacts found")

        for addr, data in contacts.items():
            all_contacts[addr]["names"].update(data["names"])
            all_contacts[addr]["dates"].extend(data["dates"])
            all_contacts[addr]["subjects"].extend(data["subjects"])
            # Outbound = stronger signal
            if direction == "outbound":
                all_contacts[addr]["direction"] = "outbound"

    print(f"\n📊 Total unique contacts: {len(all_contacts)}")

    added, updated, interactions = save_to_db(all_contacts)

    print(f"\n✅ Done!")
    print(f"   Added:        {added}")
    print(f"   Updated:      {updated}")
    print(f"   Interactions: {interactions}")

    # Show top contacts (most interactions)
    conn = sqlite3.connect(DB_PATH)
    print("\n👤 Top contacts by interactions:")
    cur = conn.execute("""
        SELECT c.name, c.email, c.company, c.role,
               COUNT(i.id) as interactions,
               MAX(i.date) as last_contact
        FROM contacts c
        LEFT JOIN interactions i ON c.id = i.contact_id
        WHERE c.is_noisy = 0
        GROUP BY c.id
        ORDER BY interactions DESC, last_contact DESC
        LIMIT 15
    """)
    for r in cur.fetchall():
        print(f"   • {str(r[0] or ''):<25} {str(r[1] or ''):<35} {str(r[2] or ''):<20} {r[4]} emails")
    conn.close()

if __name__ == "__main__":
    main()
