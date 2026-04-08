#!/usr/bin/env python3
"""
Add a job to the Notion Pipeline DB and applied-job-ids.txt.
Call after CV is tailored and ready to apply.

Usage:
    python3 scripts/add-to-pipeline.py \
        --company "Valtech Group" \
        --role "Experience Operations Director" \
        --location "Dubai, UAE" \
        --url "https://ae.indeed.com/viewjob?jk=5bd6d3474b0865fa" \
        --source "Indeed" \
        --ats-score 67 \
        --job-id "5bd6d3474b0865fa"
"""
import json
import os
import sys
import argparse, requests, re
from datetime import datetime
from pathlib import Path

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, os.path.dirname(__file__))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

WORKSPACE = Path("/root/.openclaw/workspace")
NOTION_TOKEN = json.load(open(os.path.expanduser("~/.openclaw/workspace/config/notion.json")))["token"]
PIPELINE_DB = "3268d599-a162-81b4-b768-f162adfa4971"
APPLIED_IDS_FILE = WORKSPACE / "jobs-bank" / "applied-job-ids.txt"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}


def find_existing_page(url):
    """Find existing Pipeline entry by URL."""
    if not url:
        return None
    payload = {
        "filter": {"property": "URL", "url": {"equals": url}},
        "page_size": 1,
    }
    resp = requests.post(
        f"https://api.notion.com/v1/databases/{PIPELINE_DB}/query",
        headers=HEADERS, json=payload,
    )
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        if results:
            return results[0]["id"]
    return None


def add_to_notion(company, role, location, url, source, ats_score, cv_link=None, cv_model=None, verdict=None):
    """Add job to Notion Pipeline DB, or update existing entry to Applied."""
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Check if entry already exists (from push-submit-to-notion.py)
    existing_id = find_existing_page(url)
    
    if existing_id:
        # Update stage to Applied
        update_props = {
            "Stage": {"select": {"name": "✅ Applied"}},
            "Applied Date": {"date": {"start": today}},
        }
        # Add CV fields if provided
        if cv_link:
            update_props["CV Link"] = {"url": cv_link}
            update_props["CV Date"] = {"date": {"start": today}}
            update_props["Stage"] = {"select": {"name": "📄 CV Ready"}}
        if cv_model:
            update_props["CV Model"] = {"select": {"name": cv_model}}
        if verdict:
            update_props["Verdict"] = {"select": {"name": verdict}}
        # Auto-set follow-up 7 days from now
        from datetime import timedelta
        follow_up = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        update_props["Follow-up Due"] = {"date": {"start": follow_up}}
        
        resp = requests.patch(
            f"https://api.notion.com/v1/pages/{existing_id}",
            headers=HEADERS,
            json={"properties": update_props},
        )
        if resp.status_code == 200:
            page_url = resp.json().get("url", "")
            print(f"✅ Notion Pipeline (updated to Applied): {page_url}")
            return True
        else:
            print(f"❌ Notion update error {resp.status_code}: {resp.text[:200]}")
            return False
    else:
        # Create new entry
        props = {
            "Company": {"title": [{"text": {"content": company}}]},
            "Role": {"rich_text": [{"text": {"content": role}}]},
            "Stage": {"select": {"name": "✅ Applied"}},
            "Location": {"rich_text": [{"text": {"content": location}}]},
            "URL": {"url": url},
            "Source": {"select": {"name": source}},
            "Applied Date": {"date": {"start": today}},
            "Discovered Date": {"date": {"start": today}},
        }
        if ats_score:
            props["ATS Score"] = {"number": ats_score}
        if cv_link:
            props["CV Link"] = {"url": cv_link}
            props["CV Date"] = {"date": {"start": today}}
            props["Stage"] = {"select": {"name": "📄 CV Ready"}}
        if cv_model:
            props["CV Model"] = {"select": {"name": cv_model}}
        if verdict:
            props["Verdict"] = {"select": {"name": verdict}}
        # Auto-set follow-up 7 days from now
        from datetime import timedelta
        follow_up = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        props["Follow-up Due"] = {"date": {"start": follow_up}}

        payload = {"parent": {"database_id": PIPELINE_DB}, "properties": props}
        resp = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
        
        if resp.status_code == 200:
            page_url = resp.json().get("url", "")
            print(f"✅ Notion Pipeline (created): {page_url}")
            return True
        else:
            print(f"❌ Notion error {resp.status_code}: {resp.text[:200]}")
            return False


def add_to_applied_ids(job_id, company, role):
    """Add job ID to applied-job-ids.txt filter."""
    if not job_id:
        return
    
    # Check if already exists
    existing = set()
    if APPLIED_IDS_FILE.exists():
        with open(APPLIED_IDS_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split("|")
                    if parts:
                        existing.add(parts[0].strip())
    
    if job_id in existing:
        print(f"⏭️ Job ID {job_id} already in applied list")
        return
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    with open(APPLIED_IDS_FILE, "a") as f:
        f.write(f"{job_id} | {company} | {role} | {date_str}\n")
    print(f"✅ Applied IDs: added {job_id}")


def record_outcome(company, role, url, verdict, ats_score):
    """Append to jobs-outcomes.jsonl for the feedback loop."""
    outcomes_file = WORKSPACE / "data" / "feedback" / "jobs-outcomes.jsonl"
    outcomes_file.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "company": company,
        "role": role,
        "url": url,
        "verdict": verdict,
        "outcome": "applied",
        "applied_date": datetime.now().strftime("%Y-%m-%d"),
        "ats_score": ats_score or 0,
    }
    with open(outcomes_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def extract_job_id(url):
    """Extract LinkedIn/Indeed job ID from URL."""
    if not url:
        return None
    # LinkedIn: /view/NUMBER or slug-NUMBER
    m = re.search(r'/view/(\d{8,})', url)
    if m:
        return m.group(1)
    m = re.search(r'-(\d{8,})/?$', url.rstrip('/'))
    if m:
        return m.group(1)
    # Indeed: jk=HEXID
    m = re.search(r'jk=([a-f0-9]+)', url)
    if m:
        return m.group(1)
    return None


def main():
    parser = argparse.ArgumentParser(description="Add job to pipeline")
    parser.add_argument("--company", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--location", default="")
    parser.add_argument("--url", default="")
    parser.add_argument("--source", default="LinkedIn")
    parser.add_argument("--ats-score", type=int, default=None)
    parser.add_argument("--job-id", default=None, help="Override auto-extracted job ID")
    parser.add_argument("--cv-link", default=None, help="GitHub URL to tailored CV")
    parser.add_argument("--cv-model", default=None, help="Model used (e.g. Opus 4.6)")
    parser.add_argument("--verdict", default=None, help="SUBMIT/REVIEW")
    args = parser.parse_args()

    # Add to Notion
    add_to_notion(args.company, args.role, args.location, args.url, args.source, args.ats_score,
                  cv_link=args.cv_link, cv_model=args.cv_model, verdict=args.verdict)

    # Add to applied IDs filter
    job_id = args.job_id or extract_job_id(args.url)
    add_to_applied_ids(job_id, args.company, args.role)
    
    # Record outcome for feedback loop
    record_outcome(args.company, args.role, args.url, args.verdict or "SUBMIT", args.ats_score)

    # ── DB write (dual-write, non-blocking) ──────────────────────────────────
    if _pdb:
        try:
            db_job_id = job_id or ""
            if not db_job_id:
                import hashlib
                db_job_id = f"manual-{hashlib.md5(f'{args.company}|{args.role}|{args.url}'.encode()).hexdigest()[:10]}"
            _pdb.register_job(
                source=args.source.lower() if args.source else "manual",
                job_id=db_job_id,
                company=args.company,
                title=args.role,
                location=args.location or None,
                url=args.url or None,
                ats_score=args.ats_score,
                verdict=args.verdict,
                status="applied",
            )
            _pdb.mark_applied(db_job_id, applied_date=datetime.now().strftime("%Y-%m-%d"))
            print(f"  DB: registered {db_job_id}")
        except Exception as _e:
            print(f"  DB write failed (non-fatal): {_e}")
    # ─────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    main()
