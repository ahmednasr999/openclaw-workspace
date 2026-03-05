#!/usr/bin/env python3
"""
LinkedIn Job Scout
Daily automated job search from LinkedIn
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Configuration
OUTPUT_DIR = Path("/root/.openclaw/workspace/memory")
OUTPUT_FILE = OUTPUT_DIR / "linkedin-job-scout.md"
LOG_FILE = Path("/root/.openclaw/workspace/logs/linkedin-scout.log")

# Configure logging
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# Search configuration
SEARCH_TERMS = [
    ("PMO Director", "United Arab Emirates"),
    ("Program Manager", "United Arab Emirates"),
    ("VP Digital Transformation", "United Arab Emirates"),
    ("CTO", "Dubai"),
    ("Head of AI", "UAE"),
    ("Director IT", "Saudi Arabia"),
    ("Digital Transformation Executive", "GCC"),
    ("Chief Digital Officer", "UAE"),
]

def build_url(keyword: str, location: str) -> str:
    """Build LinkedIn job search URL"""
    keyword_encoded = keyword.replace(" ", "%20")
    location_encoded = location.replace(" ", "%20")
    # f_TPR=r604800 = last 7 days
    return f"https://www.linkedin.com/jobs/search/?keywords={keyword_encoded}&location={location_encoded}&f_TPR=r604800&f_E=1"

def get_jobs_webfetch(keyword: str, location: str) -> list:
    """Fetch jobs using web_fetch tool via exec curl"""
    url = build_url(keyword, location)
    
    # Use curl to fetch the page
    import subprocess
    
    try:
        cmd = [
            "curl", "-s", "-L", 
            "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        html = result.stdout
        
        # Extract job titles using grep/sed
        import re
        
        # Find job cards
        jobs = re.findall(r'class="job-card-list__title[^"]*"[^>]*>\s*<a[^>]*>([^<]+)', html)
        
        # Clean up
        jobs = [j.strip() for j in jobs[:15]]
        
        # Try alternative pattern
        if not jobs:
            jobs = re.findall(r'<h3[^>]*>([^<]+)<span[^>]*class="[^"]*screen-reader-text[^"]*"[^>]*>([^<]+)', html)
            jobs = [f"{j[0].strip()} at {j[1].strip()}" for j in jobs[:15]]
        
        logging.info(f"Found {len(jobs)} jobs for '{keyword}' in '{location}'")
        return jobs
        
    except Exception as e:
        logging.error(f"Error fetching {keyword} in {location}: {e}")
        return []

def generate_report(jobs_data: dict) -> str:
    """Generate markdown report"""
    report = []
    report.append(f"# LinkedIn Job Scout — {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    report.append("")
    report.append("> Auto-generated job search from LinkedIn")
    report.append("")
    
    for location, keywords in jobs_data.items():
        report.append(f"## {location}")
        report.append("")
        
        for keyword, jobs in keywords.items():
            if jobs:
                report.append(f"### {keyword}")
                report.append("")
                for job in jobs:
                    report.append(f"- {job}")
                report.append("")
    
    report.append("---")
    report.append(f"*Scanned: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*")
    
    return "\n".join(report)

def main():
    logging.info("Starting LinkedIn Job Scout...")
    
    jobs_data = {}
    
    for keyword, location in SEARCH_TERMS:
        logging.info(f"Searching: {keyword} in {location}")
        
        if location not in jobs_data:
            jobs_data[location] = {}
        
        jobs = get_jobs_webfetch(keyword, location)
        jobs_data[location][keyword] = jobs
    
    # Generate report
    report = generate_report(jobs_data)
    
    # Save to file
    OUTPUT_FILE.write_text(report)
    logging.info(f"Report saved to {OUTPUT_FILE}")
    
    # Count total jobs
    total = sum(len(jobs) for loc in jobs_data.values() for jobs in loc.values())
    logging.info(f"Total jobs found: {total}")
    
    return total

if __name__ == "__main__":
    main()
