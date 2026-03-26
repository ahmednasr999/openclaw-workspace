#!/usr/bin/env python3
"""
wayback-fallback.py
====================
Fetches archived versions of URLs via Wayback Machine.
Used when primary fetch fails (429, 403, connection error).

Usage:
  python3 wayback-fallback.py "https://venturebeat.com/ai/article-slug"
  # Returns archived text or None

Also a standalone test:
  python3 wayback-fallback.py --test-all

Flow in article fetch:
  1. Fetch primary URL
  2. If fails with 429/403/timeout → try Wayback
  3. Wayback CDX API → check if archived
  4. Fetch archived URL → return text
"""
import json, re, ssl, sys, urllib.request, urllib.error, urllib.parse
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
}

TIMEOUT = 15
CTX = ssl.create_default_context()

def get_wayback_url(url):
    """Check Wayback Machine CDX API for archived snapshot."""
    cdx_url = f"https://web.archive.org/web/2/{urllib.parse.quote(url)}"
    req = urllib.request.Request(cdx_url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=CTX) as r:
            # CDX returns metadata lines; find closest to today
            lines = r.read().decode("utf-8", errors="ignore").strip().split("\n")
            if not lines:
                return None
            # Last non-redirect line is most recent
            for line in reversed(lines):
                parts = line.split()
                if len(parts) >= 4 and parts[4] != "redirect":
                    timestamp = parts[1]
                    wayback_url = f"https://web.archive.org/web/{timestamp}/{urllib.parse.urlparse(url)._url}"
                    return wayback_url, timestamp
    except Exception:
        pass
    return None

def fetch_wayback(url):
    """Fetch full page from Wayback Machine."""
    result = get_wayback_url(url)
    if not result:
        return None, "No archive found"
    
    wayback_url, timestamp = result
    
    req = urllib.request.Request(wayback_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=CTX) as r:
            html = r.read().decode("utf-8", errors="ignore")
            # Check if Wayback served a real snapshot or an error page
            if "prewrap" not in html and len(html) < 5000:
                return None, f"Archive too short ({len(html)} chars)"
            return html, timestamp
    except Exception as e:
        return None, f"Failed to fetch archive: {e}"

def strip_html(html):
    t = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    t = re.sub(r"<style[^>]*>.*?</style>", "", t, flags=re.DOTALL)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"&nbsp;", " ", t)
    t = re.sub(r"&#x[A-Fa-f0-9]+;", " ", t)
    t = re.sub(r"&[a-z]+;", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def extract_text_from_wayback(html):
    """Extract substantial text from Wayback HTML."""
    if not html or len(html) < 1000:
        return ""
    
    # Try to find article content
    for sel in [
        r'<div[^>]+class=["\'](?:[^"\']*article[^"\']*|story-body|post-content|entry-content)["\'][^>]*>(.*?)</div>',
        r"<article[^>]*>(.*?)</article>",
    ]:
        m = re.search(sel, html, re.DOTALL | re.I)
        if m:
            t = strip_html(m.group(1))
            if len(t) > 300:
                return t[:50000]
    
    # Fallback: collect paragraphs
    paras = re.findall(r"<p[^>]*>(.*?)</p>", html, re.DOTALL | re.I)
    big = [strip_html(p) for p in paras if len(strip_html(p)) > 80]
    if big:
        return "\n\n".join(big[:30])[:50000]
    
    return strip_html(html)[:50000]

def fetch_with_fallback(url):
    """Fetch article with Wayback fallback. Returns (text, source, timestamp)."""
    # Step 1: Try direct
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=CTX) as r:
            html = r.read().decode("utf-8", errors="ignore")
            if len(html) > 1000:
                return html, "direct", None
    except urllib.error.HTTPError as e:
        if e.code not in (403, 429, 500, 502, 503):
            return None, f"HTTP {e.code}", None
        print(f"  Primary fetch failed ({e.code}), trying Wayback...")
    except Exception as e:
        print(f"  Primary fetch error: {e}, trying Wayback...")
    
    # Step 2: Try Wayback
    html, ts_or_err = fetch_wayback(url)
    if html:
        text = extract_text_from_wayback(html)
        return text, "wayback", ts_or_err
    
    return None, "failed", ts_or_err

def test_urls():
    """Test the fallback on known blocked/unblocked URLs."""
    test_cases = [
        ("https://venturebeat.com/ai/anthropic-launches-cowork-a-claude-desktop-agent/", "VentureBeat (known blocked)"),
        ("https://fs.blog/feed/", "Farnam Street (RSS)"),
        ("https://www.healthcareittoday.com/feed/", "Healthcare IT Today (RSS)"),
    ]
    
    for url, desc in test_cases:
        print(f"\n--- {desc} ---")
        result, source, ts = fetch_with_fallback(url)
        if result:
            print(f"  Source: {source} | Timestamp: {ts} | Chars: {len(result)}")
            print(f"  Preview: {result[:200]}...")
        else:
            print(f"  FAILED: {source}")

if __name__ == "__main__":
    if "--test-all" in sys.argv:
        test_urls()
    elif len(sys.argv) > 1:
        url = sys.argv[1]
        result, source, ts = fetch_with_fallback(url)
        if result:
            print(f"SUCCESS ({source}, archived {ts}): {len(result)} chars")
            print(result[:1000])
        else:
            print(f"FAILED: {source}")
    else:
        print("Usage:")
        print("  python3 wayback-fallback.py <url>")
        print("  python3 wayback-fallback.py --test-all")
