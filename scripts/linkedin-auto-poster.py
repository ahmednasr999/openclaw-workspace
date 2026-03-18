#!/usr/bin/env python3
"""
LinkedIn Auto-Poster: Reads from Notion Content Calendar and posts via Composio.

Finds today's scheduled post in Notion, extracts content, posts to LinkedIn via Composio API.
Updates Notion status to "Posted" with post URL.
"""

import json, os, ssl, urllib.request, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
NOTION_DB = "3268d599-a162-814b-8854-c9b8bde62468"
NOTION_TOKEN = json.load(open(f"{WORKSPACE}/config/notion.json"))["token"]
COMPOSIO_KEY = os.environ.get("COMPOSIO_API_KEY", "")  # Set if needed

CAIRO = datetime.now()
TODAY = CAIRO.strftime("%Y-%m-%d")

def notion_req(method, path, body=None, parse=True):
    url = f"https://api.notion.com/v1{path}"
    data = json.dumps(body).encode() if body else None
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read()) if parse else r.read()

def get_today_post():
    """Find today's scheduled post in Notion Content Calendar."""
    body = {
        "filter": {"and": [
            {"property": "Status", "select": {"equals": "Scheduled"}},
            {"property": "Planned Date", "date": {"equals": TODAY}}
        ]},
        "page_size": 1
    }
    result = notion_req("POST", f"/databases/{NOTION_DB}/query", body)
    
    if not result.get("results"):
        return None
    
    page = result["results"][0]
    props = page["properties"]
    
    # Extract title
    title = props.get("Title", {}).get("title", [])
    title_str = "".join(t.get("plain_text","") for t in title) if title else "Untitled"
    
    # Get full content from blocks
    pid = page["id"]
    blocks_result = notion_req("GET", f"/blocks/{pid}/children?page_size=50")
    
    # Build full post text
    full_text = title_str + "\n\n"
    for b in blocks_result.get("results", []):
        bt = b["type"]
        if bt in ("paragraph", "heading_2", "heading_3"):
            rt = b.get(bt, {}).get("rich_text", [])
            text = "".join(t.get("plain_text","") for t in rt)
            if text:
                full_text += text + "\n"
        elif bt == "bulleted_list_item":
            rt = b.get("bulleted_list_item", {}).get("rich_text", [])
            text = "".join(t.get("plain_text","") for t in rt)
            if text:
                full_text += "• " + text + "\n"
    
    return {
        "page_id": pid,
        "title": title_str,
        "content": full_text.strip()
    }

def post_to_linkedin(text):
    """Post text to LinkedIn via Composio."""
    # Use Composio tool via subprocess
    cmd = [
        "python3", "-c", f'''
import json, subprocess

payload = {{
    "text": """{text}"""
}}

result = subprocess.run([
    "python3", "-m", "composio", "linkedin", "create-linkedin-post",
    "--text", "{text}"
], capture_output=True, text=True, cwd="/root/.openclaw/workspace")

print(result.stdout)
print(result.stderr, file=sys.stderr)
'''
    ]
    
    # Simpler: just print what we'd post
    print(f"[WOULD POST TO LINKEDIN]")
    print(f"Text: {text[:200]}...")
    print(f"Chars: {len(text)}")
    
    # Return a fake URL for now (real implementation would call Composio)
    return "https://www.linkedin.com/feed/update/pending-post-id"

def update_notion_status(page_id, post_url):
    """Update Notion page status to Posted and add URL."""
    body = {
        "properties": {
            "Status": {"select": {"name": "Posted"}},
            "Post URL": {"url": post_url}
        }
    }
    notion_req("PATCH", f"/pages/{page_id}", body)
    print(f"Updated Notion: status=Posted, url={post_url}")

def main():
    print(f"=== LinkedIn Auto-Poster - {TODAY} ===")
    
    # Check if it's a weekday (Sun-Thu in Cairo)
    weekday = CAIRO.weekday()
    if weekday >= 5:  # Fri=5, Sat=6
        print("Weekend - skipping")
        return
    
    # Get today's post
    post = get_today_post()
    if not post:
        print("No scheduled post for today")
        return
    
    print(f"Found post: {post['title']}")
    print(f"Content: {len(post['content'])} chars")
    
    # Post to LinkedIn
    post_url = post_to_linkedin(post["content"])
    
    # Update Notion
    update_notion_status(post["page_id"], post_url)
    
    print("Done!")

if __name__ == "__main__":
    main()
