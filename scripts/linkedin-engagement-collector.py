#!/usr/bin/env python3
"""
linkedin-engagement-collector.py - Scrapes LinkedIn profile activity page
to collect post engagement data (reactions, comments) using Playwright.

Output: data/linkedin-engagement.json
Updates: Notion Content Calendar with engagement metrics

Requires: playwright, LinkedIn cookies
"""
import os, time
import json, re, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
OUTPUT_FILE = DATA_DIR / "linkedin-engagement.json"
COOKIE_CONFIG = Path("/root/.openclaw/workspace/config/linkedin-cookies.json")
COOKIE_FILE_FALLBACK = Path("/root/.openclaw/media/inbound/www.linkedin.com_cookies---c22104a1-b837-4ea4-b22f-29275813363b.txt")
NOTION_TOKEN = json.load(open(os.path.expanduser("~/.openclaw/workspace/config/notion.json")))["token"]
CONTENT_DB = "3268d599-a162-814b-8854-c9b8bde62468"
CAIRO = timezone(timedelta(hours=2))
MAX_COOKIE_AGE_HOURS = 72  # Hard-fail if cookies older than this


def get_cookie_path():
    """Get LinkedIn cookie file path from config or fallback."""
    if COOKIE_CONFIG.exists():
        try:
            cfg = json.load(open(COOKIE_CONFIG))
            path = Path(cfg.get("cookie_file", str(COOKIE_FILE_FALLBACK)))
            if path.exists():
                return path
        except:
            pass
    if COOKIE_FILE_FALLBACK.exists():
        return COOKIE_FILE_FALLBACK
    return None


def check_cookie_freshness(cookie_path):
    """Check cookie file age. Warn >24h, fail >72h."""
    import os
    mtime = os.path.getmtime(cookie_path)
    age_hours = (time.time() - mtime) / 3600
    if age_hours > MAX_COOKIE_AGE_HOURS:
        print(f"ERROR: LinkedIn cookies are {age_hours:.0f}h old (max {MAX_COOKIE_AGE_HOURS}h). Re-export cookies.")
        return False, age_hours
    if age_hours > 24:
        print(f"WARNING: LinkedIn cookies are {age_hours:.0f}h old. Consider refreshing soon.")
    return True, age_hours


def scrape_engagement():
    """Scrape LinkedIn activity page via Camofox (uses pre-imported cookies)."""
    import subprocess

    # Check cookie freshness
    cookie_path = get_cookie_path()
    if cookie_path:
        ok, age = check_cookie_freshness(cookie_path)
        if not ok:
            return []
        print(f"Cookie age: {age:.0f}h")
    
    url = "https://www.linkedin.com/in/ahmednasr/recent-activity/all/"
    
    try:
        # Open tab via Camofox
        result = subprocess.run(
            ["camofox-browser", "open", url],
            capture_output=True, text=True, timeout=30
        )
        tab_id = ""
        try:
            data = json.loads(result.stdout)
            tab_id = data.get("tabId", "")
        except:
            if "tabId:" in result.stdout:
                tab_id = result.stdout.strip().split("tabId:")[-1].strip()
        
        if not tab_id:
            print("ERROR: Could not get Camofox tab ID")
            return []
        
        time.sleep(6)  # Wait for initial load
        
        # Scroll 5 times to load more posts
        for i in range(5):
            subprocess.run(
                ["camofox-browser", "scroll", tab_id, "down", "2000"],
                capture_output=True, timeout=10
            )
            time.sleep(2)
        
        # Get snapshot
        result = subprocess.run(
            ["camofox-browser", "snapshot", tab_id],
            capture_output=True, text=True, timeout=30
        )
        content = result.stdout
        
        # Close tab
        subprocess.run(["camofox-browser", "close", tab_id], capture_output=True, timeout=10)
        
        if not content or len(content) < 200:
            print("ERROR: Empty snapshot from Camofox. Cookies may be expired.")
            return []
        
        # Parse snapshot text for post data
        posts = parse_activity_snapshot(content)
        print(f"Scraped {len(posts)} posts via Camofox")
        return posts
        
    except subprocess.TimeoutExpired:
        print("ERROR: Camofox timeout")
        return []
    except Exception as e:
        print(f"ERROR: Camofox scrape failed: {e}")
        return []


def parse_activity_snapshot(content):
    """Parse Camofox accessibility snapshot into post data."""
    posts = []
    lines = content.split("\n")
    
    current_post = None
    for line in lines:
        stripped = line.strip()
        
        # Look for activity URN patterns
        urn_match = re.search(r'urn:li:activity:(\d+)', stripped)
        if urn_match:
            if current_post and current_post.get("urn"):
                posts.append(current_post)
            current_post = {
                "urn": f"urn:li:activity:{urn_match.group(1)}",
                "text": "",
                "reactions": 0,
                "comments": 0,
                "time": ""
            }
            continue
        
        if current_post:
            # Extract reaction/comment counts from text
            reaction_match = re.search(r'(\d+)\s*reaction', stripped, re.IGNORECASE)
            comment_match = re.search(r'(\d+)\s*comment', stripped, re.IGNORECASE)
            if reaction_match:
                current_post["reactions"] = max(current_post["reactions"], int(reaction_match.group(1)))
            if comment_match:
                current_post["comments"] = max(current_post["comments"], int(comment_match.group(1)))
            
            # Capture post text (substantive lines)
            if len(stripped) > 30 and not any(skip in stripped.lower() for skip in [
                "like", "comment", "repost", "send", "follow", "connect",
                "reaction", "more actions"
            ]):
                if not current_post["text"]:
                    current_post["text"] = stripped[:500]
    
    # Don't forget the last post
    if current_post and current_post.get("urn"):
        posts.append(current_post)
    
    return posts


def load_notion_posts():
    """Load posted content from Notion Content Calendar."""
    import ssl
    from urllib.request import Request, urlopen
    
    body = {
        "filter": {"property": "Status", "select": {"equals": "Posted"}},
        "page_size": 50,
        "sorts": [{"property": "Planned Date", "direction": "descending"}]
    }
    headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
    req = Request(f"https://api.notion.com/v1/databases/{CONTENT_DB}/query",
                  data=json.dumps(body).encode(), headers=headers, method="POST")
    with urlopen(req, context=ssl.create_default_context()) as r:
        data = json.loads(r.read())
    
    posts = []
    for page in data.get("results", []):
        props = page.get("properties", {})
        title = (props.get("Title", {}).get("title", [{}])[0].get("plain_text", "") 
                 if props.get("Title", {}).get("title") else "")
        date = props.get("Planned Date", {}).get("date", {})
        post_url = ""
        for key in ["Post URL"]:
            if key in props and props[key].get("url"):
                post_url = props[key]["url"]
                break
        
        # Extract topic/hook
        hook = (props.get("Hook", {}).get("rich_text", [{}])[0].get("plain_text", "")
                if props.get("Hook", {}).get("rich_text") else "")
        topic = ""
        if "Topic" in props:
            sel = props["Topic"].get("select", {})
            topic = sel.get("name", "") if sel else ""
        
        posts.append({
            "page_id": page["id"],
            "title": title,
            "hook": hook,
            "topic": topic,
            "date": date.get("start", "") if date else "",
            "post_url": post_url,
        })
    
    return posts


def match_posts(scraped, notion_posts):
    """Match scraped posts to Notion entries by text similarity or URL."""
    from difflib import SequenceMatcher
    
    matched = []
    for sp in scraped:
        best_match = None
        best_score = 0
        
        # Try URL match first
        for np in notion_posts:
            if np["post_url"] and sp["urn"]:
                # Extract activity ID from URN
                urn_id = sp["urn"].split(":")[-1]
                if urn_id in np["post_url"]:
                    best_match = np
                    best_score = 1.0
                    break
        
        # Try text match
        if not best_match and sp["text"]:
            for np in notion_posts:
                # Compare scraped text with Notion title/hook
                compare_text = np["title"] + " " + np.get("hook", "")
                score = SequenceMatcher(None, sp["text"][:100].lower(), compare_text[:100].lower()).ratio()
                if score > best_score and score > 0.5:
                    best_score = score
                    best_match = np
        
        entry = {
            "urn": sp["urn"],
            "reactions": sp["reactions"],
            "comments": sp["comments"],
            "engagement": sp["reactions"] + sp["comments"],
            "text_preview": sp["text"][:100],
            "time": sp["time"],
        }
        
        if best_match:
            entry["notion_page_id"] = best_match["page_id"]
            entry["title"] = best_match["title"]
            entry["hook"] = best_match.get("hook", "")
            entry["topic"] = best_match.get("topic", "")
            entry["date"] = best_match.get("date", "")
            entry["match_score"] = round(best_score, 2)
        
        matched.append(entry)
    
    return matched


def analyze_patterns(matched):
    """Analyze engagement patterns across posts."""
    if len(matched) < 3:
        return {"error": "Not enough posts to analyze", "post_count": len(matched)}
    
    # Sort by engagement
    by_engagement = sorted(matched, key=lambda x: x["engagement"], reverse=True)
    
    # Basic stats
    engagements = [m["engagement"] for m in matched]
    avg_engagement = sum(engagements) / len(engagements)
    
    # Top vs bottom performers
    top = by_engagement[:3]
    bottom = by_engagement[-3:]
    
    # Text length analysis
    with_text = [m for m in matched if m.get("text_preview")]
    avg_text_len = sum(len(m["text_preview"]) for m in with_text) / max(1, len(with_text))
    
    return {
        "post_count": len(matched),
        "avg_engagement": round(avg_engagement, 1),
        "max_engagement": max(engagements),
        "min_engagement": min(engagements),
        "top_3": [{"title": t.get("title", t.get("text_preview", "?"))[:50], "engagement": t["engagement"], "reactions": t["reactions"], "comments": t["comments"]} for t in top],
        "bottom_3": [{"title": t.get("title", t.get("text_preview", "?"))[:50], "engagement": t["engagement"]} for t in bottom],
        "avg_text_length": round(avg_text_len),
        "collected_at": datetime.now(CAIRO).isoformat(),
    }


def main():
    print("=== LinkedIn Engagement Collector ===")
    print(f"Time: {datetime.now(CAIRO).strftime('%Y-%m-%d %H:%M')}")
    
    # Step 1: Scrape engagement data
    print("\n--- Scraping LinkedIn activity page ---")
    scraped = scrape_engagement()
    
    if not scraped:
        print("ERROR: No posts scraped. Cookies may be expired.")
        sys.exit(1)
    
    # Step 2: Load Notion posts
    print("\n--- Loading Notion Content Calendar ---")
    notion_posts = load_notion_posts()
    print(f"Notion posts: {len(notion_posts)}")
    
    # Step 3: Match scraped to Notion
    print("\n--- Matching posts ---")
    matched = match_posts(scraped, notion_posts)
    matched_count = sum(1 for m in matched if m.get("notion_page_id"))
    print(f"Matched: {matched_count}/{len(matched)}")
    
    # Step 4: Analyze patterns
    print("\n--- Analyzing patterns ---")
    analysis = analyze_patterns(matched)
    
    # Step 5: Save output
    output = {
        "collected_at": datetime.now(CAIRO).isoformat(),
        "posts": matched,
        "analysis": analysis,
    }
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {OUTPUT_FILE}")
    
    # Print summary
    print(f"\n=== Summary ===")
    print(f"Posts: {len(matched)}")
    print(f"Avg engagement: {analysis.get('avg_engagement', 0)}")
    print(f"Top post: {analysis.get('top_3', [{}])[0].get('title', '?')[:40]} ({analysis.get('top_3', [{}])[0].get('engagement', 0)} reactions+comments)")
    
    return output


if __name__ == "__main__":
    main()
