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

    url_hash        TEXT,
    source_method   TEXT,
    search_title    TEXT,
    search_country  TEXT,
    date_posted     TEXT,

    tags            TEXT,
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_jobs_status   ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_company  ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_verdict  ON jobs(verdict);
CREATE INDEX IF NOT EXISTS idx_jobs_source   ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_url_hash ON jobs(url_hash);

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

CREATE TABLE IF NOT EXISTS status_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id      TEXT NOT NULL REFERENCES jobs(job_id),
    from_status TEXT,
    to_status   TEXT NOT NULL,
    changed_at  TEXT DEFAULT (datetime('now')),
    source      TEXT DEFAULT 'system'
);

CREATE INDEX IF NOT EXISTS idx_status_history_job_id ON status_history(job_id);
CREATE INDEX IF NOT EXISTS idx_status_history_changed ON status_history(changed_at);

CREATE TABLE IF NOT EXISTS recruiters (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT,
    email           TEXT,
    phone           TEXT,
    company         TEXT,
    linkedin_url    TEXT,
    last_contacted  TEXT,
    notes           TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_recruiters_email ON recruiters(email) WHERE email IS NOT NULL;

CREATE TABLE IF NOT EXISTS job_recruiters (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          TEXT NOT NULL REFERENCES jobs(job_id),
    recruiter_id    INTEGER NOT NULL REFERENCES recruiters(id),
    role            TEXT DEFAULT 'contact',
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(job_id, recruiter_id)
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
    """Generate a stable job_id when none is provided.
    Prefers URL-based hash (deterministic, matches scanner IDs).
    Falls back to multi-field hash for manual entries without URLs.
    """
    import hashlib
    if url:
        return url_hash(url)
    base = f"{source}|{company.lower().strip()}|{title.lower().strip()}"
    return f"gen-{hashlib.md5(base.encode()).hexdigest()[:12]}"


# ── URL-based hashing (unified ID scheme) ────────────────────────────────────
def url_hash(url: str) -> str:
    """Deterministic 12-char SHA256 hash from URL. Single ID scheme for all scripts."""
    import hashlib
    return hashlib.sha256(url.encode()).hexdigest()[:12]


# ── Scanner/Review functions (merged from jobs_db.py) ────────────────────────
def job_exists(url: str) -> bool:
    """Check if a job URL is already tracked."""
    if not ENABLED or not url:
        return False
    try:
        conn = _get_conn()
        h = url_hash(url)
        row = conn.execute("SELECT 1 FROM jobs WHERE url_hash = ? OR job_id = ?", (h, h)).fetchone()
        conn.close()
        return row is not None
    except Exception as e:
        log.error("job_exists failed: %s", e)
        return False


def is_duplicate(url: str) -> bool:
    """Single dedup check - replaces all scattered dedup logic."""
    return job_exists(url)


def upsert_job(job: dict) -> str:
    """Insert or update a job from scanner/review. Returns 'inserted', 'updated', or 'skipped'.

    Expects dict with keys: url, title, company, location, source, source_method,
    search_title, search_country, date_posted, ats_score, fit_score, verdict, etc.
    Protects applied/cv_built/response status from being overwritten by discovery.
    """
    if not ENABLED:
        return "skipped"
    url = job.get("url", "")
    if not url:
        return "skipped"

    h = url_hash(url)
    try:
        conn = _get_conn()
        existing = conn.execute(
            "SELECT id, status, job_id FROM jobs WHERE url_hash = ? OR job_id = ? OR job_url = ?",
            (h, h, url)
        ).fetchone()

        if existing:
            ex_status = existing["status"] or ""
            # Don't overwrite advanced statuses with discovered
            if ex_status in ("applied", "cv_built", "response", "interview", "offer"):
                updates = {}
                for field in ("ats_score", "fit_score", "verdict", "jd_text"):
                    if job.get(field) is not None:
                        updates[field] = job[field]
                if updates:
                    updates["updated_at"] = _now_iso()
                    sets = ", ".join(f"{k} = ?" for k in updates)
                    vals = list(updates.values()) + [existing["job_id"]]
                    conn.execute(f"UPDATE jobs SET {sets} WHERE job_id = ?", vals)
                    conn.commit()
                conn.close()
                return "updated"

            # Update scoring/enrichment for discovered/scored jobs
            updates = {}
            for field in ("ats_score", "fit_score", "verdict", "score_notes", "jd_text",
                          "jd_fetched_at", "source_method", "search_title", "search_country",
                          "date_posted", "status", "location", "country"):
                if job.get(field) is not None:
                    updates[field] = job[field]
            if updates:
                updates["updated_at"] = _now_iso()
                sets = ", ".join(f"{k} = ?" for k in updates)
                vals = list(updates.values()) + [existing["job_id"]]
                conn.execute(f"UPDATE jobs SET {sets} WHERE job_id = ?", vals)
            conn.commit()
            conn.close()
            return "updated"

        # Insert new job
        conn.execute("""
            INSERT INTO jobs (job_id, url_hash, job_url, title, company, location, country,
                              source, source_method, search_title, search_country, date_posted,
                              ats_score, fit_score, verdict, score_notes, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            h, h, url,
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
            _now_iso(), _now_iso(),
        ))
        conn.commit()
        conn.close()
        return "inserted"
    except Exception as e:
        log.error("upsert_job failed for %s: %s", url[:60], e)
        return "skipped"


def is_company_tracked(company: str) -> bool:
    """Check if we have jobs from this company in applied/cv_built/response status."""
    if not ENABLED or not company or company.lower() in ("confidential", "unknown"):
        return False
    try:
        conn = _get_conn()
        row = conn.execute("""
            SELECT 1 FROM jobs WHERE LOWER(company) = LOWER(?)
            AND status IN ('applied', 'cv_built', 'response', 'interview', 'offer') LIMIT 1
        """, (company,)).fetchone()
        conn.close()
        return row is not None
    except Exception as e:
        log.error("is_company_tracked failed: %s", e)
        return False


def get_unscored_jobs(limit: int = 300) -> list:
    """Get jobs that haven't been reviewed yet."""
    if not ENABLED:
        return []
    try:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT * FROM jobs
            WHERE status = 'discovered' AND verdict IS NULL
            ORDER BY created_at DESC LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        log.error("get_unscored_jobs failed: %s", e)
        return []


def get_unenriched_jobs(limit: int = 50) -> list:
    """Get scored jobs that need JD enrichment."""
    if not ENABLED:
        return []
    try:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT * FROM jobs
            WHERE (jd_text IS NULL OR jd_text = '')
            AND verdict IN ('APPLY', 'STRETCH', 'SUBMIT', 'REVIEW')
            AND status IN ('discovered', 'scored')
            ORDER BY fit_score DESC LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        log.error("get_unenriched_jobs failed: %s", e)
        return []


def get_scanner_funnel_stats() -> dict:
    """Pipeline funnel for scanner/review reporting."""
    if not ENABLED:
        return {}
    try:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT status, COUNT(*) as cnt FROM jobs GROUP BY status ORDER BY cnt DESC
        """).fetchall()
        stats = {r["status"]: r["cnt"] for r in rows}

        source_rows = conn.execute("""
            SELECT source_method, COUNT(*) as cnt FROM jobs
            WHERE status = 'applied' AND source_method IS NOT NULL AND source_method != ''
            GROUP BY source_method
        """).fetchall()
        stats["by_source"] = {r["source_method"]: r["cnt"] for r in source_rows}

        applied = stats.get("applied", 0)
        responded = stats.get("response", 0)
        stats["response_rate"] = f"{responded}/{applied} ({responded/applied*100:.1f}%)" if applied > 0 else "0/0"
        conn.close()
        return stats
    except Exception as e:
        log.error("get_scanner_funnel_stats failed: %s", e)
        return {}


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
        # Compute url_hash if URL provided
        _uhash = url_hash(url) if url else None
        # First try insert
        conn.execute("""
            INSERT OR IGNORE INTO jobs
                (job_id, source, company, title, location, country, job_url,
                 url_hash, jd_text, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id, source, company, title, location, country, url,
            _uhash, jd_text, status, _now_iso(), _now_iso()
        ))

        # Then update any new enrichment fields that were provided
        update_fields = {}
        if url:
            update_fields["job_url"] = url
            update_fields["url_hash"] = _uhash
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


def update_status(job_id: str, new_status: str, notes: str = None, source: str = "system") -> bool:
    """Update the lifecycle status of a job. Records transition in status_history.
    Returns True on success."""
    if not ENABLED or not job_id:
        return False
    try:
        conn = _get_conn()
        # Get current status for history
        row = conn.execute("SELECT status FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        old_status = row["status"] if row else None

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

        # Record transition in status_history
        if old_status != new_status:
            conn.execute("""
                INSERT INTO status_history (job_id, from_status, to_status, changed_at, source)
                VALUES (?, ?, ?, ?, ?)
            """, (job_id, old_status, new_status, _now_iso(), source))

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
            AND (recruiter_email IS NOT NULL OR recruiter_name IS NOT NULL)
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


# ══════════════════════════════════════════════════════════════════════════════
# LIFECYCLE FUNCTIONS (D7)
# ══════════════════════════════════════════════════════════════════════════════

def get_status_history(job_id: str) -> list:
    """Get all status transitions for a job, ordered chronologically."""
    if not ENABLED or not job_id:
        return []
    try:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT * FROM status_history WHERE job_id = ? ORDER BY changed_at ASC
        """, (job_id,)).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        log.error("get_status_history failed: %s", e)
        return []


def get_recent_transitions(days: int = 1, to_status: str = None) -> list:
    """Get recent status transitions. Optionally filter by destination status."""
    if not ENABLED:
        return []
    try:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        conn = _get_conn()
        if to_status:
            rows = conn.execute("""
                SELECT sh.*, j.company, j.title FROM status_history sh
                JOIN jobs j ON j.job_id = sh.job_id
                WHERE sh.changed_at >= ? AND sh.to_status = ?
                ORDER BY sh.changed_at DESC
            """, (cutoff, to_status)).fetchall()
        else:
            rows = conn.execute("""
                SELECT sh.*, j.company, j.title FROM status_history sh
                JOIN jobs j ON j.job_id = sh.job_id
                WHERE sh.changed_at >= ?
                ORDER BY sh.changed_at DESC
            """, (cutoff,)).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        log.error("get_recent_transitions failed: %s", e)
        return []


def get_stage_velocity() -> dict:
    """Compute average days between stages from status_history."""
    if not ENABLED:
        return {}
    try:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT job_id, from_status, to_status, changed_at
            FROM status_history ORDER BY job_id, changed_at
        """).fetchall()
        conn.close()

        # Group by job, compute time between transitions
        from collections import defaultdict
        transitions = defaultdict(list)
        for r in rows:
            transitions[r["job_id"]].append(_row_to_dict(r))

        stage_times = defaultdict(list)
        for job_id, hist in transitions.items():
            for i in range(1, len(hist)):
                from_s = hist[i-1]["to_status"]
                to_s = hist[i]["to_status"]
                try:
                    t1 = datetime.fromisoformat(hist[i-1]["changed_at"].replace("Z", "+00:00"))
                    t2 = datetime.fromisoformat(hist[i]["changed_at"].replace("Z", "+00:00"))
                    days = (t2 - t1).total_seconds() / 86400
                    if days >= 0:
                        stage_times[f"{from_s}->{to_s}"].append(days)
                except Exception:
                    pass

        velocity = {}
        for transition, times in stage_times.items():
            velocity[transition] = {
                "avg_days": round(sum(times) / len(times), 1),
                "count": len(times),
                "min_days": round(min(times), 1),
                "max_days": round(max(times), 1),
            }
        return velocity
    except Exception as e:
        log.error("get_stage_velocity failed: %s", e)
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# RECRUITER FUNCTIONS (D9)
# ══════════════════════════════════════════════════════════════════════════════

def add_recruiter(name: str = None, email: str = None, phone: str = None,
                  company: str = None, linkedin_url: str = None, notes: str = None) -> int:
    """Add or find a recruiter. Returns recruiter_id. Deduplicates by email."""
    if not ENABLED:
        return -1
    try:
        conn = _get_conn()
        # Check if exists by email
        if email:
            row = conn.execute("SELECT id FROM recruiters WHERE email = ?", (email,)).fetchone()
            if row:
                # Update fields if new info provided
                updates = {}
                if name:
                    updates["name"] = name
                if phone:
                    updates["phone"] = phone
                if company:
                    updates["company"] = company
                if linkedin_url:
                    updates["linkedin_url"] = linkedin_url
                if notes:
                    updates["notes"] = notes
                if updates:
                    updates["updated_at"] = _now_iso()
                    sets = ", ".join(f"{k} = ?" for k in updates)
                    vals = list(updates.values()) + [row["id"]]
                    conn.execute(f"UPDATE recruiters SET {sets} WHERE id = ?", vals)
                    conn.commit()
                conn.close()
                return row["id"]

        # Insert new
        cur = conn.execute("""
            INSERT INTO recruiters (name, email, phone, company, linkedin_url, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, company, linkedin_url, notes, _now_iso(), _now_iso()))
        rid = cur.lastrowid
        conn.commit()
        conn.close()
        return rid
    except Exception as e:
        log.error("add_recruiter failed: %s", e)
        return -1


def link_recruiter_to_job(job_id: str, recruiter_id: int, role: str = "contact") -> bool:
    """Link a recruiter to a job (many-to-many)."""
    if not ENABLED or not job_id or recruiter_id < 0:
        return False
    try:
        conn = _get_conn()
        conn.execute("""
            INSERT OR IGNORE INTO job_recruiters (job_id, recruiter_id, role, created_at)
            VALUES (?, ?, ?, ?)
        """, (job_id, recruiter_id, role, _now_iso()))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log.error("link_recruiter_to_job failed: %s", e)
        return False


def get_job_recruiters(job_id: str) -> list:
    """Get all recruiters linked to a job."""
    if not ENABLED or not job_id:
        return []
    try:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT r.*, jr.role FROM recruiters r
            JOIN job_recruiters jr ON jr.recruiter_id = r.id
            WHERE jr.job_id = ?
        """, (job_id,)).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        log.error("get_job_recruiters failed: %s", e)
        return []


def get_recruiter_jobs(recruiter_id: int) -> list:
    """Get all jobs linked to a recruiter."""
    if not ENABLED or recruiter_id < 0:
        return []
    try:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT j.*, jr.role FROM jobs j
            JOIN job_recruiters jr ON jr.job_id = j.job_id
            WHERE jr.recruiter_id = ?
        """, (recruiter_id,)).fetchall()
        conn.close()
        return [_row_to_dict(r) for r in rows]
    except Exception as e:
        log.error("get_recruiter_jobs failed: %s", e)
        return []


def update_recruiter_contacted(recruiter_id: int, date: str = None) -> bool:
    """Update last_contacted date for a recruiter."""
    if not ENABLED or recruiter_id < 0:
        return False
    try:
        conn = _get_conn()
        conn.execute("UPDATE recruiters SET last_contacted = ?, updated_at = ? WHERE id = ?",
                     (date or _now_iso(), _now_iso(), recruiter_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log.error("update_recruiter_contacted failed: %s", e)
        return False


def migrate_flat_recruiters() -> int:
    """Migrate existing flat recruiter fields from jobs table into recruiters/job_recruiters tables.
    Safe to run multiple times (deduplicates by email)."""
    if not ENABLED:
        return 0
    try:
        conn = _get_conn()
        rows = conn.execute("""
            SELECT job_id, recruiter_name, recruiter_email, recruiter_phone, recruiter_company
            FROM jobs WHERE recruiter_name IS NOT NULL OR recruiter_email IS NOT NULL
        """).fetchall()
        conn.close()

        migrated = 0
        for r in rows:
            rid = add_recruiter(
                name=r["recruiter_name"],
                email=r["recruiter_email"],
                phone=r["recruiter_phone"],
                company=r["recruiter_company"],
            )
            if rid >= 0:
                link_recruiter_to_job(r["job_id"], rid)
                migrated += 1
        return migrated
    except Exception as e:
        log.error("migrate_flat_recruiters failed: %s", e)
        return 0


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
