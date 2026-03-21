#!/usr/bin/env python3
"""
github-discovery.py — Find fastest-growing GitHub repos.

Strategy: Search TRENDING GLOBALLY, then filter for relevance.
NOT: search our narrow topics and hope for results.

Sources:
1. GitHub API: repos created in last 7 days, sorted by stars (fastest growing)
2. GitHub API: repos created in last 30 days with 500+ stars (breakout hits)
3. GitHub API: topic-specific trending for our domains

Output: data/github-discovery.json + stdout for briefing
"""
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

WORKSPACE = Path("/root/.openclaw/workspace")
OUTPUT = WORKSPACE / "data" / "github-discovery.json"
GH_API = "https://api.github.com/search/repositories"
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "NASR-Discovery/1.0",
}

# Our relevance domains
RELEVANT_TOPICS = {
    "ai-agents": ["agent", "multi-agent", "orchestrat", "mcp", "tool-use", "function-call"],
    "automation": ["automat", "pipeline", "workflow", "cron", "scheduler"],
    "linkedin": ["linkedin", "social media", "content", "post"],
    "job-search": ["job", "career", "resume", "cv", "ats", "application"],
    "browser": ["browser", "scrape", "crawl", "selenium", "playwright", "puppeteer"],
    "ai-tools": ["llm", "gpt", "claude", "openai", "anthropic", "prompt", "rag"],
    "productivity": ["notion", "obsidian", "note", "knowledge", "dashboard"],
    "devops": ["deploy", "docker", "monitor", "backup", "infra"],
    "coding-tools": ["code", "editor", "terminal", "cli", "developer tool"],
}


def gh_search(query, sort="stars", order="desc", per_page=20):
    """Search GitHub API."""
    import urllib.parse
    url = f"{GH_API}?q={urllib.parse.quote(query)}&sort={sort}&order={order}&per_page={per_page}"
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  API error: {e}", file=sys.stderr)
        return {"items": []}


def classify_repo(repo):
    """Classify repo into our relevance domains."""
    text = " ".join([
        (repo.get("description") or "").lower(),
        (repo.get("full_name") or "").lower(),
        " ".join(repo.get("topics", [])),
    ])
    
    matches = []
    for domain, keywords in RELEVANT_TOPICS.items():
        for kw in keywords:
            if kw in text:
                matches.append(domain)
                break
    return matches


def run():
    today = datetime.utcnow()
    day_of_week = today.weekday()  # 0=Mon, 6=Sun
    day_of_month = today.day
    
    # Determine tier
    if day_of_month == 1:
        tier = "monthly"
    elif day_of_week == 6:  # Sunday
        tier = "weekly"
    else:
        tier = "daily"
    
    print(f"🔭 GitHub Discovery ({tier} scan)")
    
    all_repos = {}  # full_name -> repo_data
    
    # ═══════════════════════════════════════════
    # SEARCH 1: Fastest growing this week (global)
    # ═══════════════════════════════════════════
    week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    print(f"\n📈 Fastest growing repos (created since {week_ago})...")
    
    data = gh_search(f"created:>{week_ago}", sort="stars", per_page=30)
    for r in data.get("items", []):
        all_repos[r["full_name"]] = r
    print(f"  Found {len(data.get('items', []))} repos")
    time.sleep(1)
    
    # ═══════════════════════════════════════════
    # SEARCH 2: Today's fastest (last 48h)
    # ═══════════════════════════════════════════
    two_days = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    print(f"\n🔥 Today's fastest (created since {two_days})...")
    
    data = gh_search(f"created:>{two_days}", sort="stars", per_page=20)
    for r in data.get("items", []):
        all_repos[r["full_name"]] = r
    print(f"  Found {len(data.get('items', []))} repos")
    time.sleep(1)
    
    # ═══════════════════════════════════════════
    # SEARCH 3: AI/Agent specific trending
    # ═══════════════════════════════════════════
    month_ago = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    ai_queries = [
        f"ai agent created:>{month_ago} stars:>100",
        f"mcp server created:>{month_ago} stars:>50",
        f"linkedin automation created:>{month_ago} stars:>20",
    ]
    
    print(f"\n🤖 Domain-specific trending...")
    for q in ai_queries:
        data = gh_search(q, per_page=10)
        for r in data.get("items", []):
            all_repos[r["full_name"]] = r
        time.sleep(1)
    print(f"  Total unique repos: {len(all_repos)}")
    
    # ═══════════════════════════════════════════
    # SEARCH 4: Weekly/Monthly broader sweep
    # ═══════════════════════════════════════════
    if tier in ("weekly", "monthly"):
        print(f"\n📊 Broader sweep ({tier})...")
        broader = [
            f"job search automation stars:>200 pushed:>{month_ago}",
            f"browser automation stars:>500 pushed:>{month_ago}",
            f"notion integration stars:>200 pushed:>{month_ago}",
            f"pdf generation stars:>300 pushed:>{month_ago}",
        ]
        for q in broader:
            data = gh_search(q, sort="updated", per_page=10)
            for r in data.get("items", []):
                all_repos[r["full_name"]] = r
            time.sleep(1)
    
    if tier == "monthly":
        print(f"\n🏆 Best in class (monthly)...")
        best = [
            "linkedin stars:>1000",
            "ai agent framework stars:>5000",
            "job automation stars:>500",
        ]
        for q in best:
            data = gh_search(q, sort="stars", per_page=5)
            for r in data.get("items", []):
                all_repos[r["full_name"]] = r
            time.sleep(1)
    
    # ═══════════════════════════════════════════
    # CLASSIFY & RANK
    # ═══════════════════════════════════════════
    print(f"\n🏷️ Classifying {len(all_repos)} repos...")
    
    results = []
    for name, repo in all_repos.items():
        domains = classify_repo(repo)
        stars = repo.get("stargazers_count", 0)
        created = repo.get("created_at", "")[:10]
        language = repo.get("language") or "?"
        
        # Calculate growth rate (stars per day since creation)
        try:
            created_dt = datetime.strptime(created, "%Y-%m-%d")
            age_days = max((today - created_dt).days, 1)
            growth_rate = stars / age_days
        except:
            growth_rate = 0
        
        results.append({
            "name": name,
            "description": (repo.get("description") or "")[:120],
            "stars": stars,
            "growth_rate": round(growth_rate, 1),
            "created": created,
            "language": language,
            "url": repo.get("html_url", ""),
            "domains": domains,
            "relevant": len(domains) > 0,
            "topics": repo.get("topics", [])[:5],
        })
    
    # Sort by growth rate (stars per day)
    results.sort(key=lambda x: x["growth_rate"], reverse=True)
    
    # ═══════════════════════════════════════════
    # OUTPUT
    # ═══════════════════════════════════════════
    
    # Top 10 overall (fastest growing globally)
    top_global = results[:10]
    
    # Top 10 relevant to us
    top_relevant = [r for r in results if r["relevant"]][:10]
    
    output = {
        "date": today.strftime("%Y-%m-%d"),
        "tier": tier,
        "total_scanned": len(results),
        "top_global": top_global,
        "top_relevant": top_relevant,
    }
    
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump(output, open(OUTPUT, "w"), indent=2)
    
    # Print report
    print(f"\n{'='*50}")
    print(f"🔭 GitHub Discovery - {today.strftime('%Y-%m-%d')} ({tier} scan)")
    print(f"Scanned: {len(results)} repos")
    print(f"{'='*50}")
    
    print(f"\n🌍 TOP 10 FASTEST GROWING (globally):")
    for i, r in enumerate(top_global, 1):
        relevant_tag = " 🎯" if r["relevant"] else ""
        domains_str = f" [{', '.join(r['domains'])}]" if r["domains"] else ""
        print(f"  #{i} {r['name']} ({r['stars']:,}⭐, {r['growth_rate']}/day) [{r['language']}]{domains_str}{relevant_tag}")
        print(f"     {r['description'][:80]}")
        print(f"     {r['url']}")
    
    if top_relevant:
        print(f"\n🎯 TOP RELEVANT TO US:")
        for i, r in enumerate(top_relevant, 1):
            print(f"  #{i} {r['name']} ({r['stars']:,}⭐, {r['growth_rate']}/day) [{', '.join(r['domains'])}]")
            print(f"     {r['description'][:80]}")
            print(f"     {r['url']}")
    else:
        print(f"\n🎯 No directly relevant repos found this scan.")
    
    print(f"\n📊 Domain coverage:")
    domain_counts = {}
    for r in results:
        for d in r["domains"]:
            domain_counts[d] = domain_counts.get(d, 0) + 1
    for d, c in sorted(domain_counts.items(), key=lambda x: -x[1]):
        print(f"  {d}: {c} repos")
    
    print(f"\nSaved to: {OUTPUT}")


if __name__ == "__main__":
    run()
