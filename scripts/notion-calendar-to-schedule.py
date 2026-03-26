#!/usr/bin/env python3
"""
notion-calendar-to-schedule.py
==============================
Bridges Notion Content Calendar "Idea" entries → content-orchestrator's schedule.

Flow:
  Notion Content Calendar (Ideas)
    → This script (reads Ideas, picks best ones)
      → content-schedule.json (local orchestrator schedule)
        → Content Orchestrator (generates drafts)
          → LinkedIn Auto-poster (posts)

This script runs BEFORE content-orchestrator.py each day.

Usage:
  python3 notion-calendar-to-schedule.py          # Normal run
  python3 notion-calendar-to-schedule.py --dry   # Preview only
  python3 notion-calendar-to-schedule.py --days 7 # Look back 7 days
"""
import json, os, ssl, sys, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
os.makedirs(DATA_DIR, exist_ok=True)

NOTION_TOKEN = json.load(open(f"{WORKSPACE}/config/notion.json"))["token"]
CAL_DB = "3268d599-a162-814b-8854-c9b8bde62468"
HEADERS = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
CAIRO = timezone(timedelta(hours=2))

DRY = "--dry" in sys.argv
LOOKBACK_DAYS = 30  # Consider ideas from last 30 days

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
        except urllib.error.HTTPError as e:
            log(f"  Notion HTTP {e.code}: {e.read().decode()[:100]}")
            return []
        except Exception as e:
            log(f"  Notion error: {e}")
            return []
        all_results.extend(d.get("results", []))
        cursor = d.get("next_cursor")
        if not cursor: break
    return all_results

def get_prop(page, key):
    """Safely get a property value from a Notion page."""
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
    elif pt == "number":
        return prop.get("number") or 0
    return ""

def score_article(page):
    """Score an article for priority. Higher = better."""
    title = get_prop(page, "Title")
    hook = get_prop(page, "Hook")
    topic = get_prop(page, "Topic")
    planned_date = get_prop(page, "Planned Date")
    
    score = 0
    
    # Recency bonus: newer articles score higher
    if planned_date:
        try:
            from datetime import datetime as dt
            pd = dt.fromisoformat(planned_date)
            days_ago = (now().replace(tzinfo=None) - pd.replace(tzinfo=None)).days
            score += max(0, 30 - days_ago)  # 30pts for today, -1/day
        except:
            pass
    
    # Topic relevance (Ahmed's sweet spots)
    sweet = ["ai", "automation", "transformation", "pmo", "program", "digital", "leadership", "strategy"]
    if any(t in (title + hook + topic).lower() for t in sweet):
        score += 20
    
    # Strong hook (has numbers, specific claims)
    if any(c in hook for c in ["%", "$", "million", "billion"]):
        score += 15
    if len(hook) > 100:
        score += 10  # Substantive hook
    
    # Story-type hooks (personal, narrative)
    story_words = ["i ", "my ", "we ", "when i", "lessons", "hired", "fired", "built"]
    if any(w in hook.lower() for w in story_words):
        score += 15  # These tend to perform well
    
    return score

def main():
    log(f"=== Notion Calendar → Schedule Bridge === {now().strftime('%Y-%m-%d %H:%M')} Cairo")
    if DRY:
        log("  [DRY RUN — no changes]")
    
    # Load existing content-schedule.json
    schedule_file = DATA_DIR / "content-schedule.json"
    existing_titles = set()
    existing_schedule_titles = set()
    
    if schedule_file.exists():
        sched = json.load(open(schedule_file))
        # Get all existing titles in the schedule
        for post in sched.get("data", {}).get("this_week", {}).get("posts", []):
            existing_schedule_titles.add(post.get("title","").lower())
        log(f"  Existing schedule has {len(existing_schedule_titles)} posts")
    
    # Fetch Idea entries from Notion Content Calendar
    log(f"  Fetching 'Idea' entries from Notion (last {LOOKBACK_DAYS} days)...")
    ideas = notion_query_db(
        CAL_DB,
        filter_body={"property": "Status", "select": {"equals": "Idea"}}
    )
    log(f"  Found {len(ideas)} total Ideas in Notion")
    
    # Score and filter
    cutoff = (now() - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    scored = []
    for page in ideas:
        title = get_prop(page, "Title")
        planned_date = get_prop(page, "Planned Date")
        
        if not title:
            continue
        if planned_date and planned_date < cutoff:
            continue  # Skip very old ideas
        if title.lower() in existing_schedule_titles:
            continue  # Already in schedule
        
        score = score_article(page)
        topic = get_prop(page, "Topic")
        hook = get_prop(page, "Hook")
        bookmark_url = ""
        
        # Try to get bookmark URL from blocks
        pid = page["id"]
        try:
            req2 = urllib.request.Request(
                f"https://api.notion.com/v1/blocks/{pid}/children?page_size=10",
                headers=HEADERS
            )
            with urllib.request.urlopen(req2, timeout=15, context=ssl.create_default_context()) as r2:
                blocks = json.loads(r2.read())
            for b in blocks.get("results", []):
                if b.get("type") == "bookmark":
                    bookmark_url = (b.get("bookmark") or {}).get("url", "")
                    break
        except:
            pass
        
        scored.append({
            "title": title,
            "topic": topic,
            "hook": hook,
            "url": bookmark_url,
            "score": score,
            "planned_date": planned_date,
            "page_id": pid
        })
    
    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)
    
    if not scored:
        log("  No new ideas to add (all already in schedule or none found)")
        return
    
    log(f"\n  Top candidates ({len(scored)} new):")
    for i, a in enumerate(scored[:10]):
        log(f"  {i+1}. [{a['score']:3d}pts] [{a['topic'] or '?'}] {a['title'][:55]}")
    
    if DRY:
        return
    
    # Update content-schedule.json with new ideas
    if schedule_file.exists():
        sched = json.load(open(schedule_file))
    else:
        sched = {"meta": {}, "data": {"this_week": {"posts": []}, "pipeline": {"ideas": 0}}}
    
    # Add new ideas as scheduled posts (starting from today)
    today_str = now().strftime("%Y-%m-%d")
    
    # Count how many we can add (cap at 7 per week)
    existing_count = len(sched.get("data",{}).get("this_week",{}).get("posts",[]))
    available_slots = max(0, 7 - existing_count)
    
    added = 0
    for idea in scored[:available_slots]:
        # Pick next available weekday (Sun-Thu)
        post_date = idea.get("planned_date") or today_str
        
        sched["data"].setdefault("this_week", {"posts": []})
        sched["data"]["this_week"].setdefault("posts", [])
        sched["data"]["this_week"]["posts"].append({
            "title": idea["title"],
            "date": post_date,
            "topic": idea["topic"],
            "hook": idea["hook"][:200] if idea["hook"] else "",
            "status": "scheduled",
            "source": "notion_idea",
            "url": idea["url"],
            "page_id": idea["page_id"]
        })
        added += 1
        log(f"  + Added: {idea['title'][:55]}")
    
    # Update pipeline counts
    sched["data"]["pipeline"] = sched["data"].get("pipeline", {})
    sched["data"]["pipeline"]["ideas"] = len(scored)
    
    # Update meta
    sched["meta"]["notion_bridge"] = {
        "last_run": now().isoformat(),
        "ideas_added": added,
        "total_notion_ideas": len(scored)
    }
    
    json.dump(sched, open(schedule_file, "w"), indent=2, ensure_ascii=False)
    log(f"\n  ✅ Added {added} ideas to content-schedule.json")
    log(f"  Total posts in schedule: {len(sched['data']['this_week']['posts'])}")
    log(f"  Pipeline ideas: {sched['data']['pipeline']['ideas']}")

if __name__ == "__main__":
    main()
