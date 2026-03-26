#!/usr/bin/env python3
"""
rss-to-content-calendar.py
============================
Bridges RSS Intelligence DB → Content Calendar DB.

Run: Daily via cron (before LinkedIn auto-poster runs)
  30 8 * * * python3 .../rss-to-content-calendar.py >> .../logs/rss-to-calendar.log 2>&1

What it does:
1. Query RSS Intelligence DB for articles with Status = "New" or "New (Unprocessed)"
2. For each unprocessed article:
   a. Check if already in Content Calendar (by URL dedup)
   b. If not → create Content Calendar entry with Status="Ideas"
3. Mark processed articles in RSS DB (change Status to "Ideas Queued")

Deduplication: Uses URL as unique key. If same URL already in Content Calendar, skip.
"""
import json, os, ssl, sys, re, time, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
LOG_FILE = WORKSPACE / "logs" / "rss-to-calendar.log"
os.makedirs(LOG_FILE.parent, exist_ok=True)

NOTION_TOKEN = json.load(open(WORKSPACE / "config" / "notion.json"))["token"]
RSS_DB = "32e8d599-a162-8180-9e3a-fbfc17a84e49"       # RSS Intelligence DB
CAL_DB = "3268d599-a162-814b-8854-c9b8bde62468"       # Content Calendar DB

CAIRO = timezone(timedelta(hours=2))

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# ── Logging ────────────────────────────────────────────────────────────────
def log(msg):
    ts = datetime.now(CAIRO).strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ── Notion helpers ─────────────────────────────────────────────────────────
def notion_req(method, path, body=None):
    url = f"https://api.notion.com/v1{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20, context=ssl.create_default_context()) as r:
        return json.loads(r.read())

def query_db(db_id, filter_body=None, page_size=100):
    """Query all pages in a DB (handles pagination)."""
    all_results = []
    cursor = None
    while True:
        body = {"page_size": page_size}
        if cursor:
            body["start_cursor"] = cursor
        if filter_body:
            body["filter"] = filter_body
        d = notion_req("POST", f"/databases/{db_id}/query", body)
        all_results.extend(d.get("results", []))
        cursor = d.get("next_cursor")
        if not cursor:
            break
    return all_results

# ── Get existing Content Calendar URLs (for dedup) ─────────────────────────
def get_existing_cal_titles():
    """Get all titles already in Content Calendar to avoid duplicates."""
    pages = query_db(CAL_DB)
    titles = set()
    for p in pages:
        props = p.get("properties", {})
        title = "".join([t.get("plain_text","") for t in props.get("Title",{}).get("title",[])])
        if title:
            titles.add(title.lower().strip())
    log(f"  Content Calendar has {len(titles)} existing entries (by title)")
    return titles

# ── Get unprocessed RSS articles ──────────────────────────────────────────
def get_unprocessed_rss_articles():
    """Get ONLY High-priority (Gold) articles from RSS DB that haven't been sent to Content Calendar.
    The Content Factory scorer must run first to score articles. Only Gold items move to Calendar."""
    pages = query_db(RSS_DB, {
        "and": [
            {"property": "Status", "select": {"equals": "Read"}},
            {"property": "Priority", "select": {"equals": "High"}},
            {"property": "Quality Score", "number": {"is_not_empty": True}},
        ]
    })
    log(f"  RSS DB: {len(pages)} Gold articles ready for Content Calendar")
    return pages

# ── Create Content Calendar entry ─────────────────────────────────────────
def create_content_calendar_entry(article_props, title, url, category, summary, published_date):
    """Create a new entry in Content Calendar DB with scoring data from RSS Intelligence."""
    summary = (summary or "")[:500].strip()
    
    # Extract scoring data from RSS article
    posting_angle = "".join([t.get("plain_text","") for t in article_props.get("Posting Angle",{}).get("rich_text",[])])
    exec_summary = "".join([t.get("plain_text","") for t in article_props.get("Executive Summary",{}).get("rich_text",[])])
    post_formats = [f.get("name","") for f in article_props.get("Post Format",{}).get("multi_select",[])]
    quality_score = article_props.get("Quality Score",{}).get("number", 0)
    source = "".join([t.get("plain_text","") for t in article_props.get("Source",{}).get("rich_text",[])])
    
    # Build hook from posting angle (better than raw summary)
    hook = posting_angle[:300] if posting_angle else summary[:300]
    format_tag = " | ".join(post_formats) if post_formats else ""
    
    body = {
        "parent": {"database_id": CAL_DB},
        "properties": {
            "Title": {"title": [{"text": {"content": title[:200]}}]},
            "Topic": {"select": {"name": category or "General"}},
            "Status": {"select": {"name": "Ideas"}},
            "Hook": {"rich_text": [{"text": {"content": hook}}] if hook else []},
        }
    }
    
    if published_date:
        body["properties"]["Planned Date"] = {"date": {"start": published_date}}
    
    # Add article URL as first block (not a property — stored in page body)
    blocks = []
    if url:
        blocks.append({
            "object": "block",
            "type": "bookmark",
            "bookmark": {"url": url, "caption": []}
        })
    
    try:
        result = notion_req("POST", "/pages", body)
        page_id = result.get("id", "")
        
        # Add article URL as bookmark block (visible in page body)
        if url and page_id:
            time.sleep(0.5)
            notion_req("PATCH", f"/blocks/{page_id}/children", {
                "children": blocks
            })
        
        return True, page_id[:20]
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()[:200]
        return False, f"HTTP {e.code}: {body_err}"
    except Exception as e:
        return False, str(e)

def mark_rss_article_processed(page_id):
    """Update RSS article Status from 'New' to 'Read' (queued for content)."""
    try:
        notion_req("PATCH", f"/pages/{page_id}", {
            "properties": {
                "Status": {"select": {"name": "Read"}}
            }
        })
        return True
    except Exception as e:
        log(f"  ⚠️ Could not mark {page_id[:20]} as processed: {e}")
        return False

# ── Extract article metadata ───────────────────────────────────────────────
def extract_article_data(page):
    props = page.get("properties", {})
    name = "".join([t.get("plain_text", "") for t in props.get("Name", {}).get("title", [])])
    url = props.get("URL", {}).get("url") or ""
    category = props.get("Category", {}).get("multi_select", [{}])
    category = category[0].get("name", "") if category else ""
    summary = "".join([t.get("plain_text", "") for t in props.get("Summary", {}).get("rich_text", [])])
    published = props.get("Published", {}).get("date", {})
    published = published.get("start", "") if published else ""
    return name, url, category, summary, published

# ── Main ──────────────────────────────────────────────────────────────────
def main():
    now = datetime.now(CAIRO)
    log(f"=== RSS → Content Calendar Bridge === {now.strftime('%Y-%m-%d %H:%M')} Cairo")
    
    # Check state - only run once per day
    state_file = DATA_DIR / "rss-to-calendar-state.json"
    today = now.strftime("%Y-%m-%d")
    if state_file.exists():
        state = json.load(open(state_file))
        if state.get("last_run") == today:
            log(f"  Already ran today ({today}). Skipping.")
            return
    
    # Get existing Content Calendar titles (dedup by title)
    log("  Fetching existing Content Calendar entries...")
    existing_titles = get_existing_cal_titles()
    
    # Get unprocessed RSS articles
    log("  Fetching unprocessed RSS articles...")
    rss_pages = get_unprocessed_rss_articles()
    log(f"  {len(rss_pages)} articles to process")
    
    added = 0
    skipped_dup = 0
    errors = 0
    
    for page in rss_pages:
        name, url, category, summary, published = extract_article_data(page)
        page_id = page.get("id", "")
        
        # Dedupe by title
        title_key = name.lower().strip()
        if title_key in existing_titles:
            skipped_dup += 1
            mark_rss_article_processed(page_id)
            continue
        
        log(f"  + {name[:60]}")
        
        ok, result = create_content_calendar_entry(
            article_props=page.get("properties", {}),
            title=name,
            url=url,
            category=category,
            summary=summary,
            published_date=published
        )
        
        if ok:
            added += 1
            existing_titles.add(title_key)  # prevent double-add in same run
            mark_rss_article_processed(page_id)
            time.sleep(1)  # Notion rate limit
        else:
            log(f"    ERROR: {result}")
            errors += 1
    
    log(f"\n=== Done ===")
    log(f"  Added to Content Calendar: {added}")
    log(f"  Skipped (duplicate title): {skipped_dup}")
    log(f"  Errors: {errors}")
    
    # Save state
    state = {"last_run": today, "added": added, "skipped_dup": skipped_dup}
    json.dump(state, open(state_file, "w"), indent=2)
    
    return 0 if errors == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
