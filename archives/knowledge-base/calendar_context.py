#!/usr/bin/env python3
"""
Calendar Integration — Get today's events with CRM context
"""

import subprocess, sqlite3
from datetime import datetime, timedelta

DB_PATH = "/root/.openclaw/workspace/knowledge-base/kb.db"

def get_todays_events():
    """Get today's calendar events using gog"""
    result = subprocess.run(
        ["gog", "calendar", "events", "--output", "json"],
        capture_output=True, text=True, timeout=30
    )
    
    if result.returncode != 0:
        return {
            "status": "no_auth",
            "message": "Calendar not connected",
            "action": "Run: gog auth to connect Google Calendar"
        }
    
    try:
        import json
        events = json.loads(result.stdout)
        return {"status": "success", "events": events}
    except:
        return {"status": "error", "message": "Failed to parse events"}

def get_contact_context(email):
    """Get CRM context for a contact"""
    conn = sqlite3.connect(DB_PATH)
    
    contact = conn.execute("""
        SELECT name, company, role, last_contact_date, 
               (SELECT COUNT(*) FROM interactions WHERE contact_id = contacts.id) as interactions
        FROM contacts
        WHERE email LIKE ? OR name LIKE ?
        LIMIT 1
    """, (f"%{email}%", f"%{email}%")).fetchone()
    
    conn.close()
    
    if contact:
        return {
            "name": contact[0],
            "company": contact[1],
            "role": contact[2],
            "last_contact": contact[3],
            "interactions": contact[4]
        }
    return None

def enrich_events_with_context(events):
    """Add CRM context to calendar events"""
    enriched = []
    
    for event in events:
        # Try to find attendee emails
        attendees = event.get("attendees", [])
        context = None
        
        for attendee in attendees[:3]:  # Check first 3 attendees
            email = attendee.get("email", "")
            if email:
                context = get_contact_context(email)
                if context:
                    break
        
        enriched.append({
            "title": event.get("summary", "No title"),
            "time": event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "All day")),
            "attendees": [a.get("email", "") for a in attendees[:3]],
            "context": context
        })
    
    return enriched

def get_meeting_context():
    """Get today's meetings with CRM context"""
    result = get_todays_events()
    
    if result["status"] != "success":
        return result
    
    events = result.get("events", [])
    enriched = enrich_events_with_context(events)
    
    return {
        "status": "success",
        "events": enriched,
        "count": len(enriched)
    }

def print_meeting_context():
    """Print meeting context for today"""
    print("\n📅 TODAY'S MEETINGS")
    print("=" * 50)
    
    result = get_meeting_context()
    
    if result["status"] == "no_auth":
        print(f"⚠️  {result['message']}")
        print(f"   💡 {result['action']}")
        return
    
    if result["status"] == "error":
        print(f"❌ Error: {result.get('message')}")
        return
    
    events = result.get("events", [])
    
    if not events:
        print("   ✅ No meetings scheduled")
        return
    
    for i, event in enumerate(events, 1):
        print(f"\n{i}. {event['title']}")
        time_str = event['time'][:16] if len(event['time']) > 16 else event['time']
        print(f"   🕐 {time_str}")
        
        if event['context']:
            ctx = event['context']
            print(f"   👤 {ctx['name']} | {ctx['company']} | {ctx['role']}")
            print(f"   📧 Last contact: {ctx['last_contact'] or 'never'} | {ctx['interactions']} interactions")
        else:
            print(f"   👥 Attendees: {', '.join([a for a in event['attendees'] if a][:2])}")

if __name__ == "__main__":
    print_meeting_context()
