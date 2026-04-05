#!/usr/bin/env python3
"""
Knowledge Brain — Daily Briefing Generator.

Compiles a daily briefing from the knowledge brain state.
Used by: morning briefing pipeline + CTO agent cron

Usage:
  python3 scripts/knowledge-brain-briefing.py              # today's briefing
  python3 scripts/knowledge-brain-briefing.py --output file.md  # write to file
  python3 scripts/knowledge-brain-briefing.py --json       # JSON output
"""
import os
import sys
import json
import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
sys.path.insert(0, str(WORKSPACE / "scripts"))
import sqlite3

BRAIN_DB = os.environ.get("KNOWLEDGE_DB", str(WORKSPACE / "knowledge.db"))


def get_db():
    conn = sqlite3.connect(BRAIN_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def fm_status(frontmatter_json):
    """Safely extract status from frontmatter JSON."""
    try:
        return json.loads(frontmatter_json or "{}").get("status", "unknown")
    except Exception:
        return "unknown"


def get_hot_today(cursor):
    """Items needing attention today (interviews, urgent threads)."""
    items = []
    cursor.execute("SELECT title, slug, frontmatter FROM pages WHERE type = 'role'")
    for row in cursor.fetchall():
        status = fm_status(row["frontmatter"])
        if "interview" in status or "screen" in status:
            cursor.execute("""
                SELECT summary FROM timeline_entries
                WHERE page_id = (SELECT id FROM pages WHERE slug = ?)
                ORDER BY date DESC LIMIT 1
            """, (row["slug"],))
            last = cursor.fetchone()
            items.append({
                "type": "interview",
                "title": row["title"],
                "context": last["summary"][:120] if last else status,
                "priority": "high"
            })
    return items


def get_people_in_play(cursor):
    """Active contacts with recent activity."""
    cursor.execute("""
        SELECT p.title, p.slug, p.frontmatter, MAX(t.date) as last_contact, COUNT(t.id) as interactions
        FROM pages p
        JOIN timeline_entries t ON t.page_id = p.id
        WHERE p.type = 'person'
        GROUP BY p.id
        ORDER BY MAX(t.date) DESC
    """)
    return [{
        "name": r["title"],
        "slug": r["slug"],
        "last_contact": r["last_contact"],
        "interactions": r["interactions"],
        "priority": fm_status(r["frontmatter"]),
        "status": fm_status(r["frontmatter"])
    } for r in cursor.fetchall()]


def get_active_applications(cursor):
    """Active job applications sorted by status."""
    cursor.execute("""
        SELECT title, slug, frontmatter, updated_at
        FROM pages
        WHERE type = 'role'
        ORDER BY updated_at DESC
    """)
    apps = []
    for row in cursor.fetchall():
        fm = {}
        try:
            fm = json.loads(row["frontmatter"]) if row["frontmatter"] else {}
        except Exception:
            pass
        apps.append({
            "title": row["title"],
            "slug": row["slug"],
            "status": fm.get("status", "unknown"),
            "date_applied": fm.get("date_applied", "unknown"),
            "notes": fm.get("notes", ""),
            "updated": row["updated_at"][:10]
        })
    # Sort: interview > applied > researching > other
    priority = {"interview": 1, "applied": 2, "researching": 3}
    apps.sort(key=lambda a: (priority.get(a["status"], 9), a["updated"]))
    return apps


def get_open_threads(cursor):
    """All open threads from entity frontmatter."""
    cursor.execute("SELECT slug, type, title, frontmatter FROM pages")
    threads = []
    for row in cursor.fetchall():
        try:
            fm = json.loads(row["frontmatter"]) if row["frontmatter"] else {}
        except Exception:
            fm = {}
        open_t = fm.get("open_threads", [])
        if open_t:
            threads.append({
                "entity": row["title"],
                "slug": row["slug"],
                "type": row["type"],
                "threads": open_t
            })
    return threads


def generate_briefing():
    conn = get_db()
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    briefing = {
        "date": now,
        "hot": get_hot_today(cursor),
        "people": get_people_in_play(cursor),
        "applications": get_active_applications(cursor),
        "threads": get_open_threads(cursor),
    }
    conn.close()
    return briefing


def format_text(briefing):
    d = datetime.datetime.now().strftime("%Y-%m-%d")
    lines = [f"🧠 DAILY BRIEFING — {d}\n"]

    if briefing["hot"]:
        lines.append("🔥 HOT (needs attention today)")
        for h in briefing["hot"]:
            lines.append(f"- {h['title']}: {h['context']}")
        lines.append("")

    if briefing["people"]:
        lines.append("👥 PEOPLE IN PLAY")
        for p in briefing["people"]:
            lines.append(f"- {p['name']} | {p['status']} | last: {p['last_contact']} | {p['interactions']} contacts")
        lines.append("")

    if briefing["applications"]:
        lines.append("💼 ACTIVE APPLICATIONS")
        for a in briefing["applications"]:
            lines.append(f"- {a['title']} | {a['status']} | applied: {a['date_applied']} | updated: {a['updated']}")
        lines.append("")

    if briefing["threads"]:
        lines.append("📋 OPEN THREADS")
        for t in briefing["threads"]:
            for thread in t["threads"]:
                lines.append(f"- [{t['type']}: {t['entity']}] {thread}")

    return "\n".join(lines)


def main():
    briefing = generate_briefing()

    if "--json" in sys.argv:
        print(json.dumps(briefing, indent=2, default=str))
    elif "--output" in sys.argv:
        idx = sys.argv.index("--output")
        outfile = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else f"briefing-{datetime.date.today()}.md"
        Path(outfile).write_text(format_text(briefing))
        print(f"  ✅ Briefing written to {outfile}")
    else:
        print(format_text(briefing))


if __name__ == "__main__":
    main()
