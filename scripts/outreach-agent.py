#!/usr/bin/env python3
"""
Outreach Agent v1 - Suggests LinkedIn connections tied to applied companies.
Pulls recent "Applied" entries from Notion Pipeline, finds recruiters/HR/hiring
managers at those companies via Tavily, outputs 3-5 profiles daily.

Output: data/outreach-suggestions.json
"""
import json, re, ssl, os, time, hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
CONFIG_DIR = WORKSPACE / "config"
OUTPUT = DATA_DIR / "outreach-suggestions.json"
HISTORY_FILE = DATA_DIR / "outreach-history.json"

# Notion config
NOTION_TOKEN = "NOTION_TOKEN_REDACTED"
PIPELINE_DB = "3268d599-a162-81b4-b768-f162adfa4971"
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# Tavily
TAVILY_KEY = None
try:
    TAVILY_KEY = json.load(open(CONFIG_DIR / "tavily.json")).get("api_key")
except:
    pass

# Roles to search for at target companies
SEARCH_ROLES = [
    "recruiter OR talent acquisition OR HR",
    "hiring manager OR head of OR director",
    "CTO OR CIO OR VP technology OR VP engineering",
]


def retry_request(req_fn, max_retries=3, name="request"):
    """Retry a request with backoff. Returns result or raises on exhaustion."""
    for attempt in range(1, max_retries + 1):
        try:
            return req_fn()
        except Exception as e:
            err_str = str(e)
            # Classify failure
            if any(k in err_str.lower() for k in ["401", "403", "unauthorized", "forbidden", "invalid token"]):
                print(f"  CONFIG ERROR in {name}: {e} (not retryable)")
                raise
            if any(k in err_str.lower() for k in ["keyerror", "typeerror", "valueerror"]):
                print(f"  LOGIC ERROR in {name}: {e} (not retryable)")
                raise
            # Transient - retry
            if attempt < max_retries:
                wait = attempt * 15
                print(f"  TRANSIENT ERROR in {name} (attempt {attempt}/{max_retries}): {e} - retrying in {wait}s")
                time.sleep(wait)
            else:
                print(f"  TRANSIENT ERROR in {name} exhausted {max_retries} retries: {e}")
                raise


def notion_query_applied():
    """Get recently applied companies from Notion Pipeline."""
    payload = json.dumps({
        "filter": {
            "property": "Stage",
            "select": {"equals": "\u2705 Applied"}
        },
        "sorts": [
            {"property": "Applied Date", "direction": "descending"}
        ],
        "page_size": 20,
    }).encode()

    req = Request(
        f"https://api.notion.com/v1/databases/{PIPELINE_DB}/query",
        data=payload,
        headers=NOTION_HEADERS,
        method="POST",
    )

    ctx = ssl.create_default_context()
    try:
        def _notion_fetch():
            with urlopen(req, timeout=30, context=ctx) as r:
                return json.loads(r.read().decode("utf-8", errors="ignore"))
        data = retry_request(_notion_fetch, max_retries=3, name="notion_applied")

        companies = []
        for page in data.get("results", []):
            props = page.get("properties", {})

            # Extract company name
            company_title = props.get("Company", {}).get("title", [])
            company = company_title[0]["plain_text"] if company_title else ""

            # Extract job title
            role_rt = props.get("Role", {}).get("rich_text", [])
            role = role_rt[0]["plain_text"] if role_rt else ""

            # Applied date
            applied = props.get("Applied Date", {}).get("date", {})
            applied_date = applied.get("start", "") if applied else ""

            if company:
                companies.append({
                    "company": company,
                    "role": role,
                    "applied_date": applied_date,
                    "page_id": page["id"],
                })

        return companies
    except Exception as e:
        print(f"  Notion error: {e}")
        return []


def search_profiles(company, role_query="recruiter OR HR OR talent acquisition"):
    """Search Tavily for LinkedIn profiles at a company."""
    if not TAVILY_KEY:
        return []

    query = f'site:linkedin.com/in/ "{company}" ({role_query})'
    payload = json.dumps({
        "api_key": TAVILY_KEY,
        "query": query,
        "max_results": 5,
        "search_depth": "basic",
        "include_domains": ["linkedin.com"],
    }).encode()

    ctx = ssl.create_default_context()
    req = Request("https://api.tavily.com/search", data=payload,
                  headers={"Content-Type": "application/json"})

    try:
        def _tavily_fetch():
            with urlopen(req, timeout=30, context=ctx) as r:
                return json.loads(r.read().decode("utf-8", errors="ignore"))
        data = retry_request(_tavily_fetch, max_retries=3, name=f"tavily_{company}")

        profiles = []
        seen = set()
        for r in data.get("results", []):
            url = r.get("url", "")
            if "/in/" not in url:
                continue

            # Normalize URL: country subdomain -> www
            clean = url.split("?")[0].rstrip("/")
            clean = re.sub(r'https?://\w+\.linkedin\.com', 'https://www.linkedin.com', clean)

            if clean in seen:
                continue
            seen.add(clean)

            title = r.get("title", "")

            # Extract person name and role from title
            # Pattern: "Name - Role at Company" or "Name - Company"
            name = title.split(" - ")[0].strip() if " - " in title else title.split("|")[0].strip()
            name = re.sub(r'\s*\|.*$', '', name)
            name = re.sub(r'\s*LinkedIn.*$', '', name, flags=re.IGNORECASE)
            name = name.strip()

            # Extract their role
            person_role = ""
            m = re.search(r' - (.+?)(?:\s*[-|@]\s*|\s+at\s+)', title)
            if m:
                person_role = m.group(1).strip()
            elif " - " in title:
                parts = title.split(" - ")
                if len(parts) >= 2:
                    person_role = parts[1].strip()[:60]

            # Signal-based scoring (Outbound Strategist pattern)
            signal_score = 0
            role_lower = person_role.lower()
            title_lower = title.lower()
            
            # Tier 1: Direct hiring signals (highest value)
            if any(w in role_lower or w in title_lower for w in ["talent acquisition", "recruiter", "recruiting", "hiring"]):
                signal_score += 30
            # Tier 2: HR leadership
            elif any(w in role_lower or w in title_lower for w in ["hr director", "head of hr", "chief people", "chro", "vp people", "vp hr"]):
                signal_score += 25
            # Tier 3: Hiring manager (executive at target company)
            elif any(w in role_lower or w in title_lower for w in ["cto", "cio", "vp", "director", "head of", "chief"]):
                signal_score += 20
            # Tier 4: General HR
            elif any(w in role_lower or w in title_lower for w in ["human resources", "hr ", "people operations"]):
                signal_score += 15
            else:
                signal_score += 5
            
            profiles.append({
                "name": name[:50],
                "role": person_role[:80],
                "url": clean,
                "company": company,
                "signal_score": signal_score,
            })

        return profiles
    except Exception as e:
        print(f"  Search error for {company}: {e}")
        return []


def load_history():
    """Load previously suggested profiles to avoid repeats."""
    if HISTORY_FILE.exists():
        try:
            return json.load(open(HISTORY_FILE))
        except:
            pass
    return {"suggested": []}


def save_history(history):
    """Save suggestion history."""
    # Keep only last 90 days
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    history["suggested"] = [
        s for s in history["suggested"]
        if s.get("date", "") > cutoff
    ]
    json.dump(history, open(HISTORY_FILE, "w"), indent=2)


def run_outreach():
    """Main outreach agent."""
    print("=== Outreach Agent v1 ===")
    print(f"Time: {datetime.now(timezone(timedelta(hours=2))).strftime('%Y-%m-%d %H:%M')}")

    # Load history
    history = load_history()
    seen_urls = set(s.get("url", "") for s in history.get("suggested", []))
    print(f"  Previously suggested: {len(seen_urls)} profiles")

    # Get applied companies from Notion
    companies = notion_query_applied()
    print(f"  Applied companies: {len(companies)}")

    if not companies:
        print("  No applied companies found!")
        output = {
            "generated": datetime.now(timezone.utc).isoformat(),
            "suggestions": [],
            "status": "no_companies",
        }
        json.dump(output, open(OUTPUT, "w"), indent=2)
        return

    # Search for profiles at each company (most recent first)
    all_suggestions = []

    for comp in companies[:10]:  # Top 10 most recent
        company_name = comp["company"]
        print(f"\n  Searching: {company_name}...")

        # Search with different role queries
        profiles = []
        for role_q in SEARCH_ROLES[:2]:  # Use first 2 role queries
            found = search_profiles(company_name, role_q)
            profiles.extend(found)
            time.sleep(1)

        # Deduplicate
        seen_in_batch = set()
        unique_profiles = []
        for p in profiles:
            if p["url"] not in seen_in_batch and p["url"] not in seen_urls:
                seen_in_batch.add(p["url"])
                unique_profiles.append(p)

        if unique_profiles:
            # Rank by signal score, pick top 1-2 per company
            unique_profiles.sort(key=lambda x: x.get("signal_score", 0), reverse=True)
            for p in unique_profiles[:2]:
                p["applied_role"] = comp["role"]
                p["applied_date"] = comp["applied_date"]
                p["reason"] = f"You applied for {comp['role']} at {company_name}"
                all_suggestions.append(p)
                print(f"    + {p['name'][:25]:25s} | {p['role'][:30]:30s} | {p['url']}")
        else:
            print(f"    No new profiles found")

        # Stop once we have enough
        if len(all_suggestions) >= 5:
            break

    # Take top 5
    suggestions = all_suggestions[:5]

    # Update history
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for s in suggestions:
        history["suggested"].append({
            "url": s["url"],
            "name": s["name"],
            "company": s["company"],
            "date": today,
        })
    save_history(history)

    output = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "suggestions": suggestions,
        "companies_searched": len(companies[:10]),
        "status": "ok",
    }

    json.dump(output, open(OUTPUT, "w"), indent=2)
    print(f"\n=== Done: {len(suggestions)} connection suggestions saved ===")


if __name__ == "__main__":
    run_outreach()
