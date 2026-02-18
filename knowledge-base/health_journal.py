#!/usr/bin/env python3
"""
Health Journal
Track meals, symptoms, and health metrics
"""

import sqlite3, subprocess
from datetime import datetime

DB_PATH = "/root/.openclaw/workspace/knowledge-base/kb.db"

def init_db():
    """Initialize health journal tables"""
    conn = sqlite3.connect(DB_PATH)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS health_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_type TEXT,  -- food, drink, symptom, note
            description TEXT,
            severity INTEGER,  -- 1-5 for symptoms
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            date DATE DEFAULT CURRENT_DATE
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS health_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,  -- 08:00, 13:00, 19:00
            enabled INTEGER DEFAULT 1,
            message TEXT
        )
    """)
    
    # Default reminders
    conn.execute("""
        INSERT OR IGNORE INTO health_reminders (id, time, message) VALUES
        (1, '08:00', '☀️ Good morning! Log your breakfast and how you\'re feeling.'),
        (2, '13:00', '🌤️ Lunch time! What did you have? Any symptoms?'),
        (3, '19:00', '🌙 Evening check-in: Dinner and how\'s your energy?')
    """)
    
    conn.commit()
    conn.close()

def log_entry(entry_type, description, severity=None, notes=None):
    """Log a health entry"""
    conn = sqlite3.connect(DB_PATH)
    
    conn.execute("""
        INSERT INTO health_entries (entry_type, description, severity, notes)
        VALUES (?, ?, ?, ?)
    """, (entry_type, description, severity, notes))
    
    conn.commit()
    conn.close()
    return True

def get_today_entries():
    """Get today's entries"""
    conn = sqlite3.connect(DB_PATH)
    
    entries = conn.execute("""
        SELECT entry_type, description, severity, created_at
        FROM health_entries
        WHERE date = date('now')
        ORDER BY created_at DESC
    """).fetchall()
    
    conn.close()
    return entries

def weekly_summary():
    """Generate weekly health summary"""
    conn = sqlite3.connect(DB_PATH)
    
    # Food count
    food = conn.execute("""
        SELECT COUNT(*) FROM health_entries 
        WHERE entry_type = 'food' AND date >= date('now', '-7 days')
    """).fetchone()[0]
    
    # Symptom count
    symptoms = conn.execute("""
        SELECT COUNT(*) FROM health_entries 
        WHERE entry_type = 'symptom' AND date >= date('now', '-7 days')
    """).fetchone()[0]
    
    # Avg severity
    avg_severity = conn.execute("""
        SELECT AVG(severity) FROM health_entries 
        WHERE entry_type = 'symptom' AND date >= date('now', '-7 days')
    """).fetchone()[0] or 0
    
    conn.close()
    
    return {
        "meals_logged": food,
        "symptoms_reported": symptoms,
        "avg_symptom_severity": round(avg_severity, 1),
        "days_logged": 7
    }

def print_today():
    """Print today's health journal"""
    print("\n📓 TODAY'S HEALTH JOURNAL")
    print("=" * 40)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    entries = get_today_entries()
    
    if not entries:
        print("   No entries yet today.")
        print("   💡 Log with: /health log <type> <description>")
        return
    
    for entry in entries:
        emoji = {"food": "🍽️", "drink": "💧", "symptom": "🤒", "note": "📝"}.get(entry[0], "•")
        severity = f" (severity: {entry[2]})" if entry[2] else ""
        print(f"   {emoji} {entry[1]}{severity}")
    
    # Weekly summary
    print()
    summary = weekly_summary()
    print(f"📊 This Week:")
    print(f"   🍽️  Meals logged: {summary['meals_logged']}")
    print(f"   🤒  Symptoms: {summary['symptoms_reported']} (avg: {summary['avg_symptom_severity']}/5)")

def send_telegram_daily():
    """Send daily health reminder"""
    conn = sqlite3.connect(DB_PATH)
    reminder = conn.execute("SELECT message FROM health_reminders WHERE time = '08:00' AND enabled=1").fetchone()
    conn.close()
    
    if reminder:
        text = f"☀️ *Health Journal*\n\n{reminder[0]}\n\n/meal <description>\n/symptom <description> 1-5"
        subprocess.run(
            ["openclaw", "message", "send", "--target", "telegram:866838380", "--message", text],
            capture_output=True
        )

if __name__ == "__main__":
    init_db()
    
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--today":
            print_today()
        elif cmd == "--week":
            s = weekly_summary()
            print(f"\n📊 Weekly Summary")
            print(f"   Meals: {s['meals_logged']}")
            print(f"   Symptoms: {s['symptoms_reported']} (avg: {s['avg_symptom_severity']}/5)")
        elif cmd == "--log":
            # /health log food "Oatmeal with berries"
            entry_type = sys.argv[2] if len(sys.argv) > 2 else "note"
            description = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
            log_entry(entry_type, description)
            print(f"✅ Logged: {entry_type} - {description}")
        elif cmd == "--remind":
            send_telegram_daily()
        else:
            print("Usage: health.py [--today|--week|--log <type> <desc>|--remind]")
    else:
        print_today()
