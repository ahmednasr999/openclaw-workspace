#!/usr/bin/env python3
"""
Link two entity pages together.

Usage:
  python3 scripts/knowledge-brain-link.py link people/lee-abrahams companies/proximie "Recruiter for Proximie Transformation Lead UAE role"
  python3 scripts/knowledge-brain-link.py link companies/proximie roles/proximie-transformation-lead-uae "Proximie is hiring for this role"
  python3 scripts/knowledge-brain-link.py link people/lee-abrahams roles/proximie-transformation-lead-uae "Lee is handling this recruitment"
  python3 scripts/knowledge-brain-link.py link companies/proximie companies/network-international "Same sector: GCC FinTech/HealthTech"
"""
import sqlite3
import sys
import os

WORKSPACE = "/root/.openclaw/workspace"
BRAIN_DB = os.environ.get("KNOWLEDGE_DB", f"{WORKSPACE}/knowledge.db")


def get_db():
    conn = sqlite3.connect(BRAIN_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def link_entities(from_slug, to_slug, context, bidirectional=True):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM pages WHERE slug = ?", (from_slug,))
    from_page = cursor.fetchone()
    cursor.execute("SELECT id FROM pages WHERE slug = ?", (to_slug,))
    to_page = cursor.fetchone()

    if not from_page:
        print(f"ERROR: Entity not found: {from_slug}")
        return
    if not to_page:
        print(f"ERROR: Entity not found: {to_slug}")
        return

    from_id = from_page["id"]
    to_id = to_page["id"]

    # Insert forward link
    cursor.execute("""
        INSERT OR IGNORE INTO links (from_page_id, to_page_id, context)
        VALUES (?, ?, ?)
    """, (from_id, to_id, context))
    forward = cursor.rowcount > 0

    # Insert reverse link if bidirectional
    if bidirectional:
        cursor.execute("""
            INSERT OR IGNORE INTO links (from_page_id, to_page_id, context)
            VALUES (?, ?, ?)
        """, (to_id, from_id, context))
        reverse = cursor.rowcount > 0
    else:
        reverse = False

    conn.commit()
    conn.close()

    if forward:
        print(f"  + Linked: {from_slug} → {to_slug}")
    else:
        print(f"  ↺ Already linked: {from_slug} → {to_slug}")
    if reverse:
        print(f"  + Linked: {to_slug} → {from_slug}")


def main():
    if len(sys.argv) < 4 or sys.argv[1] != "link":
        print(__doc__)
        sys.exit(1)

    _, _, from_slug, to_slug, *rest = sys.argv
    context = rest[0] if rest else ""
    link_entities(from_slug, to_slug, context)


if __name__ == "__main__":
    main()
