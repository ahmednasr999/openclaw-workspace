#!/usr/bin/env python3
"""
Push SUBMIT jobs to Notion Pipeline DB with full JD text.
Creates entries with stage "📋 Recommended".
Skips jobs already in Pipeline (checks by URL).

Run after jobs-review.py produces jobs-summary.json.
"""
import os
import sys
import json, requests, re, time
from pathlib import Path
from datetime import datetime

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, os.path.dirname(__file__))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

WORKSPACE = Path("/root/.openclaw/workspace")
SUMMARY_FILE = WORKSPACE / "data" / "jobs-summary.json"
NOTION_TOKEN = json.load(open(os.path.expanduser("~/.openclaw/workspace/config/notion.json")))["token"]
PIPELINE_DB = "3268d599-a162-81b4-b768-f162adfa4971"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def get_existing_urls() -> set:
    """Get all URLs already in the Pipeline DB."""
    urls = set()
    payload = {
        "filter": {"property": "URL", "url": {"is_not_empty": True}},
        "page_size": 100,
    }
    has_more = True
    while has_more:
        resp = requests.post(
            f"https://api.notion.com/v1/databases/{PIPELINE_DB}/query",
            headers=HEADERS,
            json=payload,
        )
        if resp.status_code != 200:
            print(f"  Warning: Could not query Pipeline DB: {resp.status_code}")
            break
        data = resp.json()
        for page in data.get("results", []):
            url_prop = page.get("properties", {}).get("URL", {}).get("url")
            if url_prop:
                urls.add(url_prop.strip().rstrip("/"))
        has_more = data.get("has_more", False)
        if has_more:
            payload["start_cursor"] = data.get("next_cursor")
    return urls


def get_jd_text(job: dict) -> str:
    """Get JD text from enriched data (no re-fetch — single source of truth is jobs-enrich-jd.py)."""
    return job.get("jd_text", "") or job.get("jd_page_text", "") or job.get("raw_snippet", "")


def create_notion_entry(job: dict, jd_text: str) -> bool:
    """Create a Notion Pipeline entry for a SUBMIT job."""
    company = job.get("company", "Unknown")
    title = job.get("title", "Unknown")
    location = job.get("location", "")
    url = job.get("url", "")
    source = job.get("source", "linkedin").capitalize()
    ats_score = job.get("ats_score", 0)
    fit_score = job.get("career_fit_score", 0)
    reason = job.get("verdict_reason", "")

    verdict = job.get("verdict", "SUBMIT")
    
    props = {
        "Company": {"title": [{"text": {"content": company[:100]}}]},
        "Role": {"rich_text": [{"text": {"content": title[:200]}}]},
        "Stage": {"select": {"name": "📋 Scored"}},
        "Verdict": {"select": {"name": verdict}},
        "Location": {"rich_text": [{"text": {"content": location[:100]}}]},
        "Source": {"select": {"name": source}},
        "ATS Score": {"number": ats_score},
        "Discovered Date": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
    }
    if url:
        props["URL"] = {"url": url}
    salary = job.get("salary", "")
    if salary:
        props["Salary"] = {"rich_text": [{"text": {"content": salary[:100]}}]}

    # Build page body with JD text
    children = []
    
    # Fit score + reason
    children.append({
        "object": "block", "type": "callout",
        "callout": {
            "rich_text": [{"text": {"content": f"Fit: {fit_score}/10 | ATS: {ats_score}/100 | {reason}"[:2000]}}],
            "icon": {"emoji": "🎯"}
        }
    })

    # JD text (split into chunks of 2000 chars for Notion limit)
    if jd_text:
        children.append({
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "Job Description"}}]}
        })
        
        # Split JD into 2000-char chunks
        for i in range(0, len(jd_text), 2000):
            chunk = jd_text[i:i+2000]
            children.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": chunk}}]}
            })

    payload = {
        "parent": {"database_id": PIPELINE_DB},
        "properties": props,
        "children": children[:20],  # Notion limit
    }

    resp = safe_notion_request(requests.post, "https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
    if resp and resp.status_code == 200:
        resp_data = resp.json()
        page_url = resp_data.get("url", "")
        notion_page_id = resp_data.get("id", "")
        print(f"  ✅ {title[:40]} → {page_url}")
        # ── DB write (dual-write, non-blocking) ──────────────────────────────
        if _pdb:
            try:
                job_id = str(job.get("id", job.get("job_id", ""))).strip()
                if job_id:
                    _pdb.update_field(
                        job_id,
                        notion_page_id=notion_page_id,
                        notion_synced=1,
                    )
            except Exception:
                pass
        # ─────────────────────────────────────────────────────────────────────
        return True
    else:
        status = resp.status_code if resp else "NO_RESPONSE"
        text = resp.text[:100] if resp else "Connection failed"
        print(f"  ❌ {title[:40]}: {status} {text}")
        return False


def safe_notion_request(method, url, **kwargs):
    """Wrap Notion API calls with retry and error handling."""
    for attempt in range(3):
        try:
            resp = method(url, **kwargs)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", 2))
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            return resp
        except requests.exceptions.RequestException as e:
            print(f"  HTTP error (attempt {attempt+1}/3): {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
    return None


def main():
    if not SUMMARY_FILE.exists():
        print("No jobs-summary.json found")
        sys.exit(1)

    data = json.load(open(SUMMARY_FILE))
    submit_jobs = data.get("data", {}).get("submit", [])
    review_jobs = data.get("data", {}).get("review", [])
    
    # Push both SUBMIT and REVIEW to Pipeline
    all_jobs = submit_jobs + review_jobs
    
    if not all_jobs:
        print("No SUBMIT/REVIEW jobs to push")
        return

    print(f"Found {len(submit_jobs)} SUBMIT + {len(review_jobs)} REVIEW jobs")
    
    # Get existing URLs to avoid duplicates
    print("Checking existing Pipeline entries...")
    existing_urls = get_existing_urls()
    print(f"  {len(existing_urls)} existing entries")
    
    new_jobs = []
    for job in all_jobs:
        url = job.get("url", "").strip().rstrip("/")
        if url and url in existing_urls:
            continue
        new_jobs.append(job)
    
    if not new_jobs:
        print("All jobs already in Pipeline")
        return
    
    print(f"Pushing {len(new_jobs)} new jobs to Pipeline...")
    
    added = 0
    for i, job in enumerate(new_jobs):
        if i > 0:
            time.sleep(0.5)  # Rate limit
        
        jd_text = get_jd_text(job)
        
        if create_notion_entry(job, jd_text):
            added += 1
    
    print(f"\nDone: {added}/{len(new_jobs)} added to Pipeline")
    
    # Auto-cleanup: archive Discovered/Scored entries older than 14 days
    auto_cleanup()


def auto_cleanup():
    """Archive stale pipeline entries (Discovered/Scored >14 days old)."""
    from datetime import timezone, timedelta
    
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%d")
    
    # Find stale entries
    payload = {
        "filter": {
            "and": [
                {"property": "Stage", "select": {"equals": "🔍 Discovered"}},
                {"property": "Discovered Date", "date": {"before": cutoff}},
            ]
        },
        "page_size": 100,
    }
    
    stale_ids = []
    has_more = True
    while has_more:
        resp = requests.post(
            f"https://api.notion.com/v1/databases/{PIPELINE_DB}/query",
            headers=HEADERS, json=payload,
        )
        if resp.status_code != 200:
            break
        data = resp.json()
        for page in data.get("results", []):
            stale_ids.append(page["id"])
        has_more = data.get("has_more", False)
        if has_more:
            payload["start_cursor"] = data.get("next_cursor")
    
    if not stale_ids:
        return
    
    print(f"\nAuto-cleanup: archiving {len(stale_ids)} stale Discovered entries (>14 days)...")
    archived = 0
    for i, pid in enumerate(stale_ids):
        if i > 0 and i % 3 == 0:
            time.sleep(0.4)
        resp = requests.patch(
            f"https://api.notion.com/v1/pages/{pid}",
            headers=HEADERS,
            json={"archived": True},
        )
        if resp.status_code == 200:
            archived += 1
    print(f"  Archived: {archived}/{len(stale_ids)}")


if __name__ == "__main__":
    main()
