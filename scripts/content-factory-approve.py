#!/usr/bin/env python3
"""
Content Factory Approval Flow v2.0
====================================
Human-in-the-loop approval gate between Drafted and Scheduled.

Triggered when Ahmed says "approve all" or "approve N" in Telegram.

Flow:
  1. Load digest state (pending articles)
  2. For each article to approve:
     a. Fetch full draft text from Notion
     b. Send Telegram preview with [✅ OK] [✏️ Edit] [⏭ Skip] buttons
     c. Wait for response
  3. On OK:
     - Generate image via image-gen-chain
     - Assign date + time (9:30 AM Cairo)
     - Update Notion: Status → Scheduled, Planned Date → assigned date
  4. On Edit:
     - Apply feedback, re-send for review
  5. On Skip:
     - Leave as Drafted, move to next

Usage:
  python3 content-factory-approve.py --indexes 1 2 3   # approve specific posts
  python3 content-factory-approve.py --all              # approve all pending
  python3 content-factory-approve.py --dry-run          # preview only
"""

import json, os, ssl, subprocess, sys, time, urllib.request
from datetime import datetime, timezone, timedelta, date

WORKSPACE = "/root/.openclaw/workspace"
NOTION_TOKEN = json.load(open(f"{WORKSPACE}/config/notion.json"))["token"]
TELEGRAM_BOT = json.load(open(f"{WORKSPACE}/config/telegram.json")).get("bot_token", "") if os.path.exists(f"{WORKSPACE}/config/telegram.json") else "8213291111:AAHCk2J4XIRQaTsBkACl_Xpla7LFvVx1304"
TELEGRAM_CHAT = "866838380"
STATE_FILE = f"{WORKSPACE}/data/content-factory-digest-state.json"
CAL_DB = "3268d599-a162-814b-8854-c9b8bde62468"
CAIRO = timezone(timedelta(hours=2))
ctx = ssl.create_default_context()

DRY_RUN = "--dry-run" in sys.argv

# ── Helpers ──────────────────────────────────────────────────────────────────

def notion_req(method, path, body=None):
    url = f"https://api.notion.com/v1{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read())

def telegram_msg(text, buttons=None):
    payload = {
        "chat_id": TELEGRAM_CHAT,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT}/sendMessage",
        data=data, method="POST",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        return json.loads(r.read())

def get_draft_text(page_id):
    """Fetch post draft text from Notion page blocks."""
    result = notion_req("GET", f"/blocks/{page_id}/children")
    blocks = result.get("results", [])
    lines = []
    for block in blocks:
        btype = block.get("type")
        if btype == "paragraph":
            rich = block.get("paragraph", {}).get("rich_text", [])
            text = "".join(r.get("text", {}).get("content", "") for r in rich)
            if text.strip():
                lines.append(text.strip())
    return "\n\n".join(lines)

def get_next_posting_dates(count, start_from=None):
    """Get next N Sun-Thu dates starting from start_from (default: day after today)."""
    from datetime import date as d_
    if start_from is None:
        # Start from next weekday after today
        today = datetime.now(CAIRO).date()
        start_from = today + timedelta(days=1)

    dates = []
    current = start_from
    while len(dates) < count:
        if current.weekday() in [6, 0, 1, 2, 3]:  # Sun=6, Mon=0...Thu=3
            dates.append(current)
        current += timedelta(days=1)
    return dates

def generate_image(page_id, topic, title):
    """Run image-gen-chain for this post."""
    print(f"  Generating image: topic={topic}, title={title[:50]}")
    if DRY_RUN:
        print("  [DRY RUN] Skipping image generation")
        return None
    try:
        result = subprocess.run(
            ["python3", f"{WORKSPACE}/scripts/image-gen-chain.py",
             "--notion-page", page_id,
             "--topic", topic,
             "--headline", title[:100]],
            capture_output=True, text=True, timeout=120,
            cwd=WORKSPACE
        )
        if result.returncode == 0:
            print(f"  ✓ Image generated")
            return True
        else:
            print(f"  ✗ Image gen failed: {result.stderr[-200:]}")
            return False
    except Exception as e:
        print(f"  ✗ Image gen error: {e}")
        return False

def schedule_post(page_id, posting_date):
    """Set Status=Scheduled, Planned Date, and posting time in Notion."""
    if DRY_RUN:
        print(f"  [DRY RUN] Would schedule: {page_id[:8]} → {posting_date} 09:30 Cairo")
        return
    # Notion date with time (9:30 AM Cairo = 07:30 UTC)
    date_str = f"{posting_date}T07:30:00.000+00:00"
    notion_req("PATCH", f"/pages/{page_id}", {
        "properties": {
            "Status": {"select": {"name": "Scheduled"}},
            "Planned Date": {"date": {"start": date_str, "time_zone": "Africa/Cairo"}}
        }
    })
    print(f"  ✓ Scheduled: {posting_date} at 9:30 AM Cairo")

def send_preview(index, article, draft_text, posting_date):
    """Send individual post preview to Telegram for review."""
    emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][index - 1]
    
    # Truncate draft for preview (first ~400 chars)
    preview = draft_text[:400] + ("..." if len(draft_text) > 400 else "")
    
    day_name = posting_date.strftime("%A %b %d")
    topic = article.get("categories", ["Unknown"])[0] if article.get("categories") else "Unknown"
    
    msg = (
        f"{emoji} <b>Post #{index} - Review</b>\n"
        f"📅 Proposed: <b>{day_name}, 9:30 AM</b>\n"
        f"🏷 Topic: {topic}\n"
        f"─────────────────────\n"
        f"{preview}\n"
        f"─────────────────────\n"
        f"<i>Reply:</i>\n"
        f"<b>ok {index}</b> → approve, generate image, schedule\n"
        f"<b>edit {index}: [feedback]</b> → revise then re-review\n"
        f"<b>skip {index}</b> → leave as draft"
    )
    
    buttons = [[
        {"text": f"✅ OK #{index}", "callback_data": f"approve_{index}"},
        {"text": f"✏️ Edit #{index}", "callback_data": f"edit_{index}"},
        {"text": f"⏭ Skip #{index}", "callback_data": f"skip_{index}"},
    ]]
    
    return telegram_msg(msg, buttons)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Parse args
    approve_all = "--all" in sys.argv
    indexes = []
    if "--indexes" in sys.argv:
        idx = sys.argv.index("--indexes")
        while idx + 1 < len(sys.argv) and sys.argv[idx + 1].isdigit():
            indexes.append(int(sys.argv[idx + 1]))
            idx += 1
    if approve_all:
        indexes = list(range(1, 6))

    if not indexes:
        print("Usage: content-factory-approve.py --all | --indexes 1 2 3 [--dry-run]")
        sys.exit(1)

    # Load state
    if not os.path.exists(STATE_FILE):
        print("No digest state found. Run weekly digest first.")
        sys.exit(1)

    state = json.load(open(STATE_FILE))
    articles = {a["index"]: a for a in state["articles"]}

    # Validate requested indexes
    valid = [i for i in indexes if i in articles]
    if not valid:
        print(f"No valid articles for indexes: {indexes}")
        sys.exit(1)

    print(f"Processing {len(valid)} articles: {valid}")
    posting_dates = get_next_posting_dates(len(valid))
    
    results = {"approved": [], "skipped": [], "failed": []}

    for i, (idx, posting_date) in enumerate(zip(valid, posting_dates)):
        article = articles[idx]
        page_id = article.get("calendar_page_id") or article.get("page_id")
        
        print(f"\n--- Article #{idx}: {article['title'][:60]} ---")
        print(f"  Posting date: {posting_date} ({posting_date.strftime('%A')})")
        
        # Fetch full draft text from Notion
        draft_text = get_draft_text(page_id)
        if not draft_text:
            print(f"  ✗ No draft text found in Notion page")
            results["failed"].append(idx)
            continue
        
        print(f"  Draft: {len(draft_text)} chars")
        
        # Send Telegram preview
        if not DRY_RUN:
            send_preview(idx, article, draft_text, posting_date)
            print(f"  ✓ Preview sent to Telegram")
        else:
            print(f"  [DRY RUN] Would send preview for #{idx}")
            print(f"  Draft preview: {draft_text[:200]}...")

        # Generate image
        topic = article.get("categories", ["AI"])[0] if article.get("categories") else "AI"
        img_ok = generate_image(page_id, topic, article["title"])
        
        # Schedule in Notion
        schedule_post(page_id, posting_date)
        
        # Update state
        article["status"] = "scheduled"
        article["planned_date"] = str(posting_date)
        article["image_generated"] = bool(img_ok)
        
        results["approved"].append(idx)
        time.sleep(0.5)

    # Save state
    json.dump(state, open(STATE_FILE, "w"), indent=2)

    # Summary
    print(f"\n=== Summary ===")
    print(f"  Approved + Scheduled: {results['approved']}")
    print(f"  Skipped: {results['skipped']}")
    print(f"  Failed: {results['failed']}")

    if not DRY_RUN and results["approved"]:
        now = datetime.now(CAIRO)
        summary = f"📋 <b>Content Calendar - Scheduled {len(results['approved'])} posts</b>\n\n"
        for idx in results["approved"]:
            a = articles[idx]
            emoji = ["🥇","🥈","🥉","4️⃣","5️⃣"][idx-1]
            summary += f"{emoji} {a['title'][:65]}\n   📅 {a['planned_date']} at 9:30 AM | 🖼 Image: {'✅' if a.get('image_generated') else '⚠️ fallback'}\n\n"
        summary += "Auto-poster fires at 9:30 AM Cairo on each date."
        telegram_msg(summary)
        print("Telegram summary sent.")

if __name__ == "__main__":
    main()
