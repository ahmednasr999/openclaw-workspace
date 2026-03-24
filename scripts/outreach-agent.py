#!/usr/bin/env python3

# ==============================================================================
# AGENT BEHAVIOR STANDARD — Anthropic XML-Structured Format
# ==============================================================================
# Prompt structure for any future LLM calls:
#   <task>What to do</task>
#   <context>Background, Ahmed's profile, data available</context>
#   <constraints>Rules, what NOT to do, format requirements</constraints>
#   <output_format>Exact output structure expected</output_format>
# ==============================================================================
"""
Outreach Agent v1 - Suggests LinkedIn connections tied to applied companies.
Pulls recent "Applied" entries from Notion Pipeline, finds recruiters/HR/hiring
managers at those companies via Tavily, outputs 3-5 profiles daily.

Output: data/outreach-suggestions.json
"""
import os
import sys
import json, re, ssl, time, hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
CONFIG_DIR = WORKSPACE / "config"
OUTPUT = DATA_DIR / "outreach-suggestions.json"
HISTORY_FILE = DATA_DIR / "outreach-history.json"

# Notion config
NOTION_TOKEN = json.load(open(os.path.expanduser("~/.openclaw/workspace/config/notion.json")))["token"]
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


def retry_request(req_fn, max_retries=2, name="request"):
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
        data = retry_request(_notion_fetch, max_retries=2, name="notion_applied")

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
        data = retry_request(_tavily_fetch, max_retries=2, name=f"tavily_{company}")

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
            # Try "Name - Role at Company | LinkedIn" first
            m = re.search(r' - (.+?)\s+at\s+', title)
            if m:
                person_role = m.group(1).strip()
            else:
                # Try "Name - Role - Company | LinkedIn"
                parts = [p.strip() for p in title.split(" - ")]
                if len(parts) >= 3:
                    # Middle part is likely the role
                    person_role = parts[1][:60]
                elif len(parts) == 2:
                    # "Name - Company | LinkedIn" — role is unknown
                    candidate = re.sub(r'\s*\|.*$', '', parts[1]).strip()
                    # If it looks like a company name (matches our target), skip it
                    if candidate.lower() == company.lower():
                        person_role = ""
                    else:
                        person_role = candidate[:60]
            # Clean up trailing "| LinkedIn"
            person_role = re.sub(r'\s*\|.*$', '', person_role).strip()

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


def call_llm(prompt, max_tokens=1000, model="anthropic/claude-sonnet-4-6"):
    """Call LLM via OpenClaw gateway."""
    gateway_url = "http://127.0.0.1:18789/v1/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }).encode()
    ctx = ssl.create_default_context()
    gw_token = json.load(open(os.path.expanduser("~/.openclaw/openclaw.json")))["gateway"]["auth"]["token"]
    req = Request(gateway_url, data=payload,
                  headers={"Content-Type": "application/json",
                           "Authorization": f"Bearer {gw_token}"}, method="POST")
    try:
        with urlopen(req, timeout=30, context=ctx) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  LLM error: {e}")
        return ""


def draft_connection_messages(suggestions):
    """Draft personalized LinkedIn connection requests for each suggestion."""
    profiles = []
    for i, s in enumerate(suggestions, 1):
        profiles.append(
            f"PROFILE #{i}:\n"
            f"Name: {s.get('name', '?')}\n"
            f"Role: {s.get('role', 'Unknown')}\n"
            f"Company: {s.get('company', '?')}\n"
            f"Ahmed applied for: {s.get('applied_role', '?')} at {s.get('company', '?')}\n"
        )

    prompt = f"""<task>Draft a personalized LinkedIn connection request for each profile below. Ahmed Nasr is reaching out because he applied to a role at their company.</task>

<context>
Ahmed Nasr: 20+ years tech leadership across GCC. PMO excellence, digital transformation, AI automation. Currently seeking senior executive roles in UAE/Saudi.
These are recruiters, HR leaders, or hiring managers at companies Ahmed has applied to.
</context>

<constraints>
- MAX 280 characters per message (LinkedIn connection request limit)
- Open with something specific to their role or company, not "I saw your profile"
- Mention the role Ahmed applied for naturally, not desperately
- End with a soft ask: "Would love to connect" or "Happy to share more context"
- NEVER: "I'm a perfect fit", "I'd love to pick your brain", "Hope you don't mind me reaching out"
- Tone: Confident peer, not job seeker. Executive to executive.
- NEVER use em dashes. Use commas or hyphens instead.
</constraints>

<output_format>
Return ONLY a valid JSON array - no markdown fences:
[
  {{"profile_num": 1, "message": "connection request text here"}},
  {{"profile_num": 2, "message": "connection request text here"}}
]
</output_format>

{"".join(profiles)}"""

    response = call_llm(prompt, max_tokens=800)
    if not response:
        return suggestions

    try:
        clean = response.strip()
        if clean.startswith("```"):
            clean = re.sub(r"```\w*\n?", "", clean).strip()
        messages = json.loads(clean)
    except json.JSONDecodeError:
        m = re.search(r'\[.*\]', response, re.DOTALL)
        if m:
            try:
                messages = json.loads(m.group(0))
            except Exception:
                print("  Failed to parse connection messages")
                return suggestions
        else:
            return suggestions

    for msg in messages:
        idx = msg.get("profile_num", 0) - 1
        if 0 <= idx < len(suggestions) and msg.get("message"):
            suggestions[idx]["draft_message"] = msg["message"][:300]

    drafted = sum(1 for s in suggestions if s.get("draft_message"))
    print(f"  Drafted {drafted}/{len(suggestions)} connection messages")
    return suggestions


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

    # Draft personalized connection requests via Sonnet
    if suggestions:
        print("\n  Drafting connection messages...")
        suggestions = draft_connection_messages(suggestions)

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

    # ── DB write (dual-write, non-blocking) ──────────────────────────────────
    if _pdb and suggestions:
        try:
            for s in suggestions:
                company = s.get("company", "")
                if not company:
                    continue
                jobs = _pdb.get_by_company(company)
                job_db_id = jobs[0]["job_id"] if jobs else None
                if job_db_id:
                    _pdb.log_interaction(
                        job_id=job_db_id,
                        type="linkedin_message",
                        summary=f"Outreach suggested: {s.get('name', '?')} ({s.get('role', '?')}) at {company}",
                        from_name=s.get("name"),
                        channel="linkedin",
                        notes=s.get("message", "")[:300] if s.get("message") else None,
                    )
            print(f"  DB: logged {len(suggestions)} outreach interactions")
        except Exception as _e:
            print(f"  DB write failed (non-fatal): {_e}")
    # ─────────────────────────────────────────────────────────────────────────


def mark_status(url_or_name, status):
    """Mark a suggested profile as connected/messaged/response.
    Usage: python3 outreach-agent.py --mark connected "linkedin.com/in/john-doe"
    """
    history = load_history()
    updated = False
    search = url_or_name.lower().strip()
    
    for entry in history.get("suggested", []):
        entry_url = entry.get("url", "").lower()
        entry_name = entry.get("name", "").lower()
        if search in entry_url or search in entry_name:
            old_status = entry.get("status", "none")
            entry["status"] = status
            entry["status_date"] = datetime.now(timezone.utc).isoformat()
            updated = True
            print(f"Updated: {entry.get('name')} ({old_status} -> {status})")
    
    if updated:
        save_history(history)
    else:
        print(f"No match found for: {url_or_name}")
        print("Recent suggestions:")
        for entry in history.get("suggested", [])[-5:]:
            print(f"  {entry.get('name', '?')} - {entry.get('url', '?')}")


def report_stats():
    """Print outreach funnel stats."""
    history = load_history()
    suggested = history.get("suggested", [])
    
    total = len(suggested)
    by_status = {}
    for s in suggested:
        st = s.get("status", "none")
        by_status[st] = by_status.get(st, 0) + 1
    
    print(f"Outreach funnel (last 90 days):")
    print(f"  Suggested:  {total}")
    for st in ["connected", "messaged", "response", "none"]:
        if st in by_status:
            pct = by_status[st] / max(1, total) * 100
            print(f"  {st.title():12s}: {by_status[st]} ({pct:.0f}%)")


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    
    if "--mark" in args:
        idx = args.index("--mark")
        if idx + 2 < len(args):
            status = args[idx + 1]  # connected, messaged, response
            target = args[idx + 2]  # URL or name
            if status in ("connected", "messaged", "response", "rejected", "no_reply"):
                mark_status(target, status)
            else:
                print(f"Invalid status: {status}. Use: connected, messaged, response, rejected, no_reply")
        else:
            print("Usage: python3 outreach-agent.py --mark <status> <url_or_name>")
    elif "--stats" in args:
        report_stats()
    else:
        run_outreach()
