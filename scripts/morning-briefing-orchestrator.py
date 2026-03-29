#!/usr/bin/env python3
"""
Morning Briefing Orchestrator v2
=================================
Single deterministic script. Outputs: Notion page + Telegram message + Dashboard update.
No Google Docs. No LLM calls for data gathering. No split-brain with SKILL.md.

Usage:
    python3 morning-briefing-orchestrator.py
    python3 morning-briefing-orchestrator.py --dry-run
    python3 morning-briefing-orchestrator.py --date 2026-03-15
"""

import json, os, sys, re, subprocess, argparse, glob, traceback, time
import urllib.request, ssl
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ============================================================
# PATHS
# ============================================================
WORKSPACE = "/root/.openclaw/workspace"
JOBS_DIR = f"{WORKSPACE}/jobs-bank/scraped"
PIPELINE_FILE = f"{WORKSPACE}/jobs-bank/pipeline.md"
ACCOUNT_EMAIL = "ahmednasr999@gmail.com"
NOTION_CONFIG = f"{WORKSPACE}/config/notion.json"

cairo = timezone(timedelta(hours=2))

# Notion Pipeline DB (for live dedup)
PIPELINE_DB_ID = "3268d599-a162-81b4-b768-f162adfa4971"


def log(msg):
    ts = datetime.now(cairo).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_notion_token():
    try:
        with open(NOTION_CONFIG) as f:
            return json.load(f)['token']
    except:
        return None


def fetch_notion_pipeline_for_dedup():
    """
    Query Notion Pipeline DB for ALL jobs (all stages).
    Returns (applied_urls: set, applied_keys: set, total: int, applied_companies: dict).
    applied_urls = LinkedIn job IDs from URLs.
    applied_keys = "company|role" normalized pairs.
    applied_companies = {normalized_company: {"count": N, "stages": [list], "roles": [list]}}
    """
    token = load_notion_token()
    applied_urls = set()
    applied_keys = set()
    applied_companies = {}  # company -> {count, stages, roles}
    total = 0
    if not token:
        log("  WARNING: No Notion token - falling back to pipeline.md for dedup")
        return applied_urls, applied_keys, total, applied_companies

    headers = {
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    }
    ctx = ssl.create_default_context()
    cursor = None

    try:
        while True:
            body = {'page_size': 100}
            if cursor:
                body['start_cursor'] = cursor
            req = urllib.request.Request(
                f'https://api.notion.com/v1/databases/{PIPELINE_DB_ID}/query',
                data=json.dumps(body).encode(), method='POST', headers=headers
            )
            resp = json.loads(urllib.request.urlopen(req, timeout=20, context=ctx).read())

            for page in resp.get('results', []):
                props = page.get('properties', {})
                total += 1

                # Extract company (title property)
                company_arr = props.get('Company', {}).get('title', [])
                company = company_arr[0].get('plain_text', '').strip().lower() if company_arr else ''

                # Extract role (rich_text property)
                role_arr = props.get('Role', {}).get('rich_text', [])
                role = role_arr[0].get('plain_text', '').strip().lower() if role_arr else ''

                # Extract URL
                url = props.get('URL', {}).get('url', '') or ''

                # Extract LinkedIn job ID from URL
                url_match = re.search(r'/view/(\d+)', url)
                if url_match:
                    applied_urls.add(url_match.group(1))

                if company and role:
                    applied_keys.add(f"{company}|{role}")

                # Track company-level application history
                if company:
                    # Extract stage
                    stage = ''
                    for sk, sv in props.items():
                        if sv.get('type') == 'select' and sv.get('select'):
                            stage = sv['select'].get('name', '')
                            break
                        elif sv.get('type') == 'status' and sv.get('status'):
                            stage = sv['status'].get('name', '')
                            break
                    if company not in applied_companies:
                        applied_companies[company] = {"count": 0, "stages": [], "roles": []}
                    applied_companies[company]["count"] += 1
                    if stage:
                        applied_companies[company]["stages"].append(stage)
                    if role:
                        applied_companies[company]["roles"].append(role)

            cursor = resp.get('next_cursor')
            if not cursor:
                break

        # Build canonical company names (merge variants like "fab" and "first abu dhabi bank (fab)")
        merged = {}
        for comp, data in applied_companies.items():
            # Find canonical key - longest name wins
            matched = False
            for existing in list(merged.keys()):
                if comp in existing or existing in comp:
                    canonical = comp if len(comp) > len(existing) else existing
                    other = existing if canonical == comp else comp
                    if canonical != other:
                        merged[canonical] = {
                            "count": merged.get(existing, {}).get("count", 0) + data["count"],
                            "stages": merged.get(existing, {}).get("stages", []) + data["stages"],
                            "roles": merged.get(existing, {}).get("roles", []) + data["roles"],
                        }
                        if other in merged:
                            del merged[other]
                    else:
                        merged[canonical]["count"] += data["count"]
                        merged[canonical]["stages"].extend(data["stages"])
                        merged[canonical]["roles"].extend(data["roles"])
                    matched = True
                    break
            if not matched:
                merged[comp] = data
        applied_companies = merged

        log(f"  Notion Pipeline: {total} jobs loaded for dedup ({len(applied_urls)} URLs, {len(applied_keys)} company|role keys, {len(applied_companies)} companies)")
    except Exception as e:
        log(f"  WARNING: Notion Pipeline query failed ({e}), falling back to pipeline.md")

    return applied_urls, applied_keys, total, applied_companies


# ============================================================
# DATA GATHERING (pure Python, no LLM)
# ============================================================

def read_pipeline():
    """Parse pipeline.md (Markdown table format) into structured data."""
    result = {
        "total_applications": 0, "applied": 0, "interviews": 0,
        "stale": 0, "closed": 0, "rejected": 0,
        "recent": [], "overdue": [], "interview_list": []
    }
    if not os.path.exists(PIPELINE_FILE):
        return result

    with open(PIPELINE_FILE) as f:
        content = f.read()

    now = datetime.now(cairo)

    for line in content.strip().split("\n"):
        line = line.strip()
        # Match table rows: | # | ☑️ | Company | Role | Location | ATS | Stage | ...
        if not line.startswith("|") or line.startswith("| #") or line.startswith("|---"):
            continue

        cols = [c.strip() for c in line.split("|")]
        # Remove empty first/last from split
        cols = [c for c in cols if c]

        if len(cols) < 7:
            continue

        # Skip header row
        if cols[0] == "#" or cols[0] == "---":
            continue

        try:
            int(cols[0])
        except:
            continue

        # Parse columns: #, Applied?, Company, Role, Location, ATS, Stage, JD Status, Applied Date, Follow-up Due, Job URL, CV
        company = cols[2].strip().replace("~~", "")  # Remove strikethrough
        role = cols[3].strip().replace("~~", "") if len(cols) > 3 else "?"
        stage = cols[6].strip().replace("~~", "") if len(cols) > 6 else "?"
        applied_date_str = cols[8].strip().replace("~~", "") if len(cols) > 8 else ""

        # Skip strikethrough-only entries that are fully cancelled
        stage_lower = stage.lower()

        result["total_applications"] += 1

        # Detect stage
        if "interview" in stage_lower:
            result["interviews"] += 1
            result["interview_list"].append({"company": company, "role": role, "stage": stage})
        elif "applied" in stage_lower:
            result["applied"] += 1
        elif "rejected" in stage_lower:
            result["closed"] += 1
            result["rejected"] += 1
        elif "closed" in stage_lower or "withdrawn" in stage_lower:
            result["closed"] += 1

        # Check staleness
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', applied_date_str)
        if date_match:
            try:
                applied_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").replace(tzinfo=cairo)
                days_ago = (now - applied_date).days
                if days_ago >= 14 and "interview" not in stage_lower and "rejected" not in stage_lower and "closed" not in stage_lower:
                    result["stale"] += 1
                    result["overdue"].append({
                        "company": company, "role": role[:40], "days": days_ago
                    })
            except:
                pass

    # Sort overdue by days descending
    result["overdue"].sort(key=lambda x: x["days"], reverse=True)
    return result


def load_scanner_data(today_str):
    """Load scanner results for today or most recent."""
    meta = {}
    qualified = []
    borderline = []

    # Try today's meta first, then most recent
    meta_file = f"{JOBS_DIR}/scanner-meta-{today_str}.json"
    if not os.path.exists(meta_file):
        meta_files = sorted(glob.glob(f"{JOBS_DIR}/scanner-meta-*.json"), reverse=True)
        meta_file = meta_files[0] if meta_files else None

    if meta_file and os.path.exists(meta_file):
        with open(meta_file) as f:
            meta = json.load(f)

    # Try today's qualified jobs
    qual_file = f"{JOBS_DIR}/qualified-jobs-{today_str}.md"
    if not os.path.exists(qual_file):
        qual_files = sorted(glob.glob(f"{JOBS_DIR}/qualified-jobs-*.md"), reverse=True)
        qual_file = qual_files[0] if qual_files else None

    if qual_file and os.path.exists(qual_file):
        with open(qual_file) as f:
            content = f.read()
        # Parse qualified jobs - supports two formats:
        # Format A: ### Job Title\n- Company: X\n- Location: Y\n- URL: Z
        # Format B: - Title @ Company (ATS: XX)
        current_section = ""
        current_section_prev = ""
        current_job = None

        for line in content.split("\n"):
            line = line.strip()

            # Section headers (## Priority Picks, ## Leads, ## APPLY, etc.)
            if line.startswith("## "):
                current_section = line.lstrip("# ").strip().lower()
                # Save previous job before switching sections
                if current_job:
                    if any(k in current_section_prev for k in ["priority", "pick", "apply", "genuine"]):
                        qualified.append(current_job)
                    elif "skip" not in current_section_prev:
                        borderline.append(current_job)
                    current_job = None
                current_section_prev = current_section
                continue

                        # Job title as ### heading (Format A)
            if line.startswith("### "):
                # Save previous job
                if current_job:
                    if any(k in current_section for k in ["priority", "pick", "apply", "genuine"]):
                        current_job["career_verdict"] = "APPLY"  # Trust section classification
                        qualified.append(current_job)
                    elif "skip" not in current_section:
                        borderline.append(current_job)
                title = line.lstrip("# ").strip()
                # Strip ATS icon (🟢🟡🔴), career fit score [X/10], and ATS score from title
                title = re.sub(r'^[🟢🟡🔴]\s*', '', title)
                # Extract and strip career fit score like [7/10]
                fit_in_title = re.search(r'^\[(\d+)/10\]\s*', title)
                fit_val = int(fit_in_title.group(1)) if fit_in_title else None
                title = re.sub(r'^\[\d+/10\]\s*', '', title)
                ats_in_title = re.search(r'\(ATS:\s*(\d+)%?\)', title)
                ats_val = int(ats_in_title.group(1)) if ats_in_title else None
                title = re.sub(r'\s*\(ATS:\s*\d+%?\)\s*$', '', title)
                current_job = {"title": title[:60], "company": "", "location": "", "url": ""}
                if fit_val is not None:
                    current_job["career_fit"] = fit_val
                if ats_val is not None:
                    current_job["ats_score"] = ats_val
                continue

            # Metadata lines under ### heading
            if current_job and line.startswith("- "):
                kv = line[2:].strip()
                if kv.lower().startswith("company:"):
                    # Handle markdown links: [Name](url)
                    val = kv.split(":", 1)[1].strip()
                    link_match = re.match(r'\[(.+?)\]', val)
                    current_job["company"] = (link_match.group(1) if link_match else val)[:30]
                elif kv.lower().startswith("location:"):
                    current_job["location"] = kv.split(":", 1)[1].strip()[:30]
                elif kv.lower().startswith("url:"):
                    current_job["url"] = kv.split(":", 1)[1].strip()
                elif kv.lower().startswith("source:"):
                    current_job["source"] = kv.split(":", 1)[1].strip()
                elif kv.lower().startswith("ats score:"):
                    ats_str = re.search(r'(\d+)', kv.split(":", 1)[1])
                    if ats_str:
                        current_job["ats_score"] = int(ats_str.group(1))
                elif kv.lower().startswith("posted:"):
                    current_job["date_posted"] = kv.split(":", 1)[1].strip()
                elif kv.lower().startswith("matching keywords:"):
                    current_job["ats_keywords"] = kv.split(":", 1)[1].strip()
                continue

            # Bullet format (Format B): - Title @ Company (ATS: XX)
            if line.startswith("- ") or line.startswith("* "):
                job_text = line[2:].strip()
                if not any(job_text.lower().startswith(k) for k in ["company:", "location:", "url:", "source:"]):
                    job = {"title": job_text[:60], "raw": job_text}
                    at_match = re.match(r'(.+?)\s*@\s*(.+?)(?:\s*\(ATS:\s*(\d+)\))?$', job_text)
                    if at_match:
                        job["title"] = at_match.group(1).strip()[:50]
                        job["company"] = at_match.group(2).strip()[:30]
                        if at_match.group(3):
                            job["ats_score"] = int(at_match.group(3))
                    if any(k in current_section for k in ["priority", "pick", "apply", "genuine"]):
                        qualified.append(job)
                    elif "skip" not in current_section:
                        borderline.append(job)

        # Don't forget the last job
        if current_job:
            if any(k in current_section for k in ["priority", "pick", "apply", "genuine"]):
                qualified.append(current_job)
            elif "skip" not in current_section:
                borderline.append(current_job)

    scanner_age = None
    if meta.get("date"):
        try:
            scan_date = datetime.strptime(meta["date"], "%Y-%m-%d")
            scanner_age = (datetime.now() - scan_date).days
        except:
            pass

    # Load JD cache if available (for semantic analysis)
    jd_cache = {}
    jd_cache_file = f"{JOBS_DIR}/jd-cache-{today_str}.json"
    if os.path.exists(jd_cache_file):
        try:
            with open(jd_cache_file) as f:
                raw_cache = json.load(f)
            # Clean HTML from JD text
            for url, data in raw_cache.items():
                jd_text = data.get("jd_text", "")
                jd_text = re.sub(r'<[^>]+>', ' ', jd_text)
                jd_text = re.sub(r'&amp;', '&', jd_text)
                jd_text = re.sub(r'&[a-z]+;', ' ', jd_text)
                jd_text = re.sub(r'\s+', ' ', jd_text).strip()
                jd_cache[url] = {"jd_text": jd_text}
        except:
            pass

    # Apply semantic career-fit filter if not already present
    # This ensures legacy scanner data gets filtered too
    for job in qualified:
        if not job.get("career_verdict"):
            title = job.get("title", "").lower()
            # Try to get JD from cache by URL
            jd = ""
            url = job.get("url", "")
            if url in jd_cache:
                jd = jd_cache[url].get("jd_text", "").lower()
            keywords = job.get("ats_keywords", "").lower()
            combined = title + " " + jd + " " + keywords

            SKIP_DOMAINS = {
                "cybersecurity": ["ciso", "information security officer", "security engineer", "penetration", "soc analyst"],
                "hands-on coding": ["software engineer", "developer", "full stack", "backend engineer", "frontend engineer", "code reviews", "sdlc", "hands-on technical", "production-grade ai products", "build platforms from scratch", "technical architecture and product delivery"],
                "oil & gas": ["offshore", "upstream", "downstream", "drilling", "petroleum", "subsea", "oil and gas", "oil & gas"],
                "civil engineering": ["roads", "highways", "bridges", "tunnels", "structural engineer", "geotechnical", "civil engineer"],
                "investment banking": ["equity capital markets", "ecm", "ipo execution", "block trades", "league table", "deal origination"],
                "aviation": ["aircraft", "mro", "ground support equipment", "aviation maintenance"],
                "construction/engineering": ["engineering, construction, and project management services", "engineering and construction consultancy", "construction consultancy solutions", "engineering standards"],
                "pure sales": ["quota-carrying", "business development representative", "sales representative"],
            }
            AHMED_DOMAINS = ["digital transformation", "pmo", "program management", "project management",
                "healthcare", "healthtech", "fintech", "payments", "e-commerce", "ecommerce",
                "operational excellence", "change management", "enterprise", "consulting"]
            AHMED_ROLES = ["pmo", "program", "director", "vp", "vice president", "head of", "chief",
                "transformation", "operations", "strategy", "product management", "delivery"]

            verdict, fit, reason = "APPLY", 5, "Default"
            for domain, keywords in SKIP_DOMAINS.items():
                matches = [k for k in keywords if k in combined]
                if len(matches) >= 2:
                    verdict, fit, reason = "SKIP", max(1, min(3, job.get("ats_score", 0) // 30)), f"Domain mismatch: {domain}"
                    break
                if len(matches) == 1 and any(k in title for k in keywords):
                    verdict, fit, reason = "SKIP", 2, f"Title indicates {domain}"
                    break

            # Additional SKIP: roles that sound executive but are wrong domain
            SKIP_TITLES = ["people transformation", "hr ", "human resources", "facilities",
                "asset management", "ip strategy", "intellectual property", "business development",
                "sales director", "marketing director", "design director", "creative director",
                "construction manager", "site manager", "quantity surveyor"]
            if verdict != "SKIP":
                for st in SKIP_TITLES:
                    if st in title:
                        verdict, fit, reason = "SKIP", 2, f"Wrong specialization: {st.strip()}"
                        break

            if verdict != "SKIP":
                # Require actual domain matches, not just role-level words
                CORE_DOMAINS = ["digital transformation", "pmo", "program management", "project management",
                    "healthcare", "healthtech", "fintech", "payments", "e-commerce", "enterprise"]
                core_hits = sum(1 for d in CORE_DOMAINS if d in combined)
                domain_hits = sum(1 for d in AHMED_DOMAINS if d in combined)
                role_hits = sum(1 for r in AHMED_ROLES if r in combined)

                if core_hits >= 3 and role_hits >= 1:
                    verdict, fit, reason = "APPLY", min(10, 6 + core_hits), "Strong career fit"
                elif core_hits >= 2:
                    verdict, fit, reason = "APPLY", min(8, 5 + core_hits), "Good career fit"
                elif core_hits == 1 and role_hits >= 2:
                    verdict, fit, reason = "STRETCH", min(5, 3 + core_hits), "Partial fit - review JD"
                elif domain_hits >= 1:
                    verdict, fit, reason = "STRETCH", 4, "Weak domain overlap"
                else:
                    verdict, fit, reason = "SKIP", 2, "No relevant domain experience"

            # ATS gate: If ATS score is meaningful (>=20, meaning JD was actually read)
            # but still below threshold (<55), cap verdict at STRETCH.
            # ATS < 20 typically means "couldn't fetch JD" -- don't penalize for missing data.
            # This prevents "good title, weak JD match" jobs from being SUBMIT.
            ats = job.get("ats_score", 0) or 0
            if verdict == "APPLY" and 20 <= ats < 55:
                verdict = "STRETCH"
                fit = min(fit, 6)
                reason = f"{reason} (ATS gate: {ats}/100 - title looks good but JD keyword match is weak)"

            job["career_verdict"] = verdict
            job["career_fit"] = fit
            job["career_reason"] = reason

    return meta, qualified, borderline, scanner_age


def check_email():
    """Read email summary from shared snapshot (written by email-agent.py).
    Falls back to himalaya if snapshot is stale (>6 hours) or missing."""
    import json as _json
    snapshot_path = Path(__file__).parent.parent / "data" / "email-latest.json"
    emails = []
    try:
        if snapshot_path.exists():
            data = _json.load(open(snapshot_path))
            # Check staleness (6 hour threshold)
            scan_time = data.get("scan_time", "")
            if scan_time:
                from datetime import datetime as _dt
                age_hrs = 999
                try:
                    st = _dt.fromisoformat(scan_time.replace("Z", "+00:00"))
                    age_hrs = (_dt.now(st.tzinfo) - st).total_seconds() / 3600
                except Exception:
                    pass
                if age_hrs > 6:
                    return [], f"email-latest.json stale ({age_hrs:.0f}h old)"
            if data.get("status") == "error":
                return [], f"email-agent error: {data.get('error', 'unknown')}"

            # Map snapshot categories to briefing priority levels
            for item in data.get("interview_invites", []):
                item["priority"] = "action"
                item["sender"] = item.get("from", "")
                emails.append(item)
            for item in data.get("assessments", []):
                item["priority"] = "action"
                item["sender"] = item.get("from", "")
                emails.append(item)
            for item in data.get("follow_ups_needed", []):
                item["priority"] = "action"
                item["sender"] = item.get("from", "")
                emails.append(item)
            for item in data.get("recruiter_messages", []):
                item["priority"] = "job"
                item["sender"] = item.get("from", "")
                emails.append(item)
            for item in data.get("application_acks", []):
                item["priority"] = "job"
                item["sender"] = item.get("from", "")
                emails.append(item)

            # Sort: action first, then job
            priority_order = {"action": 0, "job": 1, "linkedin": 2}
            emails.sort(key=lambda e: priority_order.get(e.get("priority", ""), 9))
            return emails, None
        else:
            return [], "email-latest.json not found (email-agent hasn't run yet)"
    except Exception as e:
        return [], str(e)


def check_calendar():
    """Check calendar events. Reads from pre-fetched calendar cache or falls back to gog."""
    events = []
    cal_error = None

    # Try reading pre-fetched calendar data (written by calendar cron via Composio)
    try:
        today_str = datetime.now(cairo).strftime("%Y-%m-%d")
        cache_file = f"/tmp/calendar-events-{today_str}.json"
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                cached = json.load(f)
            for ev in cached:
                events.append({
                    "title": ev.get("title", "Untitled"),
                    "start": ev.get("start", ""),
                    "end": ev.get("end", ""),
                    "calendar": ev.get("calendar", ""),
                    "all_day": ev.get("is_all_day", False),
                })
            return events, None
    except Exception as e:
        pass  # Fall through to gog

    # Fallback: gog calendar (likely broken)
    try:
        r = subprocess.run(
            "gog calendar today",
            shell=True, capture_output=True, text=True, timeout=15
        )
        if r.returncode != 0:
            cal_error = "Calendar auth expired - re-auth needed"
        elif r.stdout.strip():
            for line in r.stdout.strip().split("\n"):
                line = line.strip()
                if line and not line.startswith("="):
                    events.append(line[:60])
    except Exception as e:
        cal_error = f"Calendar check failed: {str(e)[:40]}"
    return events, cal_error


def get_content_calendar():
    """Get content calendar status from Notion."""
    result = {"scheduled": 0, "drafted": 0, "posted": 0, "ideas": 0, "today_post": None,
              "tomorrow_post": None, "next_scheduled": None, "gap_days": 0}
    token = load_notion_token()
    if not token:
        return result

    ctx = ssl.create_default_context()
    today = datetime.now(cairo).date()
    today_str = today.strftime("%Y-%m-%d")
    tomorrow_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        # Query content calendar
        url = "https://api.notion.com/v1/databases/3268d599-a162-814b-8854-c9b8bde62468/query"
        body = json.dumps({"page_size": 100}).encode()
        req = urllib.request.Request(url, data=body, method='POST', headers={
            'Authorization': f'Bearer {token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        })
        with urllib.request.urlopen(req, context=ctx) as r:
            data = json.loads(r.read())

        future_scheduled = []  # Track all future scheduled posts

        for p in data.get('results', []):
            props = p['properties']
            status = (props.get('Status', {}).get('select') or {}).get('name', '')
            planned = (props.get('Planned Date', {}).get('date') or {}).get('start', '')
            title = ''.join(t.get('plain_text', '') for t in props.get('Title', {}).get('title', []))

            if status == 'Posted':
                result["posted"] += 1
            elif status == 'Drafted':
                result["drafted"] += 1
            elif status == 'Scheduled':
                result["scheduled"] += 1
            elif status == 'Ideas':
                result["ideas"] += 1

            if planned == today_str:
                post_url = (props.get('Post URL', {}).get('url') or '')
                page_id = p['id']
                image_url = None
                # Fetch image from page body if posted
                if status == 'Posted':
                    try:
                        burl = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=20"
                        breq = urllib.request.Request(burl, method='GET', headers={
                            'Authorization': f'Bearer {token}', 'Notion-Version': '2022-06-28'
                        })
                        with urllib.request.urlopen(breq, context=ctx, timeout=10) as br:
                            for blk in json.loads(br.read()).get('results', []):
                                if blk.get('type') == 'image':
                                    img = blk.get('image', {})
                                    image_url = (img.get('external', {}).get('url', '') or
                                                 img.get('file', {}).get('url', ''))
                                    break
                    except:
                        pass
                result["today_post"] = {
                    "title": title[:50], "status": status, "date": planned,
                    "post_url": post_url, "image_url": image_url
                }
            elif planned == tomorrow_str and status != 'Posted':
                result["tomorrow_post"] = {"title": title[:50], "status": status, "date": planned}

            # Track future scheduled/drafted posts
            if planned and planned > today_str and status in ('Scheduled', 'Drafted'):
                future_scheduled.append(planned)

        # Find content gap - days until next scheduled post runs out
        if future_scheduled:
            future_scheduled.sort()
            result["next_scheduled"] = future_scheduled[0]
            last_date = future_scheduled[-1]
            try:
                last_dt = datetime.strptime(last_date, "%Y-%m-%d").date()
                result["gap_days"] = (last_dt - today).days
            except:
                pass
    except Exception as e:
        log(f"  Content calendar error: {e}")

    return result


def get_engagement_stats():
    """Get LinkedIn engagement stats from comment tracker."""
    engagement_dir = os.path.join(os.path.dirname(__file__), "..", "memory", "engagement")
    tracker_file = os.path.join(engagement_dir, "comment-tracker.json")
    today_str = datetime.now(cairo).strftime("%Y-%m-%d")
    radar_file = os.path.join(engagement_dir, f"{today_str}-radar.json")
    
    result = {"comments_today": 0, "goal": 5, "streak": 0, "total_comments": 0, "radar_picks": 0}
    
    try:
        if os.path.exists(tracker_file):
            with open(tracker_file) as f:
                tracker = json.load(f)
            today_data = tracker.get("daily_comments", {}).get(today_str, {})
            result["comments_today"] = today_data.get("count", 0) if isinstance(today_data, dict) else today_data
            result["streak"] = tracker.get("streak_days", 0)
            result["total_comments"] = tracker.get("total_comments", 0)
    except:
        pass
    
    try:
        if os.path.exists(radar_file):
            with open(radar_file) as f:
                radar = json.load(f)
            result["radar_picks"] = len(radar.get("top_picks", []))
    except:
        pass
    
    return result


def get_system_health():
    """Check system health metrics."""
    health = {"gateway": "?", "disk_pct": "?", "mem_pct": "?", "uptime": "?",
              "cron_total": 0, "cron_enabled": 0, "cron_disabled": 0, "errors": []}

    # Disk
    try:
        import shutil
        usage = shutil.disk_usage("/")
        health["disk_pct"] = int(usage.used / usage.total * 100)
    except:
        pass

    # Memory
    try:
        with open("/proc/meminfo") as f:
            meminfo = f.read()
        total = int(re.search(r"MemTotal:\s+(\d+)", meminfo).group(1))
        avail = int(re.search(r"MemAvailable:\s+(\d+)", meminfo).group(1))
        health["mem_pct"] = int((total - avail) / total * 100)
    except:
        pass

    # Uptime
    try:
        with open("/proc/uptime") as f:
            uptime_secs = float(f.read().split()[0])
        days = int(uptime_secs // 86400)
        hours = int((uptime_secs % 86400) // 3600)
        health["uptime"] = f"{days}d{hours}h" if days else f"{hours}h"
    except:
        pass

    # Gateway
    try:
        r = subprocess.run("pgrep -f 'openclaw.*gateway'", shell=True, capture_output=True, text=True, timeout=5)
        health["gateway"] = "UP" if r.returncode == 0 else "DOWN"
    except:
        pass

    # Cron health from jobs.json (direct read, no gateway dependency)
    try:
        cron_file = os.path.expanduser("~/.openclaw/cron/jobs.json")
        with open(cron_file) as f:
            cron_data = json.load(f)
        jobs = cron_data.get("jobs", [])
        health["cron_total"] = len(jobs)
        for j in jobs:
            if j.get("enabled", True):
                health["cron_enabled"] += 1
            else:
                health["cron_disabled"] += 1
    except:
        pass

    return health


def score_github_repo(repo):
    """Score a GitHub Discovery repo for relevance to Ahmed's work (0-10)."""
    score = 0
    text = f"{repo.get('name', '')} {repo.get('desc', '')} {repo.get('why', '')}".lower()

    # High-value keywords (3 pts each, max 6)
    high = ["pmo", "program manag", "project manag", "openclaw", "claw",
            "executive", "portfolio", "digital transform"]
    score += min(6, sum(3 for kw in high if kw in text))

    # Medium keywords (2 pts each, max 4)
    med = ["ai agent", "agent skill", "automation", "orchestrat", "multi-agent",
           "mcp", "llm", "briefing", "linkedin", "notion"]
    score += min(4, sum(2 for kw in med if kw in text))

    # Low keywords (1 pt each, max 2)
    low = ["python", "typescript", "cli tool", "framework", "template",
           "skill", "workflow", "pipeline", "cron", "deploy"]
    score += min(2, sum(1 for kw in low if kw in text))

    # Star bonus
    stars = repo.get("stars", 0)
    if stars >= 100:
        score += 2
    elif stars >= 20:
        score += 1

    return min(10, score)


def get_github_discovery():
    """Read GitHub Discovery Radar results from cache, with relevance scoring."""
    today_str = datetime.now(cairo).strftime("%Y-%m-%d")
    yesterday_str = (datetime.now(cairo) - timedelta(days=1)).strftime("%Y-%m-%d")
    
    for date_str in [today_str, yesterday_str]:
        cache_file = f"/tmp/github-discovery-{date_str}.json"
        if os.path.exists(cache_file):
            try:
                with open(cache_file) as f:
                    repos = json.load(f)
                # Score and sort by relevance
                for r in repos:
                    r["relevance"] = score_github_repo(r)
                repos.sort(key=lambda r: r["relevance"], reverse=True)
                return {"repos": repos, "date": date_str, "count": len(repos)}
            except:
                pass
    return {"repos": [], "date": None, "count": 0}


def get_active_tasks():
    """Get task status from Notion Active Tasks DB."""
    result = {"total_open": 0, "overdue": [], "due_today": [], "completed_recent": 0}
    token = load_notion_token()
    if not token:
        return result

    ctx = ssl.create_default_context()
    today_str = datetime.now(cairo).strftime("%Y-%m-%d")

    try:
        url = "https://api.notion.com/v1/databases/3268d599-a162-8152-9036-e4e4a85d444d/query"
        body = json.dumps({"page_size": 100}).encode()
        req = urllib.request.Request(url, data=body, method='POST', headers={
            'Authorization': f'Bearer {token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        })
        with urllib.request.urlopen(req, context=ctx) as r:
            data = json.loads(r.read())

        for p in data.get('results', []):
            props = p['properties']
            done = props.get('Done', {}).get('checkbox', False)
            title = ''.join(t.get('plain_text', '') for t in props.get('Task', {}).get('title', []))
            due = (props.get('Due Date', {}).get('date') or {}).get('start', '')

            if done:
                result["completed_recent"] += 1
                continue

            result["total_open"] += 1

            if due:
                if due < today_str:
                    result["overdue"].append(f"{title[:50]} (due {due})")
                elif due == today_str:
                    result["due_today"].append(title[:50])
    except Exception as e:
        log(f"  Tasks error: {e}")

    return result


def get_scanner_trends():
    """Get scanner trends from Notion."""
    try:
        sys.path.insert(0, f"{WORKSPACE}/scripts")
        from notion_sync import get_scanner_trends as _get_trends
        return _get_trends()
    except:
        return {}


def notion_two_way_sync():
    """Run two-way pipeline + tasks sync."""
    changes = []
    try:
        sys.path.insert(0, f"{WORKSPACE}/scripts")
        from notion_sync import read_pipeline_from_notion, apply_notion_changes_to_pipeline, two_way_sync_active_tasks
        notion_result = read_pipeline_from_notion()
        changes = notion_result.get("changes", [])
        if changes:
            apply_notion_changes_to_pipeline(changes)
            log(f"  Pipeline: {len(changes)} changes synced from Notion")
    except Exception as e:
        log(f"  Two-way sync error: {e}")
    return changes


# ============================================================
# OUTPUT: NOTION PAGE
# ============================================================


def cross_reference(pipeline, emails, events, qualified):
    """Cross-reference data sources for high-value signals."""
    alerts = []

    # Build set of pipeline company names (normalized)
    pipeline_companies = set()
    for ov in pipeline.get("overdue", []):
        pipeline_companies.add(ov["company"].lower().strip())
    for iv in pipeline.get("interview_list", []):
        pipeline_companies.add(iv["company"].lower().strip())

    # 1. Email from company in pipeline
    for e in emails:
        sender_lower = e.get("sender", "").lower()
        for co in pipeline_companies:
            # Match company name in sender (at least 4 chars to avoid false positives)
            if len(co) >= 4 and co in sender_lower:
                alerts.append(f"📧 Email from {e['sender']} matches pipeline company '{co.title()}' - check immediately")
                break

    # 2. Calendar event matching pipeline company (interview prep check)
    for ev in (events or []):
        title_lower = ev.get("title", "").lower()
        for co in pipeline_companies:
            if len(co) >= 4 and co in title_lower:
                # Check if interview stage
                interview_cos = {iv["company"].lower() for iv in pipeline.get("interview_list", [])}
                if co in interview_cos:
                    alerts.append(f"📅 Meeting '{ev['title'][:35]}' matches interview-stage company '{co.title()}'")
                else:
                    alerts.append(f"📅 Meeting '{ev['title'][:35]}' matches pipeline company '{co.title()}'")
                break

    # 2b. Interview prep kit check — flag if prep kit missing for any interview-stage company
    interview_cos = pipeline.get("interview_list", [])
    if interview_cos:
        prep_dir = Path("/root/.openclaw/workspace/docs/interview-prep")
        prep_dir.mkdir(parents=True, exist_ok=True)
        for iv in interview_cos:
            company_slug = re.sub(r'[^\w]', '-', iv.get("company", "")).strip("-").lower()[:20]
            existing = list(prep_dir.glob(f"*{iv.get('company','')[:10]}*.md")) if iv.get("company") else []
            if not existing:
                alerts.append(f"🎯 No interview prep kit for {iv.get('company','')} ({iv.get('role','')}) — run: python3 scripts/jobs-interview-prep.py --all-interviews")

    # 3. New scanner pick at company where already applied
    scanner_companies = set()
    for j in (qualified or []):
        jco = j.get("company", "").lower().strip()
        if jco:
            scanner_companies.add(jco)

    for sco in scanner_companies:
        if len(sco) >= 4 and sco in pipeline_companies:
            alerts.append(f"🔍 New job found at '{sco.title()}' where you already have an application")

    # 4. Interview scheduled but no recent prep/dossier
    dossier_dir = os.path.join(WORKSPACE, "research", "dossiers")
    for iv in pipeline.get("interview_list", []):
        co = iv["company"]
        if os.path.isdir(dossier_dir):
            dossier_files = [f for f in os.listdir(dossier_dir) if co.lower() in f.lower()]
            if not dossier_files:
                alerts.append(f"🎯 Interview at {co} but no dossier found - prepare company research")

    return alerts


# ============================================================

def create_notion_briefing(date_str, date_display, pipeline, scanner_meta, qualified, borderline,
                           scanner_age, emails, email_error, events, cal_error, content_cal,
                           system, tasks, notion_changes, trends, github_discovery=None, cross_refs=None):
    """Create a rich Notion briefing page with ALL sections."""
    import time as _time
    _start_time = _time.time()
    token = load_notion_token()
    if not token:
        log("  No Notion token - skipping")
        return None

    ctx = ssl.create_default_context()

    def notion_req(method, path, body=None, retries=3):
        url = f"https://api.notion.com/v1{path}"
        data = json.dumps(body).encode() if body else None
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, data=data, method=method, headers={
                    'Authorization': f'Bearer {token}',
                    'Notion-Version': '2022-06-28',
                    'Content-Type': 'application/json'
                })
                with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as e:
                if e.code in (429, 502, 503) and attempt < retries - 1:
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    log(f"  Notion API {e.code} - retry {attempt+1}/{retries} in {wait}s")
                    _time.sleep(wait)
                else:
                    raise

    def rt(text):
        """Rich text helper - auto-links URLs so they're clickable in Notion."""
        text = str(text)[:2000]  # Notion rich_text content limit per segment is 2000
        # Split text on URLs and create linked segments
        url_pattern = re.compile(r'(https?://[^\s\])<>]+)')
        parts = url_pattern.split(text)
        if len(parts) == 1:
            # No URLs found - plain text
            return [{"type": "text", "text": {"content": text}}]
        segments = []
        for i, part in enumerate(parts):
            if not part:
                continue
            if url_pattern.match(part):
                # This is a URL - make it a clickable link
                segments.append({"type": "text", "text": {"content": part, "link": {"url": part}}})
            else:
                segments.append({"type": "text", "text": {"content": part}})
        return segments if segments else [{"type": "text", "text": {"content": text}}]

    # Build blocks
    blocks = []

    def add_callout(text, emoji="📋"):
        blocks.append({"type": "callout", "callout": {"rich_text": rt(text), "icon": {"type": "emoji", "emoji": emoji}}})

    def add_heading(text):
        blocks.append({"type": "heading_2", "heading_2": {"rich_text": rt(text)}})

    def add_heading3(text):
        blocks.append({"type": "heading_3", "heading_3": {"rich_text": rt(text)}})

    def add_para(text):
        blocks.append({"type": "paragraph", "paragraph": {"rich_text": rt(text)}})

    def add_bullet(text):
        blocks.append({"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rt(text)}})

    def add_numbered(text):
        blocks.append({"type": "numbered_list_item", "numbered_list_item": {"rich_text": rt(text)}})

    def add_divider():
        blocks.append({"type": "divider", "divider": {}})

    def add_toggle(title, children_texts):
        """Add a collapsible toggle block with bullet children."""
        children = [{"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rt(t)}} for t in children_texts]
        blocks.append({
            "type": "toggle",
            "toggle": {
                "rich_text": rt(title),
                "children": children[:100]
            }
        })

    p = pipeline

    # ==================== EXECUTIVE SUMMARY ====================
    # Build summary sentence
    summary_parts = []
    if p["interviews"]:
        summary_parts.append(f"🎯 {p['interviews']} interview(s) active")
    if qualified:
        apply_count = len([j for j in qualified if j.get("career_verdict") == "APPLY" or (not j.get("career_verdict") and j.get("ats_score", 0) >= 50)])
        summary_parts.append(f"{len(qualified)} scanned ({apply_count} genuine fits)")
    # Stale count removed from summary - LinkedIn applications have no follow-up channel
    # Guard against content_cal being None (Notion API failure)
    if content_cal is None:
        content_cal = {"scheduled": 0, "drafted": 0, "posted": 0, "ideas": 0, "today_post": None,
                       "tomorrow_post": None, "next_scheduled": None, "gap_days": 0}
    content_status = "posted ✅" if (content_cal.get("today_post") or {}).get("status") == "Posted" else "pending"
    summary_parts.append(f"content {content_status}")
    gw_status = "🟢" if system.get("gateway") == "UP" else "🔴"
    summary_parts.append(f"systems {gw_status}")

    add_callout(" | ".join(summary_parts), "☀️")

    # ==================== ACTION ITEMS (RED - TOP) ====================
    # Helper: Gmail web search link
    def gmail_link(subject):
        from urllib.parse import quote
        return f"https://mail.google.com/mail/u/0/#search/{quote(subject[:60])}"
    # Helper: Pipeline DB filtered view (stale)
    pipeline_db_url = "https://www.notion.so/3268d599a162812da59ee5496dec80e7?v=stale"

    actions = []
    if p["interviews"]:
        for iv in p["interview_list"]:
            actions.append(f"\U0001f3af Follow up {iv['company']} interview")
    action_emails = [e for e in emails if e.get("priority") == "action"]
    if action_emails:
        for ae in action_emails[:2]:
            subj = ae.get('subject', '')[:35]
            actions.append(f"\U0001f4e7 Reply: {subj} - {gmail_link(ae.get('subject', ''))}")
    if qualified:
        apply_jobs = [j for j in qualified if j.get("career_verdict") == "APPLY" or (not j.get("career_verdict") and j.get("ats_score", 0) >= 50)]
        if apply_jobs:
            top = apply_jobs[0]
            url = top.get("url", "")
            actions.append(f"Apply to {len(apply_jobs)} career fits (top: {top.get('title','')[:30]} @ {top.get('company','')[:20]}) {url}")
    # Stale follow-ups removed - applied via LinkedIn so no direct follow-up channel
    if content_cal.get("today_post") and content_cal["today_post"].get("status") != "Posted":
        actions.append(f"Publish: \"{content_cal['today_post'].get('title', '')[:30]}\"")
    if content_cal.get("drafted", 0) == 0:
        actions.append("\U0001f4dd Content pipeline empty!")
    if tasks.get("overdue"):
        actions.append(f"Address {len(tasks['overdue'])} overdue tasks")
    if isinstance(system.get('disk_pct'), int) and system['disk_pct'] >= 80:
        actions.append(f"\u26a0\ufe0f Disk {system['disk_pct']}%")
    if cal_error:
        actions.append("Fix Calendar auth")

    if actions:
        add_callout("ACTION ITEMS\n" + "\n".join(f"{i}. {a}" for i, a in enumerate(actions[:7], 1)), "🔴")
    else:
        add_callout("All clear - no urgent actions", "✅")

    # Cross-reference intelligence
    if cross_refs:
        add_callout("INTELLIGENCE\n" + "\n".join(f"🔗 {cr}" for cr in cross_refs), "🧠")

    add_divider()

    # ==================== PIPELINE ====================
    add_heading("📊 Pipeline")
    response_rate = p['interviews'] / max(p['total_applications'], 1) * 100
    add_para(f"{p['total_applications']} total | {p['applied']} applied | {p['interviews']} interviews | Response rate: {response_rate:.1f}%")

    if p["interview_list"]:
        for iv in p["interview_list"]:
            add_bullet(f"🎯 {iv['company']} - {iv['role']} ({iv['stage']})")

    # Stale follow-up toggle removed - LinkedIn applications have no direct follow-up channel

    if notion_changes:
        change_items = [f"{c['company']}: {c.get('old','?')} → {c.get('new','?')}" for c in notion_changes[:5]]
        add_toggle(f"🔄 {len(notion_changes)} Notion changes", change_items)

    add_divider()

    # ==================== JOBS ====================
    add_heading("💼 Jobs")

    # Load fresh data from jobs-summary.json (the real LLM-reviewed output)
    _jobs_summary_path = Path(WORKSPACE) / "data" / "jobs-summary.json"
    _submit_jobs = []
    _review_jobs = []
    _skip_count = 0
    _total_raw = 0
    _total_reviewed = 0
    _new_submit = []  # genuinely new (not in Notion)

    try:
        if _jobs_summary_path.exists():
            with open(_jobs_summary_path) as _jsf:
                _js_data = json.load(_jsf)
            _jsd = _js_data.get('data', _js_data)
            _submit_jobs = _jsd.get('submit', [])
            _review_jobs = _jsd.get('review', [])
            _skip_count = _jsd.get('skip_count', 0)
            _total_reviewed = _jsd.get('reviewed', len(_submit_jobs) + len(_review_jobs) + _skip_count)
            _total_raw = _jsd.get('total_candidates', _total_reviewed)
    except Exception as _je:
        log(f"  Jobs summary load error: {_je}")

    # Dedup info
    _deduped_count = len([j for j in qualified if j.get("_deduped")]) if qualified else 0
    _new_submit = _submit_jobs  # cross_refs is a list of strings, not a dict

    # ---- Scanner Health Block ----
    if scanner_meta:
        _sm_total = scanner_meta.get("total_found", 0)
        _sm_searches = scanner_meta.get("total_searches", 0)
        _sm_countries = scanner_meta.get("countries", [])
        _sm_sources = scanner_meta.get("sources", [])
        _sm_source_status = scanner_meta.get("source_status", {})
        _sm_titles = scanner_meta.get("search_terms", scanner_meta.get("titles", []))
        _sm_freshness = "fresh" if scanner_age == 0 else f"{scanner_age}d old" if scanner_age else ""

        # Applied to date count from pipeline
        _applied_to_date = p.get("applied", 0) + p.get("interviews", 0)

        # Source health line
        if _sm_source_status:
            _src_parts = []
            for src_name, src_stat in _sm_source_status.items():
                _src_parts.append(f"{src_name}: {src_stat}")
            _src_line = " | ".join(_src_parts)
        elif _sm_sources:
            _src_line = " | ".join(f"{s} ✅" for s in _sm_sources)
        else:
            _src_line = "LinkedIn ✅ | Indeed ✅"

        add_para(f"🔍 Scanned: {_sm_total} raw → {len(_submit_jobs)} SUBMIT | {len(_review_jobs)} REVIEW | {_skip_count} SKIP | {_sm_freshness}")
        add_para(f"📋 Applied to date: {_applied_to_date} | Searches run: {_sm_searches} | Countries: {len(_sm_countries)} ({', '.join(_sm_countries[:6])})")
        # Source health
        _src_health_items = []
        for src_name, src_stat in (_sm_source_status.items() if _sm_source_status else {s: '✅' for s in _sm_sources}.items()):
            status_icon = "✅" if "✅" in str(src_stat) or str(src_stat).strip() == "✅" else "⚠️"
            _src_health_items.append(f"{status_icon} {src_name}: {src_stat}")
        if _src_health_items:
            add_toggle(f"📡 Sources ({len(_src_health_items)} active)", _src_health_items)
        # Titles covered
        if _sm_titles:
            add_toggle(f"🏷️ Titles covered ({len(_sm_titles)})", [f"• {t}" for t in _sm_titles])
        elif _sm_searches:
            add_para(f"🏷️ {_sm_searches} search queries executed across {len(_sm_countries)} countries")
    else:
        add_para(f"Reviewed: {_total_reviewed} | {len(_submit_jobs)} SUBMIT | {len(_review_jobs)} REVIEW | {_skip_count} SKIP")

    # Load CV links generated by jobs-cv-autogen.py
    _cv_links = {}
    _cv_links_file = Path("/root/.openclaw/workspace/data/jobs-cv-links.json")
    if _cv_links_file.exists():
        try:
            with open(_cv_links_file) as _f:
                _cv_links = json.load(_f)
        except Exception:
            pass

    # Load cover letter links generated by jobs-coverletter-autogen.py
    _cover_links = {}
    _cover_links_file = Path("/root/.openclaw/workspace/data/jobs-cover-links.json")
    if _cover_links_file.exists():
        try:
            with open(_cover_links_file) as _f:
                _cover_links = json.load(_f)
        except Exception:
            pass

    def _format_job_lines(j, rank: int = None):
        """Return a list of lines for a job — each will become its own Notion bullet."""
        title = j.get("title", "?")[:45]
        company = j.get("company", "")[:22]
        ats = j.get("ats_score", 0)
        loc = j.get("location", "")[:15]
        url = j.get("url", "")
        posted = j.get("posted", "")
        first_seen = j.get("first_seen", "")
        job_id = j.get("id", "")
        reason = j.get("sonnet_reason", "") or j.get("verdict_reason", "")
        override_flag = " ⚡" if j.get("sonnet_overrode_m2") else ""
        freshness = ""
        if first_seen == today_str:
            freshness = "🆕 "
        elif posted:
            try:
                posted_dt = datetime.strptime(posted, "%Y-%m-%d").date()
                days_old = (datetime.now(cairo).date() - posted_dt).days
                if days_old <= 1:
                    freshness = "🆕 "
                elif days_old <= 3:
                    freshness = f"📌{days_old}d "
                else:
                    freshness = f"🕐{days_old}d "
            except Exception:
                pass

        rank_prefix = f"#{rank} " if rank is not None else ""
        lines = [f"{rank_prefix}{freshness}ATS:{ats} | {title} @ {company} | {loc}{override_flag}"]
        if url:
            lines.append(f"  → 🔗 Apply: {url}")
        if reason:
            lines.append(f"  └ {reason[:120]}")

        # CV link from autogen — always its own bullet so it's never truncated
        cv_info = _cv_links.get(job_id, {})
        cv_url = cv_info.get("cv_url", "")
        if cv_url:
            if cv_info.get("generated"):
                lines.append(f"  → 📄 CV (Opus draft): {cv_url}")
            elif cv_info.get("reused"):
                lines.append(f"  → 📄 CV (existing): {cv_url}")
            elif cv_info.get("fallback"):
                lines.append(f"  → 📄 CV (closest match): {cv_url}")

        # Cover letter link
        cover_info = _cover_links.get(job_id, {})
        cover_url = cover_info.get("cover_url", "")
        if cover_url:
            label = "existing" if cover_info.get("reused") else "draft"
            lines.append(f"  → ✉️ Cover ({label}): {cover_url}")
        return lines

    def _format_job_line(j, rank: int = None):
        """Single-string version for use in toggles (limited context)."""
        lines = _format_job_lines(j, rank)
        return " | ".join(l.strip() for l in lines)

    def add_job_bullets(j, rank: int = None):
        """Emit each sub-line of a job as its own bullet — ensures CV links are never truncated."""
        for line in _format_job_lines(j, rank):
            add_bullet(line)

    # Split by freshness
    today_str = datetime.now(cairo).strftime("%Y-%m-%d")
    yesterday_str = (datetime.now(cairo) - timedelta(days=1)).strftime("%Y-%m-%d")

    # SUBMIT section — ranked, numbered, with CV links
    if _submit_jobs:
        _submit_sorted = sorted(
            _submit_jobs,
            key=lambda x: (x.get("sonnet_rank") or 99, -(x.get("ats_score") or 0))
        )
        _fresh_submit = [j for j in _submit_sorted if j.get("first_seen", "") >= yesterday_str or j.get("posted", "") >= yesterday_str]
        _older_submit = [j for j in _submit_sorted if j not in _fresh_submit]

        add_heading3(f"🟢 SUBMIT ({len(_submit_jobs)} jobs)")

        if _fresh_submit:
            add_para(f"🆕 {len(_fresh_submit)} fresh (posted/seen in last 48h):")
            for i, j in enumerate(_fresh_submit[:5], 1):
                add_job_bullets(j, rank=i)
            if len(_fresh_submit) > 5:
                more = [_format_job_line(j, rank=i+5) for i, j in enumerate(_fresh_submit[5:])]
                add_toggle(f"📋 {len(_fresh_submit) - 5} more fresh SUBMIT...", more)

        if _older_submit:
            base_rank = len(_fresh_submit) + 1
            older_items = [_format_job_line(j, rank=base_rank+i) for i, j in enumerate(_older_submit)]
            add_toggle(f"📌 {len(_older_submit)} still open (posted 2+ days ago)", older_items)

        if not _fresh_submit:
            add_para("No fresh SUBMIT jobs today - all are older postings still open")
            for i, j in enumerate(_submit_sorted[:5], 1):
                add_job_bullets(j, rank=i)
            if len(_submit_sorted) > 5:
                more = [_format_job_line(j, rank=i+5) for i, j in enumerate(_submit_sorted[5:])]
                add_toggle(f"📋 {len(_submit_sorted) - 5} more SUBMIT jobs...", more)

    # REVIEW section — collapsed, no CV links (review only)
    if _review_jobs:
        _review_sorted = sorted(_review_jobs, key=lambda x: x.get("ats_score", 0), reverse=True)
        _fresh_review = [j for j in _review_sorted if j.get("first_seen", "") >= yesterday_str or j.get("posted", "") >= yesterday_str]
        review_items = [_format_job_line(j) for j in _review_sorted]
        fresh_note = f" | {len(_fresh_review)} fresh" if _fresh_review else ""
        add_toggle(f"🟡 REVIEW ({len(_review_jobs)} jobs{fresh_note}) — tap to expand", review_items)

    # SKIP count
    if _skip_count:
        add_para(f"❌ {_skip_count} jobs skipped (domain mismatch or low fit)")

    # ATS distribution insight
    if _submit_jobs:
        strong = len([j for j in _submit_jobs if j.get('ats_score', 0) >= 40])
        mid = len([j for j in _submit_jobs if 20 <= j.get('ats_score', 0) < 40])
        weak = len([j for j in _submit_jobs if j.get('ats_score', 0) < 20])
        add_para(f"ATS quality: {strong} strong (≥40) | {mid} mid (20-39) | {weak} no JD (<20)")

    if trends.get("total_runs", 0) >= 3:
        add_para(f"Trend: {trends.get('trend','')} 7d avg: {trends.get('avg_7d_found',0):.0f} found, {trends.get('avg_7d_picks',0):.0f} picks")

    add_divider()

    # ==================== EMAIL + CALENDAR ====================
    # Decision 3: Conditional collapsing
    email_action_list = [e for e in emails if e.get("priority") == "action"]
    job_emails = [e for e in emails if e.get("priority") in ("job", "linkedin")]
    has_email_actions = bool(email_action_list)
    has_events = bool(events)
    email_cal_quiet = not has_email_actions and not has_events and not email_error and not cal_error

    if email_cal_quiet:
        email_count = len(emails) if emails else 0
        toggle_items = []
        if job_emails:
            toggle_items = [f"\U0001f7e1 {e.get('subject', '')[:50]} - {e.get('sender', '')[:25]}" for e in job_emails[:5]]
        add_toggle(f"\U0001f4e7 {email_count} emails (no replies needed) | \U0001f4c5 Clear day \u2705", toggle_items or ["No items"])
    else:
        add_heading("\U0001f4e7 Email & Calendar")
        if email_action_list:
            for e in email_action_list:
                unread = " \U0001f195" if e.get("unread") else ""
                subj = e.get('subject', '')[:50]
                add_bullet(f"\U0001f534 {subj} - {e.get('sender', '')[:25]}{unread} - {gmail_link(e.get('subject', ''))}")
        if job_emails:
            email_items = [f"\U0001f7e1 {e.get('subject', '')[:50]} - {e.get('sender', '')[:25]}{'  \U0001f195' if e.get('unread') else ''}" for e in job_emails[:10]]
            add_toggle(f"\U0001f4e7 {len(emails)} job-related emails", email_items)
        if not emails and not email_error:
            add_bullet("\U0001f4e7 No job-related emails")
        if email_error:
            add_bullet(f"\U0001f4e7 \u26a0\ufe0f {email_error}")

        if cal_error:
            add_bullet(f"\U0001f4c5 \u26a0\ufe0f {cal_error}")
        elif events:
            for ev in events[:3]:
                title = ev.get("title", "Untitled")[:40]
                start = ev.get("start", "")
                time_str = str(start).split("T")[1][:5] if "T" in str(start) else ("All day" if ev.get("all_day") else "")
                add_bullet(f"\U0001f4c5 {title} ({time_str})" if time_str else f"\U0001f4c5 {title}")
        else:
            add_bullet("\U0001f4c5 Clear day \u2705")

    add_divider()

    # ==================== CONTENT + ENGAGEMENT (Decision 5: collapse when all clear) ====================
    engagement_stats = get_engagement_stats()
    comments_today = engagement_stats.get("comments_today", 0)
    comment_goal = engagement_stats.get("goal", 5)
    streak = engagement_stats.get("streak", 0)
    radar_picks = engagement_stats.get("radar_picks", 0)

    today_posted = (content_cal.get("today_post") or {}).get("status") == "Posted"
    comments_met = comments_today >= comment_goal
    content_all_clear = today_posted and comments_met and content_cal.get("drafted", 0) > 1

    if content_all_clear:
        streak_str = f" | \U0001f525 {streak}d streak" if streak > 1 else ""
        detail_items = [
            f"{content_cal['posted']} posted | {content_cal['scheduled']} scheduled | {content_cal['drafted']} drafted",
            f"Today: \"{(content_cal.get('today_post') or {}).get('title', '')[:30]}\" Posted \u2705",
        ]
        if content_cal.get("tomorrow_post"):
            detail_items.append(f"Tomorrow: \"{content_cal['tomorrow_post'].get('title', '')[:30]}\" [{content_cal['tomorrow_post'].get('status', '?')}]")
        add_toggle(f"\U0001f4dd Content \u2705 | \U0001f4ac {comments_today}/{comment_goal} comments{streak_str}", detail_items)
    else:
        add_heading("\U0001f4dd Content & Engagement")
        status_parts = [f"{content_cal['posted']} posted", f"{content_cal['scheduled']} scheduled", f"{content_cal['drafted']} drafted"]
        add_para(" | ".join(status_parts))

        if content_cal.get("today_post"):
            tp = content_cal["today_post"]
            icon = "\u2705" if tp["status"] == "Posted" else "\U0001f4cb"
            add_bullet(f"Today: \"{tp['title'][:40]}\" [{tp['status']}] {icon}")
            if tp["status"] == "Posted" and tp.get("post_url"):
                add_bullet(f"\U0001f517 LinkedIn: {tp['post_url']}")
            if tp.get("image_url"):
                add_bullet(f"\U0001f5bc\ufe0f Image: {tp['image_url']}")
                blocks.append({"type": "image", "image": {"type": "external", "external": {"url": tp["image_url"]}}})
        if content_cal.get("tomorrow_post"):
            tp = content_cal["tomorrow_post"]
            add_bullet(f"Tomorrow: \"{tp['title'][:40]}\" [{tp['status']}]")
        if content_cal.get("drafted", 0) <= 1:
            add_bullet(f"\u26a0\ufe0f Only {content_cal['drafted']} draft(s) - pipeline drying up")

        progress_bar = "\U0001f7e2" * min(comments_today, comment_goal) + "\u26aa" * max(0, comment_goal - comments_today)
        streak_str = f" | \U0001f525 {streak}d streak" if streak > 1 else ""
        add_bullet(f"\U0001f4ac Comments: {comments_today}/{comment_goal} {progress_bar}{streak_str}")
        if radar_picks > 0:
            add_bullet(f"\U0001f4e1 {radar_picks} comment opportunities ready")
        add_bullet(f"\U0001f91d {content_cal.get('posted', 0)} total posts")

    add_divider()

    # ==================== ENGAGE LAYER ====================
    try:
        engage_items = []

        # Comment Radar data
        radar_path = Path(WORKSPACE) / "data" / "comment-radar.json"
        if radar_path.exists():
            with open(radar_path) as _rf:
                _radar = json.load(_rf)
            radar_gen = _radar.get("generated", "?")[:16]
            radar_count = _radar.get("posts_found", 0)
            top_posts = _radar.get("top_posts", [])
            if top_posts:
                engage_items.append(f"🎯 {len(top_posts)} comment targets found (last scan: {radar_gen})")
                for tp in top_posts[:3]:
                    author = tp.get("author", "Unknown")
                    pqs = tp.get("pqs", "?")
                    topic = tp.get("topic", tp.get("title", ""))[:50]
                    engage_items.append(f"  • {author} | PQS {pqs} | {topic}")
            else:
                engage_items.append(f"🎯 Comment Radar: {_radar.get('status', 'no_results')} (last: {radar_gen})")

        # Comment Tracker stats
        tracker_path = Path(WORKSPACE) / "data" / "comment-tracker.json"
        if tracker_path.exists():
            with open(tracker_path) as _tf:
                _tracker = json.load(_tf)
            stats = _tracker.get("stats", {})
            total_posted = stats.get("total_posted", 0)
            total_drafted = stats.get("total_drafted", 0)
            last_radar = _tracker.get("last_radar_run", "?")[:16]
            engage_items.append(f"📊 Comments: {total_posted} posted | {total_drafted} drafted | Last radar: {last_radar}")

        # Commented posts history
        commented_path = Path(WORKSPACE) / "data" / "commented-posts.jsonl"
        if commented_path.exists():
            commented_lines = commented_path.read_text().strip().split('\n')
            commented_lines = [l for l in commented_lines if l.strip()]
            if commented_lines:
                last_comment = json.loads(commented_lines[-1])
                engage_items.append(f"💬 {len(commented_lines)} comments posted via browser | Last: {last_comment.get('date', '?')}")

        # Cron schedule info
        engage_items.append("⏰ Pre-Post Priming: 9 AM (finds 5 posts) → Engage: 10:30 AM (Sun-Thu)")

        if engage_items:
            add_toggle(f"🤝 Engage Layer | {len(engage_items) - 1} data points", engage_items)
        else:
            add_toggle("🤝 Engage Layer | No data yet", ["Comment radar and engagement tracking will populate here"])
    except Exception as _eng_err:
        add_toggle(f"🤝 Engage Layer ⚠️ {str(_eng_err)[:50]}", ["Check comment-radar-agent.py"])

    add_divider()

    # ==================== CONTENT FACTORY ====================
    try:
        cf_items = []
        # RSS Intelligence state
        rss_state_path = Path(WORKSPACE) / "data" / "rss-intelligence-state.json"
        if rss_state_path.exists():
            with open(rss_state_path) as _f:
                _rss_st = json.load(_f)
            cf_items.append(f"📡 RSS: {len(_rss_st.get('seen_urls', []))} articles indexed | Last run: {_rss_st.get('last_run', '?')[:16]}")

        # Exa Scanner status
        exa_state_path = Path(WORKSPACE) / "data" / "exa-scanner-state.json"
        if exa_state_path.exists():
            with open(exa_state_path) as _f:
                _exa_st = json.load(_f)
            cf_items.append(f"🔎 Exa: {_exa_st.get('total_saved', '?')} saved | Last: {_exa_st.get('last_run', '?')[:16]} | Sources: Web + X + LinkedIn")
        else:
            cf_items.append("🔎 Exa: Mon/Wed/Fri 8 AM (12 searches across Web, X, LinkedIn)")

        # Content Calendar stats (already available from content_cal var)
        cal_total = (content_cal.get('posted', 0) + content_cal.get('scheduled', 0) +
                     content_cal.get('drafted', 0) + content_cal.get('ideas', 0))
        cf_items.append(f"📅 Calendar: {cal_total} total | {content_cal.get('ideas', 0)} Ideas → {content_cal.get('drafted', 0)} Drafts → {content_cal.get('scheduled', 0)} Scheduled → {content_cal.get('posted', 0)} Posted")

        # Pipeline stages with times
        cf_items.append("⏰ Daily chain: RSS 7AM → Scorer 7:30 → Exa 8 (M/W/F) → Bridge 8:30 → Drafter 9 → Poster 9:30")
        cf_items.append("📋 Weekly: Friday 9AM Top-5 Digest to Telegram")

        # Check last pipeline run log
        pipeline_log = Path(WORKSPACE) / "data" / "pipeline-runs.jsonl"
        if pipeline_log.exists():
            lines = pipeline_log.read_text().strip().split('\n')
            if lines:
                last_run = json.loads(lines[-1])
                stages_ok = sum(1 for s in last_run.get('stages', {}).values() if s.get('status') in ('success', 'skipped'))
                stages_total = len(last_run.get('stages', {}))
                cf_items.append(f"🏭 Last pipeline: {last_run.get('timestamp', '?')[:16]} | {stages_ok}/{stages_total} stages OK | {last_run.get('total_duration', 0)}s")

        cf_all_ok = len(cf_items) >= 4  # Has enough data = probably healthy
        if cf_all_ok:
            add_toggle(f"🏭 Content Factory ✅ | {content_cal.get('drafted', 0)} drafts ready | {content_cal.get('ideas', 0)} in queue", cf_items)
        else:
            add_heading("🏭 Content Factory")
            for item in cf_items:
                add_bullet(item)
    except Exception as _cf_err:
        add_toggle(f"🏭 Content Factory ⚠️ Error: {str(_cf_err)[:50]}", ["Check content-factory-health-monitor.py"])

    add_divider()

    # ==================== SCANNER HEALTH (broken sources) ====================
    try:
        scanner_items = []
        # Check each source from latest merge
        merged_path = Path(WORKSPACE) / "data" / "jobs-merged.json"
        source_counts = {}
        if merged_path.exists():
            with open(merged_path) as _f:
                _merged = json.load(_f)
            _jobs_list = _merged if isinstance(_merged, list) else _merged.get('jobs', _merged.get('data', []))
            if isinstance(_jobs_list, list):
                for _j in _jobs_list:
                    src = _j.get('source', 'unknown')
                    source_counts[src] = source_counts.get(src, 0) + 1

        # Known scanner statuses
        scanners = [
            ("LinkedIn (tls-client)", source_counts.get('linkedin', source_counts.get('LinkedIn', 0)), "✅"),
            ("Google Jobs", source_counts.get('google', source_counts.get('Google', 0)), "✅"),
            ("Indeed", source_counts.get('indeed', source_counts.get('Indeed', 0)), "✅"),
            ("Bayt", source_counts.get('bayt', source_counts.get('Bayt', 0)), "❌ 403 Forbidden"),
            ("Adzuna", source_counts.get('adzuna', source_counts.get('Adzuna', 0)), "❌ 0 results (API keys present)"),
            ("HiringCafe", source_counts.get('hiringcafe', source_counts.get('HiringCafe', 0)), "❌ Hangs on execution"),
        ]

        working = sum(1 for _, c, s in scanners if c > 0 or s == "✅")
        broken = sum(1 for _, c, s in scanners if "❌" in s)

        for name, count, status in scanners:
            icon = "🟢" if count > 0 else ("🔴" if "❌" in status else "🟡")
            scanner_items.append(f"{icon} {name}: {count} jobs | {status}")

        total_jobs = sum(c for _, c, _ in scanners)
        scanner_items.append(f"📊 Total: {total_jobs} raw jobs from {working} working sources")

        if broken > 0:
            add_toggle(f"📡 Job Scanners: {working}/6 working | {broken} broken ⚠️", scanner_items)
        else:
            add_toggle(f"📡 Job Scanners: {working}/6 all green ✅", scanner_items)
    except Exception as _sc_err:
        add_toggle(f"📡 Job Scanners ⚠️ Error: {str(_sc_err)[:50]}", ["Check nasr-doctor.py"])

    add_divider()

    # ==================== OUTREACH ====================
    _outreach_path = Path(WORKSPACE) / "data" / "outreach-summary.json"
    try:
        with open(_outreach_path) as _of:
            _outreach = json.load(_of)
        _odata = _outreach.get("data", {})
        _this_week = _odata.get("this_week", {})
        _queue = _odata.get("queue_health", {})
        _next_actions = _odata.get("next_actions", [])
        _targets = _odata.get("targets", {})

        _sent = _this_week.get("sent", 0)
        _accepted = _this_week.get("accepted", 0)
        _pending = _this_week.get("pending", 0)
        _overdue = _queue.get("overdue_follow_ups", 0)
        _follow_up_due = _queue.get("follow_ups_due", 0)
        _warm = _queue.get("warm_leads", 0)

        _outreach_items = []
        _outreach_items.append(f"This week: {_sent} sent | {_accepted} accepted | {_pending} pending")
        if _overdue > 0:
            _outreach_items.append(f"⚠️ {_overdue} overdue follow-up(s)")
        if _warm > 0:
            _outreach_items.append(f"🔥 {_warm} warm lead(s) — respond now")
        if _targets:
            _total_targets = _targets.get("total", 0)
            _contacted = _targets.get("contacted", 0)
            _connected = _targets.get("connected", 0)
            _outreach_items.append(f"Network: {_contacted}/{_total_targets} contacted | {_connected} connected")
        if _next_actions:
            _action_lines = []
            for _a in _next_actions[:5]:
                _name = _a.get("name", "?")
                _co = _a.get("company", "")
                _type_action = _a.get("next_action", "?").replace("_", " ")
                _pri = "🔴" if _a.get("priority") == "high" else "🟡"
                _action_lines.append(f"{_pri} {_name} @ {_co} → {_type_action}")
            add_toggle(f"🤝 Outreach | {_sent} sent this week | {_follow_up_due} follow-ups due", _outreach_items + _action_lines)
        else:
            add_toggle(f"🤝 Outreach | {_sent} sent this week", _outreach_items if _outreach_items else ["No outreach data"])
    except Exception as _oe:
        add_toggle("🤝 Outreach", [f"Data unavailable: {str(_oe)[:60]}"])

    add_divider()

    # ==================== TASKS (own section, Decision 6) ====================
    add_heading("\u2705 Tasks")
    overdue_str = f" | \U0001f534 {len(tasks['overdue'])} overdue" if tasks["overdue"] else ""
    due_str = f" | \U0001f4cc {len(tasks['due_today'])} due today" if tasks["due_today"] else ""
    done_str = f" | \u2714\ufe0f {tasks['completed_recent']} done" if tasks.get("completed_recent") else ""
    add_para(f"Tasks: {tasks['total_open']} open{overdue_str}{due_str}{done_str}")

    if tasks["overdue"]:
        add_toggle(f"\U0001f534 {len(tasks['overdue'])} overdue tasks", tasks["overdue"][:5])
    if tasks["due_today"]:
        for t in tasks["due_today"][:3]:
            add_bullet(f"\U0001f4cc {t}")

    add_divider()

    # ==================== SYSTEM (collapsed toggle, Decision 6) ====================
    disk_warn = " \u26a0\ufe0f" if isinstance(system['disk_pct'], int) and system['disk_pct'] >= 80 else ""
    mem_warn = " \u26a0\ufe0f" if isinstance(system['mem_pct'], int) and system['mem_pct'] >= 85 else ""
    disabled_str = f" ({system['cron_disabled']} off)" if system.get("cron_disabled") else ""
    gw_icon = "\U0001f7e2" if system.get("gateway") == "UP" else "\U0001f534"
    sys_has_issues = disk_warn or mem_warn or system.get("gateway") != "UP"

    sys_summary = f"\u2699\ufe0f Systems {gw_icon} | Disk {system['disk_pct']}%{disk_warn} | Mem {system['mem_pct']}%{mem_warn} | Up {system['uptime']} | Crons {system['cron_enabled']}/{system['cron_total']}{disabled_str}"
    if sys_has_issues:
        add_heading("\u2699\ufe0f System")
        add_para(sys_summary)
    else:
        add_toggle(sys_summary, ["All systems nominal"])

    add_divider()

    # ==================== GITHUB DISCOVERY (always collapsed, bottom) ====================
    if github_discovery and github_discovery.get("repos"):
        repos = github_discovery["repos"]
        age = " (yesterday)" if github_discovery.get("date") != datetime.now(cairo).strftime("%Y-%m-%d") else ""
        # Only show repos scoring 3+ (skip noise)
        relevant = [r for r in repos if r.get("relevance", 0) >= 3]
        all_items = []
        for r in repos[:8]:
            rel = r.get("relevance", 0)
            bar = "\U0001f7e2" if rel >= 6 else ("\U0001f7e1" if rel >= 3 else "\u26aa")
            text = f"{bar} [{rel}/10] {r.get('name', '?')} - {r.get('desc', '')[:45]}"
            if r.get("why"):
                text += f" \u2192 {r['why'][:35]}"
            if r.get("url"):
                text += f" | {r['url']}"
            all_items.append(text)
        relevant_count = len(relevant)
        label = f"\U0001f52d {len(repos)} GitHub discoveries ({relevant_count} relevant){age}"
        add_toggle(label, all_items or ["No repos found"])
        add_divider()


    # Create page
    log(f"  Creating Notion page with {len(blocks)} blocks...")

    # Notion API only accepts 100 blocks per append
    # Compute property values
    total_found = scanner_meta.get("total_found", 0) if scanner_meta else 0
    picks_count = len(qualified) if qualified else 0
    email_count = len(emails) if emails else 0
    cal_count = len(events) if events else 0
    gw = system.get("gateway", "?")
    disk = system.get("disk_pct", "?")
    health_status = "🟢 Healthy" if gw == "UP" and (not isinstance(disk, int) or disk < 80) else "🟡 Warning" if gw == "UP" else "🔴 Down"

    import time as _time
    gen_time = int(_time.time() - _start_time) if '_start_time' in dir() else None

    page_body = {
        "parent": {"database_id": "3268d599-a162-812d-a59e-e5496dec80e7"},
        "properties": {
            "Name": {"title": rt(f"Briefing {date_str}")},
            "Date": {"date": {"start": date_str}},
            "Jobs Found": {"number": total_found},
            "Priority Picks": {"number": picks_count},
            "Emails Flagged": {"number": email_count},
            "Calendar Events": {"number": cal_count},
            "System Health": {"select": {"name": health_status}},
            "Status": {"select": {"name": "✅ Delivered"}},
            "Model Used": {"rich_text": rt("orchestrator-v2")},
            "Interviews": {"number": p.get("interviews", 0)},
            "Actions": {"number": len(actions)},
            "Stale Count": {"number": p.get("stale", 0)},
        },
        "children": blocks[:100]
    }
    if gen_time is not None:
        page_body["properties"]["Generation Time (s)"] = {"number": gen_time}

    try:
        page = notion_req('POST', '/pages', page_body)
        page_id = page['id']
        page_url = page.get('url', f"https://www.notion.so/{page_id.replace('-','')}")

        # Append remaining blocks if any
        if len(blocks) > 100:
            _time.sleep(0.5)
            notion_req('PATCH', f'/blocks/{page_id}/children', {"children": blocks[100:]})

        log(f"  Notion page created: {page_url}")
        return page_url
    except Exception as e:
        log(f"  Notion page creation failed: {e}")
        # Decision 8: Local fallback on failure
        fallback_path = f"/tmp/briefing-fallback-{date_str}.json"
        try:
            with open(fallback_path, "w") as fb:
                json.dump({"date": date_str, "blocks": blocks, "properties": {k: str(v) for k, v in page_body.get("properties", {}).items()}}, fb, default=str)
            log(f"  Fallback saved: {fallback_path}")
            return f"FALLBACK:{fallback_path}"
        except Exception as fb_err:
            log(f"  Fallback save also failed: {fb_err}")
            return None


# ============================================================
# OUTPUT: TELEGRAM MESSAGE
# ============================================================

def build_telegram_message(date_display, pipeline, scanner_meta, qualified, borderline,
                           scanner_age, emails, email_error, events, cal_error, content_cal, github_discovery,
                           system, tasks, notion_changes, trends, notion_url, cross_refs=None):
    """Build compact Telegram nudge. Telegram = nudge, Notion = full briefing."""
    p = pipeline
    lines = []

    # Date header
    short_date = datetime.now(cairo).strftime("%a %b %d")
    lines.append(f"☀️ Brief - {short_date}")

    # Urgent line (most important signal)
    urgent_parts = []
    if p["interviews"]:
        urgent_parts.append(f"{p['interviews']} interview(s) active")
    # Stale follow-ups removed - LinkedIn applications have no direct follow-up channel
    action_emails = [e for e in emails if e.get("priority") == "action"]
    if action_emails:
        urgent_parts.append(f"{len(action_emails)} email(s) need reply")
    if tasks.get("overdue"):
        urgent_parts.append(f"{len(tasks['overdue'])} overdue tasks")
    if isinstance(system.get('disk_pct'), int) and system['disk_pct'] >= 80:
        urgent_parts.append(f"disk {system['disk_pct']}%")

    if urgent_parts:
        lines.append("🔴 " + ", ".join(urgent_parts))
    else:
        lines.append("✅ No urgent items")

    # Jobs line
    if qualified:
        apply_jobs = [j for j in qualified if j.get("career_verdict") == "APPLY" or (not j.get("career_verdict") and j.get("ats_score", 0) >= 50)]
        if apply_jobs:
            apply_jobs.sort(key=lambda x: (x.get("career_fit", 0), x.get("ats_score", 0)), reverse=True)
            top = apply_jobs[0]
            top_str = f"{top.get('title', '?')[:30]}"
            top_co = top.get("company", "")
            if top_co:
                top_str += f", {top_co[:15]}"
            _sm2 = scanner_meta or {}
            _fits_searches = _sm2.get("total_searches", "?")
            _fits_countries = len(_sm2.get("countries", []))
            lines.append(f"🔍 {len(apply_jobs)} new fits | {_sm2.get('total_found','?')} scanned | {_fits_searches} queries | {_fits_countries} countries (top: {top_str})")
        else:
            lines.append("🔍 No new fits today")
    elif scanner_meta:
        _sm_total = scanner_meta.get("total_found", 0)
        _sm_searches = scanner_meta.get("total_searches", 0)
        _sm_countries = scanner_meta.get("countries", [])
        _sm_src_status = scanner_meta.get("source_status", {})
        _bad_sources = [n for n, s in _sm_src_status.items() if "✅" not in str(s)] if _sm_src_status else []
        _src_health = f" ⚠️ {', '.join(_bad_sources)} down" if _bad_sources else ""
        lines.append(f"🔍 {_sm_total} scanned | {_sm_searches} queries | {len(_sm_countries)} countries{_src_health} | no new fits")
    else:
        lines.append("🔍 No scanner data")

    # Pipeline snapshot - applied to date + interviews
    _applied_to_date = p.get("applied", 0) + p.get("interviews", 0)
    lines.append(f"📊 Pipeline: {p['total_applications']} tracked | {_applied_to_date} applied | {p['interviews']} interviews")

    # Email line
    if emails:
        lines.append(f"📧 {len(emails)} job emails" + (f" ({len(action_emails)} need reply)" if action_emails else ""))
    elif email_error:
        lines.append(f"📧 ⚠️ {email_error[:25]}")

    # Calendar (only if events exist)
    if events:
        lines.append(f"📅 {len(events)} events today")
    elif cal_error:
        lines.append(f"📅 ⚠️ Calendar error")

    # Content (only if actionable)
    if content_cal and content_cal.get("today_post") and content_cal["today_post"]["status"] != "Posted":
        tp_title = content_cal['today_post']['title'][:25]
        lines.append(f'📝 Post ready: "{tp_title}"')

    # Cross-reference alerts (high-value signals)
    if cross_refs:
        lines.append("")
        for cr in cross_refs[:3]:
            lines.append(f"🔗 {cr}")

    # Notion link (the real briefing)
    if notion_url and notion_url.startswith("FALLBACK:"):
        lines.append(f"\n\u26a0\ufe0f Notion failed - briefing saved locally ({notion_url.split(':',1)[1]})")
    elif notion_url:
        lines.append(f"\n\U0001f449 [Full briefing in Notion]({notion_url})")

    return "\n".join(lines)

# ============================================================
# OUTPUT: DASHBOARD UPDATE
# ============================================================

def update_dashboard(pipeline):
    """Update Dashboard KPI and Stale Alerts blocks."""
    try:
        sys.path.insert(0, f"{WORKSPACE}/scripts")
        from notion_sync import compute_stale_alerts, update_stale_alerts
        alerts = compute_stale_alerts()
        update_stale_alerts(alerts)
        log(f"  Dashboard stale alerts updated: {len(alerts)} items")
    except Exception as e:
        log(f"  Dashboard update error: {e}")


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--date", help="Override date (YYYY-MM-DD)")
    args = parser.parse_args()

    now = datetime.now(cairo)
    today_str = args.date or now.strftime("%Y-%m-%d")
    date_display = now.strftime("%A, %B %d, %Y")

    log("=== Morning Briefing v2 ===")
    log(f"Date: {date_display}")
    log("")

    # ---- STEP 0: ONTOLOGY GRAPH SYNC ----
    log("Step 0: Syncing ontology knowledge graph...")
    try:
        import importlib.util as _ilu, sys as _sys
        _sys.path.insert(0, f"{WORKSPACE}/scripts")
        # Content calendar sync
        from ontology_notion_sync import sync as _content_sync
        _cr = _content_sync()
        log(f"  Content posts: {_cr.get('new', 0)} new | {_cr.get('updated', 0)} updated")
        # Job pipeline sync
        from ontology_pipeline_sync import sync as _pipeline_sync
        _pr = _pipeline_sync()
        log(f"  Job pipeline: {_pr.get('new_jobs', 0)} new | {_pr.get('updated', 0)} updated | {_pr.get('new_orgs', 0)} new orgs")
    except Exception as _e:
        log(f"  ⚠️ Ontology sync skipped: {_e}")

    # ---- GATHER ALL DATA (pure Python, no LLM) ----

    # 1. Pipeline
    log("Step 1: Reading pipeline...")
    pipeline = read_pipeline()
    log(f"  {pipeline['total_applications']} total, {pipeline['interviews']} interviews, {pipeline['stale']} stale")

    # 2. Scanner
    log("Step 2: Loading scanner data...")
    scanner_meta, qualified, borderline, scanner_age = load_scanner_data(today_str)
    log(f"  {len(qualified)} qualified, {len(borderline)} borderline, age: {scanner_age}d")

    # 2b. Dedup: remove jobs already in pipeline (LIVE from Notion Pipeline DB)
    log("Step 2b: Dedup scanner picks against Notion Pipeline DB...")
    if qualified:
        applied_urls, applied_keys, notion_total, applied_companies = fetch_notion_pipeline_for_dedup()

        # Log high-frequency companies
        heavy_companies = {c: d for c, d in applied_companies.items() if d["count"] >= 3}
        if heavy_companies:
            _hc_parts = [f"{c}({d['count']}x)" for c, d in sorted(heavy_companies.items(), key=lambda x: -x[1]["count"])[:10]]
            log(f"  ⚠️ High-frequency companies (3+ applications): {', '.join(_hc_parts)}")

        # Fallback to pipeline.md ONLY if Notion query returned nothing
        if notion_total == 0 and os.path.exists(PIPELINE_FILE):
            log("  Fallback: reading pipeline.md for dedup...")
            with open(PIPELINE_FILE) as pf:
                for pline in pf:
                    pline = pline.strip()
                    if not pline.startswith("|") or pline.startswith("| #") or pline.startswith("|---"):
                        continue
                    pcols = [c.strip().replace("~~","") for c in pline.split("|") if c.strip()]
                    if len(pcols) < 7:
                        continue
                    try:
                        int(pcols[0])
                    except:
                        continue
                    p_company = pcols[2].strip().lower()
                    p_role = pcols[3].strip().lower() if len(pcols) > 3 else ""
                    p_url = pcols[10].strip() if len(pcols) > 10 else ""
                    url_match = re.search(r'/view/(\d+)', p_url)
                    if url_match:
                        applied_urls.add(url_match.group(1))
                    if p_company and p_role:
                        applied_keys.add(f"{p_company}|{p_role}")

        before_count = len(qualified)
        deduped = []
        removed = []
        for job in qualified:
            job_url = job.get("url", "")
            job_id_match = re.search(r'/view/(\d+)', job_url)
            is_dup = False

            # Check URL match (most reliable)
            if job_id_match and job_id_match.group(1) in applied_urls:
                is_dup = True

            # Check company+role fuzzy match
            if not is_dup:
                j_company = job.get("company", "").strip().lower()
                j_title = job.get("title", "").strip().lower()
                for akey in applied_keys:
                    a_comp, a_role = akey.split("|", 1)
                    if j_company and a_comp and (j_company in a_comp or a_comp in j_company):
                        # Company matches - check role similarity
                        title_words = set(w for w in j_title.split() if len(w) > 3)
                        role_words = set(w for w in a_role.split() if len(w) > 3)
                        if title_words & role_words:
                            is_dup = True
                            break

            # Check company saturation (3+ existing applications = flag it)
            company_app_count = 0
            if not is_dup:
                j_company = job.get("company", "").strip().lower()
                for comp_key, comp_data in applied_companies.items():
                    if j_company and comp_key and (j_company in comp_key or comp_key in j_company):
                        company_app_count = comp_data["count"]
                        if company_app_count >= 3:
                            is_dup = True
                            break

            if is_dup:
                reason = f"{job.get('title','')} @ {job.get('company','')}"
                if company_app_count >= 3:
                    reason += f" (company saturated: {company_app_count}x applied)"
                removed.append(reason)
            else:
                deduped.append(job)

        qualified = deduped
        if removed:
            log(f"  Removed {len(removed)} already-applied jobs: {', '.join(removed[:5])}")
        log(f"  {before_count} -> {len(qualified)} after dedup")

    # 3. Email
    log("Step 3: Checking email...")
    emails, email_error = check_email()
    log(f"  {len(emails)} job emails" + (f" (error: {email_error})" if email_error else ""))

    # 4. Calendar
    log("Step 4: Checking calendar...")
    events, cal_error = check_calendar()
    log(f"  {len(events)} events" + (f" (error: {cal_error})" if cal_error else ""))

    # 5. Content Calendar
    log("Step 5: Content calendar...")
    content_cal = get_content_calendar()
    if content_cal is None:
        content_cal = {"scheduled": 0, "drafted": 0, "posted": 0, "ideas": 0, "today_post": None,
                       "tomorrow_post": None, "next_scheduled": None, "gap_days": 0}
        log("  ⚠️ Content calendar returned None - using defaults")
    log(f"  Posted: {content_cal['posted']}, Scheduled: {content_cal['scheduled']}, Drafted: {content_cal['drafted']}")

    # 6. System Health
    log("Step 6: System health...")
    system = get_system_health()
    log(f"  GW: {system['gateway']}, Disk: {system['disk_pct']}%, Mem: {system['mem_pct']}%, Crons: {system['cron_enabled']}/{system['cron_total']}")

    # 7. Active Tasks
    log("Step 7: Active tasks...")
    tasks = get_active_tasks()
    log(f"  {tasks['total_open']} open, {len(tasks['overdue'])} overdue, {len(tasks['due_today'])} due today")

    # 8. Scanner Trends
    log("Step 8: Scanner trends...")
    trends = get_scanner_trends()

    # 8b. GitHub Discovery
    log("Step 8b: GitHub discovery...")
    github_discovery = get_github_discovery()
    log(f"  {github_discovery['count']} repos found")

    # 9. Two-way sync
    log("Step 9: Two-way Notion sync...")
    notion_changes = notion_two_way_sync()

    # 10. Cross-reference intelligence
    log("Step 10: Cross-referencing data sources...")
    cross_refs = cross_reference(pipeline, emails, events, qualified)
    if cross_refs:
        for cr in cross_refs:
            log(f"  🔗 {cr}")
    else:
        log("  No cross-references found")

    log("")
    log("=== DATA COMPLETE - Building outputs ===")
    log("")

    # ---- OUTPUT 1: NOTION PAGE ----
    log("Output 1: Notion page...")
    notion_url = None
    if not args.dry_run:
        notion_url = create_notion_briefing(
            today_str, date_display, pipeline, scanner_meta, qualified, borderline,
            scanner_age, emails, email_error, events, cal_error, content_cal,
            system, tasks, notion_changes, trends, github_discovery, cross_refs
        )
    else:
        log("  (dry-run - skipped)")
    log("")

    # ---- OUTPUT 2: TELEGRAM MESSAGE ----
    log("Output 2: Telegram message...")
    telegram_msg = build_telegram_message(
        date_display, pipeline, scanner_meta, qualified, borderline,
        scanner_age, emails, email_error, events, cal_error, content_cal, github_discovery,
        system, tasks, notion_changes, trends, notion_url, cross_refs
    )

    # Save to file for the cron to pick up and deliver
    telegram_file = f"/tmp/briefing-telegram-{today_str}.txt"
    with open(telegram_file, "w") as f:
        f.write(telegram_msg)
    log(f"  Saved to {telegram_file}")

    # Print for cron delivery
    print(f"\n{telegram_msg}\n")
    log("")

    # ---- OUTPUT 3: DASHBOARD UPDATE ----
    log("Output 3: Dashboard update...")
    if not args.dry_run:
        update_dashboard(pipeline)
    log("")

    # ---- COST LOGGING ----
    elapsed = int((datetime.now(cairo) - now).total_seconds())
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("cost_logger", "/root/.openclaw/workspace/scripts/cost_logger.py")
        cl = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cl)
        cl.log_cost(
            session_name=f"Morning Briefing ({today_str})",
            model="MiniMax-M2.5",
            agent="Morning Briefing",
            duration=elapsed,
            status="success",
            notes=f"Picks: {len(qualified)}, Emails: {len(emails)}, Pipeline: {pipeline['total_applications']}"
        )
    except Exception as e:
        log(f"Cost logging failed (non-fatal): {e}")

    # ---- DISPATCH TO THREADS ----
    try:
        import subprocess
        dispatch_script = os.path.join(WORKSPACE, "scripts", "briefing-thread-dispatch.py")
        if os.path.exists(dispatch_script):
            result = subprocess.run(
                ["python3", dispatch_script, today_str],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                log("Thread dispatch: OK")
            else:
                log(f"Thread dispatch failed: {result.stderr[:200]}")
    except Exception as e:
        log(f"Thread dispatch error (non-fatal): {e}")

    # ---- SMOKE TEST ----
    log("Smoke test...")
    smoke_errors = []
    if not telegram_msg or len(telegram_msg) < 50:
        smoke_errors.append("Telegram message too short or empty")
    required_sections = ["Pipeline", "Brief"]
    for section in required_sections:
        if section.lower() not in telegram_msg.lower():
            smoke_errors.append(f"Missing section: {section}")
    if not args.dry_run and not notion_url:
        smoke_errors.append("Notion page was not created")
    if smoke_errors:
        log(f"⚠️ SMOKE TEST FAILED: {'; '.join(smoke_errors)}")
        sys.exit(1)
    else:
        log("Smoke test: PASSED")

    # ---- DONE ----
    log("=== COMPLETE ===")
    log(f"Notion: {notion_url or 'skipped'}")
    log(f"Telegram: {len(telegram_msg)} chars")
    log(f"Blocks: {len(qualified)} picks, {pipeline['interviews']} interviews, {len(emails)} emails")
    log(f"Duration: {elapsed}s")


if __name__ == "__main__":
    main()
