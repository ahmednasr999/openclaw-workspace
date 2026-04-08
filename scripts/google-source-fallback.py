#!/usr/bin/env python3
"""
google-source-fallback.py — Web Aggregator via COMPOSIO_SEARCH_WEB (free, no Exa credits).
Replaces Exa-powered jobs-source-google.py when Exa credits are exhausted.

Same three-phase search strategy, but uses COMPOSIO_SEARCH_WEB which has no credit limits.
Output: data/jobs-raw/google-jobs.json (compatible with existing merge pipeline)
"""

import hashlib
import json
import re
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from _imports import agent_common, jobs_source_common

AgentResult = agent_common.AgentResult
agent_main = agent_common.agent_main
is_dry_run = agent_common.is_dry_run
load_json = agent_common.load_json
WORKSPACE = agent_common.WORKSPACE
DATA_DIR = agent_common.DATA_DIR
JOBS_RAW_DIR = agent_common.JOBS_RAW_DIR
COMPOSIO_MCP_URL = "https://connect.composio.dev/mcp"
RATE_LIMIT_DELAY = 1.5
RECENCY_DAYS = 14
ALL_TITLES = jobs_source_common.ALL_TITLES
PRIORITY_COUNTRIES = jobs_source_common.PRIORITY_COUNTRIES
DISCOVERY_BOARDS = jobs_source_common.DISCOVERY_BOARDS
AGENT_NAME = "google-source-fallback"
OUTPUT_FILE = JOBS_RAW_DIR / "google-jobs.json"

try:
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

def load_composio_key():
    """Load Composio consumer key from secrets.json."""
    secrets = Path("/root/.openclaw/config/secrets.json")
    if secrets.exists():
        cfg = json.loads(secrets.read_text())
        return cfg.get("composio_consumer_key", "")
    return ""

def mcp_call(method, params, timeout=45):
    """Make an MCP call to Composio."""
    import requests
    consumer_key = load_composio_key()
    if not consumer_key:
        print("  No consumer key found")
        return None
    headers = {"Content-Type": "application/json", "x-consumer-api-key": consumer_key}
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    try:
        resp = requests.post(COMPOSIO_MCP_URL, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json().get("result")
    except Exception as e:
        print(f"  MCP call error: {e}")
    return None

def mcp_initialize():
    result = mcp_call("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "google-source-fallback", "version": "1.0"},
    })
    return result is not None

def web_search(query):
    """Search via COMPOSIO_SEARCH_WEB. Returns list of citation dicts."""
    result = mcp_call("tools/call", {
        "name": "COMPOSIO_MULTI_EXECUTE_TOOL",
        "arguments": {
            "tools": [{
                "tool_slug": "COMPOSIO_SEARCH_WEB",
                "arguments": {"query": query},
            }],
            "sync_response_to_workbench": False,
        },
    }, timeout=45)
    if not result:
        return []
    try:
        content = result.get("content", [])
        if not content:
            return []
        text = content[0].get("text", "")
        if not text:
            return []
        outer = json.loads(text)
        if not outer.get("successful"):
            return []
        results_list = outer.get("data", {}).get("results", [])
        if not results_list:
            return []
        inner = results_list[0].get("response", {})
        if not inner.get("successful"):
            return []
        data = inner.get("data", {})
        return data.get("citations", [])
    except Exception as e:
        print(f"    Search parse error: {e}")
    return []

def extract_job_from_citation(citation):
    """Convert a COMPOSIO_SEARCH_WEB citation into a job dict."""
    url = citation.get("url", "")
    raw_title = citation.get("title", "")
    snippet = citation.get("snippet", "") or citation.get("text", "")
    if not url or not raw_title:
        return None
    # Determine board
    board = "web"
    for b in DISCOVERY_BOARDS:
        if b.replace("https://", "").split("/")[0] in url.lower():
            board = b.split("//")[-1].split("/")[0]
            break
    # Extract company from title or domain
    company = "Confidential"
    company_match = re.search(r'\s+at\s+(.+?)(?:\s*[\|–\-]|$)', raw_title, re.IGNORECASE)
    if company_match:
        company = company_match.group(1).strip()
        title = re.sub(r'\s+at\s+' + re.escape(company) + r'.*$', '', raw_title, flags=re.IGNORECASE).strip()
    else:
        domain_match = re.match(r'https?://(?:www\.)?([^/]+)', url)
        if domain_match:
            domain = domain_match.group(1)
            if domain not in [b.replace("https://", "").split("/")[0] for b in DISCOVERY_BOARDS]:
                company = domain.split(".")[0].title()
        title = re.sub(r'\s*[\|–-].*$', '', raw_title).strip()
    # Location from snippet
    location_match = re.search(r'(Dubai|Abu Dhabi|Riyadh|Doha|Muscat|Manama|Kuwait|Jeddah|Cairo|Gulf|UAE|Saudi|Qatar|Bahrain|Oman|GCC)(?:\s*,\s*(\w+))?', snippet, re.IGNORECASE)
    location = location_match.group(0) if location_match else ""
    if not location:
        location_match = re.search(r'(Dubai|Abu Dhabi|Riyadh|Doha|Muscat|Manama|Kuwt|Jeddah|Cairo)', snippet, re.IGNORECASE)
        if location_match:
            location = location_match.group(0)
    return {
        "title": title if len(title) > 5 else raw_title,
        "company": company,
        "location": location,
        "url": url,
        "snippet": snippet[:500] if snippet else "",
        "board": board,
    }

def run_google_fallback(result: AgentResult):
    """Main scanner using COMPOSIO_SEARCH_WEB."""
    consumer_key = load_composio_key()
    if not consumer_key:
        result.set_error("No Composio consumer key found in secrets.json")
        return
    if not mcp_initialize():
        result.set_error("Failed to initialize MCP session")
        return
    print("  MCP session initialized")
    if is_dry_run():
        queries_count = len(ALL_TITLES) * 3 + len(DISCOVERY_BOARDS[:5]) * len(ALL_TITLES[:2]) + 2
        print(f"  DRY RUN: {queries_count} queries planned")
        result.set_data([])
        result.set_kpi({"queries_planned": queries_count})
        return

    all_results = []
    seen_urls = set()
    errors = 0
    searches_run = 0

    # Phase 1: Keyword searches across priority countries
    print("\n=== Phase 1: Title + Country keyword search ===")
    top_countries = PRIORITY_COUNTRIES[:3]
    for title in ALL_TITLES:
        for country in top_countries:
            searches_run += 1
            query = f"{title} job {country} 2026"
            citations = web_search(query)
            if not citations:
                errors += 1
            else:
                for c in citations:
                    url = c.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        job = extract_job_from_citation(c)
                        if job:
                            all_results.append(job)
            if searches_run % 10 == 0:
                print(f"  Progress: {searches_run} queries | jobs: {len(all_results)} (errs: {errors})")
            time.sleep(RATE_LIMIT_DELAY)
    print(f"  Phase 1 done: {len(all_results)} jobs from {searches_run} queries")

    # Phase 2: Board-specific searches
    print(f"\n=== Phase 2: Board-specific search ===")
    target_boards = DISCOVERY_BOARDS[:5]
    for board in target_boards:
        board_name = board.replace("https://", "").split("/")[0].replace("www.", "")
        for title in ALL_TITLES[:3]:
            searches_run += 1
            query = f"{title} {board_name} 2026"
            citations = web_search(query)
            if citations:
                for c in citations:
                    url = c.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        job = extract_job_from_citation(c)
                        if job:
                            all_results.append(job)
            else:
                errors += 1
            time.sleep(RATE_LIMIT_DELAY)
    print(f"  Phase 2 done: +{len(all_results)} jobs total, {errors} errors")

    # Phase 3: Neural catch-all
    print(f"\n=== Phase 3: Catch-all search ===")
    catch_queries = [
        "executive technology leadership role hiring Dubai Riyadh 2026",
        "digital transformation director VP Abu Dhabi Doha 2026",
        "CIO CTO CDO senior role opening Gulf region",
    ]
    for q in catch_queries:
        searches_run += 1
        citations = web_search(q)
        if citations:
            for c in citations:
                url = c.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    job = extract_job_from_citation(c)
                    if job:
                        all_results.append(job)
        else:
            errors += 1
        time.sleep(RATE_LIMIT_DELAY)

    print(f"\n=== Final: {len(all_results)} unique results from {searches_run} queries ({errors} errors) ===")

    # DB write
    if _pdb and all_results:
        try:
            db_count = 0
            for j in all_results:
                _pdb.register_job(
                    source="google",
                    company=j.get("company", "Unknown"),
                    title=j.get("title", "Unknown"),
                    location=j.get("location"),
                    url=j.get("url"),
                    jd_text=j.get("snippet", None),
                )
                db_count += 1
            print(f"  DB: {db_count} jobs registered")
            _pdb.log_source_run(
                source="google",
                raw_count=searches_run,
                unique_count=len(all_results),
                db_registered=db_count,
                countries_json="{}",
                titles_json="{}",
                duration_ms=0,
                errors=errors,
            )
        except Exception as e:
            print(f"  DB write skipped (non-fatal): {e}")

    result.set_data(all_results)
    result.set_kpi({
        "searches_run": searches_run,
        "unique_results": len(all_results),
        "errors": errors,
        "strategy": "COMPOSIO_SEARCH_WEB (free, no Exa credits)",
    })

if __name__ == "__main__":
    JOBS_RAW_DIR.mkdir(parents=True, exist_ok=True)
    agent_main(AGENT_NAME, run_google_fallback, OUTPUT_FILE)
