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

import json, os, sys, ssl, urllib.request, re
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent.parent
INTEL_FILE = BASE / "intel" / "DAILY-INTEL.md"
EXA_CONFIG = BASE / "config" / "exa.json"

cairo = timezone(timedelta(hours=2))
today = datetime.now(cairo).strftime("%Y-%m-%d")
now_str = datetime.now(cairo).strftime("%Y-%m-%d %H:%M Cairo")

DRY_RUN = "--dry-run" in sys.argv
ctx = ssl.create_default_context()


def log(msg):
    print(f"[intel-sweep] {msg}", flush=True)


def get_exa_key():
    try:
        return json.loads(EXA_CONFIG.read_text())["api_key"]
    except:
        return os.environ.get("EXA_API_KEY", "")


def exa_search(query, n=5, domain_filter=None, days=3):
    """Search via Exa REST API."""
    api_key = get_exa_key()
    if not api_key:
        log(f"  No Exa API key — skipping '{query}'")
        return []

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
        req = urllib.request.Request(
            "https://api.exa.ai/search",
            data=json.dumps(body).encode(),
            method="POST",
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        with urllib.request.urlopen(req, context=ctx, timeout=25) as r:
            return json.loads(r.read()).get("results", [])
    except Exception as e:
        log(f"  Exa error for '{query}': {e}")
        return []


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

    sections.append(f"""## 1. Hot Topics (AI / Tech / PMO)
*Fresh signals for content angles and conversations — {now_str}*

{fmt(hot, 6)}
""")

    # ── 2. Job Market Signals ──────────────────────────────────────────────
    log("Section 2: Job Market Signals...")
    jobs = exa_search("VP Director executive PMO digital transformation hiring GCC UAE Saudi Arabia 2026", n=5, days=14)
    jobs += exa_search("AI program manager technology executive Middle East job opening 2026", n=3, days=21)

    sections.append(f"""## 2. Job Market Signals
*Executive hiring trends in GCC — context for HR Agent*

{fmt(jobs, 6)}
""")

    # ── 3. LinkedIn Engagement Opportunities ──────────────────────────────
    log("Section 3: LinkedIn Opportunities...")
    li = exa_search("AI transformation leadership lessons PMO", n=4, domain_filter="linkedin", days=5)
    if len(li) < 3:
        li += exa_search("digital health executive strategy GCC", n=3, domain_filter="linkedin", days=7)

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
        r = exa_search(q, n=2, days=30)
        if r:
            co.append(f"\n### {company}")
            co.append(fmt(r, 2))

    sections.append(f"""## 4. Company Intel
*News on active applications — for HR Agent interview/follow-up prep*

{"".join(co) if co else "_No recent news found_"}
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
