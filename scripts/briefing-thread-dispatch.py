#!/usr/bin/env python3
"""
Post briefing section summaries to their matching Telegram forum threads.
Run after morning-briefing-orchestrator.py completes.

Thread mapping (Nasr Command Center forum):
  Topic 6  = Jobs thread
  Topic 7  = LinkedIn/Content thread
  Topic 10 = General/System thread
  Topic 32 = CRM/Networking thread  
  Topic 52 = X/Twitter thread
"""

import json, os, sys, re, ssl, urllib.request

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
NOTION_CONFIG = f"{WORKSPACE}/config/notion.json"
BOT_TOKEN = "8213291111:AAHCk2J4XIRQaTsBkACl_Xpla7LFvVx1304"
CHAT_ID = "-1003882622947"
ctx = ssl.create_default_context()

# Thread mapping
THREADS = {
    "jobs": 6,
    "content": 7,
    "general": 10,
    "crm": 32,
    "twitter": 52,
}

def send_to_thread(topic_id, text, parse_mode="HTML"):
    """Send a message to a specific forum thread."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = json.dumps({
        "chat_id": CHAT_ID,
        "message_thread_id": topic_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }).encode()
    req = urllib.request.Request(url, data=payload, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ❌ Failed to send to topic {topic_id}: {e}")
        return None

def load_notion_token():
    with open(NOTION_CONFIG) as f:
        return json.load(f)["token"]

def get_briefing_page_id(date_str):
    """Find today's briefing page in Notion."""
    token = load_notion_token()
    url = "https://api.notion.com/v1/databases/3268d599-a162-812d-a59e-e5496dec80e7/query"
    body = json.dumps({"filter": {"property": "Name", "title": {"contains": date_str}}}).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            data = json.loads(r.read())
            results = data.get("results", [])
            if results:
                return results[0]["id"]
    except:
        pass
    return None

def get_page_blocks(page_id):
    """Get all blocks from a Notion page."""
    token = load_notion_token()
    blocks = []
    cursor = None
    while True:
        path = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
        if cursor:
            path += f"&start_cursor={cursor}"
        req = urllib.request.Request(path, method="GET", headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28"
        })
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            data = json.loads(r.read())
            blocks.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
    return blocks

def extract_text(block):
    """Extract plain text from a Notion block."""
    btype = block.get("type", "")
    content = block.get(btype, {})
    rich_text = content.get("rich_text", [])
    return "".join(rt.get("text", {}).get("content", "") or rt.get("plain_text", "") for rt in rich_text)

def parse_briefing_sections(blocks):
    """Parse blocks into sections based on headings."""
    sections = {}
    current_section = None
    current_lines = []
    
    for b in blocks:
        btype = b.get("type", "")
        text = extract_text(b)
        
        if btype in ("heading_2",):
            if current_section and current_lines:
                sections[current_section] = current_lines
            current_section = text
            current_lines = []
        elif current_section:
            if btype == "divider":
                continue
            if text.strip():
                current_lines.append(text.strip())
    
    if current_section and current_lines:
        sections[current_section] = current_lines
    
    return sections

def build_thread_messages(sections, notion_url):
    """Build messages for each thread from briefing sections."""
    messages = {}
    
    # Jobs thread (Topic 6): Pipeline + Scanner sections
    jobs_lines = []
    for key, lines in sections.items():
        if any(kw in key.lower() for kw in ["pipeline", "scanner", "job"]):
            jobs_lines.extend(lines)
    if jobs_lines:
        msg = f"📋 <b>Today's Briefing - Jobs</b>\n\n"
        for line in jobs_lines[:15]:
            msg += f"• {_escape_html(line)}\n"
        if len(jobs_lines) > 15:
            msg += f"\n... and {len(jobs_lines)-15} more"
        msg += f"\n\n🔗 <a href=\"{notion_url}\">Full briefing</a>"
        messages["jobs"] = msg
    
    # Content thread (Topic 7): Content & Engagement section
    content_lines = []
    for key, lines in sections.items():
        if any(kw in key.lower() for kw in ["content", "engagement", "linkedin"]):
            content_lines.extend(lines)
    if content_lines:
        msg = f"📝 <b>Today's Briefing - Content</b>\n\n"
        for line in content_lines[:10]:
            msg += f"• {_escape_html(line)}\n"
        msg += f"\n🔗 <a href=\"{notion_url}\">Full briefing</a>"
        messages["content"] = msg
    
    # CRM thread (Topic 32): Email section (recruiter/networking emails)
    email_lines = []
    for key, lines in sections.items():
        if any(kw in key.lower() for kw in ["email", "calendar"]):
            email_lines.extend(lines)
    if email_lines:
        msg = f"📧 <b>Today's Briefing - Email & Calendar</b>\n\n"
        for line in email_lines[:10]:
            msg += f"• {_escape_html(line)}\n"
        msg += f"\n🔗 <a href=\"{notion_url}\">Full briefing</a>"
        messages["crm"] = msg
    
    # General thread (Topic 10): Tasks & System section
    task_lines = []
    for key, lines in sections.items():
        if any(kw in key.lower() for kw in ["task", "system"]):
            task_lines.extend(lines)
    if task_lines:
        msg = f"✅ <b>Today's Briefing - Tasks & System</b>\n\n"
        for line in task_lines[:10]:
            msg += f"• {_escape_html(line)}\n"
        msg += f"\n🔗 <a href=\"{notion_url}\">Full briefing</a>"
        messages["general"] = msg
    
    return messages

def _escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def save_briefing_files(sections, date_str, notion_url):
    """Save briefing sections as shared files any thread can read."""
    briefing_dir = os.path.join(WORKSPACE, "memory", "briefings")
    os.makedirs(briefing_dir, exist_ok=True)
    
    section_map = {
        "jobs": ["pipeline", "scanner", "job"],
        "email": ["email", "calendar"],
        "content": ["content", "engagement", "linkedin"],
        "tasks": ["task", "system"],
    }
    
    # Save section-specific files
    for name, keywords in section_map.items():
        lines = []
        for key, content in sections.items():
            if any(kw in key.lower() for kw in keywords):
                lines.append(f"## {key}")
                lines.extend(content)
        if lines:
            path = os.path.join(briefing_dir, f"{date_str}-{name}.md")
            with open(path, "w") as f:
                f.write("\n".join(lines))
    
    # Save full briefing
    full_path = os.path.join(briefing_dir, f"{date_str}.md")
    with open(full_path, "w") as f:
        f.write(f"# Morning Briefing {date_str}\n# Source: {notion_url}\n\n")
        for key, content in sections.items():
            f.write(f"## {key}\n")
            f.write("\n".join(content))
            f.write("\n\n")
    
    print(f"  💾 Saved briefing files to {briefing_dir}")

def main():
    from datetime import datetime, timezone, timedelta
    cairo_tz = timezone(timedelta(hours=2))
    today = datetime.now(cairo_tz).strftime("%Y-%m-%d")
    
    # Allow override
    if len(sys.argv) > 1:
        today = sys.argv[1]
    
    print(f"📤 Dispatching briefing sections to threads for {today}...")
    
    # Find briefing page
    page_id = get_briefing_page_id(today)
    if not page_id:
        print(f"❌ No briefing page found for {today}")
        sys.exit(1)
    
    notion_url = f"https://www.notion.so/{page_id.replace('-','')}"
    print(f"  Found page: {notion_url}")
    
    # Get blocks and parse
    blocks = get_page_blocks(page_id)
    sections = parse_briefing_sections(blocks)
    print(f"  Sections found: {list(sections.keys())}")
    
    # Save shared briefing files for cross-thread access
    save_briefing_files(sections, today, notion_url)
    
    # Build per-thread messages
    messages = build_thread_messages(sections, notion_url)
    
    # Send to threads
    for thread_name, msg in messages.items():
        topic_id = THREADS.get(thread_name)
        if not topic_id:
            continue
        print(f"  📤 Sending to {thread_name} (topic {topic_id})...")
        result = send_to_thread(topic_id, msg)
        if result and result.get("ok"):
            print(f"  ✅ {thread_name} done")
        
    print(f"\n✅ Dispatch complete!")

if __name__ == "__main__":
    main()
