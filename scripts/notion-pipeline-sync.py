#!/usr/bin/env python3
"""
Notion Pipeline Sync
====================
One-way sync: SQLite (source of truth) → Notion Job Pipeline DB.
Syncs active jobs (applied, response, interview, offer) + recent discoveries.

Usage:
    python3 notion-pipeline-sync.py                # Full sync
    python3 notion-pipeline-sync.py --active-only  # Only applied/response/interview
    python3 notion-pipeline-sync.py --dry-run      # Preview without writing

Cron: 1 AM Cairo daily
"""

import json, os, sys, sqlite3, hashlib, time
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from notion_client_shared import get_client, notion_req as _shared_notion_req
    _notion_client = get_client()
    _USE_SHARED = True
except Exception:
    _USE_SHARED = False
    _notion_client = None

WORKSPACE = "/root/.openclaw/workspace"
DB_PATH = f"{WORKSPACE}/data/nasr-pipeline.db"
NOTION_CONFIG = f"{WORKSPACE}/config/notion.json"
NOTION_DB_ID = "3268d599-a162-81b4-b768-f162adfa4971"
CAIRO = timezone(timedelta(hours=2))

# Stage mapping: SQLite status → Notion Stage select
STATUS_TO_STAGE = {
    "discovered": "Discovered",
    "scored": "Scored",
    "cv_built": "CV Built",
    "applied": "Applied",
    "response": "Response",
    "interview": "Interview",
    "offer": "Offer",
    "rejected": "Rejected",
    "withdrawn": "Withdrawn",
}

# Verdict mapping
VERDICT_MAP = {
    "SUBMIT": "Submit",
    "REVIEW": "Review",
    "SKIP": "Skip",
}

# Source mapping
SOURCE_MAP = {
    "linkedin": "LinkedIn",
    "linkedin-manual": "LinkedIn",
    "indeed": "Indeed",
    "google-jobs": "Google Jobs",
    "recruiter-inbound": "Recruiter Inbound",
    "referral": "Referral",
}


def load_notion_config():
    with open(NOTION_CONFIG) as f:
        return json.load(f)


def notion_request(method, endpoint, body=None, cfg=None):
    """Make a Notion API request using shared client with retry/backoff.
    Falls back to direct urllib if shared client unavailable.
    """
    if _USE_SHARED and _notion_client:
        # Map method names: this function uses HTTP methods like "POST", "PATCH"
        data, err = _shared_notion_req(_notion_client, method.lower(), endpoint.lstrip("/"), body)
        if err:
            log(f"  Notion API error: {err}")
            return None
        return data

    # Fallback: direct urllib (legacy path)
    import urllib.request, urllib.error
    if cfg is None:
        cfg = load_notion_config()

    headers = {
        "Authorization": f"Bearer {cfg['token']}",
        "Notion-Version": cfg["version"],
        "Content-Type": "application/json",
    }

    url = f"https://api.notion.com/v1{endpoint}"
    data_bytes = json.dumps(body).encode() if body else None

    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry = int(e.headers.get("Retry-After", "2"))
                log(f"  Rate limited, waiting {retry}s...")
                time.sleep(retry)
                continue
            elif e.code == 409:
                log(f"  Conflict (409), retrying...")
                time.sleep(1)
                continue
            else:
                body_text = e.read().decode() if hasattr(e, 'read') else ""
                log(f"  Notion API error {e.code}: {body_text[:200]}")
                raise
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
                continue
            raise
    return None


def log(msg):
    now = datetime.now(CAIRO).strftime("%H:%M:%S")
    print(f"[{now}] {msg}")


def get_existing_notion_pages(cfg):
    """Fetch all existing pages in the Notion Pipeline DB, keyed by Company+Role.
    Returns dict: key -> {id, last_edited_time, stage}
    """
    pages = {}
    has_more = True
    start_cursor = None
    
    while has_more:
        body = {"page_size": 100}
        if start_cursor:
            body["start_cursor"] = start_cursor
        
        result = notion_request("POST", f"/databases/{NOTION_DB_ID}/query", body, cfg)
        if not result:
            break
        
        for page in result.get("results", []):
            props = page.get("properties", {})
            
            # Extract company (title)
            company_parts = props.get("Company", {}).get("title", [])
            company = company_parts[0].get("plain_text", "") if company_parts else ""
            
            # Extract role
            role_parts = props.get("Role", {}).get("rich_text", [])
            role = role_parts[0].get("plain_text", "") if role_parts else ""
            
            # Extract stage for reverse sync
            stage_data = props.get("Stage", {}).get("select")
            stage = stage_data["name"] if stage_data else None

            key = f"{company.lower().strip()}|{role.lower().strip()}"
            pages[key] = {
                "id": page["id"],
                "last_edited_time": page.get("last_edited_time", ""),
                "stage": stage,
            }
        
        has_more = result.get("has_more", False)
        start_cursor = result.get("next_cursor")
    
    return pages


# Reverse mapping: Notion Stage → SQLite status
STAGE_TO_STATUS = {v.lower(): k for k, v in STATUS_TO_STAGE.items()}
# Add emoji-prefixed variants
STAGE_TO_STATUS.update({
    "✅ applied": "applied",
    "📄 cv ready": "cv_built",
    "📄 cv built": "cv_built",
    "🎤 interview": "interview",
    "💰 offer": "offer",
    "❌ rejected": "rejected",
    "🔍 discovered": "discovered",
    "📊 scored": "scored",
    "📩 response": "response",
    "🚫 withdrawn": "withdrawn",
})


def build_notion_properties(job):
    """Build Notion page properties from a SQLite job row."""
    props = {}
    
    # Company (title - required)
    company = job.get("company") or "Unknown"
    props["Company"] = {"title": [{"text": {"content": company[:100]}}]}
    
    # Role
    title = job.get("title") or ""
    if title:
        props["Role"] = {"rich_text": [{"text": {"content": title[:200]}}]}
    
    # Location
    location = job.get("location") or ""
    if location:
        props["Location"] = {"rich_text": [{"text": {"content": location[:100]}}]}
    
    # Stage (select)
    status = job.get("status") or "discovered"
    stage = STATUS_TO_STAGE.get(status, "Discovered")
    props["Stage"] = {"select": {"name": stage}}
    
    # ATS Score
    ats = job.get("ats_score")
    if ats and str(ats).isdigit():
        props["ATS Score"] = {"number": int(ats)}
    
    # URL
    job_url = job.get("job_url") or ""
    if job_url and job_url.startswith("http"):
        props["URL"] = {"url": job_url}
    
    # Source
    source = job.get("source") or ""
    source_label = SOURCE_MAP.get(source, source[:20] if source else "")
    if source_label:
        props["Source"] = {"select": {"name": source_label}}
    
    # Verdict
    verdict = job.get("verdict") or ""
    verdict_label = VERDICT_MAP.get(verdict, "")
    if verdict_label:
        props["Verdict"] = {"select": {"name": verdict_label}}
    
    # Applied Date
    applied_date = job.get("applied_date") or ""
    if applied_date:
        try:
            # Ensure proper format
            if len(applied_date) == 10:
                props["Applied Date"] = {"date": {"start": applied_date}}
        except:
            pass
    
    # CV Link (GitHub URL)
    cv_path = job.get("cv_path") or ""
    if cv_path:
        filename = os.path.basename(cv_path).replace(" ", "%20")
        github_url = f"https://github.com/ahmednasr999/openclaw-workspace/blob/master/cvs/{filename}"
        props["CV Link"] = {"url": github_url}
    
    # Discovered Date (from created_at)
    created_at = job.get("created_at") or ""
    if created_at:
        try:
            # Parse ISO format and extract date
            date_str = created_at[:10]
            if len(date_str) == 10 and date_str[4] == '-':
                props["Discovered Date"] = {"date": {"start": date_str}}
        except:
            pass
    
    # CV Date (from cv_built_at)
    cv_built = job.get("cv_built_at") or ""
    if cv_built:
        try:
            date_str = cv_built[:10]
            if len(date_str) == 10 and date_str[4] == '-':
                props["CV Date"] = {"date": {"start": date_str}}
        except:
            pass
    
    # Follow-up Due
    follow_up = job.get("follow_up_date") or ""
    if follow_up:
        try:
            date_str = follow_up[:10]
            if len(date_str) == 10 and date_str[4] == '-':
                props["Follow-up Due"] = {"date": {"start": date_str}}
        except:
            pass
    
    # Salary
    salary = job.get("salary_range") or ""
    if salary:
        currency = job.get("salary_currency") or ""
        salary_text = f"{currency} {salary}".strip() if currency else salary
        props["Salary"] = {"rich_text": [{"text": {"content": salary_text[:100]}}]}
    
    # Notes (combine recruiter info, cluster, score notes, and manual notes)
    notes = job.get("notes") or ""
    recruiter = job.get("recruiter_name") or ""
    recruiter_email = job.get("recruiter_email") or ""
    recruiter_phone = job.get("recruiter_phone") or ""
    cluster = job.get("cv_cluster") or ""
    score_notes = job.get("score_notes") or ""
    next_action = job.get("next_action") or ""
    
    note_parts = []
    if recruiter:
        contact = f"Recruiter: {recruiter}"
        if recruiter_email:
            contact += f" ({recruiter_email})"
        if recruiter_phone:
            contact += f" | {recruiter_phone}"
        note_parts.append(contact)
    if cluster:
        note_parts.append(f"Cluster: {cluster}")
    if next_action:
        note_parts.append(f"Next: {next_action}")
    if score_notes:
        note_parts.append(f"Score: {score_notes[:200]}")
    if notes:
        note_parts.append(notes[:500])
    
    if note_parts:
        full_notes = " | ".join(note_parts)[:2000]
        props["Notes"] = {"rich_text": [{"text": {"content": full_notes}}]}
    
    return props


def sync_jobs(active_only=False, dry_run=False):
    """Main sync: SQLite → Notion."""
    cfg = load_notion_config()
    
    log("Loading existing Notion pages...")
    existing = get_existing_notion_pages(cfg)
    log(f"Found {len(existing)} existing pages in Notion")
    
    # Query SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    if active_only:
        query = """
            SELECT * FROM jobs 
            WHERE status IN ('applied', 'response', 'interview', 'offer', 'cv_built')
            ORDER BY created_at DESC
        """
    else:
        # Sync active + recent discoveries (last 7 days) + anything with recruiter contact
        query = """
            SELECT * FROM jobs 
            WHERE status IN ('applied', 'response', 'interview', 'offer', 'cv_built')
               OR (status = 'discovered' AND verdict = 'SUBMIT')
               OR recruiter_name IS NOT NULL
               OR recruiter_email IS NOT NULL
            ORDER BY 
                CASE status 
                    WHEN 'interview' THEN 1
                    WHEN 'offer' THEN 2
                    WHEN 'response' THEN 3
                    WHEN 'applied' THEN 4
                    WHEN 'cv_built' THEN 5
                    ELSE 6
                END,
                created_at DESC
            LIMIT 200
        """
    
    jobs = conn.execute(query).fetchall()
    conn.close()
    
    log(f"Syncing {len(jobs)} jobs to Notion...")
    
    created = 0
    updated = 0
    skipped = 0
    errors = 0
    
    for i, job in enumerate(jobs):
        company = (job["company"] or "Unknown").strip()
        title = (job["title"] or "").strip()
        
        # Skip unknown/empty records
        if company == "Unknown" and (not title or title == "Unknown Role"):
            skipped += 1
            continue
        
        key = f"{company.lower()}|{title.lower()}"
        
        props = build_notion_properties(dict(job))
        
        if dry_run:
            status = "UPDATE" if key in existing else "CREATE"
            log(f"  [{status}] {company} | {title} | {job['status']}")
            if status == "CREATE":
                created += 1
            else:
                updated += 1
            continue
        
        try:
            if key in existing:
                page_info = existing[key]
                page_id = page_info["id"]
                notion_last_edit = page_info.get("last_edited_time", "")
                notion_stage = page_info.get("stage", "")

                # D4: Bidirectional sync — Status/Stage: Notion always wins
                if notion_stage:
                    notion_status = STAGE_TO_STATUS.get(notion_stage.lower(), None)
                    sqlite_status = job["status"]
                    if notion_status and notion_status != sqlite_status:
                        # Notion has a different stage — reverse sync to SQLite
                        log(f"  ↩️ Reverse sync: {company} | {title} — Notion '{notion_stage}' → SQLite '{notion_status}' (was '{sqlite_status}')")
                        try:
                            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                            import pipeline_db as _pdb
                            _pdb.update_status(job["job_id"], notion_status, source="notion_sync")
                        except Exception as rsync_err:
                            log(f"  ⚠️ Reverse sync failed: {rsync_err}")
                        # Don't overwrite Notion's stage in this push
                        props.pop("Stage", None)

                notion_request("PATCH", f"/pages/{page_id}", {"properties": props}, cfg)
                updated += 1
            else:
                # Create new page
                notion_request("POST", "/pages", {
                    "parent": {"database_id": NOTION_DB_ID},
                    "properties": props,
                }, cfg)
                created += 1
            
            # Rate limit: 3 req/s max, stay at 2/s to be safe
            if (i + 1) % 2 == 0:
                time.sleep(0.5)
            
            if (i + 1) % 25 == 0:
                log(f"  Progress: {i+1}/{len(jobs)} (created={created}, updated={updated})")
                
        except Exception as e:
            log(f"  ERROR on {company} | {title}: {e}")
            errors += 1
            if errors > 10:
                log("Too many errors, stopping.")
                break
    
    log(f"Sync complete: {created} created, {updated} updated, {skipped} skipped, {errors} errors")
    
    return {"created": created, "updated": updated, "skipped": skipped, "errors": errors}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Sync SQLite pipeline to Notion")
    parser.add_argument("--active-only", action="store_true", help="Only sync active jobs")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()
    
    log("Notion Pipeline Sync starting...")
    result = sync_jobs(active_only=args.active_only, dry_run=args.dry_run)
    log(f"Result: {json.dumps(result)}")


if __name__ == "__main__":
    main()
