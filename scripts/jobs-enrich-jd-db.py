#!/usr/bin/env python3
"""
jobs-enrich-jd-db.py — Enriches JDs directly from SQLite DB (not merged JSON).
Processes jobs with no JD, prioritizing today's batch then by created_at DESC.
"""
import sqlite3, sys, time, re, ssl
from pathlib import Path
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_PATH = Path("/root/.openclaw/workspace/data/nasr-pipeline.db")
MAX_FETCH = int(sys.argv[1]) if len(sys.argv) > 1 else 300
DELAY = 0.3
FETCH_TIMEOUT = 15
MAX_WORKERS = 3

NATIONALS_PATTERNS = [
    r"emirati nationals only", r"uae nationals only", r"saudi nationals only",
    r"nationals only", r"for nationals", r"citizens only",
]

def detect_nationals_only(text):
    t = text.lower()
    return any(re.search(p, t) for p in NATIONALS_PATTERNS)

def fetch_linkedin_jd(job_id):
    """Fetch JD via LinkedIn public job view (JobSpy approach)."""
    url = f"https://www.linkedin.com/jobs/view/{job_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        ctx = ssl.create_default_context()
        req = Request(url, headers=headers)
        with urlopen(req, timeout=FETCH_TIMEOUT, context=ctx) as r:
            html = r.read().decode("utf-8", errors="replace")
        # Extract description
        m = re.search(r'<div[^>]+class="[^"]*description[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
        if not m:
            m = re.search(r'"description"\s*:\s*\{"text"\s*:\s*"(.*?)"', html, re.DOTALL)
        if m:
            text = re.sub(r'<[^>]+>', ' ', m.group(1))
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 100:
                return text[:5000]
    except Exception:
        pass
    return None

def fetch_indeed_jd(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html",
    }
    try:
        ctx = ssl.create_default_context()
        req = Request(url, headers=headers)
        with urlopen(req, timeout=FETCH_TIMEOUT, context=ctx) as r:
            html = r.read().decode("utf-8", errors="replace")
        m = re.search(r'id="jobDescriptionText"[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
        if m:
            text = re.sub(r'<[^>]+>', ' ', m.group(1))
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 100:
                return text[:5000]
    except Exception:
        pass
    return None

def enrich_job(row):
    job_id, title, url, source = row['id'], row['title'], row['url'], row['source']
    if not url or not url.startswith('http'):
        return job_id, None, "no_url"
    
    time.sleep(DELAY)
    jd = None
    
    if 'linkedin.com' in url:
        m = re.search(r'/jobs/view/(\d+)', url)
        if m:
            jd = fetch_linkedin_jd(m.group(1))
    elif 'indeed.com' in url:
        jd = fetch_indeed_jd(url)
    
    if jd and len(jd) > 100:
        return job_id, jd, "ok"
    return job_id, None, "failed"

def main():
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    # Get jobs without JD - today's first, then oldest unscored
    cur.execute("""
        SELECT id, title, job_url as url, source FROM jobs
        WHERE (jd_text IS NULL OR length(jd_text) <= 100)
        AND job_url IS NOT NULL AND job_url != ''
        ORDER BY 
            CASE WHEN date(created_at) = date('now') THEN 0 ELSE 1 END,
            created_at DESC
        LIMIT ?
    """, (MAX_FETCH,))
    jobs = cur.fetchall()
    
    print(f"Jobs to enrich: {len(jobs)} (max {MAX_FETCH})")
    
    enriched = failed = 0
    nationals = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(enrich_job, j): j for j in jobs}
        for i, fut in enumerate(as_completed(futures), 1):
            job_id, jd, status = fut.result()
            title = futures[fut]['title'][:45]
            if jd:
                nat = detect_nationals_only(jd)
                db.execute(
                    "UPDATE jobs SET jd_text=? WHERE id=?",
                    (jd, job_id)
                )
                db.commit()
                enriched += 1
                flag = " ⚠️ NATIONALS" if nat else ""
                if nat:
                    nationals += 1
                print(f"  [{i}] {title}... ✅ ({len(jd)} chars){flag}")
            else:
                failed += 1
                if i <= 30 or i % 50 == 0:
                    print(f"  [{i}] {title}... ❌ {status}")
    
    db.close()
    print(f"\n✅ Enriched: {enriched} | Failed: {failed} | Nationals flagged: {nationals}")
    print(f"Coverage: {enriched}/{len(jobs)} = {round(100*enriched/max(1,len(jobs)))}%")

if __name__ == '__main__':
    main()
