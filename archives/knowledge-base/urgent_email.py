#!/usr/bin/env python3
"""
Urgent Email Detection System
Scans Gmail for urgent emails and learns from feedback
"""

import subprocess, json, sqlite3, re
from datetime import datetime, timedelta
from collections import defaultdict

DB_PATH = "/root/.openclaw/workspace/knowledge-base/kb.db"

# Urgency keywords (weight-based scoring)
URGENCY_KEYWORDS = {
    # High urgency (weight 3)
    3: ["urgent", "asap", "immediately", "emergency", "critical", "deadline today", 
        "response required", "time sensitive", "act now", "expires today", "breaking"],
    # Medium urgency (weight 2)
    2: ["important", "please respond", "need your input", "by tomorrow", "due soon",
        "priority", "attention required", "decision needed", "blocked", "help needed"],
    # Low urgency (weight 1)
    1: ["please", "feedback", "question", "inquiry", "thoughts", "update", 
        "follow up", "check in", "checking in", "touch base"]
}

# Noise patterns (always skip)
NOISE_PATTERNS = [
    "newsletter", "marketing", "promotions", "deals", "discount",
    "noreply", "no-reply", "automated", "system", "donotreply",
    "unsubscribe", "no longer subscribed", "weekly digest", "monthly roundup",
    "skool.com", "substack.com", "beehiiv.com", "yourstory.com", "thedefiant.io"
]

def is_noise_email(email_addr, subject):
    """Check if email is likely noise"""
    combined = (email_addr + " " + subject).lower()
    return any(pat in combined for pat in NOISE_PATTERNS)

def calculate_urgency_score(subject, sender):
    """Calculate urgency score (0-10)"""
    text = (subject + " " + sender).lower()
    score = 0
    
    for weight, keywords in URGENCY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                score += weight
                break  # Only count highest weight match
    
    # Cap at 10
    return min(score, 10)

def scan_emails():
    """Scan INBOX for urgency"""
    result = subprocess.run(
        ["himalaya", "envelope", "list", "--folder", "INBOX", "--page-size", "30", "--output", "json"],
        capture_output=True, text=True, timeout=120
    )
    
    if result.returncode != 0:
        print(f"❌ Himalaya error: {result.stderr}")
        return []
    
    # Parse JSON - output is an array
    try:
        emails = json.loads(result.stdout)
    except json.JSONDecodeError:
        emails = []
    
    processed = []
    
    for email in emails:
        subject = email.get("subject", "")
        from_field = email.get("from", {})
        sender_addr = from_field.get("addr", "").lower()
        sender_name = from_field.get("name", "")
        date = email.get("date", "")[:10]
        
        # Skip noise
        if is_noise_email(sender_addr, subject):
            continue
        
        # Calculate urgency
        score = calculate_urgency_score(subject, sender_addr)
        
        processed.append({
            "subject": subject,
            "sender_addr": sender_addr,
            "sender_name": sender_name,
            "date": date,
            "urgency_score": score
        })
    
    # Sort by urgency
    processed.sort(key=lambda x: -x["urgency_score"])
    return processed

def init_db():
    """Initialize database for email tracking"""
    conn = sqlite3.connect(DB_PATH)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS email_scan_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            emails_scanned INTEGER,
            urgent_count INTEGER
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS email_urgency_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_addr TEXT,
            subject TEXT,
            original_score INTEGER,
            feedback_score INTEGER,
            is_urgent INTEGER,
            feedback_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS learned_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern TEXT UNIQUE,
            weight INTEGER DEFAULT 1,
            is_sender INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

def save_scan_results(emails):
    """Save scan results to database"""
    conn = sqlite3.connect(DB_PATH)
    
    urgent_count = sum(1 for e in emails if e["urgency_score"] >= 5)
    
    # Log scan
    conn.execute("INSERT INTO email_scan_log (emails_scanned, urgent_count) VALUES (?, ?)",
                 (len(emails), urgent_count))
    
    # Store urgent emails (score >= 5)
    for email in emails:
        if email["urgency_score"] >= 5:
            conn.execute("""
                INSERT OR IGNORE INTO email_urgency_feedback (email_addr, subject, original_score, is_urgent)
                VALUES (?, ?, ?, NULL)
            """, (email["sender_addr"], email["subject"], email["urgency_score"]))
    
    conn.commit()
    conn.close()
    return urgent_count

def record_feedback(email_addr, subject, was_urgent):
    """Record user feedback to improve detection"""
    conn = sqlite3.connect(DB_PATH)
    
    # Update existing record
    conn.execute("""
        UPDATE email_urgency_feedback 
        SET is_urgent = ?, feedback_time = CURRENT_TIMESTAMP
        WHERE email_addr = ? AND subject = ?
    """, (1 if was_urgent else 0, email_addr, subject))
    
    conn.commit()
    conn.close()

def get_urgent_emails():
    """Get emails marked as urgent from latest scan"""
    conn = sqlite3.connect(DB_PATH)
    
    urgent = conn.execute("""
        SELECT email_addr, subject, original_score, feedback_time
        FROM email_urgency_feedback
        WHERE is_urgent IS NULL
        ORDER BY original_score DESC
    """).fetchall()
    
    conn.close()
    return [{"email": r[0], "subject": r[1], "score": r[2], "time": r[3]} for r in urgent]

def scan_and_report():
    """Main scan and report function"""
    print("\n📧 URGENT EMAIL SCAN")
    print("=" * 50)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    emails = scan_emails()
    
    if not emails:
        print("📭 No emails found in INBOX")
        return []
    
    urgent_count = save_scan_results(emails)
    
    print(f"📊 Scanned {len(emails)} emails")
    print(f"⚠️  {urgent_count} potentially urgent")
    print()
    
    # Show urgent emails
    urgent_emails = [e for e in emails if e["urgency_score"] >= 5]
    
    if urgent_emails:
        print("🚨 POTENTIALLY URGENT:")
        print("-" * 50)
        for i, e in enumerate(urgent_emails[:10], 1):
            score_emoji = "🔴" if e["urgency_score"] >= 7 else "🟠"
            print(f"{score_emoji} {i}. {e['sender_name'] or e['sender_addr']}")
            print(f"   Subject: {e['subject'][:60]}...")
            print(f"   Score: {e['urgency_score']}/10 | {e['date']}")
            print()
        
        if len(urgent_emails) > 10:
            print(f"   ... and {len(urgent_emails) - 10} more")
    else:
        print("✅ No urgent emails detected")
    
    # Show recent non-urgent
    recent = [e for e in emails if e["urgency_score"] < 3][:5]
    if recent:
        print("\n📬 RECENT (not urgent):")
        for e in recent:
            print(f"   • {e['sender_name'] or e['sender_addr'][:30]}")
    
    return urgent_emails

def send_telegram_report():
    """Send report to Telegram"""
    emails = scan_emails()
    urgent_emails = [e for e in emails if e["urgency_score"] >= 5]
    
    text = f"📧 *Urgent Email Scan*\n\n"
    text += f"🕐 {datetime.now().strftime('%H:%M')}\n\n"
    
    if urgent_emails:
        text += f"⚠️ *{len(urgent_emails)} urgent emails:*\n\n"
        for e in urgent_emails[:5]:
            score_emoji = "🔴" if e["urgency_score"] >= 7 else "🟠"
            sender = e["sender_name"] or e["sender_addr"][:20]
            text += f"{score_emoji} *{sender}*\n"
            text += f"   {e['subject'][:45]}...\n\n"
    else:
        text += "✅ No urgent emails detected"
    
    subprocess.run(
        ["openclaw", "message", "send", "--target", "telegram:866838380", "--message", text],
        capture_output=True
    )

def approve_urgent(email_addr, subject):
    """Mark an email as actually urgent"""
    record_feedback(email_addr, subject, True)
    print(f"✅ Marked as urgent: {subject[:40]}...")

def reject_urgent(email_addr, subject):
    """Mark an email as not urgent"""
    record_feedback(email_addr, subject, False)
    print(f"✅ Marked as not urgent: {subject[:40]}...")

if __name__ == "__main__":
    import sys
    
    init_db()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--scan":
            scan_and_report()
        elif cmd == "--telegram":
            send_telegram_report()
        elif cmd == "--urgent":
            for e in get_urgent_emails():
                print(f"{e['score']:>2} | {e['email'][:30]:30} | {e['subject'][:40]}")
        elif cmd == "--feedback":
            if len(sys.argv) >= 4:
                action = sys.argv[2]
                email = sys.argv[3]
                subject = sys.argv[4] if len(sys.argv) > 4 else ""
                if action == "--urgent":
                    approve_urgent(email, subject)
                elif action == "--not-urgent":
                    reject_urgent(email, subject)
            else:
                print("Usage: python3 urgent_email.py --feedback --urgent|not-urgent <email> <subject>")
        else:
            print("Usage: python3 urgent_email.py [--scan|--telegram|--urgent|--feedback]")
    else:
        scan_and_report()
