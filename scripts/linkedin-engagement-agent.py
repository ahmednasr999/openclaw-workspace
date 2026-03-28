#!/usr/bin/env python3
"""
linkedin-engagement-agent.py
==============================
Daily LinkedIn engagement agent for Ahmed Nasr.

Workflow:
  1. Load Ahmed's context (career, sectors, target personas, recent comments)
  2. Discover fresh LinkedIn posts via Exa search (30-50 candidates)
  3. Score each post against context (career overlap, persona match, comment gap, brand fit)
  4. Select top 5
  5. Draft comments in Ahmed's voice
  6. Send to Telegram thread for human approval (topic_id=7)
  7. On approval: browser posts comment + like, updates ontology graph

Cron: 0 7 * * 0-4  (9 AM Cairo Sun-Thu)

Usage:
  python3 scripts/linkedin-engagement-agent.py          # Send morning scan reminder to Telegram
  python3 scripts/linkedin-engagement-agent.py --dry-run # Print context without sending
  python3 scripts/linkedin-engagement-agent.py --post-id p1a2b3 # Post approved comment by post_id
  python3 scripts/linkedin-engagement-agent.py --skip-id p1a2b3 # Skip a post by post_id

Architecture note:
  Browser-based discovery runs through the OpenClaw session (not this script).
  This script sends the morning trigger to thread 7. Ahmed replies "scan" and
  the session does real-time discovery via LinkedIn browser + scores + drafts 5 cards.
"""

import json
import os
import subprocess
import sys
import uuid
import logging
from datetime import datetime, timezone, timedelta, date
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────

WORKSPACE       = Path("/root/.openclaw/workspace")
GRAPH_FILE      = WORKSPACE / "memory/ontology/graph.jsonl"
MASTER_CV       = WORKSPACE / "memory/master-cv-data.md"
LOGS_DIR        = WORKSPACE / "logs"
DATA_DIR        = WORKSPACE / "data"
PENDING_FILE    = DATA_DIR / "linkedin-engagement-pending.json"

TELEGRAM_CHAT_ID   = "-1003882622947"
TELEGRAM_TOPIC_ID  = 7   # Content thread
OPENCLAW_JSON      = Path("/root/.openclaw/openclaw.json")

CAIRO = timezone(timedelta(hours=2))
OPENCLAW_JSON = Path("/root/.openclaw/openclaw.json")

DRY_RUN   = "--dry-run" in sys.argv
POST_ID   = None
SKIP_ID   = None

for i, arg in enumerate(sys.argv):
    if arg == "--post-id" and i + 1 < len(sys.argv):
        POST_ID = sys.argv[i + 1]
    if arg == "--skip-id" and i + 1 < len(sys.argv):
        SKIP_ID = sys.argv[i + 1]

# LLM config (loaded once)
_ANTHROPIC_API_KEY = ""
_ANTHROPIC_BASE_URL = "https://api.anthropic.com"

def load_llm_config():
    global _ANTHROPIC_API_KEY, _ANTHROPIC_BASE_URL
    try:
        cfg = json.loads(OPENCLAW_JSON.read_text())
        p = cfg.get("models", {}).get("providers", {}).get("anthropic", {})
        _ANTHROPIC_API_KEY = p.get("apiKey", "")
        _ANTHROPIC_BASE_URL = p.get("baseUrl", "https://api.anthropic.com")
    except Exception as e:
        log.warning(f"Could not load LLM config: {e}")

def call_claude(prompt, max_tokens=2000, model="claude-haiku-4-5"):
    """Call Claude via direct API using OpenClaw's Anthropic key."""
    import urllib.request
    if not _ANTHROPIC_API_KEY:
        load_llm_config()
    payload = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        f"{_ANTHROPIC_BASE_URL}/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": _ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["content"][0]["text"]

# ─── Logging ──────────────────────────────────────────────────────────────────

LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGS_DIR / "linkedin-engagement.log"),
    ],
)
log = logging.getLogger("engagement")

# ─── Helpers ──────────────────────────────────────────────────────────────────

def now_cairo():
    return datetime.now(CAIRO)

def get_bot_token():
    try:
        cfg = json.loads(OPENCLAW_JSON.read_text())
        return cfg["channels"]["telegram"]["botToken"]
    except Exception as e:
        log.error(f"Could not read bot token: {e}")
        return None

def send_telegram(text, buttons=None, thread_id=TELEGRAM_TOPIC_ID):
    """Send a message to the Telegram engagement thread."""
    token = get_bot_token()
    if not token:
        log.error("No Telegram token, skipping send")
        return None

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "message_thread_id": thread_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}

    payload_bytes = json.dumps(payload).encode()
    try:
        result = subprocess.run(
            ["curl", "-sf", "-X", "POST",
             f"https://api.telegram.org/bot{token}/sendMessage",
             "-H", "Content-Type: application/json",
             "-d", "@-"],
            input=payload_bytes,
            capture_output=True,
            timeout=15,
        )
        resp = json.loads(result.stdout)
        if resp.get("ok"):
            return resp["result"]["message_id"]
        else:
            log.error(f"Telegram error: {resp.get('description')}")
            return None
    except Exception as e:
        log.error(f"Telegram send failed: {e}")
        return None

# ─── Stage 1: Context Load ─────────────────────────────────────────────────────

def load_ahmed_context():
    """Build the 'Ahmed lens' from known files and ontology graph."""
    ctx = {
        "career_companies": [
            "Talabat", "Delivery Hero", "HungerStation",
            "Saudi German Hospital", "Aster DM Healthcare",
            "Raya Holding", "IBM", "Microsoft",
        ],
        "career_sectors": [
            "HealthTech", "Health Tech", "Healthcare", "Digital Health",
            "FinTech", "Financial Technology", "BNPL", "Payments",
            "PMO", "Program Management", "Project Management",
            "Digital Transformation", "AI Strategy", "AI Agents",
            "E-Commerce", "Food Tech", "Quick Commerce",
            "Supply Chain", "Operations",
        ],
        "target_personas": [
            "VP", "Vice President", "C-suite", "CEO", "CTO", "CDO", "COO", "CISO",
            "Director", "Head of", "Chief", "SVP", "EVP",
            "GCC", "Saudi Arabia", "UAE", "Dubai", "Riyadh", "Qatar", "Kuwait",
        ],
        "brand_themes": [
            "AI transformation", "digital transformation",
            "PMO excellence", "program management",
            "scaling operations", "platform scaling",
            "HealthTech innovation", "FinTech strategy",
            "AI agents", "enterprise AI", "automation",
            "GCC tech", "Middle East digital",
        ],
        "recent_commented": [],  # LinkedIn URLs, filled from graph
    }

    # Load recently commented persons from ontology graph (14-day window)
    cutoff = (date.today() - timedelta(days=14)).isoformat()
    if GRAPH_FILE.exists():
        with open(GRAPH_FILE) as f:
            entities = {}
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("op") == "create":
                        e = entry["entity"]
                        entities[e["id"]] = e
                    elif entry.get("op") == "update":
                        e = entry["entity"]
                        if e["id"] in entities:
                            entities[e["id"]]["properties"].update(e.get("properties", {}))
                except Exception:
                    continue

        for e in entities.values():
            if e["type"] == "Person":
                last = e["properties"].get("last_commented", "")
                url  = e["properties"].get("linkedin_url", "")
                if last >= cutoff and url:
                    ctx["recent_commented"].append(url)

    log.info(f"Context loaded. {len(ctx['recent_commented'])} persons commented on in last 14 days.")
    return ctx

# ─── Stage 2: Post Discovery ──────────────────────────────────────────────────

def discover_posts_via_browser(ctx):
    """
    Scrape LinkedIn search results via Ahmed-Mac browser (OpenClaw gateway API).
    Runs 5 targeted searches, extracts post content via JS evaluation.
    Returns list of dicts: {url, author, title, snippet, query_source}
    """
    import urllib.request
    import time

    # Load gateway config
    try:
        oc_cfg = json.loads(OPENCLAW_JSON.read_text())
        gateway_token = oc_cfg.get("gateway", {}).get("auth", {}).get("token", "")
        gateway_port  = oc_cfg.get("gateway", {}).get("port", 18789)
    except Exception as e:
        log.error(f"Could not load gateway config: {e}")
        return _discover_via_exa(ctx)

    if not gateway_token:
        log.warning("No gateway token, falling back to static list")
        return _discover_via_exa(ctx)

    api_base = f"http://localhost:{gateway_port}"
    headers  = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {gateway_token}",
    }

    # JS extractor — runs inside the LinkedIn page
    EXTRACTOR_JS = """() => {
        const posts = [];
        const seen = new Set();
        document.querySelectorAll('[data-urn]').forEach(el => {
            const urn = el.getAttribute('data-urn') || '';
            if (!urn.includes('activity') || seen.has(urn)) return;
            seen.add(urn);
            const textEl = el.querySelector('.feed-shared-text, .update-components-text, .break-words');
            const text = textEl ? textEl.innerText.trim().slice(0, 400) : '';
            const titleEl = el.querySelector(
                '.update-components-actor__description, .feed-shared-actor__description'
            );
            const title = titleEl ? titleEl.innerText.replace(/\\n+/g, ' ').trim() : '';
            const nameEl = el.querySelector(
                '.update-components-actor__name span[aria-hidden="true"], .feed-shared-actor__name'
            );
            const author = nameEl ? nameEl.innerText.trim() : '';
            const reactionEl = el.querySelector('.social-details-social-counts__reactions-count');
            const reactions = reactionEl ? reactionEl.innerText.trim() : '0';
            const commentEl = el.querySelector('.social-details-social-counts__comments');
            const comments = commentEl ? commentEl.innerText.trim() : '0';
            const url = 'https://www.linkedin.com/feed/update/' + urn + '/';
            if (text.length > 50) {
                posts.push({urn, author, title, text, url, reactions, comments});
            }
        });
        return JSON.stringify(posts.slice(0, 15));
    }"""

    def browser_call(action, params=None):
        payload = json.dumps({"action": action, "node": "Ahmed-Mac", **(params or {})}).encode()
        req = urllib.request.Request(
            f"{api_base}/api/browser",
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:
            log.warning(f"Browser API call failed ({action}): {e}")
            return {"ok": False}

    search_queries = [
        ("digital+transformation+AI+GCC",         "Digital Transformation / AI / GCC"),
        ("HealthTech+digital+health+Saudi+UAE",    "HealthTech / Digital Health"),
        ("FinTech+payments+BNPL+Middle+East",      "FinTech / Payments / MENA"),
        ("PMO+program+management+executive+GCC",   "PMO / Program Management"),
        ("AI+agents+automation+enterprise+GCC",    "AI Agents / Enterprise Automation"),
    ]

    all_results = []
    seen_urns   = set()

    for kw, label in search_queries:
        url = (
            f"https://www.linkedin.com/search/results/content/"
            f"?keywords={kw}&datePosted=past-24h&sortBy=date_posted"
        )
        log.info(f"Scraping: {label}")
        nav = browser_call("navigate", {"url": url, "targetId": "A6B8139035B3866E464E304955079D02"})
        if not nav.get("ok"):
            log.warning(f"  Navigation failed for {label}")
            continue
        time.sleep(2.5)  # let page render

        result = browser_call("evaluate", {
            "fn": EXTRACTOR_JS,
            "targetId": "A6B8139035B3866E464E304955079D02",
        })
        if not result.get("ok"):
            log.warning(f"  JS eval failed for {label}")
            continue

        try:
            posts = json.loads(result.get("result", "[]"))
        except Exception:
            posts = []

        for p in posts:
            urn = p.get("urn", "")
            if not urn or urn in seen_urns:
                continue
            seen_urns.add(urn)
            all_results.append({
                "url":          p.get("url", ""),
                "urn":          urn,
                "author":       p.get("author", ""),
                "author_title": p.get("title", ""),
                "snippet":      p.get("text", ""),
                "reactions":    p.get("reactions", "0"),
                "comments":     p.get("comments", "0"),
                "query_source": label,
            })

        log.info(f"  Found {len(posts)} posts for '{label}'")

    # Also scrape main feed for serendipitous finds
    log.info("Scraping main LinkedIn feed...")
    nav = browser_call("navigate", {
        "url": "https://www.linkedin.com/feed/",
        "targetId": "A6B8139035B3866E464E304955079D02",
    })
    if nav.get("ok"):
        time.sleep(2.5)
        result = browser_call("evaluate", {
            "fn": EXTRACTOR_JS,
            "targetId": "A6B8139035B3866E464E304955079D02",
        })
        if result.get("ok"):
            try:
                feed_posts = json.loads(result.get("result", "[]"))
                for p in feed_posts:
                    urn = p.get("urn", "")
                    if urn and urn not in seen_urns:
                        seen_urns.add(urn)
                        all_results.append({
                            "url":          p.get("url", ""),
                            "urn":          urn,
                            "author":       p.get("author", ""),
                            "author_title": p.get("title", ""),
                            "snippet":      p.get("text", ""),
                            "reactions":    p.get("reactions", "0"),
                            "comments":     p.get("comments", "0"),
                            "query_source": "main_feed",
                        })
                log.info(f"  Found {len(feed_posts)} posts from main feed")
            except Exception:
                pass

    log.info(f"Total discovered via browser: {len(all_results)} posts")

    if not all_results:
        log.warning("Browser discovery returned 0 posts, falling back to static list")
        return _discover_via_exa(ctx)

    return all_results


def _discover_via_exa(ctx):
    """Use Composio Exa search for LinkedIn post discovery."""
    import urllib.request

    # Check for Exa credentials
    exa_key = None
    try:
        # Try exa.json first (primary config location)
        exa_key = json.loads((WORKSPACE / "config/exa.json").read_text()).get("api_key")
    except Exception:
        pass
    if not exa_key:
        try:
            exa_key = os.environ.get("EXA_API_KEY")
        except Exception:
            pass
    if not exa_key:
        try:
            firehose_cfg = json.loads((WORKSPACE / "config/firehose.json").read_text())
            exa_key = firehose_cfg.get("exa_api_key") or firehose_cfg.get("exa", {}).get("api_key")
        except Exception:
            pass

    if not exa_key:
        log.warning("No Exa API key found, falling back to RSS discovery")
        return _discover_via_rss(ctx)

    queries = [
        "GCC digital transformation VP Director leadership",
        "Saudi Arabia FinTech payments hiring executive",
        "UAE HealthTech AI digital health strategy",
        "PMO program management Middle East C-suite",
        "AI agents enterprise automation GCC executive",
    ]

    all_results = []
    seen_urls = set()

    for query in queries:
        try:
            payload = json.dumps({
                "query": query,
                "numResults": 8,
                "includeDomains": ["linkedin.com"],
                "startPublishedDate": (
                    datetime.now(timezone.utc) - timedelta(days=2)
                ).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "type": "neural",
                "contents": {"text": {"maxCharacters": 400}},
            }).encode()

            req = urllib.request.Request(
                "https://api.exa.ai/search",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": exa_key,
                    "User-Agent": "Mozilla/5.0 (compatible; EngagementAgent/1.0)",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read())

            for item in data.get("results", []):
                url = item.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                all_results.append({
                    "url": url,
                    "author": item.get("author", ""),
                    "title": item.get("title", ""),
                    "snippet": item.get("text", "")[:400],
                    "query_source": query,
                })

        except Exception as e:
            log.warning(f"Exa query failed '{query[:40]}': {e}")

    log.info(f"Discovered {len(all_results)} posts via Exa.")
    return all_results


def _discover_via_rss(ctx):
    """
    Fallback: use LinkedIn keyword search via RSS/web scrape.
    Reads priority authors from config/priority-authors.json and
    checks their recent activity.
    """
    all_results = []

    try:
        priority_cfg = json.loads((WORKSPACE / "config/priority-authors.json").read_text())
        # Handle both list format and dict with "authors" key
        if isinstance(priority_cfg, list):
            authors = priority_cfg
        else:
            authors = priority_cfg.get("authors", [])
        log.info(f"Checking {len(authors)} priority authors for recent posts")

        for author in authors[:20]:
            slug = author.get("slug", "")
            name = author.get("name", "")
            if not slug:
                continue
            activity_url = f"https://www.linkedin.com/in/{slug}/recent-activity/all/"
            all_results.append({
                "url": activity_url,
                "author": name,
                "title": f"Recent post by {name}",
                "snippet": author.get("why", "GCC/ME tech leader"),
                "query_source": "priority_authors",
            })
    except Exception as e:
        log.warning(f"Priority authors fallback failed: {e}")

    log.info(f"Discovered {len(all_results)} posts via priority authors fallback.")
    return all_results

# ─── Stage 3: Context Scoring ─────────────────────────────────────────────────

def score_posts(posts, ctx):
    """
    Score posts 0-100 using LLM. Returns sorted list with scores.
    Skips posts where author LinkedIn URL is in recent_commented.
    """
    if not posts:
        return []

    # Filter out recently commented
    filtered = []
    for p in posts:
        skip = any(
            rc and rc in p.get("url", "")
            for rc in ctx["recent_commented"]
        )
        if not skip:
            filtered.append(p)

    log.info(f"After recent-comment filter: {len(filtered)} posts remain.")

    # Build scoring prompt
    ahmed_context = f"""Ahmed Nasr's profile:
- Career companies: {', '.join(ctx['career_companies'])}
- Career sectors: {', '.join(ctx['career_sectors'][:8])}
- Target personas: VP/Director/C-suite in GCC (UAE, Saudi, Qatar, Kuwait)
- Brand themes: Digital Transformation Executive, AI strategy, PMO excellence, scaling platforms
- Location target: GCC region"""

    posts_json = json.dumps([
        {"id": i, "url": p["url"], "author": p.get("author",""), "author_title": p.get("author_title",""),
         "snippet": p.get("snippet", p.get("title",""))[:300], "reactions": p.get("reactions","0"), "comments": p.get("comments","0"), "source": p.get("query_source","")}
        for i, p in enumerate(filtered[:50])
    ], ensure_ascii=False, indent=2)

    prompt = f"""{ahmed_context}

Score each LinkedIn post below 0-100 for Ahmed to comment on.

SELECTION CRITERIA (strict):
INCLUDE (scores 60+):
- Topics: PMO, digital transformation, operations, AI, GCC/MENA business, leadership, HealthTech, FinTech, technology strategy
- Authors: C-suite, VP, Director, GM, hiring managers, industry influencers, people at companies Ahmed has applied to
- Recency: posted in last 24 hours (fresh posts only)
- Engagement: has some likes or comments (proof it's active, comment gets seen)

SKIP (score below 30, these are hard filters):
- Purely personal posts (birthday, travel, family, celebrations with no business angle)
- Political or controversial topics
- Zero engagement posts with no comments at all
- Posts with no visible business relevance to Ahmed's sectors

COMMENT VALUE (what makes a comment worthwhile):
- Ahmed can add a real insight from his 20 years in GCC operations
- Post invites discussion or asks a question
- Commenting would reinforce Ahmed's brand as a Digital Transformation Executive
- Author is someone worth being visible to (potential referral, future colleague, hiring manager)

Return JSON array only, no explanation:
[{{"id": 0, "score": 85, "reason": "one-line reason why this is worth commenting on", "author_name": "...", "author_title": "..."}}, ...]

Posts:
{posts_json}"""

    try:
        load_llm_config()
        raw = call_claude(prompt, max_tokens=2000, model="claude-haiku-4-5")

        # Parse JSON from response
        import re
        json_match = re.search(r'\[.*\]', raw, re.DOTALL)
        if json_match:
            scores = json.loads(json_match.group())
        else:
            scores = json.loads(raw)

        # Merge scores back into posts
        score_map = {s["id"]: s for s in scores}
        for i, post in enumerate(filtered[:50]):
            s = score_map.get(i, {})
            post["score"]        = s.get("score", 0)
            post["reason"]       = s.get("reason", "")
            post["author_name"]  = s.get("author_name", post.get("author", "Unknown"))
            post["author_title"] = s.get("author_title", "")

        scored = sorted(filtered[:50], key=lambda x: x.get("score", 0), reverse=True)
        log.info(f"Top scores: {[p.get('score') for p in scored[:5]]}")
        return scored[:5]

    except Exception as e:
        log.error(f"Scoring failed: {e}")
        # Return top 5 by query diversity as fallback
        return filtered[:5]

# ─── Stage 4: Draft Comments ──────────────────────────────────────────────────

def draft_comment(post, ctx):
    """Draft a comment in Ahmed's voice for a specific post."""
    prompt = f"""You are writing a LinkedIn comment for Ahmed Nasr.

Ahmed's profile:
- Digital Transformation Executive with 20+ years in GCC
- Led operations scaling from 30K to 7M daily orders at Talabat (Delivery Hero ecosystem)
- Expertise: FinTech, HealthTech, PMO, AI strategy, e-commerce operations
- Currently building AI automation systems
- Tone: peer-to-peer, direct, adds genuine insight, no corporate fluff

Post to comment on:
Author: {post.get('author_name', '')} - {post.get('author_title', '')}
Content: {post.get('snippet', post.get('title', ''))[:500]}
URL: {post.get('url', '')}

Write a LinkedIn comment that:
- Opens with a specific insight or perspective, NEVER with "Great post!", "So true!", "Absolutely!", or any empty affirmation
- Is grounded in Ahmed's ACTUAL experience - reference his GCC operations, Talabat scaling, HealthTech/FinTech work naturally if it genuinely fits the post topic (do NOT force it)
- Adds something real: a data point, a counter-angle, a specific challenge he's faced, or a nuanced observation
- References Ahmed subtly if relevant: "In my experience scaling operations across GCC..." NOT "I'm looking for my next role"
- Ends with a question or bold statement that invites a reply from the author
- Is 2-4 sentences MAX - executives don't write essays in comments
- Uses NO hashtags - they look automated in comments
- Uses NO em dashes - use commas or hyphens instead
- Reads like a peer having a genuine conversation, NOT a job seeker or fan

Return ONLY the comment text, no quotes, no explanation."""

    try:
        load_llm_config()
        return call_claude(prompt, max_tokens=300, model="claude-haiku-4-5").strip()
    except Exception as e:
        log.error(f"Draft failed: {e}")
        return f"Interesting perspective on {post.get('title', 'this topic')}. From experience in the GCC market, the implementation challenge is often organizational rather than technical. What's been the biggest resistance point you've encountered?"

# ─── Stage 5: Send to Telegram ────────────────────────────────────────────────

def send_engagement_batch(top5):
    """Send all 5 posts to Telegram thread with approval buttons."""
    today = now_cairo().strftime("%A, %d %b %Y")

    # Save pending state first
    pending = {
        "date": now_cairo().isoformat(),
        "posts": top5,
    }
    DATA_DIR.mkdir(exist_ok=True)
    PENDING_FILE.write_text(json.dumps(pending, ensure_ascii=False, indent=2))
    log.info(f"Pending state saved to {PENDING_FILE}")

    if DRY_RUN:
        log.info("=== DRY RUN - Not sending to Telegram ===")
        for i, post in enumerate(top5, 1):
            log.info(f"\n{'='*60}")
            log.info(f"Post {i}/5 | Score: {post.get('score', 'N/A')}")
            log.info(f"Author: {post.get('author_name')} - {post.get('author_title')}")
            log.info(f"URL: {post['url']}")
            log.info(f"Reason: {post.get('reason')}")
            log.info(f"Comment:\n{post.get('comment', '')}")
        return

    # Header message
    header = (
        f"🔍 <b>LinkedIn Engagement - {today}</b>\n\n"
        f"Found 5 posts worth your attention. Review and approve below.\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    send_telegram(header)

    # Individual post messages
    for i, post in enumerate(top5, 1):
        post_id = post.get("post_id", f"p{i}")
        author  = post.get("author_name", "Unknown")
        title   = post.get("author_title", "")
        url     = post.get("url", "")
        comment = post.get("comment", "")
        reason  = post.get("reason", "")
        score   = post.get("score", "?")

        text = (
            f"🎯 <b>Post {i} of 5</b>  |  Score: {score}/100\n\n"
            f"👤 <b>{author}</b>"
            + (f"\n   {title}" if title else "")
            + f"\n🔗 {url}\n\n"
            f"💬 <b>Draft Comment:</b>\n"
            f"<i>{comment}</i>\n\n"
            f"✅ <b>Why:</b> {reason}"
        )

        buttons = [[
            {"text": "✅ Post It",  "callback_data": f"engage_post_{post_id}"},
            {"text": "✏️ Edit",    "callback_data": f"engage_edit_{post_id}"},
            {"text": "❌ Skip",    "callback_data": f"engage_skip_{post_id}"},
        ]]

        msg_id = send_telegram(text, buttons=buttons)
        post["telegram_msg_id"] = msg_id
        log.info(f"Sent post {i}/5 to Telegram (msg_id={msg_id})")

    # Update pending with telegram msg IDs
    PENDING_FILE.write_text(json.dumps(pending, ensure_ascii=False, indent=2))

# ─── Ontology Update ──────────────────────────────────────────────────────────

def update_graph_commented(author_name, author_linkedin_url, post_url):
    """
    After a comment is posted, update ontology graph.
    Finds existing Person entity by linkedin_url, or creates new one.
    Sets last_commented = today and adds post_url to interaction history.
    """
    today = date.today().isoformat()

    entities = {}
    if GRAPH_FILE.exists():
        with open(GRAPH_FILE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("op") == "create":
                        e = entry["entity"]
                        entities[e["id"]] = e
                    elif entry.get("op") == "update":
                        e = entry["entity"]
                        if e["id"] in entities:
                            entities[e["id"]]["properties"].update(e.get("properties", {}))
                except Exception:
                    continue

    # Find matching Person
    existing_id = None
    for eid, e in entities.items():
        if e["type"] == "Person":
            if (author_linkedin_url and
                    author_linkedin_url in e["properties"].get("linkedin_url", "")):
                existing_id = eid
                break
            if (author_name and
                    author_name.lower() in e["properties"].get("name", "").lower()):
                existing_id = eid
                break

    now_str = datetime.now(timezone.utc).isoformat()

    with open(GRAPH_FILE, "a") as f:
        if existing_id:
            update_entry = {
                "op": "update",
                "entity": {
                    "id": existing_id,
                    "properties": {
                        "last_commented": today,
                        "last_commented_post": post_url,
                    },
                    "updated": now_str,
                },
            }
            f.write(json.dumps(update_entry, ensure_ascii=False) + "\n")
            log.info(f"Updated Person {existing_id} (last_commented={today})")
        else:
            new_id = f"person_{uuid.uuid4().hex[:8]}"
            create_entry = {
                "op": "create",
                "entity": {
                    "id": new_id,
                    "type": "Person",
                    "properties": {
                        "name": author_name or "Unknown",
                        "linkedin_url": author_linkedin_url or "",
                        "source": "linkedin_engagement",
                        "last_commented": today,
                        "last_commented_post": post_url,
                        "notes": f"Auto-added by linkedin-engagement-agent on {today}",
                    },
                    "created": now_str,
                    "updated": now_str,
                },
            }
            f.write(json.dumps(create_entry, ensure_ascii=False) + "\n")
            log.info(f"Created new Person {new_id} for {author_name}")

# ─── Post Approved Comment (Option A handler) ─────────────────────────────────

def post_approved_comment(post_id):
    """
    Post an approved comment to LinkedIn via browser on Ahmed-Mac.
    Reads pending state, finds post by post_id, navigates to URL, types comment, submits.
    Updates ontology graph on success.
    """
    if not PENDING_FILE.exists():
        log.error("No pending file found. Run the agent first.")
        return False

    pending = json.loads(PENDING_FILE.read_text())
    posts = pending.get("posts", [])
    post = next((p for p in posts if p.get("post_id") == post_id), None)

    if not post:
        log.error(f"Post ID {post_id} not found in pending state.")
        log.info(f"Available IDs: {[p.get('post_id') for p in posts]}")
        return False

    url     = post.get("url", "")
    comment = post.get("comment", "")
    author  = post.get("author_name", "Unknown")

    log.info(f"Posting comment on {author}'s post: {url}")
    log.info(f"Comment: {comment[:80]}...")

    # Use OpenClaw browser on Ahmed-Mac
    try:
        import urllib.request

        token = get_bot_token()
        oc_cfg = json.loads(OPENCLAW_JSON.read_text())
        gateway_token = oc_cfg.get("gateway", {}).get("auth", {}).get("token", "")
        gateway_port  = oc_cfg.get("gateway", {}).get("port", 18789)
        api_base      = f"http://localhost:{gateway_port}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {gateway_token}",
        }

        def browser_request(action, params=None):
            payload = json.dumps({"action": action, **(params or {})}).encode()
            req = urllib.request.Request(
                f"{api_base}/api/browser",
                data=payload,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())

        # Navigate to post URL
        log.info(f"Navigating to: {url}")
        result = browser_request("navigate", {"url": url, "node": "Ahmed-Mac"})
        if not result.get("ok"):
            log.error(f"Navigation failed: {result}")
            return False

        import time
        time.sleep(3)

        # Take snapshot to find comment box
        snap = browser_request("snapshot", {"node": "Ahmed-Mac", "compact": True})
        content = snap.get("content", "")

        # Find comment box ref
        comment_ref = None
        for line in content.splitlines():
            if "Write a comment" in line or "Add a comment" in line:
                import re
                m = re.search(r'\[ref=(e\d+)\]', line)
                if m:
                    comment_ref = m.group(1)
                    break

        if not comment_ref:
            log.warning("Could not find comment box via snapshot, trying selector")
            comment_ref = None

        # Click comment box and type
        if comment_ref:
            browser_request("act", {"request": {"kind": "click", "ref": comment_ref}, "node": "Ahmed-Mac"})
            time.sleep(1)
            browser_request("act", {"request": {"kind": "type", "ref": comment_ref, "text": comment}, "node": "Ahmed-Mac"})
        else:
            # Fallback: use selector
            browser_request("act", {
                "request": {"kind": "click", "selector": ".comments-comment-box__form-container"},
                "node": "Ahmed-Mac"
            })
            time.sleep(1)
            browser_request("act", {
                "request": {"kind": "type", "selector": ".ql-editor", "text": comment},
                "node": "Ahmed-Mac"
            })

        time.sleep(1)

        # Submit (press Enter or click Post button)
        browser_request("act", {"request": {"kind": "press", "key": "Control+Return"}, "node": "Ahmed-Mac"})
        time.sleep(2)

        # Like the post
        snap2 = browser_request("snapshot", {"node": "Ahmed-Mac", "compact": True})
        content2 = snap2.get("content", "")
        like_ref = None
        for line in content2.splitlines():
            if "Like" in line and "[ref=" in line and "button" in line.lower():
                import re
                m = re.search(r'\[ref=(e\d+)\]', line)
                if m:
                    like_ref = m.group(1)
                    break
        if like_ref:
            browser_request("act", {"request": {"kind": "click", "ref": like_ref}, "node": "Ahmed-Mac"})
            log.info("Liked the post")

        # Update ontology graph
        update_graph_commented(
            author_name=author,
            author_linkedin_url=post.get("url", ""),
            post_url=url,
        )

        # Notify Telegram
        if token:
            msg = (
                f"✅ <b>Comment Posted!</b>\n\n"
                f"👤 {author}\n"
                f"🔗 {url}\n\n"
                f"💬 <i>{comment[:200]}</i>"
            )
            send_telegram(msg)

        log.info(f"Successfully posted comment on {author}'s post.")
        return True

    except Exception as e:
        log.error(f"Browser posting failed: {e}")
        if get_bot_token():
            send_telegram(
                f"❌ <b>Comment post failed</b>\n"
                f"Post ID: {post_id}\n"
                f"Error: {str(e)[:200]}\n\n"
                f"Post manually at: {url}\n"
                f"Comment: {comment}"
            )
        return False


def skip_post(post_id):
    """Mark a post as skipped and notify Telegram."""
    if not PENDING_FILE.exists():
        log.error("No pending file found.")
        return

    pending = json.loads(PENDING_FILE.read_text())
    posts   = pending.get("posts", [])
    post    = next((p for p in posts if p.get("post_id") == post_id), None)

    if post:
        post["status"] = "skipped"
        PENDING_FILE.write_text(json.dumps(pending, ensure_ascii=False, indent=2))
        send_telegram(f"⏭ Skipped post by {post.get('author_name', 'Unknown')}")
        log.info(f"Skipped post {post_id}")
    else:
        log.error(f"Post ID {post_id} not found.")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    """
    Morning trigger: send a scan prompt to the Telegram engagement thread.
    The actual browser discovery runs in the OpenClaw session when Ahmed replies.
    """
    log.info("=== LinkedIn Engagement Agent — morning trigger ===")

    today = now_cairo().strftime("%A, %d %b")

    if DRY_RUN:
        log.info("DRY RUN: Would send morning scan reminder to thread 7")
        log.info("Context loaded:")
        ctx = load_ahmed_context()
        log.info(f"  Recent commented (14d): {len(ctx['recent_commented'])} persons")
        log.info(f"  Sectors: {ctx['career_sectors'][:4]}")
        return

    ctx = load_ahmed_context()
    recent_count = len(ctx["recent_commented"])
    cooldown_note = f" ({recent_count} persons in 14-day cooldown)" if recent_count else ""

    msg = (
        f"🔍 <b>LinkedIn Engagement Scan — {today}</b>\n\n"
        f"Ready to find your top 5 comment opportunities{cooldown_note}.\n\n"
        f"Reply <b>scan</b> to start — I'll search LinkedIn, score by context, draft comments, and send approval cards here."
    )
    buttons = [[{"text": "🔍 Scan Now", "callback_data": "engage_scan_now"}]]
    send_telegram(msg, buttons=buttons)
    log.info("Morning scan reminder sent to thread 7.")


if __name__ == "__main__":
    if POST_ID:
        log.info(f"=== Option A: Posting approved comment for post_id={POST_ID} ===")
        success = post_approved_comment(POST_ID)
        sys.exit(0 if success else 1)
    elif SKIP_ID:
        log.info(f"=== Skipping post_id={SKIP_ID} ===")
        skip_post(SKIP_ID)
        sys.exit(0)
    else:
        main()
