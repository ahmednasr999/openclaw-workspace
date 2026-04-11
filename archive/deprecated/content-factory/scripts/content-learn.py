#!/usr/bin/env python3
"""
content-learn.py — LEARN layer for Content Agent.

Reads engagement data + Notion Content Calendar, computes performance metrics,
updates references/content-performance.json and references/content-mix.md.

Usage:
  python3 content-learn.py              # Normal weekly run
  python3 content-learn.py --backfill   # Backfill from Notion + engagement data
  python3 content-learn.py --dry-run    # Print what would be updated
"""

import json, os, re, sys, ssl
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
REFS_DIR = WORKSPACE / "skills" / "content-agent" / "references"
PERF_FILE = REFS_DIR / "content-performance.json"
MIX_FILE = REFS_DIR / "content-mix.md"
ENGAGEMENT_DIR = DATA_DIR / "linkedin-engagement"
POSTS_REGISTRY = DATA_DIR / "linkedin-posts.json"
RESEARCH_LOG = DATA_DIR / "linkedin-research-log.json"
ENGAGEMENT_DATA = DATA_DIR / "linkedin-engagement.json"

NOTION_TOKEN = json.load(open(os.path.expanduser("~/.openclaw/workspace/config/notion.json")))["token"]
CONTENT_DB = "3268d599-a162-814b-8854-c9b8bde62468"
CAIRO = timezone(timedelta(hours=2))

DRY_RUN = "--dry-run" in sys.argv
BACKFILL = "--backfill" in sys.argv


def notion_query(database_id, body=None):
    """Query Notion database."""
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    all_results = []
    has_more = True
    start_cursor = None
    
    while has_more:
        req_body = body.copy() if body else {}
        if start_cursor:
            req_body["start_cursor"] = start_cursor
        
        req = Request(url, data=json.dumps(req_body).encode(), headers=headers, method="POST")
        try:
            ctx = ssl.create_default_context()
            with urlopen(req, timeout=30, context=ctx) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            print(f"  Notion API error: {e}")
            break
        
        all_results.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
    
    return all_results


def load_notion_posts():
    """Load all posted content from Notion."""
    body = {
        "filter": {"property": "Status", "select": {"equals": "Posted"}},
        "sorts": [{"property": "Planned Date", "direction": "descending"}]
    }
    pages = notion_query(CONTENT_DB, body)
    
    posts = []
    for page in pages:
        props = page.get("properties", {})
        
        def get_title(p):
            t = p.get("title", [])
            return t[0]["plain_text"] if t else ""
        
        def get_text(p):
            t = p.get("rich_text", [])
            return t[0]["plain_text"] if t else ""
        
        def get_select(p):
            s = p.get("select")
            return s["name"] if s else ""
        
        def get_date(p):
            d = p.get("date")
            return d["start"] if d else ""
        
        def get_url(p):
            return p.get("url", "")
        
        post = {
            "page_id": page["id"],
            "title": "",
            "hook": "",
            "topic": "",
            "date": "",
            "post_url": "",
            "day": "",
        }
        
        for key, prop in props.items():
            k = key.lower().strip()
            pt = prop.get("type")
            if pt == "title":
                post["title"] = get_title(prop)
            elif k == "hook" and pt == "rich_text":
                post["hook"] = get_text(prop)
            elif k == "topic" and pt == "select":
                post["topic"] = get_select(prop)
            elif k in ("planned date", "date") and pt == "date":
                post["date"] = get_date(prop)
            elif k == "post url" and pt == "url":
                post["post_url"] = get_url(prop)
            elif k == "day" and pt == "select":
                post["day"] = get_select(prop)
            elif k == "draft" and pt == "rich_text":
                post["draft"] = get_text(prop)
        
        posts.append(post)
    
    return posts


def load_engagement_snapshots():
    """Load all engagement snapshots from data/linkedin-engagement/."""
    snapshots = {}
    if not ENGAGEMENT_DIR.exists():
        return snapshots
    
    for f in ENGAGEMENT_DIR.glob("*.json"):
        try:
            data = json.load(open(f))
            activity_id = data.get("activity_id", f.stem)
            snapshots[activity_id] = data
        except:
            pass
    
    return snapshots


def load_collector_data():
    """Load scraped engagement data from linkedin-engagement-collector."""
    if ENGAGEMENT_DATA.exists():
        try:
            return json.load(open(ENGAGEMENT_DATA))
        except:
            pass
    return {}


def classify_post_type(title, hook, draft=""):
    """Classify post into type: story, expertise, opinion, data, bts."""
    text = (title + " " + hook + " " + draft).lower()
    
    story_signals = ["i ", "my ", "when i", "years ago", "learned", "hired", "built", "managed"]
    opinion_signals = ["unpopular", "controversial", "disagree", "hot take", "wrong about", "stop ", "don't "]
    data_signals = ["%", "data", "survey", "research", "study", "statistic", "number", "metric"]
    bts_signals = ["behind the scenes", "bts", "how i", "my process", "my workflow", "day in"]
    
    if any(s in text for s in story_signals):
        return "story"
    if any(s in text for s in opinion_signals):
        return "opinion"
    if any(s in text for s in data_signals):
        return "data"
    if any(s in text for s in bts_signals):
        return "bts"
    return "expertise"


def classify_pillar(title, topic, hook=""):
    """Classify post pillar: pmo, ai, transformation, leadership, personal."""
    text = (title + " " + topic + " " + hook).lower()
    
    if any(w in text for w in ["pmo", "program manage", "project manage", "portfolio", "governance"]):
        return "pmo"
    if any(w in text for w in ["ai", "artificial intelligence", "automation", "agent", "llm", "gpt"]):
        return "ai"
    if any(w in text for w in ["transform", "digital", "moderniz", "legacy", "migration"]):
        return "transformation"
    if any(w in text for w in ["leader", "team", "executive", "hire", "culture", "management"]):
        return "leadership"
    return "personal"


def classify_hook_style(hook):
    """Classify hook style: bold_claim, curiosity_gap, specific_story, question, stat."""
    h = hook.lower()
    if "?" in hook:
        return "question"
    if any(c in h for c in ["%", "number", "data", "$"]):
        return "stat"
    if any(w in h for w in ["i ", "my ", "when"]):
        return "specific_story"
    if any(w in h for w in ["never", "always", "stop", "don't", "worst", "best"]):
        return "bold_claim"
    return "curiosity_gap"


def build_performance_entries(notion_posts, snapshots, collector_data):
    """Build performance entries from all data sources."""
    entries = []
    
    # Index collector data by page_id or text match
    collector_by_title = {}
    if collector_data and "posts" in collector_data:
        for cp in collector_data["posts"]:
            title = cp.get("title", "")
            if title:
                collector_by_title[title.lower()[:40]] = cp
    
    for np in notion_posts:
        date = np.get("date", "")
        title = np.get("title", "")
        hook = np.get("hook", "")
        topic = np.get("topic", "")
        post_url = np.get("post_url", "")
        draft = np.get("draft", "")
        
        # Try to find engagement data
        reactions = 0
        comments = 0
        
        # Match by activity URN in URL
        activity_id = ""
        if post_url:
            m = re.search(r'activity[/-](\d+)', post_url)
            if m:
                activity_id = m.group(1)
        
        # Check reaction tracker snapshots
        if activity_id and activity_id in snapshots:
            snap = snapshots[activity_id]
            if snap.get("snapshots"):
                latest = snap["snapshots"][-1]
                reactions = latest.get("reaction_count", 0)
        
        # Check collector data
        title_key = title.lower()[:40]
        if title_key in collector_by_title:
            cd = collector_by_title[title_key]
            reactions = max(reactions, cd.get("reactions", 0))
            comments = max(comments, cd.get("comments", 0))
        
        entry = {
            "date": date,
            "title": title[:50] if title else "Untitled",
            "post_type": classify_post_type(title, hook, draft),
            "pillar": classify_pillar(title, topic, hook),
            "hook_style": classify_hook_style(hook),
            "hook_text": hook[:100] if hook else "",
            "char_count": len(draft) if draft else 0,
            "has_image": bool(post_url),  # Rough proxy
            "image_genre": "none",
            "activity_urn": f"urn:li:activity:{activity_id}" if activity_id else "",
            "post_url": post_url,
            "reactions": reactions,
            "comments": comments,
            "reposts": 0,
            "engagement_rate": None,
            "impressions": None,
            "notes": ""
        }
        
        entries.append(entry)
    
    return entries


def compute_mix_stats(entries, window_days=28):
    """Compute content mix stats over a rolling window."""
    cutoff = (datetime.now(CAIRO) - timedelta(days=window_days)).strftime("%Y-%m-%d")
    recent = [e for e in entries if (e.get("date") or "") >= cutoff]
    
    total = len(recent) or 1
    
    type_counts = {}
    pillar_counts = {}
    hook_counts = {}
    
    for e in recent:
        pt = e.get("post_type", "unknown")
        type_counts[pt] = type_counts.get(pt, 0) + 1
        
        pl = e.get("pillar", "unknown")
        pillar_counts[pl] = pillar_counts.get(pl, 0) + 1
        
        hs = e.get("hook_style", "unknown")
        hook_counts[hs] = hook_counts.get(hs, 0) + 1
    
    return {
        "window_days": window_days,
        "total_posts": len(recent),
        "type_distribution": {k: round(v/total*100, 1) for k, v in type_counts.items()},
        "pillar_distribution": {k: round(v/total*100, 1) for k, v in pillar_counts.items()},
        "hook_distribution": {k: round(v/total*100, 1) for k, v in hook_counts.items()},
    }


def update_mix_md(mix_stats):
    """Update content-mix.md with actual stats."""
    targets = {"story": 30, "expertise": 25, "opinion": 20, "data": 15, "bts": 10}
    actual = mix_stats.get("type_distribution", {})
    
    type_table = ""
    for t in ["story", "expertise", "opinion", "data", "bts"]:
        pct = actual.get(t, 0)
        target = targets.get(t, 0)
        delta = round(pct - target, 1)
        sign = "+" if delta > 0 else ""
        type_table += f"| {t.title()} | {pct}% | {target}% | {sign}{delta}% |\n"
    
    pillar_dist = mix_stats.get("pillar_distribution", {})
    pillar_table = ""
    for p in ["pmo", "transformation", "ai", "leadership", "personal"]:
        count = 0
        pct = pillar_dist.get(p, 0)
        for k, v in pillar_dist.items():
            if k == p:
                count = round(v * mix_stats["total_posts"] / 100)
        pillar_table += f"| {p.upper()} | {count} | {pct}% | 30% |\n"
    
    content = f"""# Content Mix Tracker

## Target Ratios

| Type | Target % | Posts/Month (20 posts) |
|------|----------|----------------------|
| Story | 30% | 6 |
| Expertise | 25% | 5 |
| Opinion | 20% | 4 |
| Data | 15% | 3 |
| Behind-the-Scenes | 10% | 2 |

## Rules

- Check actual ratio over rolling 4-week window
- If any type is >10% off target, prioritize it in next batch
- Never do 3+ of the same type in a row (variety keeps the audience)
- Pillar rotation: no pillar should exceed 30% in any 2-week window

## Current Status

_Updated by content-learn.py on {datetime.now(CAIRO).strftime('%Y-%m-%d %H:%M')} Cairo._

| Type | Last 4 Weeks | Target | Delta |
|------|-------------|--------|-------|
{type_table}
## Pillar Distribution (Last 4 Weeks)

| Pillar | Count | % | Target Max |
|--------|-------|---|-----------|
{pillar_table}"""
    
    return content


def main():
    print("=== Content LEARN Layer ===")
    print(f"Time: {datetime.now(CAIRO).strftime('%Y-%m-%d %H:%M')}")
    print(f"Mode: {'BACKFILL' if BACKFILL else 'Weekly'} {'(DRY RUN)' if DRY_RUN else ''}")
    
    # Load existing performance data
    perf = json.load(open(PERF_FILE)) if PERF_FILE.exists() else {"posts": []}
    existing_urls = {p.get("post_url") for p in perf.get("posts", []) if p.get("post_url")}
    
    # Fetch Notion posts
    print("\n  Fetching Notion Content Calendar (Posted)...")
    notion_posts = load_notion_posts()
    print(f"  Found {len(notion_posts)} posted items in Notion")
    
    # Load engagement data
    print("  Loading engagement snapshots...")
    snapshots = load_engagement_snapshots()
    print(f"  Loaded {len(snapshots)} reaction snapshots")
    
    collector_data = load_collector_data()
    collector_count = len(collector_data.get("posts", [])) if collector_data else 0
    print(f"  Loaded {collector_count} collector entries")
    
    # Build entries
    new_entries = build_performance_entries(notion_posts, snapshots, collector_data)
    print(f"  Built {len(new_entries)} performance entries")
    
    # Merge: add new entries, update existing ones
    merged = {e.get("post_url"): e for e in perf.get("posts", []) if e.get("post_url")}
    added = 0
    updated = 0
    for entry in new_entries:
        url = entry.get("post_url")
        if not url:
            continue
        if url in merged:
            # Update reactions/comments if higher
            old = merged[url]
            if entry["reactions"] > old.get("reactions", 0):
                old["reactions"] = entry["reactions"]
                updated += 1
            if entry["comments"] > old.get("comments", 0):
                old["comments"] = entry["comments"]
                updated += 1
        else:
            merged[url] = entry
            added += 1
    
    all_posts = sorted(merged.values(), key=lambda x: x.get("date", ""), reverse=True)
    
    print(f"\n  New entries: {added}")
    print(f"  Updated entries: {updated}")
    print(f"  Total tracked: {len(all_posts)}")
    
    # Compute mix stats
    mix_stats = compute_mix_stats(all_posts)
    print(f"\n  Mix stats (last {mix_stats['window_days']} days, {mix_stats['total_posts']} posts):")
    for k, v in mix_stats.get("type_distribution", {}).items():
        print(f"    {k}: {v}%")
    
    # Compute engagement averages
    with_engagement = [p for p in all_posts if p.get("reactions", 0) > 0]
    if with_engagement:
        avg_reactions = sum(p["reactions"] for p in with_engagement) / len(with_engagement)
        avg_comments = sum(p.get("comments", 0) for p in with_engagement) / len(with_engagement)
        print(f"\n  Avg reactions: {avg_reactions:.1f}")
        print(f"  Avg comments: {avg_comments:.1f}")
    
    if DRY_RUN:
        print("\n  [DRY RUN] Would update content-performance.json and content-mix.md")
        return
    
    # Save performance data
    perf["posts"] = all_posts
    perf["metadata"]["last_updated"] = datetime.now(CAIRO).isoformat()
    perf["metadata"]["total_posts_tracked"] = len(all_posts)
    json.dump(perf, open(PERF_FILE, "w"), indent=2, ensure_ascii=False)
    print(f"\n  Saved {PERF_FILE}")
    
    # Update content-mix.md
    mix_content = update_mix_md(mix_stats)
    MIX_FILE.write_text(mix_content)
    print(f"  Saved {MIX_FILE}")
    
    print(f"\n=== LEARN complete: {len(all_posts)} posts tracked ===")


if __name__ == "__main__":
    main()
