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
    result = {"scheduled": 0, "drafted": 0, "posted": 0, "today_post": None,
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

            if planned == today_str:
                result["today_post"] = {"title": title[:50], "status": status, "date": planned}
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


def get_github_discovery():
    """Read GitHub Discovery Radar results from cache."""
    today_str = datetime.now(cairo).strftime("%Y-%m-%d")
    yesterday_str = (datetime.now(cairo) - timedelta(days=1)).strftime("%Y-%m-%d")
    
    for date_str in [today_str, yesterday_str]:
        cache_file = f"/tmp/github-discovery-{date_str}.json"
        if os.path.exists(cache_file):
            try:
                with open(cache_file) as f:
                    repos = json.load(f)
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

def create_notion_briefing(date_str, date_display, pipeline, scanner_meta, qualified, borderline,
                           scanner_age, emails, email_error, events, cal_error, content_cal,
                           system, tasks, notion_changes, trends, github_discovery=None):
    """Create a rich Notion briefing page with ALL sections."""
    import time as _time
    _start_time = _time.time()
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
        apply_count = len([j for j in qualified if j.get("ats_score", 0) >= 50])
        summary_parts.append(f"{len(qualified)} new picks ({apply_count} apply-worthy)")
    if p["stale"]:
        summary_parts.append(f"{p['stale']} stale")
    content_status = "posted ✅" if content_cal.get("today_post", {}).get("status") == "Posted" else "pending"
    summary_parts.append(f"content {content_status}")
    gw_status = "🟢" if system.get("gateway") == "UP" else "🔴"
    summary_parts.append(f"systems {gw_status}")

    add_callout(" | ".join(summary_parts), "☀️")

    # ==================== ACTION ITEMS (RED - TOP) ====================
    actions = []
    if p["interviews"]:
        for iv in p["interview_list"]:
            actions.append(f"🎯 Follow up {iv['company']} interview")
    action_emails = [e for e in emails if e.get("priority") == "action"]
    if action_emails:
        for ae in action_emails[:2]:
            actions.append(f"📧 Reply: {ae.get('subject', '')[:35]}")
    if qualified:
        apply_count = len([j for j in qualified if j.get("ats_score", 0) >= 50])
        actions.append(f"Review {len(qualified)} picks ({apply_count} worth applying)")
    if p["overdue"]:
        actions.append(f"Follow up {min(5, len(p['overdue']))} stale applications")
    if content_cal.get("today_post") and content_cal["today_post"]["status"] != "Posted":
        actions.append(f"Publish: \"{content_cal['today_post']['title'][:30]}\"")
    if content_cal.get("drafted", 0) == 0:
        actions.append("📝 Content pipeline empty!")
    if tasks.get("overdue"):
        actions.append(f"Address {len(tasks['overdue'])} overdue tasks")
    if isinstance(system.get('disk_pct'), int) and system['disk_pct'] >= 80:
        actions.append(f"⚠️ Disk {system['disk_pct']}%")
    if cal_error:
        actions.append("Fix Calendar auth")

    if actions:
        add_callout("ACTION ITEMS\n" + "\n".join(f"{i}. {a}" for i, a in enumerate(actions[:7], 1)), "🔴")
    else:
        add_callout("All clear - no urgent actions", "✅")

    add_divider()

    # ==================== PIPELINE ====================
    add_heading("📊 Pipeline")
    stale_pct = int(p['stale'] / max(p['total_applications'], 1) * 100)
    response_rate = p['interviews'] / max(p['total_applications'], 1) * 100
    add_para(f"{p['total_applications']} total | {p['applied']} applied | {p['interviews']} interviews | {p['stale']} stale ({stale_pct}%) | Response: {response_rate:.1f}%")

    if p["interview_list"]:
        for iv in p["interview_list"]:
            add_bullet(f"🎯 {iv['company']} - {iv['role']} ({iv['stage']})")

    if p["overdue"]:
        stale_items = [f"{'🔴' if o['days'] >= 21 else '🟡'} {o['company']} - {o['role']} ({o['days']}d)" for o in p["overdue"][:10]]
        add_toggle(f"⏰ {len(p['overdue'])} follow-ups overdue (oldest: {p['overdue'][0]['days']}d)", stale_items)

    if notion_changes:
        change_items = [f"{c['company']}: {c.get('old','?')} → {c.get('new','?')}" for c in notion_changes[:5]]
        add_toggle(f"🔄 {len(notion_changes)} Notion changes", change_items)

    add_divider()

    # ==================== SCANNER ====================
    add_heading("🔍 Scanner")
    if scanner_meta:
        total = scanner_meta.get("total_found", 0)
        picks = scanner_meta.get("priority_picks", 0)
        src = scanner_meta.get("source_status", {})
        src_str = " | ".join(f"{n}:{s}" for n, s in src.items()) if src else "LinkedIn, Indeed"
        freshness = "fresh" if scanner_age == 0 else f"{scanner_age}d old" if scanner_age else ""
        add_para(f"Found: {total} | Picks: {picks} | Sources: {src_str} | {freshness}")
    else:
        add_para("No scanner data available")

    if qualified:
        apply_jobs = [j for j in qualified if j.get("ats_score", 0) >= 50]
        skip_jobs = [j for j in qualified if j.get("ats_score", 0) < 50]

        def format_job(idx, j):
            title = j.get("title", "?")[:45]
            company = j.get("company", "")[:20]
            ats = j.get("ats_score", 0)
            city = j.get("location", "").split(",")[0].strip()[:12] if j.get("location") else ""
            url = j.get("url", "")
            icon = "🟢" if ats >= 75 else "🟡"
            text = f"{idx}. {icon} {title} @ {company}"
            if city:
                text += f" - {city}"
            text += f" ({ats}%)"
            if url:
                text += f" | {url}"
            return text

        # Top 5 APPLY jobs shown directly
        if apply_jobs:
            add_heading3(f"✅ APPLY ({len(apply_jobs)} jobs, ATS 50%+)")
            for idx, j in enumerate(apply_jobs[:5], 1):
                add_bullet(format_job(idx, j))

            # Rest in toggle
            if len(apply_jobs) > 5:
                more = [format_job(i, j) for i, j in enumerate(apply_jobs[5:], 6)]
                add_toggle(f"📋 {len(apply_jobs) - 5} more apply-worthy jobs...", more)

        # Skip in toggle (collapsed)
        if skip_jobs:
            skip_items = []
            for idx, j in enumerate(skip_jobs, len(apply_jobs) + 1):
                title = j.get("title", "?")[:45]
                company = j.get("company", "")[:20]
                ats = j.get("ats_score", 0)
                skip_items.append(f"{idx}. 🔴 {title} @ {company} ({ats}%)")
            add_toggle(f"❌ SKIP ({len(skip_jobs)} jobs, ATS below 50%)", skip_items)

    if trends.get("total_runs", 0) >= 3:
        add_para(f"Trend: {trends.get('trend','')} 7d avg: {trends.get('avg_7d_found',0):.0f} found, {trends.get('avg_7d_picks',0):.0f} picks")

    add_divider()

    # ==================== EMAIL + CALENDAR (compact row) ====================
    add_heading("📧 Email & Calendar")
    if emails:
        action_emails_list = [e for e in emails if e.get("priority") == "action"]
        job_emails = [e for e in emails if e.get("priority") in ("job", "linkedin")]
        reply_str = f" - {len(action_emails_list)} NEED REPLY" if action_emails_list else ""
        
        if action_emails_list:
            for e in action_emails_list:
                unread = " 🆕" if e.get("unread") else ""
                add_bullet(f"🔴 {e.get('subject', '')[:50]} - {e.get('sender', '')[:25]}{unread}")

        if job_emails:
            email_items = [f"🟡 {e.get('subject', '')[:50]} - {e.get('sender', '')[:25]}{'  🆕' if e.get('unread') else ''}" for e in job_emails[:10]]
            add_toggle(f"📧 {len(emails)} job-related emails{reply_str}", email_items)
    elif email_error:
        add_bullet(f"📧 ⚠️ {email_error}")
    else:
        add_bullet("📧 No job-related emails")

    if cal_error:
        add_bullet(f"📅 ⚠️ {cal_error}")
    elif events:
        for ev in events[:3]:
            title = ev.get("title", "Untitled")[:40]
            start = ev.get("start", "")
            time_str = str(start).split("T")[1][:5] if "T" in str(start) else ("All day" if ev.get("all_day") else "")
            add_bullet(f"📅 {title} ({time_str})" if time_str else f"📅 {title}")
    else:
        add_bullet("📅 Clear day ✅")

    add_divider()

    # ==================== CONTENT + ENGAGEMENT (merged) ====================
    add_heading("📝 Content & Engagement")
    status_parts = [f"{content_cal['posted']} posted", f"{content_cal['scheduled']} scheduled", f"{content_cal['drafted']} drafted"]
    add_para(" | ".join(status_parts))

    if content_cal.get("today_post"):
        tp = content_cal["today_post"]
        icon = "✅" if tp["status"] == "Posted" else "📋"
        add_bullet(f"Today: \"{tp['title'][:40]}\" [{tp['status']}] {icon}")
    if content_cal.get("tomorrow_post"):
        tp = content_cal["tomorrow_post"]
        add_bullet(f"Tomorrow: \"{tp['title'][:40]}\" [{tp['status']}]")

    if content_cal.get("drafted", 0) <= 1:
        add_bullet(f"⚠️ Only {content_cal['drafted']} draft(s) - pipeline drying up")
    
    add_bullet(f"🤝 {content_cal.get('posted', 0)} total posts | Goal: 3-5 GCC comments daily")

    add_divider()

    # ==================== TASKS + SYSTEM (compact) ====================
    add_heading("✅ Tasks & System")
    
    # Tasks
    overdue_str = f" | 🔴 {len(tasks['overdue'])} overdue" if tasks["overdue"] else ""
    due_str = f" | 📌 {len(tasks['due_today'])} due today" if tasks["due_today"] else ""
    done_str = f" | ✔️ {tasks['completed_recent']} done" if tasks.get("completed_recent") else ""
    add_para(f"Tasks: {tasks['total_open']} open{overdue_str}{due_str}{done_str}")
    
    if tasks["overdue"]:
        add_toggle(f"🔴 {len(tasks['overdue'])} overdue tasks", tasks["overdue"][:5])
    if tasks["due_today"]:
        for t in tasks["due_today"][:3]:
            add_bullet(f"📌 {t}")

    # System
    disk_warn = " ⚠️" if isinstance(system['disk_pct'], int) and system['disk_pct'] >= 80 else ""
    mem_warn = " ⚠️" if isinstance(system['mem_pct'], int) and system['mem_pct'] >= 85 else ""
    disabled_str = f" ({system['cron_disabled']} off)" if system.get("cron_disabled") else ""
    add_para(f"System: GW {system['gateway']} | Disk {system['disk_pct']}%{disk_warn} | Mem {system['mem_pct']}%{mem_warn} | Up {system['uptime']} | Crons {system['cron_enabled']}/{system['cron_total']}{disabled_str}")

    add_divider()

    # ==================== GITHUB DISCOVERY (if available) ====================
    if github_discovery and github_discovery.get("repos"):
        repos = github_discovery["repos"]
        age = " (yesterday)" if github_discovery.get("date") != datetime.now(cairo).strftime("%Y-%m-%d") else ""
        repo_items = []
        for r in repos[:5]:
            text = f"🔹 {r.get('name', '?')} - {r.get('desc', '')[:50]}"
            if r.get("why"):
                text += f" → {r['why'][:40]}"
            if r.get("url"):
                text += f" | {r['url']}"
            repo_items.append(text)
        add_toggle(f"🔭 {len(repos)} GitHub discoveries{age}", repo_items)
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
                           scanner_age, emails, email_error, events, cal_error, content_cal, github_discovery,
                           system, tasks, notion_changes, trends, notion_url):
    """Build compact Telegram briefing. Must be under 1500 chars."""
    p = pipeline
    lines = []
    lines.append(f"☀️ Morning Brief - {date_display}")

    # Action items first (red) - comprehensive, prioritized
    actions = []
    # Priority 1: Interviews
    if p["interviews"]:
        actions.append(f"🎯 {p['interviews']} INTERVIEW(S) active!")
    # Priority 2: Email replies needed
    action_emails = [e for e in emails if e.get("priority") == "action"]
    if action_emails:
        for ae in action_emails[:2]:
            actions.append(f"📧 Reply: {ae.get('subject', '')[:30]}")
    # Priority 3: New job picks
    if qualified:
        apply_count = len([q for q in qualified if q.get("ats_score", 0) >= 50])
        actions.append(f"Review {len(qualified)} picks ({apply_count} worth applying)")
    # Priority 4: Stale follow-ups
    if p["overdue"]:
        actions.append(f"Follow up {min(5, len(p['overdue']))} stale applications")
    # Priority 5: Content
    if content_cal.get("today_post") and content_cal["today_post"]["status"] != "Posted":
        actions.append(f"Publish: \"{content_cal['today_post']['title'][:25]}\"")
    if content_cal.get("drafted", 0) == 0:
        actions.append("📝 Content pipeline empty!")
    # Priority 6: Overdue tasks
    if tasks.get("overdue"):
        actions.append(f"Address {len(tasks['overdue'])} overdue tasks")
    # Priority 7: System issues
    if isinstance(system.get('disk_pct'), int) and system['disk_pct'] >= 80:
        actions.append(f"⚠️ Disk {system['disk_pct']}%")
    if cal_error:
        actions.append("Fix Google Calendar")

    if actions:
        lines.append("\n🔴 ACTION NEEDED")
        for i, a in enumerate(actions[:6], 1):
            lines.append(f"  {i}. {a}")
    else:
        lines.append("\n✅ All clear - no urgent actions")

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
                    # Clickable link format: [text](url)
                    lines.append(f"    [Apply →]({url})")

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
        lines.append(f"\n📅 CALENDAR: ⚠️ {cal_error[:25]}")
    elif events:
        lines.append(f"\n📅 CALENDAR: {len(events)} events today")
        for ev in events[:5]:
            title = ev.get("title", "Untitled")[:35]
            start = ev.get("start", "")
            # Extract time from ISO format
            time_str = ""
            if "T" in str(start):
                time_str = str(start).split("T")[1][:5]
            elif ev.get("all_day"):
                time_str = "All day"
            line = f"  📌 {title}"
            if time_str:
                line += f" ({time_str})"
            lines.append(line)
    else:
        lines.append(f"\n📅 CALENDAR: Clear ✅")

    # Content
    lines.append(f"\n📝 CONTENT: {content_cal['posted']} posted | {content_cal['scheduled']} scheduled | {content_cal['drafted']} drafted")
    if content_cal.get("today_post"):
        tp = content_cal["today_post"]
        status_icon = "✅" if tp["status"] == "Posted" else "📋"
        lines.append(f"  Today: \"{tp['title'][:35]}\" [{tp['status']}] {status_icon}")
    if content_cal.get("tomorrow_post"):
        tp = content_cal["tomorrow_post"]
        lines.append(f"  Tomorrow: \"{tp['title'][:35]}\" [{tp['status']}]")
    if content_cal.get("drafted", 0) <= 1:
        lines.append(f"  ⚠️ Only {content_cal['drafted']} draft(s) left - pipeline drying up")
    if content_cal.get("gap_days", 99) <= 3 and content_cal.get("scheduled", 0) > 0:
        lines.append(f"  ⚠️ Last scheduled post in {content_cal['gap_days']} days")

    # GitHub Discovery
    if github_discovery and github_discovery.get("repos"):
        repos = github_discovery["repos"]
        lines.append(f"\n🔭 GITHUB: {len(repos)} repos found")
        for r in repos[:3]:
            lines.append(f"  🔹 {r.get('name', '?')[:30]}")

    # LinkedIn Engagement
    lines.append(f"\n🤝 ENGAGEMENT:")
    if content_cal.get("today_post") and content_cal["today_post"]["status"] == "Posted":
        lines.append(f"  ✅ Posted today: \"{content_cal['today_post']['title'][:30]}\"")
    elif content_cal.get("today_post"):
        lines.append(f"  📋 Ready to post: \"{content_cal['today_post']['title'][:30]}\"")
    else:
        lines.append(f"  ⚠️ No post scheduled for today")
    lines.append(f"  Total: {content_cal.get('posted', 0)} posts | Goal: comment on 3-5 GCC posts daily")

    # Tasks
    if tasks["total_open"] > 0 or tasks["overdue"]:
        overdue_str = f" | 🔴 {len(tasks['overdue'])} overdue" if tasks["overdue"] else ""
        due_str = f" | 📌 {len(tasks['due_today'])} due today" if tasks["due_today"] else ""
        done_str = f" | ✔️ {tasks['completed_recent']} done" if tasks.get("completed_recent") else ""
        lines.append(f"\n✅ TASKS: {tasks['total_open']} open{overdue_str}{due_str}{done_str}")
        if tasks["overdue"]:
            for t in tasks["overdue"][:3]:
                lines.append(f"  🔴 {t}")
        if tasks["due_today"]:
            for t in tasks["due_today"][:3]:
                lines.append(f"  📌 {t}")

    # System
    disk_icon = " 🔴" if isinstance(system['disk_pct'], int) and system['disk_pct'] >= 80 else ""
    mem_icon = " 🔴" if isinstance(system['mem_pct'], int) and system['mem_pct'] >= 85 else ""
    lines.append(f"\n⚙️ SYSTEM: GW {system['gateway']} | Disk {system['disk_pct']}%{disk_icon} | Mem {system['mem_pct']}%{mem_icon} | Up {system['uptime']}")
    disabled_str = f" ({system['cron_disabled']} off)" if system.get("cron_disabled") else ""
    lines.append(f"  Crons: {system['cron_enabled']}/{system['cron_total']} active{disabled_str}")
    if system["errors"]:
        for err in system["errors"][:2]:
            lines.append(f"  ❌ {err}")

    # Notion link
    if notion_url:
        lines.append(f"\n📎 [View in Notion]({notion_url})")

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
            system, tasks, notion_changes, trends, github_discovery
        )
    else:
        log("  (dry-run - skipped)")
    log("")

    # ---- OUTPUT 2: TELEGRAM MESSAGE ----
    log("Output 2: Telegram message...")
    telegram_msg = build_telegram_message(
        date_display, pipeline, scanner_meta, qualified, borderline,
        scanner_age, emails, email_error, events, cal_error, content_cal, github_discovery,
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
