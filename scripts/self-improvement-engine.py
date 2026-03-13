#!/usr/bin/env python3
"""
Self-Improvement Engine (SIE) for OpenClaw
==========================================
Monitors ALL 26 areas (A-Z) of the OpenClaw system and generates insights.

Usage:
    python3 self-improvement-engine.py              # Full analysis + writes
    python3 self-improvement-engine.py --dry-run   # Report only, no file writes
    python3 self-improvement-engine.py --json      # JSON output to stdout

Deterministic thresholds per Section 14 of the spec.
"""

import json
import os
import sys
import re
import subprocess
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

# === Configuration ===
WORKSPACE = "/root/.openclaw/workspace"
HEARTBEAT_DIR = f"{WORKSPACE}/.heartbeat"
MEMORY_DIR = f"{WORKSPACE}/memory"
SESSIONS_DIR = "/root/.openclaw/agents/main/sessions"
SCRIPTS_DIR = f"{WORKSPACE}/scripts"
LEARNINGS_FILE = f"{WORKSPACE}/.learnings/LEARNINGS.md"
GATEWAY_LOG = "/root/.openclaw/gateway.log"
STATE_FILE = f"{HEARTBEAT_DIR}/sie-state.json"
OUTPUT_FILE = f"{MEMORY_DIR}/insights.md"

CAIRO_TZ = timezone(timedelta(hours=2))

# === Helper Functions ===

def log(msg):
    """Log to stderr."""
    ts = datetime.now(CAIRO_TZ).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr, flush=True)


def run_cmd(cmd, timeout=5):
    """Run shell command with timeout, return stdout."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", -1
    except Exception as e:
        return str(e), -1


def file_age_hours(filepath):
    """Get file age in hours."""
    if not os.path.exists(filepath):
        return 999
    try:
        mtime = os.path.getmtime(filepath)
        age = (datetime.now().timestamp() - mtime) / 3600
        return round(age, 1)
    except:
        return 999


def read_json(filepath, default=None):
    """Read JSON file safely."""
    if default is None:
        default = {}
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath) as f:
            return json.load(f)
    except:
        return default


def write_json(filepath, data):
    """Write JSON file safely."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


# === State Management ===

def load_state():
    """Load SIE state."""
    return read_json(STATE_FILE, {
        "last_run": None,
        "run_count": 0,
        "areas": {},
        "health_score": 100,
        "history": []
    })


def save_state(state):
    """Save SIE state with history trimming."""
    # Keep last 30 history entries
    if "history" in state:
        state["history"] = state["history"][-30:]
    write_json(STATE_FILE, state)


# === Area Checks (A-Z) ===

def check_applications(state):
    """A - Applications: Track ATS score distribution."""
    # Check for recent CV/ATS scoring activity
    ats_scores = []
    ats_dir = f"{WORKSPACE}/memory"
    
    # Scan for ATS score files
    for root, dirs, files in os.walk(ats_dir):
        for f in files:
            if "ats" in f.lower() or "score" in f.lower():
                path = os.path.join(root, f)
                content = open(path).read() if os.path.exists(path) else ""
                # Look for score patterns like "82/100" or "Score: 85"
                matches = re.findall(r'(\d{2,3})/100', content)
                ats_scores.extend([int(m) for m in matches if 50 <= int(m) <= 100])
    
    if ats_scores:
        avg = sum(ats_scores) / len(ats_scores)
        if avg < 85:
            return "ALERT", f"ATS avg {avg:.0f} below threshold (85)"
        return "OK", f"ATS avg {avg:.0f}, {len(ats_scores)} scores tracked"
    return "OK", "No recent ATS data"


def check_backups(state):
    """B - Backups: Check last git commit age."""
    stdout, code = run_cmd(f"cd {WORKSPACE} && git log -1 --format=%ci 2>/dev/null")
    if code != 0 or not stdout:
        return "ALERT", "Git commit unavailable"
    
    # Parse ISO date
    try:
        commit_time = datetime.fromisoformat(stdout.replace(" +0000", ""))
        age_hours = (datetime.now() - commit_time.replace(tzinfo=None)).total_seconds() / 3600
        if age_hours > 24:
            return "ALERT", f"Git stale: {age_hours:.0f}h since last commit"
        return "OK", f"Last commit {age_hours:.1f}h ago"
    except:
        return "WARN", "Could not parse commit time"


def check_crons(state):
    """C - Crons: Check failure count."""
    # Try openclaw cron list with timeout
    stdout, code = run_cmd("timeout 10 openclaw cron list --json 2>/dev/null", timeout=15)
    if code != 0 or not stdout:
        # Fallback: check cron DB file directly
        cron_db = os.path.expanduser("~/.openclaw/cron.json")
        if os.path.exists(cron_db):
            try:
                with open(cron_db) as f:
                    data = json.load(f)
                jobs = data if isinstance(data, list) else data.get("jobs", [])
                failures = [j for j in jobs if j.get("state", {}).get("lastError")]
                if len(failures) > 2:
                    return "ALERT", f"{len(failures)} cron failures detected"
                if failures:
                    return "WARN", f"{len(failures)} cron failures"
                return "OK", f"{len(jobs)} crons healthy"
            except:
                pass
        return "OK", "Crons running (could not query gateway)"
    
    # Extract JSON from output (skip config warnings)
    try:
        json_start = stdout.find('{')
        if json_start == -1:
            json_start = stdout.find('[')
        if json_start > 0:
            stdout = stdout[json_start:]
        
        crons = json.loads(stdout) if stdout else []
        if isinstance(crons, dict) and "jobs" in crons:
            crons = crons["jobs"]
    except:
        return "OK", "Crons running (parse skipped)"
    
    failures = [c for c in crons if "error" in str(c.get("status", "")).lower() 
                or "fail" in str(c.get("status", "")).lower()]
    
    if len(failures) > 2:
        return "ALERT", f"{len(failures)} cron failures detected"
    if len(failures) > 0:
        return "WARN", f"{len(failures)} cron failures"
    return "OK", f"{len(crons)} crons healthy"


def check_disk(state):
    """D - Disk: Check usage percentage."""
    stdout, code = run_cmd("df / --output=pcent 2>/dev/null | tail -1 | tr -d ' %'")
    if code != 0:
        return "WARN", "Could not check disk"
    
    try:
        usage = int(stdout)
    except:
        return "WARN", "Could not parse disk usage"
    
    if usage >= 95:
        return "CRITICAL", f"Disk {usage}% - immediate action needed"
    if usage >= 85:
        return "ALERT", f"Disk {usage}% approaching limit"
    return "OK", f"Disk {usage}%"


def check_errors(state):
    """E - Errors: Scan logs for new error patterns."""
    error_patterns = defaultdict(int)
    
    # Scan gateway log
    if os.path.exists(GATEWAY_LOG):
        try:
            with open(GATEWAY_LOG) as f:
                lines = f.readlines()
            
            recent = lines[-500:] if len(lines) > 500 else lines
            for line in recent:
                # Extract error type
                if "error" in line.lower() or "exception" in line.lower():
                    # Extract first 50 chars of potential error
                    match = re.search(r'(error|exception)[:\s]+([^\n]{10,50})', line, re.I)
                    if match:
                        error_patterns[match.group(2)[:50]] += 1
        except:
            pass
    
    # Check for recurring errors (3+ occurrences)
    recurring = {k: v for k, v in error_patterns.items() if v >= 3}
    if recurring:
        worst = max(recurring.items(), key=lambda x: x[1])
        return "ALERT", f"Recurring: '{worst[0][:40]}' ({worst[1]}x)"
    if error_patterns:
        return "WARN", f"{len(error_patterns)} unique errors in recent logs"
    return "OK", "No significant errors"


def check_feedback(state):
    """F - Feedback: Check unprocessed corrections."""
    # Check for recent corrections in learnings
    if not os.path.exists(LEARNINGS_FILE):
        return "OK", "No learnings file"
    
    try:
        with open(LEARNINGS_FILE) as f:
            content = f.read()
        
        # Count unprocessed (no "applied", "resolved", "promoted", "fix" tag)
        sections = [s for s in content.split("##") if "[LRN-" in s]
        unprocessed = len([s for s in sections 
                          if not any(kw in s.lower() for kw in ["applied", "resolved", "promoted", "fix applied", "fix:", "rule:"])])
        
        if unprocessed > 3:
            return "ALERT", f"{unprocessed} unprocessed corrections"
        if unprocessed > 0:
            return "WARN", f"{unprocessed} unprocessed corrections"
    except:
        pass
    
    return "OK", "Feedback processed"


def check_gateway(state):
    """G - Gateway: Check uptime and restarts."""
    # First check if gateway process is running
    stdout, code = run_cmd("pgrep -f openclaw-gateway", timeout=3)
    
    if code != 0 or not stdout.strip():
        return "CRITICAL", "Gateway process not found"
    
    # Count restarts in last 24h from log
    restart_count = 0
    if os.path.exists(GATEWAY_LOG):
        try:
            with open(GATEWAY_LOG) as f:
                lines = f.readlines()
            
            # Look for restart patterns in last 500 lines
            recent = lines[-500:] if len(lines) > 500 else lines
            restart_count = sum(1 for l in recent if "starting" in l.lower() and "gateway" in l.lower())
        except:
            pass
    
    if restart_count > 3:
        return "ALERT", f"Gateway restarted {restart_count}x in 24h"
    
    return "OK", f"Gateway running (PID: {stdout.strip().split()[0]})"


def check_heartbeat(state):
    """H - Heartbeat: Check success rate."""
    state_file = f"{HEARTBEAT_DIR}/state.json"
    data = read_json(state_file)
    
    if not data:
        return "WARN", "No heartbeat state"
    
    # Calculate success rate from checks
    checks = data.get("checks", {})
    if not checks:
        return "OK", "No heartbeat failures"
    
    total = len(checks)
    failed = sum(1 for c in checks.values() if not c.get("success", True))
    success_rate = ((total - failed) / total * 100) if total > 0 else 100
    
    if success_rate < 90:
        return "ALERT", f"Heartbeat success {success_rate:.0f}% < 90%"
    return "OK", f"Heartbeat {success_rate:.0f}% success"


def check_integrations(state):
    """I - Integrations: Test Gmail, LinkedIn."""
    issues = []
    
    # Test gog gmail with correct syntax
    stdout, code = run_cmd('GOG_KEYRING_PASSWORD="" gog gmail ls "is:inbox" --max 1 -a ahmednasr999@gmail.com 2>/dev/null', timeout=15)
    if code != 0 or not stdout:
        issues.append("Gmail")
    
    # Test LinkedIn (via cookie file - check multiple paths)
    cookie_paths = [
        os.path.expanduser("~/.openclaw/cookies/linkedin.txt"),
        f"{WORKSPACE}/config/linkedin-cookies.txt",
        f"{WORKSPACE}/config/linkedin-cookies.json",
    ]
    if not any(os.path.exists(p) for p in cookie_paths):
        issues.append("LinkedIn (no cookie)")
    
    if len(issues) >= 2:
        return "ALERT", f"Failed: {', '.join(issues)}"
    if issues:
        return "WARN", f"Issue: {issues[0]}"
    return "OK", "Integrations healthy"


def check_jobs(state):
    """J - Jobs: Check radar yield."""
    # Check for recent job radar runs
    radar_file = f"{MEMORY_DIR}/job-radar.md"
    age = file_age_hours(radar_file)
    
    # Check for empty results in recent runs
    if os.path.exists(radar_file):
        try:
            with open(radar_file) as f:
                content = f.read()
            
            # Count job entries
            job_count = len(re.findall(r'###.*?job|##.*?position|^\|.*?\|.*?\|', content, re.I | re.M))
            
            if job_count == 0 and age < 24:
                return "ALERT", "0 jobs in recent radar"
            if job_count < 5 and age < 24:
                return "WARN", f"Low yield: {job_count} jobs"
        except:
            pass
    
    if age > 72:
        return "WARN", f"Radar stale: {age:.0f}h"
    return "OK", "Job radar functional"


def check_knowledge(state):
    """K - Knowledge: Check memory file freshness."""
    memory_file = f"{WORKSPACE}/MEMORY.md"
    age = file_age_hours(memory_file)
    
    if age > 168:  # 7 days
        return "ALERT", f"MEMORY.md stale: {age/24:.0f}d"
    if age > 72:  # 3 days
        return "WARN", f"MEMORY.md aging: {age/24:.0f}d"
    return "OK", f"MEMORY.md current"


def check_learnings(state):
    """L - Learnings: Check unapplied lessons."""
    if not os.path.exists(LEARNINGS_FILE):
        return "OK", "No learnings"
    
    try:
        with open(LEARNINGS_FILE) as f:
            content = f.read()
        
        # Count pending learnings
        pending = len(re.findall(r'\[LRN-\d+\](?!.*(?:applied|resolved))', content))
        
        if pending > 5:
            return "ALERT", f"{pending} pending learnings"
        if pending > 0:
            return "WARN", f"{pending} pending learnings"
    except:
        pass
    
    return "OK", "Learnings applied"


def check_models(state):
    """M - Models: Check fallback frequency."""
    # Count model fallbacks in gateway log
    fallbacks = []
    
    if os.path.exists(GATEWAY_LOG):
        try:
            with open(GATEWAY_LOG) as f:
                lines = f.readlines()
            
            recent = lines[-500:] if len(lines) > 500 else lines
            for line in recent:
                if "fallback" in line.lower() or "falling back" in line.lower():
                    fallbacks.append(line.strip()[:100])
        except:
            pass
    
    if len(fallbacks) > 3:
        return "ALERT", f"{len(fallbacks)} model fallbacks in 24h"
    if fallbacks:
        return "WARN", f"{len(fallbacks)} model fallbacks"
    return "OK", "Models stable"


def check_notifications(state):
    """N - Notifications: Check alert frequency."""
    # Check for recent Telegram alerts
    alert_count = 0
    
    if os.path.exists(GATEWAY_LOG):
        try:
            with open(GATEWAY_LOG) as f:
                lines = f.readlines()
            
            # Look for alert/sendMessage patterns in last 200 lines
            recent = lines[-200:] if len(lines) > 200 else lines
            alert_count = sum(1 for l in recent if "alert" in l.lower() or "telegram" in l.lower())
        except:
            pass
    
    if alert_count > 5:
        return "WARN", f"High alert volume: {alert_count} today"
    return "OK", "Notification volume normal"


def check_outputs(state):
    """O - Outputs: Check CV generation success."""
    # Check for recent CV files
    cv_dir = f"{WORKSPACE}/jobs-bank"
    recent_cvs = []
    
    for root, dirs, files in os.walk(cv_dir):
        for f in files:
            if f.endswith(".pdf") and "cv" in f.lower():
                path = os.path.join(root, f)
                age = file_age_hours(path)
                if age < 48:
                    recent_cvs.append((f, age))
    
    if not recent_cvs:
        return "WARN", "No recent CV outputs"
    return "OK", f"{len(recent_cvs)} CVs generated recently"


def check_pipeline(state):
    """P - Pipeline: Check conversion rate."""
    pipeline_file = f"{WORKSPACE}/jobs-bank/pipeline.md"
    
    if not os.path.exists(pipeline_file):
        return "WARN", "No pipeline file"
    
    try:
        with open(pipeline_file) as f:
            content = f.read()
        
        # Count stages
        applied = len(re.findall(r'Applied|applied', content))
        interview = len(re.findall(r'Interview|interview', content))
        
        if applied == 0:
            return "WARN", "No applications in pipeline"
        if interview == 0 and applied > 5:
            return "WARN", f"{applied} apps, 0 interviews"
    except:
        pass
    
    return "OK", "Pipeline active"


def check_quality(state):
    """Q - Quality: Check LinkedIn engagement."""
    # Check for recent engagement data (check daily folder and main file)
    engagement_dir = f"{WORKSPACE}/linkedin/engagement/daily"
    engagement_file = f"{WORKSPACE}/linkedin/engagement/engagement.md"
    # Check daily folder for recent files first
    if os.path.isdir(engagement_dir):
        try:
            files = sorted(os.listdir(engagement_dir), reverse=True)
            if files:
                engagement_file = os.path.join(engagement_dir, files[0])
        except:
            pass
    age = file_age_hours(engagement_file)
    
    if age > 168:  # 7 days
        return "WARN", f"Engagement stale: {age/24:.0f}d"
    return "OK", "Content quality tracked"


def check_reliability(state):
    """R - Reliability: Check session sizes."""
    if not os.path.exists(SESSIONS_DIR):
        return "WARN", "No sessions dir"
    
    bloated = []
    try:
        for f in os.listdir(SESSIONS_DIR):
            path = os.path.join(SESSIONS_DIR, f)
            if os.path.isfile(path):
                # Skip sessions.json (active DB, expected to be large)
                if f == "sessions.json":
                    continue
                size_mb = os.path.getsize(path) / (1024 * 1024)
                if size_mb > 5:
                    bloated.append((f, round(size_mb, 1)))
    except:
        return "WARN", "Could not check sessions"
    
    if bloated:
        worst = max(bloated, key=lambda x: x[1])
        return "ALERT", f"Session {worst[0]} is {worst[1]}MB"
    return "OK", f"Session sizes normal"


def check_skills(state):
    """S - Skills: Check skill execution errors."""
    # Check skill execution logs
    skill_errors = []
    
    # Look for recent skill failures in logs
    if os.path.exists(GATEWAY_LOG):
        try:
            with open(GATEWAY_LOG) as f:
                lines = f.readlines()
            
            recent = lines[-500:] if len(lines) > 500 else lines
            for line in recent:
                if "skill" in line.lower() and ("error" in line.lower() or "fail" in line.lower()):
                    skill_errors.append(line.strip()[:80])
        except:
            pass
    
    if len(skill_errors) > 2:
        return "ALERT", f"{len(skill_errors)} skill errors"
    if skill_errors:
        return "WARN", f"{len(skill_errors)} skill errors"
    return "OK", "Skills healthy"


def check_tools(state):
    """T - Tools: Check tool success rate."""
    # This would require more detailed logging
    # For now, check if critical tools exist
    critical_tools = [
        f"{SCRIPTS_DIR}/heartbeat-checks.sh",
        f"{SCRIPTS_DIR}/gateway-watchdog.sh",
    ]
    
    missing = [t for t in critical_tools if not os.path.exists(t)]
    
    if missing:
        return "ALERT", f"Missing tools: {', '.join(missing)}"
    return "OK", "Tools available"


def check_uptime(state):
    """U - Uptime: Check gateway availability."""
    # Ping the gateway
    stdout, code = run_cmd("curl -sf http://127.0.0.1:18789/health 2>/dev/null || echo 'down'")
    
    if "down" in stdout.lower() or code != 0:
        # Check if gateway process exists
        stdout2, _ = run_cmd("pgrep -f openclaw-gateway")
        if not stdout2:
            return "CRITICAL", "Gateway down"
        return "ALERT", "Gateway responding slowly"
    return "OK", "Gateway up"


def check_velocity(state):
    """V - Velocity: Count tasks completed/day."""
    # Check for recent session activity
    if not os.path.exists(SESSIONS_DIR):
        return "WARN", "No sessions"
    
    recent_sessions = []
    try:
        for f in os.listdir(SESSIONS_DIR):
            path = os.path.join(SESSIONS_DIR, f)
            if os.path.isfile(path):
                age = file_age_hours(path)
                if age < 24:
                    recent_sessions.append(f)
    except:
        pass
    
    if not recent_sessions:
        return "WARN", "No recent activity"
    return "OK", f"{len(recent_sessions)} sessions today"


def check_workspace(state):
    """W - Workspace: Count root files."""
    root_files = []
    
    try:
        for f in os.listdir(WORKSPACE):
            path = os.path.join(WORKSPACE, f)
            if os.path.isfile(path) and not f.startswith('.'):
                root_files.append(f)
    except:
        return "WARN", "Could not check workspace"
    
    if len(root_files) > 20:
        return "ALERT", f"{len(root_files)} files in root (clean recommended)"
    return "OK", f"{len(root_files)} files in root"


def check_execution(state):
    """X - Execution: Check command failure rate."""
    # Check for command failures in recent logs
    failures = []
    recent = []

    if os.path.exists(GATEWAY_LOG):
        try:
            with open(GATEWAY_LOG) as f:
                lines = f.readlines()

            recent = lines[-500:] if len(lines) > 500 else lines
            for line in recent:
                if "command failed" in line.lower() or "exit code" in line.lower():
                    failures.append(line.strip()[:60])
        except:
            pass

    total_lines = len(recent) if recent else 1
    failure_rate = len(failures) / total_lines

    if failure_rate > 0.2:
        return "ALERT", f"High failure rate: {failure_rate:.0%}"
    if failures:
        return "WARN", f"{len(failures)} command failures"
    return "OK", "Execution healthy"


def check_yield(state):
    """Y - Yield: Calculate ROI on time spent."""
    # This is a complex metric - check pipeline activity
    return check_pipeline(state)


def check_zero_downtime(state):
    """Z - Zero-downtime: Measure recovery time."""
    # Check for recent restart timestamps
    restarts = []
    
    if os.path.exists(GATEWAY_LOG):
        try:
            with open(GATEWAY_LOG) as f:
                lines = f.readlines()
            
            # Look for restart timestamps
            for line in lines[-100:]:
                if "gateway" in line.lower() and "start" in line.lower():
                    restarts.append(line.strip()[:60])
        except:
            pass
    
    if len(restarts) > 2:
        return "ALERT", f"{len(restarts)} restarts - stability issue"
    return "OK", "System stable"


# === Main Execution ===

# Map area letters to check functions
CHECKS = {
    "A": ("Applications", check_applications),
    "B": ("Backups", check_backups),
    "C": ("Crons", check_crons),
    "D": ("Disk", check_disk),
    "E": ("Errors", check_errors),
    "F": ("Feedback", check_feedback),
    "G": ("Gateway", check_gateway),
    "H": ("Heartbeat", check_heartbeat),
    "I": ("Integrations", check_integrations),
    "J": ("Jobs", check_jobs),
    "K": ("Knowledge", check_knowledge),
    "L": ("Learnings", check_learnings),
    "M": ("Models", check_models),
    "N": ("Notifications", check_notifications),
    "O": ("Outputs", check_outputs),
    "P": ("Pipeline", check_pipeline),
    "Q": ("Quality", check_quality),
    "R": ("Reliability", check_reliability),
    "S": ("Skills", check_skills),
    "T": ("Tools", check_tools),
    "U": ("Uptime", check_uptime),
    "V": ("Velocity", check_velocity),
    "W": ("Workspace", check_workspace),
    "X": ("Execution", check_execution),
    "Y": ("Yield", check_yield),
    "Z": ("Zero-downtime", check_zero_downtime),
}


def run_all_checks(state):
    """Run all 26 area checks."""
    results = {}
    
    for letter, (name, check_fn) in CHECKS.items():
        try:
            status, details = check_fn(state)
            results[letter] = {
                "name": name,
                "status": status,
                "details": details,
                "timestamp": datetime.now(CAIRO_TZ).isoformat()
            }
        except Exception as e:
            results[letter] = {
                "name": name,
                "status": "ERROR",
                "details": str(e)[:100],
                "timestamp": datetime.now(CAIRO_TZ).isoformat()
            }
    
    return results


def calculate_health_score(results):
    """Calculate overall health score 0-100."""
    if not results:
        return 100
    
    scores = {
        "OK": 100,
        "INFO": 90,
        "WARN": 70,
        "ALERT": 40,
        "CRITICAL": 10,
        "ERROR": 0
    }
    
    total = len(results)
    score_sum = sum(scores.get(r.get("status", "OK"), 50) for r in results.values())
    
    return round(score_sum / total)


def generate_insights(results, health_score, state):
    """Generate markdown insights."""
    now = datetime.now(CAIRO_TZ)
    timestamp = now.strftime("%Y-%m-%d %H:%M")
    
    # Group by severity
    critical = [(k, v) for k, v in results.items() if v["status"] == "CRITICAL"]
    alerts = [(k, v) for k, v in results.items() if v["status"] == "ALERT"]
    warnings = [(k, v) for k, v in results.items() if v["status"] == "WARN"]
    ok = [(k, v) for k, v in results.items() if v["status"] in ("OK", "INFO")]
    
    # Compare to previous run
    trends = []
    if state.get("areas"):
        for letter, result in results.items():
            prev = state["areas"].get(letter, {}).get("status")
            curr = result["status"]
            if prev and prev != curr:
                direction = "improved" if _status_order(curr) < _status_order(prev) else "declined"
                trends.append(f"- {result['name']}: {direction} from {prev} to {curr}")
    
    # Build markdown
    md = f"""# System Insights — {timestamp}

## System Health Score: {health_score}/100

"""
    
    if critical:
        md += "## Critical\n"
        for letter, r in critical:
            md += f"- [{letter}] {r['name']}: {r['details']}\n"
        md += "\n"
    
    if alerts:
        md += "## Alerts\n"
        for letter, r in alerts:
            md += f"- [{letter}] {r['name']}: {r['details']}\n"
        md += "\n"
    
    if warnings:
        md += "## Warnings\n"
        for letter, r in warnings:
            md += f"- [{letter}] {r['name']}: {r['details']}\n"
        md += "\n"
    
    if ok:
        md += "## All Clear\n"
        for letter, r in ok:
            md += f"- [{letter}] {r['name']}: {r['details']}\n"
        md += "\n"
    
    # Recommendations
    recommendations = []
    if critical:
        recommendations.append("Immediate attention required for critical issues")
    if alerts:
        recommendations.append("Review alerts and address within 24h")
    if warnings:
        recommendations.append("Monitor warning areas for deterioration")
    if health_score >= 90:
        recommendations.append("System healthy - continue monitoring")
    
    if recommendations:
        md += "## Recommendations\n"
        for rec in recommendations:
            md += f"- {rec}\n"
        md += "\n"
    
    if trends:
        md += "## Trends (vs last run)\n"
        for trend in trends:
            md += f"{trend}\n"
    
    return md


def _status_order(status):
    """Return numeric order for status severity."""
    order = {"OK": 0, "INFO": 1, "WARN": 2, "ALERT": 3, "CRITICAL": 4, "ERROR": 5}
    return order.get(status, 0)


def main():
    parser = argparse.ArgumentParser(description="Self-Improvement Engine for OpenClaw")
    parser.add_argument("--dry-run", action="store_true", help="Report only, no file writes")
    parser.add_argument("--json", action="store_true", help="Output JSON summary to stdout")
    args = parser.parse_args()
    
    log("=== Self-Improvement Engine (SIE) ===")
    
    # Load previous state
    state = load_state()
    prev_health = state.get("health_score", 100)
    
    # Run all checks
    log("Running 26 area checks...")
    results = run_all_checks(state)
    
    # Count by severity
    status_counts = defaultdict(int)
    for r in results.values():
        status_counts[r["status"]] += 1
    
    log(f"Results: {dict(status_counts)}")
    
    # Calculate health score
    health_score = calculate_health_score(results)
    log(f"Health score: {health_score}/100")
    
    # Generate insights
    insights_md = generate_insights(results, health_score, state)
    
    # Update state
    now_iso = datetime.now(CAIRO_TZ).isoformat()
    state["last_run"] = now_iso
    state["run_count"] = state.get("run_count", 0) + 1
    state["areas"] = results
    state["health_score"] = health_score
    
    # Add to history
    state.setdefault("history", []).append({
        "timestamp": now_iso,
        "health_score": health_score,
        "alerts": status_counts.get("ALERT", 0),
        "criticals": status_counts.get("CRITICAL", 0)
    })
    
    # Write outputs (unless dry-run)
    if not args.dry_run:
        log("Writing outputs...")
        write_json(STATE_FILE, state)
        
        os.makedirs(MEMORY_DIR, exist_ok=True)
        with open(OUTPUT_FILE, "w") as f:
            f.write(insights_md)
        
        log(f"Insights written to {OUTPUT_FILE}")
        log(f"State saved to {STATE_FILE}")
    else:
        log("Dry-run: skipping file writes")
    
    # JSON output to stdout
    if args.json:
        output = {
            "timestamp": now_iso,
            "health_score": health_score,
            "previous_health": prev_health,
            "status_counts": dict(status_counts),
            "areas": results,
            "dry_run": args.dry_run
        }
        print(json.dumps(output, indent=2))
    
    log("=== SIE Complete ===")
    
    # Exit code based on health
    if health_score < 50:
        sys.exit(2)
    elif health_score < 80:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
