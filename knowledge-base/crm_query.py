#!/usr/bin/env python3
"""
CRM Query Interface — Natural Language + Health Scores
Usage:
  python3 crm_query.py "who do I know at Huxley"
  python3 crm_query.py "who haven't I talked to in a while"
  python3 crm_query.py "show recruiters"
  python3 crm_query.py "stale relationships"
  python3 crm_query.py "summary"
"""

import sqlite3, sys, re
from datetime import datetime, timezone

DB_PATH = "/root/.openclaw/workspace/knowledge-base/kb.db"

def health_score(last_contact_str, interaction_count):
    """0-100 relationship health score"""
    if not last_contact_str:
        return 0
    try:
        # Strip timezone for parsing
        ds = re.sub(r'[+-]\d{2}:\d{2}$', '', str(last_contact_str)).strip()
        last = datetime.fromisoformat(ds)
        days = (datetime.now() - last).days
    except:
        return 0

    if days <= 7:    recency = 100
    elif days <= 30: recency = 80
    elif days <= 90: recency = 55
    elif days <= 180: recency = 30
    elif days <= 365: recency = 15
    else:            recency = 5

    freq = min(interaction_count * 8, 30)
    return min(recency + freq, 100)

def health_emoji(score):
    if score >= 75: return "🟢"
    if score >= 45: return "🟡"
    if score >= 20: return "🟠"
    return "🔴"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def cmd_summary():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM contacts WHERE is_noisy=0").fetchone()[0]
    recruiters = conn.execute("SELECT COUNT(*) FROM contacts WHERE role='recruiter' AND is_noisy=0").fetchone()[0]
    interactions = conn.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]
    pending_fu = conn.execute("SELECT COUNT(*) FROM follow_ups WHERE status='pending'").fetchone()[0]
    jobs = conn.execute("SELECT COUNT(*) FROM job_pipeline").fetchone()[0]

    rows = conn.execute("""
        SELECT c.name, c.email, c.company, c.role,
               COUNT(i.id) as cnt, MAX(i.date) as last
        FROM contacts c
        LEFT JOIN interactions i ON c.id=i.contact_id
        WHERE c.is_noisy=0
          AND c.email NOT LIKE '%mailer-daemon%'
          AND c.email NOT LIKE '%bounce%'
        GROUP BY c.id
        ORDER BY cnt DESC, last DESC
        LIMIT 10
    """).fetchall()

    print(f"\n📊 CRM Summary")
    print(f"{'─'*50}")
    print(f"  Total contacts:    {total}")
    print(f"  Recruiters:        {recruiters}")
    print(f"  Total interactions:{interactions}")
    print(f"  Pending follow-ups:{pending_fu}")
    print(f"  Job pipeline:      {jobs}")
    print(f"\n🔝 Top Contacts")
    print(f"{'─'*50}")
    for r in rows:
        score = health_score(r['last'], r['cnt'])
        print(f"  {health_emoji(score)} {str(r['name'] or ''):<26} {str(r['company'] or ''):<20} {r['cnt']} emails")
    conn.close()

def cmd_search(query):
    """Natural language search"""
    conn = get_conn()
    q = query.lower()

    # Detect intent
    if any(w in q for w in ["stale", "haven't", "not talked", "inactive", "silent", "long time"]):
        rows = conn.execute("""
            SELECT c.name, c.email, c.company, c.role,
                   COUNT(i.id) as cnt, MAX(i.date) as last
            FROM contacts c
            LEFT JOIN interactions i ON c.id=i.contact_id
            WHERE c.is_noisy=0
            GROUP BY c.id
            HAVING last < date('now','-90 days') OR last IS NULL
            ORDER BY last ASC
            LIMIT 15
        """).fetchall()
        print(f"\n🔴 Stale Relationships (no contact > 90 days)\n{'─'*55}")
        for r in rows:
            score = health_score(r['last'], r['cnt'])
            age = r['last'][:10] if r['last'] else "never"
            print(f"  {health_emoji(score)} {str(r['name'] or ''):<28} {str(r['company'] or ''):<20} last: {age}")

    elif any(w in q for w in ["recruiter", "recruiting", "headhunter", "talent"]):
        rows = conn.execute("""
            SELECT c.name, c.email, c.company,
                   COUNT(i.id) as cnt, MAX(i.date) as last
            FROM contacts c
            LEFT JOIN interactions i ON c.id=i.contact_id
            WHERE c.role='recruiter' AND c.is_noisy=0
            GROUP BY c.id ORDER BY last DESC
        """).fetchall()
        print(f"\n🎯 Recruiters ({len(rows)})\n{'─'*55}")
        for r in rows:
            score = health_score(r['last'], r['cnt'])
            print(f"  {health_emoji(score)} {str(r['name'] or ''):<28} {str(r['company'] or ''):<20} {r['cnt']} emails")

    elif any(w in q for w in ["health", "score", "top", "best", "active"]):
        rows = conn.execute("""
            SELECT c.name, c.email, c.company, c.role,
                   COUNT(i.id) as cnt, MAX(i.date) as last
            FROM contacts c
            LEFT JOIN interactions i ON c.id=i.contact_id
            WHERE c.is_noisy=0
              AND c.email NOT LIKE '%mailer-daemon%'
            GROUP BY c.id
            ORDER BY cnt DESC, last DESC
            LIMIT 20
        """).fetchall()
        print(f"\n💪 Active Relationships\n{'─'*55}")
        for r in rows:
            score = health_score(r['last'], r['cnt'])
            print(f"  {health_emoji(score)} {score:>3}  {str(r['name'] or ''):<26} {str(r['company'] or ''):<20} {r['cnt']} emails")

    else:
        # Generic company/name search
        kw = f"%{query}%"
        rows = conn.execute("""
            SELECT c.name, c.email, c.company, c.role,
                   COUNT(i.id) as cnt, MAX(i.date) as last
            FROM contacts c
            LEFT JOIN interactions i ON c.id=i.contact_id
            WHERE c.is_noisy=0
              AND (c.name LIKE ? OR c.company LIKE ? OR c.email LIKE ?)
            GROUP BY c.id ORDER BY cnt DESC
        """, (kw, kw, kw)).fetchall()
        print(f"\n🔍 '{query}' — {len(rows)} results\n{'─'*55}")
        for r in rows:
            score = health_score(r['last'], r['cnt'])
            last = r['last'][:10] if r['last'] else "—"
            print(f"  {health_emoji(score)} {str(r['name'] or ''):<28} {str(r['email'] or ''):<36} {str(r['company'] or ''):<18} {r['cnt']} emails  last:{last}")

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "summary":
        cmd_summary()
    else:
        cmd_search(" ".join(sys.argv[1:]))
