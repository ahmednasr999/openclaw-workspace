#!/usr/bin/env python3
"""
push-to-nocodb.py — Push merged+enriched jobs to NocoDB and send Telegram status alerts.

Reads: data/jobs-merged.json (after enrich step fills jd_text)
       data/jobs-summary.json (after review step scores jobs)
Writes: NocoDB Jobs table (insert new, update scored)

Sends Telegram alerts after each phase:
  - Source scrape results (reads pipeline-phase-status.json)
  - NocoDB push summary (new/dupes/updated)
  - Top SUBMIT jobs with scores

Run: python3 scripts/push-to-nocodb.py [--dry-run]
Cron: Wired as Phase 3 in run-briefing-pipeline.sh (after review, before telegram)
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
CONFIG_DIR = WORKSPACE / "config"
NOCODB_CONFIG = CONFIG_DIR / "nocodb.json"
MERGED_FILE = DATA_DIR / "jobs-merged.json"
SUMMARY_FILE = DATA_DIR / "jobs-summary.json"
PHASE_STATUS_FILE = DATA_DIR / "pipeline-phase-status.json"

# Telegram config
TG_GROUP = "-1003882622947"
TG_TOPIC_CEO = "10"  # CEO General
TG_TOPIC_HR = "9"    # HR Desk

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, str(WORKSPACE / "scripts"))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

import requests


def load_nocodb_auth():
    """Load NocoDB config and authenticate."""
    cfg = json.loads(NOCODB_CONFIG.read_text())
    resp = requests.post(
        f"{cfg['url']}/api/v1/auth/user/signin",
        json={"email": cfg["email"], "password": cfg["password"]},
        timeout=10
    )
    resp.raise_for_status()
    token = resp.json()["token"]
    return {
        "url": cfg["url"],
        "table_id": cfg["table_id"],
        "headers": {"xc-auth": token, "Content-Type": "application/json"},
    }


def get_existing_urls(noco):
    """Get all existing URLs from NocoDB to dedup."""
    table_url = f"{noco['url']}/api/v2/tables/{noco['table_id']}/records"
    existing = set()
    offset = 0
    while True:
        r = requests.get(
            f"{table_url}?fields=Id,URL&limit=200&offset={offset}",
            headers=noco["headers"], timeout=15
        ).json()
        for row in r.get("list", []):
            if row.get("URL"):
                existing.add(row["URL"])
        if len(r.get("list", [])) < 200:
            break
        offset += 200
    return existing


def send_telegram(message, topic=None):
    """Send message to Telegram via openclaw CLI."""
    target = TG_GROUP
    if topic:
        target = f"{TG_GROUP}:{topic}"
    try:
        result = subprocess.run(
            ["openclaw", "message", "send", "--channel", "telegram",
             "--target", target, "--message", message],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0 or "Sent via Telegram" not in (result.stdout + result.stderr):
            print(f"  [TG ERROR] Delivery failed: {(result.stdout + result.stderr).strip()[:200]}")
        else:
            # Extract message ID
            _mid = next((p for p in (result.stdout+result.stderr).split() if p.strip().isdigit()), None)
            print(f"  [TG OK] Delivered (msg_id={_mid})")
    except Exception as e:
        print(f"  Telegram send failed: {e}")


def format_source_status():
    """Read pipeline phase status and format source scrape results."""
    if not PHASE_STATUS_FILE.exists():
        return None

    try:
        status = json.loads(PHASE_STATUS_FILE.read_text())
        phases = status.get("phases", {})
    except Exception:
        return None

    # Read raw source files for counts
    sources = {}
    for name, fname in [("LinkedIn", "linkedin.json"), ("Indeed", "indeed.json"), ("Google", "google-jobs.json")]:
        path = DATA_DIR / "jobs-raw" / fname
        if path.exists():
            try:
                data = json.loads(path.read_text())
                jobs = data.get("data", data) if isinstance(data, dict) else data
                ts = data.get("generated_at", "") if isinstance(data, dict) else ""
                sources[name] = {"count": len(jobs) if isinstance(jobs, list) else 0, "ts": ts}
            except Exception:
                sources[name] = {"count": 0, "ts": "error"}
        else:
            sources[name] = {"count": 0, "ts": "missing"}

    # Read merged count
    merged_count = 0
    if MERGED_FILE.exists():
        try:
            merged = json.loads(MERGED_FILE.read_text())
            jobs = merged.get("data", merged) if isinstance(merged, dict) else merged
            merged_count = len(jobs) if isinstance(jobs, list) else 0
        except Exception:
            pass

    lines = ["📡 Job Source Scrape Complete\n"]
    total_raw = 0
    for name, info in sources.items():
        status_icon = "✅" if info["count"] > 0 else "❌"
        lines.append(f"{status_icon} {name}: {info['count']} jobs")
        total_raw += info["count"]

    lines.append(f"\n📊 Raw: {total_raw} - After dedup & filters: {merged_count}")

    return "\n".join(lines)


def push_new_jobs(noco, dry_run=False):
    """Push new merged jobs to NocoDB. Returns stats dict."""
    if not MERGED_FILE.exists():
        return {"new": 0, "dupes": 0, "errors": 0, "total_merged": 0}

    merged = json.loads(MERGED_FILE.read_text())
    jobs = merged.get("data", merged) if isinstance(merged, dict) else merged
    if not isinstance(jobs, list):
        return {"new": 0, "dupes": 0, "errors": 0, "total_merged": 0}

    existing_urls = get_existing_urls(noco)
    table_url = f"{noco['url']}/api/v2/tables/{noco['table_id']}/records"

    # Source capitalization map
    source_cap = {"linkedin": "LinkedIn", "indeed": "Indeed", "google": "Google"}

    # Pre-load JD texts from SQLite for any jobs missing JD in merged JSON
    jd_from_db = {}
    try:
        import sqlite3 as _sql
        db_path = WORKSPACE / "data" / "nasr-pipeline.db"
        if db_path.exists():
            conn = _sql.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("SELECT job_url, jd_text FROM jobs WHERE jd_text IS NOT NULL AND length(jd_text) > 100 AND job_url IS NOT NULL")
            for row in cur.fetchall():
                jd_from_db[row[0]] = row[1]
            conn.close()
            print(f"  Loaded {len(jd_from_db)} JDs from SQLite for backfill")
    except Exception as e:
        print(f"  SQLite JD load warning: {e}")

    new_jobs = []
    dupes = 0
    for j in jobs:
        url = j.get("url", "")
        if url in existing_urls:
            dupes += 1
            continue
        new_jobs.append(j)

    if dry_run:
        return {"new": len(new_jobs), "dupes": dupes, "errors": 0, "total_merged": len(jobs)}

    created = 0
    errors = 0

    for i in range(0, len(new_jobs), 10):
        batch = []
        for j in new_jobs[i:i + 10]:
            row = {
                "Title": (j.get("title", "") or "Unknown")[:200],
                "Company": (j.get("company", "") or "Unknown")[:200],
                "Location": (j.get("location", "") or "")[:200],
                "URL": j.get("url", ""),
                "Source": source_cap.get(j.get("source", ""), j.get("source", "Other")),
                "Status": "New",
                "Keyword Score": j.get("keyword_score", 0),
                "Matched Keywords": (j.get("match_keywords", "") or "")[:500],
                "Seniority": (j.get("seniority", "") or "")[:50],
                "Domain Match": bool(j.get("domain_match")),
            }

            # JD from enrich step, fallback to SQLite
            jd = j.get("jd_text", "")
            if not jd or len(jd) < 100:
                jd = jd_from_db.get(j.get("url", ""), "")
            if jd and len(jd) > 100:
                row["Full Description"] = jd[:50000]

            # Raw snippet as fallback
            if j.get("raw_snippet") and not row.get("Full Description"):
                row["Raw Snippet"] = j["raw_snippet"][:2000]

            # Date
            posted = j.get("posted") or j.get("first_seen", "")[:10]
            if posted and len(posted) >= 10:
                row["Posted"] = posted[:10]

            # Additional fields from SQLite (identical schema sync)
            extra_map = {
                "country": "Country", "search_country": "Search Country",
                "search_title": "Search Title", "source_method": "Source Method",
                "tags": "Tags", "url_hash": "URL Hash",
            }
            for jk, nk in extra_map.items():
                v = j.get(jk) or ""
                if v:
                    row[nk] = str(v)[:500]

            batch.append(row)

        try:
            resp = requests.post(table_url, json=batch, headers=noco["headers"], timeout=30)
            if resp.status_code == 200:
                created += len(batch)
            else:
                errors += len(batch)
        except Exception:
            errors += len(batch)

    return {"new": created, "dupes": dupes, "errors": errors, "total_merged": len(jobs)}


def update_scored_jobs(noco, dry_run=False):
    """Update NocoDB rows with review scores from SQLite (ALL verdicts, not just SUBMIT/REVIEW)."""
    import sqlite3 as _sql

    db_path = WORKSPACE / "data" / "nasr-pipeline.db"
    if not db_path.exists():
        print("  WARNING: SQLite DB not found, falling back to summary JSON")
        return _update_scored_jobs_legacy(noco, dry_run)

    conn = _sql.connect(str(db_path))
    conn.row_factory = _sql.Row
    cur = conn.cursor()

    # Get ALL scored jobs from SQLite (the single source of truth)
    cur.execute("""
        SELECT id, title, company, job_url, jd_text, ats_score, fit_score,
               verdict, score_notes, status, applied_date,
               recruiter_name, recruiter_email, recruiter_phone, recruiter_company,
               cv_path, cv_html_path, cv_cluster, cv_built_at,
               country, search_country, search_title, days_to_apply,
               jd_path, jd_fetched_at, source_method, next_action,
               tags, applied_via, response_date, url_hash, salary_currency, salary_range,
               created_at
        FROM jobs
        WHERE verdict IS NOT NULL AND verdict != ''
          AND job_url IS NOT NULL AND job_url != ''
    """)
    rows = cur.fetchall()
    conn.close()

    # Build score map by URL
    score_map = {}
    submit_count = 0
    review_count = 0
    for r in rows:
        url = r["job_url"]
        if not url:
            continue

        patch = {
            "Verdict": r["verdict"],
            "ATS Score": r["ats_score"] or 0,
            "Fit Score": r["fit_score"] or 0,
            "AI Reasoning": (r["score_notes"] or "")[:5000],
        }

        # Map pipeline status to NocoDB status
        status = r["status"] or ""
        if status == "applied":
            patch["Status"] = "Applied"
        elif status == "interview":
            patch["Status"] = "Interview"
        elif r["verdict"] == "SUBMIT":
            patch["Status"] = "Interested"
            submit_count += 1
        elif r["verdict"] == "REVIEW":
            patch["Status"] = "Interested"
            review_count += 1

        # Always sync JD text if available
        jd = r["jd_text"] or ""
        if len(jd) > 100:
            patch["Full Description"] = jd[:50000]

        # Applied date
        if r["applied_date"]:
            patch["Applied Date"] = r["applied_date"][:10]

        # Full field sync (identical schema)
        extra_fields = {
            "recruiter_name": "Recruiter Name", "recruiter_email": "Recruiter Email",
            "recruiter_phone": "Recruiter Phone", "recruiter_company": "Recruiter Company",
            "cv_path": "CV Link", "cv_html_path": "CV HTML Path",
            "cv_cluster": "CV Cluster", "cv_built_at": "CV Built At",
            "country": "Country", "search_country": "Search Country",
            "search_title": "Search Title", "days_to_apply": "Days to Apply",
            "jd_path": "JD Path", "jd_fetched_at": "JD Fetched At",
            "source_method": "Source Method", "next_action": "Next Action",
            "tags": "Tags", "applied_via": "Applied Via",
            "url_hash": "URL Hash", "salary_currency": "Salary Currency",
            "salary_range": "Salary",
        }
        for sq_col, noco_col in extra_fields.items():
            val = r[sq_col]
            if val is not None and val != "" and val != 0:
                if isinstance(val, str) and len(val) > 500:
                    val = val[:500]
                patch[noco_col] = val
        if r["response_date"]:
            patch["Response Date"] = r["response_date"][:10]
        if r["created_at"]:
            patch["Discovered Date"] = str(r["created_at"])[:10]

        score_map[url] = patch

    if not score_map:
        return {"updated": 0, "submit": submit_count, "review": review_count, "total_scored": 0}

    print(f"  SQLite has {len(score_map)} scored jobs with URLs")

    if dry_run:
        return {"updated": len(score_map), "submit": submit_count, "review": review_count, "total_scored": len(score_map)}

    # Get NocoDB rows by URL
    table_url = f"{noco['url']}/api/v2/tables/{noco['table_id']}/records"
    url_to_id = {}
    offset = 0
    while True:
        r = requests.get(
            f"{table_url}?fields=Id,URL&limit=200&offset={offset}",
            headers=noco["headers"], timeout=15
        ).json()
        for row in r.get("list", []):
            if row.get("URL"):
                url_to_id[row["URL"]] = row["Id"]
        if len(r.get("list", [])) < 200:
            break
        offset += 200

    # Build update batches
    updates = []
    for url, scores in score_map.items():
        row_id = url_to_id.get(url)
        if row_id:
            patch = {"Id": row_id}
            patch.update(scores)
            updates.append(patch)

    print(f"  Matched {len(updates)}/{len(score_map)} to NocoDB rows")

    updated = 0
    for i in range(0, len(updates), 10):
        batch = updates[i:i + 10]
        try:
            resp = requests.patch(table_url, json=batch, headers=noco["headers"], timeout=30)
            if resp.status_code == 200:
                updated += len(batch)
            else:
                print(f"  Batch update error: {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            print(f"  Batch update exception: {e}")

    return {"updated": updated, "submit": submit_count, "review": review_count, "total_scored": len(score_map)}


def _update_scored_jobs_legacy(noco, dry_run=False):
    """Legacy fallback: update from summary JSON only (SUBMIT/REVIEW)."""
    if not SUMMARY_FILE.exists():
        return {"updated": 0, "submit": 0, "review": 0}

    summary = json.loads(SUMMARY_FILE.read_text())
    submit_jobs = summary.get("data", {}).get("submit", [])
    review_jobs = summary.get("data", {}).get("review", [])

    score_map = {}
    for j in submit_jobs:
        if j.get("url"):
            score_map[j["url"]] = {
                "Verdict": "SUBMIT",
                "ATS Score": j.get("ats_score", 0),
                "Fit Score": j.get("career_fit_score", 0),
                "AI Reasoning": (j.get("verdict_reason", "") or "")[:5000],
                "Status": "Interested",
            }
            if j.get("jd_text") and len(j["jd_text"]) > 100:
                score_map[j["url"]]["Full Description"] = j["jd_text"][:50000]

    for j in review_jobs:
        if j.get("url"):
            score_map[j["url"]] = {
                "Verdict": "REVIEW",
                "ATS Score": j.get("ats_score", 0),
                "Fit Score": j.get("career_fit_score", 0),
                "AI Reasoning": (j.get("verdict_reason", "") or "")[:5000],
            }
            if j.get("jd_text") and len(j["jd_text"]) > 100:
                score_map[j["url"]]["Full Description"] = j["jd_text"][:50000]

    if not score_map:
        return {"updated": 0, "submit": len(submit_jobs), "review": len(review_jobs)}

    if dry_run:
        return {"updated": len(score_map), "submit": len(submit_jobs), "review": len(review_jobs)}

    table_url = f"{noco['url']}/api/v2/tables/{noco['table_id']}/records"
    url_to_id = {}
    offset = 0
    while True:
        r = requests.get(
            f"{table_url}?fields=Id,URL&limit=200&offset={offset}",
            headers=noco["headers"], timeout=15
        ).json()
        for row in r.get("list", []):
            if row.get("URL"):
                url_to_id[row["URL"]] = row["Id"]
        if len(r.get("list", [])) < 200:
            break
        offset += 200

    updates = []
    for url, scores in score_map.items():
        row_id = url_to_id.get(url)
        if row_id:
            patch = {"Id": row_id}
            patch.update(scores)
            updates.append(patch)

    updated = 0
    for i in range(0, len(updates), 10):
        batch = updates[i:i + 10]
        try:
            resp = requests.patch(table_url, json=batch, headers=noco["headers"], timeout=30)
            if resp.status_code == 200:
                updated += len(batch)
        except Exception:
            pass

    return {"updated": updated, "submit": len(submit_jobs), "review": len(review_jobs)}


def format_push_summary(push_stats, score_stats):
    """Format NocoDB push summary for Telegram."""
    lines = ["📋 NocoDB Pipeline Update\n"]

    # Push stats
    lines.append(f"🆕 New jobs added: {push_stats['new']}")
    lines.append(f"🔄 Already existed: {push_stats['dupes']}")
    if push_stats["errors"]:
        lines.append(f"❌ Errors: {push_stats['errors']}")
    lines.append(f"📊 Total merged: {push_stats['total_merged']}")

    # Score stats
    if score_stats["submit"] or score_stats["review"]:
        lines.append(f"\n🎯 AI Review: {score_stats['submit']} SUBMIT / {score_stats['review']} REVIEW")
        lines.append(f"✅ Scores synced: {score_stats['updated']}")

    return "\n".join(lines)


def format_top_jobs():
    """Format top SUBMIT jobs for Telegram alert."""
    if not SUMMARY_FILE.exists():
        return None

    summary = json.loads(SUMMARY_FILE.read_text())
    submit_jobs = summary.get("data", {}).get("submit", [])

    if not submit_jobs:
        return None

    # Sort by ATS desc
    submit_jobs.sort(key=lambda j: j.get("ats_score", 0), reverse=True)

    lines = [f"🎯 Top {min(len(submit_jobs), 10)} SUBMIT Jobs\n"]
    for i, j in enumerate(submit_jobs[:10], 1):
        fit = j.get("career_fit_score", 0)
        ats = j.get("ats_score", 0)
        title = j.get("title", "?")[:50]
        company = j.get("company", "?")[:30]
        location = j.get("location", "")[:20]
        url = j.get("url", "")

        lines.append(f"#{i} [Fit:{fit} ATS:{ats}] {title}")
        lines.append(f"   {company} ({location})")
        if url:
            lines.append(f"   {url}")
        lines.append("")

    lines.append(f"📊 View all: http://100.99.230.14:8080 - Kanban Pipeline view")

    return "\n".join(lines)


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN MODE - no writes")

    print("=" * 60)
    print(f"push-to-nocodb.py — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Phase 1: Source status alert
    print("\n--- Phase 1: Source Status ---")
    source_msg = format_source_status()
    if source_msg:
        print(source_msg)
        if not dry_run:
            send_telegram(source_msg, topic=TG_TOPIC_HR)
    else:
        print("  No phase status file found, skipping source alert")

    # Phase 2: NocoDB auth
    print("\n--- Phase 2: NocoDB Push ---")
    try:
        noco = load_nocodb_auth()
        print(f"  NocoDB connected: {noco['url']}")
    except Exception as e:
        print(f"  ERROR: NocoDB auth failed: {e}")
        if not dry_run:
            send_telegram(f"❌ NocoDB Push FAILED: Auth error - {e}", topic=TG_TOPIC_CEO)
        sys.exit(1)

    # Phase 3: Push new jobs
    push_stats = push_new_jobs(noco, dry_run=dry_run)
    print(f"  New: {push_stats['new']}, Dupes: {push_stats['dupes']}, Errors: {push_stats['errors']}")

    # Phase 4: Update scored jobs
    print("\n--- Phase 3: Score Sync ---")
    score_stats = update_scored_jobs(noco, dry_run=dry_run)
    print(f"  Updated: {score_stats['updated']}, SUBMIT: {score_stats['submit']}, REVIEW: {score_stats['review']}")

    # Phase 5: Send summary to Telegram
    print("\n--- Phase 4: Telegram Alerts ---")
    push_msg = format_push_summary(push_stats, score_stats)
    print(push_msg)
    if not dry_run:
        send_telegram(push_msg, topic=TG_TOPIC_HR)

    # Phase 6: Top jobs alert
    top_msg = format_top_jobs()
    if top_msg:
        print(top_msg)
        if not dry_run:
            send_telegram(top_msg, topic=TG_TOPIC_HR)

    print("\n✅ Done")


if __name__ == "__main__":
    main()
