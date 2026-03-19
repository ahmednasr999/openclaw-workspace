#!/usr/bin/env python3
"""
LinkedIn Auto-Poster v2: Reads from Notion Content Calendar, posts via Composio.

Flow:
1. Find today's "Scheduled" post in Notion Content Calendar
2. Extract full post text from page blocks
3. Convert **bold** markdown to LinkedIn Unicode bold
4. Download image from GitHub (if any)
5. Upload image to LinkedIn via Composio INITIALIZE_IMAGE_UPLOAD
6. Create post via Composio LINKEDIN_CREATE_LINKED_IN_POST
7. Update Notion status to "Posted" with post URL

Usage:
  python3 linkedin-auto-poster.py              # Post today's scheduled content
  python3 linkedin-auto-poster.py --dry-run     # Preview without posting
  python3 linkedin-auto-poster.py --date 2026-03-19  # Post for specific date
"""

import json, os, re, ssl, sys, urllib.request, tempfile
from datetime import datetime
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
NOTION_DB = "3268d599-a162-814b-8854-c9b8bde62468"  # Content Calendar
NOTION_TOKEN = json.load(open(f"{WORKSPACE}/config/notion.json"))["token"]
PERSON_URN = "urn:li:person:mm8EyA56mj"

# Parse args
DRY_RUN = "--dry-run" in sys.argv
CUSTOM_DATE = None
for i, arg in enumerate(sys.argv):
    if arg == "--date" and i + 1 < len(sys.argv):
        CUSTOM_DATE = sys.argv[i + 1]

TODAY = CUSTOM_DATE or datetime.now().strftime("%Y-%m-%d")

# ── Notion helpers ──────────────────────────────────────────────

def notion_req(method, path, body=None):
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
        return json.loads(r.read())


# ── Unicode Bold Converter ──────────────────────────────────────

def to_unicode_bold(text):
    """Convert regular text to Unicode Mathematical Bold (LinkedIn-compatible)."""
    result = []
    for ch in text:
        if 'A' <= ch <= 'Z':
            result.append(chr(0x1D5D4 + ord(ch) - ord('A')))
        elif 'a' <= ch <= 'z':
            result.append(chr(0x1D5EE + ord(ch) - ord('a')))
        elif '0' <= ch <= '9':
            result.append(chr(0x1D7EC + ord(ch) - ord('0')))
        else:
            result.append(ch)
    return ''.join(result)


def convert_bold_markdown(text):
    """Replace **bold text** with Unicode bold equivalent."""
    def bold_replacer(match):
        return to_unicode_bold(match.group(1))
    return re.sub(r'\*\*(.+?)\*\*', bold_replacer, text)


# ── Content Extraction ──────────────────────────────────────────

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
    pid = page["id"]
    props = page["properties"]

    title = "".join(t.get("plain_text", "") for t in props.get("Title", {}).get("title", []))

    # Get full content from page blocks
    blocks_result = notion_req("GET", f"/blocks/{pid}/children?page_size=100")

    full_text = ""
    image_url = None

    for b in blocks_result.get("results", []):
        bt = b["type"]

        if bt == "image":
            # Get image URL (external or file)
            img = b["image"]
            image_url = img.get("external", {}).get("url") or img.get("file", {}).get("url", "")

        elif bt in ("paragraph", "heading_2", "heading_3"):
            rt = b.get(bt, {}).get("rich_text", [])
            line = ""
            for t in rt:
                text = t.get("plain_text", "")
                annotations = t.get("annotations", {})
                # If bold in Notion, wrap with ** for our converter
                if annotations.get("bold") and text.strip():
                    line += f"**{text}**"
                else:
                    line += text
            if line:
                full_text += line + "\n"
            else:
                full_text += "\n"  # Empty paragraph = line break

        elif bt == "bulleted_list_item":
            rt = b.get("bulleted_list_item", {}).get("rich_text", [])
            text = "".join(t.get("plain_text", "") for t in rt)
            if text:
                full_text += f"• {text}\n"

        elif bt == "numbered_list_item":
            rt = b.get("numbered_list_item", {}).get("rich_text", [])
            text = "".join(t.get("plain_text", "") for t in rt)
            if text:
                full_text += f"- {text}\n"

    # Clean up: remove excessive blank lines, trim
    full_text = re.sub(r'\n{3,}', '\n\n', full_text).strip()

    # Convert **bold** to Unicode bold
    full_text = convert_bold_markdown(full_text)

    return {
        "page_id": pid,
        "title": title,
        "content": full_text,
        "image_url": image_url
    }


# ── Image Upload ────────────────────────────────────────────────

def download_image(url):
    """Download image from URL and return (bytes, content_type)."""
    print(f"Downloading image: {url[:80]}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
        content_type = r.headers.get("Content-Type", "image/png")
        data = r.read()
        print(f"Downloaded: {len(data)} bytes, type: {content_type}")
        return data, content_type


def upload_image_to_linkedin(image_bytes, content_type):
    """
    Upload image to LinkedIn via Composio.
    Returns image URN for use in post.
    
    This function writes the image to a temp file and outputs
    upload instructions for the calling agent.
    """
    # Save image to temp file for the agent to use
    ext = "png" if "png" in content_type else "jpg"
    tmp_path = f"/tmp/linkedin-post-image.{ext}"
    with open(tmp_path, "wb") as f:
        f.write(image_bytes)
    print(f"Image saved to: {tmp_path} ({len(image_bytes)} bytes)")
    return tmp_path


# ── Notion Update ───────────────────────────────────────────────

def update_notion_status(page_id, post_url):
    """Update Notion page status to Posted and add URL.
    Note: Post URL property is type 'url' in Notion, NOT rich_text."""
    body = {
        "properties": {
            "Status": {"select": {"name": "Posted"}},
        }
    }
    # Post URL is a 'url' type property in Notion - NOT rich_text
    if post_url:
        body["properties"]["Post URL"] = {"url": post_url[:2000]}
    notion_req("PATCH", f"/pages/{page_id}", body)
    print(f"Updated Notion: status=Posted, url={post_url}")


# ── Main ────────────────────────────────────────────────────────

def main():
    print(f"=== LinkedIn Auto-Poster v2 - {TODAY} ===")
    if DRY_RUN:
        print("[DRY RUN MODE - will not post]")

    # Get today's post
    post = get_today_post()
    if not post:
        print(f"No scheduled post for {TODAY}")
        return

    print(f"\nTitle: {post['title']}")
    print(f"Content length: {len(post['content'])} chars")
    print(f"Image: {post['image_url'] or 'None'}")
    print(f"\n--- POST CONTENT ---")
    print(post['content'])
    print(f"--- END CONTENT ---\n")

    if DRY_RUN:
        print("[DRY RUN] Would post above content to LinkedIn")
        if post['image_url']:
            print(f"[DRY RUN] Would attach image: {post['image_url']}")
        return

    # Download image if present
    image_path = None
    if post['image_url']:
        try:
            image_bytes, content_type = download_image(post['image_url'])
            image_path = upload_image_to_linkedin(image_bytes, content_type)
        except Exception as e:
            print(f"Warning: Image download failed ({e}), posting without image")

    # Output for agent to pick up
    output = {
        "action": "post_to_linkedin",
        "person_urn": PERSON_URN,
        "content": post['content'],
        "image_path": image_path,
        "page_id": post['page_id'],
        "title": post['title']
    }
    
    # Write output for agent consumption
    output_path = "/tmp/linkedin-post-payload.json"
    with open(output_path, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nPayload written to: {output_path}")
    print(f"READY_TO_POST")

if __name__ == "__main__":
    main()
