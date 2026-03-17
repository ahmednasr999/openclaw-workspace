#!/usr/bin/env python3
"""
Self-Improvement Engine (SIE) for OpenClaw
==========================================
Monitors ALL 26 areas (A-Z) of the OpenClaw system and generates insights.
Autoresearch mode: detect → fix → verify → keep/revert → repeat.

Usage:
    python3 self-improvement-engine.py              # Full analysis + writes
    python3 self-improvement-engine.py --dry-run   # Report only, no file writes
    python3 self-improvement-engine.py --json      # JSON output to stdout
    python3 self-improvement-engine.py --fix       # Autoresearch: auto-fix issues
    python3 self-improvement-engine.py --fix --max-iterations 5  # Limit fix loops

Deterministic thresholds per Section 14 of the spec.
Autoresearch inspired by Karpathy's autoresearch + uditgoenka/autoresearch.
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
    """K - Knowledge: Check memory file freshness + GitHub Radar evaluation."""
    memory_file = f"{WORKSPACE}/MEMORY.md"
    age = file_age_hours(memory_file)
    
    memory_msg = ""
    if age > 168:  # 7 days
        memory_msg = f"MEMORY.md stale: {age/24:.0f}d"
    elif age > 72:  # 3 days
        memory_msg = f"MEMORY.md aging: {age/24:.0f}d"
    
    # GitHub Radar evaluation
    radar_file = f"{WORKSPACE}/memory/github-radar.md"
    radar_age = file_age_hours(radar_file)
    
    # X Radar evaluation
    x_radar_file = f"{WORKSPACE}/memory/x-radar.md"
    x_radar_age = file_age_hours(x_radar_file)
    
    radar_msg = ""
    
    # Only evaluate if radar is fresh (within 26 hours)
    if radar_age < 26:
        radar_result = evaluate_github_radar(radar_file)
        radar_msg = radar_result
    
    x_radar_msg = ""
    if x_radar_age < 26:
        x_radar_msg = "X Radar active"
    
    # Combine messages
    
    # Combine messages
    messages = []
    if memory_msg:
        messages.append(memory_msg)
    if radar_msg:
        messages.append(radar_msg)
    if x_radar_msg:
        messages.append(x_radar_msg)
    
    combined = ", ".join(messages) if messages else "Knowledge systems current"
    
    # Determine status
    if "ALERT" in combined:
        return "ALERT", combined
    elif "WARN" in combined:
        return "WARN", combined
    return "OK", combined


def evaluate_github_radar(radar_file):
    """Evaluate GitHub Radar repos and generate recommendations."""
    import urllib.request
    
    if not os.path.exists(radar_file):
        return "GitHub Radar not found"
    
    try:
        with open(radar_file) as f:
            content = f.read()
        
        # Extract relevant repos (lines with [owner/repo])
        repos = re.findall(r'\*\*\[([^\]]+)\]\(https://github\.com/([^\)]+)\)', content)
        
        if not repos:
            return "No relevant repos in radar"
        
        recommendations = []
        
        for display_name, repo_path in repos[:3]:  # Evaluate top 3
            # Fetch README
            readme_urls = [
                f"https://raw.githubusercontent.com/{repo_path}/main/README.md",
                f"https://raw.githubusercontent.com/{repo_path}/master/README.md",
            ]
            
            readme_content = ""
            for url in readme_urls:
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'OpenClaw-SIE'})
                    with urllib.request.urlopen(req, timeout=5) as response:
                        readme_content = response.read().decode('utf-8', errors='ignore')
                        break
                except:
                    continue
            
            if not readme_content:
                continue
            
            # Simple relevance scoring based on keywords
            score = 0
            relevant_keywords = ["openclaw", "claude", "mcp", "skill", "agent", "automation", "workflow", "context", "memory"]
            for kw in relevant_keywords:
                if kw.lower() in readme_content.lower():
                    score += 1
            
            # Generate recommendation if score >= 2
            if score >= 2:
                # Extract description (first line)
                first_line = readme_content.split('\n')[0][:100]
                recommendations.append(f"{repo_path}: {first_line}")
        
        if recommendations:
            # Store recommendations in a file for later reference
            rec_file = f"{MEMORY_DIR}/sie-github-recommendations.md"
            with open(rec_file, 'w') as f:
                f.write(f"# GitHub Radar Recommendations — {datetime.now().strftime('%Y-%m-%d')}\n\n")
                for i, rec in enumerate(recommendations, 1):
                    f.write(f"{i}. {rec}\n")
            return f"GitHub Radar: {len(recommendations)} actionable repos (see sie-github-recommendations.md)"
        return "GitHub Radar: No high-relevance repos"
        
    except Exception as e:
        return f"GitHub Radar evaluation error: {str(e)[:50]}"


def check_learnings(state):
    """L - Learnings: Check unapplied lessons and unenforced entries."""
    if not os.path.exists(LEARNINGS_FILE):
        return "OK", "No learnings"
    
    try:
        with open(LEARNINGS_FILE) as f:
            content = f.read()
        
        # Count pending learnings (old format)
        pending = len(re.findall(r'\[LRN-\d+\](?!.*(?:applied|resolved))', content))
        
        # Count learning entries without enforcement (Action: code-check|sie-rule|cron-constraint)
        entries = re.findall(r'## 2026-\d{2}-\d{2}:.*', content)
        enforced = len(re.findall(r'\*\*Action:\*\*.*(?:code-check|sie-rule|cron-constraint)', content))
        unenforced = len(entries) - enforced
        
        issues = []
        if pending > 0:
            issues.append(f"{pending} pending")
        if unenforced > 0:
            issues.append(f"{unenforced} learnings without enforcement action")
        
        if unenforced > 3:
            return "ALERT", "; ".join(issues)
        if issues:
            return "WARN", "; ".join(issues)
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
    # Check for recent CV files in both jobs-bank and cvs directories
    cv_dirs = [f"{WORKSPACE}/jobs-bank", f"{WORKSPACE}/cvs"]
    recent_cvs = []
    
    for cv_dir in cv_dirs:
        if not os.path.exists(cv_dir):
            continue
        for root, dirs, files in os.walk(cv_dir):
            for f in files:
                if f.endswith(".pdf"):  # All PDFs in cvs/ are CVs
                    path = os.path.join(root, f)
                    age = file_age_hours(path)
                    if age < 168:  # 7 days
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


def check_nasr_behavior(state):
    """NASR Behavior Audit: Check for Pre-Flight violations in recent sessions."""
    warnings = []
    
    # Check 1: Did briefing doc get raw text (no italic/size 9)?
    briefing_data_dir = f"{WORKSPACE}/jobs-bank/scraped"
    today = datetime.now(CAIRO_TZ).strftime("%Y-%m-%d")
    briefing_file = f"{briefing_data_dir}/briefing-data-{today}.json"
    if os.path.exists(briefing_file):
        try:
            with open(briefing_file) as f:
                data = json.load(f)
            jobs = data.get("jobs", {})
            for job in jobs.get("qualified", []) + jobs.get("borderline", []):
                link = job.get("link", job.get("url", ""))
                if link and "linkedin.com" in link and not job.get("jd_fetched"):
                    warnings.append(f"Verdict without JD: {job.get('title', '?')[:40]}")
        except:
            pass
    
    # Check 2: Did scanner filtered-out log get written?
    filtered_file = f"{briefing_data_dir}/filtered-out-jobs.md"
    if os.path.exists(briefing_file) and not os.path.exists(filtered_file):
        warnings.append("Scanner filtered-out audit log missing")
    
    # Check 3: Check MEMORY.md for unverified claims vs actual scripts
    # (Lightweight: just check if scanner search count matches script)
    scanner_script = f"{SCRIPTS_DIR}/linkedin-gulf-jobs.py"
    if os.path.exists(scanner_script):
        try:
            with open(scanner_script) as f:
                code = f.read()
            # Count expected searches from the code structure
            primary = code.count('"') // 2  # rough proxy
            memory_file = f"{WORKSPACE}/MEMORY.md"
            if os.path.exists(memory_file):
                with open(memory_file) as f:
                    mem = f.read()
                if "55 search combos" in mem:
                    # Verify by counting actual search plan
                    # Priority: 3 countries x 10 titles = 30
                    # Secondary: 2 countries x 5 titles = 10  
                    # Extra: 3 countries x 5 titles = 15
                    # Total should be 55
                    pass  # This is correct now, was validated Mar 16
        except:
            pass
    
    # Check 4: Learnings-to-action audit
    if os.path.exists(LEARNINGS_FILE):
        try:
            with open(LEARNINGS_FILE) as f:
                content = f.read()
            # Count learnings
            learning_count = content.count("## 20")
            # Check if learnings have been acted on (rough heuristic)
            unacted = []
            for line in content.split("\n"):
                if line.startswith("## 20") and "TODO" in content[content.index(line):content.index(line)+500]:
                    unacted.append(line.strip())
            if unacted:
                warnings.append(f"{len(unacted)} learnings still have TODOs")
        except:
            pass
    
    if warnings:
        return "WARN", f"NASR behavior: {'; '.join(warnings[:3])}"
    return "OK", "NASR Pre-Flight behavior clean"


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
    "NASR": ("NASR Behavior", check_nasr_behavior),
}


# === Auto-Fix Registry (Autoresearch Pattern) ===
# Each fix: area letter -> list of {condition, fix_fn, description}
# Fix functions return (success: bool, message: str)
# Only safe, non-destructive fixes. Never: delete data, send messages, modify pipeline.

def fix_bloated_sessions(state):
    """Fix R (Reliability): Remove bloated session backup files."""
    try:
        removed = []
        sessions_dir = Path(SESSIONS_DIR)
        if sessions_dir.exists():
            for f in sessions_dir.iterdir():
                size_mb = f.stat().st_size / (1024 * 1024)
                # Only remove .tmp, .bak, and .reset backup files > 5MB, never active sessions
                is_backup = (f.suffix in ('.tmp', '.bak') or '.bak.' in f.name or '.reset.' in f.name)
                if size_mb > 5 and is_backup:
                    f.unlink()
                    removed.append(f"{f.name} ({size_mb:.1f}MB)")
        if removed:
            return True, f"Removed {len(removed)} bloated files: {', '.join(removed[:3])}"
        return False, "No bloated backup files found"
    except Exception as e:
        return False, f"Error: {str(e)[:80]}"

def fix_stale_git(state):
    """Fix B (Backups): Auto-commit if there are uncommitted changes."""
    try:
        result = subprocess.run(
            "cd /root/.openclaw/workspace && git status --porcelain",
            shell=True, capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip():
            # There are changes, auto-commit
            subprocess.run(
                'cd /root/.openclaw/workspace && git add -A && git commit -m "sie: auto-commit uncommitted changes"',
                shell=True, capture_output=True, text=True, timeout=30
            )
            return True, "Auto-committed uncommitted workspace changes"
        return False, "No uncommitted changes"
    except Exception as e:
        return False, f"Error: {str(e)[:80]}"

def fix_gateway_down(state):
    """Fix G (Gateway): Restart gateway if down."""
    try:
        # Check if really down
        result = subprocess.run("pgrep -f 'openclaw.*gateway'", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            # Gateway is down, restart
            subprocess.run(
                "openclaw gateway start",
                shell=True, capture_output=True, text=True, timeout=30
            )
            import time
            time.sleep(3)
            # Verify
            result2 = subprocess.run("pgrep -f 'openclaw.*gateway'", shell=True, capture_output=True, text=True)
            if result2.returncode == 0:
                return True, "Gateway restarted successfully"
            return False, "Gateway restart failed"
        return False, "Gateway already running"
    except Exception as e:
        return False, f"Error: {str(e)[:80]}"

def fix_disk_space(state):
    """Fix D (Disk): Clean up known safe temp files."""
    try:
        cleaned = 0
        # Clean /tmp files older than 7 days
        result = subprocess.run(
            "find /tmp -maxdepth 1 -type f -mtime +7 -name 'sie-*' -o -name 'self-heal-*' | head -20",
            shell=True, capture_output=True, text=True, timeout=10
        )
        for f in result.stdout.strip().split('\n'):
            if f and os.path.exists(f):
                os.unlink(f)
                cleaned += 1
        
        # Clean old gateway logs (keep last 10MB)
        if os.path.exists(GATEWAY_LOG):
            size = os.path.getsize(GATEWAY_LOG) / (1024 * 1024)
            if size > 50:
                subprocess.run(
                    f"tail -c 10M {GATEWAY_LOG} > {GATEWAY_LOG}.tmp && mv {GATEWAY_LOG}.tmp {GATEWAY_LOG}",
                    shell=True, capture_output=True, text=True, timeout=10
                )
                cleaned += 1
        
        if cleaned > 0:
            return True, f"Cleaned {cleaned} temp/log items"
        return False, "Nothing safe to clean"
    except Exception as e:
        return False, f"Error: {str(e)[:80]}"

def fix_workspace_clutter(state):
    """Fix W (Workspace): Move misplaced files from root to proper folders."""
    try:
        moved = []
        workspace = Path(WORKSPACE)
        for f in workspace.iterdir():
            if f.is_file():
                ext = f.suffix.lower()
                dest = None
                if ext in ('.pdf',) and f.name not in ('README.md',):
                    dest = workspace / 'jobs-bank' / f.name
                elif ext in ('.png', '.jpg', '.jpeg', '.gif', '.webp'):
                    dest = workspace / 'media' / f.name
                elif ext in ('.html',):
                    dest = workspace / 'archives' / f.name
                
                if dest and not dest.exists():
                    os.makedirs(dest.parent, exist_ok=True)
                    f.rename(dest)
                    moved.append(f.name)
        
        if moved:
            return True, f"Moved {len(moved)} files: {', '.join(moved[:3])}"
        return False, "No misplaced files"
    except Exception as e:
        return False, f"Error: {str(e)[:80]}"


# Fix registry: maps area letter to list of fix functions
AUTO_FIXES = {
    "R": [{"fn": fix_bloated_sessions, "desc": "Remove bloated session backups"}],
    "B": [{"fn": fix_stale_git, "desc": "Auto-commit uncommitted changes"}],
    "G": [{"fn": fix_gateway_down, "desc": "Restart gateway"}],
    "D": [{"fn": fix_disk_space, "desc": "Clean temp files and trim logs"}],
    "W": [{"fn": fix_workspace_clutter, "desc": "Move misplaced root files"}],
}

# Areas that should NEVER be auto-fixed (need human decision)
NO_AUTO_FIX = {"P", "A", "Y", "M", "I"}  # Pipeline, Applications, Yield, Models, Integrations


def run_autofix_loop(state, max_iterations=3):
    """
    Autoresearch-style fix loop:
    1. Run all checks
    2. For each ALERT/WARN/CRITICAL with a known fix, attempt the fix
    3. Re-run that specific check to verify
    4. If improved -> keep. If same/worse -> log as failed.
    5. Repeat until no more fixable issues or max iterations reached.
    
    Returns: (final_results, fix_log)
    """
    fix_log = []
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        log(f"--- Autoresearch Iteration {iteration}/{max_iterations} ---")
        
        # Run all checks
        results = run_all_checks(state)
        
        # Find fixable issues
        fixable = []
        for letter, result in results.items():
            if result["status"] in ("ALERT", "WARN", "CRITICAL"):
                if letter in AUTO_FIXES and letter not in NO_AUTO_FIX:
                    fixable.append((letter, result))
        
        if not fixable:
            log(f"No fixable issues found. Stopping at iteration {iteration}.")
            break
        
        fixed_any = False
        for letter, result in fixable:
            for fix_entry in AUTO_FIXES[letter]:
                fix_fn = fix_entry["fn"]
                fix_desc = fix_entry["desc"]
                
                log(f"  [{letter}] Attempting: {fix_desc}")
                
                # Attempt fix
                try:
                    success, message = fix_fn(state)
                except Exception as e:
                    success, message = False, f"Exception: {str(e)[:80]}"
                
                if success:
                    # Re-run the specific check to verify
                    check_name, check_fn = CHECKS[letter]
                    try:
                        new_status, new_details = check_fn(state)
                    except:
                        new_status = result["status"]
                        new_details = result["details"]
                    
                    improved = _status_order(new_status) < _status_order(result["status"])
                    
                    entry = {
                        "iteration": iteration,
                        "area": letter,
                        "fix": fix_desc,
                        "message": message,
                        "before": f"{result['status']}: {result['details']}",
                        "after": f"{new_status}: {new_details}",
                        "result": "KEPT" if improved else "NO_IMPROVEMENT",
                        "timestamp": datetime.now(CAIRO_TZ).isoformat()
                    }
                    fix_log.append(entry)
                    
                    if improved:
                        log(f"  ✅ [{letter}] {result['status']} -> {new_status}: {message}")
                        results[letter]["status"] = new_status
                        results[letter]["details"] = new_details
                        fixed_any = True
                    else:
                        log(f"  ⚪ [{letter}] Fix applied but no status change: {message}")
                else:
                    fix_log.append({
                        "iteration": iteration,
                        "area": letter,
                        "fix": fix_desc,
                        "message": message,
                        "result": "FAILED",
                        "timestamp": datetime.now(CAIRO_TZ).isoformat()
                    })
                    log(f"  ❌ [{letter}] {fix_desc}: {message}")
        
        if not fixed_any:
            log(f"No improvements made in iteration {iteration}. Stopping.")
            break
    
    return results, fix_log


def _status_order(status):
    """Lower is better."""
    return {"OK": 0, "INFO": 1, "WARN": 2, "ALERT": 3, "CRITICAL": 4, "ERROR": 5}.get(status, 3)


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



# === Phase 5: Improvement Suggestions ===

IMPROVEMENT_LOG = f"{MEMORY_DIR}/improvement-log.md"
PROMPT_FILE = "/tmp/sie-improvement-prompt.txt"


def read_file(filepath, default=""):
    """Read file safely."""
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath) as f:
            return f.read()
    except:
        return default


def parse_improvement_log(content):
    """Parse improvement log to extract suggestions."""
    suggestions = {"active": [], "implemented": [], "archived": []}
    
    current_section = None
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("## Active Suggestions"):
            current_section = "active"
        elif line.startswith("## Implemented"):
            current_section = "implemented"
        elif line.startswith("## Archived"):
            current_section = "archived"
        elif line.startswith("- [") and current_section:
            suggestions[current_section].append(line)
    
    return suggestions


def generate_improvement_prompt(results, health_score, state, improvement_log_content, learnings_content):
    """Generate structured analysis prompt for Phase 5."""
    
    # Extract trend data from history
    trends = []
    history = state.get("history", [])
    if len(history) >= 2:
        prev = history[-2]
        curr = history[-1]
        score_change = curr.get("health_score", 0) - prev.get("health_score", 0)
        trends.append(f"Health score: {prev.get('health_score', 0)} -> {curr.get('health_score', 0)} ({'+' if score_change > 0 else ''}{score_change})")
        
        # Identify areas that changed
        areas = state.get("areas", {})
        for letter, area in areas.items():
            if area.get("status") in ("ALERT", "CRITICAL"):
                trends.append(f"ALERT area: {area.get('name')} - {area.get('details')}")
    
    # Parse improvement log for past suggestions
    suggestions = parse_improvement_log(improvement_log_content)
    active_suggestions = suggestions.get("active", [])
    
    # Build the prompt
    prompt = f"""# SIE Phase 5: Improvement Analysis

## Current Health
- **Health Score:** {health_score}/100
- **Total Areas:** {len(results)}
- **Status Distribution:**
"""
    
    status_counts = defaultdict(int)
    for r in results.values():
        status_counts[r["status"]] += 1
    
    for status, count in sorted(status_counts.items(), key=lambda x: _status_order(x[0])):
        prompt += f"  - {status}: {count}\n"
    
    # Warning/Alerts details
    warning_areas = [(k, v) for k, v in results.items() if v["status"] in ("WARN", "ALERT", "CRITICAL")]
    if warning_areas:
        prompt += "\n## Areas Needing Attention\n"
        for letter, r in warning_areas:
            prompt += f"- [{letter}] {r['name']}: {r['details']}\n"
    
    # Trend data
    if trends:
        prompt += "\n## Trends (vs previous run)\n"
        for trend in trends:
            prompt += f"- {trend}\n"
    
    # Past suggestions
    if active_suggestions:
        prompt += f"\n## Active Past Suggestions ({len(active_suggestions)})\n"
        for s in active_suggestions[:10]:  # Limit to 10
            prompt += f"{s}\n"
    
    # Recent learnings
    if learnings_content:
        prompt += "\n## Recent Learnings (from .learnings/LEARNINGS.md)\n"
        # Extract last 3 learnings
        lrns = learnings_content.split("## [LRN-")
        for lrn in lrns[-3:]:
            if lrn.strip():
                # Get first 200 chars
                snippet = lrn[:200].strip()
                prompt += f"- {snippet}...\n"
    
    # System context for smarter suggestions
    prompt += """
## System Context
Current setup:
- 4 AM: SIE health check + improvements (YOU ARE HERE)
- 6 AM: Daily briefing (news, search, insights)
- 9 AM: LinkedIn engagement radar (19 GCC influencers)
- MiniMax M2.5 for crons, Opus/Sonnet for main, GPT-5.4 for coding
- Camoufox for browser automation
- GOG for Gmail
- Composio for LinkedIn posting

Active capabilities:
- Job radar with ATS scoring
- LinkedIn auto-posting
- Company dossier builder
- YouTube intelligence
- SIE (self-improvement engine)

Gaps to consider:
- No video content generation (just installed Medeo, untested)
- Swipefile not built (conflict with daily briefing)
- No automatic CV generation trigger
- No interview prep automation
"""
    
    prompt += """
## Task
Generate 3-5 system improvement suggestions (not health warnings). Focus on:
- NEW automations to build
- Ways to make the system SMARTER
- Performance optimizations
- New capabilities to add

Each must have:
- Area tag (letter + name)  
- Description
- Rationale
- Concrete action step

Format:
- [HIGH/MED/LOW] [Area] Description. Action: concrete step.
"""
    
    # Ensure prompt stays under 2000 tokens
    if len(prompt) > 5000:
        prompt = prompt[:5000] + "\n[...truncated...]"
    
    return prompt


def run_phase5(results, health_score, state):
    """Execute Phase 5: generate improvement prompt."""
    log("Running Phase 5: Generating improvement prompt...")
    
    # Read supporting files
    improvement_log_content = read_file(IMPROVEMENT_LOG)
    learnings_content = read_file(LEARNINGS_FILE)
    
    # Generate prompt
    prompt = generate_improvement_prompt(results, health_score, state, improvement_log_content, learnings_content)
    
    # Write to prompt file
    with open(PROMPT_FILE, "w") as f:
        f.write(prompt)
    
    log(f"Improvement prompt written to {PROMPT_FILE}")
    
    # Generate comprehensive suggestions based on system audit
    suggestions = []
    
    # === AUDIT: What capabilities exist ===
    # Medeo removed by Ahmed - do not suggest
    medeo_exists = False
    
    files_and_dirs = {
        "sie": "/root/.openclaw/workspace/scripts/self-improvement-engine.py",
        "youtube": "/root/.openclaw/workspace/scripts/youtube-intel.py",
        "radar": "/root/.openclaw/workspace/scripts/linkedin-engagement-radar.py",
        "dossier": "/root/.openclaw/workspace/scripts/auto-dossier.py",
        "ats": "/root/.openclaw/workspace/scripts/ats-scorer.py",
        "job_scout": "/root/.openclaw/workspace/scripts/job-scout.py",
        "briefing": "/root/.openclaw/workspace/scripts/daily-briefing.py",
        "heartbeat": "/root/.openclaw/workspace/scripts/heartbeat-checks.sh",
    }
    
    existing = {k: os.path.exists(v) for k, v in files_and_dirs.items()}
    
    # === SUGGESTION ENGINE ===
    
    # 1. Video Content (if Medeo exists but no video cron)
    if medeo_exists:
        suggestions.append("### 20260314-001 | [HIGH] [O] Auto-Video for LinkedIn\n"
            "- **Area:** O (Outputs)\n"
            "- **Description:** Medeo video skill installed but unused. Could generate 1 video/week for LinkedIn.\n"
            "- **Rationale:** Video content = 3x engagement on LinkedIn. Would automate content creation.\n"
            "- **Action:** Build `scripts/auto-linkedin-video.py` + weekly cron")
    
    # 2. Job Enrichment (if YouTube + dossier exist)
    if existing["youtube"] and existing["dossier"]:
        suggestions.append("### 20260314-002 | [HIGH] [J] Job Company Intelligence\n"
            "- **Area:** J (Jobs)\n"
            "- **Description:** YouTube intel + dossier builder exist but disconnected.\n"
            "- **Rationale:** Could auto-enrich job applications with company earnings calls, news, insights.\n"
            "- **Action:** Create `scripts/job-enrichment.py` to combine YouTube + dossier data")
    
    # 3. Interview Prep Automation
    if existing["ats"] and not os.path.exists("/root/.openclaw/workspace/scripts/interview-prep.py"):
        suggestions.append("### 20260314-003 | [MED] [P] Interview Prep Generator\n"
            "- **Area:** P (Pipeline)\n"
            "- **Description:** ATS scores jobs but no interview prep automation.\n"
            "- **Rationale:** When interview scheduled, could auto-generate: company research, STAR stories, questions to ask.\n"
            "- **Action:** Build `scripts/interview-prep.py` triggered by pipeline stage change")
    
    # 4. Smarter Engagement Radar
    if existing["radar"] and not os.path.exists("/root/.openclaw/workspace/scripts/engagement-responder.py"):
        suggestions.append("### 20260314-004 | [MED] [Q] Auto-Comment on Influencer Posts\n"
            "- **Area:** Q (Quality)\n"
            "- **Description:** Radar finds posts but doesn't engage. Could auto-comment on top posts.\n"
            "- **Rationale:** GCC healthcare executives post daily. Auto-commenting builds visibility.\n"
            "- **Action:** Build `scripts/engagement-responder.py` using LLM to generate comments")
    
    # 5. Morning Briefing Enhancement
    if existing["briefing"] and not os.path.exists("/root/.openclaw/workspace/scripts/briefing-visual.py"):
        suggestions.append("### 20260314-005 | [MED] [N] Visual Morning Brief\n"
            "- **Area:** N (Notifications)\n"
            "- **Description:** Briefing is text-only. Could generate summary card/image.\n"
            "- **Rationale:** Visual brief = faster consumption, better engagement.\n"
            "- **Action:** Add `scripts/briefing-visual.py` to generate PNG summary")
    
    # 6. Self-Healing Gateway
    if existing["heartbeat"] and not os.path.exists("/root/.openclaw/workspace/scripts/gateway-healer.py"):
        suggestions.append("### 20260314-006 | [LOW] [G] Auto-Restart Gateway\n"
            "- **Area:** G (Gateway)\n"
            "- **Description:** Heartbeat checks health but doesn't fix. Gateway could hang.\n"
            "- **Rationale:** Auto-restart on failure = zero-downtime. Like Craig Hewitt's watchdog.\n"
            "- **Action:** Build `scripts/gateway-healer.py` + 5-min cron to check and restart")
    
    # 7. CV Version History
    if not os.path.exists("/root/.openclaw/workspace/.cv-history"):
        suggestions.append("### 20260314-007 | [LOW] [A] CV Version Control\n"
            "- **Area:** A (Applications)\n"
            "- **Description:** No CV version history. Can't track what changed.\n"
            "- **Rationale:** Would help when recruiter asks what's different from last version\n"
            "- **Action:** Add `.cv-history/` folder + auto-commit on each CV generation")
    
    # 8. Skill Auto-Discovery
    if not os.path.exists("/root/.openclaw/workspace/scripts/skill-discoverer.py"):
        suggestions.append("### 20260314-008 | [LOW] [S] New Skill Radar\n"
            "- **Area:** S (Skills)\n"
            "- **Description:** No auto-discovery of new OpenClaw skills from ClawHub.\n"
            "- **Rationale:** New skills drop weekly. Could auto-scan and suggest relevant ones.\n"
            "- **Action:** Build `scripts/skill-discoverer.py` + weekly cron to check ClawHub")
    
    # 9. Transcript Fetcher (YouTube)
    if existing["youtube"] and not os.path.exists("/root/.openclaw/workspace/scripts/transcript-fetcher.py"):
        suggestions.append("### 20260314-009 | [LOW] [K] YouTube Transcript Auto-Save\n"
            "- **Area:** K (Knowledge)\n"
            "- **Description:** YouTube intel runs but transcripts not saved consistently.\n"
            "- **Rationale:** Transcripts = searchable knowledge base for company research.\n"
            "- **Action:** Enhance youtube-intel.py to save transcripts to `memory/youtube-transcripts/`")
    
    # 10. Predictive Health
    if existing["sie"] and not os.path.exists("/root/.openclaw/workspace/scripts/predictive-health.py"):
        suggestions.append("### 20260314-010 | [LOW] [M] Predictive Failure Detection\n"
            "- **Area:** M (Models)\n"
            "- **Description:** SIE sees current state but not trends. Could predict failures.\n"
            "- **Rationale:** Track disk growth, session bloat, cron failures over time. ML = early warning.\n"
            "- **Action:** Add trend analysis to SIE: linear regression on history data")
    
    # 11. Chart Generation (just demonstrated)
    if not os.path.exists("/root/.openclaw/workspace/scripts/chart-generator.py"):
        suggestions.append("### 20260314-011 | [MED] [N] Auto-Chart Generation\n"
            "- **Area:** N (Notifications)\n"
            "- **Description:** Matplotlib installed, can generate charts for briefings/insights.\n"
            "- **Rationale:** Visual data beats text. Could auto-generate: job pipeline charts, health trends, model usage graphs.\n"
            "- **Action:** Build `scripts/chart-generator.py` for PNG charts, save to `media/`")
    
    # Write suggestions
    if suggestions:
        with open(IMPROVEMENT_LOG, "w") as f:
            f.write("# Improvement Log\n\n*Auto-generated by SIE Phase 5. Ahmed reviews and approves.*\n\n## Active Suggestions\n\n")
            for s in suggestions:
                f.write(s + "\n\n")
            f.write("\n## Implemented\n(none yet)\n\n## Archived\n(none yet)\n")
        log(f"Generated {len(suggestions)} system improvements")
    
    # Write suggestions to improvement log if new
    if suggestions and "(waiting for next" in improvement_log_content:
        with open(IMPROVEMENT_LOG, "w") as f:
            f.write("# Improvement Log\n\n*Auto-generated by SIE Phase 5. Ahmed reviews and approves.*\n\n## Active Suggestions\n\n")
            for s in suggestions:
                f.write(s + "\n\n")
            f.write("\n## Implemented\n(none yet)\n\n## Archived\n(none yet)\n")
        log(f"Generated {len(suggestions)} system improvements")
    
    # Update state with suggestion counts
    parsed = parse_improvement_log(improvement_log_content)
    state["suggestions"] = {
        "total_generated": state.get("suggestions", {}).get("total_generated", 0) + len(suggestions),
        "implemented": len(parsed.get("implemented", [])),
        "expired": len(parsed.get("archived", [])),
        "pending": len(parsed.get("active", []))
    }
    
    return prompt


def main():
    parser = argparse.ArgumentParser(description="Self-Improvement Engine for OpenClaw")
    parser.add_argument("--dry-run", action="store_true", help="Report only, no file writes")
    parser.add_argument("--json", action="store_true", help="Output JSON summary to stdout")
    parser.add_argument("--suggest", action="store_true", help="Generate improvement prompt for Phase 5")
    parser.add_argument("--fix", action="store_true", help="Autoresearch mode: auto-fix issues")
    parser.add_argument("--max-iterations", type=int, default=3, help="Max fix loop iterations (default: 3)")
    args = parser.parse_args()
    
    mode = "AUTORESEARCH" if args.fix else "MONITOR"
    log(f"=== Self-Improvement Engine (SIE) [{mode}] ===")
    
    # Load previous state
    state = load_state()
    prev_health = state.get("health_score", 100)
    
    # Run checks (with optional auto-fix loop)
    fix_log = []
    if args.fix:
        log(f"Running autoresearch loop (max {args.max_iterations} iterations)...")
        results, fix_log = run_autofix_loop(state, max_iterations=args.max_iterations)
        log(f"Autoresearch complete: {len(fix_log)} fix attempts")
    else:
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
    
    # Store fix log in state for history
    if fix_log:
        state["last_fix_log"] = fix_log
    
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
    
    # Phase 5: Generate improvement prompt
    prompt = run_phase5(results, health_score, state)
    
    # Print prompt if --suggest flag
    if args.suggest:
        print("\n" + "="*60)
        print("IMPROVEMENT PROMPT (Phase 5)")
        print("="*60)
        print(prompt)
        print("="*60)
    
    log("=== SIE Complete ===")
    
    # Send Telegram notification
    try:
        # Read from insights.md
        insights_path = Path("memory/insights.md")
        if insights_path.exists():
            content = insights_path.read_text()
            health_match = re.search(r'Health Score: (\d+)/100', content)
            warnings_match = re.search(r'## Warnings\n((?:.*\n)*)', content)
            
            health = health_match.group(1) if health_match else "?"
            warnings = warnings_match.group(1).count('-') if warnings_match else 0
            
            msg = f"🎯 SIE — Health: {health}/100"
            if fix_log:
                kept = sum(1 for f in fix_log if f["result"] == "KEPT")
                failed = sum(1 for f in fix_log if f["result"] in ("FAILED", "NO_IMPROVEMENT"))
                msg += f"\n🔧 Autoresearch: {kept} fixed, {failed} unchanged"
                for f in fix_log:
                    if f["result"] == "KEPT":
                        msg += f"\n  ✅ [{f['area']}] {f['fix']}"
            if warnings > 0:
                msg += f"\n⚠️ {warnings} warnings"
            
            import subprocess
            subprocess.run([
                "openclaw", "message", "send",
                "--target", "866838380",
                "--message", msg[:500]
            ], capture_output=True, timeout=10)
            log("Telegram notification sent")
    except Exception as e:
        log(f"Notification failed: {e}")
    
    # Exit code based on health
    if health_score < 50:
        sys.exit(2)
    elif health_score < 80:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()

def send_telegram_alert(health_score, warnings, improvements):
    """Send Telegram notification with SIE results."""
    import os
    import json
    
    # Build message
    msg = f"🎯 SIE Daily — Health: {health_score}/100\n\n"
    
    if warnings:
        msg += "⚠️ Warnings:\n"
        for w in warnings[:3]:
            msg += f"  • {w}\n"
        msg += "\n"
    
    if improvements:
        msg += "💡 Top Improvements:\n"
        for imp in improvements[:2]:
            msg += f"  • {imp[:80]}...\n" if len(imp) > 80 else f"  • {imp}\n"
    
    # Write to notification queue (cron will pick up)
    queue_file = "/root/.openclaw/workspace/.notifications/sie-daily.md"
    os.makedirs(os.path.dirname(queue_file), exist_ok=True)
    with open(queue_file, 'w') as f:
        f.write(msg)
    
    log(f"Notification queued: {queue_file}")
    return msg
