#!/usr/bin/env python3
"""
content-agent.py — Reads Notion Content Calendar DB, tracks content pipeline health.

Tracks: today's scheduled post, this_week stats, full pipeline
Content health: days until content runs out, posting streak, topics covered
Merged Engagement Radar: engagement opportunities from coordination/content-calendar.json
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

# Import from agent-common.py
import sys
sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module
common = import_module("agent-common")

AgentResult = common.AgentResult
agent_main = common.agent_main
retry_with_backoff = common.retry_with_backoff
load_json = common.load_json
is_dry_run = common.is_dry_run
now_cairo = common.now_cairo
now_iso = common.now_iso
WORKSPACE = common.WORKSPACE
DATA_DIR = common.DATA_DIR

# Configuration
NOTION_TOKEN = "NOTION_TOKEN_REDACTED"
CONTENT_DB_ID = "3268d599-a162-814b-8854-c9b8bde62468"
OUTPUT_PATH = DATA_DIR / "content-schedule.json"
COORDINATION_CALENDAR = WORKSPACE / "coordination" / "content-calendar.json"


@retry_with_backoff(max_retries=3, base_delay=2)
def fetch_notion_db(database_id):
    """Fetch all pages from a Notion database."""
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    all_results = []
    has_more = True
    start_cursor = None
    
    while has_more:
        body = {}
        if start_cursor:
            body["start_cursor"] = start_cursor
        
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        all_results.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
    
    return all_results


def parse_notion_page(page):
    """Extract relevant fields from a Notion page."""
    props = page.get("properties", {})
    
    def get_title(prop):
        title = prop.get("title", [])
        return title[0]["plain_text"] if title else ""
    
    def get_select(prop):
        select = prop.get("select")
        return select["name"] if select else None
    
    def get_date(prop):
        date = prop.get("date")
        return date["start"] if date else None
    
    def get_rich_text(prop):
        text = prop.get("rich_text", [])
        return text[0]["plain_text"] if text else ""
    
    result = {
        "id": page.get("id"),
        "created_time": page.get("created_time"),
        "last_edited_time": page.get("last_edited_time"),
    }
    
    for key, prop in props.items():
        key_lower = key.lower().replace(" ", "_")
        prop_type = prop.get("type")
        
        if prop_type == "title":
            result["title"] = get_title(prop)
        elif prop_type == "select":
            result[key_lower] = get_select(prop)
        elif prop_type == "date":
            result[key_lower] = get_date(prop)
        elif prop_type == "rich_text":
            result[key_lower] = get_rich_text(prop)
        elif prop_type == "url":
            result[key_lower] = prop.get("url")
        elif prop_type == "checkbox":
            result[key_lower] = prop.get("checkbox", False)
        elif prop_type == "multi_select":
            result[key_lower] = [s["name"] for s in prop.get("multi_select", [])]
    
    return result


def run_content_agent(result: AgentResult):
    """Main agent logic."""
    now = now_cairo()
    today = now.strftime("%Y-%m-%d")
    week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    week_end = (now + timedelta(days=6-now.weekday())).strftime("%Y-%m-%d")
    
    print("  Fetching Notion Content Calendar DB...")
    pages = fetch_notion_db(CONTENT_DB_ID)
    print(f"  Found {len(pages)} content items")
    
    posts = []
    by_status = {"idea": [], "outline": [], "draft": [], "scheduled": [], "posted": [], "published": []}
    today_scheduled = []
    this_week_posts = []
    topics_covered = {}
    
    # Status normalization mapping
    status_map = {
        "idea": "idea",
        "ideas": "idea",
        "outline": "outline",
        "outlined": "outline",
        "draft": "draft",
        "drafted": "draft",
        "in progress": "draft",
        "scheduled": "scheduled",
        "ready": "scheduled",
        "posted": "posted",
        "published": "posted",
        "done": "posted"
    }
    
    for page in pages:
        post = parse_notion_page(page)
        posts.append(post)
        
        # Normalize status
        raw_status = (post.get("status") or "").lower()
        status = status_map.get(raw_status, raw_status)
        if status in by_status:
            by_status[status].append(post)
        
        # Check planned date
        planned_date = post.get("planned_date") or post.get("date") or post.get("publish_date")
        if planned_date:
            # Today's posts
            if planned_date == today:
                today_scheduled.append({
                    "title": post.get("title", "Untitled"),
                    "status": status,
                    "topic": post.get("topic"),
                    "hook": post.get("hook", "")[:100] if post.get("hook") else ""
                })
            
            # This week's posts (scheduled or posted)
            if week_start <= planned_date <= week_end:
                this_week_posts.append({
                    "title": post.get("title", "Untitled"),
                    "date": planned_date,
                    "status": status
                })
        
        # Track topics
        topic = post.get("topic") or post.get("category") or "General"
        if isinstance(topic, list):
            for t in topic:
                topics_covered[t] = topics_covered.get(t, 0) + 1
        else:
            topics_covered[topic] = topics_covered.get(topic, 0) + 1
    
    # Calculate content runway (days until scheduled content runs out)
    future_scheduled = [
        p for p in by_status["scheduled"]
        if (p.get("planned_date") or p.get("date") or "") >= today
    ]
    runway_days = len(future_scheduled)  # Assuming 1 post per day target
    
    # Calculate posting streak (consecutive days with posts)
    posted_dates = set()
    for p in by_status["posted"]:
        date = p.get("planned_date") or p.get("date") or p.get("publish_date")
        if date:
            posted_dates.add(date)
    
    streak = 0
    check_date = now
    while check_date.strftime("%Y-%m-%d") in posted_dates:
        streak += 1
        check_date -= timedelta(days=1)
        if streak > 365:  # Safety limit
            break
    
    # Posts this month
    month_start = now.replace(day=1).strftime("%Y-%m-%d")
    posts_this_month = len([
        p for p in by_status["posted"]
        if (p.get("planned_date") or p.get("date") or "") >= month_start
    ])
    
    # Load engagement opportunities from coordination file
    engagement_opportunities = []
    coord_data = load_json(COORDINATION_CALENDAR)
    if coord_data:
        # Check for any engagement items in coordination calendar
        for item in coord_data.get("scheduled", []):
            if item.get("status") == "engagement" or "comment" in (item.get("topic") or "").lower():
                engagement_opportunities.append({
                    "topic": item.get("topic"),
                    "date": item.get("date"),
                    "notes": item.get("notes", "")
                })
    
    # Pipeline summary
    pipeline = {
        "ideas": len(by_status["idea"]),
        "outlines": len(by_status["outline"]),
        "drafts": len(by_status["draft"]),
        "scheduled": len(by_status["scheduled"]),
        "posted": len(by_status["posted"])
    }
    
    # Build data
    result.set_data({
        "scan_time": now_iso(),
        "today": {
            "date": today,
            "scheduled": today_scheduled,
            "count": len(today_scheduled)
        },
        "this_week": {
            "start": week_start,
            "end": week_end,
            "posts": this_week_posts,
            "count": len(this_week_posts)
        },
        "pipeline": pipeline,
        "content_health": {
            "runway_days": runway_days,
            "streak_days": streak,
            "posts_this_month": posts_this_month,
            "topics_covered": dict(sorted(topics_covered.items(), key=lambda x: -x[1])[:10])
        },
        "drafts_ready_for_review": [
            {"title": p.get("title"), "topic": p.get("topic")}
            for p in by_status["draft"][:5]
        ],
        "engagement_opportunities": engagement_opportunities
    })
    
    # KPIs
    result.set_kpi({
        "posting_consistency": round(posts_this_month / max(now.day, 1) * 100, 1),  # % of days with posts
        "content_runway_days": runway_days,
        "drafts_in_review": len(by_status["draft"]),
        "streak_days": streak,
        "posts_this_month": posts_this_month
    })
    
    # Recommendations
    if runway_days < 3:
        result.add_recommendation(
            action="create_content",
            target="Content pipeline",
            reason=f"Only {runway_days} days of scheduled content remaining",
            urgency="high"
        )
    
    if not today_scheduled:
        result.add_recommendation(
            action="schedule_post",
            target="Today's content",
            reason="No post scheduled for today",
            urgency="medium"
        )
    
    if len(by_status["draft"]) > 3:
        result.add_recommendation(
            action="review_drafts",
            target=f"{len(by_status['draft'])} pending drafts",
            reason="Drafts accumulating - review and publish",
            urgency="medium"
        )
    
    if streak == 0:
        result.add_recommendation(
            action="post_today",
            target="Posting streak",
            reason="No active posting streak - post today to start one",
            urgency="low"
        )


if __name__ == "__main__":
    agent_main(
        agent_name="content-agent",
        run_func=run_content_agent,
        output_path=OUTPUT_PATH,
        ttl_hours=6,
        version="1.0.0"
    )
