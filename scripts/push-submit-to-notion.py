#!/usr/bin/env python3
"""
Push SUBMIT jobs to Notion Pipeline DB with full JD text.
Creates entries with stage "📋 Recommended".
Skips jobs already in Pipeline (checks by URL).

Run after jobs-review.py produces jobs-summary.json.
"""
import json, requests, re, time, sys
from pathlib import Path
from datetime import datetime
import urllib.request

WORKSPACE = Path("/root/.openclaw/workspace")
SUMMARY_FILE = WORKSPACE / "data" / "jobs-summary.json"
NOTION_TOKEN = "NOTION_TOKEN_REDACTED"
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


def fetch_jd_text(url: str) -> str:
    """Fetch job description text from URL."""
    if not url:
        return ""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read(50000).decode("utf-8", errors="ignore")
            # Strip HTML tags
            clean = re.sub(r'<script[^>]*>.*?</script>', ' ', raw, flags=re.DOTALL)
            clean = re.sub(r'<style[^>]*>.*?</style>', ' ', clean, flags=re.DOTALL)
            clean = re.sub(r'<[^>]+>', ' ', clean)
            clean = re.sub(r'\s+', ' ', clean).strip()
            # Trim to reasonable size for Notion (2000 char limit per block)
            return clean[:4000]
    except Exception as e:
        print(f"  Could not fetch JD: {str(e)[:50]}")
        return ""


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

    props = {
        "Company": {"title": [{"text": {"content": company[:100]}}]},
        "Role": {"rich_text": [{"text": {"content": title[:200]}}]},
        "Stage": {"select": {"name": "📋 Recommended"}},
        "Location": {"rich_text": [{"text": {"content": location[:100]}}]},
        "Source": {"select": {"name": source}},
        "ATS Score": {"number": ats_score},
        "Discovered Date": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
    }
    if url:
        props["URL"] = {"url": url}

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

    resp = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
    if resp.status_code == 200:
        page_url = resp.json().get("url", "")
        print(f"  ✅ {title[:40]} → {page_url}")
        return True
    else:
        print(f"  ❌ {title[:40]}: {resp.status_code} {resp.text[:100]}")
        return False


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
        
        # Use enriched JD from jobs-summary.json first, fetch only if missing
        jd_text = job.get("jd_text", "") or job.get("description", "") or job.get("snippet", "")
        if not jd_text or len(jd_text) < 100:
            print(f"  Fetching JD (not in summary): {job.get('title','?')[:40]}...")
            jd_text = fetch_jd_text(job.get("url", ""))
        
        if create_notion_entry(job, jd_text):
            added += 1
    
    print(f"\nDone: {added}/{len(new_jobs)} added to Pipeline")


if __name__ == "__main__":
    main()
