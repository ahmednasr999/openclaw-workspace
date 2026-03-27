#!/usr/bin/env python3
"""
LinkedIn Post Pre-Flight Check
Runs at 9:00 AM Cairo (30 min before auto-poster).
Checks today's Notion post is ready to go.
Alerts on Telegram if issues found.
"""

import json, os, sys, urllib.request, ssl, subprocess
from datetime import datetime, timezone, timedelta

CAIRO = timezone(timedelta(hours=2))
TODAY = datetime.now(CAIRO).strftime("%Y-%m-%d")
DOW = datetime.now(CAIRO).strftime("%A")

# Skip Fri/Sat (no posting days)
if DOW in ("Friday", "Saturday"):
    print(f"[{TODAY}] {DOW} - no post scheduled. Skipping.")
    sys.exit(0)

NOTION_TOKEN = json.load(open(os.path.expanduser("~/.openclaw/workspace/config/notion.json")))["token"]
DB_ID = "3268d599-a162-814b-8854-c9b8bde62468"
TELEGRAM_CHAT = "-1003882622947:7"  # CMO Desk (topic 7) in Nasr Command Center
DRY_RUN = "--dry-run" in sys.argv


def notion_req(method, path, body=None):
    url = f"https://api.notion.com/v1{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    })
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read())


def send_alert(msg):
    """Send Telegram alert via OpenClaw CLI."""
    if DRY_RUN:
        print(f"[DRY RUN] Would alert: {msg}")
        return
    try:
        subprocess.run(
            ["openclaw", "telegram", "send", "--to", TELEGRAM_CHAT, "--message", msg],
            timeout=15, capture_output=True
        )
    except Exception as e:
        print(f"Telegram alert failed: {e}")


def check():
    issues = []
    
    # 1. Find today's post
    result = notion_req("POST", f"/databases/{DB_ID}/query", {
        "filter": {"and": [
            {"property": "Planned Date", "date": {"equals": TODAY}}
        ]},
        "page_size": 1
    })
    
    if not result.get("results"):
        issues.append("No post found in Notion calendar for today")
        return issues
    
    page = result["results"][0]
    pid = page["id"]
    props = page["properties"]
    
    title = "".join(t.get("plain_text", "") for t in props.get("Title", {}).get("title", []))
    status = props.get("Status", {}).get("select", {})
    status_name = status.get("name", "?") if status else "?"
    
    print(f"Post: {title[:60]}")
    print(f"Status: {status_name}")
    
    # 2. Check status
    if status_name != "Scheduled":
        issues.append(f"Status is '{status_name}' (not 'Scheduled')")
    
    # 3. Check content
    blocks = notion_req("GET", f"/blocks/{pid}/children?page_size=100")
    text_blocks = []
    has_image = False
    
    for b in blocks.get("results", []):
        bt = b["type"]
        if bt == "image":
            has_image = True
            # Check if image URL is accessible
            img = b["image"]
            img_url = img.get("external", {}).get("url") or img.get("file", {}).get("url", "")
            if img_url:
                try:
                    req = urllib.request.Request(img_url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
                    ctx = ssl.create_default_context()
                    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
                        if r.status != 200:
                            issues.append(f"Image URL returns HTTP {r.status}")
                except Exception as e:
                    issues.append(f"Image URL unreachable: {str(e)[:60]}")
        elif bt in ("paragraph", "heading_2", "heading_3"):
            rt = b.get(bt, {}).get("rich_text", [])
            text = "".join(t.get("plain_text", "") for t in rt)
            if text.strip():
                text_blocks.append(text)
    
    total_text = "\n".join(text_blocks)
    print(f"Content: {len(total_text)} chars, {len(text_blocks)} text blocks")
    print(f"Image: {'yes' if has_image else 'no'}")
    
    # 4. Content quality checks
    if len(total_text) < 200:
        issues.append(f"Content too thin ({len(total_text)} chars, minimum 200)")
    
    if not has_image:
        issues.append("No image attached")
    
    if not any(tag in total_text for tag in ["#", "DM", "comment", "share"]):
        issues.append("Missing hashtags or CTA")
    
    return issues


# Run
print(f"=== LinkedIn Pre-Flight Check - {TODAY} ({DOW}) ===\n")
issues = check()

if issues:
    print(f"\n⚠️ {len(issues)} issue(s) found:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
    
    alert_msg = f"⚠️ LinkedIn Pre-Flight ({TODAY})\n\n"
    for issue in issues:
        alert_msg += f"- {issue}\n"
    alert_msg += "\nPost may fail or underperform at 9:30 AM."
    send_alert(alert_msg)
else:
    print("\n✅ All clear. Post is ready for 9:30 AM.")
