#!/usr/bin/env python3
"""
Daily Briefing Generator - Telegram Edition
Generates morning briefing and sends to Telegram
"""

import sqlite3, subprocess, json, re, sys
from datetime import datetime, timedelta

DB_PATH = "/root/.openclaw/workspace/knowledge-base/kb.db"
TELEGRAM_CHAT = "telegram:866838380"  # Your personal chat

def get_meetings():
    """Get today's calendar events"""
    return {"status": "no_auth", "message": "Calendar not connected", "action": "gog calendar events"}

def get_urgent_emails(limit=5):
    """Get emails that might be urgent"""
    cutoff_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    
    result = subprocess.run(
        ["himalaya", "envelope", "list", "--output", "json", f"after {cutoff_date}"],
        capture_output=True, text=True, timeout=60
    )
    
    if result.returncode != 0:
        return []
    
    lines = [l for l in result.stdout.split('\n') if l.strip().startswith('{')]
    emails = []
    for line in lines:
        try:
            email = json.loads(line)
            subject = email.get("subject", "")
            from_field = email.get("from", {})
            sender = from_field.get("addr", "").lower()
            
            if any(x in sender for x in ["noreply", "no-reply", "newsletter", "skool.com", "substack.com"]):
                continue
            
            urgency = 0
            if any(x in subject.lower() for x in ["urgent", "asap", "today", "deadline", "important", "response needed"]):
                urgency = 3
            elif any(x in subject.lower() for x in ["please", "help", "question", "feedback"]):
                urgency = 1
            
            if urgency > 0:
                emails.append({
                    "from": from_field.get("name", sender),
                    "subject": subject,
                    "date": email.get("date", "")[:10],
                    "urgency": urgency
                })
        except:
            pass
    
    emails.sort(key=lambda x: (-x["urgency"], x["date"]))
    return emails[:limit]

def get_job_pipeline():
    """Get current job pipeline status"""
    conn = sqlite3.connect(DB_PATH)
    status_counts = conn.execute("SELECT status, COUNT(*) FROM job_pipeline GROUP BY status").fetchall()
    recent = conn.execute("SELECT company, role, status, applied_date FROM job_pipeline ORDER BY applied_date DESC LIMIT 5").fetchall()
    conn.close()
    return {
        "counts": {s[0]: s[1] for s in status_counts},
        "recent": [{"company": r[0], "role": r[1], "status": r[2], "applied": r[3]} for r in recent]
    }

def get_pending_followups():
    """Get pending follow-ups"""
    conn = sqlite3.connect(DB_PATH)
    pending = conn.execute("""
        SELECT f.action, f.due_date, f.priority, c.name, j.company
        FROM follow_ups f
        LEFT JOIN contacts c ON f.contact_id = c.id
        LEFT JOIN job_pipeline j ON f.job_id = j.id
        WHERE f.status = 'pending'
        ORDER BY f.due_date ASC LIMIT 10
    """).fetchall()
    conn.close()
    return [{"action": p[0], "due": p[1], "priority": p[2], "contact": p[3], "job": p[4]} for p in pending]

def get_stale_relationships(limit=10):
    """Get relationships that need attention"""
    conn = sqlite3.connect(DB_PATH)
    stale = conn.execute("""
        SELECT c.name, c.company, c.role, MAX(i.date) as last_contact
        FROM contacts c
        LEFT JOIN interactions i ON c.id = i.contact_id
        WHERE c.is_noisy = 0 AND c.email NOT LIKE '%mailer-daemon%' AND c.email NOT LIKE '%noreply%'
        GROUP BY c.id
        HAVING last_contact < date('now', '-60 days') OR last_contact IS NULL
        ORDER BY last_contact ASC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [{"name": s[0], "company": s[1], "role": s[2], "last": s[3]} for s in stale]

def generate_briefing_text():
    """Generate the full daily briefing as text"""
    
    date_str = datetime.now().strftime("%A, %B %d, %Y")
    
    text = f"📅 *DAILY BRIEFING — {date_str}*\n"
    text += "=" * 40 + "\n\n"
    
    # Calendar
    text += "📆 *TODAY'S MEETINGS*\n"
    meetings = get_meetings()
    if meetings.get("status") == "no_auth":
        text += f"⚠️ {meetings['message']}\n"
        text += f"💡 Run: `{meetings['action']}`\n"
    else:
        text += "No meetings scheduled\n"
    
    # Urgent Emails
    text += "\n📧 *URGENT EMAILS*\n"
    emails = get_urgent_emails()
    if emails:
        for e in emails[:3]:
            emoji = "🔴" if e["urgency"] >= 3 else "🟡"
            text += f"{emoji} *{e['from']}*\n"
            text += f"   {e['subject'][:45]}...\n"
    else:
        text += "✅ No urgent emails detected\n"
    
    # Job Pipeline
    text += "\n💼 *JOB PIPELINE*\n"
    pipeline = get_job_pipeline()
    total = sum(pipeline["counts"].values())
    text += f"Total: {total} applications\n"
    status_emoji = {"discovered": "🔍", "applied": "📤", "screening": "📋", 
                    "interview": "🎤", "offer": "🎉", "rejected": "❌", "withdrawn": "↩️"}
    for status, count in pipeline["counts"].items():
        emoji = status_emoji.get(status, "•")
        text += f"{emoji} {status.capitalize()}: {count}\n"
    
    if pipeline["recent"]:
        text += "\nRecent:\n"
        for r in pipeline["recent"][:3]:
            text += f"• {r['company']} — {r['role']} ({r['status']})\n"
    
    # Follow-ups
    text += "\n📋 *PENDING FOLLOW-UPS*\n"
    followups = get_pending_followups()
    if followups:
        for f in followups[:3]:
            priority_emoji = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
            emoji = priority_emoji.get(f["priority"], "•")
            text += f"{emoji} {f['action']}\n"
    else:
        text += "✅ No pending follow-ups\n"
    
    # Stale Relationships
    text += "\n🤝 *STALE RELATIONSHIPS*\n"
    stale = get_stale_relationships()
    if stale:
        text += "Consider re-engaging:\n"
        for s in stale[:5]:
            last = s["last"][:10] if s["last"] else "never"
            text += f"• {s['name'] or s.get('email', 'Unknown')} — {s['company'] or ''} (last: {last})\n"
    else:
        text += "✅ All relationships active\n"
    
    # Summary
    text += "\n" + "=" * 40 + "\n"
    text += "*SUMMARY*\n"
    text += f"Meetings: {'?' if meetings.get('status') == 'no_auth' else '0'}\n"
    text += f"Urgent mail: {len(emails)}\n"
    text += f"Job apps: {total}\n"
    text += f"Follow-ups: {len(followups)}\n"
    text += f"Stale leads: {len(stale)}\n"
    text += f"\n🤖 OpenClaw — {datetime.now().strftime('%H:%M')}\n"
    
    return text

def print_briefing():
    """Print briefing to console"""
    print(generate_briefing_text())

def send_to_telegram():
    """Send briefing to Telegram"""
    text = generate_briefing_text()
    
    result = subprocess.run(
        ["openclaw", "message", "send", "--target", TELEGRAM_CHAT, "--message", text],
        capture_output=True, text=True, timeout=30
    )
    
    if result.returncode == 0:
        print("✅ Sent to Telegram")
        return True
    else:
        print(f"❌ Telegram error: {result.stderr}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--telegram":
        send_to_telegram()
    else:
        print_briefing()
