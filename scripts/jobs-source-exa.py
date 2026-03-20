#!/usr/bin/env python3
"""
jobs-source-exa.py — Exa AI search source adapter for job scanner.

Uses Composio MCP endpoint to search via Exa AI.
Searches 22 titles x 6 GCC countries with priority ordering.
Rate limited at 1.5s between API calls.

Output: data/jobs-raw/exa.json
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add scripts dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from _imports import agent_common, jobs_source_common

# Import from agent_common
AgentResult = agent_common.AgentResult
agent_main = agent_common.agent_main
is_dry_run = agent_common.is_dry_run
load_json = agent_common.load_json
WORKSPACE = agent_common.WORKSPACE
DATA_DIR = agent_common.DATA_DIR
JOBS_RAW_DIR = agent_common.JOBS_RAW_DIR

# Import from jobs_source_common
ALL_TITLES = jobs_source_common.ALL_TITLES
GCC_COUNTRIES = jobs_source_common.GCC_COUNTRIES
PRIORITY_COUNTRIES = jobs_source_common.PRIORITY_COUNTRIES
SECONDARY_COUNTRIES = jobs_source_common.SECONDARY_COUNTRIES
COUNTRY_SEARCH_TERMS = jobs_source_common.COUNTRY_SEARCH_TERMS
is_relevant = jobs_source_common.is_relevant
standard_job_dict = jobs_source_common.standard_job_dict

# Configuration
AGENT_NAME = "jobs-source-exa"
OUTPUT_FILE = JOBS_RAW_DIR / "exa.json"
CONFIG_FILE = Path("/root/.openclaw/openclaw.json")
COMPOSIO_MCP_URL = "https://connect.composio.dev/mcp"
RATE_LIMIT_DELAY = 1.0  # seconds between API calls
RESULTS_PER_QUERY = 10
RECENCY_DAYS = 14


def load_composio_key() -> str:
    """Load Composio consumer key from openclaw.json."""
    try:
        config = load_json(CONFIG_FILE)
        key = config.get("plugins", {}).get("entries", {}).get("composio", {}).get("config", {}).get("consumerKey", "")
        if key:
            return key
    except Exception as e:
        print(f"  Warning: Could not load Composio key: {e}")
    return ""


def mcp_call(method: str, params: dict, consumer_key: str, timeout: int = 45) -> dict | None:
    """Make a JSON-RPC call to Composio MCP endpoint."""
    import requests

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "x-consumer-api-key": consumer_key,
    }

    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 1000000,
        "method": method,
        "params": params,
    }

    try:
        resp = requests.post(COMPOSIO_MCP_URL, json=payload, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            print(f"    MCP HTTP {resp.status_code}: {resp.text[:200]}")
            return None

        # Parse SSE response
        for line in resp.text.split("\n"):
            if line.startswith("data:"):
                data = json.loads(line[5:].strip())
                if "error" in data:
                    print(f"    MCP error: {data['error']}")
                    return None
                return data.get("result", {})

        return None
    except Exception as e:
        print(f"    MCP error: {e}")
        return None


def mcp_initialize(consumer_key: str) -> bool:
    """Initialize MCP session."""
    result = mcp_call("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "jobs-source-exa", "version": "1.0"},
    }, consumer_key)
    return result is not None


def exa_search(query: str, consumer_key: str, num_results: int = 10, start_date: str = None) -> list[dict]:
    """Search via EXA_SEARCH through Composio MCP. Returns list of result dicts."""
    args = {
        "query": query,
        "type": "neural",
        "numResults": num_results,
    }
    if start_date:
        args["startPublishedDate"] = start_date

    result = mcp_call("tools/call", {
        "name": "COMPOSIO_MULTI_EXECUTE_TOOL",
        "arguments": {
            "tools": [{
                "tool_slug": "EXA_SEARCH",
                "arguments": args,
            }],
            "sync_response_to_workbench": False,
        },
    }, consumer_key, timeout=45)

    if not result:
        return []

    # Parse the nested response
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
        return inner.get("data", {}).get("results", [])
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"    Parse error: {e}")
        return []


def extract_job_from_result(result: dict, search_title: str, search_country: str) -> dict | None:
    """Convert an Exa search result into a job dict."""
    import re

    url = result.get("url", "")
    if not url:
        return None

    raw_title = result.get("title", "")

    # Clean title: remove site names
    title = re.sub(
        r'\s*[\|–-]\s*(LinkedIn|Indeed|GulfTalent|Glassdoor|Bayt|NaukriGulf|Michael Page|Hays|Robert Half).*$',
        '', raw_title, flags=re.IGNORECASE
    ).strip()

    # Extract company from title patterns like "Role at Company"
    company = "Confidential"
    company_match = re.search(r'\s+at\s+(.+?)(?:\s*[\|–-]|$)', raw_title, re.IGNORECASE)
    if company_match:
        company = company_match.group(1).strip()
        title = re.sub(r'\s+at\s+' + re.escape(company) + r'.*$', '', title, flags=re.IGNORECASE).strip()
    else:
        # Try domain-based extraction
        domain_match = re.match(r'https?://(?:www\.)?([^/]+)', url)
        if domain_match:
            domain = domain_match.group(1)
            job_boards = ["linkedin.com", "indeed.com", "glassdoor.com", "bayt.com",
                         "naukrigulf.com", "gulftalent.com", "michaelpage.ae"]
            if not any(jb in domain for jb in job_boards):
                company = domain.replace("careers.", "").replace("jobs.", "").split(".")[0].title()

    # Extract location
    location = search_country
    for country, terms in COUNTRY_SEARCH_TERMS.items():
        for term in terms:
            if term.lower() in raw_title.lower() or term.lower() in url.lower():
                location = country
                break

    # Generate stable ID
    job_id = str(abs(hash(url)))[:10]
    posted = result.get("publishedDate", "")[:10] if result.get("publishedDate") else ""

    return standard_job_dict(
        job_id=job_id,
        source="exa",
        title=title if title else search_title,
        company=company,
        location=location,
        url=url,
        posted=posted,
        raw_snippet=result.get("text", "")[:500] if result.get("text") else ""
    )


def run_exa_scanner(result: AgentResult):
    """Main scanner logic."""
    
    # Load Composio key
    consumer_key = load_composio_key()
    if not consumer_key:
        result.set_error("No Composio consumer key found")
        return
    
    if is_dry_run():
        print("\n=== DRY RUN: Search Matrix ===")
        total_searches = 0
        
        # Priority countries first
        print("\n--- Priority Countries (all titles) ---")
        for country in PRIORITY_COUNTRIES:
            for title in ALL_TITLES:
                print(f"  [{country}] {title}")
                total_searches += 1
        
        # Secondary countries
        print("\n--- Secondary Countries (all titles) ---")
        for country in SECONDARY_COUNTRIES:
            for title in ALL_TITLES:
                print(f"  [{country}] {title}")
                total_searches += 1
        
        print(f"\n--- Total: {total_searches} searches ---")
        print(f"Estimated time: {total_searches * RATE_LIMIT_DELAY / 60:.1f} minutes")
        
        result.set_data([])
        result.set_kpi({
            "searches_planned": total_searches,
            "priority_searches": len(PRIORITY_COUNTRIES) * len(ALL_TITLES),
            "secondary_searches": len(SECONDARY_COUNTRIES) * len(ALL_TITLES),
        })
        return
    
    # Initialize MCP
    print("Initializing Composio MCP...")
    if not mcp_initialize(consumer_key):
        result.set_error("Failed to initialize MCP session")
        return
    print("  MCP session initialized ✓")
    
    # Calculate start date for recency filter
    start_date = (datetime.now() - timedelta(days=RECENCY_DAYS)).strftime("%Y-%m-%d")
    
    # Build search plan - priority countries only (secondary too slow for Exa rate limits)
    # 3 countries x 22 titles = 66 searches (~2 min at 1.5s rate limit)
    # Add one broad GCC query per title to catch secondary countries
    searches = []
    for country in PRIORITY_COUNTRIES:
        for title in ALL_TITLES:
            searches.append((title, country))
    # Broad GCC catch-all for secondary countries
    for title in ALL_TITLES:
        searches.append((title, "GCC"))
    
    print(f"Search plan: {len(searches)} queries")
    
    # Track stats
    searches_run = 0
    jobs_found_raw = 0
    exec_filter_pass = 0
    domain_filter_pass = 0
    seen_urls = set()
    all_jobs = []
    errors = 0
    
    for title, country in searches:
        searches_run += 1
        
        # Build query
        location_term = COUNTRY_SEARCH_TERMS.get(country, {"GCC": "Gulf GCC Middle East"}.get(country, country))
        if isinstance(location_term, list):
            location_term = location_term[0]
        query = f"{title} {location_term} job opening hiring 2026"
        
        # Search
        results = exa_search(query, consumer_key, num_results=RESULTS_PER_QUERY, start_date=start_date)
        
        if not results:
            errors += 1
            time.sleep(0.5)
            continue
        
        jobs_found_raw += len(results)
        
        for r in results:
            job = extract_job_from_result(r, title, country)
            if not job:
                continue
            
            # Dedup by URL
            if job["url"] in seen_urls:
                continue
            seen_urls.add(job["url"])
            
            # Track filter stats
            if job.get("seniority") and job["seniority"] != "Other":
                exec_filter_pass += 1
            if job.get("domain_match"):
                domain_filter_pass += 1
            
            # Only keep relevant jobs
            if job.get("relevant", False):
                all_jobs.append(job)
        
        # Progress
        if searches_run % 20 == 0:
            print(f"  Progress: {searches_run}/{len(searches)} | found {jobs_found_raw} | kept {len(all_jobs)}")
        
        # Rate limit
        time.sleep(RATE_LIMIT_DELAY)
    
    print(f"\nCompleted: {searches_run} searches, {jobs_found_raw} raw, {len(all_jobs)} kept")
    
    result.set_data(all_jobs)
    result.set_kpi({
        "searches_run": searches_run,
        "results_per_search": round(jobs_found_raw / max(1, searches_run), 2),
        "unique_jobs": len(all_jobs),
        "exec_filter_pass": exec_filter_pass,
        "domain_filter_pass": domain_filter_pass,
        "errors": errors,
    })


def main():
    """Entry point."""
    JOBS_RAW_DIR.mkdir(parents=True, exist_ok=True)
    agent_main(
        agent_name=AGENT_NAME,
        run_func=run_exa_scanner,
        output_path=OUTPUT_FILE,
        ttl_hours=6,
        version="1.0.0"
    )


if __name__ == "__main__":
    main()
