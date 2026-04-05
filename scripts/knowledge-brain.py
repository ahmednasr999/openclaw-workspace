#!/usr/bin/env python3
"""
Knowledge Brain — SQLite query layer + entity management.

SQLite + FTS5 knowledge database. Thin Python, fat markdown skills.
Unifies: ontology, memories, daily notes, agent traces.

Usage:
  python3 scripts/knowledge-brain.py init                       # create brain.db
  python3 scripts/knowledge-brain.py get people/lee-abrahams     # read entity
  python3 scripts/knowledge-brain.py search "Proximie"           # FTS5 search
  python3 scripts/knowledge-brain.py query "what's new with Proximie?"  # ranked results
  python3 scripts/knowledge-brain import entities               # import memory/entities/
  python3 scripts/knowledge-brain.py list --type person          # list entities
  python3 scripts/knowledge-brain.py stats                       # brain stats
  python3 scripts/knowledge-brain.py maintain                    # lint + stale alerts
"""
import os
import sys
import json
import re
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone

WORKSPACE = Path("/root/.openclaw/workspace")
BRAIN_DB = os.environ.get("KNOWLEDGE_DB", str(WORKSPACE / "knowledge.db"))
ENTITIES_DIR = WORKSPACE / "memory/entities"

TYPE_MAP = {
    "people": "person",
    "companies": "company",
    "roles": "role",
    "projects": "project",
    "sources": "source",
}
REVERSE_TYPE_MAP = {v: k for k, v in TYPE_MAP.items()}


def get_db(path=BRAIN_DB):
    """Open SQLite DB with WAL mode."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path=BRAIN_DB):
    """Create brain.db with full schema."""
    conn = get_db(path)

    conn.executescript("""
    -- pages: entity pages with compiled_truth + timeline
    CREATE TABLE IF NOT EXISTS pages (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        slug          TEXT    NOT NULL UNIQUE,
        type          TEXT    NOT NULL,
        title         TEXT    NOT NULL,
        compiled_truth TEXT   NOT NULL DEFAULT '',
        timeline      TEXT    NOT NULL DEFAULT '',
        frontmatter   TEXT    NOT NULL DEFAULT '{}',
        created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
        updated_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    );

    CREATE INDEX IF NOT EXISTS idx_pages_type ON pages(type);
    CREATE INDEX IF NOT EXISTS idx_pages_slug ON pages(slug);

    -- FTS5 full-text search
    CREATE VIRTUAL TABLE IF NOT EXISTS page_fts USING fts5(
        title, compiled_truth, timeline,
        content='pages', content_rowid='id',
        tokenize='porter unicode61'
    );

    -- Triggers to keep FTS in sync
    CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN
        INSERT INTO page_fts(rowid, title, compiled_truth, timeline)
        VALUES (new.id, new.title, new.compiled_truth, new.timeline);
    END;
    CREATE TRIGGER IF NOT EXISTS pages_ad AFTER DELETE ON pages BEGIN
        INSERT INTO page_fts(page_fts, rowid, title, compiled_truth, timeline)
        VALUES ('delete', old.id, old.title, old.compiled_truth, old.timeline);
    END;
    CREATE TRIGGER IF NOT EXISTS pages_au AFTER UPDATE ON pages BEGIN
        INSERT INTO page_fts(page_fts, rowid, title, compiled_truth, timeline)
        VALUES ('delete', old.id, old.title, old.compiled_truth, old.timeline);
        INSERT INTO page_fts(rowid, title, compiled_truth, timeline)
        VALUES (new.id, new.title, new.compiled_truth, new.timeline);
    END;

    -- Structured timeline entries
    CREATE TABLE IF NOT EXISTS timeline_entries (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        page_id   INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
        date      TEXT    NOT NULL,
        source    TEXT    NOT NULL DEFAULT '',
        summary   TEXT    NOT NULL,
        detail    TEXT    NOT NULL DEFAULT '',
        created_at TEXT   NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    );
    CREATE INDEX IF NOT EXISTS idx_timeline_page ON timeline_entries(page_id);
    CREATE INDEX IF NOT EXISTS idx_timeline_date ON timeline_entries(date);

    -- Tags
    CREATE TABLE IF NOT EXISTS tags (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
        tag     TEXT    NOT NULL,
        UNIQUE(page_id, tag)
    );
    CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);
    CREATE INDEX IF NOT EXISTS idx_tags_page ON tags(page_id);

    -- Cross-references (links between entities)
    CREATE TABLE IF NOT EXISTS links (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        from_page_id INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
        to_page_id   INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
        context      TEXT    NOT NULL DEFAULT '',
        created_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
        UNIQUE(from_page_id, to_page_id)
    );
    CREATE INDEX IF NOT EXISTS idx_links_from ON links(from_page_id);
    CREATE INDEX IF NOT EXISTS idx_links_to ON links(to_page_id);

    -- Ingest log (what came in, when, from where)
    CREATE TABLE IF NOT EXISTS ingest_log (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        source_type   TEXT    NOT NULL,
        source_ref    TEXT    NOT NULL,
        pages_updated TEXT    NOT NULL DEFAULT '[]',
        summary       TEXT    NOT NULL DEFAULT '',
        timestamp     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    );

    -- Config
    CREATE TABLE IF NOT EXISTS config (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    INSERT OR IGNORE INTO config (key, value) VALUES ('version', '1');
    INSERT OR IGNORE INTO config (key, value) VALUES ('chunk_strategy', 'section');
    INSERT OR IGNORE INTO config (key, value) VALUES ('entities_dir', 'memory/entities');
    """)

    conn.commit()
    conn.close()
    print(f"✅ brain.db initialized at {path}")


def parse_entity_file(content, path=None):
    """Parse a markdown entity file: frontmatter + compiled_truth + timeline."""
    frontmatter = {}
    compiled_truth = ""
    timeline = ""

    # Extract YAML frontmatter
    fm_match = re.match(r'^<!--[\s\S]*?-->\s*\n', content)
    if fm_match:
        comment = fm_match.group(0)
    else:
        comment = ""

    body = content[len(comment):].strip() if comment else content

    # Split on the horizontal rule --- that separates compiled_truth from timeline
    hr_match = re.search(r'\n---\n', body)
    if hr_match:
        compiled_truth = body[:hr_match.start()].strip()
        timeline = body[hr_match.end():].strip()
    else:
        compiled_truth = body.strip()
        timeline = ""

    # Extract title from first # heading
    title_match = re.search(r'^#\s+(.+)$', compiled_truth, re.MULTILINE)
    title = title_match.group(1) if title_match else (path.stem if path else "Unknown")

    # Extract State section for structured fields
    state_match = re.search(r'## State\n([\s\S]*?)(?=###|\n---|\Z)', compiled_truth)
    state_text = state_match.group(1) if state_match else ""

    for key in ['Last Updated', 'Status', 'Relationship', 'Priority', 'Fit Score',
                'Date Applied', 'Applied Via', 'Location', 'Company', 'Industry',
                'Relationship Type']:
        match = re.search(rf'\*\*{key}:\*\*\s*(.+)', state_text)
        if match:
            frontmatter[key.lower().replace(' ', '_')] = match.group(1).strip()

    # Extract open threads for frontmatter
    threads = re.findall(r'- \[ \]\s*(.*)', body)
    if threads:
        frontmatter['open_threads'] = threads

    return {
        "title": title,
        "compiled_truth": compiled_truth,
        "timeline": timeline,
        "frontmatter": frontmatter,
    }


def import_entities(db_path=BRAIN_DB):
    """Import all entity files from memory/entities/."""
    if not ENTITIES_DIR.exists():
        print(f"ERROR: {ENTITIES_DIR} not found. Run 'init' first.")
        return

    conn = get_db(db_path)
    cursor = conn.cursor()

    total = 0
    for type_dir, entity_type in TYPE_MAP.items():
        dir_path = ENTITIES_DIR / type_dir
        if not dir_path.exists():
            continue
        for md_file in sorted(dir_path.glob("*.md")):
            if md_file.name == "TEMPLATE.md":
                continue
            content = md_file.read_text()
            parsed = parse_entity_file(content, md_file)
            slug = f"{type_dir}/{md_file.stem}"

            cursor.execute("SELECT id FROM pages WHERE slug = ?", (slug,))
            existing = cursor.fetchone()

            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            frontmatter_json = json.dumps(parsed["frontmatter"])

            if existing:
                cursor.execute("""
                    UPDATE pages SET title=?, compiled_truth=?, timeline=?,
                           frontmatter=?, updated_at=? WHERE slug=?
                """, (parsed["title"], parsed["compiled_truth"],
                       parsed["timeline"], frontmatter_json, now, slug))
                print(f"  ↻ Updated: {slug}")
            else:
                cursor.execute("""
                    INSERT INTO pages (slug, type, title, compiled_truth, timeline, frontmatter)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (slug, entity_type, parsed["title"],
                       parsed["compiled_truth"], parsed["timeline"], frontmatter_json))
                print(f"  + Created: {slug}")

            total += 1

            # Also parse and insert timeline entries
            if parsed["timeline"]:
                _parse_and_insert_timeline(cursor, conn, slug, parsed["timeline"])

    conn.commit()

    # Log the import
    cursor.execute("""
        INSERT INTO ingest_log (source_type, source_ref, pages_updated, summary)
        VALUES (?, ?, ?, ?)
    """, ("import", str(ENTITIES_DIR), json.dumps([f"{d}/{f.stem}" for d in TYPE_MAP for f in (ENTITIES_DIR / d).glob("*.md") if f.name != "TEMPLATE.md"]),
          f"Imported {total} entities from {ENTITIES_DIR}"))
    conn.commit()
    conn.close()
    print(f"\n✅ Imported {total} entities into brain.db")


def _parse_and_insert_timeline(cursor, conn, slug, timeline_text):
    """Parse timeline markdown entries and insert as structured rows."""
    cursor.execute("SELECT id FROM pages WHERE slug = ?", (slug,))
    page = cursor.fetchone()
    if not page:
        return
    page_id = page["id"]

    # Pattern: - **YYYY-MM-DD** | Source — Summary
    for match in re.finditer(r'-\s+\*\*(\d{4}-\d{2}-\d{2})\*\*\s*\|\s*([^\—]+)\s*[—\-]\s*(.+)', timeline_text):
        date, source, summary = match.group(1), match.group(2).strip(), match.group(3).strip()
        cursor.execute("""
            SELECT id FROM timeline_entries WHERE page_id=? AND date=? AND source=? AND summary=?
        """, (page_id, date, source, summary))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO timeline_entries (page_id, date, source, summary, detail)
                VALUES (?, ?, ?, ?, '')
            """, (page_id, date, source, summary))


def search(query, limit=10, db_path=BRAIN_DB):
    """FTS5 full-text search."""
    conn = get_db(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.slug, p.type, p.title,
               page_fts.rank as score
        FROM page_fts
        JOIN pages p ON p.id = page_fts.rowid
        WHERE page_fts MATCH ?
        ORDER BY page_fts.rank
        LIMIT ?
    """, (query, limit))

    results = cursor.fetchall()
    conn.close()

    if not results:
        print(f"No results for: {query}")
        return []

    print(f"\n🔍 Search: '{query}'\n")
    for r in results:
        print(f"  [{r['type']}] {r['title']}")
        print(f"    → {r['slug']}  (score: {r['score']:.2f})")
    return results


def query_semantic(question, limit=5, db_path=BRAIN_DB):
    """Search + ranked results. For now, FTS5 with question-as-query."""
    conn = get_db(db_path)
    cursor = conn.cursor()

    # Extract key terms from the question for FTS5
    stop_words = {"what", "who", "when", "where", "how", "why", "is", "are", "the", "a", "an",
                  "with", "for", "to", "of", "in", "on", "at", "and", "or", "not", "do", "did",
                  "has", "have", "been", "being", "new", "latest", "about", "know"}
    terms = [w for w in re.findall(r'\b\w{3,}\b', question.lower()) if w not in stop_words]
    if not terms:
        terms = re.findall(r'\b\w+\b', question.lower())

    query_str = " OR ".join(terms[:10])

    cursor.execute("""
        SELECT p.slug, p.type, p.title, p.compiled_truth,
               page_fts.rank as score
        FROM page_fts
        JOIN pages p ON p.id = page_fts.rowid
        WHERE page_fts MATCH ?
        ORDER BY page_fts.rank
        LIMIT ?
    """, (query_str, limit))

    results = cursor.fetchall()
    conn.close()

    if not results:
        print(f"No results for: {question}\nTerms used: {query_str}")
        return []

    print(f"\n❓ Query: '{question}'\n")
    for r in results:
        snippet = r['compiled_truth'][:200].replace('\n', ' ')
        print(f"  [{r['type']}] {r['title']} → {r['slug']}")
        print(f"    {snippet}...\n")
    return results


def get_entity(slug, db_path=BRAIN_DB):
    """Read entity by slug."""
    conn = get_db(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pages WHERE slug = ?", (slug,))
    page = cursor.fetchone()
    if not page:
        print(f"Entity not found: {slug}")
        conn.close()
        return None

    conn.close()
    print(f"\n# {page['title']}\n")
    print(f"**Type:** {page['type']}\n")
    print(page['compiled_truth'])
    if page['timeline']:
        print(f"\n---\n\n{page['timeline']}")
    return dict(page)


def list_entities(entity_type=None, tag=None, limit=50, db_path=BRAIN_DB):
    """List entities with optional filters."""
    conn = get_db(db_path)
    cursor = conn.cursor()

    sql = "SELECT slug, type, title, updated_at FROM pages WHERE 1=1"
    params = []
    if entity_type:
        sql += " AND type = ?"
        params.append(entity_type)
    if tag:
        sql += " AND id IN (SELECT page_id FROM tags WHERE tag = ?)"
        params.append(tag)
    sql += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()

    if not results:
        print("No entities found.")
        return []

    for r in results:
        print(f"  [{r['type']}] {r['title']} → {r['slug']} (updated: {r['updated_at'][:10]})")
    print(f"\n  Total: {len(results)}")
    return results


def stats(db_path=BRAIN_DB):
    """Brain statistics."""
    conn = get_db(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM pages")
    page_count = cursor.fetchone()[0]

    cursor.execute("SELECT type, COUNT(*) FROM pages GROUP BY type ORDER BY COUNT(*) DESC")
    type_counts = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM timeline_entries")
    timeline_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM links")
    link_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tags")
    tag_count = cursor.fetchone()[0]

    # DB file size
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    size_str = f"{db_size / 1024:.0f} KB" if db_size < 1024*1024 else f"{db_size / (1024*1024):.1f} MB"

    # Latest ingest
    cursor.execute("SELECT source_type, source_ref, timestamp, summary FROM ingest_log ORDER BY id DESC LIMIT 1")
    latest_ingest = cursor.fetchone()

    conn.close()

    print(f"\n🧠 Knowledge Brain Stats")
    print(f"{'='*40}")
    print(f"  Pages:           {page_count}")
    for tc in type_counts:
        print(f"    {tc[0]}:        {tc[1]}")
    print(f"  Timeline entries: {timeline_count}")
    print(f"  Links:            {link_count}")
    print(f"  Tags:             {tag_count}")
    print(f"  DB size:          {size_str}")
    if latest_ingest:
        print(f"\n  Latest ingest: {latest_ingest[0]} — {latest_ingest[2][:16]} — {latest_ingest[3][:80]}")


def maintain(db_path=BRAIN_DB):
    """Lint checks: stale alerts, contradictions, timeline gaps, orphans."""
    conn = get_db(db_path)
    cursor = conn.cursor()
    now = datetime.now(timezone.utc)
    alerts = []

    # 1. Stale entities — not updated in 30+ days
    stale_threshold = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    cursor.execute("""
        SELECT slug, type, title, updated_at FROM pages
        WHERE updated_at < ? ORDER BY updated_at ASC
    """, (stale_threshold,))
    stale = cursor.fetchall()
    if stale:
        alerts.append(f"\n⚠️  STALE ENTITIES ({len(stale)}):")
        for s in stale:
            days = (now - datetime.strptime(s["updated_at"][:19], "%Y-%m-%dT%H:%M:%S")).days
            alerts.append(f"  [{s['type']}] {s['title']} — stale {days}d ({s['updated_at'][:10]})")

    # 2. Orphan entities — no inbound links
    cursor.execute("""
        SELECT slug, type, title FROM pages
        WHERE id NOT IN (SELECT to_page_id FROM links)
        AND id NOT IN (SELECT from_page_id FROM links)
        AND type != 'source'
    """)
    orphans = cursor.fetchall()
    if orphans:
        alerts.append(f"\n🔗 ORPHAN ENTITIES ({len(orphans)}):")
        for o in orphans:
            alerts.append(f"  [{o['type']}] {o['title']} — no inbound or outbound links")

    # 3. Timeline gaps — entities with activity >14 days ago, no recent activity
    gap_threshold = (now - timedelta(days=14)).strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT DISTINCT p.slug, p.type, p.title, MAX(t.date) as last_activity
        FROM pages p
        JOIN timeline_entries t ON t.page_id = p.id
        GROUP BY p.id
        HAVING last_activity < ?
        ORDER BY last_activity ASC
    """, (gap_threshold,))
    gaps = cursor.fetchall()
    if gaps:
        alerts.append(f"\n📅 TIMELINE GAPS ({len(gaps)}):")
        for g in gaps:
            alerts.append(f"  [{g['type']}] {g['title']} — last activity: {g['last_activity']}")

    # 4. Entities with open threads but no recent activity
    # (check frontmatter for open_threads)
    cursor.execute("SELECT slug, type, title, frontmatter FROM pages")
    all_pages = cursor.fetchall()
    open_threads = []
    for p in all_pages:
        fm = json.loads(p["frontmatter"]) if p["frontmatter"] else {}
        if fm.get("open_threads"):
            open_threads.append((p["slug"], p["type"], p["title"], fm["open_threads"]))
    if open_threads:
        alerts.append(f"\n📋 OPEN THREADS ({len(open_threads)}):")
        for slug, typ, title, threads in open_threads:
            for t in threads:
                alerts.append(f"  [{typ}] {title}: {t}")

    conn.close()

    if not alerts:
        print("✅ All clear. No maintenance issues found.")
    else:
        print(f"\n🔧 Maintenance Report\n{'='*40}")
        for a in alerts:
            print(a)

    return alerts


def main():
    parser = argparse.ArgumentParser(description="Knowledge Brain CLI")
    parser.add_argument("action", nargs="?", default="stats",
                       choices=["init", "get", "search", "query", "list",
                               "import", "stats", "maintain"])
    parser.add_argument("--slug", "-s", help="Entity slug")
    parser.add_argument("query_pos", nargs="?", help="Query string (positional for search)")
    parser.add_argument("--type", "-t", help="Entity type filter")
    parser.add_argument("--tag", help="Tag filter")
    parser.add_argument("--limit", "-l", type=int, default=50, help="Result limit")
    parser.add_argument("--db", help="Path to brain.db")

    args = parser.parse_args()
    db_path = args.db or BRAIN_DB

    if args.action == "init":
        init_db(db_path)
    elif args.action == "import":
        import_entities(db_path)
    elif args.action == "get":
        if not args.slug:
            print("Usage: knowledge-brain.py get --slug people/lee-abrahams")
            sys.exit(1)
        get_entity(args.slug, db_path)
    elif args.action == "search":
        q = args.query_pos or args.query or ""
        if not q:
            print("Usage: knowledge-brain.py search 'Proximie'")
            sys.exit(1)
        search(q, args.limit, db_path)
    elif args.action == "query":
        q = args.query_pos or ""
        if not q:
            print("Usage: knowledge-brain.py query 'job applications status'")
            sys.exit(1)
        query_semantic(q, args.limit, db_path)
    elif args.action == "list":
        list_entities(args.type, args.tag, args.limit, db_path)
    elif args.action == "stats":
        stats(db_path)
    elif args.action == "maintain":
        maintain(db_path)


if __name__ == "__main__":
    main()
