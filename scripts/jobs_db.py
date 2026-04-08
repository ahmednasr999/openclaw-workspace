#!/usr/bin/env python3
"""
jobs_db.py - Single source of truth for the job pipeline.

All scripts read/write through this module. No more dual-write to JSON/JSONL/markdown.
SQLite DB: data/nasr-pipeline.db
"""

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("/root/.openclaw/workspace/data/nasr-pipeline.db")


def get_db():
    """Get a connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def url_hash(url: str) -> str:
    """Deterministic 12-char hash from URL."""
    return hashlib.sha256(url.encode()).hexdigest()[:12]


def job_exists(conn, url: str) -> bool:
    """Check if a job URL is already tracked."""
    h = url_hash(url)
    row = conn.execute("SELECT 1 FROM jobs WHERE url_hash = ?", (h,)).fetchone()
    return row is not None


def upsert_job(conn, job: dict) -> str:
    """Insert or update a job. Returns 'inserted', 'updated', or 'skipped'.
    
    Expects dict with keys: url, title, company, location, source, source_method,
    search_title, search_country, date_posted, ats_score, fit_score, verdict, etc.
    """
    url = job.get("url", "")
    if not url:
        return "skipped"

    h = url_hash(url)
    existing = conn.execute("SELECT id, status FROM jobs WHERE url_hash = ?", (h,)).fetchone()

    if existing:
        # Don't overwrite applied/cv_built/response status with discovered
        if existing["status"] in ("applied", "cv_built", "response"):
            # Only update scoring fields if provided
            updates = {}
            if job.get("ats_score") is not None:
                updates["ats_score"] = job["ats_score"]
            if job.get("fit_score") is not None:
                updates["fit_score"] = job["fit_score"]
            if job.get("verdict"):
                updates["verdict"] = job["verdict"]
            if job.get("jd_text"):
                updates["jd_text"] = job["jd_text"]
            if updates:
                sets = ", ".join(f"{k} = ?" for k in updates)
                vals = list(updates.values()) + [h]
                conn.execute(f"UPDATE jobs SET {sets}, updated_at = datetime('now') WHERE url_hash = ?", vals)
            return "updated"

        # Update scoring/enrichment for discovered/scored jobs
        updates = {}
        for field in ["ats_score", "fit_score", "verdict", "score_notes", "jd_text",
                       "jd_fetched_at", "source_method", "search_title", "search_country",
                       "date_posted", "status"]:
            if job.get(field) is not None:
                updates[field] = job[field]
        if updates:
            sets = ", ".join(f"{k} = ?" for k in updates)
            vals = list(updates.values()) + [h]
            conn.execute(f"UPDATE jobs SET {sets}, updated_at = datetime('now') WHERE url_hash = ?", vals)
        return "updated"

    # Insert new job
    conn.execute("""
        INSERT INTO jobs (job_id, url_hash, job_url, title, company, location, country,
                          source, source_method, search_title, search_country, date_posted,
                          ats_score, fit_score, verdict, score_notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        h,  # job_id = url_hash for new entries
        h,
        url,
        job.get("title", "Unknown"),
        job.get("company", "Confidential"),
        job.get("location", ""),
        job.get("search_country", job.get("country", "")),
        job.get("source", job.get("site", "exa")),
        job.get("source_method", ""),
        job.get("search_title", ""),
        job.get("search_country", ""),
        job.get("date_posted", ""),
        job.get("ats_score"),
        job.get("fit_score", job.get("career_fit")),
        job.get("verdict", job.get("career_verdict", "discovered")),
        job.get("score_notes", job.get("career_reason", "")),
        job.get("status", "discovered"),
    ))
    return "inserted"


def get_unscored_jobs(conn, limit=300):
    """Get jobs that haven't been reviewed yet."""
    return conn.execute("""
        SELECT * FROM jobs 
        WHERE status = 'discovered' AND verdict IS NULL
        ORDER BY created_at DESC LIMIT ?
    """, (limit,)).fetchall()


def get_unenriched_jobs(conn, limit=50):
    """Get scored jobs that need JD enrichment."""
    return conn.execute("""
        SELECT * FROM jobs 
        WHERE (jd_text IS NULL OR jd_text = '') 
        AND verdict IN ('APPLY', 'STRETCH')
        AND status IN ('discovered', 'scored')
        ORDER BY fit_score DESC LIMIT ?
    """, (limit,)).fetchall()


def mark_applied(conn, url_or_hash: str, applied_date=None, applied_via="manual"):
    """Mark a job as applied."""
    h = url_or_hash if len(url_or_hash) == 12 else url_hash(url_or_hash)
    conn.execute("""
        UPDATE jobs SET status = 'applied', applied_date = ?, applied_via = ?,
        updated_at = datetime('now') WHERE url_hash = ?
    """, (applied_date or datetime.now().strftime("%Y-%m-%d"), applied_via, h))


def is_duplicate(conn, url: str) -> bool:
    """Single dedup check - replaces all the scattered dedup logic."""
    return job_exists(conn, url)


def is_company_tracked(conn, company: str) -> bool:
    """Check if we already have jobs from this company in applied/cv_built status."""
    if not company or company.lower() in ("confidential", "unknown"):
        return False
    row = conn.execute("""
        SELECT 1 FROM jobs WHERE LOWER(company) = LOWER(?) 
        AND status IN ('applied', 'cv_built', 'response') LIMIT 1
    """, (company,)).fetchone()
    return row is not None


def get_funnel_stats(conn):
    """Pipeline funnel for D10 reporting."""
    rows = conn.execute("""
        SELECT status, COUNT(*) as cnt FROM jobs GROUP BY status ORDER BY cnt DESC
    """).fetchall()
    stats = {r["status"]: r["cnt"] for r in rows}

    # Source breakdown for applied jobs
    source_rows = conn.execute("""
        SELECT source_method, COUNT(*) as cnt FROM jobs 
        WHERE status = 'applied' AND source_method IS NOT NULL AND source_method != ''
        GROUP BY source_method
    """).fetchall()
    stats["by_source"] = {r["source_method"]: r["cnt"] for r in source_rows}

    # Response rate
    applied = stats.get("applied", 0)
    responded = stats.get("response", 0)
    stats["response_rate"] = f"{responded}/{applied} ({responded/applied*100:.1f}%)" if applied > 0 else "0/0"

    return stats


if __name__ == "__main__":
    conn = get_db()
    stats = get_funnel_stats(conn)
    print("Pipeline Funnel:")
    for k, v in stats.items():
        if k != "by_source":
            print(f"  {k}: {v}")
    if stats.get("by_source"):
        print("  By source:")
        for k, v in stats["by_source"].items():
            print(f"    {k}: {v}")
    conn.close()
