#!/usr/bin/env python3
"""
X (Twitter) Content Intelligence Crawler
Scrapes top tweets per category via Ahmed-Mac Chrome browser,
saves to the same Notion RSS Intelligence DB.

Usage:
    python3 x-intelligence-crawler.py          # run all categories
    python3 x-intelligence-crawler.py --dry-run # print results, no Notion save
"""

import json, os, sys, ssl, re, urllib.request, time
from datetime import datetime, date

# ── Config ─────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
CFG_NOTION = json.load(open(f"{BASE}/../config/notion.json"))
NOTION_TOKEN = CFG_NOTION["token"]
NOTION_DB = "32e8d599-a162-8180-9e3a-fbfc17a84e49"  # X Intelligence DB
STATE_FILE = f"{BASE}/../data/x-intelligence-state.json"
DRY_RUN = "--dry-run" in sys.argv

OPENCLAW_CFG = json.load(open("/root/.openclaw/openclaw.json"))
GATEWAY_TOKEN = OPENCLAW_CFG.get("gateway", {}).get("auth", {}).get("token", "")

os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
state = json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {"seen_urls": []}
seen = set(state["seen_urls"])

ctx = ssl.create_default_context()

# ── X search queries per category ─────────────────────────────────────────
SEARCHES = {
    "Strategy": '"business strategy" OR "corporate strategy" OR "execution strategy" min_faves:200 min_retweets:100 lang:en',
    "Healthcare": '"healthcare AI" OR "hospital operations" OR "clinical AI" min_faves:200 min_retweets:100 lang:en',
    "HealthTech": '"digital health" OR healthtech OR "health technology" min_faves:200 min_retweets:100 lang:en',
    "FinTech": 'fintech OR "open banking" OR "digital payments" OR "embedded finance" min_faves:200 min_retweets:100 lang:en',
    "Digital Transformation": '"digital transformation" min_faves:300 min_retweets:100 lang:en',
    "PMO": '"project management" OR "program management" OR PMO min_faves:200 min_retweets:100 lang:en',
    "Operation Excellence": '"operational excellence" OR "process improvement" OR "lean management" min_faves:200 min_retweets:100 lang:en',
    "AI": '"artificial intelligence" OR "AI agents" OR "large language models" min_faves:300 min_retweets:100 lang:en',
}

# ── Browser helper (Ahmed-Mac Chrome via OpenClaw gateway) ─────────────────
def browser_call(action, **kwargs):
    """Call OpenClaw browser tool via gateway HTTP API."""
    url = "http://localhost:18789/api/browser"
    payload = {"action": action, "node": "Ahmed-Mac", **kwargs}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GATEWAY_TOKEN}",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}

# ── Notion helper ─────────────────────────────────────────────────────────
def notion_req(path, method="GET", body=None):
    url = f"https://api.notion.com/v1{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read())

def save_to_notion(title, url, summary, category, likes, retweets):
    today = date.today().isoformat()
    engagement = f"{likes}L / {retweets}RT"
    body = {
        "parent": {"database_id": NOTION_DB},
        "properties": {
            "Name":     {"title": [{"text": {"content": title[:200]}}]},
            "Category": {"multi_select": [{"name": category}]},
            "Source":   {"rich_text": [{"text": {"content": f"X (Twitter) - {engagement}"}}]},
            "URL":      {"url": url},
            "Status":   {"select": {"name": "New"}},
            "Published":{"date": {"start": today}},
            "Summary":  {"rich_text": [{"text": {"content": summary[:500]}}]},
        }
    }
    notion_req("/pages", method="POST", body=body)

# ── X scraper via browser evaluate ────────────────────────────────────────
EXTRACT_JS = r"""
(function() {
    var results = [];
    var articles = document.querySelectorAll('article[data-testid="tweet"], [data-testid="tweet"]');
    if (!articles.length) {
        // fallback: grab all articles
        articles = document.querySelectorAll('article');
    }
    articles.forEach(function(a) {
        try {
            var text = '';
            var textEls = a.querySelectorAll('[data-testid="tweetText"]');
            textEls.forEach(function(el) { text += el.innerText + ' '; });
            text = text.trim();
            if (!text) return;

            var authorEl = a.querySelector('[data-testid="User-Name"]');
            var author = authorEl ? authorEl.innerText.replace(/\n/g, ' ').trim() : '';

            var timeEl = a.querySelector('time');
            var postTime = timeEl ? timeEl.getAttribute('datetime') : '';

            // get post URL from the timestamp link
            var timeLink = timeEl ? timeEl.closest('a') : null;
            var postUrl = timeLink ? timeLink.href : '';

            // engagement
            var likes = 0, retweets = 0, replies = 0;
            var engEls = a.querySelectorAll('[data-testid$="-count"]');
            engEls.forEach(function(el) {
                var testId = el.getAttribute('data-testid') || '';
                var val = parseInt((el.innerText || '0').replace(/[^0-9]/g, '') || '0');
                if (testId.includes('like')) likes = val;
                else if (testId.includes('retweet')) retweets = val;
                else if (testId.includes('reply')) replies = val;
            });

            // skip promoted/ads
            if (a.innerText.includes('Promoted') || !text) return;

            results.push({
                text: text.substring(0, 300),
                author: author.substring(0, 80),
                url: postUrl,
                time: postTime,
                likes: likes,
                retweets: retweets,
                replies: replies
            });
        } catch(e) {}
    });
    return JSON.stringify(results.slice(0, 10));
})()
"""

def scrape_x_search(category, query):
    """Navigate to X search and extract top posts."""
    import urllib.parse
    encoded = urllib.parse.quote(query)
    search_url = f"https://x.com/search?q={encoded}&src=typed_query&f=top"

    print(f"  Searching: {category}...")

    # Navigate
    nav = browser_call("navigate", url=search_url)
    if not nav.get("ok"):
        print(f"    FAIL navigate: {nav}")
        return []
    time.sleep(3)  # let results load

    # Extract posts
    result = browser_call("evaluate", expression=EXTRACT_JS)
    if "error" in result or not result.get("ok"):
        print(f"    FAIL evaluate: {result}")
        return []

    raw = result.get("result", "[]")
    if isinstance(raw, str):
        try:
            posts = json.loads(raw)
        except:
            posts = []
    elif isinstance(raw, list):
        posts = raw
    else:
        posts = []

    # Filter: must have URL, skip already seen, reasonable engagement
    filtered = []
    for p in posts:
        url = p.get("url", "")
        if not url or url in seen:
            continue
        if "x.com" not in url and "twitter.com" not in url:
            continue
        # Skip posts with zero engagement (likely noise)
        if p.get("likes", 0) + p.get("retweets", 0) == 0:
            continue
        filtered.append(p)

    print(f"    Found {len(filtered)} new posts")
    return filtered[:3]  # top 3 per category

# ── Main ───────────────────────────────────────────────────────────────────
print(f"[{datetime.now().strftime('%H:%M:%S')}] X Intelligence Crawler")
print(f"Categories: {len(SEARCHES)} | Dry run: {DRY_RUN} | Known URLs: {len(seen)}")
print()

all_posts = []

for category, query in SEARCHES.items():
    posts = scrape_x_search(category, query)
    for p in posts:
        all_posts.append((category, p))
    time.sleep(2)

print(f"\nTotal collected: {len(all_posts)} posts")
print()

saved = 0
errors = []

for category, p in all_posts:
    url = p.get("url", "")
    text = p.get("text", "")
    author = p.get("author", "Unknown")
    likes = p.get("likes", 0)
    retweets = p.get("retweets", 0)
    title = f"[{author.split()[0] if author else 'X'}] {text[:100]}..."

    print(f"  [{category}] {likes}L/{retweets}RT | {text[:70]}...")

    if DRY_RUN:
        print(f"    URL: {url}")
        continue

    try:
        save_to_notion(title, url, text, category, likes, retweets)
        seen.add(url)
        saved += 1
        print(f"    Saved to Notion")
    except Exception as e:
        err = str(e)[:100]
        errors.append(f"{category}: {err}")
        print(f"    ERROR: {err}")

# Save state
if not DRY_RUN:
    state["seen_urls"] = list(seen)[-10000:]
    state["last_run"] = datetime.now().isoformat()
    json.dump(state, open(STATE_FILE, "w"))

print(f"\nDone. Saved: {saved} | Errors: {len(errors)}")
if errors:
    for e in errors:
        print(f"  ERROR: {e}")
