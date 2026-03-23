#!/usr/bin/env python3
"""
pipeline_db.py — Pipeline Intelligence Database module.

Single access point for all SQLite operations on nasr-pipeline.db.
All writes are safe: try/except wrapped. Kill switch via ENABLED flag.

Usage (safe fallback pattern in other scripts):
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        import pipeline_db as pdb
    except ImportError:
        pdb = None
    ...
    if pdb: pdb.register_job(...)
"""

import sqlite3
import json
import os
import sys
import shutil
import csv
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from difflib import SequenceMatcher

# ── Kill switch ──────────────────────────────────────────────────────────────
ENABLED = True  # Set to False to disable all DB reads/writes without code changes

# ── Config ───────────────────────────────────────────────────────────────────
WORKSPACE = Path("/root/.openclaw/workspace")
DB_PATH = WORKSPACE / "data" / "nasr-pipeline.db"
BACKUP_DIR = WORKSPACE / "data" / "backups"

# ── Logging ──────────────────────────────────────────────────────────────────
log = logging.getLogger("pipeline_db")
if not log.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("[pipeline_db] %(levelname)s %(message)s"))
    log.addHandler(handler)
log.setLevel(logging.WARNING)  # Quiet by default; set DEBUG to troubleshoot


# ── Schema ───────────────────────────────────────────────────────────────────
SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          TEXT UNIQUE,
    source          TEXT,
    company         TEXT NOT NULL,
    title           TEXT NOT NULL,
    location        TEXT,
    country         TEXT,
    job_url         TEXT,

    jd_text         TEXT,
    jd_path         TEXT,
    jd_fetched_at   TEXT,

    ats_score       INTEGER,
    fit_score       INTEGER,
    verdict         TEXT,
    score_notes     TEXT,

    cv_path         TEXT,
    cv_html_path    TEXT,
    cv_cluster      TEXT,
    cv_built_at     TEXT,

    status          TEXT DEFAULT 'discovered',
    applied_date    TEXT,
    applied_via     TEXT,

    recruiter_name  TEXT,
    recruiter_email TEXT,
    recruiter_company TEXT,
    recruiter_phone TEXT,

    follow_up_date  TEXT,
    next_action     TEXT,

    salary_range    TEXT,
    salary_currency TEXT,

    notion_page_id  TEXT,
    notion_synced   INTEGER DEFAULT 0,

    tags            TEXT,
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_jobs_status  ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_verdict ON jobs(verdict);
CREATE INDEX IF NOT EXISTS idx_jobs_source  ON jobs(source);

CREATE TABLE IF NOT EXISTS interactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id      TEXT REFERENCES jobs(job_id),
    type        TEXT NOT NULL,
    date        TEXT NOT NULL,
    summary     TEXT,
    from_name   TEXT,
    from_email  TEXT,
    channel     TEXT,
    next_action TEXT,
    notes       TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_interactions_job_id ON interactions(job_id);

CREATE TABLE IF NOT EXISTS keywords (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword     TEXT UNIQUE NOT NULL,
    frequency   INTEGER DEFAULT 1,
    in_master_cv INTEGER DEFAULT 0,
    category    TEXT,
    last_seen   TEXT
);

CREATE INDEX IF NOT EXISTS idx_keywords_frequency ON keywords(frequency);

CREATE TABLE IF NOT EXISTS cv_templates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_name    TEXT UNIQUE NOT NULL,
    template_path   TEXT,
    target_keywords TEXT,
    jobs_covered    INTEGER DEFAULT 0,
    avg_ats_score   REAL,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
"""


# ── Connection ────────────────────────────────────────────────────────────────
def _get_conn() -> sqlite3.Connection:
    """Open a WAL-mode connection. Caller is responsible for close()."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create tables if they don't exist. Safe to call multiple times."""
    if not ENABLED:
        return
    try:
        conn = _get_conn()
        conn.executescript(SCHEMA)
        conn.commit()
        conn.close()
        log.debug("DB initialized at %s", DB_PATH)
    except Exception as e:
        log.error("init_db failed: %s", e)


# Auto-init on import
try:
    init_db()
except Exception:
    pass


# ── Helpers ───────────────────────────────────────────────────────────────────
def _now_iso() -> str:
    cairo = timezone(timedelta(hours=2))
    return datetime.now(cairo).isoformat()


def _row_to_dict(row) -> dict:
    if row is None:
        return None
    return dict(row)


def _generate_job_id(source: str, company: str, title: str, url: str = "") -> str:
    """Generate a stable job_id when none is provided."""
    import hashlib
    base = f"{source}|{company.lower().strip()}|{title.lower().strip()}|{url}"
    return f"gen-{hashlib.md5(base.encode()).hexdigest()[:12]}"


# ══════════════════════════════════════════════════════════════════════════════
# WRITE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def register_job(
    source: str,
    job_id: str,
    company: str,
    title: str,
    location: str = None,
    url: str = None,
    jd_text: str = None,
    country: str = None,
    status: str = "discovered",
    **extra
) -> str:
    """
    INSERT OR IGNORE a job record. Returns job_id.
    If job already exists, updates enrichment fields (non-destructive UPSERT).
    Safe: returns job_id even if DB is disabled or fails.
    """
    if not ENABLED:
        return job_id

    if not job_id:
        job_id = _generate_job_id(source or "unknown", company or "", title or "", url or "")

    try:
        conn = _get_conn()
        # First try insert
        conn.execute("""
            INSERT OR IGNORE INTO jobs
                (job_id, source, company, title, location, country, job_url,
                 jd_text, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id, source, company, title, location, country, url,
            jd_text, status, _now_iso(), _now_iso()
        ))

        # Then update any new enrichment fields that were provided
        update_fields = {}
        if url:
            update_fields["job_url"] = url
        if jd_text:
            update_fields["jd_text"] = jd_text
        if location:
            update_fields["location"] = location
        if country:
            update_fields["country"] = country

        # Handle extra fields that map to columns
        allowed_columns = {
            "ats_score", "fit_score", "verdict", "score_notes",
            "cv_path", "cv_html_path", "cv_cluster", "cv_built_at",
            "applied_date", "applied_via",
            "recruiter_name", "recruiter_email", "recruiter_company", "recruiter_phone",
            "follow_up_date", "next_action",
            "salary_range", "salary_currency",
            "notion_page_id", "notion_synced",
            "tags", "notes", "jd_path", "jd_fetched_at",
        }
        for k, v in extra.items():
            if k in allowed_columns and v is not None:
                update_fields[k] = v

        if update_fields:
            update_fields["updated_at"] = _now_iso()
            sets = ", ".join(f"{k} = COALESCE({k}, ?)" for k in update_fields if k != "updated_at")
            vals = [update_fields[k] for k in update_fields if k != "updated_at"]
            # updated_at always refreshes
            conn.execute(
                f"UPDATE jobs SET {sets}, updated_at = ? WHERE job_id = ?",
                vals + [_now_iso(), job_id]
            )

        conn.commit()
        conn.close()
        log.debug("register_job: %s | %s @ %s", job_id, title, company)
    except Exception as e:
        log.error("register_job failed for %s: %s", job_id, e)

    return job_id


def update_score(
    job_id: str,
    ats_score: int = None,
    fit_score: int = None,
    verdict: str = None,
    notes: str = None,
) -> bool:
    """Update scoring fields on an existing job. Returns True on success."""
    if not ENABLED or not job_id:
        return False
    try:
        conn = _get_conn()
        fields = {}
        if ats_score is not None:
            fields["ats_score"] = ats_score
        if fit_score is not None:
            fields["fit_score"] = fit_score
        if verdict is not None:
            fields["verdict"] = verdict
        if notes is not None:
            fields["score_notes"] = notes

        if not fields:
            conn.close()
            return False

        # Auto-advance status if scored
        if "verdict" in fields and fields["verdict"] in ("SUBMIT", "REVIEW", "SKIP"):
            fields["status"] = "scored"

        fields["updated_at"] = _now_iso()
        sets = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values()) + [job_id]
        conn.execute(f"UPDATE jobs SET {sets} WHERE job_id = ?", vals)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log.error("update_score failed for %s: %s", job_id, e)
        return False


def attach_cv(
    job_id: str,
    cv_path: str,
    cv_html_path: str = None,
    cluster: str = None,
) -> bool:
    """Record CV attachment to a job. Returns True on success."""
    if not ENABLED or not job_id:
        return False
    try:
        conn = _get_conn()
        conn.execute("""
            UPDATE jobs
            SET cv_path = ?, cv_html_path = ?, cv_cluster = ?,
                cv_built_at = ?, status = CASE
                    WHEN status IN ('discovered', 'scored') THEN 'cv_built'
                    ELSE status
                END,
                updated_at = ?
            WHERE job_id = ?
        """, (cv_path, cv_html_path, cluster, _now_iso(), _now_iso(), job_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log.error("attach_cv failed for %s: %s", job_id, e)
        return False


def mark_applied(
    job_id: str,
    applied_date: str = None,
    applied_via: str = None,
) -> bool:
    """Mark a job as applied. Returns True on success."""
    if not ENABLED or not job_id:
        return False
    try:
        if not applied_date:
            applied_date = _now_iso()[:10]
        conn = _get_conn()
        conn.execute("""
            UPDATE jobs
            SET status = 'applied', applied_date = ?, applied_via = ?, updated_at = ?
            WHERE job_id = ?
        """, (applied_date, applied_via, _now_iso(), job_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log.error("mark_applied failed for %s: %s", job_id, e)
        return False


def log_interaction(
    job_id: str,
    type: str,
    summary: str,
    from_name: str = None,
    from_email: str = None,
    channel: str = None,
    next_action: str = None,
    notes: str = None,
    date: str = None,
) -> bool:
    """Record an interaction (email, call, message) for a job. Returns True on success."""
    if not ENABLED or not job_id:
        return False
    try:
        if not date:
            date = _now_iso()
        conn = _get_conn()
        conn.execute("""
            INSERT INTO interactions (job_id, type, date, summary, from_name, from_email,
                                      channel, next_action, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (job_id, type, date, summary, from_name, from_email, channel, next_action, notes))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log.error("log_interaction failed for %s: %s", job_id, e)
        return False


def update_status(job_id: str, new_status: str, notes: str = None) -> bool:
    """Update the lifecycle status of a job. Returns True on success."""
    if not ENABLED or not job_id:
        return False
    try:
        conn = _get_conn()
        if notes:
            conn.execute("""
                UPDATE jobs SET status = ?, notes = COALESCE(notes || '\n', '') || ?,
                updated_at = ? WHERE job_id = ?
            """, (new_status, notes, _now_iso(), job_id))
        else:
            conn.execute(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
                (new_status, _now_iso(), job_id)
            )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log.error("update_status failed for %s: %s", job_id, e)
        return False


def update_field(job_id: str, **fields) -> bool:
    """
    Flexible field update — pass any column=value kwargs.
    Example: update_field(job_id, jd_text="...", jd_path="...", notion_synced=1)
    Returns True on success.
    """
    if not ENABLED or not job_id or not fields:
        return False
    try:
        allowed_columns = {
            "source", "company", "title", "location", "country", "job_url",
            "jd_text", "jd_path", "jd_fetched_at",
            "ats_score", "fit_score", "verdict", "score_notes",
            "cv_path", "cv_html_path", "cv_cluster", "cv_built_at",
            "status", "applied_date", "applied_via",
            "recruiter_name", "recruiter_email", "recruiter_company", "recruiter_phone",
            "follow_up_date", "next_action",
            "salary_range", "salary_currency",
            "notion_page_id", "notion_synced",
            "tags", "notes",
        }
        safe_fields = {k: v for k, v in fields.items() if k in allowed_columns}
        if not safe_fields:
            return False

        safe_fields["updated_at"] = _now_iso()
        sets = ", ".join(f"{k} = ?" for k in safe_fields)
        vals = list(safe_fields.values()) + [job_id]
        conn = _get_conn()
        conn.execute(f"UPDATE jobs SET {sets} WHERE job_id = ?", vals)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log.error("update_field failed for %s: %s", job_id, e)
        return False


# ══════════════════════════════════════════════════════════════════════════════
# READ FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_job(job_id: str) -> dict:
    """Fetch a single job by job_id. Returns dict or None."""
    if not ENABLED or not job_id:
        return None
    try:
        conn = _get_conn()
        row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        conn.close()
        return _row_to_dict(row)
    except Exception as e:
        log.error("get_job failed for %s: %s", job_id, e)
        return None


def get_by_company(company: str) -> list:
    """Fetch all jobs for a company (case-insensitive substring match). Returns list of dicts."""
    if not ENABLED or not company:
        return []
    try:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT * FROM jobs WHERE LOWER(company) LIKE ? ORDER BY created_at DESC",
            (f"%{company.lower()}%",)
        ).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        log.error("get_by_company failed for %s: %s", company, e)
        return []


def search(
    company: str = None,
    title: str = None,
    status: str = None,
    location: str = None,
    verdict: str = None,
    source: str = None,
    limit: int = 200,
) -> list:
    """
    Flexible search across jobs table.
    All filters are optional. Returns list of dicts.
    """
    if not ENABLED:
        return []
    try:
        conditions = []
        params = []

        if company:
            conditions.append("LOWER(company) LIKE ?")
            params.append(f"%{company.lower()}%")
        if title:
            conditions.append("LOWER(title) LIKE ?")
            params.append(f"%{title.lower()}%")
        if status:
            conditions.append("status = ?")
            params.append(status)
        if location:
            conditions.append("LOWER(location) LIKE ?")
            params.append(f"%{location.lower()}%")
        if verdict:
            conditions.append("verdict = ?")
            params.append(verdict)
        if source:
            conditions.append("source = ?")
            params.append(source)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        conn = _get_conn()
        rows = conn.execute(
            f"SELECT * FROM jobs {where} ORDER BY created_at DESC LIMIT ?",
            params + [limit]
        ).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        log.error("search failed: %s", e)
        return []


def get_stale(days: int = 7) -> list:
    """Return applied jobs with no response in the last `days` days."""
    if not ENABLED:
        return []
    try:
        cutoff = datetime.now().strftime("%Y-%m-%d")
        from datetime import timedelta
        cutoff_dt = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        conn = _get_conn()
        rows = conn.execute("""
            SELECT * FROM jobs
            WHERE status = 'applied'
            AND applied_date <= ?
            AND applied_date IS NOT NULL
            ORDER BY applied_date ASC
        """, (cutoff_dt,)).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        log.error("get_stale failed: %s", e)
        return []


def get_funnel() -> dict:
    """Return count of jobs at each lifecycle stage."""
    if not ENABLED:
        return {}
    try:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT status, COUNT(*) as n FROM jobs GROUP BY status ORDER BY n DESC"
        ).fetchall()
        conn.close()
        funnel = {r["status"]: r["n"] for r in rows}
        # Add total
        funnel["_total"] = sum(funnel.values())
        return funnel
    except Exception as e:
        log.error("get_funnel failed: %s", e)
        return {}


def get_recent(days: int = 1) -> list:
    """Return jobs created in the last `days` days."""
    if not ENABLED:
        return []
    try:
        cutoff = (datetime.now() - timedelta(hours=days * 24)).isoformat()
        conn = _get_conn()
        rows = conn.execute(
            "SELECT * FROM jobs WHERE created_at >= ? ORDER BY created_at DESC",
            (cutoff,)
        ).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        log.error("get_recent failed: %s", e)
        return []


def get_all(status: str = None, limit: int = 1000) -> list:
    """Return all jobs, optionally filtered by status."""
    if not ENABLED:
        return []
    try:
        conn = _get_conn()
        if status:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        log.error("get_all failed: %s", e)
        return []


def count_by_status() -> dict:
    """Return {status: count} mapping."""
    return get_funnel()


# ══════════════════════════════════════════════════════════════════════════════
# INTELLIGENCE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def analyze_keywords(top_n: int = 50) -> list:
    """Return top N most frequent JD keywords with metadata."""
    if not ENABLED:
        return []
    try:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT keyword, frequency, in_master_cv, category, last_seen
            FROM keywords
            ORDER BY frequency DESC
            LIMIT ?
        """, (top_n,)).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        log.error("analyze_keywords failed: %s", e)
        return []


def keyword_gaps() -> list:
    """Return keywords present in JDs but NOT in Ahmed's master CV."""
    if not ENABLED:
        return []
    try:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT keyword, frequency, category, last_seen
            FROM keywords
            WHERE in_master_cv = 0
            ORDER BY frequency DESC
        """).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        log.error("keyword_gaps failed: %s", e)
        return []


def suggest_clusters(n: int = 5) -> list:
    """
    Group jobs by CV cluster. Returns clusters with job counts and top companies.
    Falls back to grouping by verdict/status if no clusters set.
    """
    if not ENABLED:
        return []
    try:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT cv_cluster, COUNT(*) as job_count,
                   GROUP_CONCAT(company, ', ') as companies,
                   AVG(ats_score) as avg_ats
            FROM jobs
            WHERE cv_cluster IS NOT NULL
            GROUP BY cv_cluster
            ORDER BY job_count DESC
            LIMIT ?
        """, (n,)).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        log.error("suggest_clusters failed: %s", e)
        return []


def get_cv_reuse_candidates(job_id: str) -> list:
    """
    Find jobs that could share a CV with the given job_id.
    Matches on same cluster or same title keywords.
    """
    if not ENABLED or not job_id:
        return []
    try:
        conn = _get_conn()
        job = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if not job:
            conn.close()
            return []
        job = _row_to_dict(job)

        cluster = job.get("cv_cluster")
        rows = []
        if cluster:
            rows = conn.execute("""
                SELECT * FROM jobs
                WHERE cv_cluster = ? AND job_id != ? AND cv_path IS NOT NULL
                ORDER BY ats_score DESC LIMIT 10
            """, (cluster, job_id)).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        log.error("get_cv_reuse_candidates failed for %s: %s", job_id, e)
        return []


def funnel_conversion() -> dict:
    """Return conversion rates between pipeline stages."""
    if not ENABLED:
        return {}
    try:
        funnel = get_funnel()
        total = funnel.get("_total", 0) or 1

        # Key transition points
        discovered = funnel.get("discovered", 0)
        scored = funnel.get("scored", 0)
        cv_built = funnel.get("cv_built", 0)
        applied = funnel.get("applied", 0)
        response = funnel.get("response", 0)
        interview = funnel.get("interview", 0)
        offer = funnel.get("offer", 0)

        def pct(a, b):
            return round((a / b * 100), 1) if b else 0.0

        return {
            "discovered_to_scored": pct(scored + cv_built + applied, total),
            "scored_to_cv_built": pct(cv_built + applied, max(1, scored + cv_built + applied)),
            "cv_to_applied": pct(applied, max(1, cv_built + applied)),
            "applied_to_response": pct(response + interview + offer, max(1, applied)),
            "response_to_interview": pct(interview + offer, max(1, response + interview + offer)),
            "interview_to_offer": pct(offer, max(1, interview + offer)),
            "totals": funnel,
        }
    except Exception as e:
        log.error("funnel_conversion failed: %s", e)
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def export_csv(filepath: str) -> int:
    """Export all jobs to CSV. Returns number of rows written."""
    if not ENABLED:
        return 0
    try:
        conn = _get_conn()
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        conn.close()
        if not rows:
            return 0

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))

        log.info("Exported %d rows to %s", len(rows), filepath)
        return len(rows)
    except Exception as e:
        log.error("export_csv failed: %s", e)
        return 0


def backup() -> str:
    """
    Copy DB file with timestamp to data/backups/.
    Returns path of backup file, or empty string on failure.
    """
    if not ENABLED or not DB_PATH.exists():
        return ""
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        dest = BACKUP_DIR / f"nasr-pipeline-{ts}.db"
        shutil.copy2(DB_PATH, dest)
        log.info("Backup created: %s", dest)
        return str(dest)
    except Exception as e:
        log.error("backup failed: %s", e)
        return ""


def get_db_stats() -> dict:
    """Return basic stats about the DB for health checks."""
    if not ENABLED:
        return {"enabled": False}
    try:
        conn = _get_conn()
        jobs_count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        interactions_count = conn.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]
        keywords_count = conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
        last_update = conn.execute(
            "SELECT MAX(updated_at) FROM jobs"
        ).fetchone()[0]
        conn.close()
        db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        return {
            "enabled": True,
            "db_path": str(DB_PATH),
            "db_size_kb": round(db_size / 1024, 1),
            "jobs_count": jobs_count,
            "interactions_count": interactions_count,
            "keywords_count": keywords_count,
            "last_update": last_update,
        }
    except Exception as e:
        log.error("get_db_stats failed: %s", e)
        return {"enabled": True, "error": str(e)}


def index_keywords_from_jd(job_id: str, jd_text: str, master_cv_keywords: list = None):
    """
    Extract and index keywords from a JD text.
    master_cv_keywords: list of keywords known to be in Ahmed's CV.
    """
    if not ENABLED or not jd_text:
        return

    # Simple keyword extraction: split on whitespace/punctuation, keep meaningful words
    import re
    words = re.findall(r'\b[a-zA-Z][a-zA-Z\s\-/]{2,30}\b', jd_text.lower())

    # Common meaningful phrases to look for
    PHRASE_PATTERNS = [
        r'\b(?:pmo|pmp|agile|scrum|kanban|prince2|lean|six sigma|togaf|itil|cobit)\b',
        r'\b(?:digital transformation|change management|stakeholder management|portfolio management|program management|project management)\b',
        r'\b(?:data governance|data strategy|data analytics|business intelligence|ai|machine learning|cloud|erp|crm|sap|oracle)\b',
        r'\b(?:cto|cio|cdo|vp|director|head of|chief)\b',
        r'\b(?:fintech|banking|financial services|insurance|healthcare|telecom|retail|logistics)\b',
        r'\b(?:uae|saudi|gcc|qatar|bahrain|kuwait|oman|riyadh|dubai|abu dhabi)\b',
        r'\b(?:budget|p&l|revenue|cost reduction|roi|kpi|okr)\b',
    ]

    try:
        conn = _get_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        master_set = set(k.lower() for k in (master_cv_keywords or []))

        for pattern in PHRASE_PATTERNS:
            for match in re.finditer(pattern, jd_text.lower()):
                kw = match.group(0).strip()
                if len(kw) < 2:
                    continue
                in_cv = 1 if kw in master_set else 0
                conn.execute("""
                    INSERT INTO keywords (keyword, frequency, in_master_cv, last_seen)
                    VALUES (?, 1, ?, ?)
                    ON CONFLICT(keyword) DO UPDATE SET
                        frequency = frequency + 1,
                        in_master_cv = MAX(in_master_cv, excluded.in_master_cv),
                        last_seen = excluded.last_seen
                """, (kw, in_cv, today))

        conn.commit()
        conn.close()
    except Exception as e:
        log.error("index_keywords_from_jd failed for %s: %s", job_id, e)


# ── CLI entry point (for quick checks) ──────────────────────────────────────
if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if cmd == "stats":
        print("=== Pipeline DB Stats ===")
        print(json.dumps(get_db_stats(), indent=2))
    elif cmd == "funnel":
        print("=== Funnel ===")
        print(json.dumps(get_funnel(), indent=2))
    elif cmd == "status":
        print("=== By Status ===")
        print(json.dumps(count_by_status(), indent=2))
    elif cmd == "stale":
        jobs = get_stale(days=7)
        print(f"=== Stale Applications ({len(jobs)}) ===")
        for j in jobs:
            print(f"  {j['company']} | {j['title']} | applied {j.get('applied_date','?')}")
    elif cmd == "keywords":
        kws = analyze_keywords(top_n=20)
        print(f"=== Top Keywords ({len(kws)}) ===")
        for k in kws:
            print(f"  [{k['frequency']:3d}] {'✅' if k.get('in_master_cv') else '❌'} {k['keyword']}")
    elif cmd == "gaps":
        gaps = keyword_gaps()
        print(f"=== Keyword Gaps ({len(gaps)}) - In JDs but NOT in CV ===")
        for k in gaps[:20]:
            print(f"  [{k['frequency']:3d}] {k['keyword']}")
    elif cmd == "backup":
        path = backup()
        print(f"Backup: {path}")
    elif cmd == "company" and len(sys.argv) > 2:
        company = " ".join(sys.argv[2:])
        jobs = get_by_company(company)
        print(f"=== {company} ({len(jobs)} records) ===")
        for j in jobs:
            print(f"  [{j['status']}] {j['title']} | {j.get('verdict','?')} | ATS:{j.get('ats_score','?')}")
    else:
        print("Usage: pipeline_db.py [stats|funnel|status|stale|keywords|gaps|backup|company <name>]")
