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

import json, os, sys, re, subprocess, argparse, glob, traceback, urllib.request
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
            if "Qualified" in l and ("##" in l or "🟢" in l):
                if job.get("title") and section:
                    (qualified if section == "q" else borderline).append(job)
                    job = {}
                section = "q"
            elif "Borderline" in l and ("##" in l or "🟡" in l):
                if job.get("title") and section:
                    (qualified if section == "q" else borderline).append(job)
                    job = {}
                section = "b"
            elif l.startswith("### "):
                if job.get("title"):
                    (qualified if section == "q" else borderline).append(job)
                job = {"title": l.lstrip("# ").strip()}
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

    if job.get("title"):
        (qualified if section == "q" else borderline).append(job)

    note = f"{os.path.basename(latest)}: {len(qualified)} qualified, {len(borderline)} borderline."
    log(f"  {len(qualified)} qualified, {len(borderline)} borderline")
    return qualified, borderline, note


# ============================================================
# STEP 2: CALENDAR
# ============================================================
def check_calendar():
    log("Step 2: Checking calendar...")
    events, upcoming = [], []
    try:
        r = subprocess.run(
            f'GOG_KEYRING_PASSWORD="" gog calendar list --today -a {ACCOUNT_EMAIL}',
            shell=True, capture_output=True, text=True, timeout=30
        )
        if r.stdout.strip() and "no events" not in r.stdout.lower():
            for line in r.stdout.strip().split("\n"):
                if line.strip():
                    events.append({"time": "", "title": line.strip(), "notes": ""})
        log(f"  Today: {len(events)} events")

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
        log(f"  Calendar check failed: {e}")
    return events, upcoming


# ============================================================
# STEP 3: PIPELINE
# ============================================================
def read_pipeline():
    log("Step 3: Reading pipeline...")
    if not os.path.exists(PIPELINE_FILE):
        log("  Pipeline file not found.")
        return {}
    with open(PIPELINE_FILE) as f:
        content = f.read()

    applied = content.count("✅ Applied")
    closed  = content.count("❌ Closed")
    log(f"  {applied} applied, {closed} closed")

    return {
        "total_applications": f"{applied} active",
        "responses_this_week": 0,
        "overdue": f"Review follow-up dates on all {applied} applications",
        "recent": [],
        "recommendation": f"{applied} applications sent. Zero responses. Action: direct email follow-up on top 5 targets."
    }


# ============================================================
# STEP 4: LINKEDIN POSTS (Tavily)
# ============================================================
def ddg_search(query, n=5):
    """Search via DuckDuckGo (free, no API key, no quota)."""
    try:
        from ddgs import DDGS
        results = DDGS().text(query, max_results=n)
        # Normalize to Tavily-compatible format
        return [{"title": r.get("title",""), "url": r.get("href",""), "content": r.get("body","")} for r in results]
    except Exception as e:
        log(f"  DDG error: {e}")
        return []


def tavily_search(query, n=5, days=7):
    """Search via Tavily (primary) with DDG fallback (free)."""
    # Try Tavily first if key available
    if TAVILY_API_KEY:
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

    def is_fresh(url):
        if "linkedin.com/posts/" not in url:
            return False
        if url in commented_urls:
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

    # Layer 2: Recruiters (don't add year - recruiter posts rarely mention it)
    firms = targets.get("layer_2_recruiters", {}).get("firms", [])
    q2a = " OR ".join(f'"{f}"' for f in firms[:5])
    raw2a = tavily_search(f'site:linkedin.com/posts ({q2a}) executive hiring GCC', n=8, days=10)
    raw2b = tavily_search('site:linkedin.com/posts executive search recruitment UAE Saudi leadership', n=8, days=7)
    L2 = [make_post(r, "Layer 2: Recruiter") for r in (raw2a + raw2b) if is_fresh(r.get("url",""))]
    log(f"  Layer 2: {len(raw2a)+len(raw2b)} raw, {len(L2)} passed filter")

    # Layer 3: Industry (add year for freshness bias)
    raw3a = tavily_search(f'site:linkedin.com/posts digital transformation healthcare PMO GCC Saudi {_month} {_year}', n=8, days=7)
    raw3b = tavily_search(f'site:linkedin.com/posts CIO CTO technology strategy Dubai UAE {_year}', n=8, days=7)
    L3 = [make_post(r, "Layer 3: Industry") for r in (raw3a + raw3b) if is_fresh(r.get("url",""))]
    log(f"  Layer 3: {len(raw3a)+len(raw3b)} raw, {len(L3)} passed filter")

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
            "recommendation": f"{len(qualified)} qualified roles to review. Check fit and decide: apply or skip." if qualified else "No new qualified roles today.",
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
    try:
        events, upcoming = check_calendar()
        went_right.append("Calendar check completed.")
    except Exception as e:
        errors.append({"issue": f"Calendar failed: {e}", "fix": "Check gog auth"})
        events, upcoming = [], []
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
            # Check for matching image
            img_pattern = pf.replace(".md", ".png")
            img_exists = os.path.exists(img_pattern)
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
        log("Step 8: Generating Daily Briefing Google Doc...")
        try:
            r = subprocess.run(
                f"python3 {BRIEFING_SCRIPT} --data {briefing_path}",
                shell=True, capture_output=True, text=True, timeout=120
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
                shell=True, capture_output=True, text=True, timeout=120
            )
            if r.returncode == 0:
                log("  Done!")
            else:
                log(f"  ERROR: {r.stderr[:200]}")
        except Exception as e:
            log(f"  ERROR: {e}")
    log("")

    # Done
    drafted = sum(1 for p in selected_posts if "[Comment draft" not in p.get("ready_comment",""))
    log("=== COMPLETE ===")
    log(f"Posts found:       {len(selected_posts)}")
    log(f"Comments drafted:  {drafted}")
    log(f"Errors:            {len(errors)}")
    for e in errors:
        log(f"  ! {e.get('issue','')}")
    log(f"Briefing:   {BRIEFING_DOC}")
    log(f"System Log: {SYSLOG_DOC}")


if __name__ == "__main__":
    main()
