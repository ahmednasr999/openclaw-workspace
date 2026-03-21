#!/usr/bin/env python3
"""
LinkedIn Comment Radar Agent - Discovers fresh posts worth commenting on.
Outputs data/comment-radar.json for the briefing runner.

Uses Composio Search (Exa) to find LinkedIn posts from last 24h on Ahmed's topics.
Falls back to Google search via web scraping if needed.
"""
import json, re, ssl, sys, os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
OUTPUT = DATA_DIR / "comment-radar.json"

# Tavily API (if available)
TAVILY_KEY = os.environ.get("TAVILY_API_KEY")
if not TAVILY_KEY:
    tavily_conf = WORKSPACE / "config" / "tavily.json"
    if tavily_conf.exists():
        try:
            TAVILY_KEY = json.load(open(tavily_conf)).get("api_key")
        except:
            pass

# Topics for Ahmed
TOPICS = [
    "Digital Transformation",
    "PMO",
    "Program Management", 
    "AI in business",
    "Leadership",
    "Healthcare IT",
]

GCC_TERMS = "Saudi OR UAE OR Dubai OR Riyadh OR Qatar OR Bahrain OR Kuwait OR Oman OR GCC"

STYLE_GUIDE = {
    "max_lines": 4,
    "min_lines": 2,
    "banned_openers": ["Strong point", "Great", "Excellent", "Important signal", "Very accurate", "Very relevant"],
    "require_anchor": True,
    "no_em_dashes": True,
    "tone": "Executive, practical, decision-oriented",
}


def tavily_search(query, n=10):
    """Search using Tavily API."""
    if not TAVILY_KEY:
        return []
    
    payload = json.dumps({
        "api_key": TAVILY_KEY,
        "query": query,
        "max_results": n,
        "search_depth": "basic",
    }).encode()
    
    ctx = ssl.create_default_context()
    req = Request("https://api.tavily.com/search", data=payload, 
                  headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=30, context=ctx) as r:
            data = json.loads(r.read().decode("utf-8", errors="ignore"))
        return data.get("results", [])
    except Exception as e:
        print(f"  Tavily error: {e}")
        return []


def extract_linkedin_posts(results):
    """Filter for LinkedIn post URLs only."""
    posts = []
    seen_urls = set()
    
    for r in results:
        url = r.get("url", "")
        # Only LinkedIn posts (not jobs, not profiles)
        if "linkedin.com/posts/" not in url and "linkedin.com/feed/update/" not in url:
            continue
        
        # Normalize URL
        clean_url = url.split("?")[0]
        if clean_url in seen_urls:
            continue
        seen_urls.add(clean_url)
        
        title = r.get("title", "")
        snippet = r.get("content", r.get("snippet", ""))
        
        # Extract author from title pattern "Author Name on LinkedIn: ..."
        author = "Unknown"
        m = re.match(r"^(.+?)(?:\s+on LinkedIn|\s+posted on)", title)
        if m:
            author = m.group(1).strip()
        
        # Extract post text preview
        text_preview = snippet[:300] if snippet else title
        
        posts.append({
            "url": clean_url,
            "author": author,
            "title": title[:200],
            "preview": text_preview,
            "source": "tavily",
        })
    
    return posts


def score_post(post):
    """Score a post for comment opportunity (PQS 0-100)."""
    score = 0
    preview = (post.get("preview", "") + " " + post.get("title", "")).lower()
    
    # Topic fit (25 points)
    topic_hits = sum(1 for t in TOPICS if t.lower() in preview)
    score += min(topic_hits * 8, 25)
    
    # Author signal (25 points) - C-suite/Director/VP get higher scores
    author = post.get("author", "").lower()
    title_words = ["chief", "ceo", "coo", "cto", "cio", "vp", "vice president", "director", "head", "founder"]
    if any(w in author.lower() or w in preview for w in title_words):
        score += 20
    elif any(w in preview for w in ["manager", "lead", "principal"]):
        score += 12
    else:
        score += 5
    
    # GCC relevance (20 points)
    gcc_terms = ["saudi", "uae", "dubai", "riyadh", "qatar", "bahrain", "kuwait", "oman", "gcc", "mena"]
    gcc_hits = sum(1 for t in gcc_terms if t in preview)
    score += min(gcc_hits * 7, 20)
    
    # Engagement proxy from text (15 points) - presence of discussion markers
    discussion_markers = ["agree", "disagree", "what do you think", "thoughts?", "debate", "challenge", "unpopular opinion"]
    if any(m in preview for m in discussion_markers):
        score += 15
    else:
        score += 5
    
    # Content quality (15 points) - longer = more substance
    if len(post.get("preview", "")) > 200:
        score += 15
    elif len(post.get("preview", "")) > 100:
        score += 10
    else:
        score += 5
    
    return min(score, 100)


def run_radar():
    """Main radar execution."""
    print("🔍 LinkedIn Comment Radar")
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    
    all_posts = []
    
    # Run searches across topic clusters
    queries = [
        f'site:linkedin.com/posts ("digital transformation" OR "PMO" OR "program management") ({GCC_TERMS})',
        f'site:linkedin.com/posts ("AI" OR "artificial intelligence") (business OR enterprise OR strategy) ({GCC_TERMS})',
        f'site:linkedin.com/posts ("leadership" OR "healthcare" OR "fintech") ({GCC_TERMS})',
    ]
    
    for i, query in enumerate(queries):
        print(f"  Query {i+1}/{len(queries)}...")
        results = tavily_search(query, n=10)
        posts = extract_linkedin_posts(results)
        print(f"    Found {len(posts)} LinkedIn posts")
        all_posts.extend(posts)
    
    if not all_posts:
        print("  No posts found. Check Tavily API key.")
        # Write empty result
        output = {
            "generated": datetime.now(timezone.utc).isoformat(),
            "posts_found": 0,
            "top_posts": [],
            "status": "no_results",
        }
        json.dump(output, open(OUTPUT, "w"), indent=2)
        return
    
    # Deduplicate
    seen = set()
    unique = []
    for p in all_posts:
        if p["url"] not in seen:
            seen.add(p["url"])
            unique.append(p)
    
    # Score and rank
    for post in unique:
        post["pqs"] = score_post(post)
    
    unique.sort(key=lambda x: x["pqs"], reverse=True)
    top = unique[:10]
    
    print(f"\n  Total unique: {len(unique)} | Top 10 selected")
    for i, p in enumerate(top, 1):
        print(f"  #{i} PQS:{p['pqs']} | {p['author'][:25]} | {p['title'][:50]}")
    
    output = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "posts_found": len(unique),
        "top_posts": top,
        "status": "ok",
        "style_guide": STYLE_GUIDE,
    }
    
    json.dump(output, open(OUTPUT, "w"), indent=2)
    print(f"\n✅ Saved {len(top)} posts to {OUTPUT}")


if __name__ == "__main__":
    run_radar()
