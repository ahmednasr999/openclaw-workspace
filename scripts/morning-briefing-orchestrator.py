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


def log(msg):
    ts = datetime.now(cairo).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_notion_token():
    try:
        with open(NOTION_CONFIG) as f:
            return json.load(f)['token']
    except:
        return None


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
        current_job = None

        for line in content.split("\n"):
            line = line.strip()

            # Section headers (## Priority Picks, ## Leads, etc.)
            if line.startswith("## "):
                current_section = line.lstrip("# ").strip().lower()
                continue

            # Job title as ### heading (Format A)
            if line.startswith("### "):
                # Save previous job
                if current_job:
                    if "priority" in current_section or "pick" in current_section:
                        qualified.append(current_job)
                    else:
                        borderline.append(current_job)
                title = line.lstrip("# ").strip()
                # Strip ATS icon (🟢🟡🔴) and extract ATS score from title
                title = re.sub(r'^[🟢🟡🔴]\s*', '', title)
                ats_in_title = re.search(r'\(ATS:\s*(\d+)%?\)', title)
                ats_val = int(ats_in_title.group(1)) if ats_in_title else None
                title = re.sub(r'\s*\(ATS:\s*\d+%?\)\s*$', '', title)
                current_job = {"title": title[:60], "company": "", "location": "", "url": ""}
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
                    if "priority" in current_section or "pick" in current_section:
                        qualified.append(job)
                    else:
                        borderline.append(job)

        # Don't forget the last job
        if current_job:
            if "priority" in current_section or "pick" in current_section:
                qualified.append(current_job)
            else:
                borderline.append(current_job)

    scanner_age = None
    if meta.get("date"):
        try:
            scan_date = datetime.strptime(meta["date"], "%Y-%m-%d")
            scanner_age = (datetime.now() - scan_date).days
        except:
            pass

    return meta, qualified, borderline, scanner_age


def check_email():
    """Check recent emails via himalaya with smart categorization."""
    emails = []
    try:
        r = subprocess.run(
            "himalaya envelope list --account ahmed --folder INBOX --page-size 50",
            shell=True, capture_output=True, text=True, timeout=15
        )
        if r.returncode != 0 or not r.stdout.strip():
            return [], "himalaya returned no data"

        # Action-needed keywords (interview, reply needed)
        action_keywords = ["interview", "schedule", "shortlisted", "next steps",
                          "assessment", "offer", "congratulations", "selected",
                          "phone screen", "technical round", "final round"]
        # Job-related keywords
        job_keywords = ["application", "position", "role", "hiring", "recruiter",
                       "vacancy", "job", "career", "opportunity", "talent",
                       "resume", "cv ", "apply", "candidate"]
        # LinkedIn message keywords
        linkedin_keywords = ["messaged you", "via linkedin", "linkedin"]

        lines = r.stdout.strip().split("\n")
        # Skip header rows (first 2 lines are table header + separator)
        for line in lines[2:]:
            line = line.strip()
            if not line or line.startswith("|--"):
                continue

            # Parse: | ID | FLAGS | SUBJECT | FROM | DATE |
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 6:
                continue

            email_id = parts[1].strip()
            flags = parts[2].strip()
            subject = parts[3].strip()[:80]
            sender = parts[4].strip()[:40]
            date_str = parts[5].strip()[:20]

            subj_lower = subject.lower()
            sender_lower = sender.lower()

            # Skip obvious non-job emails
            skip_senders = ["newsletter", "prypco", "iris", "canon", "rumble",
                           "public notice", "magnitt", "quality academy"]
            if any(s in sender_lower for s in skip_senders):
                continue

            # Categorize
            priority = None
            if any(kw in subj_lower for kw in action_keywords):
                priority = "action"  # 🔴
            elif any(kw in subj_lower or kw in sender_lower for kw in job_keywords):
                priority = "job"     # 🟡
            elif any(kw in subj_lower or kw in sender_lower for kw in linkedin_keywords):
                priority = "linkedin" # 🟡
            else:
                continue  # Not job-related

            emails.append({
                "id": email_id,
                "subject": subject,
                "sender": sender,
                "date": date_str,
                "priority": priority,
                "unread": "*" in flags,
            })

        # Sort: action first, then job, then linkedin
        priority_order = {"action": 0, "job": 1, "linkedin": 2}
        emails.sort(key=lambda e: priority_order.get(e["priority"], 9))

        return emails, None
    except Exception as e:
        return [], str(e)


def check_calendar():
    """Check calendar events."""
    events = []
    cal_error = None
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
    result = {"scheduled": 0, "drafted": 0, "posted": 0, "today_post": None}
    token = load_notion_token()
    if not token:
        return result

    ctx = ssl.create_default_context()
    today_str = datetime.now(cairo).strftime("%Y-%m-%d")

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

        for p in data.get('results', []):
            props = p['properties']
            status = (props.get('Status', {}).get('select') or {}).get('name', '')
            planned = (props.get('Planned Date', {}).get('date') or {}).get('start', '')

            if status == 'Posted':
                result["posted"] += 1
            elif status == 'Drafted':
                result["drafted"] += 1
            elif status == 'Scheduled':
                result["scheduled"] += 1

            if planned == today_str:
                title = ''.join(t.get('plain_text', '') for t in props.get('Title', {}).get('title', []))
                result["today_post"] = {"title": title[:50], "status": status, "date": planned}
    except Exception as e:
        log(f"  Content calendar error: {e}")

    return result


def get_system_health():
    """Check system health metrics."""
    health = {"gateway": "?", "disk_pct": "?", "cron_ok": 0, "cron_fail": 0, "cron_disabled": 0, "errors": []}

    # Disk
    try:
        import shutil
        usage = shutil.disk_usage("/")
        health["disk_pct"] = int(usage.used / usage.total * 100)
    except:
        pass

    # Gateway
    try:
        r = subprocess.run("pgrep -f 'openclaw.*gateway'", shell=True, capture_output=True, text=True, timeout=5)
        health["gateway"] = "UP" if r.returncode == 0 else "DOWN"
    except:
        pass

    # Cron health from recent runs
    try:
        r = subprocess.run(
            "openclaw cron list 2>/dev/null",
            shell=True, capture_output=True, text=True, timeout=20
        )
        if r.stdout:
            for line in r.stdout.strip().split("\n"):
                # Each cron line has columns: id, name, schedule, next, last, status, ...
                # Status column contains: ok, error, idle, disabled
                line_lower = line.lower()
                # Skip header lines and empty
                if not line.strip() or line.startswith("ID") or line.startswith("--"):
                    continue
                # Match by the status column (appears after time columns)
                if re.search(r'\bok\b', line_lower):
                    health["cron_ok"] += 1
                elif re.search(r'\b(error|failed)\b', line_lower):
                    health["cron_fail"] += 1
                    parts = line.split()
                    if len(parts) >= 2:
                        health["errors"].append(parts[1][:30])
                elif re.search(r'\b(idle|disabled)\b', line_lower):
                    health["cron_disabled"] += 1
    except:
        pass

    return health


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

def create_notion_briefing(date_str, date_display, pipeline, scanner_meta, qualified, borderline,
                           scanner_age, emails, email_error, events, cal_error, content_cal,
                           system, tasks, notion_changes, trends):
    """Create a rich Notion briefing page with ALL 11 sections."""
    token = load_notion_token()
    if not token:
        log("  No Notion token - skipping")
        return None

    ctx = ssl.create_default_context()

    def notion_req(method, path, body=None):
        url = f"https://api.notion.com/v1{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            'Authorization': f'Bearer {token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        })
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            return json.loads(r.read())

    def rt(text):
        """Rich text helper."""
        return [{"type": "text", "text": {"content": str(text)[:2000]}}]

    # Build blocks
    blocks = []

    def add_callout(text, emoji="📋"):
        blocks.append({"type": "callout", "callout": {"rich_text": rt(text), "icon": {"type": "emoji", "emoji": emoji}}})

    def add_heading(text):
        blocks.append({"type": "heading_2", "heading_2": {"rich_text": rt(text)}})

    def add_para(text):
        blocks.append({"type": "paragraph", "paragraph": {"rich_text": rt(text)}})

    def add_bullet(text):
        blocks.append({"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": rt(text)}})

    def add_divider():
        blocks.append({"type": "divider", "divider": {}})

    # Header callout
    add_callout(f"Morning Brief - {date_display}", "☀️")
    add_divider()

    # 1. PIPELINE
    add_heading("📊 Job Pipeline")
    p = pipeline
    add_para(f"{p['total_applications']} total | {p['applied']} applied | {p['interviews']} interviews | {p['stale']} stale (14d+) | {p['closed']} closed")

    if p["interview_list"]:
        add_para(f"🎯 {len(p['interview_list'])} active interview(s)!")
        for iv in p["interview_list"]:
            add_bullet(f"{iv['company']} - {iv['role']} ({iv['stage']})")

    if p["overdue"]:
        add_para(f"⏰ {len(p['overdue'])} follow-ups overdue:")
        for o in p["overdue"][:7]:
            icon = "🔴" if o["days"] >= 21 else "🟡"
            add_bullet(f"{icon} {o['company']} - {o['role']} - {o['days']}d ago")

    if notion_changes:
        add_para(f"🔄 {len(notion_changes)} stage changes from Notion:")
        for c in notion_changes[:5]:
            add_bullet(f"{c['company']}: {c.get('old','?')} -> {c.get('new','?')}")

    add_divider()

    # 2. SCANNER
    add_heading("🔍 Job Scanner")
    if scanner_meta:
        searches = scanner_meta.get("total_searches", "?")
        countries = len(scanner_meta.get("countries", []))
        total = scanner_meta.get("total_found", 0)
        picks = scanner_meta.get("priority_picks", 0)
        leads = scanner_meta.get("exec_leads", 0)
        # Source status
        src = scanner_meta.get("source_status", {})
        src_parts = []
        for name, status in src.items():
            src_parts.append(f"{name}: {status}")
        src_str = " | ".join(src_parts) if src_parts else "LinkedIn, Indeed"
        add_para(f"Searches: {searches} | Countries: {countries} | Found: {total} | Picks: {picks} | Leads: {leads}")
        add_para(f"Sources: {src_str}")
        if scanner_meta.get("degraded"):
            add_para("⚠️ DEGRADED: Low results, possible rate limit or cookie expiry")
    else:
        add_para("No scanner data available")

    if scanner_age is not None:
        freshness = "fresh" if scanner_age == 0 else f"{scanner_age}d old"
        add_para(f"Scanner data: {freshness}")

    if qualified:
        apply_jobs = [j for j in qualified if j.get("ats_score", 0) >= 50]
        skip_jobs = [j for j in qualified if j.get("ats_score", 0) < 50]

        def format_job_bullet(idx, j):
            title = j.get("title", "?")[:50]
            company = j.get("company", "")
            ats = j.get("ats_score", 0)
            location = j.get("location", "")
            city = location.split(",")[0].strip()[:15] if location else ""
            url = j.get("url", "")
            icon = "🟢" if ats >= 75 else "🟡"
            text = f"{idx}. {icon} {title}"
            if company:
                text += f" @ {company}"
            if city:
                text += f" - {city}"
            text += f" (ATS: {ats}%)"
            if url:
                text += f"\n{url}"
            return text

        if apply_jobs:
            add_para(f"✅ APPLY ({len(apply_jobs)} jobs - ATS 50%+):")
            for idx, j in enumerate(apply_jobs, 1):
                add_bullet(format_job_bullet(idx, j))

        if skip_jobs:
            add_para(f"❌ SKIP ({len(skip_jobs)} jobs - ATS below 50%):")
            for idx, j in enumerate(skip_jobs, len(apply_jobs) + 1):
                title = j.get("title", "?")[:50]
                company = j.get("company", "")
                ats = j.get("ats_score", 0)
                city = j.get("location", "").split(",")[0].strip()[:15]
                url = j.get("url", "")
                text = f"{idx}. 🔴 {title}"
                if company:
                    text += f" @ {company}"
                if city:
                    text += f" - {city}"
                text += f" (ATS: {ats}%)"
                if url:
                    text += f"\n{url}"
                add_bullet(text)

    if trends.get("total_runs", 0) >= 3:
        add_para(f"Trend: {trends.get('trend','')} 7d avg: {trends.get('avg_7d_found',0):.0f} jobs, {trends.get('avg_7d_picks',0):.0f} picks")

    add_divider()

    # 3. EMAIL INTEL
    add_heading("📧 Email Intelligence")
    if emails:
        action_emails = [e for e in emails if e.get("priority") == "action"]
        job_emails = [e for e in emails if e.get("priority") in ("job", "linkedin")]
        reply_str = f" ({len(action_emails)} need reply)" if action_emails else ""
        add_para(f"{len(emails)} job-related emails{reply_str}:")

        if action_emails:
            add_para("🔴 ACTION NEEDED:")
            for e in action_emails:
                unread = " 🆕" if e.get("unread") else ""
                add_bullet(f"🔴 {e.get('subject', '')[:60]} - {e.get('sender', '')[:30]}{unread}")

        if job_emails:
            add_para("🟡 Job-related:")
            for e in job_emails[:10]:
                unread = " 🆕" if e.get("unread") else ""
                add_bullet(f"🟡 {e.get('subject', '')[:60]} - {e.get('sender', '')[:30]}{unread}")
    elif email_error:
        add_para(f"⚠️ Email check failed: {email_error}")
    else:
        add_para("No job-related emails found")
    add_divider()

    # 4. CALENDAR
    add_heading("📅 Calendar")
    if cal_error:
        add_para(f"⚠️ {cal_error}")
    elif events:
        for ev in events[:5]:
            add_bullet(ev)
    else:
        add_para("Clear day ✅")
    add_divider()

    # 5. DASHBOARD KPIs
    add_heading("📈 Dashboard KPIs")
    add_bullet(f"Pipeline response rate: {(p['interviews'] / max(p['total_applications'],1) * 100):.1f}%")
    add_bullet(f"Stale rate: {(p['stale'] / max(p['total_applications'],1) * 100):.0f}%")
    add_bullet(f"Active interviews: {p['interviews']}")
    add_divider()

    # 6. ACTIVE TASKS
    add_heading("✅ Active Tasks")
    add_para(f"{tasks['total_open']} open | {tasks['completed_recent']} completed")
    if tasks["overdue"]:
        add_para(f"🔴 {len(tasks['overdue'])} overdue:")
        for t in tasks["overdue"][:5]:
            add_bullet(t)
    if tasks["due_today"]:
        add_para(f"📌 Due today:")
        for t in tasks["due_today"][:5]:
            add_bullet(t)
    add_divider()

    # 7. CONTENT CALENDAR
    add_heading("📝 Content Calendar")
    add_para(f"Posted: {content_cal['posted']} | Drafted: {content_cal['drafted']} | Scheduled: {content_cal['scheduled']}")
    if content_cal.get("today_post"):
        tp = content_cal["today_post"]
        add_bullet(f"Today: \"{tp['title']}\" [{tp['status']}]")
    add_divider()

    # 8. SYSTEM HEALTH
    add_heading("🤖 System Health")
    add_bullet(f"Gateway: {system['gateway']}")
    add_bullet(f"Disk: {system['disk_pct']}%")
    add_bullet(f"Crons: {system['cron_ok']} OK, {system['cron_fail']} failed, {system['cron_disabled']} disabled/idle")
    if system["errors"]:
        for err in system["errors"][:3]:
            add_bullet(f"❌ {err}")
    add_divider()

    # 9. ACTION ITEMS
    add_heading("⚠️ Action Items")
    actions = []
    if p["interviews"]:
        for iv in p["interview_list"]:
            actions.append(f"Follow up on {iv['company']} interview")
    if qualified:
        actions.append(f"Review {len(qualified)} new job picks")
    if p["overdue"]:
        actions.append(f"Follow up on {min(5, len(p['overdue']))} oldest stale applications")
    if content_cal.get("today_post") and content_cal["today_post"]["status"] != "Posted":
        actions.append(f"Publish LinkedIn: \"{content_cal['today_post']['title'][:30]}\"")
    # Email actions
    action_emails = [e for e in emails if e.get("priority") == "action"]
    if action_emails:
        for ae in action_emails[:3]:
            actions.append(f"📧 Reply: {ae.get('subject', '')[:35]} ({ae.get('sender', '')[:15]})")
    if cal_error:
        actions.append("Re-auth Google Calendar")
    if system["cron_fail"] > 0:
        actions.append(f"Fix {system['cron_fail']} failed cron(s)")
    if tasks["overdue"]:
        actions.append(f"Address {len(tasks['overdue'])} overdue tasks")

    if not actions:
        actions.append("All systems nominal - no urgent actions")

    for i, a in enumerate(actions[:7], 1):
        blocks.append({"type": "numbered_list_item", "numbered_list_item": {"rich_text": rt(a)}})

    # Create page
    log(f"  Creating Notion page with {len(blocks)} blocks...")

    # Notion API only accepts 100 blocks per append
    page_body = {
        "parent": {"database_id": "3268d599-a162-812d-a59e-e5496dec80e7"},
        "properties": {
            "Name": {"title": rt(f"Briefing {date_str}")},
            "Date": {"date": {"start": date_str}},
        },
        "children": blocks[:100]
    }

    try:
        page = notion_req('POST', '/pages', page_body)
        page_id = page['id']
        page_url = page.get('url', f"https://www.notion.so/{page_id.replace('-','')}")

        # Append remaining blocks if any
        if len(blocks) > 100:
            time.sleep(0.5)
            notion_req('PATCH', f'/blocks/{page_id}/children', {"children": blocks[100:]})

        log(f"  Notion page created: {page_url}")
        return page_url
    except Exception as e:
        log(f"  Notion page creation failed: {e}")
        return None


# ============================================================
# OUTPUT: TELEGRAM MESSAGE
# ============================================================

def build_telegram_message(date_display, pipeline, scanner_meta, qualified, borderline,
                           scanner_age, emails, email_error, events, cal_error, content_cal,
                           system, tasks, notion_changes, trends, notion_url):
    """Build compact Telegram briefing. Must be under 1500 chars."""
    p = pipeline
    lines = []
    lines.append(f"☀️ Morning Brief - {date_display}")

    # Action items first (red)
    actions = []
    if p["interviews"]:
        actions.append(f"🎯 {p['interviews']} INTERVIEW(S) active!")
    if qualified:
        actions.append(f"Review {len(qualified)} new picks")
    if p["overdue"]:
        actions.append(f"{len(p['overdue'])} follow-ups overdue")
    if content_cal.get("today_post") and content_cal["today_post"]["status"] != "Posted":
        actions.append("Publish LinkedIn post")

    if actions:
        lines.append("\n🔴 ACTION NEEDED")
        for a in actions[:4]:
            lines.append(f"  {a}")

    # Pipeline
    lines.append(f"\n📊 PIPELINE: {p['total_applications']} total | {p['interviews']} interviews | {p['stale']} stale")
    if p["interview_list"]:
        for iv in p["interview_list"][:3]:
            lines.append(f"  {iv['company']} - {iv['role']}")
    if p["overdue"]:
        lines.append(f"  ⏰ Top stale: {p['overdue'][0]['company']} ({p['overdue'][0]['days']}d)")

    if notion_changes:
        lines.append(f"  🔄 {len(notion_changes)} Notion changes")

    # Scanner
    if scanner_meta:
        total = scanner_meta.get("total_found", 0)
        picks = scanner_meta.get("priority_picks", 0)
        age = f" ({scanner_age}d old)" if scanner_age and scanner_age > 0 else ""
        # Source status
        src = scanner_meta.get("source_status", {})
        src_parts = [f"{k}:{v}" for k, v in src.items()]
        src_str = f" | {' '.join(src_parts)}" if src_parts else ""
        lines.append(f"\n🔍 SCANNER: {total} found, {picks} picks{age}{src_str}")
        if trends.get("trend"):
            lines.append(f"  {trends['trend']}")
    else:
        lines.append(f"\n🔍 SCANNER: No data")

    if qualified:
        apply_jobs = [j for j in qualified if j.get("ats_score", 0) >= 50]
        skip_jobs = [j for j in qualified if j.get("ats_score", 0) < 50]

        if apply_jobs:
            lines.append(f"  ✅ APPLY ({len(apply_jobs)}):")
            for idx, j in enumerate(apply_jobs, 1):
                title = j.get("title", "?")[:40]
                company = j.get("company", "")[:18]
                city = j.get("location", "").split(",")[0].strip()[:12]
                ats = j.get("ats_score", 0)
                url = j.get("url", "")
                icon = "🟢" if ats >= 75 else "🟡"
                line = f"  {idx}. {icon} {title}"
                if company:
                    line += f" - {company}"
                if city:
                    line += f" ({city})"
                line += f" [{ats}%]"
                lines.append(line)
                if url:
                    lines.append(f"    {url}")

        if skip_jobs:
            lines.append(f"  ❌ SKIP ({len(skip_jobs)}):")
            for idx, j in enumerate(skip_jobs, len(apply_jobs) + 1):
                title = j.get("title", "?")[:40]
                company = j.get("company", "")[:18]
                city = j.get("location", "").split(",")[0].strip()[:12]
                ats = j.get("ats_score", 0)
                line = f"  {idx}. 🔴 {title}"
                if company:
                    line += f" - {company}"
                if city:
                    line += f" ({city})"
                line += f" [{ats}%]"
                lines.append(line)

    # Email
    if emails:
        action_count = len([e for e in emails if e.get("priority") == "action"])
        reply_str = f" ({action_count} need reply)" if action_count else ""
        lines.append(f"\n📧 EMAIL: {len(emails)} job-related{reply_str}")
        for e in emails[:5]:
            icon = "🔴" if e.get("priority") == "action" else "🟡"
            subj = e.get("subject", "")[:45]
            sender = e.get("sender", "")[:20]
            lines.append(f"  {icon} {subj} - {sender}")
    elif email_error:
        lines.append(f"\n📧 EMAIL: ⚠️ {email_error[:30]}")

    # Calendar
    if cal_error:
        lines.append(f"\n📅 CALENDAR: ⚠️ offline")
    elif events:
        lines.append(f"\n📅 CALENDAR: {len(events)} events")
    else:
        lines.append(f"\n📅 CALENDAR: Clear ✅")

    # Content
    lines.append(f"\n📝 CONTENT: {content_cal['posted']} posted | {content_cal['scheduled']} scheduled | {content_cal['drafted']} drafted")
    if content_cal.get("today_post"):
        tp = content_cal["today_post"]
        lines.append(f"  Today: \"{tp['title'][:35]}\" [{tp['status']}]")

    # Tasks
    if tasks["total_open"] > 0 or tasks["overdue"]:
        lines.append(f"\n✅ TASKS: {tasks['total_open']} open")
        if tasks["overdue"]:
            lines.append(f"  🔴 {len(tasks['overdue'])} overdue")
        if tasks["due_today"]:
            lines.append(f"  📌 {len(tasks['due_today'])} due today")

    # System
    lines.append(f"\n⚙️ SYSTEM: GW {system['gateway']} | Disk {system['disk_pct']}% | Crons {system['cron_ok']}✅ {system['cron_fail']}❌")
    if system["errors"]:
        for err in system["errors"][:2]:
            lines.append(f"  ❌ {err}")

    # Notion link
    if notion_url:
        lines.append(f"\n📎 Full: {notion_url}")

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

    # ---- GATHER ALL DATA (pure Python, no LLM) ----

    # 1. Pipeline
    log("Step 1: Reading pipeline...")
    pipeline = read_pipeline()
    log(f"  {pipeline['total_applications']} total, {pipeline['interviews']} interviews, {pipeline['stale']} stale")

    # 2. Scanner
    log("Step 2: Loading scanner data...")
    scanner_meta, qualified, borderline, scanner_age = load_scanner_data(today_str)
    log(f"  {len(qualified)} qualified, {len(borderline)} borderline, age: {scanner_age}d")

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
    log(f"  Posted: {content_cal['posted']}, Scheduled: {content_cal['scheduled']}, Drafted: {content_cal['drafted']}")

    # 6. System Health
    log("Step 6: System health...")
    system = get_system_health()
    log(f"  GW: {system['gateway']}, Disk: {system['disk_pct']}%, Crons: {system['cron_ok']}ok/{system['cron_fail']}fail")

    # 7. Active Tasks
    log("Step 7: Active tasks...")
    tasks = get_active_tasks()
    log(f"  {tasks['total_open']} open, {len(tasks['overdue'])} overdue, {len(tasks['due_today'])} due today")

    # 8. Scanner Trends
    log("Step 8: Scanner trends...")
    trends = get_scanner_trends()

    # 9. Two-way sync
    log("Step 9: Two-way Notion sync...")
    notion_changes = notion_two_way_sync()

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
            system, tasks, notion_changes, trends
        )
    else:
        log("  (dry-run - skipped)")
    log("")

    # ---- OUTPUT 2: TELEGRAM MESSAGE ----
    log("Output 2: Telegram message...")
    telegram_msg = build_telegram_message(
        date_display, pipeline, scanner_meta, qualified, borderline,
        scanner_age, emails, email_error, events, cal_error, content_cal,
        system, tasks, notion_changes, trends, notion_url
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

    # ---- DONE ----
    log("=== COMPLETE ===")
    log(f"Notion: {notion_url or 'skipped'}")
    log(f"Telegram: {len(telegram_msg)} chars")
    log(f"Blocks: {len(qualified)} picks, {pipeline['interviews']} interviews, {len(emails)} emails")


if __name__ == "__main__":
    main()
