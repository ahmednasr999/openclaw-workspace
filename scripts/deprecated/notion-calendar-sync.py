#!/usr/bin/env python3
"""
notion-calendar-sync.py
=======================
Bidirectional sync between Notion Content Calendar and content-orchestrator.

What it does:
  1. Reads 'Scheduled' posts from content-schedule.json
  2. Updates 'Idea' entries in Notion to 'Scheduled' status
  3. Reads 'Draft' field from Notion to feed back into the posting flow
  4. Updates 'Status' in Notion: Idea → Scheduled → Drafted → Posted

Run: BEFORE content-orchestrator.py each day
  python3 notion-calendar-sync.py

Cron: Before rss-to-calendar (morning)
"""
import json, os, ssl, sys, time, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"

NOTION_TOKEN = json.load(open(f"{WORKSPACE}/config/notion.json"))["token"]
CAL_DB = "3268d599-a162-814b-8854-c9b8bde62468"
HEADERS = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
CAIRO = timezone(timedelta(hours=2))

def now():
    return datetime.now(CAIRO)

def log(msg):
    print(f"[{now().strftime('%H:%M')}] {msg}")

def notion_query_db(db_id, filter_body=None, page_size=100):
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    all_results, cursor = [], None
    while True:
        body = {"page_size": page_size}
        if cursor: body["start_cursor"] = cursor
        if filter_body: body["filter"] = filter_body
        req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=20, context=ssl.create_default_context()) as r:
                d = json.loads(r.read())
        except Exception as e:
            log(f"  Notion query error: {e}")
            return []
        all_results.extend(d.get("results", []))
        cursor = d.get("next_cursor")
        if not cursor: break
    return all_results

def notion_patch(url_path, body):
    url = f"https://api.notion.com/v1{url_path}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="PATCH", headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15, context=ssl.create_default_context()) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:100]}"
    except Exception as e:
        return None, str(e)

def get_prop(page, key):
    props = page.get("properties", {})
    prop = props.get(key, {}) or {}
    pt = prop.get("type", "?")
    if pt == "title":
        return "".join([t.get("plain_text","") for t in prop.get("title",[])])
    elif pt == "select":
        return (prop.get("select") or {}).get("name", "") or ""
    elif pt == "rich_text":
        return "".join([t.get("plain_text","") for t in prop.get("rich_text",[])])
    elif pt == "date":
        return (prop.get("date") or {}).get("start", "") or ""
    elif pt == "url":
        return prop.get("url", "") or ""
    return ""

def sync_ideas_to_scheduled():
    """Update Idea entries in Notion that appear in content-schedule.json."""
    # Load schedule
    sched_file = DATA_DIR / "content-schedule.json"
    if not sched_file.exists():
        log("  No content-schedule.json found — skipping scheduled sync")
        return 0, 0
    
    sched = json.load(open(sched_file))
    scheduled_posts = sched.get("data", {}).get("this_week", {}).get("posts", [])
    
    # Build title → date map
    scheduled_titles = {p["title"].lower(): p for p in scheduled_posts if p.get("status") == "scheduled"}
    log(f"  Schedule has {len(scheduled_titles)} scheduled posts")
    
    # Get all Idea entries from Notion
    ideas = notion_query_db(CAL_DB, filter_body={"property": "Status", "select": {"equals": "Idea"}})
    log(f"  Notion has {len(ideas)} Idea entries")
    
    updated = 0
    errors = 0
    
    for idea in ideas:
        title = get_prop(idea, "Title")
        if not title:
            continue
        
        # Check if this idea is in the schedule
        match = None
        for sched_title, sched_data in scheduled_titles.items():
            if sched_title in title.lower() or title.lower() in sched_title:
                match = sched_data
                break
        
        if not match:
            continue
        
        # Update status: Idea → Scheduled
        page_id = idea["id"]
        planned_date = match.get("date", "")
        
        body = {
            "properties": {
                "Status": {"select": {"name": "Scheduled"}},
            }
        }
        
        if planned_date:
            body["properties"]["Planned Date"] = {"date": {"start": planned_date}}
        
        # Also add the Day field if present in schedule (Sun=0, Mon=1, ..., Thu=4)
        # Note: Notion uses select for Day, e.g. "Sunday", "Monday"
        if planned_date:
            try:
                from datetime import datetime as dt
                day_num = dt.fromisoformat(planned_date).weekday()
                # Python: Mon=0, Sun=6. Cairo week: Sun=0, Mon=1...Thu=4, Fri=5, Sat=6
                day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                day_name = day_names[day_num]
                body["properties"]["Day"] = {"select": {"name": day_name}}
            except:
                pass
        
        result, err = notion_patch(f"/pages/{page_id}", body)
        if err:
            log(f"  ERROR updating '{title[:40]}': {err}")
            errors += 1
        else:
            log(f"  ✅ '{title[:50]}' → Scheduled ({planned_date})")
            updated += 1
        
        time.sleep(0.5)  # Rate limit
    
    return updated, errors

def sync_drafts_from_notion():
    """Read Draft content from Notion Scheduled entries and update schedule."""
    sched_file = DATA_DIR / "content-schedule.json"
    if not sched_file.exists():
        return 0
    
    sched = json.load(open(sched_file))
    
    # Get Scheduled entries from Notion
    scheduled = notion_query_db(CAL_DB, filter_body={"property": "Status", "select": {"equals": "Scheduled"}})
    log(f"  Notion has {len(scheduled)} Scheduled entries with drafts")
    
    drafts_updated = 0
    for page in scheduled:
        title = get_prop(page, "Title")
        draft = get_prop(page, "Draft")
        topic = get_prop(page, "Topic")
        planned_date = get_prop(page, "Planned Date")
        
        if not draft:
            continue
        
        # Update the matching post in the schedule
        for post in sched.get("data", {}).get("this_week", {}).get("posts", []):
            if title.lower() in post.get("title","").lower() or post.get("title","").lower() in title.lower():
                if not post.get("draft") and draft:
                    post["draft"] = draft
                    post["topic"] = topic or post.get("topic", "")
                    drafts_updated += 1
                    log(f"  📝 Draft loaded: {title[:50]}")
                    break
    
    if drafts_updated > 0:
        json.dump(sched, open(sched_file, "w"), indent=2, ensure_ascii=False)
        log(f"  ✅ Synced {drafts_updated} drafts to content-schedule.json")
    
    return drafts_updated

def main():
    log(f"=== Notion Calendar Sync === {now().strftime('%Y-%m-%d %H:%M')} Cairo")
    
    # Step 1: Push scheduled posts to Notion
    log("\n[1] Syncing scheduled posts → Notion (Idea → Scheduled)...")
    updated, errors = sync_ideas_to_scheduled()
    
    # Step 2: Pull drafts from Notion into schedule
    log("\n[2] Syncing drafts from Notion → schedule...")
    drafts = sync_drafts_from_notion()
    
    log(f"\n=== Done ===")
    log(f"  Updated in Notion: {updated}")
    log(f"  Drafts synced: {drafts}")
    log(f"  Errors: {errors}")

if __name__ == "__main__":
    main()
