#!/usr/bin/env python3
"""
LinkedIn Job Scout - Full Pipeline Integration
Runs job searches, adds to pipeline.md + Google Sheets
"""

import subprocess
import json
import os
from datetime import datetime
from pathlib import Path

# Config
SHEET_ID = "1uKOh3XlsVb6SC0tAHkr239N4Y2d2fQr_BiQJcMHrjNw"
ACCOUNT = "ahmednasr999@gmail.com"
PIPELINE_FILE = Path("/root/.openclaw/workspace/jobs-bank/pipeline.md")
LOG_FILE = Path("/root/.openclaw/workspace/logs/linkedin-scout.log")

# Search terms
SEARCHES = [
    ("PMO Director", "UAE"),
    ("Program Manager", "UAE"),
    ("CTO", "Dubai"),
    ("Head of AI", "UAE"),
    ("Digital Transformation", "GCC"),
]

def defuddle_fetch(url: str) -> str:
    """Fetch via Defuddle, fallback Jina."""
    import urllib.request
    try:
        clean = url.replace("https://", "").replace("http://", "")
        req = urllib.request.Request(f"https://defuddle.md/{clean}", headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            if content and len(content) > 200:
                return content
    except Exception:
        pass
    try:
        req = urllib.request.Request(f"https://r.jina.ai/{url}", headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except Exception:
        pass
    return ""


def run_webfetch(keyword: str, location: str) -> str:
    """Fetch job listings: Defuddle first, curl fallback"""
    keyword_enc = keyword.replace(" ", "%20")
    location_enc = location.replace(" ", "%20")
    url = f"https://www.linkedin.com/jobs/search/?keywords={keyword_enc}&location={location_enc}&f_TPR=r604800"
    
    # Try Defuddle/Jina first
    content = defuddle_fetch(url)
    if content and len(content) > 500:
        return content
    
    # Fallback to curl
    cmd = [
        "curl", "-s", "-L", 
        "-H", "User-Agent: Mozilla/5.0",
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout

def parse_jobs(html: str) -> list:
    """Parse job listings from HTML"""
    import re
    jobs = []
    
    # Pattern to extract job titles and companies
    pattern = r'<h3[^>]*class="[^"]*job-card-list__title[^"]*"[^>]*>.*?<a[^>]*href="([^"]*job[^"]*)"[^>]*>([^<]+)'
    matches = re.findall(pattern, html, re.DOTALL)
    
    for match in matches[:10]:
        url, title = match
        title = title.strip()
        # Try to find company
        company_match = re.search(r'company/([^?]+)', url)
        company = company_match.group(1).replace('-', ' ').title() if company_match else "Unknown"
        
        if title and "job" not in title.lower():
            jobs.append({"title": title, "company": company, "url": "https://www.linkedin.com" + url[:200]})
    
    return jobs

def get_next_pipeline_row():
    """Find next row number in pipeline"""
    if not PIPELINE_FILE.exists():
        return 21
    content = PIPELINE_FILE.read_text()
    lines = content.split("\n")
    for line in reversed(lines):
        if line.startswith("| "):
            parts = line.split("|")
            if len(parts) > 2 and parts[2].strip().isdigit():
                return int(parts[2].strip()) + 1
    return 21

def add_to_pipeline(job: dict, row_num: int) -> bool:
    """Add job to pipeline.md"""
    if not PIPELINE_FILE.exists():
        print(f"Pipeline file not found: {PIPELINE_FILE}")
        return False
    
    content = PIPELINE_FILE.read_text()
    
    # Find the table end
    line = f"| {row_num} | ☑️ | [Company] | {job['title']} | GCC | TBD | 🔍 Discovered | — | {datetime.now().strftime('%Y-%m-%d')} | — | |"
    
    # Append before the closing ---
    if "---" in content:
        content = content.replace("---", f"{line}\n---", 1)
    
    PIPELINE_FILE.write_text(content)
    return True

def add_to_sheet(job: dict) -> dict:
    """Add job to Google Sheets via gog"""
    import subprocess
    
    # Prepare gog command
    row_data = [
        job.get("url", ""),
        job.get("company", "Unknown"),
        job.get("title", "Unknown Role"),
        "",  # JD
        "",  # Salary
        "LinkedIn Scout",  # Notes
        "TBD",  # ATS Score
        "SKIP",  # Decision
        "Auto-discovered from LinkedIn",  # Reason
        "Discovered",  # CV Status
        "",  # Ahmed Decision
        "",  # Applied Date
        "",  # CV Link
    ]
    
    # Get next row
    try:
        result = subprocess.run(
            ["gog", "sheets", "get", SHEET_ID, "Sheet1!A:A", "--account", ACCOUNT, "--json"],
            capture_output=True, text=True, timeout=10,
            env={"GOG_KEYRING_PASSWORD": "pass@123", **os.environ}
        )
        data = json.loads(result.stdout) if result.stdout else {"values": []}
        next_row = len(data.get("values", [])) + 1
    except Exception as e:
        print(f"Error getting row: {e}")
        next_row = 21
    
    range_ref = f"Sheet1!A{next_row}:M{next_row}"
    values_json = json.dumps([row_data])
    
    try:
        subprocess.run(
            ["gog", "sheets", "update", SHEET_ID, range_ref,
             "--values-json", values_json, "--input", "USER_ENTERED",
             "--account", ACCOUNT],
            capture_output=True, text=True, timeout=10,
            env={"GOG_KEYRING_PASSWORD": "pass@123", **os.environ},
            check=True
        )
        return {"status": "added", "row": next_row}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    print(f"=== LinkedIn Job Scout - {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    
    all_jobs = []
    
    for keyword, location in SEARCHES:
        print(f"Searching: {keyword} in {location}...")
        html = run_webfetch(keyword, location)
        jobs = parse_jobs(html)
        
        for job in jobs:
            job["keyword"] = keyword
            job["location"] = location
            all_jobs.append(job)
        
        print(f"  Found {len(jobs)} jobs")
    
    print(f"\nTotal jobs found: {len(all_jobs)}")
    
    # Add jobs to pipeline and sheet
    row_num = get_next_pipeline_row()
    added = 0
    
    for job in all_jobs[:10]:  # Limit to 10 per run
        print(f"\nProcessing: {job['title']} at {job['company']}")
        
        # Add to pipeline
        add_to_pipeline(job, row_num)
        
        # Add to sheet
        result = add_to_sheet(job)
        print(f"  Sheet: {result}")
        
        row_num += 1
        added += 1
    
    print(f"\n=== Complete: {added} jobs added to pipeline ===")
    
    # Git commit
    try:
        subprocess.run(["git", "add", "jobs-bank/pipeline.md"], cwd="/root/.openclaw/workspace", check=True)
        subprocess.run(["git", "commit", "-m", f"scout: added {added} LinkedIn jobs - {datetime.now().strftime('%Y-%m-%d')}"], 
                      cwd="/root/.openclaw/workspace", check=True)
        subprocess.run(["git", "push"], cwd="/root/.openclaw/workspace", check=True)
        print("Git: committed and pushed")
    except Exception as e:
        print(f"Git error: {e}")
    
    return {"jobs_found": len(all_jobs), "jobs_added": added}

if __name__ == "__main__":
    main()
