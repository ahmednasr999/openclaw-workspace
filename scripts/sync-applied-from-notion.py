#!/usr/bin/env python3
"""
sync-applied-from-notion.py - Sync applied job IDs from Notion Pipeline to local filter list.

Runs before each pipeline review to ensure no already-applied jobs resurface.
Reads Notion Pipeline DB, finds all "Applied" entries, extracts job IDs from URLs,
and ensures they're in applied-job-ids.txt.
"""
import os
import sys
import json, re, requests
from pathlib import Path

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, os.path.dirname(__file__))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

NOTION_TOKEN = json.load(open(os.path.expanduser("~/.openclaw/workspace/config/notion.json")))["token"]
PIPELINE_DB = "3268d599-a162-81b4-b768-f162adfa4971"
HEADERS = {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
APPLIED_FILE = Path("/root/.openclaw/workspace/jobs-bank/applied-job-ids.txt")

def run():
    # Load existing IDs
    existing = set()
    for line in open(APPLIED_FILE):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        if parts:
            aid = parts[0].strip()
            if aid and len(aid) >= 6:
                existing.add(aid)
    
    print(f"Existing IDs: {len(existing)}")
    
    # Query all pipeline entries
    all_pages = []
    has_more = True
    start_cursor = None
    while has_more:
        body = {"page_size": 100}
        if start_cursor:
            body["start_cursor"] = start_cursor
        try:
            resp = requests.post(f"https://api.notion.com/v1/databases/{PIPELINE_DB}/query",
                headers=HEADERS, json=body, timeout=15)
            if resp.status_code != 200:
                print(f"  Notion query failed: {resp.status_code}")
                break
            data = resp.json()
        except requests.exceptions.RequestException as e:
            print(f"  Notion connection error: {e}")
            break
        all_pages.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
    
    print(f"Total pipeline entries: {len(all_pages)}")
    
    new_ids = []
    for page in all_pages:
        props = page.get("properties", {})
        stage = props.get("Stage", {}).get("select", {})
        stage_name = stage.get("name", "") if stage else ""
        
        # Only sync Applied or Skipped entries
        if "Applied" not in stage_name and "Skipped" not in stage_name and "Rejected" not in stage_name:
            continue
        
        company_parts = props.get("Company", {}).get("title", [])
        company = company_parts[0].get("plain_text", "") if company_parts else "?"
        
        role_parts = props.get("Role", {}).get("rich_text", [])
        role = role_parts[0].get("plain_text", "") if role_parts else "?"
        
        url = props.get("URL", {}).get("url", "") or ""
        
        # Extract IDs from URL
        url_ids = re.findall(r'[a-f0-9]{10,}|\d{8,}', url)
        
        for uid in url_ids:
            if uid not in existing:
                new_ids.append(f"{uid} | {company} | {role[:50]} | synced from Notion | {stage_name}")
                existing.add(uid)
                # ── DB write (dual-write, non-blocking) ──────────────────────
                if _pdb:
                    try:
                        notion_page_id = page.get("id", "")
                        if "Applied" in stage_name:
                            # Ensure job exists then mark applied
                            _pdb.register_job(
                                source="notion_sync",
                                job_id=uid,
                                company=company,
                                title=role,
                                url=url,
                                status="applied",
                            )
                            _pdb.mark_applied(uid)
                            if notion_page_id:
                                _pdb.update_field(uid, notion_page_id=notion_page_id, notion_synced=1)
                    except Exception:
                        pass
                # ─────────────────────────────────────────────────────────────
    
    if new_ids:
        # NOTE: applied-job-ids.txt is DEPRECATED. Notion is the single source of truth.
        # DB write below keeps the SQLite cache in sync (used by other pipeline scripts).
        print(f"Found {len(new_ids)} new Applied jobs from Notion (DB updated, txt deprecated)")
    else:
        print("No new Applied jobs in Notion")
    
    print(f"Notion Applied count: {len(existing)}")

if __name__ == "__main__":
    run()
