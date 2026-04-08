#!/usr/bin/env python3
"""
job-dedup-check.py - Scans for duplicate job applications.

Checks both local SQLite database and Notion Pipeline DB for duplicate
company+title combinations. Reports findings for manual cleanup.

Usage:
  python3 scripts/job-dedup-check.py              # Scan all
  python3 scripts/job-dedup-check.py --fix-locks  # Auto-clean orphaned locks
  python3 scripts/job-dedup-check.py --verbose    # Detailed output
"""

import sqlite3
import json
import sys
import urllib.request
import os
from datetime import datetime
from collections import defaultdict
from pathlib import Path


WORKSPACE = "/root/.openclaw/workspace"
DB_PATH = f"{WORKSPACE}/data/nasr-pipeline.db"
NOTION_DB_ID = "3268d599-a162-81b4-b768-f162adfa4971"


def get_notion_token():
    """Read Notion token from config."""
    try:
        with open(f"{WORKSPACE}/config/notion.json") as f:
            return json.load(f)["token"]
    except Exception as e:
        print(f"ERROR: Failed to read Notion token: {e}")
        return None


def notion_request(method, endpoint, body=None):
    """Make a Notion API request."""
    token = get_notion_token()
    if not token:
        return None
    
    url = f"https://api.notion.com/v1/{endpoint}"
    data = json.dumps(body).encode() if body else None
    
    try:
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"ERROR: Notion API request failed: {e}")
        return None


def scan_sqlite_duplicates(verbose=False):
    """Find duplicate company+title combinations in SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Find duplicates: company+title pairs with count > 1
        cursor.execute("""
            SELECT LOWER(company || '|' || title) as key, 
                   company, title, COUNT(*) as count, 
                   GROUP_CONCAT(id, ',') as ids
            FROM jobs
            WHERE company IS NOT NULL AND title IS NOT NULL
            GROUP BY LOWER(company || '|' || title)
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)
        
        duplicates = cursor.fetchall()
        conn.close()
        
        if not duplicates:
            print("✅ SQLite: No duplicates found")
            return []
        
        print(f"⚠️  SQLite: Found {len(duplicates)} duplicate(s):")
        results = []
        
        for key, company, title, count, ids in duplicates:
            print(f"  [{count}x] {company} | {title}")
            if verbose:
                id_list = ids.split(',')
                for idx, job_id in enumerate(id_list, 1):
                    print(f"      ID {idx}: {job_id}")
            
            results.append({
                "source": "sqlite",
                "company": company,
                "title": title,
                "count": count,
                "ids": ids.split(',') if ids else [],
            })
        
        return results
    
    except sqlite3.Error as e:
        print(f"ERROR: SQLite error: {e}")
        return []


def scan_notion_duplicates(verbose=False):
    """Find duplicate company+title combinations in Notion."""
    result = notion_request("POST", f"databases/{NOTION_DB_ID}/query", {
        "page_size": 100
    })
    
    if not result:
        print("⚠️  Notion: Failed to query database")
        return []
    
    # Build a map of company|title -> pages
    seen = defaultdict(list)
    
    for page in result.get("results", []):
        props = page.get("properties", {})
        
        company_t = props.get("Company", {}).get("title", [])
        company = company_t[0].get("plain_text", "") if company_t else ""
        
        title_t = props.get("Role", {}).get("rich_text", [])
        title = title_t[0].get("plain_text", "") if title_t else ""
        
        if company and title:
            key = f"{company.lower()}|{title.lower()}"
            seen[key].append({
                "page_id": page["id"],
                "company": company,
                "title": title,
                "url": props.get("URL", {}).get("url", ""),
            })
    
    # Find duplicates
    duplicates = {k: v for k, v in seen.items() if len(v) > 1}
    
    if not duplicates:
        print("✅ Notion: No duplicates found")
        return []
    
    print(f"⚠️  Notion: Found {len(duplicates)} duplicate(s):")
    results = []
    
    for key, pages in duplicates.items():
        company = pages[0]["company"]
        title = pages[0]["title"]
        print(f"  [{len(pages)}x] {company} | {title}")
        
        if verbose:
            for idx, page in enumerate(pages, 1):
                print(f"      Page {idx}: {page['page_id']} - {page.get('url', 'no URL')}")
        
        results.append({
            "source": "notion",
            "company": company,
            "title": title,
            "count": len(pages),
            "page_ids": [p["page_id"] for p in pages],
        })
    
    return results


def scan_orphaned_locks(verbose=False):
    """Find locks that may be orphaned (stale)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT company, title, locked_at, locked_by
            FROM application_locks
            ORDER BY locked_at DESC
        """)
        
        locks = cursor.fetchall()
        conn.close()
        
        if not locks:
            print("✅ Locks: No active locks")
            return []
        
        import time
        current_time = int(time.time())
        lock_timeout = 300  # 5 minutes
        stale = []
        
        for company, title, locked_at, locked_by in locks:
            age = current_time - locked_at
            is_stale = age > lock_timeout
            
            status = "STALE" if is_stale else "ACTIVE"
            print(f"  [{status}] {company} | {title} (age: {age}s, pid: {locked_by})")
            
            if is_stale:
                stale.append({
                    "company": company,
                    "title": title,
                    "age_seconds": age,
                    "locked_by": locked_by,
                })
        
        if stale:
            print(f"\n⚠️  Locks: Found {len(stale)} stale lock(s) (>5 min old)")
        else:
            print(f"✅ Locks: All {len(locks)} lock(s) are active")
        
        return stale
    
    except sqlite3.Error as e:
        print(f"ERROR: SQLite error checking locks: {e}")
        return []


def cleanup_orphaned_locks(dry_run=True):
    """Remove locks older than timeout."""
    try:
        from application_lock import ApplicationLockService
        service = ApplicationLockService()
        
        locks = service.list_all_locks()
        
        if not locks:
            print("No locks to clean up")
            return 0
        
        import time
        current_time = int(time.time())
        lock_timeout = 300
        cleaned = 0
        
        for company, title, locked_at, locked_by in locks:
            age = current_time - locked_at
            if age > lock_timeout:
                print(f"  Cleaning up stale lock: {company} | {title} (age: {age}s)")
                if not dry_run:
                    service.release_lock(company, title)
                cleaned += 1
        
        return cleaned
    
    except Exception as e:
        print(f"ERROR: Cleanup failed: {e}")
        return 0


def main():
    verbose = "--verbose" in sys.argv
    fix_locks = "--fix-locks" in sys.argv
    dry_run = "--dry-run" in sys.argv or "--fix-locks" in sys.argv and "--execute" not in sys.argv
    
    print("=" * 70)
    print("Job Application Deduplication Check")
    print("=" * 70)
    
    # Scan SQLite for duplicates
    sqlite_dups = scan_sqlite_duplicates(verbose=verbose)
    
    print()
    
    # Scan Notion for duplicates
    notion_dups = scan_notion_duplicates(verbose=verbose)
    
    print()
    
    # Check for orphaned locks
    stale_locks = scan_orphaned_locks(verbose=verbose)
    
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    total_issues = len(sqlite_dups) + len(notion_dups) + len(stale_locks)
    
    if total_issues == 0:
        print("✅ No issues found!")
        return 0
    
    print(f"Found {total_issues} issue(s):")
    
    if sqlite_dups:
        print(f"  • SQLite duplicates: {len(sqlite_dups)}")
    if notion_dups:
        print(f"  • Notion duplicates: {len(notion_dups)}")
    if stale_locks:
        print(f"  • Stale locks: {len(stale_locks)}")
    
    # Handle lock cleanup
    if fix_locks and stale_locks:
        print()
        print("=" * 70)
        if dry_run:
            print("Lock Cleanup (DRY RUN)")
            cleaned = cleanup_orphaned_locks(dry_run=True)
            print(f"Would clean up {cleaned} stale lock(s)")
            print("Run with --execute to actually clean up")
        else:
            print("Lock Cleanup (EXECUTING)")
            cleaned = cleanup_orphaned_locks(dry_run=False)
            print(f"Cleaned up {cleaned} stale lock(s)")
    
    print("=" * 70)
    
    return 1 if total_issues > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
