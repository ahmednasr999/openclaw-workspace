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
import argparse, requests, json, re, sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
NOTION_TOKEN = "NOTION_TOKEN_REDACTED"
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


def add_to_notion(company, role, location, url, source, ats_score):
    """Add job to Notion Pipeline DB, or update existing entry to Applied."""
    
    # Check if entry already exists (from push-submit-to-notion.py)
    existing_id = find_existing_page(url)
    
    if existing_id:
        # Update stage to Applied
        update_props = {
            "Stage": {"select": {"name": "✅ Applied"}},
            "Applied Date": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
        }
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
            "Applied Date": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
        }
        if ats_score:
            props["ATS Score"] = {"number": ats_score}

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
    args = parser.parse_args()

    # Add to Notion
    add_to_notion(args.company, args.role, args.location, args.url, args.source, args.ats_score)

    # Add to applied IDs filter
    job_id = args.job_id or extract_job_id(args.url)
    add_to_applied_ids(job_id, args.company, args.role)


if __name__ == "__main__":
    main()
