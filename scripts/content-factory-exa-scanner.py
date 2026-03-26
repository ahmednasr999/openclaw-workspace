#!/usr/bin/env python3
"""
Content Factory Exa Scanner v1.1
=================================
Phase 3: Uses Exa AI search to find trending content that RSS feeds miss.
Now includes X/Twitter and LinkedIn scanning via domain-filtered Exa searches.

Exa budget: ~12 searches/run x 3 runs/week = 36/week = ~156/month (well under 1,000 free tier).

Searches Ahmed's core topics with recency filter (last 3 days).
Deduplicates against RSS Intelligence DB, adds new finds with scores.

Sources: Articles (general web) + X/Twitter (hot takes, newsjacking) + LinkedIn (thought leaders)

Cron: 0 6 * * 1,3,5 (Mon/Wed/Fri at 8 AM Cairo - 3x/week)
"""
import json, os, ssl, sys, urllib.request, re, time
from datetime import datetime, timezone, timedelta

WORKSPACE = "/root/.openclaw/workspace"
NOTION_TOKEN = json.load(open(f"{WORKSPACE}/config/notion.json"))["token"]
RSS_DB = "32e8d599-a162-8180-9e3a-fbfc17a84e49"

TELEGRAM_BOT = "8213291111:AAHCk2J4XIRQaTsBkACl_Xpla7LFvVx1304"
TELEGRAM_CHAT = "866838380"
CAIRO = timezone(timedelta(hours=2))
STATE_FILE = f"{WORKSPACE}/data/rss-intelligence-state.json"

LOG_FILE = f"{WORKSPACE}/logs/content-factory-exa-scanner.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

ctx = ssl.create_default_context()

# Import scorer for scoring functions
sys.path.insert(0, f"{WORKSPACE}/scripts")
from importlib.util import spec_from_file_location, module_from_spec
spec = spec_from_file_location("scorer", f"{WORKSPACE}/scripts/content-factory-scorer.py")
scorer = module_from_spec(spec)
spec.loader.exec_module(scorer)

# ── Search query structure: (query, category, domain_filter) ─────────────────
# domain_filter: None = general web (exclude social), "x" = X/Twitter only, "linkedin" = LinkedIn only
SEARCH_SETS = {
    0: [  # Monday - Core topics + X hot takes
        ("AI transformation enterprise 2026", "AI", None),
        ("digital transformation healthcare results", "Digital Transformation", None),
        ("program management AI automation", "PMO", None),
        ("AI agents business operations", "AI", None),
        ("CIO CTO digital strategy", "Digital Transformation", None),
        ("project management AI tools", "PMO", None),
        ("enterprise AI implementation challenges", "AI", None),
        # X/Twitter - hot takes and breaking news
        ("AI agents replacing jobs hot take", "AI", "x"),
        ("digital transformation failure controversy", "Digital Transformation", "x"),
        # LinkedIn - thought leaders
        ("AI transformation executive leadership lessons", "AI", "linkedin"),
        ("program management office future PMO", "PMO", "linkedin"),
        ("digital transformation case study results", "Digital Transformation", "linkedin"),
    ],
    2: [  # Wednesday - Supporting topics + X trending + LinkedIn insights
        ("fintech disruption banking 2026", "FinTech", None),
        ("healthtech AI patient outcomes", "HealthTech", None),
        ("healthcare digital transformation results", "Healthcare", None),
        ("AI automation executive leadership", "AI", None),
        ("digital transformation ROI case study", "Digital Transformation", None),
        ("PMO transformation agile enterprise", "PMO", None),
        ("operational excellence AI automation", "Operation Excellence", None),
        # X/Twitter - industry buzz
        ("fintech AI disruption banking", "FinTech", "x"),
        ("healthcare AI announcement breakthrough", "HealthTech", "x"),
        # LinkedIn - industry voices
        ("healthcare technology transformation leadership", "Healthcare", "linkedin"),
        ("fintech innovation strategy executive", "FinTech", "linkedin"),
        ("AI implementation lessons learned enterprise", "AI", "linkedin"),
    ],
    4: [  # Friday - Hot takes + thought leadership + social pulse
        ("AI replacing jobs controversy", "AI", None),
        ("digital transformation failure lessons", "Digital Transformation", None),
        ("leadership strategy AI era", "Strategy", None),
        ("enterprise technology trends 2026", "AI", None),
        ("healthcare innovation technology", "HealthTech", None),
        ("fintech regulation compliance AI", "FinTech", None),
        ("change management digital transformation", "Digital Transformation", None),
        # X/Twitter - weekend reading, provocative takes
        ("AI overhyped unpopular opinion", "AI", "x"),
        ("project management dead agile controversy", "PMO", "x"),
        # LinkedIn - viral posts, big ideas
        ("leadership AI era unpopular opinion", "Strategy", "linkedin"),
        ("CTO CIO transformation strategy post", "Digital Transformation", "linkedin"),
        ("AI automation workforce future", "AI", "linkedin"),
    ],
}

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

def telegram_msg(text):
    payload = {"chat_id": TELEGRAM_CHAT, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT}/sendMessage",
        data=data, method="POST", headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            return json.loads(r.read())
    except:
        pass

# ── Load seen URLs (dedup) ───────────────────────────────────────────────────
def load_seen_urls():
    if os.path.exists(STATE_FILE):
        state = json.load(open(STATE_FILE))
        return set(state.get("seen_urls", []))
    return set()

def save_seen_urls(seen):
    state = json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {}
    state["seen_urls"] = list(seen)[-50000:]
    json.dump(state, open(STATE_FILE, "w"))

# ── Exa Search via Composio ─────────────────────────────────────────────────
# NOTE: This script is designed to be run by the agent which has Composio access.
# For cron (non-agent) execution, we use Exa's REST API directly.
# Exa API key should be in environment or we fall back to Composio.

def exa_search(query, num_results=5, domain_filter=None):
    """Search Exa via REST API with optional domain filtering for X/LinkedIn.
    domain_filter: None=general web, "x"=X/Twitter, "linkedin"=LinkedIn
    """
    # Try environment variable first
    api_key = os.environ.get("EXA_API_KEY", "")
    
    if not api_key:
        exa_config = f"{WORKSPACE}/config/exa.json"
        if os.path.exists(exa_config):
            api_key = json.load(open(exa_config)).get("api_key", "")
    
    if not api_key:
        log("  No Exa API key found. Skipping search.")
        return []
    
    three_days_ago = (datetime.now(CAIRO) - timedelta(days=3)).strftime("%Y-%m-%dT00:00:00.000Z")
    
    body = {
        "query": query,
        "numResults": num_results,
        "type": "neural",  # neural required for domain filters
        "startPublishedDate": three_days_ago,
        "text": {"maxCharacters": 500},
    }
    
    # Domain filtering - includeDomains and excludeDomains are mutually exclusive
    if domain_filter == "x":
        body["includeDomains"] = ["twitter.com", "x.com"]
    elif domain_filter == "linkedin":
        body["includeDomains"] = ["linkedin.com"]
    else:
        # General web - exclude social media
        body["excludeDomains"] = [
            "youtube.com", "reddit.com", "twitter.com", "x.com",
            "facebook.com", "linkedin.com", "instagram.com", "tiktok.com"
        ]
    
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        "https://api.exa.ai/search",
        data=data, method="POST",
        headers={
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    )
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
            result = json.loads(r.read())
        return result.get("results", [])
    except Exception as e:
        log(f"  Exa search error: {e}")
        return []

# ── Add to RSS Intelligence DB ───────────────────────────────────────────────
def add_to_rss_db(title, url, category, summary, source):
    """Add an Exa-found article to RSS Intelligence DB with scoring."""
    # Score it
    source_quality = scorer.score_source_quality(source)
    topic_weight, topic_tier, pillar = scorer.get_topic_weight([category])
    quality_score, formats, hook_score, posting_angle, exec_summary = \
        scorer.score_content_potential(title, summary, "", [category])
    format_score = round(quality_score * (1 + topic_weight) * source_quality, 1)
    priority = scorer.calculate_priority(quality_score, topic_weight, source_quality)
    
    body = {
        "parent": {"database_id": RSS_DB},
        "properties": {
            "Name": {"title": [{"text": {"content": title[:200]}}]},
            "URL": {"url": url},
            "Category": {"multi_select": [{"name": category}]},
            "Source": {"rich_text": [{"text": {"content": f"Exa: {source[:100]}"}}]},
            "Summary": {"rich_text": [{"text": {"content": (summary or "")[:200]}}]},
            "Status": {"select": {"name": "Read"}},
            "Quality Score": {"number": quality_score},
            "Hook Score": {"number": hook_score},
            "Format Score": {"number": format_score},
            "Post Format": {"multi_select": [{"name": f} for f in formats]},
            "Topic Weight": {"select": {"name": topic_tier}},
            "Content Pillar": {"multi_select": [{"name": pillar}]},
            "Priority": {"select": {"name": priority}},
            "Posting Angle": {"rich_text": [{"text": {"content": posting_angle[:500]}}]},
            "Executive Summary": {"rich_text": [{"text": {"content": exec_summary[:500]}}]},
        }
    }
    
    try:
        notion_req("POST", "/pages", body)
        return True, quality_score, priority, formats
    except Exception as e:
        return False, 0, "", []

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    now = datetime.now(CAIRO)
    weekday = now.weekday()  # 0=Mon, 4=Fri
    log(f"=== Content Factory Exa Scanner === {now.strftime('%Y-%m-%d %H:%M')} Cairo (day={weekday})")
    
    # Pick search set for today (default to Monday set if not M/W/F)
    searches = SEARCH_SETS.get(weekday, SEARCH_SETS[0])
    log(f"Running {len(searches)} searches")
    
    seen = load_seen_urls()
    initial_seen = len(seen)
    
    added = 0
    gold = []
    total_results = 0
    
    stats = {"web": 0, "x": 0, "linkedin": 0}
    
    for query, category, domain_filter in searches:
        source_label = {"x": "𝕏", "linkedin": "LinkedIn"}.get(domain_filter, "Web")
        log(f"  [{source_label}] '{query}' → {category}")
        results = exa_search(query, num_results=5, domain_filter=domain_filter)
        total_results += len(results)
        
        for r in results:
            url = r.get("url", "")
            title = r.get("title", "")
            text = r.get("text", "")
            author = r.get("author", "")
            raw_domain = url.split("/")[2] if url and "/" in url else ""
            
            if not url or url in seen:
                continue
            
            # Build source label for Notion
            if domain_filter == "x":
                source_tag = f"X: @{author}" if author else f"X: {raw_domain}"
                stats["x"] += 1
            elif domain_filter == "linkedin":
                source_tag = f"LinkedIn: {author}" if author else f"LinkedIn: {raw_domain}"
                stats["linkedin"] += 1
            else:
                # General web - still skip social that leaked through
                skip_domains = ["youtube.com", "reddit.com", "facebook.com", "instagram.com", "tiktok.com"]
                if any(d in url.lower() for d in skip_domains):
                    continue
                source_tag = f"Exa: {raw_domain}"
                stats["web"] += 1
            
            ok, score, priority, formats = add_to_rss_db(title, url, category, text[:500], source_tag)
            
            if ok:
                seen.add(url)
                added += 1
                log(f"    + [{score}/10 {priority}] {title[:60]}")
                
                if priority == "High":
                    gold.append({
                        "title": title[:80], "score": score,
                        "formats": formats, "url": url[:80],
                        "source": source_label
                    })
            
            time.sleep(0.5)
        
        time.sleep(1)  # Between searches
    
    save_seen_urls(seen)
    
    log(f"\n=== Done ===")
    log(f"  Searches: {len(searches)} | Results: {total_results}")
    log(f"  New added: {added} | Gold: {len(gold)}")
    log(f"  Seen URLs: {initial_seen} → {len(seen)}")
    
    # Telegram summary
    if added > 0:
        lines = [f"🔍 <b>Exa Scanner v1.1</b> - {added} new items found\n"]
        lines.append(f"📡 Sources: 🌐 Web {stats['web']} | 𝕏 {stats['x']} | 💼 LinkedIn {stats['linkedin']}")
        if gold:
            lines.append(f"\n<b>🥇 Gold ({len(gold)}):</b>")
            for g in gold[:5]:
                src = g.get('source', 'Web')
                lines.append(f"• [{src}] {g['title'][:55]} [{g['score']}/10]")
        lines.append(f"\n📊 {len(searches)} searches | {total_results} results | {added} new | {len(gold)} gold")
        telegram_msg("\n".join(lines))

if __name__ == "__main__":
    main()
