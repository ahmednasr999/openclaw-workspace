#!/usr/bin/env python3
"""
briefing-doctor.py — Daily health audit for the 12-part Morning Briefing Pipeline.

Runs at 5:30 AM Cairo (after pipeline completes).
Checks every part: did it run? did it produce output? how fast? any errors?
Scores the pipeline 0-100, flags issues, tracks trends.

Usage:
  python3 briefing-doctor.py              # Full audit + Telegram report
  python3 briefing-doctor.py --dry-run    # Preview without sending
  python3 briefing-doctor.py --history    # Show last 7 days trend
"""

import os
import json, os, sys, subprocess, glob
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
DATA_DIR = WORKSPACE / "data"
SCRIPTS = WORKSPACE / "scripts"
LOGS_DIR = WORKSPACE / "logs"
HISTORY_FILE = DATA_DIR / "briefing-doctor-history.json"
CAIRO = timezone(timedelta(hours=2))
CHAT_ID = "866838380"

now = datetime.now(CAIRO)
today = now.strftime("%Y-%m-%d")
today_log = LOGS_DIR / f"briefing-pipeline-{today}.log"


def load_json(path, default=None):
    try:
        return json.load(open(path))
    except Exception:
        return default or {}


def file_age_hours(path):
    """Return age of file in hours, or -1 if missing."""
    try:
        mtime = os.path.getmtime(path)
        age = (now.timestamp() - mtime) / 3600
        return round(age, 1)
    except Exception:
        return -1


def file_size_kb(path):
    try:
        return round(os.path.getsize(path) / 1024, 1)
    except Exception:
        return 0


def check_log_for_errors():
    """Parse today's pipeline log for errors and timing."""
    if not today_log.exists():
        return {"exists": False, "phases": {}, "errors": [], "duration_min": 0}
    
    content = today_log.read_text()
    lines = content.split("\n")
    
    errors = []
    phases = {}
    start_time = None
    end_time = None
    
    for line in lines:
        # Track phase starts
        if "Phase" in line and "---" in line:
            phase_name = line.split("---")[-1].strip().rstrip("-").strip() if "---" in line else ""
            if phase_name:
                phases[phase_name] = {"started": True, "errors": []}
        
        # Track errors
        lower = line.lower()
        if any(w in lower for w in ["error", "failed", "traceback", "exception", "timeout"]):
            if not any(noise in lower for noise in ["camofox", "plugin", "gateway closed"]):
                errors.append(line.strip()[:120])
        
        # Track timing
        if "[" in line and "]" in line:
            try:
                ts = line.split("]")[0].strip("[").strip()
                if len(ts) > 10:
                    if not start_time:
                        start_time = ts
                    end_time = ts
            except Exception:
                pass
    
    # Estimate duration
    duration_min = 0
    if "PIPELINE COMPLETE" in content:
        # Count lines as rough proxy
        duration_min = round(len([l for l in lines if l.strip()]) * 0.3, 1)
    
    return {
        "exists": True,
        "phases": phases,
        "errors": errors[:10],
        "completed": "PIPELINE COMPLETE" in content,
        "duration_min": duration_min,
    }


# ── PART CHECKS ──────────────────────────────────────────

def check_part_1():
    """Job Sourcing: 3 source files exist and have jobs."""
    issues = []
    score = 100
    stats = {}
    
    for name, fname in [("LinkedIn", "linkedin.json"), ("Indeed", "indeed.json"), ("Google", "google-jobs.json")]:
        path = DATA_DIR / "jobs-raw" / fname
        age = file_age_hours(path)
        data = load_json(path)
        
        if isinstance(data, dict):
            count = len(data.get("data", []))
        elif isinstance(data, list):
            count = len(data)
        else:
            count = 0
        
        stats[name] = {"count": count, "age_h": age}
        
        if age < 0:
            issues.append(f"{name}: file missing")
            score -= 30
        elif age > 25:
            issues.append(f"{name}: stale ({age}h old)")
            score -= 15
        elif count == 0:
            issues.append(f"{name}: 0 jobs")
            score -= 10
    
    return {"score": max(0, score), "issues": issues, "stats": stats}


def check_part_2():
    """Job Merge + Dedup."""
    path = DATA_DIR / "jobs-merged.json"
    age = file_age_hours(path)
    data = load_json(path)
    issues = []
    score = 100
    
    if age < 0:
        return {"score": 0, "issues": ["jobs-merged.json missing"], "stats": {}}
    if age > 25:
        issues.append(f"Stale: {age}h old")
        score -= 30
    
    jobs = data.get("data", data.get("jobs", []))
    count = len(jobs) if isinstance(jobs, list) else 0
    stats = {"merged_count": count, "age_h": age}
    
    if count == 0:
        issues.append("0 merged jobs")
        score -= 40
    elif count < 50:
        issues.append(f"Low count: {count} (usually 200+)")
        score -= 15
    
    return {"score": max(0, score), "issues": issues, "stats": stats}


def check_part_3():
    """Job Review + Scoring."""
    path = DATA_DIR / "jobs-summary.json"
    age = file_age_hours(path)
    data = load_json(path)
    issues = []
    score = 100
    
    if age < 0:
        return {"score": 0, "issues": ["jobs-summary.json missing"], "stats": {}}
    if age > 25:
        issues.append(f"Stale: {age}h old")
        score -= 30
    
    kpi = data.get("kpi", data.get("data", {}).get("kpi", {}))
    d = data.get("data", {})
    reviewed = d.get("reviewed", 0)
    total = d.get("total_candidates", 0)
    submit = kpi.get("submit_count", len(d.get("submit", [])))
    review = kpi.get("review_count", len(d.get("review", [])))
    fallback = kpi.get("fallback_pct", 0)
    
    stats = {"reviewed": reviewed, "total": total, "submit": submit, "review": review, "fallback_pct": fallback, "age_h": age}
    
    if total > 0 and reviewed < total * 0.5:
        issues.append(f"Only {reviewed}/{total} reviewed ({round(reviewed/total*100)}%)")
        score -= 20
    if fallback > 20:
        issues.append(f"High fallback: {fallback}% keyword-scored")
        score -= 15
    if submit == 0 and review == 0:
        issues.append("0 SUBMIT + 0 REVIEW (all skipped)")
        score -= 10
    
    return {"score": max(0, score), "issues": issues, "stats": stats}


def check_part_4():
    """Push to Notion Pipeline."""
    # Check if push ran by looking at log
    log = check_log_for_errors()
    issues = []
    score = 100
    
    if not log["exists"]:
        return {"score": 0, "issues": ["No pipeline log today"], "stats": {}}
    if not log["completed"]:
        issues.append("Pipeline did not complete")
        score -= 40
    
    return {"score": max(0, score), "issues": issues, "stats": {"log_exists": log["exists"], "completed": log.get("completed", False)}}


def check_part_5():
    """Email Scanning."""
    path = DATA_DIR / "email-summary.json"
    age = file_age_hours(path)
    data = load_json(path)
    issues = []
    score = 100
    
    if age < 0:
        return {"score": 0, "issues": ["email-summary.json missing"], "stats": {}}
    if age > 25:
        issues.append(f"Stale: {age}h old")
        score -= 30
    
    d = data.get("data", {})
    scanned = d.get("total_scanned", d.get("scanned_count", 0))
    stats = {"scanned": scanned, "age_h": age}
    
    if scanned == 0:
        issues.append("0 emails scanned")
        score -= 20
    
    return {"score": max(0, score), "issues": issues, "stats": stats}


def check_part_6():
    """LinkedIn Auto-Post."""
    path = DATA_DIR / "linkedin-post.json"
    age = file_age_hours(path)
    data = load_json(path)
    issues = []
    score = 100
    
    # This is OK to be old (only updates on post days)
    stats = {"age_h": age, "has_post": data.get("has_post", False)}
    
    # Check watchdog
    flag = Path("/tmp/linkedin-post-pending.flag")
    if flag.exists():
        flag_age = file_age_hours(str(flag))
        if flag_age > 2:
            issues.append(f"Stale watchdog flag ({flag_age}h old) - post may have failed")
            score -= 25
    
    return {"score": max(0, score), "issues": issues, "stats": stats}


def check_part_7():
    """Comment Radar."""
    # Find today's radar
    radar_path = DATA_DIR / "comment-radar.json"
    age = file_age_hours(radar_path)
    data = load_json(radar_path)
    issues = []
    score = 100
    
    if age < 0:
        return {"score": 0, "issues": ["comment-radar.json missing"], "stats": {}}
    if age > 25:
        issues.append(f"Stale: {age}h old")
        score -= 20
    
    posts = data.get("top_posts", data.get("data", {}).get("top_posts", []))
    drafted = sum(1 for p in posts if p.get("draft_comment"))
    stats = {"posts": len(posts), "drafted": drafted, "age_h": age}
    
    if len(posts) == 0:
        issues.append("0 posts found")
        score -= 15
    if drafted == 0 and len(posts) > 0:
        issues.append("Posts found but 0 drafts generated")
        score -= 10
    
    return {"score": max(0, score), "issues": issues, "stats": stats}


def check_part_8():
    """Outreach Tracker."""
    path = DATA_DIR / "outreach-suggestions.json"
    age = file_age_hours(path)
    data = load_json(path)
    issues = []
    score = 100
    
    if age < 0:
        # Try outreach-summary.json
        path2 = DATA_DIR / "outreach-summary.json"
        age = file_age_hours(path2)
        if age < 0:
            return {"score": 0, "issues": ["No outreach data files"], "stats": {}}
    
    if age > 25:
        issues.append(f"Stale: {age}h old")
        score -= 20
    
    suggestions = data.get("suggestions", [])
    stats = {"suggestions": len(suggestions), "age_h": age}
    
    return {"score": max(0, score), "issues": issues, "stats": stats}


def check_part_9():
    """System Health."""
    path = DATA_DIR / "system-health.json"
    age = file_age_hours(path)
    data = load_json(path)
    issues = []
    score = 100
    
    if age < 0:
        return {"score": 0, "issues": ["system-health.json missing"], "stats": {}}
    if age > 6:
        issues.append(f"Stale: {age}h old")
        score -= 20
    
    d = data.get("data", {})
    sys_info = d.get("system", {})
    disk = sys_info.get("disk_usage_pct", 0)
    agents = d.get("agents", {})
    healthy = agents.get("healthy_count", 0)
    total = agents.get("total", 0)
    stale = agents.get("stale_count", 0)
    
    stats = {"disk_pct": disk, "agents_healthy": healthy, "agents_total": total, "stale": stale, "age_h": age}
    
    if disk > 85:
        issues.append(f"Disk at {disk}%")
        score -= 20
    if stale > 1:
        issues.append(f"{stale} stale agents")
        score -= 10
    
    return {"score": max(0, score), "issues": issues, "stats": stats}


def check_part_10():
    """Briefing Page (Notion)."""
    issues = []
    score = 100
    
    # Check if Notion page exists for today
    try:
        import urllib.request, ssl
        token = json.load(open(os.path.expanduser("~/.openclaw/workspace/config/notion.json")))["token"]
        db_id = "3268d599-a162-812d-a59e-e5496dec80e7"
        payload = json.dumps({
            "filter": {"property": "Name", "title": {"contains": today}},
            "page_size": 1
        }).encode()
        req = urllib.request.Request(
            f"https://api.notion.com/v1/databases/{db_id}/query",
            data=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
        )
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            results = json.loads(resp.read()).get("results", [])
            if results:
                page_url = results[0].get("url", "")
                return {"score": 100, "issues": [], "stats": {"page_exists": True, "url": page_url}}
            else:
                return {"score": 0, "issues": ["No Notion briefing page for today"], "stats": {"page_exists": False}}
    except Exception as e:
        issues.append(f"Notion check failed: {str(e)[:60]}")
        score -= 30
    
    return {"score": max(0, score), "issues": issues, "stats": {}}


def check_part_11():
    """Telegram Summary."""
    # Can't easily verify Telegram was sent; check if pam-telegram.py ran in log
    log = check_log_for_errors()
    issues = []
    score = 100
    
    if not log["exists"]:
        return {"score": 50, "issues": ["No log - can't verify Telegram sent"], "stats": {}}
    
    content = today_log.read_text() if today_log.exists() else ""
    if "pam-telegram" in content or "Telegram Summary" in content:
        if "Sent to Telegram" in content:
            return {"score": 100, "issues": [], "stats": {"sent": True}}
        elif "Failed" in content and "telegram" in content.lower():
            issues.append("Telegram send failed (in log)")
            score -= 40
    else:
        issues.append("pam-telegram not found in log")
        score -= 20
    
    return {"score": max(0, score), "issues": issues, "stats": {}}


def check_part_12():
    """Calendar Events."""
    path = Path(f"/tmp/calendar-events-{today}.json")
    age = file_age_hours(str(path))
    issues = []
    score = 100
    
    if age < 0:
        issues.append("Calendar file missing for today")
        score -= 30
    elif age > 6:
        issues.append(f"Calendar stale: {age}h old")
        score -= 15
    
    data = load_json(str(path), [])
    events = data if isinstance(data, list) else data.get("events", [])
    stats = {"events": len(events), "age_h": age}
    
    return {"score": max(0, score), "issues": issues, "stats": stats}


# ── MAIN AUDIT ──────────────────────────────────────────

PARTS = [
    ("Part 1: Job Sourcing", check_part_1),
    ("Part 2: Job Merge", check_part_2),
    ("Part 3: Job Review", check_part_3),
    ("Part 4: Push to Notion", check_part_4),
    ("Part 5: Email Scan", check_part_5),
    ("Part 6: LinkedIn Post", check_part_6),
    ("Part 7: Comment Radar", check_part_7),
    ("Part 8: Outreach", check_part_8),
    ("Part 9: System Health", check_part_9),
    ("Part 10: Briefing Page", check_part_10),
    ("Part 11: Telegram", check_part_11),
    ("Part 12: Calendar", check_part_12),
]


def run_audit():
    results = {}
    total_score = 0
    all_issues = []
    
    for name, check_fn in PARTS:
        try:
            result = check_fn()
        except Exception as e:
            result = {"score": 0, "issues": [f"Check crashed: {str(e)[:80]}"], "stats": {}}
        
        results[name] = result
        total_score += result["score"]
        for issue in result["issues"]:
            all_issues.append(f"{name}: {issue}")
    
    pipeline_score = round(total_score / len(PARTS))
    
    # Grade
    if pipeline_score >= 90:
        grade = "A"
        emoji = "🟢"
    elif pipeline_score >= 75:
        grade = "B"
        emoji = "🟡"
    elif pipeline_score >= 50:
        grade = "C"
        emoji = "🟠"
    else:
        grade = "F"
        emoji = "🔴"
    
    return {
        "date": today,
        "timestamp": now.isoformat(),
        "pipeline_score": pipeline_score,
        "grade": grade,
        "emoji": emoji,
        "parts": results,
        "issues": all_issues,
        "issue_count": len(all_issues),
    }


def save_history(audit):
    """Append to rolling history (last 30 days)."""
    history = load_json(str(HISTORY_FILE), {"days": []})
    days = history.get("days", [])
    
    # Remove today if already exists
    days = [d for d in days if d.get("date") != today]
    
    # Add today
    days.append({
        "date": audit["date"],
        "score": audit["pipeline_score"],
        "grade": audit["grade"],
        "issue_count": audit["issue_count"],
        "parts": {name: r["score"] for name, r in audit["parts"].items()},
    })
    
    # Keep last 30 days
    days = sorted(days, key=lambda d: d["date"])[-30:]
    
    history["days"] = days
    history["updated"] = now.isoformat()
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def format_telegram(audit):
    """Format audit as Telegram message."""
    lines = []
    lines.append(f"{audit['emoji']} Briefing Doctor: {audit['pipeline_score']}/100 (Grade {audit['grade']})")
    lines.append("")
    
    # Part scores in a compact grid
    for name, result in audit["parts"].items():
        short = name.split(": ")[1] if ": " in name else name
        s = result["score"]
        icon = "✅" if s >= 90 else ("🟡" if s >= 70 else ("🟠" if s >= 50 else "🔴"))
        lines.append(f"  {icon} {short}: {s}")
    
    # Issues
    if audit["issues"]:
        lines.append("")
        lines.append(f"⚠️ {audit['issue_count']} issue(s):")
        for issue in audit["issues"][:5]:
            lines.append(f"  - {issue[:80]}")
        if len(audit["issues"]) > 5:
            lines.append(f"  ... +{len(audit['issues']) - 5} more")
    
    # Trend (last 3 days)
    history = load_json(str(HISTORY_FILE), {"days": []})
    recent = history.get("days", [])[-4:-1]  # Exclude today
    if recent:
        trend = " -> ".join(f"{d['score']}" for d in recent) + f" -> {audit['pipeline_score']}"
        lines.append("")
        lines.append(f"📈 Trend: {trend}")
    
    return "\n".join(lines)


def show_history():
    """Display last 7 days trend."""
    history = load_json(str(HISTORY_FILE), {"days": []})
    days = history.get("days", [])[-7:]
    
    if not days:
        print("No history yet. Run the audit first.")
        return
    
    print(f"\n{'Date':<12} {'Score':>6} {'Grade':>6} {'Issues':>7}")
    print("-" * 35)
    for d in days:
        print(f"{d['date']:<12} {d['score']:>5}/100 {d['grade']:>5} {d['issue_count']:>6}")
    
    # Part-level trend
    print(f"\nPart scores (last 7 days):")
    if days and "parts" in days[0]:
        for part_name in days[0].get("parts", {}):
            short = part_name.split(": ")[1] if ": " in part_name else part_name
            scores = [str(d.get("parts", {}).get(part_name, "?")) for d in days]
            print(f"  {short:<20} {' -> '.join(scores)}")


def send_telegram(text):
    """Send via openclaw message."""
    try:
        result = subprocess.run(
            ["openclaw", "message", "send", "--channel", "telegram",
             "--to", CHAT_ID, "--message", text],
            capture_output=True, text=True, timeout=15
        )
        return result.returncode == 0
    except Exception:
        return False


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    history_mode = "--history" in sys.argv
    
    if history_mode:
        show_history()
        sys.exit(0)
    
    print("🩺 Running Briefing Doctor audit...")
    audit = run_audit()
    
    print(f"\n{'='*50}")
    print(f"Pipeline Score: {audit['pipeline_score']}/100 (Grade {audit['grade']})")
    print(f"Issues: {audit['issue_count']}")
    print(f"{'='*50}")
    
    for name, result in audit["parts"].items():
        icon = "✅" if result["score"] >= 90 else ("🟡" if result["score"] >= 70 else "🔴")
        print(f"  {icon} {name}: {result['score']}/100")
        for issue in result["issues"]:
            print(f"      ⚠️ {issue}")
    
    if not dry_run:
        save_history(audit)
        print(f"\n📊 History saved ({HISTORY_FILE})")
    
    # Send Telegram if score < 90 OR there are issues
    msg = format_telegram(audit)
    print(f"\nTelegram message ({len(msg)} chars):")
    print(msg)
    
    if not dry_run:
        if audit["pipeline_score"] < 90 or audit["issue_count"] > 0:
            ok = send_telegram(msg)
            print(f"\n{'✅ Sent to Telegram' if ok else '❌ Telegram send failed'}")
        else:
            print("\n✅ Score 90+, no issues — silent (no Telegram)")
    else:
        print("\n[DRY RUN - not sent, not saved]")
