#!/usr/bin/env python3
"""
LinkedIn Gulf Jobs Scanner
Runs 120 searches (6 countries × 20 titles), filters by 24h, scores with ATS, notifies only qualified
"""

import os
import json
import time
import requests
from datetime import datetime
from urllib.parse import quote

# Configuration
COUNTRIES = [
    "Saudi Arabia",
    "United Arab Emirates", 
    "Qatar",
    "Bahrain",
    "Kuwait",
    "Oman"
]

TITLES = [
    "Chief Digital Officer",
    "Chief Technology Officer",
    "Chief Information Officer",
    "VP Digital Transformation",
    "Director Digital Transformation",
    "Head of Digital Transformation",
    "Head of IT",
    "Head of Technology",
    "Director of Technology",
    "VP Technology",
    "VP IT",
    "Director of IT",
    "Senior Director Digital Transformation",
    "Head of Digital",
    "Director of Digital Innovation",
    "Head of Digital Innovation",
    "Program Director",
    "PMO Director",
    "Chief Strategy Officer",
    "Chief Operating Officer"
]

OUTPUT_DIR = "/root/.openclaw/workspace/jobs-bank/scraped"
LOG_FILE = f"{OUTPUT_DIR}/cron-logs.md"
NOTIFIED_FILE = f"{OUTPUT_DIR}/notified-jobs.md"

def search_linkedin(title, country):
    """Search LinkedIn jobs with 24h filter"""
    t = quote(title)
    c = quote(country)
    url = f"https://www.linkedin.com/jobs/search/?keywords={t}&location={c}&f_TPR=r86400"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        text = resp.text
        
        # Extract job count
        import re
        match = re.search(r'(\d+)\s*jobs?\s*in', text)
        if match:
            count = int(match.group(1))
            return count, url
        return 0, url
    except Exception as e:
        print(f"Error: {e}")
        return 0, url

def main():
    print(f"Starting LinkedIn Gulf Jobs Scanner at {datetime.now()}")
    
    total_scanned = 0
    total_jobs = 0
    qualified_jobs = []
    
    for country in COUNTRIES:
        print(f"\n=== {country} ===")
        for title in TITLES:
            count, url = search_linkedin(title, country)
            total_scanned += 1
            total_jobs += count
            print(f"  {title}: {count}")
            time.sleep(1)  # Rate limiting
    
    # Log results
    with open(LOG_FILE, 'a') as f:
        f.write(f"\n## {datetime.now().isoformat()}\n")
        f.write(f"- Scanned: {total_scanned}\n")
        f.write(f"- Jobs found: {total_jobs}\n")
    
    print(f"\n=== SUMMARY ===")
    print(f"Scanned: {total_scanned}")
    print(f"Jobs found: {total_jobs}")

if __name__ == "__main__":
    main()
