#!/usr/bin/env python3
"""Heartbeat v2 - System health check. Outputs clean JSON for cron agent."""
import json, subprocess, os, time
from datetime import datetime
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"

def run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except:
        return ""

def get_gateway_status():
    pid = run("pgrep -f 'openclaw.*gateway' | head -1")
    return {"status": "running" if pid else "down", "pid": pid}

def get_cron_failures():
    # Skip cron check - the dedicated Cron Watchdog (2h) handles this
    # Return empty - watchdog cron is separate and already works
    return []

def get_disk():
    out = run("df / --output=pcent | tail -1")
    try: return int(out.strip().replace('%', ''))
    except: return 0

def get_tasks_age():
    f = f"{WORKSPACE}/memory/active-tasks.md"
    if os.path.exists(f):
        age = time.time() - os.path.getmtime(f)
        return int(age / 3600)
    return 0

def get_scanner():
    from datetime import timezone
    cairo_hour = int(run("TZ=Africa/Cairo date +%H") or "0")
    today = run("TZ=Africa/Cairo date +%Y-%m-%d")
    f = f"{WORKSPACE}/jobs-bank/scraped/qualified-jobs-{today}.md"
    if cairo_hour < 7:
        return {"status": "not_checked", "total": 0}
    if not os.path.exists(f):
        return {"status": "missing", "total": 0}
    count = int(run(f"grep -c '##\\|linkedin.com/jobs' '{f}'") or "0")
    return {"status": "ok" if count > 0 else "empty", "total": count}

def get_fallbacks():
    today = run("date +%Y-%m-%d")
    log = f"/tmp/openclaw/openclaw-{today}.log"
    if not os.path.exists(log): return []
    lines = run(f"grep -i 'fallback\\|model.*fail\\|rate.limit' '{log}' | tail -5")
    return [l for l in lines.split('\n') if l.strip()][:5]

def get_bloated():
    sessions_dir = os.path.expanduser("~/.openclaw/sessions")
    if not os.path.isdir(sessions_dir): return []
    result = []
    for f in Path(sessions_dir).glob("*.json"):
        size = f.stat().st_size
        if size > 5 * 1024 * 1024:
            result.append({"file": f.name, "size_mb": round(size / (1024*1024), 1)})
    return result

report = {
    "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "cairo_time": run("TZ=Africa/Cairo date +%H:%M"),
    "gateway": get_gateway_status(),
    "cron_failures": get_cron_failures(),
    "disk_usage_pct": get_disk(),
    "active_tasks_age_hours": get_tasks_age(),
    "scanner": get_scanner(),
    "model_fallbacks": get_fallbacks(),
    "bloated_sessions": get_bloated(),
    "upcoming_deadlines": []
}

print(json.dumps(report, indent=2))
