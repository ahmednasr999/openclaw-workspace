#!/usr/bin/env python3
"""
Knowledge Brain — Ingestion Pipeline.

Auto-ingests from daily sources into the knowledge brain:
- Emails → timeline entries for people/companies
- New job applications → role entities
- Outreach interactions → person timeline

Usage:
  python3 scripts/knowledge-brain-ingest.py run        # run full pipeline
  python3 scripts/knowledge-brain-ingest.py email      # ingest recent emails
  python3 scripts/knowledge-brain-ingest.py jobs       # ingest active job apps
  python3 scripts/knowledge-brain-ingest.py status     # show ingest log
"""
import os
import sys
import json
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
BRAIN_DB = os.environ.get("KNOWLEDGE_DB", str(WORKSPACE / "knowledge.db"))
MEMORY_DIR = WORKSPACE / "memory"
ENTITY_DIR = WORKSPACE / "memory/entities"

sys.path.insert(0, str(WORKSPACE / "scripts"))
import sqlite3


def get_db():
    conn = sqlite3.connect(BRAIN_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def find_or_create_page(cursor, title, entity_type, slug_suggestion="", frontmatter=None):
    """Find existing page by slug or title, or create one."""
    slug = slug_suggestion or f"{entity_type}/" + title.lower().replace(" ", "-").replace(",", "").replace("/", "-")

    # Try exact slug
    cursor.execute("SELECT id, slug FROM pages WHERE slug = ?", (slug,))
    existing = cursor.fetchone()
    if existing:
        return dict(existing)["id"]

    # Search by title
    cursor.execute("SELECT id FROM pages WHERE title LIKE ?", (title,))
    existing = cursor.fetchone()
    if existing:
        return dict(existing)["id"]

    # Search by type + title prefix
    cursor.execute("SELECT id FROM pages WHERE type = ? AND title LIKE ?", (entity_type, f"%{title[:20]}%"))
    existing = cursor.fetchone()
    if existing:
        return dict(existing)["id"]

    # Create new
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fm = json.dumps(frontmatter or {})
    compiled = f"# {title}\n\n> [Auto-created by ingest]\n\n## State\n**Last Updated:** {now}\n**Status:** active\n\n---\n"
    cursor.execute(
        "INSERT INTO pages (slug, type, title, compiled_truth, timeline, frontmatter) VALUES (?, ?, ?, ?, ?, ?)",
        (slug, entity_type, title, compiled, "", fm)
    )
    print(f"    + Created entity: {slug}")
    return cursor.lastrowid


def add_timeline_entry(cursor, page_id, date, source, summary, detail=""):
    """Add timeline entry if not duplicate."""
    cursor.execute(
        "SELECT 1 FROM timeline_entries WHERE page_id=? AND date=? AND source=? AND summary=?",
        (page_id, date, source, summary)
    )
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO timeline_entries (page_id, date, source, summary, detail) VALUES (?, ?, ?, ?, ?)",
            (page_id, date, source, summary, detail)
        )
        return True
    return False


def ingest_emails(conn, max_emails=50):
    """Ingest recent flagged/important emails into knowledge brain."""
    cursor = conn.cursor()

    # Check HIMAYALA email cache
    cache_file = MEMORY_DIR / "email-cache.json"
    if not cache_file.exists():
        return 0

    import json
    try:
        emails = json.loads(cache_file.read_text())
    except:
        return 0

    count = 0
    for email in emails[:max_emails]:
        subject = email.get("Subject", email.get("subject", ""))
        sender_name = email.get("FromName", email.get("from_name", ""))
        sender_email = email.get("From", email.get("from", ""))
        date_str = email.get("date", email.get("Date", ""))[:10]
        snippet = email.get("Snippet", email.get("snippet", ""))
        flagged = email.get("Flagged", False)

        if not date_str or not subject:
            continue

        # Only ingest flagged/important emails
        if not flagged:
            continue

        # Extract date
        if len(date_str) > 10:
            date_clean = date_str[:10]
        else:
            date_clean = date_str

        # Create/update person entity for sender
        if sender_name and len(sender_name) > 5:
            slug_s = f"people/{sender_name.lower().replace(' ', '-').replace('.', '')}"
            person_id = find_or_create_page(cursor, sender_name, "person", slug_s)

            summary = f"Email: {subject[:80]}"
            detail = f"From: {sender_email}\nSnippet: {snippet[:200]}" if snippet else f"From: {sender_email}"

            added = add_timeline_entry(cursor, person_id, date_clean, f"email: {date_clean}", summary, detail)
            if added:
                count += 1

                # Update frontmatter status
                cursor.execute("SELECT frontmatter FROM pages WHERE id = ?", (person_id,))
                row = cursor.fetchone()
                if row:
                    try:
                        fm = json.loads(row["frontmatter"])
                        fm["last_updated"] = date_clean
                        fm["last_email_date"] = date_clean
                        cursor.execute("UPDATE pages SET frontmatter=?, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now') WHERE id = ?",
                                      (json.dumps(fm), person_id))
                    except:
                        pass

    return count


def ingest_job_applications(conn):
    """Ingest active job applications from coordination pipeline."""
    cursor = conn.cursor()
    pipeline_file = WORKSPACE / "coordination/pipeline.json"

    if not pipeline_file.exists():
        return 0

    import json
    pipeline = json.loads(pipeline_file.read_text())
    applications = pipeline.get("applications", {}).get("active", [])

    count = 0
    for app in applications:
        company = app.get("company", "")
        title = app.get("title", "")
        status = app.get("status", "unknown")
        date_applied = app.get("date_applied", "")
        notes = app.get("notes", "")
        app_id = app.get("id", "")

        if not company or not title:
            continue

        # Create company entity
        slug_c = f"companies/{company.lower().replace(' ', '-').replace('—', '-').replace('/', '-')}"
        company_id = find_or_create_page(cursor, company, "company", slug_c)

        # Create role entity
        slug_r = f"roles/{title.lower().replace(' ', '-')}—{company.lower().replace(' ', '-').replace('—', '-').replace('/', '-')}"[:120]
        role_id = find_or_create_page(cursor, f"{title} — {company}", "role", slug_r,
                                     frontmatter={
                                         "date_applied": date_applied,
                                         "status": status,
                                         "notes": notes
                                     })

        # Timeline entry for role
        if date_applied:
            summary = f"Applied: {title} at {company}"
            added = add_timeline_entry(cursor, role_id, date_applied[:10], "pipeline", summary,
                                      f"ID: {app_id}\nStatus: {status}\nNotes: {notes}")
            if added:
                count += 1

        # Link company → role
        if company_id and role_id:
            cursor.execute(
                "INSERT OR IGNORE INTO links (from_page_id, to_page_id, context) VALUES (?, ?, ?)",
                (company_id, role_id, f"Company has opening: {title}")
            )
            cursor.execute(
                "INSERT OR IGNORE INTO links (from_page_id, to_page_id, context) VALUES (?, ?, ?)",
                (role_id, company_id, f"Role at: {company}")
            )

    return count


def ingest_daily_notes(conn):
    """Ingest today's daily note into the brain as source material."""
    cursor = conn.cursor()
    import datetime
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    daily_file = MEMORY_DIR / f"agents/daily-{today}.md"

    if not daily_file.exists():
        # Try YYYY-MM-DD format
        daily_file = MEMORY_DIR / f"daily-{today}.md"

    if not daily_file.exists():
        return 0

    content = daily_file.read_text()

    # Each significant entry becomes a timeline event
    lines = content.split("\n")
    count = 0
    for line in lines:
        if line.startswith("-") or line.startswith("*") or "✅ " in content:
            if len(line) > 20:
                # This is a simple heuristic — real pipeline should be smarter
                pass

    return count


def show_status(conn):
    """Show ingest log."""
    cursor = conn.cursor()
    cursor.execute("SELECT source_type, source_ref, timestamp, summary, pages_updated FROM ingest_log ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()

    if not rows:
        print("No ingest history.")
        return

    print(f"\n📋 Ingest History\n{'='*50}")
    for r in rows:
        try:
            pages = json.loads(r["pages_updated"]) if r["pages_updated"] else []
        except:
            pages = []
        print(f"  [{r['timestamp'][:16]}] {r['source_type']}: {r['summary']}")
        if pages:
            print(f"    Pages: {', '.join(pages)})")


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    conn = get_db()

    if action == "status":
        show_status(conn)
    elif action == "run":
        import datetime
        print(f"\n🔄 Running ingestion pipeline at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

        email_count = ingest_emails(conn)
        print(f"  📧 Emails ingested: {email_count}")

        job_count = ingest_job_applications(conn)
        print(f"  💼 Job applications ingested: {job_count}")

        conn.commit()

        # Log the ingest
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ingest_log (source_type, source_ref, pages_updated, summary) VALUES (?, ?, ?, ?)",
            ("pipeline", "automated", json.dumps([]), f"Emails: {email_count}, Jobs: {job_count}")
        )
        conn.commit()
        print(f"\n✅ Pipeline complete")

    elif action == "email":
        count = ingest_emails(conn)
        conn.commit()
        print(f"  📧 Emails ingested: {count}")
    elif action == "jobs":
        count = ingest_job_applications(conn)
        conn.commit()
        print(f"  💼 Jobs ingested: {count}")
    elif action == "status":
        show_status(conn)
    else:
        print(__doc__)

    conn.close()


if __name__ == "__main__":
    main()
