#!/usr/bin/env python3
"""
RSS Content Intelligence — Daily Crawler v2
Fetches RSS/Atom feeds, deduplicates, saves to Notion, sends Telegram summary.
"""
import urllib.request, ssl, json, re, os
import xml.etree.ElementTree as ET
from datetime import datetime
from dateutil import parser as dateparser

# ── Config ────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(f"{BASE}/../config/rss-intelligence.json"))
TOKEN = CFG["notion_token"]
DB = CFG["database_id"]
FEEDS = CFG["feeds"]
STATE_FILE = CFG.get("state_file", f"{BASE}/../data/rss-intelligence-state.json")
TELEGRAM_BOT = "8213291111:AAHCk2J4XIRQaTsBkACl_Xpla7LFvVx1304"
TELEGRAM_CHAT = "866838380"
os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

# ── State ─────────────────────────────────────────────────────────────────────
state = json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {"seen_urls": []}
seen = set(state["seen_urls"])

# ── HTTP ─────────────────────────────────────────────────────────────────────
ctx = ssl.create_default_context()

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 RSS-Intelligence/1.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
        return r.read()

# ── XML cleaning ─────────────────────────────────────────────────────────────
def clean_xml(raw_bytes):
    text = raw_bytes.decode("utf-8", errors="replace")
    # mobihealthnews: atom:link without xmlns:atom declaration
    if "<atom:" in text and "xmlns:atom" not in text:
        text = text.replace(
            'xmlns="http://www.w3.org/2005/Atom"',
            'xmlns="http://www.w3.org/2005/Atom" xmlns:atom="http://www.w3.org/2005/Atom"'
        )
    try:
        return ET.fromstring(text.encode())
    except ET.ParseError:
        # Strip broken namespace declarations as last resort
        cleaned = re.sub(r'xmlns:[a-zA-Z0-9]+="[^"]+"', '', text)
        return ET.fromstring(cleaned.encode())

# ── Atom/RSS namespace-aware element finder ────────────────────────────────────
def find_all(element, tag_name):
    """Find all elements matching tag_name (case-insensitive), handling namespaces."""
    results = []
    tag_lower = tag_name.lower()
    for el in element.iter():
        el_tag = el.tag.lower().replace("{http://www.w3.org/2005/Atom}", "")
        el_tag = el_tag.replace("{http://purl.org/rss/1.0/modules/content/}", "")
        if tag_lower in el_tag:
            results.append(el)
    return results

def find_first(element, tag_name):
    results = find_all(element, tag_name)
    return results[0] if results else None

# ── Feed parser ────────────────────────────────────────────────────────────────
def parse_feed(url, category):
    raw = fetch(url)
    root = clean_xml(raw)
    source_name = url.split("/")[2]
    ATOM_NS = "http://www.w3.org/2005/Atom"
    RSS_NS = "http://purl.org/rss/1.0/"
    items = root.findall(".//item")
    if not items:
        items = root.findall(f".//{{{ATOM_NS}}}item")
    if not items:
        items = root.findall(f".//{{{ATOM_NS}}}entry")
    results = []
    for item in items:
        title_el = find_first(item, "title")
        title = title_el.text.strip() if (title_el is not None and title_el.text) else ""
        link = ""
        for link_el in find_all(item, "link"):
            href = link_el.get("href", "")
            if href.startswith("http"):
                link = href
                break
            if link_el.text and link_el.text.strip().startswith("http"):
                link = link_el.text.strip()
                break
        if link and link not in seen:
            results.append((title, link, item))
    return results, source_name

# ── Notion ────────────────────────────────────────────────────────────────────
def notion_req(path, method="GET", body=None):
    url = f"https://api.notion.com/v1{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
        return json.loads(r.read())

def add_article(title, link, item, category, source_name):
    pub_date = ""
    for pel in find_all(item, "pubdate") + find_all(item, "published") + find_all(item, "date"):
        if pel.text:
            try:
                pub_date = dateparser.parse(pel.text).strftime("%Y-%m-%d")
                break
            except:
                pass
    description = ""
    for del_ in find_all(item, "description") + find_all(item, "summary") + find_all(item, "content"):
        if del_.text:
            desc = re.sub(r"<[^>]+>", "", del_.text).strip()
            if desc:
                description = desc[:500]
                break
    body = {
        "parent": {"database_id": DB},
        "properties": {
            "Name": {"title": [{"text": {"content": title[:200]}}]},
            "Category": {"multi_select": [{"name": category}]},
            "Source": {"rich_text": [{"text": {"content": source_name}}]},
            "URL": {"url": link},
            "Status": {"select": {"name": "New"}},
        }
    }
    if pub_date:
        body["properties"]["Published"] = {"date": {"start": pub_date}}
    if description:
        body["properties"]["Summary"] = {"rich_text": [{"text": {"content": description[:200]}}]}
    try:
        notion_req("/pages", method="POST", body=body)
        return True, title[:60]
    except Exception as e:
        return False, str(e)[:100]

# ── Telegram ─────────────────────────────────────────────────────────────────
def telegram_msg(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT}/sendMessage"
    data = json.dumps({"chat_id": TELEGRAM_CHAT, "text": text, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        return json.loads(r.read())

# ── Main ─────────────────────────────────────────────────────────────────────
print(f"[{datetime.now().strftime('%H:%M:%S')}] RSS Intelligence Crawler v2")
print(f"Feeds: {len(FEEDS)} | Seen URLs: {len(seen)}")

new_count = 0
new_articles = []
errors = []

for category, url in FEEDS.items():
    try:
        articles, source_name = parse_feed(url, category)
        print(f"  {category}: {len(articles)} new")
        for title, link, item in articles:
            ok, result = add_article(title, link, item, category, source_name)
            if ok:
                seen.add(link)
                new_count += 1
                new_articles.append((category, title, link))
                print(f"    + {title[:65]}")
            else:
                errors.append(f"{category}/{title[:30]}: {result}")
    except Exception as e:
        print(f"  FAIL {category}: {e}")
        errors.append(f"{category}: {e}")

# Save state
state["seen_urls"] = list(seen)[-50000:]
json.dump(state, open(STATE_FILE, "w"))

# Telegram
if new_count > 0:
    lines = [f"<b>RSS Intelligence</b> — {new_count} new article{'s' if new_count > 1 else ''}\n"]
    for cat, title, link in new_articles[:10]:
        lines.append(f"• <b>{cat}</b>: {title[:65]}\n  {link[:90]}")
    if len(new_articles) > 10:
        lines.append(f"\n<i>+{len(new_articles)-10} more</i>")
    if errors:
        lines.append(f"\n⚠️ Errors: {len(errors)}")
    try:
        telegram_msg("\n".join(lines))
        print(f"\nTelegram: sent ({new_count} articles)")
    except Exception as e:
        print(f"\nTelegram FAIL: {e}")
else:
    print("\nNo new articles.")

print(f"\nDone. {new_count} new added. {len(seen)} total in state.")
