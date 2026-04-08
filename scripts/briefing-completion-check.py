#!/usr/bin/env python3
"""
briefing-completion-check.py — Post-pipeline validator
Checks that the morning briefing pipeline actually completed all phases.
Returns exit code 0 if healthy, 1 if issues found.

Usage:
    python3 briefing-completion-check.py              # Check today
    python3 briefing-completion-check.py --date 2026-03-24
    python3 briefing-completion-check.py --alert       # Send Telegram alert on failure
"""
import json, os, sys, argparse, ssl
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

WORKSPACE = Path("/root/.openclaw/workspace")
CAIRO = timezone(timedelta(hours=2))
LOG_DIR = Path("/var/log/briefing")

def check_phase_log(date_str):
    """Check that the pipeline log shows all phases completed."""
    log_file = LOG_DIR / f"{date_str}.log"
    if not log_file.exists():
        return False, "No pipeline log found — script may not have run"
    
    content = log_file.read_text()
    
    # Required phases that should appear in the log
    required_markers = [
        ("Phase 0", "Phase 0: Heartbeat"),
        ("Phase 1", "Phase 1: Data"),
        ("Phase 2", "Phase 2: Merge"),
        ("Phase 7", "Phase 7: Generate Notion Briefing"),
        ("Phase 8", "Phase 8: Telegram Summary"),
    ]
    
    missing = []
    for label, marker in required_markers:
        if marker not in content:
            missing.append(label)
    
    if missing:
        return False, f"Missing phases: {', '.join(missing)}"
    
    return True, "All phases logged"


def check_notion_page(date_str):
    """Check that today's Notion briefing page exists."""
    try:
        config = json.load(open(WORKSPACE / "config" / "notion.json"))
        token = config["token"]
    except Exception as e:
        return False, f"Cannot load Notion token: {e}"
    
    BRIEFINGS_DB = "3268d599-a162-812d-a59e-e5496dec80e7"
    ctx = ssl.create_default_context()
    
    try:
        req = Request(
            f"https://api.notion.com/v1/databases/{BRIEFINGS_DB}/query",
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            },
            data=json.dumps({
                "filter": {"property": "Name", "title": {"contains": date_str}},
                "page_size": 1
            }).encode()
        )
        resp = urlopen(req, context=ctx, timeout=15)
        data = json.loads(resp.read())
        results = data.get("results", [])
        
        if results:
            url = results[0].get("url", "")
            return True, f"Found: {url}"
        else:
            return False, f"No briefing page for {date_str}"
    except Exception as e:
        return False, f"Notion API error: {e}"


def check_data_freshness(date_str):
    """Check that key data files were updated today."""
    issues = []
    today_ts = datetime.strptime(date_str, "%Y-%m-%d").timestamp()
    
    critical_files = {
        "data/jobs-raw/linkedin.json": "LinkedIn scrape",
        "data/email-summary.json": "Email scan",
        "data/jobs-merged.json": "Job merge",
    }
    
    for path, label in critical_files.items():
        full = WORKSPACE / path
        if not full.exists():
            issues.append(f"{label}: file missing")
            continue
        mtime = full.stat().st_mtime
        # File should be from today (within last 24h)
        if mtime < today_ts - 3600:  # allow 1h buffer before midnight
            age_h = round((datetime.now().timestamp() - mtime) / 3600, 1)
            issues.append(f"{label}: stale ({age_h}h old)")
    
    if issues:
        return False, "; ".join(issues)
    return True, "All data files fresh"


def check_briefing_telegram(date_str):
    """Check that the Telegram briefing was actually delivered (via cron state)."""
    try:
        cron_data = json.load(open("/root/.openclaw/cron/jobs.json"))
        for job in cron_data.get("jobs", []):
            if "brief" in job.get("name", "").lower():
                state = job.get("state", {})
                delivered = state.get("lastDelivered", False)
                status = state.get("lastRunStatus", "unknown")
                if delivered and status == "ok":
                    return True, "Cron delivered successfully"
                else:
                    return False, f"Cron status: {status}, delivered: {delivered}"
        return False, "Briefing cron not found"
    except Exception as e:
        return False, f"Cannot read cron state: {e}"


def send_alert(message, chat_id="866838380"):
    """Send Telegram alert via openclaw."""
    os.system(f'openclaw message send --channel telegram --to {chat_id} --message "{message}" 2>/dev/null')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now(CAIRO).strftime("%Y-%m-%d"))
    parser.add_argument("--alert", action="store_true", help="Send Telegram alert on failure")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()
    
    checks = {
        "pipeline_log": check_phase_log(args.date),
        "notion_page": check_notion_page(args.date),
        "data_freshness": check_data_freshness(args.date),
        "telegram_delivery": check_briefing_telegram(args.date),
    }
    
    all_ok = all(ok for ok, _ in checks.values())
    
    if args.json:
        print(json.dumps({
            "date": args.date,
            "all_ok": all_ok,
            "checks": {k: {"ok": ok, "detail": detail} for k, (ok, detail) in checks.items()}
        }, indent=2))
    else:
        print(f"=== Briefing Completion Check — {args.date} ===\n")
        for name, (ok, detail) in checks.items():
            status = "✅" if ok else "❌"
            print(f"  {status} {name}: {detail}")
        print(f"\n{'✅ ALL CHECKS PASSED' if all_ok else '❌ ISSUES DETECTED'}")
    
    if not all_ok and args.alert:
        failures = [f"{k}: {detail}" for k, (ok, detail) in checks.items() if not ok]
        send_alert(f"⚠️ Briefing Completion Check FAILED:\\n" + "\\n".join(failures))
    
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
