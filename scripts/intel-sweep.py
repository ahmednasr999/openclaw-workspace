#!/usr/bin/env python3
"""
Daily Intelligence Sweep
=========================
Runs every morning at 05:45 Cairo. Writes intel/DAILY-INTEL.md.
All agents (HR, CMO, CEO) read this file — one write, many reads.

Sections:
  1. Hot Topics (AI/Tech/PMO/Digital Transformation)
  2. Job Market Signals (executive roles in GCC)
  3. LinkedIn Engagement Opportunities
  4. Company Intel (active target companies)

Usage:
    python3 intel-sweep.py            # full run
    python3 intel-sweep.py --dry-run  # print to console, don't write file
"""

import json, os, sys, ssl, urllib.request, urllib.parse, re
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent.parent
INTEL_FILE = BASE / "intel" / "DAILY-INTEL.md"
EXA_CONFIG = BASE / "config" / "exa.json"
TAVILY_CONFIG = BASE / "config" / "tavily.json"

cairo = timezone(timedelta(hours=2))
today = datetime.now(cairo).strftime("%Y-%m-%d")
now_str = datetime.now(cairo).strftime("%Y-%m-%d %H:%M Cairo")

DRY_RUN = "--dry-run" in sys.argv
ctx = ssl.create_default_context()
exa_disabled_reason = None


def log(msg):
    print(f"[intel-sweep] {msg}", flush=True)


def get_exa_key():
    try:
        return json.loads(EXA_CONFIG.read_text())["api_key"]
    except:
        return os.environ.get("EXA_API_KEY", "")


def get_tavily_key():
    try:
        return json.loads(TAVILY_CONFIG.read_text())["api_key"]
    except:
        return os.environ.get("TAVILY_API_KEY", "")


def _request_json(url, body, headers, timeout=20):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        method="POST",
        headers=headers,
    )
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as r:
        return json.loads(r.read())


def _normalize_results(results, text_key="text"):
    normalized = []
    seen = set()
    for r in results or []:
        url = (r.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        normalized.append({
            "title": (r.get("title") or "").strip(),
            "url": url,
            "text": (r.get(text_key) or r.get("content") or r.get("snippet") or "").strip(),
        })
    return normalized


def dedupe_results(results):
    seen = set()
    deduped = []
    for r in results or []:
        url = (r.get("url") or "").rstrip("/").strip().lower()
        if not url or url in seen:
            continue
        seen.add(url)
        deduped.append(r)
    return deduped


def filter_results(results, required_terms=None, excluded_domains=None, excluded_terms=None,
                   required_groups=None, min_term_matches=1):
    required_terms = [t.lower() for t in (required_terms or []) if t]
    excluded_domains = [d.lower() for d in (excluded_domains or []) if d]
    excluded_terms = [t.lower() for t in (excluded_terms or []) if t]
    required_groups = [[t.lower() for t in group if t] for group in (required_groups or [])]

    filtered = []
    for r in results or []:
        haystack = " ".join([
            r.get("title", ""),
            r.get("text", ""),
            r.get("url", ""),
        ]).lower()
        url = (r.get("url") or "").lower()

        if excluded_domains and any(domain in url for domain in excluded_domains):
            continue
        if excluded_terms and any(term in haystack for term in excluded_terms):
            continue
        if required_terms and sum(term in haystack for term in required_terms) < min_term_matches:
            continue
        if required_groups and not all(any(term in haystack for term in group) for group in required_groups):
            continue
        filtered.append(r)
    return filtered


def rank_results(results, preferred_terms=None, preferred_domains=None, penalty_terms=None, penalty_domains=None):
    preferred_terms = [t.lower() for t in (preferred_terms or []) if t]
    preferred_domains = [d.lower() for d in (preferred_domains or []) if d]
    penalty_terms = [t.lower() for t in (penalty_terms or []) if t]
    penalty_domains = [d.lower() for d in (penalty_domains or []) if d]

    ranked = []
    for idx, r in enumerate(results or []):
        haystack = " ".join([
            r.get("title", ""),
            r.get("text", ""),
            r.get("url", ""),
        ]).lower()
        url = (r.get("url") or "").lower()
        score = 0

        score += sum(3 for term in preferred_terms if term in haystack)
        score += sum(8 for domain in preferred_domains if domain in url)
        score -= sum(4 for term in penalty_terms if term in haystack)
        score -= sum(10 for domain in penalty_domains if domain in url)

        ranked.append((score, idx, r))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [r for _, _, r in ranked]


def searx_search(query, n=5, domain_filter=None, topic="general"):
    query_text = query
    if domain_filter == "linkedin":
        query_text = f"site:linkedin.com {query}"

    params = urllib.parse.urlencode({
        "q": query_text,
        "format": "json",
        "language": "all",
        "safesearch": "0",
        "categories": "news" if topic == "news" else "general",
    })
    url = f"http://127.0.0.1:8090/search?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read())
        results = payload.get("results", [])[:n]
        return _normalize_results([
            {"title": r.get("title"), "url": r.get("url"), "content": r.get("content")}
            for r in results
        ], text_key="content")
    except Exception as e:
        log(f"  SearXNG error for '{query_text}': {e}")
        return []


def tavily_search(query, n=5, domain_filter=None, days=3, topic="news"):
    api_key = get_tavily_key()
    query_text = query
    if domain_filter == "linkedin":
        query_text = f"site:linkedin.com {query}"
        topic = "general"

    if not api_key:
        log(f"  No Tavily API key — falling back to local search for '{query_text}'")
        return searx_search(query, n=n, domain_filter=domain_filter, topic=topic)

    body = {
        "api_key": api_key,
        "query": query_text,
        "search_depth": "basic",
        "topic": topic,
        "max_results": n,
        "include_answer": False,
        "include_raw_content": False,
    }
    if topic == "news" and days:
        body["days"] = days

    try:
        payload = _request_json(
            "https://api.tavily.com/search",
            body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=20,
        )
        results = _normalize_results(payload.get("results", []), text_key="content")
        if results:
            return results
        log(f"  Tavily returned no results for '{query_text}' — trying local search")
    except Exception as e:
        log(f"  Tavily error for '{query_text}': {e}")

    return searx_search(query, n=n, domain_filter=domain_filter, topic=topic)


def exa_search(query, n=5, domain_filter=None, days=3, fallback_topic=None):
    """Search via Exa first, then Tavily, then local SearXNG."""
    global exa_disabled_reason

    if exa_disabled_reason:
        log(f"  Exa disabled for this run ({exa_disabled_reason}) — falling back for '{query}'")
        return tavily_search(query, n=n, domain_filter=domain_filter, days=days,
                             topic=fallback_topic or ("general" if domain_filter == "linkedin" else "news"))

    api_key = get_exa_key()
    if not api_key:
        log(f"  No Exa API key — falling back for '{query}'")
        exa_disabled_reason = "missing_api_key"
        return tavily_search(query, n=n, domain_filter=domain_filter, days=days,
                             topic=fallback_topic or ("general" if domain_filter == "linkedin" else "news"))

    cutoff = (datetime.now(cairo) - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00.000Z")

    body = {
        "query": query,
        "numResults": n,
        "type": "neural",
        "startPublishedDate": cutoff,
        "text": {"maxCharacters": 400},
    }

    if domain_filter == "linkedin":
        body["includeDomains"] = ["linkedin.com"]
    elif domain_filter == "x":
        body["includeDomains"] = ["twitter.com", "x.com"]
    else:
        body["excludeDomains"] = ["youtube.com", "reddit.com", "twitter.com",
                                   "x.com", "facebook.com", "instagram.com", "tiktok.com"]

    try:
        payload = _request_json(
            "https://api.exa.ai/search",
            body,
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=15,
        )
        results = _normalize_results(payload.get("results", []), text_key="text")
        if results:
            return results
        log(f"  Exa returned no results for '{query}' — falling back")
    except Exception as e:
        reason = str(e)
        log(f"  Exa error for '{query}': {reason}")
        upper = reason.upper()
        if any(token in upper for token in ["402", "403", "NO_MORE_CREDITS", "FORBIDDEN", "PAYMENT REQUIRED"]):
            exa_disabled_reason = reason

    return tavily_search(query, n=n, domain_filter=domain_filter, days=days,
                         topic=fallback_topic or ("general" if domain_filter == "linkedin" else "news"))


def _oembed_tweet(url):
    """Fetch full tweet text via oEmbed API. Returns None on failure."""
    import urllib.parse
    tweet_url = url.replace("twitter.com", "x.com")
    try:
        oembed_url = f"https://publish.twitter.com/oembed?url={urllib.parse.quote(tweet_url)}&dnt=true"
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            oembed = json.loads(resp.read())
        return re.sub(r"<[^>]+>", "", oembed.get("html", "")).strip()
    except Exception:
        return None


def fmt(results, max_items=5):
    """Format Exa results as markdown bullets."""
    lines = []
    for r in results[:max_items]:
        title = r.get("title", "").strip() or "Untitled"
        url = r.get("url", "").strip()
        # For tweets: use oEmbed for full text instead of Exa snippet
        if "x.com" in url or "twitter.com" in url:
            full_text = _oembed_tweet(url)
            snippet = full_text[:300] if full_text else (r.get("text") or "").strip()[:200]
        else:
            snippet = (r.get("text") or r.get("summary") or "").strip()[:200]
        if url:
            line = f"- [{title}]({url})"
        else:
            line = f"- {title}"
        if snippet:
            line += f"\n  _{snippet}_"
        lines.append(line)
    return "\n".join(lines) if lines else "_No results found_"


def build_intel():
    sections = []

    # ── 1. Hot Topics ─────────────────────────────────────────────────────
    log("Section 1: Hot Topics...")
    hot = []
    for q in [
        "AI agents autonomous workflows enterprise 2026",
        "PMO digital transformation GCC executive leadership",
        "AI healthcare innovation Middle East",
    ]:
        hot.extend(exa_search(q, n=3, days=3))
    hot = filter_results(
        hot,
        required_groups=[
            ["ai", "agent", "digital transformation", "healthcare", "pmo"],
        ],
        excluded_domains=["wikinews.org", "domain-b.com", "startupfortune.com", "msn.com"],
        excluded_terms=["press release", "sponsored", "promoted content"],
    )
    hot = rank_results(
        hot,
        preferred_terms=["enterprise", "agent", "workflow", "healthcare", "gcc", "digital transformation", "pmo"],
        preferred_domains=["forbes.com", "healthcareitnews.com", "cio.com", "mckinsey.com", "gartner.com", "techradar.com", "cmswire.com", "beckershospitalreview.com"],
        penalty_domains=["usatoday.com/press-release"],
        penalty_terms=["press release", "sponsored"],
    )
    hot = dedupe_results(hot)

    sections.append(f"""## 1. Hot Topics (AI / Tech / PMO)
*Fresh signals for content angles and conversations — {now_str}*

{fmt(hot, 6)}
""")

    # ── 2. Job Market Signals ──────────────────────────────────────────────
    log("Section 2: Job Market Signals...")
    jobs = exa_search("VP Director executive PMO digital transformation hiring GCC UAE Saudi Arabia 2026", n=5, days=14, fallback_topic="general")
    jobs += exa_search("AI program manager technology executive Middle East job opening 2026", n=3, days=21, fallback_topic="general")
    jobs += exa_search("Riyadh Dubai Abu Dhabi PMO Director transformation job opening", n=3, days=21, fallback_topic="general")
    jobs += exa_search("Chief digital transformation officer UAE Saudi appointment 2026", n=2, days=30, fallback_topic="general")
    jobs = filter_results(
        jobs,
        excluded_domains=["youtube.com", "reddit.com", "coursera.org", "udemy.com"],
        excluded_terms=["education", "course", "certificate", "program", "executive education", "bootcamp", "training"],
        required_groups=[
            ["gcc", "uae", "saudi", "riyadh", "dubai", "abu dhabi", "middle east"],
            ["job", "opening", "hiring", "career", "vacancy", "role", "position", "director", "vp", "chief", "appointed", "appoints", "joins as"],
            ["pmo", "digital transformation", "ai", "technology", "program manager", "transformation"],
        ],
    )
    jobs = rank_results(
        jobs,
        preferred_terms=["hiring", "job", "opening", "director", "vp", "chief", "pmo", "digital transformation", "riyadh", "dubai", "abu dhabi"],
        preferred_domains=["linkedin.com/jobs", "bayt.com", "gulftalent.com", "indeed.com", "founditgulf.com", "naukrigulf.com"],
        penalty_domains=["kellogg.northwestern.edu", "mckinsey.com", "coursera.org", "udemy.com"],
        penalty_terms=["executive education", "guide", "course", "program"],
    )
    jobs = [r for r in dedupe_results(jobs) if "linkedin.com" not in (r.get("url") or "") or "/jobs/" in (r.get("url") or "")]

    sections.append(f"""## 2. Job Market Signals
*Executive hiring trends in GCC — context for HR Agent*

{fmt(jobs, 6)}
""")

    # ── 3. LinkedIn Engagement Opportunities ──────────────────────────────
    log("Section 3: LinkedIn Opportunities...")
    li = exa_search("AI transformation leadership lessons PMO", n=4, domain_filter="linkedin", days=5)
    if len(li) < 3:
        li += exa_search("digital health executive strategy GCC", n=3, domain_filter="linkedin", days=7)
    li = filter_results(
        li,
        required_terms=["linkedin.com"],
        excluded_terms=["jobs", "hiring", "careers", "comprehensive guide", "introduction:"],
    )
    li = rank_results(
        li,
        preferred_terms=["ai", "pmo", "digital transformation", "healthcare", "leadership", "strategy"],
        preferred_domains=["linkedin.com/pulse", "linkedin.com/posts"],
        penalty_terms=["jobs", "careers"],
    )
    li = dedupe_results(li)

    sections.append(f"""## 3. LinkedIn Engagement Opportunities
*Fresh posts worth commenting on — for CMO Agent*

{fmt(li, 5)}

**Ahmed's strongest comment angles:**
- AI agents + PMO/program management (rare intersection, he owns it)
- Healthcare digital transformation in GCC (20 years of ops credibility)
- Executive leadership + AI adoption (personal transformation story)
""")

    # ── 4. Company Intel ──────────────────────────────────────────────────
    log("Section 4: Company Intel...")
    co = []
    for company, q in [
        ("Cigna Healthcare", "Cigna Healthcare Middle East news 2026"),
        ("G42 / Inception", "G42 Inception UAE AI news 2026"),
        ("Involved Solutions", "Involved Solutions Egypt technology 2026"),
    ]:
        r = exa_search(q, n=3, days=30)
        if company == "Cigna Healthcare":
            r = filter_results(
                r,
                required_terms=["cigna"],
                excluded_domains=["linkedin.com", "wikinews.org"],
                excluded_terms=["stock", "price target", "investor alert"],
            )
        elif company == "G42 / Inception":
            r = filter_results(
                r,
                required_terms=["g42", "inception"],
                excluded_domains=["linkedin.com", "wikinews.org"],
                excluded_terms=["stock", "price target"],
            )
        elif company == "Involved Solutions":
            r = filter_results(
                r,
                required_terms=["involved solutions"],
                excluded_domains=["linkedin.com", "wikinews.org"],
                excluded_terms=["stock", "price target"],
            )
        r = rank_results(
            r,
            preferred_terms=[company.split(" /")[0].lower(), "middle east", "uae", "egypt", "dubai", "abu dhabi"],
            preferred_domains=["cigna.com", "newsroom.cigna.com", "g42.ai", "inception.com", "wamda.com", "magnitt.com", "menabytes.com", "reuters.com"],
            penalty_domains=["prnewswire.co.uk", "globenewswire.com", "businesswire.com", "msn.com"],
            penalty_terms=["press release", "sponsored"],
        )
        r = dedupe_results(r)
        if r:
            co.append(f"\n### {company}")
            co.append(fmt(r, 2))

    sections.append(f"""## 4. Company Intel
*News on active applications — for HR Agent interview/follow-up prep*

{"\n".join(co) if co else "_No recent news found_"}
""")

    # ── Header ─────────────────────────────────────────────────────────────
    header = f"""# DAILY-INTEL.md
*Generated: {now_str}*
*Consumers: CEO (morning briefing), HR Agent (job signals + company intel), CMO Agent (content angles)*
*Next run: tomorrow 05:45 Cairo*

---

"""
    return header + "\n".join(sections)


def main():
    log(f"Intel sweep for {today}")

    content = build_intel()

    if DRY_RUN:
        print("\n" + "=" * 60)
        print(content)
        print("=" * 60)
        log("DRY RUN — file not written")
        return

    INTEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    INTEL_FILE.write_text(content)
    log(f"Written → {INTEL_FILE}")

    # Dated archive
    archive = BASE / "intel" / f"intel-{today}.md"
    archive.write_text(content)
    log(f"Archived → {archive}")

    log("DONE")


if __name__ == "__main__":
    main()
