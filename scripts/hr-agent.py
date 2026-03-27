#!/usr/bin/env python3
"""
hr-agent.py — HR Agent Orchestrator
====================================
Handles the mechanical work of job applications:
- Parses job from jobs-summary.json
- Checks ontology for duplicates
- Updates Notion Pipeline
- Updates ontology graph
- Triggers CV build (auto-cv-builder.py)
- Sends Telegram summary

For the AI-generated content (cover letter, outreach),
the agent is meant to be run WITHIN an AI session where
the AI generates the content using Sonnet 4.6.

Standalone usage (no LLM content):
  python3 hr-agent.py --job 17 [--job 3 --job 12]

Full AI-powered (use hr-agent in your session):
  "Apply to #17 and #3 from today's pipeline"

Usage:
  python3 hr-agent.py --job 17 --dry-run    # Show job details, no changes
  python3 hr-agent.py --job 17 --no-llm     # Mechanical steps only, skip content
  python3 hr-agent.py --job 17 [--cover "..."] [--outreach "..."]  # Pass your own content
"""

import json, os, sys, re, argparse, subprocess, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE     = "/root/.openclaw/workspace"
DATA_DIR      = f"{WORKSPACE}/data"
HANDOFF_DIR   = f"{WORKSPACE}/jobs-bank/handoff"
ONTOLOGY_FILE = f"{WORKSPACE}/memory/ontology/graph.jsonl"
MASTER_CV     = f"{WORKSPACE}/memory/master-cv-data.md"
OPENCLAW_JSON = "/root/.openclaw/openclaw.json"
NOTION_CFG    = f"{WORKSPACE}/config/notion.json"
os.makedirs(f"{WORKSPACE}/media/cv-temp", exist_ok=True)
os.makedirs(HANDOFF_DIR, exist_ok=True)
os.makedirs("/var/log/hr-agent", exist_ok=True)

CAIRO = timezone(timedelta(hours=2))
NOTION_PIPELINE_DB = "3268d599-a162-81b4-b768-f162adfa4971"

# ═══════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════
def log(msg):
    ts = datetime.now(CAIRO).strftime("%H:%M")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(f"/var/log/hr-agent/{datetime.now(CAIRO).strftime('%Y-%m-%d')}.log", "a") as f:
            f.write(line + "\n")
    except:
        pass

# ═══════════════════════════════════════════════════════════════════
# NOTION
# ═══════════════════════════════════════════════════════════════════
def get_notion_token():
    with open(NOTION_CFG) as f:
        return json.load(f)["token"]

def notion_req(method, endpoint, body=None):
    token = get_notion_token()
    url = f"https://api.notion.com/v1/{endpoint}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "body": e.read().decode()[:200]}

def notion_update_applied(job):
    url    = job.get("url", "")
    url_slug = url.split("/")[-1] if url else ""
    today  = datetime.now(CAIRO).strftime("%Y-%m-%d")

    results = notion_req("POST", f"databases/{NOTION_PIPELINE_DB}/query", {
        "filter": {"property": "URL", "rich_text": {"contains": url_slug}},
        "page_size": 5
    })
    entries = results.get("results", [])

    if not entries:
        results2 = notion_req("POST", f"databases/{NOTION_PIPELINE_DB}/query", {
            "filter": {
                "and": [
                    {"property": "Role",    "rich_text": {"contains": job.get("title",   "")[:25]}},
                    {"property": "Company", "title":       {"contains": job.get("company", "")[:20]}},
                ]
            },
            "page_size": 5
        })
        entries = results2.get("results", [])

    updated = []
    for page in entries:
        patch = notion_req("PATCH", f"pages/{page['id']}", {
            "properties": {
                "Stage":        {"select": {"name": "Applied"}},
                "Applied Date": {"date":    {"start": today}},
            }
        })
        if "error" not in patch:
            updated.append(page["id"])
    return updated

# ═══════════════════════════════════════════════════════════════════
# ONTOLOGY
# ═══════════════════════════════════════════════════════════════════
def load_graph():
    entries = []
    if os.path.exists(ONTOLOGY_FILE):
        with open(ONTOLOGY_FILE) as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    return entries

def find_job_by_url(graph, url):
    for e in graph:
        if e.get("type") == "JobApplication" and e.get("properties", {}).get("linkedin_url") == url:
            return e
    return None

def find_job_by_company(graph, company):
    return [e for e in graph if e.get("type") == "JobApplication"
            and e.get("properties", {}).get("company", "").lower() == company.lower()]

def find_outreach_by_company(graph, company):
    return [e for e in graph if e.get("type") == "Outreach"
            and e.get("properties", {}).get("company", "").lower() == company.lower()]

def find_person_by_company(graph, company):
    return [e for e in graph if e.get("type") == "Person"
            and e.get("properties", {}).get("company", "").lower() == company.lower()]

def append_graph(entity):
    with open(ONTOLOGY_FILE, "a") as f:
        f.write(json.dumps(entity, ensure_ascii=False) + "\n")

def ensure_org(graph, company, location=""):
    for e in graph:
        if e.get("type") == "Organization" and e.get("properties", {}).get("name", "").lower() == company.lower():
            return e
    org_id = f"org-{company.lower()[:30].replace(' ', '-').replace('/', '-')}"
    append_graph({"id": org_id, "type": "Organization", "properties": {"name": company, "location": location}})
    return {"id": org_id}

def create_job_application(graph, job, cv_path=""):
    company = job.get("company", "Unknown")
    org     = ensure_org(graph, company, job.get("location", ""))
    jid     = f"job-{job.get('id', job.get('url', '').split('/')[-1])}"
    append_graph({
        "id": jid, "type": "JobApplication",
        "properties": {
            "title":        job.get("title", "Unknown"),
            "company":      company,
            "org_id":       org.get("id"),
            "status":       "applied",
            "linkedin_url": job.get("url", ""),
            "date_applied": datetime.now(CAIRO).strftime("%Y-%m-%d"),
            "fit_score":    str(job.get("career_fit_score", "")),
            "location":     job.get("location", ""),
            "applied_via":  "HR Agent",
            "cv_document":  cv_path,
            "notes":        (job.get("verdict_reason", "") or "")[:300],
        }
    })
    return jid

def add_to_applied_ids(job, source="hr-agent"):
    """
    Append job ID to applied-job-ids.txt immediately.
    This keeps the dedup list current between pipeline runs.
    """
    import re as _re
    url    = job.get("url", "")
    company = job.get("company", "?")
    role   = job.get("title", "?")[:50]
    today  = datetime.now(CAIRO).strftime("%Y-%m-%d")

    # Extract all IDs from URL
    url_ids = _re.findall(r'[a-f0-9]{10,}|\d{8,}', url)
    if not url_ids:
        url_ids = [job.get("id", "")]

    applied_file = Path("/root/.openclaw/workspace/jobs-bank/applied-job-ids.txt")
    for uid in url_ids:
        if len(uid) < 6:
            continue
        line = f"{uid} | {company} | {role} | {today} | {source}"
        # Only add if not already present
        existing = set()
        if applied_file.exists():
            existing = {l.strip().split("|")[0].strip() for l in open(applied_file)
                        if l.strip() and not l.strip().startswith("#")}
        if uid not in existing:
            with open(applied_file, "a") as f:
                f.write(line + "\n")
            log(f"   + Added {uid} to applied-job-ids.txt")

# ═══════════════════════════════════════════════════════════════════
# JOBS SUMMARY
# ═══════════════════════════════════════════════════════════════════
def load_jobs():
    with open(f"{DATA_DIR}/jobs-summary.json") as f:
        return json.load(f)

def find_job(jobs_data, ref):
    submit = jobs_data.get("data", {}).get("submit", [])
    review = jobs_data.get("data", {}).get("review", [])
    m = re.match(r"#?(\d+)", str(ref))
    if m:
        n = int(m.group(1)) - 1
        if 0 <= n < len(submit):
            return submit[n], "SUBMIT", n+1
        if 0 <= n < len(review):
            return review[n], "REVIEW", n+1
    ref_lower = str(ref).lower()
    for lst, tag in [(submit, "SUBMIT"), (review, "REVIEW")]:
        for i, job in enumerate(lst):
            if ref_lower in job.get("title","").lower() or ref_lower in job.get("company","").lower():
                return job, tag, i+1
    return None, None, None

# ═══════════════════════════════════════════════════════════════════
# CV BUILDER
# ═══════════════════════════════════════════════════════════════════
def build_cv(job, cv_notes):
    today_str = datetime.now(CAIRO).strftime("%Y-%m-%d")
    safe_c = re.sub(r"[^\w]", "-", job.get("company","Unknown"))[:25]
    safe_t = re.sub(r"[^\w]", "-", job.get("title","Role"))[:25]
    trigger_id   = f"{today_str}-{safe_c}-{safe_t}"
    trigger_file = f"{HANDOFF_DIR}/{trigger_id}.json"
    jd_text = job.get("jd_text","") or job.get("raw_snippet","") or job.get("verdict_reason","")

    with open(trigger_file, "w") as f:
        json.dump({
            "job_id":     trigger_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "status":     "pending_build",
            "job": {
                "company":      job.get("company", "Unknown"),
                "role":         job.get("title",   "Unknown"),
                "location":      job.get("location", ""),
                "url":          job.get("url",     ""),
                "url_verified": True,
                "salary_range": None,
                "jd_raw":       jd_text[:2000],
                "jd_keywords":   job.get("match_keywords", []),
                "ats_score":    job.get("ats_score", 0),
                "priority":     "HIGH"
            },
            "cv": {
                "path":           None,
                "ats_score":      job.get("ats_score", 0),
                "tailoring_notes": cv_notes,
                "pending_review":  True
            }
        }, f, indent=2)

    try:
        result = subprocess.run(
            ["python3", f"{WORKSPACE}/scripts/auto-cv-builder.py", "--trigger", trigger_file],
            capture_output=True, text=True, timeout=300
        )
        cv_path = None
        for line in result.stdout.split("\n"):
            if ".pdf" in line.lower():
                m = re.search(r"(/[^\s\"']+\.pdf)", line)
                if m:
                    cv_path = m.group(1)
        return trigger_file, cv_path
    except Exception as e:
        return trigger_file, None

# ═══════════════════════════════════════════════════════════════════
# TELEGRAM
# ═══════════════════════════════════════════════════════════════════
def get_telegram_token():
    try:
        with open(OPENCLAW_JSON) as f:
            cfg = json.load(f)
        return cfg.get("channels", {}).get("telegram", {}).get("botToken", "")
    except:
        return ""

HR_CHAT   = "-1003882622947:1522"   # Nasr Command Center → HR Agent thread

def send_telegram(text, chat_id=HR_CHAT):
    token = get_telegram_token()
    if not token:
        log("Telegram: no token found — printing message:")
        print(text)
        return
    url  = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode()
    req  = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15):
            pass
    except Exception as e:
        log(f"Telegram error: {e}")

# ═══════════════════════════════════════════════════════════════════
# MINIMAX (free fallback for content generation)
# ═══════════════════════════════════════════════════════════════════
def generate_content(prompt, system, max_tokens=600):
    """Use MiniMax M2.7 for free content generation."""
    body = json.dumps({
        "model": "MiniMax-M2.7",
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    try:
        proc = subprocess.run([
            "curl", "-s", "-X", "POST",
            "https://api.minimaxi.chat/v1/text/chatcompletion_v2",
            "-H", "Content-Type: application/json",
            "-d", body
        ], capture_output=True, timeout=60)
        result = json.loads(proc.stdout)
        return result.get("choices", [{}])[0].get("message", {}).get("content", "[No response]")
    except Exception as e:
        return f"[Content generation failed: {e}]"

def make_cover_letter_prompt(job):
    return f"""Write a cover letter for this role. Return ONLY the letter — no intro text.

CANDIDATE: Ahmed Nasr — 20+ years executive experience
Core: PMO leadership, Digital Transformation, AI Automation, GCC/MENA
Key achievements:
- Led 15-hospital digital transformation, $50M budget, Vision 2030 alignment
- Built 14 production AI agents for Fortune 500 operational automation
- Scaled Talabat ops 233x: logistics AI, routing optimization, automated workflows
- TopMed: clinical operations governance for 15 hospitals across GCC

ROLE: {job.get('title')} @ {job.get('company')}
Location: {job.get('location')}
Fit: {job.get('verdict_reason', '')[:400]}

Requirements to address: {', '.join(job.get('match_keywords', [])[:8])}

Format: 3 paragraphs, 250-300 words. Executive voice — sharp, specific, evidence-driven.
Start with a concrete proof point. No "I am excited to apply." No padding."""

def make_outreach_prompt(job, graph):
    company  = job.get("company", "")
    contacts = find_person_by_company(graph, company)
    outreach_list = find_outreach_by_company(graph, company)

    contact_info = ""
    if contacts:
        c = contacts[0].get("properties", {})
        contact_info = f"Contact at company: {c.get('name','Someone')} — {c.get('title','')}"
    if outreach_list:
        for o in outreach_list:
            op = o.get("properties", {})
            if op.get("status") in ("connected","messaged","replied"):
                contact_info += f"\nExisting outreach: {op.get('name','contact')} (status: {op.get('status')})"

    return f"""Write a LinkedIn outreach note for Ahmed Nasr reaching out about the {job.get('title')} role at {company}.

Ahmed: Senior exec — PMO, Digital Transformation, AI Automation. 20+ years GCC/MENA.
Target role: {job.get('title')} at {company} ({job.get('location')})

{contact_info or 'No prior connection found — write a direct, professional outreach.'}

Rules: 3 sentences max. Reference company or role specifically. Sound like a peer — not a job seeker. No "I'd love to pick your brain." Direct value proposition."""

# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
def process_job(job_ref, dry_run=False, force=False, cover_letter=None, outreach=None, no_llm=False):
    log(f"Processing: {job_ref}")
    jobs_data = load_jobs()
    job, source, number = find_job(jobs_data, job_ref)

    if not job:
        log(f"❌ Job not found: '{job_ref}'")
        log(f"   SUBMIT: {len(jobs_data.get('data',{}).get('submit',[]))} | REVIEW: {len(jobs_data.get('data',{}).get('review',[]))}")
        return None

    log(f"✅ #{number} | {job['title']} @ {job['company']} [{source}]")
    log(f"   Fit:{job.get('career_fit_score','?')} ATS:{job.get('ats_score','?')} | {job.get('url','')[:70]}")

    graph = load_graph()
    existing = find_job_by_url(graph, job.get("url",""))
    if existing and not force:
        prev = existing.get("properties",{}).get("date_applied","?")
        log(f"⚠️  Already applied on {prev} — use --force to override")
        return None

    same_co = find_job_by_company(graph, job.get("company",""))
    for e in same_co:
        dp = e.get("properties",{}).get("date_applied","")
        if dp:
            log(f"⚠️  Applied to {job.get('company')} on {dp}")

    if dry_run:
        log("🟡 DRY RUN — stopping here")
        return {"job": job, "source": source, "number": number}

    result = {
        "job": job, "source": source, "number": number,
        "cover_letter": cover_letter or "", "outreach": outreach or "",
        "cv_path": None, "notion_updated": 0, "ontology_updated": False
    }

    # Content generation (MiniMax free, unless cover_letter/outreach passed in)
    if not cover_letter and not no_llm:
        log("✍️  Cover letter (MiniMax M2.7)...")
        result["cover_letter"] = generate_content(
            make_cover_letter_prompt(job),
            system="Senior executive resume writer. Write sharp, direct, evidence-driven content. No fluff.",
            max_tokens=600
        )
        log(f"   {len(result['cover_letter'])} chars")

    if not outreach and not no_llm:
        log("✍️  LinkedIn outreach (MiniMax M2.7)...")
        result["outreach"] = generate_content(
            make_outreach_prompt(job, graph),
            system="Write LinkedIn outreach in Ahmed Nasr's voice — direct, professional, specific. 3 sentences max.",
            max_tokens=300
        )
        log(f"   {len(result['outreach'])} chars")

    # Build CV
    log("📄 Building tailored CV...")
    cv_notes = f"Role: {job.get('title')} @ {job.get('company')}\nFit: {job.get('career_fit_score')} ATS:{job.get('ats_score')}\nReason: {job.get('verdict_reason','')[:300]}"
    trigger_file, cv_path = build_cv(job, cv_notes)
    result["cv_path"] = cv_path
    log(f"   CV trigger: {trigger_file}")
    if cv_path:
        log(f"   CV PDF: {cv_path}")

    # Notion update
    log("📋 Updating Notion Pipeline → Applied...")
    notion_pages = notion_update_applied(job)
    result["notion_updated"] = len(notion_pages)
    log(f"   {'✅ Updated ' + str(len(notion_pages)) + ' entries' if notion_pages else '⚠️ No Notion entry found'}")

    # Ontology
    log("🔗 Updating ontology graph...")
    create_job_application(graph, job, cv_path or "")
    result["ontology_updated"] = True
    log("   ✅ Graph updated")

    # IMMEDIATE: Add to applied-job-ids.txt (fixes same-day re-scrape dedup)
    log("🔄 Updating applied-job-ids.txt for dedup...")
    add_to_applied_ids(job)

    # Save drafts
    out_dir  = f"{WORKSPACE}/media/cv-temp"
    safe     = re.sub(r"[^\w]", "-", f"{job['company'][:20]}-{job['title'][:20]}")
    out_file = f"{out_dir}/{safe}.txt"
    with open(out_file, "w") as f:
        f.write(f"COVER LETTER\n===========\n{result['cover_letter']}\n\nLINKEDIN OUTREACH\n================\n{result['outreach']}\n")
    result["out_file"] = out_file
    log(f"   Draft saved: {out_file}")

    # Telegram
    today = datetime.now(CAIRO).strftime("%d %b %Y")
    cv_display = cv_path.split("/")[-1] if cv_path else "building..."
    tg = f"""🎯 <b>APPLICATION READY</b>
━━━━━━━━━━━━━━━
<b>#{number}: {job['title']}</b> @ <b>{job['company']}</b>
📍 {job.get('location','?')} | Fit:{job.get('career_fit_score','?')} ATS:{job.get('ats_score','?')} | {source}
🔗 <a href="{job.get('url','')}">View Job</a>
📄 CV: <code>{cv_display}</code>
━━━━━━━━━━━━━━━
✉️ <b>OUTREACH</b>
{result['outreach'][:400]}
━━━━━━━━━━━━━━━
📝 <b>COVER LETTER</b>
{result['cover_letter'][:600]}
━━━━━━━━━━━━━━━
✅ Applied: {today} | HR Agent"""
    send_telegram(tg)
    log("📱 Telegram summary sent")
    return result

def main():
    p = argparse.ArgumentParser(description="HR Agent — apply to pipeline jobs")
    p.add_argument("--job",   dest="jobs",    action="append", default=[], help="Job #N or company name")
    p.add_argument("--dry-run",              action="store_true",           help="Show job, don't execute")
    p.add_argument("--force",               action="store_true",           help="Skip duplicate check")
    p.add_argument("--no-llm",              action="store_true",           help="Skip AI content generation")
    p.add_argument("--cover",                default=None,                  help="Pass your own cover letter text")
    p.add_argument("--outreach",             default=None,                  help="Pass your own outreach text")
    args = p.parse_args()

    if not args.jobs:
        print("Usage: hr-agent.py --job 17 [--job 3 --job 12]")
        print("       hr-agent.py --job 17 --dry-run")
        print("       hr-agent.py --job 17 --cover 'My custom cover letter...'")
        sys.exit(1)

    log("="*50)
    log("HR AGENT STARTED")
    log("="*50)
    for j in args.jobs:
        result = process_job(j, dry_run=args.dry_run, force=args.force,
                             cover_letter=args.cover, outreach=args.outreach,
                             no_llm=args.no_llm)
        if result:
            log(f"✅ {j} — complete")
        else:
            log(f"❌ {j} — failed/skipped")
    log("="*50)
    log("HR AGENT DONE")

if __name__ == "__main__":
    main()
