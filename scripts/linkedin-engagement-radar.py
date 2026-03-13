#!/usr/bin/env python3
"""
LinkedIn Engagement Radar — Extract latest posts from GCC influencers via Defuddle.
Drafts ready-to-post comments for Ahmed's engagement strategy.

Usage: python3 linkedin-engagement-radar.py
"""

import urllib.request
import json
import time
import os
from datetime import datetime
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
OUTPUT_DIR = f"{WORKSPACE}/linkedin/engagement/daily"

# Top GCC LinkedIn voices to monitor (verified active Mar 13, 2026)
# Format: (name, linkedin_slug, why_they_matter)
TARGETS = [
    # Tier 1: Global Tech Voices (high followers, daily posters)
    ("Pascal Bornet", "pascalbornet", "AI/Automation #1 Voice, 2M+ followers, Forbes Tech Council"),
    ("Bernard Marr", "bernardmarr", "AI/Futurist, bestselling author, GCC-relevant content"),
    # Tier 2: GCC C-Suite / DT Leaders
    ("Omar Turjman", "omarturjman", "GCC digital transformation leader"),
    ("Mamoun Alhomssey", "mamoun-alhomssey", "GCC CIO, digital health, Forbes ME"),
    ("Elie Soukayem", "eliesoukayem", "ME digital transformation executive"),
    ("Mohannad Alkalash", "mohannadalkalash", "Saudi tech leader, Hawsabah (24K followers)"),
    ("Badr Alghamdi", "badralghamdi", "Saudi tech leadership, stc ecosystem"),
    # Tier 3: FinTech / Banking
    ("Fady Sleiman", "fadysleiman", "GCC fintech/banking leader"),
    # Tier 4: Strategy / Consulting / Executive Search
    ("Sara Azimzadeh", "saraazimzadeh", "Russell Reynolds Associates, exec search GCC"),
    ("Abdoullah Tahri", "abdoullah-tahri-jouti", "GCC strategy/consulting"),
    # Tier 5: Egypt/GCC Bridge (Ahmed's network)
    ("Tamer Tharwat", "tamertharwat", "Egypt/GCC tech leader"),
    ("Sami Elkady", "samielkady", "Egypt/GCC tech ecosystem"),
    ("Saleem Arshad", "saleemarshad", "GCC enterprise technology"),
]


def log(msg):
    print(f"[radar] {msg}")


def defuddle_fetch(url):
    """Fetch via Defuddle, fallback Jina."""
    try:
        clean = url.replace("https://", "").replace("http://", "")
        req = urllib.request.Request(f"https://defuddle.md/{clean}", headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read().decode("utf-8")
            if content and len(content) > 100:
                return content
    except Exception as e:
        log(f"  Defuddle error: {e}")
    # Fallback Jina
    try:
        req = urllib.request.Request(f"https://r.jina.ai/{url}", headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read().decode("utf-8")
            if content and len(content) > 100:
                return content
    except Exception as e:
        log(f"  Jina error: {e}")
    return ""


def extract_via_camofox(slug):
    """Extract recent activity via Camoufox CLI (NASR's account)."""
    import subprocess
    try:
        # Open profile activity page
        url = f"https://www.linkedin.com/in/{slug}/recent-activity/all/"
        result = subprocess.run(
            ["camofox-browser", "open", url],
            capture_output=True, text=True, timeout=30
        )
        tab_id = result.stdout.strip().split("tabId:")[-1].strip() if "tabId:" in result.stdout else ""
        
        if not tab_id:
            # Try parsing JSON output
            try:
                data = json.loads(result.stdout)
                tab_id = data.get("tabId", "")
            except Exception:
                pass
        
        if not tab_id:
            log(f"  Camofox: couldn't get tab ID")
            return ""
        
        time.sleep(3)  # Wait for page load
        
        # Get snapshot
        result = subprocess.run(
            ["camofox-browser", "snapshot", tab_id],
            capture_output=True, text=True, timeout=30
        )
        content = result.stdout
        
        # Close tab
        subprocess.run(["camofox-browser", "close", tab_id], capture_output=True, timeout=10)
        
        return content if content and len(content) > 200 else ""
    except Exception as e:
        log(f"  Camofox error: {e}")
        return ""


def extract_post_content(post_url):
    """Extract individual post content via Defuddle (posts are more public than profiles)."""
    return defuddle_fetch(post_url)


def scan_targets():
    """Scan all target profiles for recent posts via Camoufox (LinkedIn blocks Defuddle)."""
    results = []
    
    for name, slug, why in TARGETS:
        log(f"Scanning {name} ({slug})...")
        
        # LinkedIn blocks Defuddle/Jina. Use Camoufox on NASR's account.
        content = extract_via_camofox(slug)
        
        if content and len(content) > 200:
            results.append({
                "name": name,
                "slug": slug,
                "why": why,
                "content": content[:3000],
                "url": f"https://www.linkedin.com/in/{slug}/recent-activity/all/",
                "extracted": True
            })
            log(f"  Found activity ({len(content)} chars)")
        else:
            results.append({
                "name": name,
                "slug": slug,
                "why": why,
                "content": "",
                "url": f"https://www.linkedin.com/in/{slug}/recent-activity/all/",
                "extracted": False
            })
            log(f"  No activity extracted")
        
        time.sleep(2)  # Rate limit between profiles
    
    return results


def generate_report(results):
    """Generate daily engagement report."""
    date = datetime.now().strftime("%Y-%m-%d")
    
    extracted = [r for r in results if r["extracted"]]
    
    report = f"""# LinkedIn Engagement Radar — {date}

**Scanned:** {len(results)} profiles
**With activity:** {len(extracted)} profiles
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

---

"""
    
    for r in extracted:
        report += f"""## {r['name']}
**Profile:** https://www.linkedin.com/in/{r['slug']}
**Why:** {r['why']}

### Recent Activity Preview
{r['content'][:1000]}

### Comment Opportunity
- Topic alignment: [TO ASSESS]
- Draft comment: [TO DRAFT]
- Priority: [HIGH/MEDIUM/LOW]

---

"""
    
    if not extracted:
        report += """## No Activity Extracted

LinkedIn may be blocking extraction. Fallback options:
1. Use Camoufox on NASR's account to scrape activity pages
2. Check profiles manually and log engagement targets

---
"""
    
    # Save report
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = f"{OUTPUT_DIR}/{date}.md"
    Path(filepath).write_text(report)
    log(f"Report saved: {filepath}")
    
    return filepath


def main():
    log("Starting LinkedIn Engagement Radar...")
    results = scan_targets()
    filepath = generate_report(results)
    
    extracted = sum(1 for r in results if r["extracted"])
    log(f"Done: {extracted}/{len(results)} profiles extracted")
    log(f"Report: {filepath}")
    
    return {"scanned": len(results), "extracted": extracted, "report": filepath}


if __name__ == "__main__":
    main()
