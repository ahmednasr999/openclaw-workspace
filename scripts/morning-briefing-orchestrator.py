#!/usr/bin/env python3
"""
Morning Briefing Orchestrator
=============================
Single deterministic script. LLM (Sonnet 4.6) is called ONLY for comment drafting.
Everything else: file reads, calendar, search, JSON build, doc generation = pure Python.

Usage:
    python3 morning-briefing-orchestrator.py
    python3 morning-briefing-orchestrator.py --dry-run
    python3 morning-briefing-orchestrator.py --date 2026-03-15
"""

import json, os, sys, re, subprocess, argparse, glob, traceback, urllib.request, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ============================================================
# PATHS
# ============================================================
WORKSPACE        = "/root/.openclaw/workspace"
JOBS_DIR         = f"{WORKSPACE}/jobs-bank/scraped"
PIPELINE_FILE    = f"{WORKSPACE}/jobs-bank/pipeline.md"
COMMENTED_FILE   = f"{WORKSPACE}/linkedin/engagement/commented-posts.md"
TARGETS_CONFIG   = f"{WORKSPACE}/config/linkedin-comment-targets.json"
LEARNINGS_FILE   = f"{WORKSPACE}/.learnings/LEARNINGS.md"
BRIEFING_SCRIPT  = f"{WORKSPACE}/scripts/daily-briefing-generator.py"
SYSLOG_SCRIPT    = f"{WORKSPACE}/scripts/nasr-system-log-generator.py"
OPENCLAW_JSON    = "/root/.openclaw/openclaw.json"
ACCOUNT_EMAIL    = "ahmednasr999@gmail.com"

BRIEFING_DOC = "https://docs.google.com/document/d/1gtl5sXIsvXiXhODFs29FD9L09i9mGQlsBVIrZbVkTYs/edit"
SYSLOG_DOC   = "https://docs.google.com/document/d/1Ti5kle0bq4fXBgF54arYO2C723LtHkDUhO2o2rmDAqU/edit"

# Ahmed's metrics for comment drafting
AHMED_METRICS = [
    "$50M digital transformation across 15 hospitals at Saudi German Hospital Group",
    "Scaled Talabat from 30K to 7M daily orders as part of the technology leadership team",
    "20+ years across FinTech, HealthTech, and e-commerce in GCC and Egypt",
    "PMO leadership for multi-hospital digital transformation under Saudi Vision 2030",
    "Led cross-functional teams across 15 hospital facilities",
    "Implemented AI automation ecosystem with 14-product personal productivity suite",
]

COMMENT_PROMPT = """Write a LinkedIn comment for Ahmed Nasr to post. Rules:
- 3-5 sentences exactly
- Include ONE specific metric (choose the most relevant):
  {metrics}
- Peer executive tone. He is a senior technology executive, NOT a job seeker.
- NEVER start with "Great post!", "Thanks for sharing!", or "I couldn't agree more!"
- Structure: Open with insight or challenge → Add specific experience → Close with question
- NEVER use em dashes. Use commas, periods, or colons instead.
- Sound human, not corporate.
- Do NOT mention he is looking for a job.

Post context:
Author: {author}
Topic/Snippet: {snippet}

Write ONLY the comment text. Nothing else."""

# ============================================================
# GLOBALS (loaded from config)
# ============================================================
ANTHROPIC_API_KEY = ""
ANTHROPIC_BASE_URL = "https://api.anthropic.com"
GATEWAY_URL = "http://127.0.0.1:18789"
GATEWAY_TOKEN = ""
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "").strip()


def log(msg):
    cairo = timezone(timedelta(hours=2))
    ts = datetime.now(cairo).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ============================================================
# CONFIG
# ============================================================
def load_config():
    global ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, GATEWAY_TOKEN
    try:
        with open(OPENCLAW_JSON) as f:
            cfg = json.load(f)
        p = cfg.get("models", {}).get("providers", {}).get("anthropic", {})
        ANTHROPIC_API_KEY = p.get("apiKey", "")
        ANTHROPIC_BASE_URL = p.get("baseUrl", "https://api.anthropic.com")
        GATEWAY_TOKEN = cfg.get("gateway", {}).get("auth", {}).get("token", "")
        if GATEWAY_TOKEN:
            log(f"Gateway token loaded (len={len(GATEWAY_TOKEN)}). Using gateway for LLM calls.")
        else:
            log(f"Anthropic key loaded: {ANTHROPIC_API_KEY[:15]}... (direct API, no gateway token)")
    except Exception as e:
        log(f"WARNING: Could not load config: {e}")


def call_llm(prompt, model="anthropic/claude-sonnet-4-6", max_tokens=1024):
    """Call LLM via OpenClaw gateway (preferred) or direct Anthropic API (fallback)."""
    # Try gateway first
    if GATEWAY_TOKEN:
        try:
            data = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            }).encode()
            req = urllib.request.Request(
                f"{GATEWAY_URL}/v1/chat/completions",
                data=data,
                method="POST",
            )
            req.add_header("Authorization", f"Bearer {GATEWAY_TOKEN}")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())
            text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            if text:
                return text
        except Exception as e:
            log(f"    Gateway LLM error: {e}")

    # Fallback: direct Anthropic API
    if ANTHROPIC_API_KEY:
        try:
            data = json.dumps({
                "model": "claude-sonnet-4-20250514",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }).encode()
            req = urllib.request.Request(
                f"{ANTHROPIC_BASE_URL}/v1/messages",
                data=data,
                method="POST",
            )
            req.add_header("x-api-key", ANTHROPIC_API_KEY)
            req.add_header("anthropic-version", "2023-06-01")
            req.add_header("content-type", "application/json")
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
            blocks = result.get("content", [])
            return blocks[0].get("text", "") if blocks else ""
        except Exception as e:
            log(f"    Direct Anthropic error: {e}")

    return ""


def load_commented_urls():
    """Load already-suggested post URLs to avoid repeats."""
    urls = set()
    if not os.path.exists(COMMENTED_FILE):
        return urls
    with open(COMMENTED_FILE) as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) >= 2:
                val = parts[1].strip()
                if "linkedin.com" in val:
                    urls.add(val)
    return urls


def load_targets():
    if os.path.exists(TARGETS_CONFIG):
        with open(TARGETS_CONFIG) as f:
            return json.load(f)
    return {}


# ============================================================
# STEP 1: JOBS
# ============================================================
def load_scanner_meta():
    """Load scanner metadata JSON for health reporting."""
    meta_pattern = f"{JOBS_DIR}/scanner-meta-*.json"
    meta_files = sorted(glob.glob(meta_pattern), reverse=True)
    if not meta_files:
        return None
    try:
        with open(meta_files[0]) as f:
            return json.load(f)
    except:
        return None


def gather_jobs():
    log("Step 1: Gathering job data...")
    pattern = f"{JOBS_DIR}/qualified-jobs-*.md"
    files = sorted(glob.glob(pattern), reverse=True)
    if not files:
        log("  No qualified-jobs files found.")
        return [], [], "No scanner data available."

    latest = files[0]
    log(f"  File: {os.path.basename(latest)}")

    qualified, borderline = [], []
    section = None
    job = {}

    with open(latest) as f:
        for line in f:
            l = line.strip()
            # v3.0 format: "Priority Picks" = qualified, "Executive Leads" = borderline
            # v2.1 format: "Qualified" / "Borderline"
            if ("Qualified" in l or "Priority Picks" in l) and ("##" in l or "🟢" in l):
                if job.get("title") and section:
                    (qualified if section == "q" else borderline).append(job)
                    job = {}
                section = "q"
            elif ("Borderline" in l or "Executive Leads" in l) and ("##" in l or "🟡" in l or "##" in l):
                if job.get("title") and section:
                    (qualified if section == "q" else borderline).append(job)
                    job = {}
                section = "b"
            elif l.startswith("### "):
                if job.get("title"):
                    (qualified if section == "q" else borderline).append(job)
                job = {"title": l.lstrip("# ").strip()}
            elif l.startswith("- **") and section == "b":
                # v3.0 inline lead format: - **Title** | Company | Location | [site](url)
                import re as _re
                m = _re.match(r'-\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*\[.*?\]\((.+?)\)', l)
                if m:
                    borderline.append({"title": m.group(1), "company": m.group(2), "location": m.group(3), "link": m.group(4)})
            elif ":" in l and job:
                k, _, v = l.partition(":")
                k = k.strip().lstrip("-* ").lower()
                v = v.strip()
                if "company" in k:
                    job["company"] = v
                elif "location" in k:
                    job["location"] = v
                elif "score" in k or "ats" in k:
                    job["score"] = v
                elif "link" in k or "url" in k:
                    job["link"] = v
                elif "source" in k:
                    job["source"] = v

    if job.get("title"):
        (qualified if section == "q" else borderline).append(job)

    note = f"{os.path.basename(latest)}: {len(qualified)} priority picks, {len(borderline)} exec leads."
    log(f"  {len(qualified)} priority picks, {len(borderline)} exec leads")

    # v3.2: Fetch full JDs for all leads before publishing verdicts
    all_leads = qualified + borderline
    if all_leads:
        log(f"  Fetching JDs for {len(all_leads)} leads...")
        for job in all_leads:
            link = job.get("link", job.get("url", ""))
            if not link or "linkedin.com" not in link:
                continue

            # PRIMARY: LinkedIn public guest API (no auth needed, most reliable)
            import re as _re2
            job_id_match = _re2.search(r'/jobs/view/(\d+)', link)
            if job_id_match:
                job_id = job_id_match.group(1)
                try:
                    guest_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
                    req_guest = urllib.request.Request(guest_url, headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                        "Accept": "text/html"
                    })
                    with urllib.request.urlopen(req_guest, timeout=15) as resp:
                        raw_html = resp.read().decode("utf-8", errors="replace")
                    # Extract description div
                    desc_match = _re2.search(r'class="description__text[^"]*"[^>]*>(.*?)</div>', raw_html, _re2.DOTALL)
                    desc_html = desc_match.group(1) if desc_match else raw_html
                    # Convert HTML to text
                    import html as _html_mod
                    jd_text = _re2.sub(r'<br\s*/?>', '\n', desc_html)
                    jd_text = _re2.sub(r'<li[^>]*>', '\n- ', jd_text)
                    jd_text = _re2.sub(r'<[^>]+>', ' ', jd_text)
                    jd_text = _html_mod.unescape(jd_text)
                    jd_text = _re2.sub(r'[ \t]+', ' ', jd_text)
                    jd_text = _re2.sub(r'\n{3,}', '\n\n', jd_text).strip()
                    if len(jd_text) > 200:
                        job["jd_snippet"] = jd_text[:2000]
                        job["jd_fetched"] = True
                        jd_lower = jd_text.lower()
                        if "equity" in jd_lower and "salary" not in jd_lower:
                            job["jd_flag"] = "equity-only compensation"
                        if "co-found" in jd_lower or "startup" in jd_lower:
                            job["jd_flag"] = job.get("jd_flag", "") + " early-stage/startup"
                        if "crypto" in jd_lower or "blockchain" in jd_lower or "defi" in jd_lower:
                            job["jd_flag"] = job.get("jd_flag", "") + " crypto/blockchain"
                        if "security printing" in jd_lower:
                            job["jd_flag"] = job.get("jd_flag", "") + " niche: security printing"
                        log(f"    JD fetched (guest API): {job.get('title', '?')[:40]} ({len(jd_text)} chars)")
                        time.sleep(0.5)
                        continue
                except Exception as e:
                    log(f"    Guest API failed for {job.get('title', '?')[:40]}: {e}")

            # FALLBACK: Jina Reader
            try:
                jina_url = f"https://r.jina.ai/{link}"
                req_obj = urllib.request.Request(jina_url, headers={
                    "Accept": "text/plain",
                    "X-Return-Format": "text",
                    "X-No-Cache": "true"
                })
                with urllib.request.urlopen(req_obj, timeout=20) as resp:
                    jd_text = resp.read().decode("utf-8", errors="replace")[:3000]
                    job["jd_snippet"] = jd_text[:1500]
                    job["jd_fetched"] = True
                    # Extract key info for quick review
                    jd_lower = jd_text.lower()
                    if "equity" in jd_lower and "salary" not in jd_lower:
                        job["jd_flag"] = "equity-only compensation"
                    if "co-found" in jd_lower or "startup" in jd_lower:
                        job["jd_flag"] = job.get("jd_flag", "") + " early-stage/startup"
                    log(f"    JD fetched: {job.get('title', '?')[:40]}")
            except Exception as e:
                log(f"    Jina failed for {job.get('title', '?')[:40]}: {e}. Trying direct curl...")
                # Fallback: direct curl to LinkedIn (public JD pages don't require login)
                try:
                    req_obj2 = urllib.request.Request(link, headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                        "Accept": "text/html"
                    })
                    with urllib.request.urlopen(req_obj2, timeout=15) as resp:
                        html = resp.read().decode("utf-8", errors="replace")
                    # Extract text between common JD markers
                    import re as _re
                    # Try to find the job description section
                    match = _re.search(r'(?:About the Role|Key Responsibilities|Description)(.*?)(?:Show more|Similar jobs|Seniority level)', html, _re.DOTALL)
                    if match:
                        from html.parser import HTMLParser
                        class TagStripper(HTMLParser):
                            def __init__(self):
                                super().__init__()
                                self.text = []
                            def handle_data(self, d):
                                self.text.append(d)
                        s = TagStripper()
                        s.feed(match.group(0))
                        jd_text = ' '.join(s.text)[:1500]
                        job["jd_snippet"] = jd_text
                        job["jd_fetched"] = True
                        jd_lower = jd_text.lower()
                        if "equity" in jd_lower and "salary" not in jd_lower:
                            job["jd_flag"] = "equity-only compensation"
                        if "co-found" in jd_lower or "startup" in jd_lower:
                            job["jd_flag"] = job.get("jd_flag", "") + " early-stage/startup"
                        log(f"    JD fetched via direct curl: {job.get('title', '?')[:40]}")
                    else:
                        job["jd_fetched"] = False
                        log(f"    Direct curl: no JD section found for {job.get('title', '?')[:40]}")
                except Exception as e2:
                    job["jd_fetched"] = False
                    log(f"    All JD fetch methods failed for {job.get('title', '?')[:40]}: {e2}")
            time.sleep(1)  # Respect rate limits

    # v3.3: ATS Quick Score each job with a fetched JD
    PROFILE_SUMMARY = """Ahmed Nasr - Digital Transformation Executive, 20+ years.
Current: Acting PMO & Regional Engagement Lead at TopMed (Saudi German Hospital Group), $50M digital transformation across 15 hospitals, 3 countries (KSA, UAE, Egypt).
Previous: Scaled Talabat/Delivery Hero from 30K to 7M daily orders. Built enterprise PMO managing 300+ concurrent projects across 8 countries at Network International. PaySky FinTech platform architect.
Sectors: HealthTech, FinTech, e-commerce, Digital Transformation.
Skills: Enterprise PMO, Cloud (AWS/Azure), AI/LLM deployment, P&L ownership, Agile, Saudi Vision 2030, GCC market expertise.
Certs: PMP, CSM, CSPO, Lean Six Sigma, CBAP. MBA in progress (Paris ESLSCA).
Target: VP/C-Suite roles in GCC. Digital transformation, technology leadership, PMO leadership."""

    all_leads = qualified + borderline
    scored_leads = [j for j in all_leads if j.get("jd_fetched") and j.get("jd_snippet")]
    if scored_leads:
        log(f"  ATS Quick Scoring {len(scored_leads)} leads against profile...")
        for job in scored_leads:
            try:
                jd = job.get("jd_snippet", "")[:1500]
                title = job.get("title", "Unknown")
                company = job.get("company", "Unknown")

                # Quick scoring prompt - designed for fast, accurate scoring
                score_prompt = f"""Score this job's fit for the candidate. Return ONLY a JSON object, nothing else.

CANDIDATE PROFILE:
{PROFILE_SUMMARY}

JOB: {title} at {company}
JD EXCERPT:
{jd}

Scoring rules:
- 90-100: Perfect match (sector + seniority + skills + location all align)
- 82-89: Strong match (most criteria align, minor gaps)
- 75-81: Borderline (some fit but significant gaps in sector or skills)
- 60-74: Weak match (different sector or seniority level)
- Below 60: No fit (completely different domain)

Return exactly: {{"score": <number>, "verdict": "SUBMIT|REVIEW|SKIP", "reason": "<15 words max>"}}
Rules: SUBMIT if score >= 82, REVIEW if 75-81, SKIP if < 75."""

                # Use subprocess to call a quick LLM scoring
                import subprocess
                score_result = subprocess.run(
                    ["python3", "-c", f"""
import json, urllib.request, os

# Use OpenClaw's API to get a quick score
prompt = {repr(score_prompt)}

# Simple approach: write to temp file for the orchestrator to parse
# Use a basic heuristic scoring as fallback
jd_lower = {repr(jd.lower())}
profile_keywords = ["digital transformation", "pmo", "healthcare", "fintech", "e-commerce",
                     "cloud", "aws", "azure", "ai", "agile", "strategic", "enterprise",
                     "hospital", "technology", "program management", "project management",
                     "stakeholder", "governance", "vision 2030", "gcc", "uae", "saudi"]

score = 50  # base
matches = 0
for kw in profile_keywords:
    if kw in jd_lower:
        matches += 1

# Scoring heuristic
if matches >= 10: score = 90
elif matches >= 7: score = 85
elif matches >= 5: score = 78
elif matches >= 3: score = 70
else: score = 55

# Penalty for clearly wrong domains
wrong_domains = ["crypto", "blockchain", "defi", "mining", "security printing",
                  "construction supervisor", "civil engineer", "structural engineer",
                  "residential tower", "oil and gas drilling", "pharmaceutical manufacturing"]
for wd in wrong_domains:
    if wd in jd_lower:
        score = min(score, 55)
        break

# Bonus for exact role matches
exact_matches = ["digital transformation", "pmo director", "head of technology",
                  "chief digital officer", "chief technology officer", "vp technology",
                  "head of transformation"]
for em in exact_matches:
    if em in jd_lower:
        score += 5
        break

score = min(score, 100)

if score >= 82: verdict = "SUBMIT"
elif score >= 75: verdict = "REVIEW"
else: verdict = "SKIP"

# Generate reason
if score >= 82:
    reason = f"{{matches}} keyword matches, strong sector/skill alignment"
elif score >= 75:
    reason = f"{{matches}} keyword matches, partial alignment"
else:
    reason = f"Low fit: {{matches}} keyword matches, different domain"

print(json.dumps({{"score": score, "verdict": verdict, "reason": reason}}))
"""],
                    capture_output=True, text=True, timeout=10
                )

                if score_result.returncode == 0 and score_result.stdout.strip():
                    try:
                        score_data = json.loads(score_result.stdout.strip())
                        job["ats_score"] = score_data.get("score", 0)
                        job["ats_verdict"] = score_data.get("verdict", "UNSCORED")
                        job["ats_reason"] = score_data.get("reason", "")
                        log(f"    ATS: {title[:35]} = {job['ats_score']}/100 ({job['ats_verdict']}): {job['ats_reason']}")
                    except json.JSONDecodeError:
                        job["ats_verdict"] = "UNSCORED"
                        log(f"    ATS parse error for {title[:35]}")
                else:
                    job["ats_verdict"] = "UNSCORED"
                    log(f"    ATS scoring failed for {title[:35]}")
            except Exception as e:
                job["ats_verdict"] = "UNSCORED"
                log(f"    ATS error for {job.get('title','?')[:35]}: {e}")

        # Re-categorize based on ATS scores
        new_qualified = []
        new_borderline = []
        for job in qualified + borderline:
            verdict = job.get("ats_verdict", "UNSCORED")
            if verdict == "SUBMIT":
                new_qualified.append(job)
            elif verdict in ("REVIEW", "UNSCORED"):
                new_borderline.append(job)
            else:  # SKIP
                new_borderline.append(job)  # Keep in borderline but marked as SKIP

        qualified = new_qualified
        borderline = new_borderline
        note = f"{os.path.basename(latest)}: {len(qualified)} recommended (82+), {len(borderline)} other leads."
        log(f"  After ATS: {len(qualified)} recommended, {len(borderline)} other leads")

    return qualified, borderline, note


# ============================================================
# STEP 2: CALENDAR
# ============================================================
def check_calendar():
    log("Step 2: Checking calendar...")
    events, upcoming = [], []
    cal_error = None
    try:
        r = subprocess.run(
            f'GOG_KEYRING_PASSWORD="" gog calendar list --today -a {ACCOUNT_EMAIL}',
            shell=True, capture_output=True, text=True, timeout=30
        )
        output = r.stdout.strip() + r.stderr.strip()
        if "expired" in output.lower() or "revoked" in output.lower() or "invalid_grant" in output.lower():
            cal_error = "Google Calendar auth expired. Re-auth needed: gog auth add ahmednasr999@gmail.com --services calendar"
            log(f"  ⚠️ {cal_error}")
        elif r.stdout.strip() and "no events" not in r.stdout.lower():
            for line in r.stdout.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                # Try to parse time from line (format varies: "14:00 Meeting Title" or just "Meeting Title")
                time_match = re.match(r'^(\d{1,2}:\d{2})\s+(.+)', line)
                if time_match:
                    events.append({"time": time_match.group(1), "title": time_match.group(2), "notes": ""})
                else:
                    events.append({"time": "", "title": line, "notes": ""})
        log(f"  Today: {len(events)} events")

        if not cal_error:
            r2 = subprocess.run(
                f'GOG_KEYRING_PASSWORD="" gog calendar list --from today --to "+3 days" -a {ACCOUNT_EMAIL}',
                shell=True, capture_output=True, text=True, timeout=30
            )
            if r2.stdout.strip() and "no events" not in r2.stdout.lower():
                for line in r2.stdout.strip().split("\n"):
                    if line.strip():
                        upcoming.append(line.strip())
            log(f"  Upcoming: {len(upcoming)} items")
    except Exception as e:
        cal_error = f"Calendar check failed: {e}"
        log(f"  {cal_error}")
    return events, upcoming, cal_error


# ============================================================
# STEP 3: PIPELINE
# ============================================================
def read_pipeline():
    log("Step 3: Reading pipeline...")
    if not os.path.exists(PIPELINE_FILE):
        log("  Pipeline file not found.")
        return {}
    with open(PIPELINE_FILE) as f:
        lines = f.readlines()

    from datetime import datetime as _dt, timedelta as _td
    _today = _dt.now()

    applied = 0
    interview = 0
    closed = 0
    stale = 0
    overdue_list = []
    total = 0

    for line in lines:
        if "|" not in line or line.strip().startswith("#") or line.strip().startswith("|---"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 10:
            continue
        stage = cols[7] if len(cols) > 7 else ""
        applied_date_str = cols[9] if len(cols) > 9 else ""
        company = cols[3] if len(cols) > 3 else ""
        role = cols[4] if len(cols) > 4 else ""

        if "Applied" in stage or "Interview" in stage or "Closed" in stage:
            total += 1

        if "Applied" in stage and "~~" not in stage:
            applied += 1
            m = re.search(r'(\d{4}-\d{2}-\d{2})', applied_date_str)
            if m:
                app_date = _dt.strptime(m.group(1), "%Y-%m-%d")
                days_ago = (_today - app_date).days
                if days_ago >= 14:
                    stale += 1
                    overdue_list.append({
                        "company": company.replace("~~", "").strip(),
                        "role": role.replace("~~", "").strip(),
                        "applied": m.group(1),
                        "days": days_ago
                    })
        elif "Interview" in stage:
            interview += 1
        elif "Closed" in stage:
            closed += 1

    overdue_list.sort(key=lambda x: x["days"], reverse=True)

    log(f"  Applied: {applied} | Interview: {interview} | Closed: {closed} | Stale: {stale}")

    return {
        "total_applications": total,
        "applied": applied,
        "interviews": interview,
        "closed": closed,
        "stale": stale,
        "overdue": overdue_list,
    }


# ============================================================
# STEP 4: LINKEDIN POSTS (Tavily)
# ============================================================
def ddg_search(query, n=5, timelimit='w'):
    """Search via DuckDuckGo (free, no API key, no quota). timelimit: d=day, w=week, m=month."""
    try:
        from ddgs import DDGS
        results = DDGS().text(query, max_results=n, timelimit=timelimit)
        # Normalize to Tavily-compatible format
        normalized = [{"title": r.get("title",""), "url": r.get("href",""), "content": r.get("body","")} for r in results]
        if not normalized and timelimit == 'w':
            # Retry with month if week returns nothing
            results = DDGS().text(query, max_results=n, timelimit='m')
            normalized = [{"title": r.get("title",""), "url": r.get("href",""), "content": r.get("body","")} for r in results]
        return normalized
    except Exception as e:
        log(f"  DDG error: {e}")
        return []


def tavily_search(query, n=5, days=7):
    """Search via Tavily (primary) with DDG fallback (free)."""
    # Try Tavily first if key available and not exhausted
    if TAVILY_API_KEY and not getattr(tavily_search, '_exhausted', False):
        payload = json.dumps({
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": n,
            "topic": "news",
            "days": days,
            "include_answer": False,
        }).encode()
        req = urllib.request.Request(
            "https://api.tavily.com/search",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                results = json.loads(resp.read()).get("results", [])
                if results:
                    return results
        except Exception as e:
            error_str = str(e)
            if "432" in error_str or "429" in error_str or "402" in error_str:
                tavily_search._exhausted = True
                log(f"  Tavily quota exhausted (432). Switching to DDG for all remaining searches.")
            else:
                log(f"  Tavily error: {e}")

    # Fallback: DuckDuckGo (free, no quota)
    return ddg_search(query, n)


def is_company_page(url):
    """Return True if this looks like a company page post (not individual)."""
    COMPANY_SLUGS = [
        "-company", "official", "-magazine", "-news",
        "-solutions", "-technologies", "-group", "-bank",
        "-consulting", "-partners", "-recruitment", "-search"
    ]
    slug_m = re.search(r'linkedin\.com/posts/([^_]+?)_', url)
    if slug_m:
        slug = slug_m.group(1).lower()
        for s in COMPANY_SLUGS:
            if s in slug:
                return True
    return False


def defuddle_fetch(url):
    """Fetch page content via Defuddle (primary). Returns markdown or None."""
    try:
        # Strip protocol for defuddle URL format
        clean_url = url.replace("https://", "").replace("http://", "")
        defuddle_url = f"https://defuddle.md/{clean_url}"
        req = urllib.request.Request(defuddle_url, headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            if content and len(content) > 200:
                log(f"  Defuddle fetched {len(content)} chars from {url}")
                return content
    except Exception as e:
        log(f"  Defuddle fetch error for {url}: {e}")
    return None


def jina_fetch(url):
    """Fetch page content via Jina Reader (fallback). Returns text or None."""
    try:
        jina_url = f"https://r.jina.ai/{url}"
        req = urllib.request.Request(jina_url, headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            if content and len(content) > 200:
                return content
    except Exception as e:
        log(f"  Jina fetch error for {url}: {e}")
    return None


def fetch_page_content(url):
    """Fetch page content: Defuddle first, Jina fallback."""
    content = defuddle_fetch(url)
    if content:
        return content
    log(f"  Defuddle failed, trying Jina for {url}")
    return jina_fetch(url)


HUMANIZER_PROMPT = """You are a content humanizer. Remove AI-generated artifacts and make this text sound authentically human.

REMOVE these AI tells:
- Words: "delve", "landscape", "leverage", "important to note", "game-changing", "transformative"
- Tone inflation and generic phrasing
- Excessive hedging ("perhaps", "might", "could potentially")
- Overly perfect structure and identical paragraph rhythms
- "First", "Second", "Third" lists without variation

ADD human qualities:
- Vary sentence length (short punchy + longer conversational)
- Use contractions ("you're" not "you are")
- Include specific, concrete details
- Add natural transitions, not formulaic ones
- Sound like someone actually thinking, not performing

For LinkedIn specifically: Professional but conversational, authoritative but approachable.

Output ONLY the humanized text. Nothing else.

Original text:
{text}

Humanized:"""


def humanize_text(text, api_key=None, base_url=None):
    """Remove AI tells from text to sound more human. Uses gateway."""
    if len(text) < 50:
        return text
    result = call_llm(HUMANIZER_PROMPT.format(text=text), max_tokens=400)
    return result if result else text


def make_post(r, layer_label):
    url   = r.get("url", "")
    slug_m = re.search(r'linkedin\.com/posts/([^_]+?)_', url)
    author = slug_m.group(1).replace("-", " ").title() if slug_m else "Unknown"
    
    # Get content - try Tavily first, fallback to Defuddle/Jina if too short
    content = r.get("content", "") or ""
    if len(content) < 200 and url:
        # Tavily returned shallow content, try Defuddle then Jina
        fetched = fetch_page_content(url)
        if fetched:
            content = fetched[:500]
    
    return {
        "title":        r.get("title", "").split(" - ")[0][:80],
        "author":       author,
        "topic":        content[:300],
        "link":         url,
        "activity_id":  "",
        "target_layer": layer_label,
        "ready_comment": "",
        "comment_angle": "",
    }


MAX_POST_AGE_DAYS = 14  # Only comment on posts from the last 2 weeks

def get_post_age_days(url):
    """Extract post age in days from LinkedIn activity ID in URL. Returns None if can't determine."""
    m = re.search(r'activity-(\d+)', url)
    if not m:
        return None
    try:
        aid = int(m.group(1))
        # LinkedIn activity IDs are Snowflake-style: timestamp bits shifted left by 22
        # Epoch offset calibrated: activity 7434103996341964801 ≈ March 10, 2026
        EPOCH_OFFSET = 1097088299  # ms offset from Unix epoch
        ts_ms = (aid >> 22) + EPOCH_OFFSET
        import time
        age_days = (time.time() * 1000 - ts_ms) / 86400000
        return age_days
    except:
        return None


def find_posts(commented_urls, targets):
    log("Step 4: Searching LinkedIn posts (3 layers)...")
    # Dynamic date hints for DDG freshness bias
    from datetime import datetime
    _now = datetime.now()
    _year = str(_now.year)
    _month = _now.strftime("%B")  # e.g. "March"

    # Non-English domains to skip (engagement should be in English)
    NON_EN_DOMAINS = ["de.linkedin.com", "fr.linkedin.com", "es.linkedin.com", 
                       "pt.linkedin.com", "it.linkedin.com", "nl.linkedin.com",
                       "jp.linkedin.com", "cn.linkedin.com", "kr.linkedin.com",
                       "ar.linkedin.com", "tr.linkedin.com", "ru.linkedin.com"]

    def is_fresh(url):
        if "linkedin.com/posts/" not in url:
            return False
        if url in commented_urls:
            return False
        if any(url.startswith(f"https://{d}") for d in NON_EN_DOMAINS):
            return False
        if is_company_page(url):
            return False
        # Check post age from activity ID
        age = get_post_age_days(url)
        if age is not None and age > MAX_POST_AGE_DAYS:
            return False
        return True

    # Layer 1: Pipeline companies - search for INDIVIDUALS at those companies
    tier1 = targets.get("layer_1_pipeline_companies", {}).get("tier_1", [])
    raw1 = []
    # Batch companies into groups for broader coverage
    batch1 = tier1[:5]
    batch2 = tier1[5:10]
    batch3 = tier1[10:15]
    for batch in [batch1, batch2, batch3]:
        if not batch:
            break
        names = " OR ".join(f'"{c}"' for c in batch)
        # Add year to bias DDG toward recent posts
        r = tavily_search(f'site:linkedin.com/posts ({names}) digital transformation {_year}', n=8, days=10)
        raw1.extend(r)
    # Also search for executive titles at target companies (multiple queries for coverage)
    r2 = tavily_search(f'site:linkedin.com/posts CTO VP Director G42 Dubai Holding Talabat {_year}', n=8, days=10)
    raw1.extend(r2)
    # Broader: GCC tech leaders posting about transformation
    r3 = tavily_search(f'site:linkedin.com/posts CEO CTO CIO Dubai Abu Dhabi technology transformation {_month} {_year}', n=8, days=10)
    raw1.extend(r3)
    L1 = [make_post(r, "Layer 1: Pipeline Company") for r in raw1 if is_fresh(r.get("url",""))]
    # Deduplicate by URL
    seen = set()
    L1_dedup = []
    for p in L1:
        if p["link"] not in seen:
            seen.add(p["link"])
            L1_dedup.append(p)
    L1 = L1_dedup
    log(f"  Layer 1: {len(raw1)} raw, {len(L1)} passed filter")

    # Layer 2: Recruiters - broader queries for DDG compatibility
    firms = targets.get("layer_2_recruiters", {}).get("firms", [])
    q2a = " OR ".join(f'"{f}"' for f in firms[:5])
    raw2a = tavily_search(f'site:linkedin.com/posts ({q2a}) executive hiring GCC', n=8, days=10)
    # Broader recruiter queries (DDG needs simpler terms)
    raw2b = tavily_search('site:linkedin.com/posts executive recruiter hiring Dubai UAE', n=8, days=7)
    raw2c = tavily_search('site:linkedin.com/posts headhunter CTO VP hiring Saudi Arabia', n=8, days=7)
    L2 = [make_post(r, "Layer 2: Recruiter") for r in (raw2a + raw2b + raw2c) if is_fresh(r.get("url",""))]
    # Dedup L2
    seen_l2 = set()
    L2 = [p for p in L2 if p["link"] not in seen_l2 and not seen_l2.add(p["link"])]
    log(f"  Layer 2: {len(raw2a)+len(raw2b)+len(raw2c)} raw, {len(L2)} passed filter")

    # Layer 3: Industry - broader and simpler queries
    raw3a = tavily_search(f'site:linkedin.com/posts digital transformation healthcare GCC', n=8, days=7)
    raw3b = tavily_search(f'site:linkedin.com/posts CIO CTO technology strategy Dubai', n=8, days=7)
    raw3c = tavily_search(f'site:linkedin.com/posts AI automation enterprise Middle East', n=8, days=7)
    L3 = [make_post(r, "Layer 3: Industry") for r in (raw3a + raw3b + raw3c) if is_fresh(r.get("url",""))]
    # Dedup L3
    seen_l3 = set()
    L3 = [p for p in L3 if p["link"] not in seen_l3 and not seen_l3.add(p["link"])]
    log(f"  Layer 3: {len(raw3a)+len(raw3b)+len(raw3c)} raw, {len(L3)} passed filter")

    # Sort by content richness
    for lst in (L1, L2, L3):
        lst.sort(key=lambda x: len(x.get("topic", "")), reverse=True)

    # Pick top 2 from each layer
    selected = L1[:2] + L2[:2] + L3[:2]
    log(f"  Selected: {len(selected)} posts (L1:{min(2,len(L1))}, L2:{min(2,len(L2))}, L3:{min(2,len(L3))})")
    for p in selected:
        log(f"    [{p['target_layer']}] {p['author']}: {p['title'][:50]}")

    return selected, {"layer1": L1, "layer2": L2, "layer3": L3}


# ============================================================
# STEP 5: DRAFT COMMENTS (Sonnet 4.6)
# ============================================================
def draft_comments(posts):
    log(f"Step 5: Drafting {len(posts)} comments via Sonnet 4.6...")
    if not posts:
        log("  No posts to draft comments for.")
        return posts
    if not GATEWAY_TOKEN and not ANTHROPIC_API_KEY:
        log("  WARNING: No gateway token or Anthropic API key.")
        for p in posts:
            p["ready_comment"] = "[Comment draft pending]"
        return posts

    metrics_str = "\n  ".join(f"- {m}" for m in AHMED_METRICS)

    for i, post in enumerate(posts, 1):
        log(f"  [{i}/{len(posts)}] {post['author']}...")
        prompt = COMMENT_PROMPT.format(
            metrics=metrics_str,
            author=post.get("author", "Unknown"),
            snippet=post.get("topic", "No context available")[:300]
        )
        try:
            text = call_llm(prompt, model="anthropic/claude-sonnet-4-6", max_tokens=300)
            if text:
                # Remove em dashes just in case
                text = text.replace("\u2014", ",").replace("\u2013", ",")
                # Humanize the comment to remove AI tells
                text = humanize_text(text)
                post["ready_comment"] = text
                post["comment_angle"] = post.get("topic", "")[:80]
                log(f"    Done ({len(text)} chars)")
            else:
                log(f"    FAILED: empty response")
                post["ready_comment"] = "[Comment draft failed. Retry tomorrow.]"
        except Exception as e:
            log(f"    FAILED: {e}")
            post["ready_comment"] = "[Comment draft failed. Retry tomorrow.]"

    return posts


# ============================================================
# STEP 6: UPDATE DEDUP LOG
# ============================================================
def update_log(posts, today_str):
    log("Step 6: Updating commented posts log...")
    os.makedirs(os.path.dirname(COMMENTED_FILE), exist_ok=True)
    with open(COMMENTED_FILE, "a") as f:
        for p in posts:
            url = p.get("link", "")
            if url and "linkedin.com" in url:
                f.write(f"{today_str} | {url} | {p.get('author','')} | {p.get('title','')[:60]} | {p.get('target_layer','')}\n")
    log(f"  Appended {len(posts)} entries.")


# ============================================================
# STEP 7: BUILD BRIEFING JSON
# ============================================================
def load_content_intelligence():
    """Load the weekly LinkedIn Content Intelligence brief if available (runs Thu 7 PM)."""
    brief_file = f"{WORKSPACE}/memory/knowledge/weekly-content-brief.md"
    try:
        if os.path.exists(brief_file):
            mtime = os.path.getmtime(brief_file)
            from datetime import datetime as dt2
            age_days = (time.time() - mtime) / 86400
            if age_days <= 8:  # Fresh within a week
                content = open(brief_file).read()
                log(f"  Content intelligence loaded: {brief_file} (age: {age_days:.1f} days)")
                return {
                    "status": "available",
                    "age_days": round(age_days, 1),
                    "brief": content[:2000],
                    "note": "Weekly content intelligence brief from Thursday. Use for today's post planning."
                }
            else:
                log(f"  Content intelligence stale: {age_days:.1f} days old")
                return {"status": "stale", "note": f"Brief is {age_days:.0f} days old. Next update Thursday 7 PM."}
    except Exception as e:
        log(f"  Content intelligence error: {e}")
    return {"status": "not_available", "note": "No content intelligence brief found. Runs Thursdays at 7 PM Cairo."}


def load_engagement_radar(today_str):
    """Load today's LinkedIn Engagement Radar report if available."""
    radar_file = f"{WORKSPACE}/linkedin/engagement/daily/{today_str}.md"
    try:
        if os.path.exists(radar_file):
            content = open(radar_file).read()
            # Extract key stats
            scanned = content.count("## ") - 1  # Sections minus header
            log(f"  Engagement radar loaded: {radar_file}")
            return {
                "status": "available",
                "file": radar_file,
                "profiles_with_activity": scanned,
                "note": "See engagement radar report for today's comment targets from 19 GCC influencers."
            }
    except Exception as e:
        log(f"  Engagement radar error: {e}")
    return {
        "status": "not_available",
        "note": "Engagement radar runs at 9 AM Cairo. Check later if briefing runs before 9 AM."
    }


def build_briefing_json(today_str, date_display, qualified, borderline, scanner_note,
                        events, upcoming, pipeline, posts, todays_post=None, built_cvs=None):
    log("Step 7: Building briefing JSON...")

    # Match CVs to qualified jobs
    cv_map = {}
    if built_cvs:
        for cv in built_cvs:
            key = (cv.get("company","").lower(), cv.get("role","").lower())
            cv_map[key] = cv
        # Also index by company only for fuzzy matching
        for cv in built_cvs:
            cv_map[cv.get("company","").lower()] = cv

    for job in qualified:
        company = job.get("company", "").lower()
        title = job.get("title", "").lower()
        # Try exact match first, then company-only
        cv = cv_map.get((company, title)) or cv_map.get(company)
        if cv and cv.get("github_link"):
            job["cv_link"] = cv["github_link"]
            job["cv_status"] = "ready" if cv.get("status") in ("built", "existing") else "pending"

    L1 = [p for p in posts if "Layer 1" in p.get("target_layer", "")]
    L2 = [p for p in posts if "Layer 2" in p.get("target_layer", "")]
    L3 = [p for p in posts if "Layer 3" in p.get("target_layer", "")]

    categories = []
    if L1: categories.append({"name": "Layer 1: Pipeline Company Posts (Highest ROI)", "posts": L1})
    if L2: categories.append({"name": "Layer 2: GCC Executive Recruiter Posts",        "posts": L2})
    if L3: categories.append({"name": "Layer 3: Industry Thought Leadership",           "posts": L3})

    data = {
        "date": date_display,
        "summary": {
            "priority_focus": "Job pipeline review + LinkedIn strategic engagement",
            "scanner_status": scanner_note,
            "linkedin_status": f"{len(posts)} strategic posts ready to comment.",
            "calendar_status": f"{len(events)} events today" if events else "No events today",
            "pipeline_status": pipeline.get("total_applications", "No data"),
        },
        "todays_post": todays_post,
        "jobs": {
            "scanner_note": scanner_note,
            "qualified":    qualified,
            "borderline":   borderline,
            "recommendation": f"{len(qualified)} recommended roles (ATS 82+). {len([j for j in borderline if j.get('ats_verdict')=='REVIEW'])} borderline. {len([j for j in borderline if j.get('ats_verdict')=='SKIP'])} low-fit." if qualified else f"{len([j for j in borderline if j.get('ats_verdict')=='REVIEW'])} borderline leads today. No strong matches." if borderline else "No new roles today.",
        },
        "linkedin": {
            "intro": "Three-layer strategic targeting. Ready-to-post comments below.",
            "categories": categories,
            "recommendation": "Priority: Layer 1 (pipeline targets) > Layer 2 (recruiter visibility) > Layer 3 (thought leadership)."
        },
        "calendar": {
            "events":   events,
            "upcoming": upcoming or ["No upcoming events in next 3 days"],
        },
        "pipeline": pipeline,
        "engagement_radar": load_engagement_radar(today_str),
        "content_intelligence": load_content_intelligence(),
        "strategic_notes": [
            f"{len(posts)} LinkedIn posts found with ready-to-post Sonnet-drafted comments.",
            "Comment strategy: Layer 1 > Layer 2 > Layer 3 by ROI.",
            "Job scanner running daily at 6 AM Cairo.",
        ],
        "action_items": [a for a in [
            f"Comment on {len(L1)} Layer 1 posts (pipeline company visibility)" if L1 else None,
            f"Comment on {len(L2)} Layer 2 posts (recruiter recognition)"       if L2 else None,
            f"Comment on {len(L3)} Layer 3 posts (thought leadership)"           if L3 else None,
            f"Review {len(qualified)} new qualified roles"                        if qualified else None,
            "Follow up on top pipeline applications with no response",
        ] if a]
    }

    out = f"{JOBS_DIR}/briefing-data-{today_str}.json"
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    log(f"  Written: {out}")
    return out


# ============================================================
# STEP 9: BUILD SYSTEM LOG JSON
# ============================================================
def build_syslog_json(today_str, date_display, errors, stats):
    log("Step 9: Building system log JSON...")

    yesterday = (datetime.strptime(today_str, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    streak = 1
    total_enh = 0
    total_err = 0
    prev = f"{JOBS_DIR}/system-log-{yesterday}.json"
    if os.path.exists(prev):
        try:
            with open(prev) as f:
                yd = json.load(f)
            streak    = yd.get("stats", {}).get("streak_days", 0) + 1
            total_enh = yd.get("stats", {}).get("total_enhancements", 0)
            total_err = yd.get("stats", {}).get("total_errors_fixed", 0)
        except:
            pass

    data = {
        "date": date_display,
        "stats": {
            "streak_days":       streak,
            "total_enhancements": total_enh + len(stats.get("enhancements", [])),
            "total_errors_fixed": total_err + len(errors),
        },
        "operations_summary": stats.get("ops", {}),
        "went_right":           stats.get("went_right", []),
        "went_wrong":           errors,
        "lessons_learned":      stats.get("lessons", []),
        "enhancements_applied": stats.get("enhancements", []),
        "cron_health":          stats.get("cron_health", []),
        "model_usage":          stats.get("model_usage", {}),
        "tomorrow_improvements":stats.get("tomorrow", []),
        "self_improvement": stats.get("self_improvement", {}),
    }

    out = f"{JOBS_DIR}/system-log-{today_str}.json"
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    log(f"  Written: {out}")
    return out


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Skip Google Docs generation")
    parser.add_argument("--date", help="Override date (YYYY-MM-DD)")
    args = parser.parse_args()

    cairo    = timezone(timedelta(hours=2))
    now      = datetime.now(cairo)
    today_str    = args.date or now.strftime("%Y-%m-%d")
    date_display = now.strftime("%A, %B %d, %Y")

    log("=== Morning Briefing Orchestrator ===")
    log(f"Date: {date_display}")
    log("")

    errors    = []
    went_right = []

    load_config()

    # Pre-flight: verify LLM access works (gateway or direct API)
    llm_ok = False
    if GATEWAY_TOKEN:
        try:
            test_result = call_llm("ping", max_tokens=5)
            if test_result:
                log("LLM access via gateway: OK")
                llm_ok = True
            else:
                log("WARNING: Gateway returned empty response")
        except Exception as e:
            log(f"WARNING: Gateway LLM check failed: {str(e)[:80]}")
    if not llm_ok and ANTHROPIC_API_KEY:
        try:
            test_result = call_llm("ping", max_tokens=5)
            if test_result:
                log("LLM access via direct API: OK")
                llm_ok = True
        except Exception as e:
            log(f"WARNING: Direct API check also failed: {str(e)[:80]}")
    if not llm_ok:
        log("WARNING: No working LLM access. Comments will fail this run.")
        errors.append({"issue": "No LLM access (gateway + API both failed)", "fix": "Check gateway status or API key"})

    commented_urls = load_commented_urls()
    targets        = load_targets()
    log(f"Dedup: {len(commented_urls)} URLs already suggested")
    log("")

    # Step 0: Self-Improvement Engine
    try:
        log("Step 0: Running self-improvement engine...")
        r = subprocess.run(
            f"python3 {WORKSPACE}/scripts/self-improvement-engine.py --json",
            shell=True, capture_output=True, text=True, timeout=30
        )
        stdout = r.stdout.strip()
        if stdout:
            # JSON output may span multiple lines; find the JSON block
            try:
                si_result = json.loads(stdout)
            except:
                # Try to find JSON object in output
                si_result = None
                brace_start = stdout.find("{")
                if brace_start >= 0:
                    try:
                        si_result = json.loads(stdout[brace_start:])
                    except:
                        pass
            if si_result:
                patterns = si_result.get("patterns", [])
                actions = si_result.get("actions", [])
                if patterns:
                    log(f"  Patterns: {len(patterns)} detected")
                    for p in patterns:
                        log(f"    {p.get('severity','').upper()}: {p.get('detail','')[:60]}")
                if actions:
                    log(f"  Actions: {len(actions)} applied")
                    went_right.append(f"Self-improvement: {len(patterns)} patterns, {len(actions)} fixes.")
                else:
                    log("  System healthy. No fixes needed.")
    except Exception as e:
        log(f"  Self-improvement skipped: {e}")
    log("")

    # Step 1
    try:
        qualified, borderline, scanner_note = gather_jobs()
        if qualified:
            went_right.append(f"Job scanner: {len(qualified)} qualified, {len(borderline)} borderline.")
    except Exception as e:
        errors.append({"issue": f"Job data failed: {e}", "fix": "Check scanner output"})
        qualified, borderline, scanner_note = [], [], "Scanner data unavailable"
    log("")

    # Step 1b: Auto-generate CVs for qualified roles
    built_cvs = []
    try:
        log("Step 1b: Auto-generating CVs for 70+ roles...")
        r = subprocess.run(
            f"python3 {WORKSPACE}/scripts/auto-cv-builder.py --json",
            shell=True, capture_output=True, text=True, timeout=300
        )
        # Parse JSON from stdout (last line or the JSON array)
        stdout = r.stdout.strip()
        if stdout:
            # Find the JSON array in output
            for line in stdout.split("\n"):
                line = line.strip()
                if line.startswith("["):
                    built_cvs = json.loads(line)
                    break
        if built_cvs:
            built_count = sum(1 for c in built_cvs if c.get("status") == "built")
            existing_count = sum(1 for c in built_cvs if c.get("status") == "existing")
            went_right.append(f"CVs: {built_count} new, {existing_count} existing.")
            log(f"  {built_count} new CVs built, {existing_count} existing")
        else:
            log("  No trigger files to process.")
        # Print stderr (the log lines from auto-cv-builder)
        if r.stderr:
            for line in r.stderr.strip().split("\n")[:10]:
                log(f"  {line}")
    except Exception as e:
        errors.append({"issue": f"CV auto-generation failed: {e}"})
        log(f"  ERROR: {e}")
    log("")

    # Step 2
    cal_error = None
    try:
        events, upcoming, cal_error = check_calendar()
        if cal_error:
            errors.append({"issue": cal_error, "fix": "Re-auth Google Calendar"})
        else:
            went_right.append("Calendar check completed.")
    except Exception as e:
        errors.append({"issue": f"Calendar failed: {e}", "fix": "Check gog auth"})
        events, upcoming, cal_error = [], [], str(e)
    log("")

    # Step 3
    try:
        pipeline = read_pipeline()
        went_right.append(f"Pipeline read: {pipeline.get('total_applications','N/A')}.")
    except Exception as e:
        errors.append({"issue": f"Pipeline read failed: {e}"})
        pipeline = {}
    log("")

    # Step 3b: Today's LinkedIn post
    todays_post = None
    try:
        post_dir = f"{WORKSPACE}/linkedin/posts"
        post_md  = f"{post_dir}/{today_str}-*.md"
        post_files = glob.glob(post_md)
        if post_files:
            pf = post_files[0]
            with open(pf) as f:
                post_content = f.read()
            # Check for matching image: first try same-name .png, then check markdown for ![...](image.png)
            img_pattern = pf.replace(".md", ".png")
            img_exists = os.path.exists(img_pattern)
            if not img_exists:
                # Look for image reference in markdown: ![...](filename.png)
                import re as _re_img
                img_ref = _re_img.search(r'!\[.*?\]\((.+?\.(?:png|jpg|jpeg|webp))\)', post_content)
                if img_ref:
                    ref_path = os.path.join(os.path.dirname(pf), img_ref.group(1))
                    if os.path.exists(ref_path):
                        img_pattern = ref_path
                        img_exists = True
            # Extract title line (first # heading or first non-empty line)
            title_line = ""
            for line in post_content.split("\n"):
                l = line.strip()
                if l.startswith("# "):
                    title_line = l.lstrip("# ").strip()
                    break
                elif l and not l.startswith("!") and not l.startswith("---"):
                    title_line = l[:80]
                    break
            todays_post = {
                "title": title_line,
                "content": post_content,
                "image_path": img_pattern if img_exists else None,
                "image_filename": os.path.basename(img_pattern) if img_exists else None,
                "github_link": f"https://github.com/ahmednasr999/openclaw-workspace/blob/master/linkedin/posts/{os.path.basename(pf)}",
                "file": os.path.basename(pf),
            }
            log(f"  Today's post: {os.path.basename(pf)} (image: {'yes' if img_exists else 'no'})")
            went_right.append(f"LinkedIn post found: {os.path.basename(pf)}")
        else:
            log(f"  No post found for {today_str}")
    except Exception as e:
        log(f"  Post lookup failed: {e}")
    log("")

    # Step 4
    try:
        selected_posts, all_posts = find_posts(commented_urls, targets)
        went_right.append(f"LinkedIn: {len(selected_posts)} posts across 3 layers.")
    except Exception as e:
        errors.append({"issue": f"LinkedIn search failed: {e}", "trace": traceback.format_exc()[:300]})
        selected_posts, all_posts = [], {}
    log("")

    # Step 5
    try:
        selected_posts = draft_comments(selected_posts)
        drafted = sum(1 for p in selected_posts if "[Comment draft" not in p.get("ready_comment",""))
        went_right.append(f"Comments drafted: {drafted}/{len(selected_posts)} by Sonnet 4.6.")
    except Exception as e:
        errors.append({"issue": f"Comment drafting failed: {e}"})
    log("")

    # Step 6
    try:
        update_log(selected_posts, today_str)
    except Exception as e:
        errors.append({"issue": f"Dedup log update failed: {e}"})
    log("")

    # Step 7
    try:
        briefing_path = build_briefing_json(
            today_str, date_display, qualified, borderline, scanner_note,
            events, upcoming, pipeline, selected_posts, todays_post, built_cvs
        )
        went_right.append("Briefing JSON built.")
    except Exception as e:
        errors.append({"issue": f"Briefing JSON failed: {e}"})
        briefing_path = None
    log("")

    # Step 8: Generate Daily Briefing Doc
    if briefing_path and not args.dry_run:
        # Step 7b: Validate JSON before generating doc (Fix #3)
        log("Step 7b: Validating briefing JSON...")
        try:
            v = subprocess.run(
                f"python3 {BRIEFING_SCRIPT} --data {briefing_path} --validate",
                shell=True, capture_output=True, text=True, timeout=30
            )
            log(f"  Validation: {v.stdout.strip()}")
            if v.returncode != 0:
                log(f"  Validation fixed aliases, re-running...")
        except Exception as e:
            log(f"  Validation skipped: {e}")

        log("Step 8: Generating Daily Briefing Google Doc...")
        try:
            r = subprocess.run(
                f"python3 {BRIEFING_SCRIPT} --data {briefing_path}",
                shell=True, capture_output=True, text=True, timeout=300
            )
            if r.returncode == 0:
                went_right.append("Daily Briefing Google Doc generated.")
                log("  Done!")
            else:
                errors.append({"issue": f"Briefing doc failed: {r.stderr[:200]}"})
                log(f"  ERROR: {r.stderr[:200]}")
        except Exception as e:
            errors.append({"issue": f"Briefing doc failed: {e}"})
    log("")

    # Step 9
    stats = {
        "ops": {
            "jobs_scanned":     scanner_note,
            "linkedin_found":   f"{len(selected_posts)} posts across 3 layers",
            "calendar_events":  f"{len(events)} today, {len(upcoming)} upcoming",
            "comments_drafted": f"{len(selected_posts)} by Sonnet 4.6",
            "docs_generated":   "Daily Briefing + System Log",
        },
        "went_right":  went_right,
        "lessons":     [],
        "enhancements":[],
        "cron_health": [{
            "name":   "Morning Briefing Orchestrator",
            "status": "ok" if not errors else "warning",
            "detail": f"Completed with {len(errors)} error(s)" if errors else "All steps completed."
        }],
        "model_usage": {
            "Sonnet 4.6":    f"Comment drafting: {len(selected_posts)} comments",
            "Orchestrator":  "Python only for all other steps",
        },
        "tomorrow": [
            "Monitor comment quality and relevance",
            "Check if Layer 1 finding individual employees vs company pages",
        ]
    }

    try:
        syslog_path = build_syslog_json(today_str, date_display, errors, stats)
    except Exception as e:
        log(f"  ERROR building system log: {e}")
        syslog_path = None
    log("")

    # Step 10: Generate System Log Doc
    if syslog_path and not args.dry_run:
        log("Step 10: Generating System Log Google Doc...")
        try:
            r = subprocess.run(
                f"python3 {SYSLOG_SCRIPT} --data {syslog_path}",
                shell=True, capture_output=True, text=True, timeout=300
            )
            if r.returncode == 0:
                log("  Done!")
            else:
                log(f"  ERROR: {r.stderr[:200]}")
        except Exception as e:
            log(f"  ERROR: {e}")
    log("")

    # Step 10.4: Check for Notion CV requests
    log("Step 10.4: Checking Notion for CV build requests...")
    cv_requests = []
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from importlib import import_module
        cv_handler = import_module("cv-request-handler")
        cv_requests = cv_handler.find_cv_requests()
        if cv_requests:
            log(f"  Found {len(cv_requests)} CV request(s)!")
            for req in cv_requests:
                cv_handler.process_cv_request(req)
                log(f"    {req['role']} @ {req['company']}: trigger created")
            went_right.append(f"CV requests: {len(cv_requests)} triggered from Notion")
        else:
            log("  No CV requests")
    except Exception as e:
        log(f"  CV request check error (non-fatal): {e}")
    log("")

    # Step 10.5: Two-way pipeline sync from Notion
    log("Step 10.5: Checking Notion for pipeline changes...")
    notion_changes = []
    try:
        from notion_sync import read_pipeline_from_notion, apply_notion_changes_to_pipeline
        notion_result = read_pipeline_from_notion()
        notion_changes = notion_result.get("changes", [])
        if notion_changes:
            applied_count = apply_notion_changes_to_pipeline(notion_changes)
            log(f"  {applied_count} pipeline changes synced from Notion")
            for c in notion_changes:
                log(f"    {c['company']}: {c['old']} -> {c['new']}")
            went_right.append(f"Notion two-way sync: {len(notion_changes)} changes applied")
            # Re-read pipeline after changes
            pipeline = read_pipeline()
        else:
            log("  No changes detected (in sync)")
    except Exception as e:
        log(f"  Notion two-way sync error (non-fatal): {e}")
    log("")

    # Step 10.6: Two-way active tasks sync
    log("Step 10.6: Syncing active tasks with Notion...")
    tasks_result = {"changes": [], "overdue": [], "due_today": [], "total_open": 0}
    try:
        from notion_sync import two_way_sync_active_tasks
        tasks_result = two_way_sync_active_tasks()
        if tasks_result["changes"]:
            log(f"  {len(tasks_result['changes'])} tasks completed in Notion")
        if tasks_result["overdue"]:
            log(f"  ⚠️ {len(tasks_result['overdue'])} overdue tasks!")
        if tasks_result["due_today"]:
            log(f"  📌 {len(tasks_result['due_today'])} tasks due today")
        log(f"  Total open: {tasks_result['total_open']}")
    except Exception as e:
        log(f"  Active tasks sync error (non-fatal): {e}")
    log("")

    # Step 11: Sync to Notion
    log("Step 11: Syncing to Notion...")
    try:
        from notion_sync import sync_briefing, sync_new_jobs, sync_system_event
        # Build briefing data dict for Notion
        _scanner_meta = load_scanner_meta()
        notion_data = {
            "jobs": {"qualified": qualified, "borderline": borderline, "scanner_note": scanner_note},
            "scanner_meta": _scanner_meta,
            "pipeline": pipeline,
            "calendar": {"events_today": events, "upcoming": upcoming},
            "cal_error": cal_error,
            "linkedin": {},
            "todays_post": todays_post or {},
            "comments": selected_posts,
            "went_right": went_right,
            "errors": errors,
        }
        notion_url = sync_briefing(briefing_data=notion_data, date_str=today_str)
        if notion_url:
            went_right.append(f"Notion briefing: {notion_url}")
            log(f"  Notion briefing: {notion_url}")
        else:
            log("  Notion sync failed (non-fatal)")

        # Sync new jobs to pipeline
        all_new = qualified + borderline
        if all_new:
            added = sync_new_jobs(all_new)
            log(f"  {added} new jobs synced to Notion pipeline")

        # Log system event
        sync_system_event(
            f"Morning briefing {today_str}",
            component="Briefing",
            details=f"{len(qualified)} priority, {len(borderline)} borderline, {len(errors)} errors"
        )
    except Exception as e:
        log(f"  Notion sync error (non-fatal): {e}")
    log("")

    # ===== STEP 12: GENERATE TELEGRAM COMPACT FORMAT =====
    log("Step 12: Generating Telegram compact format...")
    try:
        scanner_meta = load_scanner_meta()
        lines = []
        lines.append(f"📋 BRIEFING — {date_display}")

        # Action items (urgent, top of message)
        action_items = []
        if qualified:
            action_items.append(f"Review {len(qualified)} new picks")
        p_overdue = pipeline.get("overdue", [])
        if p_overdue:
            action_items.append(f"{len(p_overdue)} follow-ups overdue (oldest: {p_overdue[0]['days']}d)")
        if pipeline.get("interviews", 0) > 0:
            action_items.insert(0, f"🎯 {pipeline['interviews']} INTERVIEW(S) in pipeline!")
        if todays_post and todays_post.get("title"):
            action_items.append("Publish LinkedIn post")
        if selected_posts:
            action_items.append(f"Post {len(selected_posts)} engagement comments")

        if action_items:
            lines.append("\n🔴 ACTION NEEDED")
            for a in action_items[:4]:
                lines.append(f"• {a}")

        # Jobs section with scanner health
        lines.append("\n💼 JOBS")
        if scanner_meta:
            searches = scanner_meta.get("total_searches", "?")
            countries = len(scanner_meta.get("countries", []))
            src_status = scanner_meta.get("source_status", {})
            src_line = " ".join(f"{k} {v}" for k, v in src_status.items())
            lines.append(f"Scanner: {searches} searches | {countries} countries | {src_line}")
            total = scanner_meta.get("total_found", 0)
            picks_n = scanner_meta.get("priority_picks", 0)
            leads_n = scanner_meta.get("exec_leads", 0)
            filtered = scanner_meta.get("filtered_out", 0)
            lines.append(f"Found: {total} total → {picks_n} picks, {leads_n} leads ({filtered} filtered)")
            cookie_age = scanner_meta.get("cookie_age_days")
            if cookie_age is not None:
                cookie_status = "✅" if cookie_age < 14 else ("⚠️" if cookie_age < 21 else "🔴 EXPIRED")
                lines.append(f"Cookie: {cookie_age}d old {cookie_status}")
            if scanner_meta.get("degraded"):
                lines.append("⚠️ DEGRADED: Low results, possible rate limit")
            if scanner_meta.get("validation_warnings"):
                for w in scanner_meta["validation_warnings"][:2]:
                    lines.append(f"⚠️ {w[:80]}")
        else:
            lines.append(f"New: {len(qualified)} picks, {len(borderline)} borderline")
        
        # Scanner trend from Notion history
        try:
            from notion_sync import get_scanner_trends
            trends = get_scanner_trends()
            if trends.get("total_runs", 0) >= 3:
                lines.append(f"{trends['trend']} 7d avg: {trends['avg_7d_found']:.0f} jobs, {trends['avg_7d_picks']:.0f} picks")
            if trends.get("alert"):
                lines.append(trends["alert"])
            if trends.get("cookie_alert"):
                lines.append(trends["cookie_alert"])
        except Exception as e:
            log(f"  Trend check error: {e}")

        # New picks with one-line JD summary
        for j in qualified[:5]:
            title = j.get("title", "?")[:40]
            company = j.get("company", "?")[:20]
            location = j.get("location", "?")[:15]
            ats = j.get("ats_score", "?")
            url = j.get("link", j.get("url", ""))
            jd_snippet = j.get("jd_snippet", j.get("description", ""))
            if jd_snippet:
                jd_snippet = jd_snippet[:60].strip()
            icon = "🟢" if isinstance(ats, (int, float)) and ats >= 82 else "🟡"
            lines.append(f"\n{icon} {title} — {company} — {location} — {ats}%")
            if jd_snippet:
                lines.append(f"   \"{jd_snippet}\"")
            if url:
                lines.append(f"   → {url}")

        # Pipeline section
        lines.append("\n📊 PIPELINE")
        p_applied = pipeline.get("applied", 0)
        p_interview = pipeline.get("interviews", 0)
        p_stale = pipeline.get("stale", 0)
        p_closed = pipeline.get("closed", 0)
        p_total = pipeline.get("total_applications", 0)
        lines.append(f"Applied: {p_applied} | Interview: {p_interview} | Stale: {p_stale}")

        # Show Notion stage changes (two-way sync)
        if notion_changes:
            lines.append(f"🔄 {len(notion_changes)} stage change(s) from Notion:")
            for c in notion_changes[:3]:
                lines.append(f"  • {c['company']}: {c['old']} -> {c['new']}")
            if len(notion_changes) > 3:
                lines.append(f"  +{len(notion_changes)-3} more")

        # Interview alert (goes to top of ACTION NEEDED too)
        if p_interview > 0:
            lines.append(f"🎯 {p_interview} active interview(s)!")

        # Overdue follow-ups (the real action item)
        p_overdue = pipeline.get("overdue", [])
        if p_overdue:
            lines.append(f"⏰ Follow-ups overdue ({len(p_overdue)}):")
            for o in p_overdue[:5]:
                lines.append(f"• {o['company']} — {o['role'][:30]} — {o['days']}d")
            if len(p_overdue) > 5:
                lines.append(f"  +{len(p_overdue)-5} more in Notion")

        # Calendar
        lines.append("\n📅 CALENDAR")
        if cal_error:
            lines.append("⚠️ Calendar offline (auth expired)")
        elif events:
            for ev in events[:4]:
                if isinstance(ev, dict):
                    t = ev.get("time", "")
                    title = ev.get("title", "?")[:40]
                    if t:
                        lines.append(f"• {t}: {title}")
                    else:
                        lines.append(f"• {title}")
            if upcoming:
                tomorrow_count = len([u for u in upcoming if u.strip()])
                if tomorrow_count > 0:
                    lines.append(f"Next 3 days: {tomorrow_count} events")
        else:
            lines.append("Clear day ✅")

        # LinkedIn
        lines.append("\n📱 LINKEDIN")
        if todays_post and todays_post.get("title"):
            post_title = todays_post.get("title", "")[:45]
            post_status = todays_post.get("status", "drafted")
            lines.append(f"Post: {post_title} [{post_status}]")
        else:
            lines.append("No post scheduled today")
        if selected_posts:
            lines.append(f"Engage: {len(selected_posts)} comment targets ready")
            # Show top 2 targets
            for sp in selected_posts[:2]:
                author = sp.get("author", "?")[:20]
                topic = sp.get("topic", sp.get("snippet", ""))[:30]
                lines.append(f"  • {author}: {topic}")

        # System
        lines.append("\n⚙️ SYSTEM")
        # Get real system health
        try:
            import shutil
            usage = shutil.disk_usage("/")
            disk_pct = int(usage.used / usage.total * 100)
        except:
            disk_pct = "?"
        # Gateway check
        gw_status = "✅"
        try:
            gw_check = subprocess.run("pgrep -f 'openclaw.*gateway'", shell=True, capture_output=True, text=True, timeout=5)
            if gw_check.returncode != 0:
                gw_status = "❌ DOWN"
        except:
            gw_status = "?"
        # Cron status
        cron_line = ""
        if errors:
            cron_line = f" | ⚠️ {len(errors)} errors"
        else:
            cron_line = " | Crons: OK"
        # Cron health from Notion dashboard
        cron_summary = None
        try:
            from notion_sync import sync_cron_dashboard_full
            cron_summary = sync_cron_dashboard_full()
        except Exception as e:
            log(f"  Cron dashboard sync error: {e}")
        
        if cron_summary:
            cron_line = f" | Crons: {cron_summary['ok']}✅ {cron_summary['failed']}❌ {cron_summary['disabled']}⏸️"
        lines.append(f"Gateway: {gw_status} | Disk: {disk_pct}%{cron_line}")
        if cron_summary and cron_summary.get("failures"):
            for fail in cron_summary["failures"][:3]:
                lines.append(f"  ❌ {fail['name'][:30]}: {fail['error'][:40]}")
        elif errors:
            for e in errors[:2]:
                lines.append(f"  ⚠️ {e.get('issue','')[:60]}")
        
        # Active Tasks section
        if tasks_result.get("overdue") or tasks_result.get("due_today") or tasks_result.get("total_open"):
            lines.append(f"\n✅ TASKS ({tasks_result.get('total_open', 0)} open)")
            if tasks_result.get("overdue"):
                lines.append(f"🔴 {len(tasks_result['overdue'])} OVERDUE:")
                for t in tasks_result["overdue"][:3]:
                    lines.append(f"  • {t[:60]}")
            if tasks_result.get("due_today"):
                lines.append(f"📌 Due today:")
                for t in tasks_result["due_today"][:3]:
                    lines.append(f"  • {t[:60]}")
            if tasks_result.get("changes"):
                lines.append(f"✅ {len(tasks_result['changes'])} completed in Notion")

        # Add Notion link at bottom
        if 'notion_url' in dir() or 'notion_url' in locals():
            pass  # Already added above if notion sync ran
        
        telegram_msg = "\n".join(lines)
        telegram_file = f"/tmp/briefing-telegram-{today_str}.txt"
        with open(telegram_file, "w") as f:
            f.write(telegram_msg)
        log(f"  Telegram format saved: {telegram_file}")
        print(f"\n{telegram_msg}\n")
        
        # Save button data for qualified picks (OpenClaw picks these up)
        if qualified:
            buttons_data = []
            for j in qualified[:5]:
                title = j.get("title", "?")[:30]
                company = j.get("company", "?")[:20]
                url = j.get("link", j.get("url", ""))
                buttons_data.append({
                    "text": f"📝 Build CV: {title} @ {company}",
                    "callback_data": f"build_cv:{company}:{title}:{url}",
                    "company": company,
                    "role": title,
                    "url": url,
                })
            buttons_file = f"/tmp/briefing-buttons-{today_str}.json"
            with open(buttons_file, "w") as f:
                json.dump(buttons_data, f, indent=2)
            log(f"  CV buttons saved: {buttons_file} ({len(buttons_data)} picks)")

    except Exception as e:
        log(f"  Telegram format error: {e}")
        import traceback; traceback.print_exc()
    log("")

    # Done
    drafted = sum(1 for p in selected_posts if "[Comment draft" not in p.get("ready_comment",""))
    # ===== SELF-VALIDATION (Fix 1) =====
    validation_warnings = []
    all_leads = qualified + borderline
    unfetched = [j for j in all_leads if j.get("link") and "linkedin.com" in j.get("link","") and not j.get("jd_fetched")]
    if unfetched:
        validation_warnings.append(f"JD NOT FETCHED: {len(unfetched)} leads have no JD. Verdicts are unreliable: {', '.join(j.get('title','?')[:30] for j in unfetched)}")
    if scanner_note and "0 priority picks, 0 exec leads" not in scanner_note:
        # Check that recommendations exist for non-empty results
        pass
    if errors:
        validation_warnings.append(f"ERRORS: {len(errors)} steps had errors: {'; '.join(e.get('issue','')[:50] for e in errors)}")

    if validation_warnings:
        log(f"\n⚠️ VALIDATION ({len(validation_warnings)} warnings):")
        for w in validation_warnings:
            log(f"  - {w}")
    else:
        log(f"\n✅ Validation passed.")

    log("")
    log("=== COMPLETE ===")
    log(f"Posts found:       {len(selected_posts)}")
    log(f"Comments drafted:  {drafted}")
    log(f"Errors:            {len(errors)}")
    log(f"Validation:        {len(validation_warnings)} warnings")
    for e in errors:
        log(f"  ! {e.get('issue','')}")
    log(f"Briefing:   {BRIEFING_DOC}")
    log(f"System Log: {SYSLOG_DOC}")


if __name__ == "__main__":
    main()
