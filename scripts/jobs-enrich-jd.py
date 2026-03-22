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
MAX_FETCH = 300  # Enrich ALL candidates (review covers all now)
FETCH_TIMEOUT = 15
DELAY = 0.5  # seconds between requests (parallel workers share load)
MAX_WORKERS = 5  # parallel fetch threads


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
    
    EXPIRED_SIGNALS = [
        "this job has expired", "job posting is closed", "no longer open",
        "position has been filled", "no longer available", "job has been removed",
        "this listing has expired", "vacancy has been closed",
        "this job is no longer accepting applications",
    ]
    STALE_SIGNALS = [
        "months ago", "month ago", "year ago", "years ago",
    ]
    
    def enrich_one(job, idx):
        """Enrich a single job. Returns (status, nationals_flag)."""
        url = job.get("url", "")
        title = job.get("title", "?")[:50]
        
        # Skip if already enriched
        if job.get("jd_text") and len(job.get("jd_text", "")) > 100:
            return "skipped", False
        
        if not url or not url.startswith("http"):
            return "skipped", False
        
        time.sleep(DELAY)  # rate limit per request
        html = fetch_page(url)
        if not html:
            job["jd_fetch_status"] = "fetch_failed"
            print(f"  [{idx}] {title}... FAIL (fetch)")
            return "failed", False
        
        # Liveness check
        html_lower = html[:20000].lower()
        if any(s in html_lower for s in EXPIRED_SIGNALS):
            job["jd_fetch_status"] = "expired"
            job["jd_live"] = False
            print(f"  [{idx}] {title}... EXPIRED")
            return "failed", False
        if any(s in html_lower for s in STALE_SIGNALS):
            job["jd_fetch_status"] = "stale"
            job["jd_live"] = False
            print(f"  [{idx}] {title}... STALE")
            return "failed", False
        
        job["jd_live"] = True
        job["jd_fetch_status"] = "ok"
        
        # Extract clean page text for ATS scoring
        page_text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL)
        page_text = re.sub(r'<style[^>]*>.*?</style>', ' ', page_text, flags=re.DOTALL)
        page_text = re.sub(r'<[^>]+>', ' ', page_text)
        page_text = re.sub(r'\s+', ' ', page_text).strip()
        if len(page_text) > 200:
            job["jd_page_text"] = page_text[:5000]
        
        jd = extract_jd(html, url)
        nationals = False
        if jd and len(jd) > 50:
            job["jd_text"] = jd
            if detect_nationals_only(jd):
                job["nationals_only"] = True
                nationals = True
                print(f"  [{idx}] {title}... OK ({len(jd)} chars) ⚠️ NATIONALS ONLY")
            else:
                print(f"  [{idx}] {title}... OK ({len(jd)} chars)")
            return "enriched", nationals
        else:
            print(f"  [{idx}] {title}... FAIL (extract)")
            return "failed", False
    
    # Parallel enrichment with ThreadPoolExecutor
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    to_process = []
    for i, job in enumerate(top_jobs, 1):
        if job.get("jd_text") and len(job.get("jd_text", "")) > 100:
            skipped += 1
        elif not job.get("url", "").startswith("http"):
            skipped += 1
        else:
            to_process.append((job, i))
    
    print(f"  Fetching {len(to_process)} jobs in parallel ({MAX_WORKERS} workers)...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(enrich_one, job, idx): (job, idx) for job, idx in to_process}
        for future in as_completed(futures):
            status, nationals = future.result()
            if status == "enriched":
                enriched += 1
            elif status == "failed":
                failed += 1
            elif status == "skipped":
                skipped += 1
            if nationals:
                nationals_flagged += 1
    
    # Write back
    if isinstance(data, dict) and "data" in data:
        data["data"] = jobs
    elif isinstance(data, dict) and "jobs" in data:
        data["jobs"] = jobs
    
    json.dump(data, open(MERGED, "w"), indent=2)
    
    print(f"\n✅ Enriched: {enriched} | Skipped: {skipped} | Failed: {failed} | Nationals flagged: {nationals_flagged}")


if __name__ == "__main__":
    run()
