#!/usr/bin/env python3
"""
Auto-Dossier Builder - Extracts company intelligence for job applications.
Uses Defuddle (primary) and Jina (fallback) for content extraction.

Usage: python3 auto-dossier.py <company_domain> [company_name] [role_title]
Example: python3 auto-dossier.py contango.ae Contango "Digital Transformation Consultant"
"""

import sys
import os
import time
import urllib.request
import json
from datetime import datetime
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
DOSSIER_DIR = f"{WORKSPACE}/jobs-bank/dossiers"


def log(msg):
    print(f"[dossier] {msg}")


def defuddle_fetch(url):
    """Fetch via Defuddle, fallback Jina."""
    # Try Defuddle
    try:
        clean = url.replace("https://", "").replace("http://", "")
        req = urllib.request.Request(f"https://defuddle.md/{clean}", headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            if content and len(content) > 200:
                log(f"  Defuddle: {len(content)} chars from {url}")
                return content
    except Exception as e:
        log(f"  Defuddle failed for {url}: {e}")
    # Fallback Jina
    try:
        req = urllib.request.Request(f"https://r.jina.ai/{url}", headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            if content and len(content) > 200:
                log(f"  Jina: {len(content)} chars from {url}")
                return content
    except Exception as e:
        log(f"  Jina failed for {url}: {e}")
    return ""


def extract_section(content, max_chars=2000):
    """Trim content to usable size."""
    if not content:
        return "Not available"
    # Remove YAML frontmatter if present
    if content.startswith("---"):
        end = content.find("---", 3)
        if end > 0:
            content = content[end+3:].strip()
    return content[:max_chars].strip() or "Not available"


def build_dossier(domain, company_name=None, role_title=None):
    """Build company dossier from web extraction."""
    if not company_name:
        company_name = domain.split(".")[0].title()
    
    log(f"Building dossier for {company_name} ({domain})")
    
    # Pages to extract
    pages = {
        "homepage": f"https://{domain}",
        "about": [
            f"https://{domain}/about",
            f"https://{domain}/about-us",
            f"https://{domain}/company",
        ],
        "leadership": [
            f"https://{domain}/team",
            f"https://{domain}/leadership",
            f"https://{domain}/about/team",
            f"https://{domain}/our-team",
        ],
        "careers": [
            f"https://{domain}/careers",
            f"https://{domain}/jobs",
            f"https://careers.{domain}",
        ],
        "services": [
            f"https://{domain}/services",
            f"https://{domain}/what-we-do",
            f"https://{domain}/solutions",
        ],
    }
    
    results = {}
    
    # Fetch homepage
    log("Fetching homepage...")
    results["homepage"] = defuddle_fetch(pages["homepage"])
    
    # Fetch other pages (try variants, with rate limit delay)
    for section, urls in pages.items():
        if section == "homepage":
            continue
        time.sleep(2)  # Rate limit protection
        log(f"Fetching {section}...")
        if isinstance(urls, list):
            for url in urls:
                content = defuddle_fetch(url)
                if content and len(content) > 200:
                    results[section] = content
                    break
            if section not in results:
                results[section] = ""
        else:
            results[section] = defuddle_fetch(urls)
    
    # Build dossier markdown
    date = datetime.now().strftime("%Y-%m-%d")
    slug = domain.replace(".", "-")
    
    dossier = f"""# Company Dossier: {company_name}

**Domain:** {domain}
**Generated:** {date}
**Role:** {role_title or "TBD"}

---

## Company Overview
{extract_section(results.get("homepage", ""), 2000)}

---

## About
{extract_section(results.get("about", ""), 2000)}

---

## Leadership Team
{extract_section(results.get("leadership", ""), 2000)}

---

## Services / What They Do
{extract_section(results.get("services", ""), 2000)}

---

## Careers / Culture
{extract_section(results.get("careers", ""), 2000)}

---

## Interview Prep Notes
- Key themes from website: [TO BE FILLED]
- Company values: [TO BE FILLED]
- Recent news: [TO BE FILLED]
- Questions to ask: [TO BE FILLED]

---

## Strategic Fit with Ahmed's Profile
- Alignment: [TO BE FILLED]
- Gaps: [TO BE FILLED]
- Talking points: [TO BE FILLED]
"""
    
    # Save dossier
    os.makedirs(DOSSIER_DIR, exist_ok=True)
    filepath = f"{DOSSIER_DIR}/{slug}-company-dossier.md"
    Path(filepath).write_text(dossier)
    log(f"Dossier saved: {filepath}")
    
    # Print summary
    sections_found = sum(1 for v in results.values() if v and len(v) > 200)
    log(f"Done: {sections_found}/5 sections extracted")
    
    return filepath


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: auto-dossier.py <domain> [company_name] [role_title]")
        print("Example: auto-dossier.py contango.ae Contango 'DT Consultant'")
        sys.exit(1)
    
    domain = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else None
    role = sys.argv[3] if len(sys.argv) > 3 else None
    
    build_dossier(domain, name, role)
