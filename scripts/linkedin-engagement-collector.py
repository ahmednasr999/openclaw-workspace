#!/usr/bin/env python3
"""
linkedin-engagement-collector.py - Scrapes LinkedIn profile activity page
to collect post engagement data (reactions, comments) using Playwright.

Output: data/linkedin-engagement.json
Updates: Notion Content Calendar with engagement metrics

Requires: playwright, LinkedIn cookies
"""
import os
import json, re, sys, os
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
OUTPUT_FILE = DATA_DIR / "linkedin-engagement.json"
COOKIE_FILE = Path("/root/.openclaw/media/inbound/www.linkedin.com_cookies---c22104a1-b837-4ea4-b22f-29275813363b.txt")
NOTION_TOKEN = json.load(open(os.path.expanduser("~/.openclaw/workspace/config/notion.json")))["token"]
CONTENT_DB = "3268d599-a162-814b-8854-c9b8bde62468"
CAIRO = timezone(timedelta(hours=2))


def load_cookies():
    from http.cookiejar import MozillaCookieJar
    jar = MozillaCookieJar()
    jar.load(str(COOKIE_FILE), ignore_discard=True, ignore_expires=True)
    return [{"name": c.name, "value": c.value, "domain": c.domain, "path": c.path or "/"} for c in jar]


def scrape_engagement():
    """Scrape LinkedIn activity page for post URNs and engagement counts."""
    from playwright.sync_api import sync_playwright
    
    cookies = load_cookies()
    print(f"Loaded {len(cookies)} cookies")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 900}
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()
        
        page.goto("https://www.linkedin.com/in/ahmednasr/recent-activity/all/",
                   wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(8000)
        
        # Scroll to load more posts
        for _ in range(5):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000)
        
        # Extract structured data from each post
        posts = page.evaluate("""
        () => {
            const posts = [];
            const urnEls = document.querySelectorAll('[data-urn]');
            
            for (const el of urnEls) {
                const urn = el.getAttribute('data-urn');
                if (!urn || !urn.includes('activity')) continue;
                
                // Get post text (first paragraph-like content)
                const textEls = el.querySelectorAll('.feed-shared-update-v2__description, .break-words, [dir="ltr"]');
                let text = '';
                for (const te of textEls) {
                    const t = te.innerText.trim();
                    if (t.length > 20 && t.length > text.length) {
                        text = t.substring(0, 500);
                    }
                }
                
                // Get engagement from aria-labels
                let reactions = 0;
                let comments = 0;
                
                const ariaEls = el.querySelectorAll('[aria-label]');
                for (const ae of ariaEls) {
                    const label = ae.getAttribute('aria-label');
                    const reactionMatch = label.match(/(\\d+)\\s*reaction/i);
                    const commentMatch = label.match(/(\\d+)\\s*comment/i);
                    if (reactionMatch) reactions = parseInt(reactionMatch[1]);
                    if (commentMatch) comments = parseInt(commentMatch[1]);
                }
                
                // Get time element
                const timeEl = el.querySelector('time, [datetime]');
                const timeText = timeEl ? (timeEl.getAttribute('datetime') || timeEl.innerText) : '';
                
                posts.push({urn, text, reactions, comments, time: timeText});
            }
            
            return posts;
        }
        """)
        
        browser.close()
    
    print(f"Scraped {len(posts)} posts")
    return posts


def load_notion_posts():
    """Load posted content from Notion Content Calendar."""
    import ssl
    from urllib.request import Request, urlopen
    
    body = {
        "filter": {"property": "Status", "select": {"equals": "Posted"}},
        "page_size": 50,
        "sorts": [{"property": "Planned Date", "direction": "descending"}]
    }
    headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
    req = Request(f"https://api.notion.com/v1/databases/{CONTENT_DB}/query",
                  data=json.dumps(body).encode(), headers=headers, method="POST")
    with urlopen(req, context=ssl.create_default_context()) as r:
        data = json.loads(r.read())
    
    posts = []
    for page in data.get("results", []):
        props = page.get("properties", {})
        title = (props.get("Title", {}).get("title", [{}])[0].get("plain_text", "") 
                 if props.get("Title", {}).get("title") else "")
        date = props.get("Planned Date", {}).get("date", {})
        post_url = ""
        for key in ["Post URL"]:
            if key in props and props[key].get("url"):
                post_url = props[key]["url"]
                break
        
        # Extract topic/hook
        hook = (props.get("Hook", {}).get("rich_text", [{}])[0].get("plain_text", "")
                if props.get("Hook", {}).get("rich_text") else "")
        topic = ""
        if "Topic" in props:
            sel = props["Topic"].get("select", {})
            topic = sel.get("name", "") if sel else ""
        
        posts.append({
            "page_id": page["id"],
            "title": title,
            "hook": hook,
            "topic": topic,
            "date": date.get("start", "") if date else "",
            "post_url": post_url,
        })
    
    return posts


def match_posts(scraped, notion_posts):
    """Match scraped posts to Notion entries by text similarity or URL."""
    from difflib import SequenceMatcher
    
    matched = []
    for sp in scraped:
        best_match = None
        best_score = 0
        
        # Try URL match first
        for np in notion_posts:
            if np["post_url"] and sp["urn"]:
                # Extract activity ID from URN
                urn_id = sp["urn"].split(":")[-1]
                if urn_id in np["post_url"]:
                    best_match = np
                    best_score = 1.0
                    break
        
        # Try text match
        if not best_match and sp["text"]:
            for np in notion_posts:
                # Compare scraped text with Notion title/hook
                compare_text = np["title"] + " " + np.get("hook", "")
                score = SequenceMatcher(None, sp["text"][:100].lower(), compare_text[:100].lower()).ratio()
                if score > best_score and score > 0.3:
                    best_score = score
                    best_match = np
        
        entry = {
            "urn": sp["urn"],
            "reactions": sp["reactions"],
            "comments": sp["comments"],
            "engagement": sp["reactions"] + sp["comments"],
            "text_preview": sp["text"][:100],
            "time": sp["time"],
        }
        
        if best_match:
            entry["notion_page_id"] = best_match["page_id"]
            entry["title"] = best_match["title"]
            entry["hook"] = best_match.get("hook", "")
            entry["topic"] = best_match.get("topic", "")
            entry["date"] = best_match.get("date", "")
            entry["match_score"] = round(best_score, 2)
        
        matched.append(entry)
    
    return matched


def analyze_patterns(matched):
    """Analyze engagement patterns across posts."""
    if len(matched) < 3:
        return {"error": "Not enough posts to analyze", "post_count": len(matched)}
    
    # Sort by engagement
    by_engagement = sorted(matched, key=lambda x: x["engagement"], reverse=True)
    
    # Basic stats
    engagements = [m["engagement"] for m in matched]
    avg_engagement = sum(engagements) / len(engagements)
    
    # Top vs bottom performers
    top = by_engagement[:3]
    bottom = by_engagement[-3:]
    
    # Text length analysis
    with_text = [m for m in matched if m.get("text_preview")]
    avg_text_len = sum(len(m["text_preview"]) for m in with_text) / max(1, len(with_text))
    
    return {
        "post_count": len(matched),
        "avg_engagement": round(avg_engagement, 1),
        "max_engagement": max(engagements),
        "min_engagement": min(engagements),
        "top_3": [{"title": t.get("title", t.get("text_preview", "?"))[:50], "engagement": t["engagement"], "reactions": t["reactions"], "comments": t["comments"]} for t in top],
        "bottom_3": [{"title": t.get("title", t.get("text_preview", "?"))[:50], "engagement": t["engagement"]} for t in bottom],
        "avg_text_length": round(avg_text_len),
        "collected_at": datetime.now(CAIRO).isoformat(),
    }


def main():
    print("=== LinkedIn Engagement Collector ===")
    print(f"Time: {datetime.now(CAIRO).strftime('%Y-%m-%d %H:%M')}")
    
    # Step 1: Scrape engagement data
    print("\n--- Scraping LinkedIn activity page ---")
    scraped = scrape_engagement()
    
    if not scraped:
        print("ERROR: No posts scraped. Cookies may be expired.")
        sys.exit(1)
    
    # Step 2: Load Notion posts
    print("\n--- Loading Notion Content Calendar ---")
    notion_posts = load_notion_posts()
    print(f"Notion posts: {len(notion_posts)}")
    
    # Step 3: Match scraped to Notion
    print("\n--- Matching posts ---")
    matched = match_posts(scraped, notion_posts)
    matched_count = sum(1 for m in matched if m.get("notion_page_id"))
    print(f"Matched: {matched_count}/{len(matched)}")
    
    # Step 4: Analyze patterns
    print("\n--- Analyzing patterns ---")
    analysis = analyze_patterns(matched)
    
    # Step 5: Save output
    output = {
        "collected_at": datetime.now(CAIRO).isoformat(),
        "posts": matched,
        "analysis": analysis,
    }
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {OUTPUT_FILE}")
    
    # Print summary
    print(f"\n=== Summary ===")
    print(f"Posts: {len(matched)}")
    print(f"Avg engagement: {analysis.get('avg_engagement', 0)}")
    print(f"Top post: {analysis.get('top_3', [{}])[0].get('title', '?')[:40]} ({analysis.get('top_3', [{}])[0].get('engagement', 0)} reactions+comments)")
    
    return output


if __name__ == "__main__":
    main()
