#!/usr/bin/env python3
"""
LinkedIn Comment Radar - Daily engagement pipeline.
Uses Google search to find fresh GCC LinkedIn posts worth commenting on.
Saves to memory/engagement/ for briefing integration.

NOTE: This script prepares the search queries and scoring logic.
The actual search is done by the cron agent using camofox or web_search tools.
Output: JSON file with top picks for the briefing.
"""

import json
import os
import re
from datetime import datetime, timezone, timedelta

CAIRO = timezone(timedelta(hours=2))
TODAY = datetime.now(CAIRO).strftime("%Y-%m-%d")
ENGAGEMENT_DIR = "/root/.openclaw/workspace/memory/engagement"
TRACKER_FILE = f"{ENGAGEMENT_DIR}/comment-tracker.json"
DAILY_FILE = f"{ENGAGEMENT_DIR}/{TODAY}-radar.json"

# Search queries for the agent to run
SEARCH_QUERIES = [
    'site:linkedin.com/posts "digital transformation" (UAE OR Saudi OR GCC) -jobs -hiring',
    'site:linkedin.com/posts "program management" OR "PMO" (Dubai OR Riyadh OR Qatar) -hiring',
    'site:linkedin.com/posts "AI" OR "artificial intelligence" (Saudi OR UAE OR MENA) executive -jobs',
    'site:linkedin.com/posts "healthcare technology" OR "healthtech" (GCC OR Middle East) -hiring',
    'site:linkedin.com/posts "leadership" OR "C-suite" (Dubai OR Riyadh OR Jeddah) -jobs',
]

GCC_KEYWORDS = ["saudi", "uae", "dubai", "riyadh", "qatar", "bahrain", "kuwait", 
                "oman", "gcc", "mena", "jeddah", "abu dhabi", "doha"]

def load_tracker():
    os.makedirs(ENGAGEMENT_DIR, exist_ok=True)
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE) as f:
            return json.load(f)
    return {"daily_comments": {}, "total_comments": 0, "streak_days": 0, "last_comment_date": None}

def save_tracker(tracker):
    with open(TRACKER_FILE, "w") as f:
        json.dump(tracker, f, indent=2)

def record_comment(post_url, comment_text=""):
    """Call this when Ahmed posts a comment. Updates tracker."""
    tracker = load_tracker()
    today = datetime.now(CAIRO).strftime("%Y-%m-%d")
    
    if today not in tracker["daily_comments"]:
        tracker["daily_comments"][today] = {"count": 0, "posts": []}
    
    tracker["daily_comments"][today]["count"] += 1
    tracker["daily_comments"][today]["posts"].append({
        "url": post_url,
        "text": comment_text[:200],
        "time": datetime.now(CAIRO).isoformat()
    })
    tracker["total_comments"] += 1
    
    # Update streak
    yesterday = (datetime.now(CAIRO) - timedelta(days=1)).strftime("%Y-%m-%d")
    if tracker.get("last_comment_date") == yesterday or tracker.get("last_comment_date") == today:
        if tracker.get("last_comment_date") != today:
            tracker["streak_days"] += 1
    else:
        tracker["streak_days"] = 1
    tracker["last_comment_date"] = today
    
    save_tracker(tracker)
    return tracker["daily_comments"][today]["count"]

def get_today_stats():
    """Get engagement stats for briefing."""
    tracker = load_tracker()
    today = datetime.now(CAIRO).strftime("%Y-%m-%d")
    today_data = tracker["daily_comments"].get(today, {"count": 0, "posts": []})
    
    # Load radar results if available
    radar_picks = 0
    if os.path.exists(DAILY_FILE):
        with open(DAILY_FILE) as f:
            radar = json.load(f)
            radar_picks = len(radar.get("top_picks", []))
    
    return {
        "comments_today": today_data["count"],
        "goal": 5,
        "streak": tracker.get("streak_days", 0),
        "total_comments": tracker.get("total_comments", 0),
        "radar_picks": radar_picks,
        "on_track": today_data["count"] >= 3,
    }

if __name__ == "__main__":
    print(f"=== Comment Radar Stats - {TODAY} ===")
    stats = get_today_stats()
    print(json.dumps(stats, indent=2))
    print(f"\nSearch queries for agent:")
    for i, q in enumerate(SEARCH_QUERIES, 1):
        print(f"  {i}. {q}")
