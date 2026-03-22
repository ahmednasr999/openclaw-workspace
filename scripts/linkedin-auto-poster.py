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

# Auth: read gateway token from openclaw.json
GATEWAY_URL = "http://127.0.0.1:18789/v1/chat/completions"
try:
    _gw_cfg = json.load(open(os.path.expanduser("~/.openclaw/openclaw.json")))
    GATEWAY_TOKEN = _gw_cfg.get("gateway", {}).get("auth", {}).get("token", "")
except Exception:
    GATEWAY_TOKEN = ""


def call_llm(prompt: str) -> str:
    """Call MiniMax-M2.7 via OpenClaw gateway (same as all other agents)."""
    payload = {
        "model": "minimax-portal/MiniMax-M2.7",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 64,
        "temperature": 0.0,
    }
    headers = {"Content-Type": "application/json"}
    if GATEWAY_TOKEN:
        headers["Authorization"] = f"Bearer {GATEWAY_TOKEN}"
    req = urllib.request.Request(
        GATEWAY_URL,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  LLM error: {e}")
        return f"ERROR: {e}"


def call_llm_long(prompt: str) -> str:
    """Call LLM with higher token limit for batched scoring."""
    payload = {
        "model": "minimax-portal/MiniMax-M2.7",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 256,
        "temperature": 0.0,
    }
    headers = {"Content-Type": "application/json"}
    if GATEWAY_TOKEN:
        headers["Authorization"] = f"Bearer {GATEWAY_TOKEN}"
    req = urllib.request.Request(
        GATEWAY_URL,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  LLM error: {e}")
        return ""


def parse_answer(text: str) -> int:
    t = text.upper().strip()
    return 1 if "YES" in t and "NO" not in t else 0


def score_post(post_text: str) -> dict:
    """Run all 10 eval questions in a single LLM call (10x faster)."""
    print("\n=== Scoring Post ===")
    
    questions_block = "\n".join(f"Q{i+1}. {q}" for i, q in enumerate(QUESTIONS))
    prompt = f"""Evaluate this LinkedIn post against 10 quality criteria.
For each question, answer ONLY "YES" or "NO" on a separate line.
Format: Q1: YES/NO, Q2: YES/NO, ... Q10: YES/NO

{questions_block}

Post to evaluate:
{post_text[:3000]}

Answer each Q1-Q10 as YES or NO:"""
    
    response = call_llm_long(prompt)
    
    # Parse: look for YES/NO per question
    results = []
    for i in range(1, 11):
        # Try patterns: "Q1: YES", "Q1. YES", "1. YES", just sequential YES/NO
        pattern = rf'Q?{i}[.:)\s]+\s*(YES|NO)'
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            results.append(1 if match.group(1).upper() == "YES" else 0)
        else:
            results.append(0)  # Default to 0 if unparseable
    
    # Fallback: if regex found nothing, count YES/NO in order
    if sum(results) == 0 and "YES" in response.upper():
        words = [w.strip().upper() for w in re.split(r'[,\n;]+', response) if w.strip().upper() in ("YES", "NO")]
        for i, w in enumerate(words[:10]):
            results[i] = 1 if w == "YES" else 0
    
    total = sum(results)
    for i, q in enumerate(QUESTIONS):
        print(f"  Q{i+1}: {q.split(':')[0]:25s} → {results[i]}")
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
    
    today_str = date.today().isoformat()
    
    # Dedup: replace existing entry for same page_id + date (don't append duplicates)
    data["posts"] = [
        p for p in data["posts"]
        if not (p.get("notion_page_id") == page_id and p.get("date") == today_str and not p.get("post_url"))
    ]
    
    entry = {
        "date": today_str,
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


def send_telegram_confirmation(post_url, title="", image_url=None):
    """Send Telegram notification that post was published."""
    import subprocess
    image_status = "✅ with image" if image_url else "📝 text only"
    msg = f"✅ LinkedIn Posted ({image_status})\n\n{title[:100]}\n\n🔗 {post_url}"
    try:
        subprocess.run(
            ["openclaw", "message", "send", "--channel", "telegram",
             "--to", "866838380", "--message", msg],
            timeout=15, capture_output=True
        )
        print(f"Telegram confirmation sent")
    except Exception as e:
        print(f"Telegram notification failed: {e}")


def update_briefing_page(post_url, image_url=None, title=""):
    """Add post details to today's morning briefing Notion page."""
    from datetime import timezone, timedelta
    cairo = timezone(timedelta(hours=2))
    today_str = datetime.now(cairo).strftime("%Y-%m-%d")
    
    # Find today's briefing page
    briefing_db = "3268d599-a162-812d-a59e-e5496dec80e7"
    result = notion_req("POST", f"/databases/{briefing_db}/query", {
        "filter": {"property": "Name", "title": {"contains": today_str}},
        "page_size": 1,
    })
    if not result:
        print("  Briefing update: No API response")
        return False
    
    pages = result.get("results", [])
    if not pages:
        print(f"  Briefing update: No page found for {today_str}")
        return False
    
    briefing_page_id = pages[0]["id"]
    
    # Get existing blocks to find Content section
    blocks_resp = notion_req("GET", f"/blocks/{briefing_page_id}/children?page_size=100")
    if not blocks_resp:
        print("  Briefing update: Could not fetch blocks")
        return False
    
    blocks = blocks_resp.get("results", [])
    
    # Find the Content & Engagement section
    content_section_idx = None
    insert_after_id = None
    for i, b in enumerate(blocks):
        btype = b["type"]
        rt = b.get(btype, {}).get("rich_text", [])
        text = "".join(t.get("text", {}).get("content", "") for t in rt)
        if "Content" in text and "Engagement" in text and btype == "heading_2":
            content_section_idx = i
        # Find last block before next section divider
        if content_section_idx is not None and i > content_section_idx:
            if b["type"] == "divider" or (b["type"] == "heading_2" and i > content_section_idx):
                break
            insert_after_id = b["id"]
    
    if not insert_after_id:
        # Fallback: insert after the heading itself
        if content_section_idx is not None:
            insert_after_id = blocks[content_section_idx]["id"]
        else:
            print("  Briefing update: Could not find Content & Engagement section")
            return False
    
    # Build blocks to insert
    new_blocks = [
        {
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": f"Posted: {title[:80]}"}, "annotations": {"bold": True}}],
                "icon": {"type": "emoji", "emoji": "✅"},
                "color": "green_background",
            }
        },
        {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {"type": "text", "text": {"content": "LinkedIn: "}},
                    {"type": "text", "text": {"content": post_url, "link": {"url": post_url}}},
                ]
            }
        },
    ]
    
    if image_url:
        new_blocks.append({
            "type": "image",
            "image": {"type": "external", "external": {"url": image_url}}
        })
    
    # Insert blocks
    resp = notion_req("PATCH", f"/blocks/{briefing_page_id}/children", {
        "children": new_blocks,
        "after": insert_after_id,
    })
    
    if resp:
        print(f"  Briefing page updated with post details")
        return True
    else:
        print(f"  Briefing update: Failed to insert blocks")
        return False


# ── Main ────────────────────────────────────────────────────────

def check_stale_watchdog():
    """Check if yesterday's watchdog flag still exists — means posting failed."""
    import subprocess
    watchdog_path = "/tmp/linkedin-post-pending.flag"
    if not os.path.exists(watchdog_path):
        return
    try:
        data = json.load(open(watchdog_path))
        created = datetime.fromisoformat(data.get("created_at", ""))
        age_hours = (datetime.now() - created).total_seconds() / 3600
        if age_hours > 1:
            title = data.get("title", "Unknown")
            msg = f"🔴 LinkedIn post FAILED yesterday\n\nTitle: {title}\nPrepared {age_hours:.0f}h ago but never posted.\nWatchdog flag still exists."
            try:
                subprocess.run(
                    ["openclaw", "message", "send", "--channel", "telegram",
                     "--to", "866838380", "--message", msg],
                    timeout=15, capture_output=True
                )
            except Exception:
                pass
            print(f"⚠️ Stale watchdog: {title} ({age_hours:.0f}h old)")
            # Remove stale flag so we don't alert again
            os.remove(watchdog_path)
    except Exception:
        # Corrupted flag — remove it
        os.remove(watchdog_path)


def main():
    # Check for stale watchdog from previous run
    check_stale_watchdog()
    
    # Handle URL update mode (after agent posts)
    if UPDATE_URL and UPDATE_PAGE_ID:
        update_post_url(UPDATE_PAGE_ID, UPDATE_URL)
        # Also update today's briefing page
        # Read the payload to get image URL and title
        payload_path = "/tmp/linkedin-post-payload.json"
        image_url = None
        title = ""
        if os.path.exists(payload_path):
            try:
                payload = json.load(open(payload_path))
                title = payload.get("title", "")
                # Get original image URL from Notion (GitHub raw URL)
                image_url = None
                # Check if the post had an image
                if payload.get("image_required") or payload.get("image_path"):
                    # Try to find image URL from today's content calendar entry
                    post_data = get_today_post()
                    if post_data:
                        image_url = post_data.get("image_url")
            except Exception:
                pass
        update_briefing_page(UPDATE_URL, image_url=image_url, title=title)
        # Remove watchdog flag — post succeeded
        watchdog_path = "/tmp/linkedin-post-pending.flag"
        if os.path.exists(watchdog_path):
            os.remove(watchdog_path)
            print("Watchdog flag removed (post successful)")
        # Send Telegram confirmation
        send_telegram_confirmation(UPDATE_URL, title, image_url)
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

    # Quality gate: score < 6 → flag for review, don't auto-post
    MIN_SCORE = 6
    if score_result["total"] < MIN_SCORE:
        print(f"⚠️ QUALITY GATE: Score {score_result['total']}/10 < {MIN_SCORE} minimum")
        print(f"Post flagged for manual review. NOT auto-posting.")
        # Write flag for agent to send Telegram alert
        flag = {
            "action": "quality_hold",
            "score": score_result["total"],
            "min_score": MIN_SCORE,
            "title": post['title'],
            "page_id": post['page_id'],
            "failed_questions": [QUESTIONS[i].split(":")[0] for i, s in enumerate(score_result["questions"]) if s == 0],
        }
        with open("/tmp/linkedin-post-payload.json", "w") as f:
            json.dump(flag, f, ensure_ascii=False, indent=2)
        print(f"QUALITY_HOLD")
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
        "image_required": bool(post['image_url']),
        "page_id": post['page_id'],
        "title": post['title'],
        "score": score_result['total'],
    }
    
    # Write output for agent consumption
    output_path = "/tmp/linkedin-post-payload.json"
    with open(output_path, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # Write a watchdog file — agent must delete this after successful post
    # If it still exists 30 min after cron, something failed
    watchdog_path = "/tmp/linkedin-post-pending.flag"
    with open(watchdog_path, "w") as f:
        f.write(json.dumps({
            "created_at": datetime.now().isoformat(),
            "page_id": post['page_id'],
            "title": post['title'],
        }))
    
    print(f"\nPayload written to: {output_path}")
    print(f"SCORE: {score_result['total']}/10")
    print(f"LOGGED_TO: {RESEARCH_LOG}")
    print(f"WATCHDOG: {watchdog_path} (agent must delete after posting)")
    print(f"POST_URL_UPDATE_CMD: python3 scripts/linkedin-auto-poster.py --update-url '<POST_URL>' --page-id {post['page_id']}")
    print(f"READY_TO_POST")

if __name__ == "__main__":
    main()
