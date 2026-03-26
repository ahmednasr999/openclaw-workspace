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
import os
import re
import ssl
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, os.path.dirname(__file__))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

WORKSPACE = Path("/root/.openclaw/workspace")
MERGED = WORKSPACE / "data" / "jobs-merged.json"
JD_CACHE_DIR = WORKSPACE / "data" / "jd-cache"
MAX_FETCH = 300  # Enrich ALL candidates (review covers all now)
FETCH_TIMEOUT = 15
DELAY = 0.3  # seconds between requests
MAX_WORKERS = 3  # parallel fetch threads (conservative for LinkedIn API)

JD_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# LinkedIn Voyager API auth (cookies-based)
LI_COOKIES_FILE = Path("/root/.openclaw/cookies/linkedin.txt")

def _load_linkedin_cookies():
    """Load LinkedIn cookies from Netscape cookie file."""
    if not LI_COOKIES_FILE.exists():
        return None, None
    cookies = {}
    csrf = None
    with open(LI_COOKIES_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 7:
                name, value = parts[5], parts[6].strip('"')
                cookies[name] = value
                if name == 'JSESSIONID':
                    csrf = value.strip('"')
    cookie_str = '; '.join(f'{k}={v}' for k, v in cookies.items())
    return cookie_str, csrf

LI_COOKIE_STR, LI_CSRF = _load_linkedin_cookies()


def jd_cache_get(job_id):
    """Read JD from cache. Returns text or None."""
    cache_file = JD_CACHE_DIR / f"{job_id}.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text())
            jd = data.get("jd_text", "")
            if len(jd) > 100:
                return jd
        except Exception:
            pass
    return None


def jd_cache_put(job_id, jd_text, source="voyager"):
    """Write JD to cache."""
    cache_file = JD_CACHE_DIR / f"{job_id}.json"
    cache_file.write_text(json.dumps({
        "job_id": job_id,
        "jd_text": jd_text,
        "source": source,
        "cached_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }, indent=2))
    # ── DB write (dual-write, non-blocking) ──────────────────────────────────
    if _pdb:
        try:
            _pdb.update_field(
                job_id,
                jd_text=jd_text,
                jd_path=str(cache_file),
                jd_fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            )
        except Exception:
            pass
    # ─────────────────────────────────────────────────────────────────────────


def fetch_linkedin_voyager(job_id):
    """Fetch JD from LinkedIn Voyager API using cookies. Returns JD text or None.
    Checks cache first, writes to cache on success."""
    # Check cache first
    cached = jd_cache_get(job_id)
    if cached:
        return cached

    if not LI_COOKIE_STR or not LI_CSRF:
        return None
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "csrf-token": LI_CSRF,
        "Cookie": LI_COOKIE_STR,
    }
    url = f"https://www.linkedin.com/voyager/api/jobs/jobPostings/{job_id}"
    ctx = ssl.create_default_context()
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=FETCH_TIMEOUT, context=ctx) as r:
            data = json.loads(r.read(500000))
            desc = data.get("description", {})
            text = desc.get("text", "") if isinstance(desc, dict) else str(desc) if desc else None
            if text and len(text) > 100:
                jd_cache_put(job_id, text, "voyager")
            return text
    except Exception:
        return None


def fetch_linkedin_jobspy(job_id, title_hint=""):
    """Fallback: use tls-client to fetch LinkedIn JD from public job page.
    tls-client mimics Chrome's TLS fingerprint, bypassing LinkedIn's auth wall
    on public job listing pages. No cookies or login required.
    Inspired by job-ops/JobSpy extractor approach."""
    # Check cache first
    cached = jd_cache_get(job_id)
    if cached:
        return cached
    try:
        import tls_client
        from html import unescape as html_unescape

        session = tls_client.Session(
            client_identifier="chrome_120",
            random_tls_extension_order=True,
        )
        url = f"https://www.linkedin.com/jobs/view/{job_id}"
        resp = session.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        })
        if resp.status_code != 200:
            return None

        html = resp.text
        # Primary: show-more-less-html div (LinkedIn's standard JD container)
        m = re.search(
            r'<div[^>]*class="show-more-less-html__markup[^"]*"[^>]*>(.*?)</div>',
            html, re.S
        )
        if m:
            text = re.sub(r'<[^>]+>', ' ', m.group(1))
            text = re.sub(r'\s+', ' ', html_unescape(text)).strip()
            if len(text) > 100:
                jd_cache_put(job_id, text, "tls_public")
                return text

        # Secondary: description__text section
        m = re.search(
            r'class="description__text[^"]*"[^>]*>(.*?)</section>',
            html, re.S
        )
        if m:
            text = re.sub(r'<[^>]+>', ' ', m.group(1))
            text = re.sub(r'\s+', ' ', html_unescape(text)).strip()
            if len(text) > 100:
                jd_cache_put(job_id, text, "tls_public")
                return text

        return None
    except Exception as e:
        print(f"  tls-client fallback failed: {e}")
        return None


def extract_linkedin_job_id(url):
    """Extract numeric job ID from LinkedIn URL."""
    m = re.search(r'(\d{8,})', url)
    return m.group(1) if m else None


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
        
        # LinkedIn: try Voyager API first (authenticated, reliable)
        if "linkedin.com" in url:
            job_id = extract_linkedin_job_id(url)
            if job_id:
                jd = fetch_linkedin_voyager(job_id)
                if jd and len(jd) > 100:
                    job["jd_text"] = jd[:5000]
                    job["jd_fetch_status"] = "voyager_ok"
                    job["jd_live"] = True
                    nationals = detect_nationals_only(jd)
                    if nationals:
                        job["nationals_only"] = True
                        print(f"  [{idx}] {title}... VOYAGER OK ({len(jd)} chars) ⚠️ NATIONALS ONLY")
                    else:
                        print(f"  [{idx}] {title}... VOYAGER OK ({len(jd)} chars)")
                    return "enriched", nationals

            # Fallback: tls-client direct fetch (no auth needed, mimics Chrome TLS)
            jd = fetch_linkedin_jobspy(job_id, title)
            if jd and len(jd) > 100:
                job["jd_text"] = jd[:5000]
                job["jd_fetch_status"] = "tls_ok"
                job["jd_live"] = True
                nationals = detect_nationals_only(jd)
                if nationals:
                    job["nationals_only"] = True
                    print(f"  [{idx}] {title}... TLS OK ({len(jd)} chars) ⚠️ NATIONALS ONLY")
                else:
                    print(f"  [{idx}] {title}... TLS OK ({len(jd)} chars)")
                return "enriched", nationals
        
        # Fallback: raw HTTP fetch (works for Indeed, Google Jobs, company pages)
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
