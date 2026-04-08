#!/usr/bin/env python3
"""
jobs-mark-applied.py — Mark a job as Applied in Notion + local dedup list.

Usage:
  python3 jobs-mark-applied.py --job-id <id>            # by ontology/pipeline ID
  python3 jobs-mark-applied.py --company "Valkyrie"     # fuzzy match by company
  python3 jobs-mark-applied.py --title "CDO" --company "Valkyrie"
  python3 jobs-mark-applied.py --notion-id <page_id>    # direct Notion page

What this does:
  1. Find the job in Notion Job Pipeline DB
  2. Update Status → "Applied", set Applied Date to today
  3. Add job URL to jobs-bank/applied-job-ids.txt (dedup file)
  4. Append to ontology graph (JobApplication status update)
  5. Confirm via stdout + Telegram message
"""

import sys
import os
import json
import re
import requests
import argparse
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

WORKSPACE = Path("/root/.openclaw/workspace")
NOTION_CFG = WORKSPACE / "config" / "notion.json"
APPLIED_IDS_FILE = WORKSPACE / "jobs-bank" / "applied-job-ids.txt"
ONTOLOGY_FILE = WORKSPACE / "memory" / "ontology" / "graph.jsonl"
DATA_DIR = WORKSPACE / "data"

PIPELINE_DB_ID = "3268d599-a162-81b4-b768-f162adfa4971"
NOTION_VERSION = "2022-06-28"

TELEGRAM_CHAT_ID = "-1003882622947"
TELEGRAM_TOPIC_ID = "10"


def load_notion_token() -> str:
    with open(NOTION_CFG) as f:
        return json.load(f)["token"]


def notion_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def fuzzy_match(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def search_notion_pipeline(token: str, company: str = "", title: str = "") -> list[dict]:
    """Query Notion pipeline DB for matching jobs."""
    url = f"https://api.notion.com/v1/databases/{PIPELINE_DB_ID}/query"
    headers = notion_headers(token)
    
    # Build filter
    filters = []
    if company:
        filters.append({
            "property": "Company",
            "title": {"contains": company[:50]}
        })
    
    payload = {}
    if len(filters) == 1:
        payload["filter"] = filters[0]
    elif filters:
        payload["filter"] = {"and": filters}
    
    payload["page_size"] = 50
    
    results = []
    has_more = True
    cursor = None
    
    while has_more:
        if cursor:
            payload["start_cursor"] = cursor
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"Notion query error: {resp.status_code} {resp.text[:200]}")
            break
        data = resp.json()
        results.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        cursor = data.get("next_cursor")
        if len(results) > 200:
            break
    
    return results


def extract_page_fields(page: dict) -> dict:
    props = page.get("properties", {})
    
    def get_text(prop):
        val = props.get(prop, {})
        if val.get("type") == "title":
            return "".join(r.get("plain_text", "") for r in val.get("title", []))
        if val.get("type") == "rich_text":
            return "".join(r.get("plain_text", "") for r in val.get("rich_text", []))
        return ""
    
    def get_select(prop):
        val = props.get(prop, {})
        sel = val.get("select")
        return sel.get("name", "") if sel else ""
    
    def get_url(prop):
        val = props.get(prop, {})
        return val.get("url", "") or ""
    
    return {
        "id": page["id"],
        "title": get_text("Name") or get_text("Title") or get_text("Role"),
        "company": get_text("Company"),
        "status": get_select("Status"),
        "url": get_url("URL") or get_url("Job URL") or get_url("Link"),
    }


def update_notion_page_applied(token: str, page_id: str) -> bool:
    """Set Status=Applied and Applied Date=today."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    today = datetime.now().strftime("%Y-%m-%d")
    payload = {
        "properties": {
            "Status": {"select": {"name": "Applied"}},
            "Applied Date": {"date": {"start": today}},
        }
    }
    resp = requests.patch(url, json=payload, headers=notion_headers(token), timeout=30)
    if resp.status_code in (200, 204):
        return True
    # Try without Applied Date if property doesn't exist
    payload2 = {"properties": {"Status": {"select": {"name": "Applied"}}}}
    resp2 = requests.patch(url, json=payload2, headers=notion_headers(token), timeout=30)
    return resp2.status_code in (200, 204)


def add_to_applied_ids(job_url: str, company: str, title: str):
    """Append to applied-job-ids.txt for dedup."""
    APPLIED_IDS_FILE.parent.mkdir(exist_ok=True)
    
    # Extract job ID from LinkedIn URL
    job_id = ""
    m = re.search(r'/jobs/view/(\d+)', job_url or "")
    if m:
        job_id = m.group(1)
    elif job_url:
        job_id = job_url.split("?")[0].split("/")[-1][:30]
    
    if not job_id:
        return
    
    # Check if already exists
    if APPLIED_IDS_FILE.exists():
        existing = APPLIED_IDS_FILE.read_text()
        if job_id in existing:
            return
    
    entry = f"{job_id} | {company} | {title} | {datetime.now().strftime('%Y-%m-%d')}\n"
    with open(APPLIED_IDS_FILE, "a") as f:
        f.write(entry)
    print(f"  Added to applied-job-ids.txt: {job_id}")


def append_ontology(company: str, title: str, notion_id: str):
    """Update ontology JobApplication entity if exists, else create."""
    ONTOLOGY_FILE.parent.mkdir(exist_ok=True)
    entry = {
        "op": "create",
        "entity": {
            "id": f"job_{notion_id.replace('-', '')[:16]}",
            "type": "JobApplication",
            "properties": {
                "company": company,
                "title": title,
                "status": "applied",
                "date_applied": datetime.now().strftime("%Y-%m-%d"),
                "notion_page_id": notion_id,
            },
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat(),
        }
    }
    with open(ONTOLOGY_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"  Ontology updated: {company} / {title}")


def send_telegram_confirmation(company: str, title: str, job_url: str):
    """Send Telegram confirmation via OpenClaw gateway."""
    try:
        cfg_file = Path("/root/.openclaw/openclaw.json")
        with open(cfg_file) as f:
            cfg = json.load(f)
        token = cfg.get("gateway", {}).get("auth", {}).get("token", "")
        if not token:
            return
        
        msg = f"✅ Marked as Applied\n\n**{title}** @ {company}\n→ {job_url or 'No URL'}\n\nNotice + dedup + ontology updated."
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "message_thread_id": TELEGRAM_TOPIC_ID,
            "text": msg,
        }
        requests.post(
            "http://127.0.0.1:18789/v1/telegram/send",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Mark a job as Applied")
    parser.add_argument("--job-id", help="Local job ID from jobs-summary.json")
    parser.add_argument("--company", help="Company name (fuzzy match)")
    parser.add_argument("--title", help="Job title (fuzzy match, optional)")
    parser.add_argument("--notion-id", help="Direct Notion page ID")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not any([args.job_id, args.company, args.notion_id]):
        print("ERROR: Provide --job-id, --company, or --notion-id")
        sys.exit(1)

    token = load_notion_token()

    # --- Direct Notion page ID ---
    if args.notion_id:
        resp = requests.get(
            f"https://api.notion.com/v1/pages/{args.notion_id}",
            headers=notion_headers(token), timeout=30
        )
        if resp.status_code != 200:
            print(f"ERROR: Notion page not found: {args.notion_id}")
            sys.exit(1)
        fields = extract_page_fields(resp.json())
        pages = [resp.json()]
    else:
        # --- Search by company/title ---
        company_q = args.company or ""
        pages = search_notion_pipeline(token, company=company_q)
        if not pages:
            print(f"No jobs found in Notion for company='{company_q}'")
            sys.exit(1)

        # Score and pick best match
        candidates = []
        for p in pages:
            f = extract_page_fields(p)
            score = fuzzy_match(company_q, f["company"])
            if args.title:
                score = (score + fuzzy_match(args.title, f["title"])) / 2
            candidates.append((score, f, p))

        candidates.sort(key=lambda x: -x[0])
        best_score, fields, best_page = candidates[0]

        if best_score < 0.4:
            print(f"No confident match found (best: {fields['company']} / {fields['title']}, score={best_score:.2f})")
            print("Top 3 candidates:")
            for s, f2, _ in candidates[:3]:
                print(f"  {s:.2f} — {f2['company']} / {f2['title']} [{f2['status']}]")
            sys.exit(1)

        pages = [best_page]
        print(f"Match: {fields['company']} / {fields['title']} (score={best_score:.2f}, status={fields['status']})")

    # --- Confirm and update ---
    if fields["status"] == "Applied":
        print(f"Already marked as Applied: {fields['company']} / {fields['title']}")
        return

    if args.dry_run:
        print(f"[DRY RUN] Would mark Applied: {fields['company']} / {fields['title']}")
        return

    print(f"Marking Applied: {fields['company']} / {fields['title']}")
    ok = update_notion_page_applied(token, fields["id"])
    if not ok:
        print("ERROR: Failed to update Notion page")
        sys.exit(1)

    add_to_applied_ids(fields["url"], fields["company"], fields["title"])
    append_ontology(fields["company"], fields["title"], fields["id"])
    send_telegram_confirmation(fields["company"], fields["title"], fields["url"])

    print(f"\n✅ Done — {fields['company']} / {fields['title']} marked Applied in Notion + dedup list + ontology")


if __name__ == "__main__":
    main()
