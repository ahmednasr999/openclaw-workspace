#!/usr/bin/env python3
"""
LinkedIn Auto-Poster v3: Reads from Notion Content Calendar, scores via autoresearch loop, posts via Composio.

Flow:
1. Find today's "Scheduled" post in Notion Content Calendar
2. Extract full post text from page blocks
3. Score post using 10 binary eval questions (linkedin-score-post logic)
4. Log score + post text to data/linkedin-research-log.json
5. Convert **bold** markdown to LinkedIn Unicode bold
6. Download image from GitHub (if any)
7. Write payload to /tmp/linkedin-post-payload.json for agent
8. Agent posts via Composio, then this script updates log with post URL

Usage:
  python3 linkedin-auto-poster.py              # Score + post today's scheduled content
  python3 linkedin-auto-poster.py --dry-run     # Preview without posting
  python3 linkedin-auto-poster.py --date 2026-03-19  # Post for specific date
  python3 linkedin-auto-poster.py --update-url "<url>" --page-id <id>  # Record post URL after agent posts
"""

import json, os, re, ssl, sys, urllib.request, tempfile
from datetime import datetime, date
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
NOTION_DB = "3268d599-a162-814b-8854-c9b8bde62468"  # Content Calendar
NOTION_TOKEN = json.load(open(f"{WORKSPACE}/config/notion.json"))["token"]
PERSON_URN = "urn:li:person:mm8EyA56mj"
RESEARCH_LOG = f"{WORKSPACE}/data/linkedin-research-log.json"

# Parse args
DRY_RUN = "--dry-run" in sys.argv
UPDATE_URL = None
UPDATE_PAGE_ID = None

for i, arg in enumerate(sys.argv):
    if arg == "--update-url" and i + 1 < len(sys.argv):
        UPDATE_URL = sys.argv[i + 1]
    if arg == "--page-id" and i + 1 < len(sys.argv):
        UPDATE_PAGE_ID = sys.argv[i + 1]

# ── Autoresearch Scoring ────────────────────────────────────────

QUESTIONS = [
    "RESULT_TRANSFORMATION: Does the hook describe a RESULT or TRANSFORMATION (not just a topic)? Answer YES or NO.",
    "SPECIFIC_PERSON: Does the post feature a SPECIFIC PERSON or STORY (not just a company)? Answer YES or NO.",
    "SCROLL_STOPPER: Is the first line a SCROLL-STOPPER that creates a curiosity gap? Answer YES or NO.",
    "METRIC: Does the post include a specific METRIC or DATA POINT? Answer YES or NO.",
    "HOOK_LENGTH: Is the hook under 300 characters? Answer YES or NO.",
    "CTA: Does the post END WITH A QUESTION or CTA for engagement? Answer YES or NO.",
    "ACHIEVE_FRAME: Is the framing about WHAT YOU CAN ACHIEVE (not what the tool/company does)? Answer YES or NO.",
    "NOT_PRESS_RELEASE: Does it avoid sounding like a press release or changelog? Answer YES or NO.",
    "CONTEXT_RICH: Is it CONTEXT-RICH — does it explain WHY, not just WHAT? Answer YES or NO.",
    "URGENCY: Does it create a SENSE OF URGENCY or exclusivity? Answer YES or NO.",
]

def get_api_key():
    """Get API key from config."""
    cfg_path = f"{WORKSPACE}/config/models.json"
    if os.path.exists(cfg_path):
        cfg = json.load(open(cfg_path))
        return cfg.get("minimax_api_key") or cfg.get("api_key") or ""
    return os.environ.get("MINIMAX_API_KEY", "")


def call_llm(prompt: str) -> str:
    """Call MiniMax-M2.7 via OpenAI-compatible API."""
    api_key = get_api_key()
    base_url = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")
    
    payload = {
        "model": "MiniMax-M2.7",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 64,
        "temperature": 0.0,
    }
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"ERROR: {e}"


def parse_answer(text: str) -> int:
    t = text.upper().strip()
    return 1 if "YES" in t and "NO" not in t else 0


def score_post(post_text: str) -> dict:
    """Run all 10 eval questions against post text."""
    results = []
    print("\n=== Scoring Post ===")
    for i, question in enumerate(QUESTIONS):
        answer = call_llm(f"{question}\n\nPost to evaluate:\n{post_text[:2000]}")
        score = parse_answer(answer)
        results.append(score)
        print(f"  Q{i+1}: {question.split(':')[0]:20s} → {score}")
    
    total = sum(results)
    print(f"=== Score: {total}/10 ===\n")
    return {"total": total, "questions": results}


def log_post(post_text: str, score_result: dict, page_id: str):
    """Append scored post to research log."""
    os.makedirs(os.path.dirname(RESEARCH_LOG), exist_ok=True)
    
    if os.path.exists(RESEARCH_LOG):
        with open(RESEARCH_LOG) as f:
            data = json.load(f)
    else:
        data = {"posts": [], "current_prompt": "", "prompt_history": [], "current_prompt_version": 1}
    
    entry = {
        "date": date.today().isoformat(),
        "post_text": post_text[:5000],
        "eval_score": score_result["total"],
        "questions": score_result["questions"],
        "engagement": None,
        "prompt_version": data.get("current_prompt_version", 1),
        "prompt_used": data.get("current_prompt", ""),
        "notion_page_id": page_id,
    }
    data["posts"].append(entry)
    
    with open(RESEARCH_LOG, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Logged to {RESEARCH_LOG} | Score: {score_result['total']}/10")


def update_post_url(page_id: str, post_url: str):
    """Update the most recent post entry with the given page_id to include the URL."""
    if not os.path.exists(RESEARCH_LOG):
        print("Research log not found")
        return
    
    with open(RESEARCH_LOG) as f:
        data = json.load(f)
    
    # Find and update the entry with matching page_id (most recent first)
    for post in reversed(data.get("posts", [])):
        if post.get("notion_page_id") == page_id and not post.get("post_url"):
            post["post_url"] = post_url
            with open(RESEARCH_LOG, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Updated post URL: {post_url}")
            return
    
    print(f"No unmatched entry found for page_id: {page_id}")
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
    # Handle URL update mode (after agent posts)
    if UPDATE_URL and UPDATE_PAGE_ID:
        update_post_url(UPDATE_PAGE_ID, UPDATE_URL)
        return
    
    print(f"=== LinkedIn Auto-Poster v3 - {TODAY} ===")
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

    # Score the post via autoresearch loop
    score_result = score_post(post['content'])
    log_post(post['content'], score_result, post['page_id'])

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
    print(f"SCORE: {score_result['total']}/10")
    print(f"LOGGED_TO: {RESEARCH_LOG}")
    print(f"POST_URL_UPDATE_CMD: python3 scripts/linkedin-auto-poster.py --update-url '<POST_URL>' --page-id {post['page_id']}")
    print(f"READY_TO_POST")

if __name__ == "__main__":
    main()
