#!/usr/bin/env python3
"""
Firehose.com (by Ahrefs) - Real-time web monitoring integration.
Streams matching web pages via SSE and processes them for NASR workflows.

Usage:
    python3 firehose-monitor.py --setup          # Create taps and rules
    python3 firehose-monitor.py --stream         # Stream and process events
    python3 firehose-monitor.py --stream --since 1h  # Replay last hour
    python3 firehose-monitor.py --check          # Check recent matches (quick)
"""

import json
import os
import sys
import urllib.request
import urllib.error
import time
from datetime import datetime, timezone, timedelta

# === Configuration ===
WORKSPACE = "/root/.openclaw/workspace"
API_BASE = "https://api.firehose.com"
CONFIG_FILE = f"{WORKSPACE}/config/firehose.json"
CACHE_DIR = f"{WORKSPACE}/jobs-bank/firehose"
RESULTS_FILE = f"{CACHE_DIR}/latest-matches.json"

# Load API key
def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    # Fallback to env
    key = os.environ.get("FIREHOSE_API_KEY", "")
    if key:
        return {"management_key": key}
    print("ERROR: No firehose config found. Run --setup first or set FIREHOSE_API_KEY")
    sys.exit(1)


def api_call(method, endpoint, token, body=None):
    """Make API call to Firehose."""
    url = f"{API_BASE}{endpoint}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 204:
                return {}
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"API Error {e.code}: {body[:200]}")
        return None
    except Exception as e:
        print(f"API Error: {e}")
        return None


# === NASR-specific rules ===
NASR_RULES = [
    # Job postings - executive level
    {
        "value": 'page_type:"/Job Posting" AND ("CTO" OR "VP" OR "Director" OR "Head of" OR "Chief") AND ("digital transformation" OR "PMO" OR "IT" OR "technology")',
        "tag": "job-postings-executive"
    },
    # Job postings - Gulf region
    {
        "value": 'page_type:"/Job Posting" AND ("Dubai" OR "Abu Dhabi" OR "Saudi" OR "Riyadh" OR "Jeddah" OR "Qatar" OR "Bahrain" OR "Kuwait")',
        "tag": "job-postings-gulf"
    },
    # Industry trends for LinkedIn content
    {
        "value": '("digital transformation" OR "AI automation" OR "PMO") AND page_category:"/News" AND language:"en"',
        "tag": "industry-trends"
    },
    # Company tracking (applied companies)
    {
        "value": 'domain:qnb.com OR domain:dubaiholding.com OR domain:publicissapient.com',
        "tag": "company-tracking"
    },
    # AI & tech leadership trends
    {
        "value": '("AI leadership" OR "digital strategy" OR "technology executive") AND page_category:"/News" AND language:"en"',
        "tag": "tech-leadership"
    },
]


def setup_tap(config):
    """Create a tap and rules for NASR monitoring."""
    mgmt_key = config["management_key"]
    
    # Check existing taps
    existing = api_call("GET", "/v1/taps", mgmt_key)
    if existing and existing.get("data"):
        for tap in existing["data"]:
            if tap["name"] == "NASR Intelligence":
                print(f"Tap already exists: {tap['id']}")
                config["tap_token"] = tap["token"]
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(config, f, indent=2)
                return tap["token"]
    
    # Create new tap
    result = api_call("POST", "/v1/taps", mgmt_key, {"name": "NASR Intelligence"})
    if not result:
        print("Failed to create tap")
        return None
    
    tap_token = result.get("token")
    config["tap_token"] = tap_token
    config["tap_id"] = result.get("data", {}).get("id")
    
    # Save config
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Tap created: NASR Intelligence")
    print(f"Tap token: {tap_token[:10]}...")
    
    # Create rules
    for rule in NASR_RULES:
        result = api_call("POST", "/v1/rules", tap_token, rule)
        if result:
            print(f"  Rule created: {rule['tag']}")
        else:
            print(f"  Rule FAILED: {rule['tag']}")
        time.sleep(0.5)
    
    return tap_token


def stream_events(config, since="1h", limit=100):
    """Stream events from Firehose via SSE and collect matches."""
    tap_token = config.get("tap_token")
    if not tap_token:
        print("No tap token. Run --setup first.")
        return []
    
    url = f"{API_BASE}/v1/stream?timeout=30&since={since}&limit={limit}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {tap_token}")
    req.add_header("Accept", "text/event-stream")
    
    events = []
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            buffer = ""
            for line in resp:
                line = line.decode("utf-8", errors="replace")
                buffer += line
                
                if line.strip() == "" and buffer.strip():
                    # Parse SSE event
                    event_type = ""
                    event_data = ""
                    for part in buffer.split("\n"):
                        if part.startswith("event:"):
                            event_type = part[6:].strip()
                        elif part.startswith("data:"):
                            event_data = part[5:].strip()
                    
                    if event_type == "update" and event_data:
                        try:
                            doc = json.loads(event_data)
                            events.append(doc)
                        except json.JSONDecodeError:
                            pass
                    
                    buffer = ""
    except urllib.error.URLError as e:
        # Timeout is expected (stream ends)
        pass
    except Exception as e:
        print(f"Stream error: {e}")
    
    return events


def process_events(events):
    """Process and categorize events for NASR workflows."""
    jobs = []
    trends = []
    company_news = []
    
    for event in events:
        doc = event.get("document", {})
        tag = ""
        # Find the rule tag
        query_id = event.get("query_id", "")
        
        url = doc.get("url", "")
        title = doc.get("title", "")
        
        # Categorize by tag or content
        title_lower = title.lower()
        
        if any(k in title_lower for k in ["job", "career", "hiring", "position", "vacancy"]):
            jobs.append({
                "title": title,
                "url": url,
                "matched_at": event.get("matched_at", ""),
                "source": doc.get("domain", ""),
            })
        elif any(k in title_lower for k in ["news", "report", "announce", "launch", "fund"]):
            trends.append({
                "title": title,
                "url": url,
                "matched_at": event.get("matched_at", ""),
                "source": doc.get("domain", ""),
            })
        else:
            company_news.append({
                "title": title,
                "url": url,
                "matched_at": event.get("matched_at", ""),
                "source": doc.get("domain", ""),
            })
    
    return {"jobs": jobs, "trends": trends, "company_news": company_news}


def build_report(categorized):
    """Build a readable report from categorized events."""
    jobs = categorized["jobs"]
    trends = categorized["trends"]
    company_news = categorized["company_news"]
    
    total = len(jobs) + len(trends) + len(company_news)
    if total == 0:
        return "🔥 Firehose: No new matches in this period."
    
    report = f"🔥 Firehose Intelligence ({total} signals)\n\n"
    
    if jobs:
        report += f"💼 Job Postings ({len(jobs)}):\n"
        for j in jobs[:10]:
            report += f"  • {j['title'][:80]}\n    {j['url']}\n"
        report += "\n"
    
    if trends:
        report += f"📰 Industry Trends ({len(trends)}):\n"
        for t in trends[:5]:
            report += f"  • {t['title'][:80]}\n    {t['url']}\n"
        report += "\n"
    
    if company_news:
        report += f"🏢 Company Intel ({len(company_news)}):\n"
        for c in company_news[:5]:
            report += f"  • {c['title'][:80]}\n    {c['url']}\n"
    
    return report


def check_mode(config):
    """Quick check - stream last hour, report matches."""
    print("Streaming last hour from Firehose...")
    events = stream_events(config, since="1h", limit=100)
    
    if not events:
        print("No matches in the last hour.")
        return
    
    categorized = process_events(events)
    report = build_report(categorized)
    print(report)
    
    # Save to cache
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(RESULTS_FILE, 'w') as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "events": events,
            "categorized": categorized,
        }, f, indent=2)
    
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Firehose.com monitor for NASR")
    parser.add_argument("--setup", action="store_true", help="Create tap and rules")
    parser.add_argument("--stream", action="store_true", help="Stream events")
    parser.add_argument("--check", action="store_true", help="Quick check last hour")
    parser.add_argument("--since", default="1h", help="Replay window (e.g., 1h, 6h, 24h)")
    parser.add_argument("--limit", type=int, default=100, help="Max events")
    args = parser.parse_args()
    
    config = get_config()
    
    if args.setup:
        setup_tap(config)
    elif args.stream:
        events = stream_events(config, since=args.since, limit=args.limit)
        categorized = process_events(events)
        print(build_report(categorized))
    elif args.check:
        check_mode(config)
    else:
        parser.print_help()
