#!/usr/bin/env python3
"""
migrate_to_db.py — One-time migration of all existing pipeline data into nasr-pipeline.db.

Data sources (in priority order):
1. jobs-bank/applied-job-ids.txt  — Applied jobs with company/role/date
2. coordination/pipeline.json     — 6 detailed application records
3. data/jobs-merged.json          — Current discovered/scored jobs
4. data/jobs-summary.json         — LLM scores and verdicts
5. data/jd-cache/*.json           — Full JD texts
6. cvs/*.pdf                      — CV files (parse filename → company + role)

Idempotent: safe to run multiple times. Uses INSERT OR IGNORE + UPSERT logic.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
sys.path.insert(0, str(WORKSPACE / "scripts"))

import pipeline_db as pdb

CAIRO = timezone(timedelta(hours=2))


def now_cairo():
    return datetime.now(CAIRO).isoformat()


def log(msg):
    print(f"[migrate] {msg}")


# ──────────────────────────────────────────────────────────────────────────────
# Source 1: applied-job-ids.txt
# ──────────────────────────────────────────────────────────────────────────────

def parse_applied_job_line(line: str) -> dict | None:
    """
    Parse a line from applied-job-ids.txt.
    Formats seen:
      4366706927 | byteSpark.ai | Director Investment Platforms | 2026-03-16
      4386334469                                           (ID only)
      025f90f1df941203 | FMC Network | CTO | 2026-03-21 | Applied
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    parts = [p.strip() for p in line.split("|")]
    if not parts:
        return None

    job_id = parts[0].strip()
    if not job_id or len(job_id) < 5:
        return None

    # Determine source from job_id format
    if job_id.startswith("li-") or job_id.startswith("linkedin-li-") or job_id.startswith("ae.linkedin-"):
        source = "linkedin"
        # Normalize: extract numeric suffix
        numeric = job_id.split("-")[-1]
        if numeric.isdigit():
            job_id = numeric
    elif job_id.startswith("indeed-in-") or job_id.startswith("ae.indeed-"):
        source = "indeed"
        job_id = job_id.split("-")[-1]
    elif len(job_id) == 16 and all(c in "0123456789abcdef" for c in job_id):
        source = "indeed"  # hex indeed IDs
    elif job_id.isdigit() and len(job_id) >= 8:
        source = "linkedin"  # LinkedIn numeric IDs
    else:
        source = "manual"

    company = parts[1] if len(parts) > 1 else "Unknown"
    title = parts[2] if len(parts) > 2 else "Unknown Role"
    date_str = parts[3] if len(parts) > 3 else ""
    notes_str = parts[4] if len(parts) > 4 else ""

    # Parse date
    applied_date = None
    if date_str:
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
        if date_match:
            applied_date = date_match.group(1)

    # Determine status
    status = "applied"
    if "SKIPPED" in notes_str.upper() or "SKIPPED" in date_str.upper():
        status = "withdrawn"
    elif "Previously Applied" in notes_str:
        status = "applied"
    elif "synced from Notion" in date_str:
        status = "applied"

    # Clean up company/title
    if company in ("Notion sync", ""):
        company = "Unknown"
    if title in ("Applied", ""):
        title = "Unknown Role"

    return {
        "job_id": job_id,
        "source": source,
        "company": company,
        "title": title,
        "applied_date": applied_date,
        "status": status,
        "notes": notes_str if notes_str and notes_str not in ("Applied", "Previously Applied") else None,
    }


def migrate_applied_ids() -> dict:
    """Import from applied-job-ids.txt."""
    filepath = WORKSPACE / "jobs-bank" / "applied-job-ids.txt"
    if not filepath.exists():
        log("⚠️  applied-job-ids.txt not found, skipping")
        return {"imported": 0, "skipped": 0}

    imported = 0
    skipped = 0
    errors = 0

    with open(filepath) as f:
        for line in f:
            record = parse_applied_job_line(line)
            if not record:
                continue

            try:
                job_id = pdb.register_job(
                    source=record["source"],
                    job_id=record["job_id"],
                    company=record["company"],
                    title=record["title"],
                    status=record["status"],
                    notes=record.get("notes"),
                )
                if record["applied_date"]:
                    pdb.mark_applied(job_id, applied_date=record["applied_date"])
                imported += 1
            except Exception as e:
                errors += 1
                log(f"  Error importing {record.get('job_id')}: {e}")

    log(f"applied-job-ids.txt: {imported} imported, {skipped} skipped, {errors} errors")
    return {"imported": imported, "skipped": skipped, "errors": errors}


# ──────────────────────────────────────────────────────────────────────────────
# Source 2: coordination/pipeline.json
# ──────────────────────────────────────────────────────────────────────────────

def migrate_pipeline_json() -> dict:
    """Import from coordination/pipeline.json (6 detailed records)."""
    filepath = WORKSPACE / "coordination" / "pipeline.json"
    if not filepath.exists():
        log("⚠️  coordination/pipeline.json not found, skipping")
        return {"imported": 0}

    imported = 0
    errors = 0

    try:
        data = json.load(open(filepath))
    except Exception as e:
        log(f"  Error loading pipeline.json: {e}")
        return {"imported": 0, "errors": 1}

    # Handle various formats
    applications = []
    if isinstance(data, list):
        applications = data
    elif isinstance(data, dict):
        # Handle nested applications dict: {"applications": {"active": [...], "rejected": [...]}}
        if "applications" in data and isinstance(data["applications"], dict):
            for sub_key, sub_val in data["applications"].items():
                if isinstance(sub_val, list):
                    applications.extend(sub_val)
        else:
            for key, val in data.items():
                if key in ("last_updated", "generated_by", "this_week_progress", "conversion_rates"):
                    continue
                if isinstance(val, list):
                    applications.extend(val)
                elif isinstance(val, dict) and "company" in val:
                    applications.append(val)

    for app in applications:
        if not isinstance(app, dict):
            continue

        company = app.get("company", "Unknown")
        title = app.get("title", app.get("role", "Unknown Role"))
        status_raw = app.get("status", "applied")
        date_applied = app.get("date_applied", app.get("applied_date", app.get("date_rejected", "")))

        # Map status
        status_map = {
            "applied": "applied",
            "interview": "interview",
            "screening": "screening",
            "offer": "offer",
            "rejected": "rejected",
            "withdrawn": "withdrawn",
        }
        status = status_map.get(status_raw.lower() if status_raw else "", "applied")

        # Generate job_id
        import hashlib
        job_id_raw = app.get("id", f"pipeline-{hashlib.md5(f'{company}|{title}'.encode()).hexdigest()[:8]}")

        try:
            jid = pdb.register_job(
                source="manual",
                job_id=str(job_id_raw),
                company=company,
                title=title,
                location=app.get("location"),
                url=app.get("url"),
                status=status,
                notes=app.get("notes"),
                follow_up_date=app.get("follow_up_date"),
            )
            if date_applied:
                pdb.mark_applied(jid, applied_date=date_applied[:10] if date_applied else None)
            imported += 1
        except Exception as e:
            errors += 1
            log(f"  Error importing pipeline record {company}: {e}")

    log(f"coordination/pipeline.json: {imported} imported, {errors} errors")
    return {"imported": imported, "errors": errors}


# ──────────────────────────────────────────────────────────────────────────────
# Source 3: data/jobs-merged.json
# ──────────────────────────────────────────────────────────────────────────────

def migrate_jobs_merged() -> dict:
    """Import from data/jobs-merged.json (current discovered jobs)."""
    filepath = WORKSPACE / "data" / "jobs-merged.json"
    if not filepath.exists():
        log("⚠️  data/jobs-merged.json not found, skipping")
        return {"imported": 0}

    try:
        raw = json.load(open(filepath))
    except Exception as e:
        log(f"  Error loading jobs-merged.json: {e}")
        return {"imported": 0, "errors": 1}

    # Extract jobs list
    if isinstance(raw, list):
        jobs = raw
    elif isinstance(raw, dict):
        jobs = raw.get("data", raw.get("jobs", []))
        if isinstance(jobs, dict):
            jobs = list(jobs.values())

    imported = 0
    errors = 0

    for job in jobs:
        if not isinstance(job, dict):
            continue

        job_id = str(job.get("id", job.get("job_id", ""))).strip()
        source = job.get("source", "unknown")
        company = job.get("company", "Unknown")
        title = job.get("title", "Unknown Role")
        location = job.get("location", "")
        url = job.get("url", job.get("job_url", ""))
        jd_text = job.get("jd_text", job.get("raw_snippet", ""))
        posted = job.get("posted", "")

        if not job_id:
            import hashlib
            job_id = f"merged-{hashlib.md5(f'{company}|{title}|{url}'.encode()).hexdigest()[:10]}"

        try:
            pdb.register_job(
                source=source,
                job_id=job_id,
                company=company,
                title=title,
                location=location,
                url=url,
                jd_text=jd_text if jd_text else None,
                status="discovered",
            )
            imported += 1
        except Exception as e:
            errors += 1

    log(f"data/jobs-merged.json: {imported} imported, {errors} errors")
    return {"imported": imported, "errors": errors}


# ──────────────────────────────────────────────────────────────────────────────
# Source 4: data/jobs-summary.json (scores + verdicts)
# ──────────────────────────────────────────────────────────────────────────────

def migrate_jobs_summary() -> dict:
    """Import scores and verdicts from data/jobs-summary.json."""
    filepath = WORKSPACE / "data" / "jobs-summary.json"
    if not filepath.exists():
        log("⚠️  data/jobs-summary.json not found, skipping")
        return {"updated": 0}

    try:
        raw = json.load(open(filepath))
    except Exception as e:
        log(f"  Error loading jobs-summary.json: {e}")
        return {"updated": 0, "errors": 1}

    # Extract job lists from summary structure
    all_jobs = []
    if isinstance(raw, list):
        all_jobs = raw
    elif isinstance(raw, dict):
        data = raw.get("data", raw)
        if isinstance(data, dict):
            for key in ("submit", "review", "skip", "jobs", "results"):
                if key in data and isinstance(data[key], list):
                    for j in data[key]:
                        if isinstance(j, dict):
                            # Tag with verdict from the key
                            if key in ("submit", "review", "skip") and "verdict" not in j:
                                j["verdict"] = key.upper()
                            all_jobs.append(j)
        elif isinstance(data, list):
            all_jobs = data

    updated = 0
    errors = 0

    for job in all_jobs:
        if not isinstance(job, dict):
            continue

        job_id = str(job.get("id", job.get("job_id", ""))).strip()
        if not job_id:
            continue

        ats_score = job.get("ats_score")
        fit_score = job.get("fit_score", job.get("score"))
        verdict = job.get("verdict")
        notes = job.get("reason", job.get("score_notes", job.get("notes", "")))

        # Also try to register the job if not already in DB
        company = job.get("company", "Unknown")
        title = job.get("title", "Unknown Role")
        if company and title:
            pdb.register_job(
                source=job.get("source", "unknown"),
                job_id=job_id,
                company=company,
                title=title,
                location=job.get("location"),
                url=job.get("url", job.get("job_url")),
                jd_text=job.get("jd_text"),
                status="scored" if verdict else "discovered",
            )

        try:
            pdb.update_score(
                job_id=job_id,
                ats_score=int(ats_score) if ats_score is not None else None,
                fit_score=int(fit_score) if fit_score is not None else None,
                verdict=verdict,
                notes=str(notes) if notes else None,
            )
            updated += 1
        except Exception as e:
            errors += 1

    log(f"data/jobs-summary.json: {updated} scores updated, {errors} errors")
    return {"updated": updated, "errors": errors}


# ──────────────────────────────────────────────────────────────────────────────
# Source 5: data/jd-cache/*.json
# ──────────────────────────────────────────────────────────────────────────────

def migrate_jd_cache() -> dict:
    """Link JD cache files to job records."""
    jd_dir = WORKSPACE / "data" / "jd-cache"
    if not jd_dir.exists():
        log("⚠️  data/jd-cache/ not found, skipping")
        return {"linked": 0}

    linked = 0
    new_jobs = 0
    errors = 0

    for f in sorted(jd_dir.glob("*.json")):
        job_id = f.stem  # filename = job_id

        try:
            data = json.load(open(f))
        except Exception:
            errors += 1
            continue

        jd_text = data.get("jd_text", data.get("text", data.get("description", "")))
        fetched_at = data.get("fetched_at", data.get("cached_at", ""))

        if not jd_text:
            continue

        # Check if job exists; if not, try to create minimal record
        existing = pdb.get_job(job_id)
        if not existing:
            # Try to extract info from JD data
            company = data.get("company", "Unknown")
            title = data.get("title", data.get("job_title", "Unknown Role"))
            pdb.register_job(
                source="linkedin",  # Most JD IDs are LinkedIn
                job_id=job_id,
                company=company,
                title=title,
                jd_text=jd_text,
                jd_path=str(f),
                jd_fetched_at=fetched_at,
            )
            new_jobs += 1
        else:
            pdb.update_field(
                job_id,
                jd_text=jd_text,
                jd_path=str(f),
                jd_fetched_at=fetched_at if fetched_at else None,
            )

        # Index keywords from JD
        try:
            pdb.index_keywords_from_jd(job_id, jd_text)
        except Exception:
            pass

        linked += 1

    log(f"data/jd-cache: {linked} JDs linked, {new_jobs} new jobs created from JD data, {errors} errors")
    return {"linked": linked, "new_jobs": new_jobs, "errors": errors}


# ──────────────────────────────────────────────────────────────────────────────
# Source 6: cvs/*.pdf
# ──────────────────────────────────────────────────────────────────────────────

def parse_cv_filename(filename: str) -> dict | None:
    """
    Parse CV filename to extract company and role.
    Pattern: "Ahmed Nasr - {Role Title} - {Company}.pdf"
    Example: "Ahmed Nasr - CTO Smart Metering - Talan.pdf"
    """
    name = filename.replace(".pdf", "").replace(".html", "").strip()

    # Remove "Ahmed Nasr - " prefix
    if name.startswith("Ahmed Nasr - "):
        name = name[len("Ahmed Nasr - "):]
    elif name.startswith("Ahmed Nasr"):
        name = name[len("Ahmed Nasr"):].lstrip(" -")

    # Split by " - " to get role and company
    parts = name.split(" - ")
    if len(parts) >= 2:
        role = parts[0].strip()
        company = parts[-1].strip()
        return {"title": role, "company": company}
    elif len(parts) == 1:
        return {"title": parts[0].strip(), "company": "Unknown"}

    return None


def migrate_cvs() -> dict:
    """Import CV files from cvs/ directory."""
    cvs_dir = WORKSPACE / "cvs"
    if not cvs_dir.exists():
        log("⚠️  cvs/ directory not found, skipping")
        return {"imported": 0}

    imported = 0
    linked = 0
    errors = 0
    skipped = 0

    from difflib import SequenceMatcher

    def fuzzy_match(a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    # Get all PDF files
    pdf_files = sorted(cvs_dir.glob("*.pdf"))
    html_files = {f.stem: f for f in cvs_dir.glob("*.html")}

    for pdf in pdf_files:
        parsed = parse_cv_filename(pdf.name)
        if not parsed:
            skipped += 1
            continue

        company = parsed["company"]
        title = parsed["title"]

        # Get file modification time as proxy for CV build date
        mtime = datetime.fromtimestamp(pdf.stat().st_mtime, tz=CAIRO)
        cv_built_at = mtime.isoformat()

        # Try to find matching job in DB by company + title fuzzy match
        existing_jobs = pdb.get_by_company(company)
        best_match = None
        best_score = 0.0

        for job in existing_jobs:
            title_sim = fuzzy_match(title, job.get("title", ""))
            company_sim = fuzzy_match(company, job.get("company", ""))
            combined = (title_sim * 0.6) + (company_sim * 0.4)
            if combined > best_score:
                best_score = combined
                best_match = job

        html_path = str(html_files.get(pdf.stem, "")) or None

        if best_match and best_score >= 0.6:
            # Link CV to existing job
            pdb.attach_cv(
                job_id=best_match["job_id"],
                cv_path=str(pdf),
                cv_html_path=html_path,
            )
            linked += 1
        else:
            # Create new job record from CV
            import hashlib
            job_id = f"cv-{hashlib.md5(f'{company}|{title}'.encode()).hexdigest()[:10]}"
            pdb.register_job(
                source="manual",
                job_id=job_id,
                company=company,
                title=title,
                status="cv_built",
                cv_path=str(pdf),
                cv_html_path=html_path,
                cv_built_at=cv_built_at,
            )
            imported += 1

    log(f"cvs/: {imported} new jobs from CVs, {linked} CVs linked to existing jobs, {skipped} skipped, {errors} errors")
    return {"imported": imported, "linked": linked, "skipped": skipped, "errors": errors}


# ──────────────────────────────────────────────────────────────────────────────
# Cross-reference: match applied IDs with discovered jobs
# ──────────────────────────────────────────────────────────────────────────────

def cross_reference() -> dict:
    """
    Try to match orphaned records by company name similarity.
    Applied records without CV → try to link CV.
    Discovered jobs that have been applied → update status.
    """
    # Find all jobs with status=applied that have no CV
    applied = pdb.search(status="applied")
    discovered = pdb.search(status="discovered")
    cv_built = pdb.search(status="cv_built")

    matched = 0

    from difflib import SequenceMatcher
    def sim(a, b):
        return SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()

    # For each applied job, see if there's a cv_built job with same company/title
    for app_job in applied:
        for cv_job in cv_built:
            company_sim = sim(app_job.get("company", ""), cv_job.get("company", ""))
            title_sim = sim(app_job.get("title", ""), cv_job.get("title", ""))
            score = company_sim * 0.5 + title_sim * 0.5

            if score >= 0.7 and cv_job.get("cv_path"):
                # Link CV to applied job
                pdb.update_field(
                    app_job["job_id"],
                    cv_path=cv_job.get("cv_path"),
                    cv_html_path=cv_job.get("cv_html_path"),
                )
                matched += 1
                break

    log(f"Cross-reference: {matched} CVs linked to applied jobs")
    return {"matched": matched}


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("NASR Pipeline DB Migration")
    print("=" * 60)
    print(f"DB path: {pdb.DB_PATH}")
    print()

    stats = {}

    print("── Source 1: applied-job-ids.txt ──")
    stats["applied_ids"] = migrate_applied_ids()

    print("\n── Source 2: coordination/pipeline.json ──")
    stats["pipeline_json"] = migrate_pipeline_json()

    print("\n── Source 3: data/jobs-merged.json ──")
    stats["jobs_merged"] = migrate_jobs_merged()

    print("\n── Source 4: data/jobs-summary.json ──")
    stats["jobs_summary"] = migrate_jobs_summary()

    print("\n── Source 5: data/jd-cache/*.json ──")
    stats["jd_cache"] = migrate_jd_cache()

    print("\n── Source 6: cvs/*.pdf ──")
    stats["cvs"] = migrate_cvs()

    print("\n── Cross-reference ──")
    stats["cross_ref"] = cross_reference()

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)

    # Summary
    db_stats = pdb.get_db_stats()
    funnel = pdb.get_funnel()

    print(f"\nDB Stats:")
    print(f"  Total jobs:         {db_stats.get('jobs_count', 0)}")
    print(f"  Total interactions: {db_stats.get('interactions_count', 0)}")
    print(f"  Keywords indexed:   {db_stats.get('keywords_count', 0)}")
    print(f"  DB size:            {db_stats.get('db_size_kb', 0)} KB")

    print(f"\nFunnel:")
    for status, count in sorted(funnel.items(), key=lambda x: -x[1]):
        if status != "_total":
            print(f"  {status:<20} {count:>5}")
    print(f"  {'TOTAL':<20} {funnel.get('_total', 0):>5}")

    print(f"\nSource breakdown:")
    for source, s in stats.items():
        print(f"  {source}: {s}")

    return stats


if __name__ == "__main__":
    main()
