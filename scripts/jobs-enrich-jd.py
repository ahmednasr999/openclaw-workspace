#!/usr/bin/env python3
"""
jobs-enrich-jd.py — Fetches full job descriptions for merged jobs before LLM review.

Reads: data/jobs-merged.json
Writes: data/jobs-merged.json (enriched with jd_text field)

Uses web_fetch to grab LinkedIn/Indeed job pages and extract JD text.
Runs BEFORE jobs-review.py in the pipeline.

Skips jobs that already have jd_text (idempotent).
Rate limited: 1 request/sec to avoid 429s.
"""
import json
import re
import ssl
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

WORKSPACE = Path("/root/.openclaw/workspace")
MERGED = WORKSPACE / "data" / "jobs-merged.json"
MAX_FETCH = 50  # Only enrich top 50 jobs (same as what review processes)
FETCH_TIMEOUT = 15
DELAY = 1.0  # seconds between requests


def fetch_page(url, max_chars=200000):
    """Fetch a URL and return text content."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    ctx = ssl.create_default_context()
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=FETCH_TIMEOUT, context=ctx) as r:
            raw = r.read(max_chars)
            return raw.decode("utf-8", errors="ignore")
    except Exception as e:
        return None


def extract_linkedin_jd(html):
    """Extract job description from LinkedIn public HTML."""
    if not html:
        return None
    
    # Method 1 (BEST): show-more-less-html with clamp class — contains full JD
    m = re.search(r'show-more-less-html__markup--clamp-after-5[^>]*>(.*?)</div>', html, re.S)
    if m:
        text = re.sub(r'<[^>]+>', ' ', m.group(1))
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 100:
            return text[:3000]
    
    # Method 2: show-more-less-html without clamp (older pages)
    m = re.search(r'show-more-less-html__markup[^>]*>(.*?)<button', html, re.S)
    if m:
        text = re.sub(r'<[^>]+>', ' ', m.group(1))
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 100:
            return text[:3000]
    
    # Method 3: description__text section
    m = re.search(r'class="description__text[^"]*"[^>]*>(.*?)</section>', html, re.S)
    if m:
        text = re.sub(r'<[^>]+>', ' ', m.group(1))
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 100:
            return text[:3000]
    
    # Method 4: Meta description (short fallback)
    m = re.search(r'<meta\s+name="description"\s+content="([^"]{50,})"', html, re.I)
    if m:
        desc = m.group(1)
        desc = desc.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        desc = desc.replace("&#39;", "'").replace("&quot;", '"')
        if len(desc) > 100:
            return desc
    
    return None


def extract_indeed_jd(html):
    """Extract job description from Indeed HTML."""
    if not html:
        return None
    
    # Indeed puts JD in jobDescriptionText div
    m = re.search(r'id="jobDescriptionText"[^>]*>(.*?)</div>', html, re.S)
    if m:
        text = re.sub(r'<[^>]+>', ' ', m.group(1))
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 100:
            return text[:3000]
    
    # Fallback to meta description
    m = re.search(r'<meta\s+name="description"\s+content="([^"]{50,})"', html, re.I)
    if m:
        return m.group(1)[:3000]
    
    return None


def extract_jd(html, url):
    """Route to the right extractor based on URL."""
    if "linkedin.com" in url:
        return extract_linkedin_jd(html)
    elif "indeed.com" in url:
        return extract_indeed_jd(html)
    else:
        # Generic extraction
        return extract_linkedin_jd(html)  # Same generic logic works


def detect_nationals_only(text):
    """Check if JD contains nationals-only requirement."""
    if not text:
        return False
    text_lower = text.lower()
    patterns = [
        "nationals only", "uae national", "emirati only", "saudi only",
        "kuwaiti national", "bahraini national", "qatari national",
        "omani national", "citizen only", "gcc national",
        "nationality is required", "must be a national",
    ]
    return any(p in text_lower for p in patterns)


def run():
    print("📄 JD Enrichment Agent")
    
    if not MERGED.exists():
        print("  No merged jobs file found")
        return
    
    data = json.load(open(MERGED))
    jobs = data.get("data", data.get("jobs", []))
    if not isinstance(jobs, list):
        print("  Invalid jobs format")
        return
    
    # Sort by keyword_score (same order as review) and take top N
    sorted_jobs = sorted(jobs, key=lambda j: j.get("keyword_score", 0), reverse=True)
    top_jobs = sorted_jobs[:MAX_FETCH]
    
    enriched = 0
    skipped = 0
    failed = 0
    nationals_flagged = 0
    
    for i, job in enumerate(top_jobs):
        url = job.get("url", "")
        title = job.get("title", "?")[:50]
        
        # Skip if already enriched
        if job.get("jd_text") and len(job.get("jd_text", "")) > 100:
            skipped += 1
            continue
        
        if not url or not url.startswith("http"):
            skipped += 1
            continue
        
        print(f"  [{i+1}/{len(top_jobs)}] {title}...", end=" ", flush=True)
        
        html = fetch_page(url)
        if not html:
            print("FAIL (fetch)")
            failed += 1
            time.sleep(DELAY)
            continue
        
        jd = extract_jd(html, url)
        if jd and len(jd) > 50:
            job["jd_text"] = jd
            enriched += 1
            
            # Also check for nationals-only
            if detect_nationals_only(jd):
                job["nationals_only"] = True
                nationals_flagged += 1
                print(f"OK ({len(jd)} chars) ⚠️ NATIONALS ONLY")
            else:
                print(f"OK ({len(jd)} chars)")
        else:
            print("FAIL (extract)")
            failed += 1
        
        time.sleep(DELAY)
    
    # Write back
    if isinstance(data, dict) and "data" in data:
        data["data"] = jobs
    elif isinstance(data, dict) and "jobs" in data:
        data["jobs"] = jobs
    
    json.dump(data, open(MERGED, "w"), indent=2)
    
    print(f"\n✅ Enriched: {enriched} | Skipped: {skipped} | Failed: {failed} | Nationals flagged: {nationals_flagged}")


if __name__ == "__main__":
    run()
