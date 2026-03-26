#!/usr/bin/env python3
"""
Content Factory Weekly Digest v1.0
===================================
Phase 2: AI pre-selects top 5 gold articles → sends Telegram digest → Ahmed approves/rejects.

Runs: Friday 9 AM Cairo (before weekend content planning)
Cron: 0 7 * * 5

What it does:
1. Query RSS Intelligence DB for articles scored this week
2. Rank by Format Score (composite: quality * topic weight * source)
3. Pick top 5 gold items
4. Send formatted Telegram digest with inline approve/reject buttons
5. Save digest state for tracking

The "Option B" curation workflow from Content Factory design:
- AI pre-selects top 5
- Ahmed approves/rejects (~3 min/week)
- Approved items get moved to Content Calendar with format + angle pre-filled
"""
import json, os, ssl, sys, urllib.request, time
from datetime import datetime, timezone, timedelta

WORKSPACE = "/root/.openclaw/workspace"
NOTION_TOKEN = json.load(open(f"{WORKSPACE}/config/notion.json"))["token"]
RSS_DB = "32e8d599-a162-8180-9e3a-fbfc17a84e49"
CAL_DB = "3268d599-a162-814b-8854-c9b8bde62468"
TELEGRAM_BOT = "8213291111:AAHCk2J4XIRQaTsBkACl_Xpla7LFvVx1304"
TELEGRAM_CHAT = "866838380"
CAIRO = timezone(timedelta(hours=2))

LOG_FILE = f"{WORKSPACE}/logs/content-factory-weekly-digest.log"
STATE_FILE = f"{WORKSPACE}/data/content-factory-digest-state.json"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

ctx = ssl.create_default_context()

def log(msg):
    ts = datetime.now(CAIRO).strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

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
    """Send Telegram message with optional inline keyboard."""
    payload = {
        "chat_id": TELEGRAM_CHAT,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
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

# ── Query top articles this week ─────────────────────────────────────────────
def get_top_articles(limit=5):
    """Get highest-scoring articles from the past 7 days."""
    week_ago = (datetime.now(CAIRO) - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00Z")
    
    # Get scored articles from the last 14 days only (sorted by format score descending)
    two_weeks_ago = (datetime.now(CAIRO) - timedelta(days=14)).strftime("%Y-%m-%d")
    all_results = []
    cursor = None
    while True:
        body = {
            "filter": {
                "and": [
                    {"property": "Quality Score", "number": {"is_not_empty": True}},
                    {"property": "Quality Score", "number": {"greater_than_or_equal_to": 5}},
                    {"property": "Published", "date": {"on_or_after": two_weeks_ago}},
                ]
            },
            "sorts": [
                {"property": "Format Score", "direction": "descending"}
            ],
            "page_size": 100
        }
        if cursor:
            body["start_cursor"] = cursor
        d = notion_req("POST", f"/databases/{RSS_DB}/query", body)
        all_results.extend(d.get("results", []))
        cursor = d.get("next_cursor")
        if not cursor or len(all_results) >= 50:
            break
    
    # Parse and rank
    articles = []
    for page in all_results:
        props = page.get("properties", {})
        title = "".join([t.get("plain_text", "") for t in props.get("Name", {}).get("title", [])])
        url = props.get("URL", {}).get("url", "")
        quality = props.get("Quality Score", {}).get("number", 0) or 0
        hook = props.get("Hook Score", {}).get("number", 0) or 0
        format_score = props.get("Format Score", {}).get("number", 0) or 0
        formats = [f.get("name", "") for f in props.get("Post Format", {}).get("multi_select", [])]
        categories = [c.get("name", "") for c in props.get("Category", {}).get("multi_select", [])]
        topic_weight = props.get("Topic Weight", {}).get("select", {})
        topic_weight = topic_weight.get("name", "") if topic_weight else ""
        priority = props.get("Priority", {}).get("select", {})
        priority = priority.get("name", "") if priority else ""
        angle = "".join([t.get("plain_text", "") for t in props.get("Posting Angle", {}).get("rich_text", [])])
        summary = "".join([t.get("plain_text", "") for t in props.get("Executive Summary", {}).get("rich_text", [])])
        
        articles.append({
            "page_id": page["id"],
            "title": title,
            "url": url,
            "quality": quality,
            "hook": hook,
            "format_score": format_score,
            "formats": formats,
            "categories": categories,
            "topic_weight": topic_weight,
            "priority": priority,
            "angle": angle,
            "summary": summary,
        })
    
    # Sort by format_score (already sorted from Notion, but double-check)
    articles.sort(key=lambda x: x["format_score"], reverse=True)
    return articles[:limit]

# ── Create Content Calendar entry for approved article ────────────────────────
def promote_to_calendar(article):
    """Move an approved article to Content Calendar with format + angle pre-filled."""
    body = {
        "parent": {"database_id": CAL_DB},
        "properties": {
            "Title": {"title": [{"text": {"content": article["title"][:200]}}]},
            "Topic": {"select": {"name": article["categories"][0] if article["categories"] else "AI/Tech"}},
            "Status": {"select": {"name": "Idea"}},
            "Hook": {"rich_text": [{"text": {"content": article["angle"][:300]}}] if article["angle"] else []},
        }
    }
    
    result = notion_req("POST", "/pages", body)
    page_id = result.get("id", "")
    
    # Add source URL as bookmark block
    if article["url"] and page_id:
        time.sleep(0.5)
        notion_req("PATCH", f"/blocks/{page_id}/children", {
            "children": [{
                "object": "block",
                "type": "bookmark",
                "bookmark": {"url": article["url"]}
            }, {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": 
                    f"Formats: {', '.join(article['formats'])} | Quality: {article['quality']}/10 | "
                    f"Composite: {article['format_score']}\n\n"
                    f"Suggested angle: {article['angle']}"
                }}]}
            }]
        })
    
    return page_id

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    now = datetime.now(CAIRO)
    log(f"=== Content Factory Weekly Digest === {now.strftime('%Y-%m-%d %H:%M')} Cairo")
    
    top_articles = get_top_articles(limit=5)
    log(f"Top {len(top_articles)} articles selected")
    
    if not top_articles:
        log("No scored articles found. Skipping digest.")
        telegram_msg("📰 <b>Content Factory Weekly Digest</b>\n\nNo gold articles this week. RSS feeds may need attention.")
        return
    
    # ── Build Telegram digest ──
    header = (
        "📰 <b>Content Factory - Weekly Top 5</b>\n"
        f"<i>{now.strftime('%B %d, %Y')}</i>\n"
        "─────────────────────\n"
        "Review these gold items (~3 min).\n"
        "Reply with numbers to approve (e.g. '1 3 5')\n\n"
    )
    
    lines = [header]
    
    for i, art in enumerate(top_articles, 1):
        fmt_str = " + ".join(art["formats"]) if art["formats"] else "General"
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📄"
        
        lines.append(
            f"{emoji} <b>#{i} — {art['title'][:70]}</b>\n"
            f"   📊 Quality: {art['quality']}/10 | Hook: {art['hook']}/10 | Score: {art['format_score']}\n"
            f"   🏷 {fmt_str} | {art['topic_weight']}\n"
            f"   💡 <i>{art['angle'][:120]}</i>\n"
            f"   🔗 {art['url'][:80]}\n"
        )
    
    lines.append(
        "\n─────────────────────\n"
        "Reply: <b>approve 1 3 5</b> → moves to Content Calendar\n"
        "Reply: <b>reject all</b> → skip this week\n"
        "Reply: <b>approve all</b> → moves all 5"
    )
    
    msg_text = "\n".join(lines)
    
    try:
        result = telegram_msg(msg_text)
        msg_id = result.get("result", {}).get("message_id", "")
        log(f"Digest sent. Message ID: {msg_id}")
    except Exception as e:
        log(f"ERROR sending digest: {e}")
        return
    
    # ── Save state ──
    state = {
        "last_digest": now.isoformat(),
        "message_id": msg_id,
        "articles": [
            {
                "index": i + 1,
                "page_id": art["page_id"],
                "title": art["title"][:100],
                "url": art["url"],
                "format_score": art["format_score"],
                "formats": art["formats"],
                "angle": art["angle"][:200],
                "categories": art["categories"],
                "status": "pending",
            }
            for i, art in enumerate(top_articles)
        ]
    }
    json.dump(state, open(STATE_FILE, "w"), indent=2)
    log(f"State saved ({len(top_articles)} articles pending)")
    
    log("=== Done ===")

if __name__ == "__main__":
    main()
