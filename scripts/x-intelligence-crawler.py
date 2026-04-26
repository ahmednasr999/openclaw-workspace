#!/usr/bin/env python3
"""
X (Twitter) Content Intelligence Crawler
Scrapes top tweets per category via Ahmed-Mac Chrome browser,
saves to the same Notion RSS Intelligence DB.

Usage:
    python3 x-intelligence-crawler.py          # run all categories
    python3 x-intelligence-crawler.py --dry-run # print results, no Notion save
"""

import json, os, sys, ssl, re, urllib.request, time, subprocess, tempfile
from datetime import datetime, date
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
CFG_NOTION = json.load(open(f"{BASE}/../config/notion.json"))
NOTION_TOKEN = CFG_NOTION["token"]
NOTION_DB = "32e8d599-a162-8180-9e3a-fbfc17a84e49"  # X Intelligence DB
STATE_FILE = f"{BASE}/../data/x-intelligence-state.json"
DRY_RUN = "--dry-run" in sys.argv
PREFLIGHT_ONLY = "--preflight-only" in sys.argv

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
def run_cli(cmd, timeout=45):
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as e:
        return 1, str(e)

def preflight():
    """Fail fast when Ahmed-Mac Chrome browser access is not ready."""
    checks = []
    node_id = os.environ.get("X_INTELLIGENCE_NODE_ID", "f43e25edb0df8786349f43738612bed403b7df5f225eb3617232d5b630ba1207")

    rc, out = run_cli(["openclaw", "nodes", "describe", "--node", node_id], timeout=45)
    node_ok = rc == 0 and "Ahmed-Mac" in out and "paired" in out and "connected" in out and "browser" in out
    checks.append(("Ahmed-Mac node connected with browser capability", node_ok, out.strip()[-1000:]))

    rc, out = run_cli(["openclaw", "browser", "doctor"], timeout=60)
    doctor_ok = rc == 0 and "OK plugin: enabled" in out and "OK browser: running" in out
    checks.append(("OpenClaw browser doctor passes", doctor_ok, out.strip()[-1000:]))

    rc, out = run_cli(["openclaw", "browser", "profiles"], timeout=45)
    chrome_ok = rc == 0 and "chrome: running" in out
    checks.append(("Ahmed-Mac chrome profile running", chrome_ok, out.strip()[-1000:]))

    failures = [(name, detail) for name, ok, detail in checks if not ok]
    print("Preflight:")
    for name, ok, _ in checks:
        print(f"  {'OK' if ok else 'FAIL'} {name}")

    if failures:
        print("\nPreflight failed. X Intelligence Crawler needs Ahmed-Mac online and Chrome profile running.")
        for name, detail in failures:
            print(f"\n[{name}]\n{detail[:1000]}")
        return False
    return True

def browser_cli(args, timeout=90):
    """Run the supported OpenClaw browser CLI against Ahmed-Mac Chrome."""
    cmd = ["openclaw", "browser", "--browser-profile", "chrome", "--json", *args]
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    except Exception as e:
        return {"ok": False, "error": str(e), "cmd": " ".join(cmd)}
    output = (p.stdout or "") + (p.stderr or "")
    if p.returncode != 0:
        return {"ok": False, "error": output.strip()[-2000:], "cmd": " ".join(cmd)}
    try:
        decoder = json.JSONDecoder()
        parsed = None
        stdout = p.stdout or ""
        for i, ch in enumerate(stdout):
            if ch not in "[{":
                continue
            try:
                parsed, _ = decoder.raw_decode(stdout[i:])
                break
            except Exception:
                continue
        if parsed is None:
            raise ValueError("no JSON payload found")
        if isinstance(parsed, dict):
            parsed.setdefault("ok", True)
            return parsed
        return {"ok": True, "result": parsed}
    except Exception:
        return {"ok": True, "result": p.stdout.strip()}


def browser_call(action, **kwargs):
    """Compatibility wrapper using the current browser CLI, not the retired /api/browser path."""
    if action == "open":
        res = browser_cli(["open", kwargs["url"]], timeout=90)
        if "targetId" in res and "ok" not in res:
            res["ok"] = True
        return res
    if action == "navigate":
        args = ["navigate", kwargs["url"]]
        if kwargs.get("target_id"):
            args += ["--target-id", kwargs["target_id"]]
        return browser_cli(args, timeout=90)
    if action == "evaluate":
        args = ["evaluate", "--fn", "() => " + kwargs["expression"]]
        if kwargs.get("target_id"):
            args += ["--target-id", kwargs["target_id"]]
        return browser_cli(args, timeout=90)
    if action == "close":
        args = ["close"]
        if kwargs.get("target_id"):
            args.append(kwargs["target_id"])
        return browser_cli(args, timeout=45)
    return {"ok": False, "error": f"Unsupported browser action: {action}"}

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

            function parseMetric(s) {
                s = (s || '').toString().trim();
                var m = s.match(/[0-9]+(?:\.[0-9]+)?\s*[KMB]?/i);
                if (!m) return 0;
                var token = m[0].replace(/\s+/g, '');
                var n = parseFloat(token);
                if (/K$/i.test(token)) n *= 1000;
                else if (/M$/i.test(token)) n *= 1000000;
                else if (/B$/i.test(token)) n *= 1000000000;
                return Math.round(n || 0);
            }

            // engagement
            var likes = 0, retweets = 0, replies = 0;
            var buttons = a.querySelectorAll('[data-testid="reply"], [data-testid="retweet"], [data-testid="like"]');
            buttons.forEach(function(el) {
                var testId = el.getAttribute('data-testid') || '';
                var label = el.getAttribute('aria-label') || '';
                var txt = el.innerText || '';
                var val = parseMetric(label || txt);
                if (testId === 'like') likes = val;
                else if (testId === 'retweet') retweets = val;
                else if (testId === 'reply') replies = val;
            });
            if (!likes && !retweets && !replies) {
                var aggregate = Array.from(a.querySelectorAll('[aria-label]')).map(function(el) { return el.getAttribute('aria-label') || ''; }).join(' | ');
                var lm = aggregate.match(/([0-9,.]+\s*[KMB]?)\s+likes?/i);
                var rm = aggregate.match(/([0-9,.]+\s*[KMB]?)\s+reposts?/i);
                var pm = aggregate.match(/([0-9,.]+\s*[KMB]?)\s+repl/i);
                likes = lm ? parseMetric(lm[1]) : 0;
                retweets = rm ? parseMetric(rm[1]) : 0;
                replies = pm ? parseMetric(pm[1]) : 0;
            }

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

    # Open a dedicated tab so the crawler does not hijack Ahmed's current Chrome tab.
    nav = browser_call("open", url=search_url)
    if not nav.get("ok"):
        print(f"    FAIL open: {nav}")
        return []
    target_id = nav.get("targetId") or nav.get("target_id")
    time.sleep(6)  # let results load

    # Extract posts
    result = browser_call("evaluate", expression=EXTRACT_JS, target_id=target_id)
    if "error" in result or not result.get("ok"):
        print(f"    FAIL evaluate: {result}")
        if target_id:
            browser_call("close", target_id=target_id)
        return []

    raw = result.get("result", result.get("value", "[]"))
    if isinstance(raw, dict):
        raw = raw.get("value", raw.get("result", raw))
    if isinstance(raw, str):
        try:
            posts = json.loads(raw)
        except Exception:
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

    if target_id:
        browser_call("close", target_id=target_id)
    print(f"    Found {len(filtered)} new posts")
    return filtered[:3]  # top 3 per category

# ── Main ───────────────────────────────────────────────────────────────────
print(f"[{datetime.now().strftime('%H:%M:%S')}] X Intelligence Crawler")
print(f"Categories: {len(SEARCHES)} | Dry run: {DRY_RUN} | Known URLs: {len(seen)}")
print()

if not preflight():
    sys.exit(2)
if PREFLIGHT_ONLY:
    print("Preflight only: OK")
    sys.exit(0)

all_posts = []

categories_to_run = SEARCHES.items()
if "--smoke-category" in sys.argv:
    idx = sys.argv.index("--smoke-category")
    wanted = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "AI"
    categories_to_run = [(wanted, SEARCHES[wanted])] if wanted in SEARCHES else list(SEARCHES.items())[:1]

for category, query in categories_to_run:
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
