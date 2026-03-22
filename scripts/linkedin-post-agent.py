#!/usr/bin/env python3
"""
LinkedIn Post Agent - Fetches today's scheduled post from Notion Content Calendar.
Outputs data/linkedin-post.json for the briefing runner.
"""
import os
import json, re, ssl, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
OUTPUT = DATA_DIR / "linkedin-post.json"
NOTION_TOKEN = json.load(open(os.path.expanduser("~/.openclaw/workspace/config/notion.json")))["token"]
CONTENT_DB = "3268d599-a162-814b-8854-c9b8bde62468"
CAIRO = timezone(timedelta(hours=2))


def notion_request(method, endpoint, body=None):
    """Make a Notion API request."""
    url = f"https://api.notion.com/v1{endpoint}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    data = json.dumps(body).encode() if body else None
    req = Request(url, data=data, headers=headers, method=method)
    ctx = ssl.create_default_context()
    try:
        with urlopen(req, timeout=15, context=ctx) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  Notion error: {e}")
        return {}


def get_page_blocks(page_id):
    """Get content blocks from a Notion page."""
    result = notion_request("GET", f"/blocks/{page_id}/children?page_size=100")
    blocks = result.get("results", [])
    text_parts = []
    image_url = None
    
    for block in blocks:
        btype = block.get("type", "")
        
        # Extract text from various block types
        if btype in ("paragraph", "bulleted_list_item", "numbered_list_item", "heading_1", "heading_2", "heading_3"):
            rich_text = block.get(btype, {}).get("rich_text", [])
            line = "".join(rt.get("plain_text", "") for rt in rich_text)
            if line.strip():
                text_parts.append(line)
        
        # Extract image
        elif btype == "image":
            img = block.get("image", {})
            if img.get("type") == "external":
                image_url = img.get("external", {}).get("url")
            elif img.get("type") == "file":
                image_url = img.get("file", {}).get("url")
    
    return "\n".join(text_parts), image_url


def fetch_todays_post():
    """Fetch today's scheduled post from Content Calendar."""
    today = datetime.now(CAIRO).strftime("%Y-%m-%d")
    print(f"📝 LinkedIn Post Agent - Looking for {today}")
    
    # Query for today's scheduled or drafted posts
    body = {
        "filter": {
            "and": [
                {"property": "Planned Date", "date": {"equals": today}},
                {"or": [
                    {"property": "Status", "select": {"equals": "Scheduled"}},
                    {"property": "Status", "select": {"equals": "Drafted"}},
                ]}
            ]
        },
        "page_size": 1,
    }
    
    result = notion_request("POST", f"/databases/{CONTENT_DB}/query", body)
    pages = result.get("results", [])
    
    if not pages:
        print("  No post scheduled for today")
        # Check for next upcoming
        body_next = {
            "filter": {
                "and": [
                    {"property": "Planned Date", "date": {"after": today}},
                    {"or": [
                        {"property": "Status", "select": {"equals": "Scheduled"}},
                        {"property": "Status", "select": {"equals": "Drafted"}},
                    ]}
                ]
            },
            "sorts": [{"property": "Planned Date", "direction": "ascending"}],
            "page_size": 1,
        }
        result_next = notion_request("POST", f"/databases/{CONTENT_DB}/query", body_next)
        next_pages = result_next.get("results", [])
        
        next_info = {}
        if next_pages:
            np = next_pages[0]
            next_date = np.get("properties", {}).get("Planned Date", {}).get("date", {}).get("start", "?")
            next_title_parts = np.get("properties", {}).get("Title", {}).get("title", [])
            if not next_title_parts:
                next_title_parts = np.get("properties", {}).get("Name", {}).get("title", [])
            next_title = "".join(p.get("plain_text", "") for p in next_title_parts) if next_title_parts else "Untitled"
            next_info = {"date": next_date, "title": next_title}
        
        output = {
            "generated": datetime.now(timezone.utc).isoformat(),
            "today": today,
            "has_post": False,
            "next_scheduled": next_info,
            "status": "no_post_today",
        }
        json.dump(output, open(OUTPUT, "w"), indent=2)
        return
    
    page = pages[0]
    page_id = page["id"]
    props = page.get("properties", {})
    
    # Get title
    title_parts = props.get("Title", {}).get("title", [])
    if not title_parts:
        title_parts = props.get("Name", {}).get("title", [])
    title = "".join(p.get("plain_text", "") for p in title_parts) if title_parts else "Untitled"
    
    # Get hook
    hook_parts = props.get("Hook", {}).get("rich_text", [])
    hook = "".join(p.get("plain_text", "") for p in hook_parts) if hook_parts else ""
    
    # Get topic
    topic = props.get("Topic", {}).get("select", {}).get("name", "") if props.get("Topic", {}).get("select") else ""
    
    # Get status
    status = props.get("Status", {}).get("select", {}).get("name", "?")
    
    # Get full post text and image from page body
    post_text, image_url = get_page_blocks(page_id)
    
    print(f"  Found: \"{title}\" ({status})")
    if image_url:
        print(f"  Image: {image_url[:60]}...")
    
    output = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "today": today,
        "has_post": True,
        "post": {
            "title": title,
            "hook": hook,
            "topic": topic,
            "status": status,
            "text": post_text[:3000],
            "image_url": image_url,
            "notion_page_id": page_id,
            "notion_url": page.get("url", ""),
        },
        "status": "ok",
    }
    
    json.dump(output, open(OUTPUT, "w"), indent=2)
    print(f"✅ Saved to {OUTPUT}")


if __name__ == "__main__":
    fetch_todays_post()
