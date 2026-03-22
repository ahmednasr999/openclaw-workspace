#!/usr/bin/env python3
"""
system-agent.py — Monitors system health, agent freshness, cron jobs.

Monitors: disk usage, RAM, gateway health, OpenClaw process
Checks: agent data freshness, cron health, external services
Alerts: interview emails, gateway down, job sources down
"""

import json
import os
import subprocess
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

# Import from agent-common.py
import sys
sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module
common = import_module("agent-common")

AgentResult = common.AgentResult
agent_main = common.agent_main
retry_with_backoff = common.retry_with_backoff
load_json = common.load_json
is_dry_run = common.is_dry_run
now_cairo = common.now_cairo
now_iso = common.now_iso
WORKSPACE = common.WORKSPACE
DATA_DIR = common.DATA_DIR

OUTPUT_PATH = DATA_DIR / "system-health.json"
ALERTS_PATH = DATA_DIR / "immediate-alerts.json"

# Agent data files to monitor
AGENT_DATA_FILES = [
    ("jobs-merge", DATA_DIR / "jobs-merged.json", 6),
    ("jobs-review", DATA_DIR / "jobs-summary.json", 6),
    ("email-agent", DATA_DIR / "email-scan.json", 4),
    ("linkedin-post", DATA_DIR / "linkedin-post.json", 6),
    ("comment-radar", DATA_DIR / "comment-radar.json", 6),
    ("outreach-agent", DATA_DIR / "outreach-suggestions.json", 6),
    ("system-agent", DATA_DIR / "system-health.json", 6),
]


def get_disk_usage():
    """Get disk usage percentage."""
    try:
        result = subprocess.run(
            ["df", "-h", "/"],
            capture_output=True,
            text=True,
            timeout=10
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            if len(parts) >= 5:
                usage = parts[4].replace('%', '')
                return int(usage)
    except Exception:
        pass
    return -1


def get_memory_usage():
    """Get memory usage from /proc/meminfo."""
    try:
        with open('/proc/meminfo') as f:
            meminfo = {}
            for line in f:
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = int(parts[1].strip().split()[0])  # Value in kB
                    meminfo[key] = val
            
            total = meminfo.get('MemTotal', 0)
            available = meminfo.get('MemAvailable', 0)
            if total > 0:
                used_pct = round((total - available) / total * 100, 1)
                return {
                    "total_gb": round(total / 1024 / 1024, 1),
                    "available_gb": round(available / 1024 / 1024, 1),
                    "used_pct": used_pct
                }
    except Exception:
        pass
    return {"total_gb": 0, "available_gb": 0, "used_pct": -1}


def check_gateway_health():
    """Check OpenClaw gateway health endpoint."""
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:18789/health",
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                return {"status": "healthy", "code": 200}
    except urllib.error.URLError as e:
        return {"status": "down", "error": str(e)}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    return {"status": "unknown"}


def check_openclaw_process():
    """Check if OpenClaw process is running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "openclaw"],
            capture_output=True,
            text=True,
            timeout=10
        )
        pids = result.stdout.strip().split('\n')
        pids = [p for p in pids if p]
        return {"running": len(pids) > 0, "pid_count": len(pids)}
    except Exception:
        return {"running": False, "pid_count": 0}


def check_agent_freshness(agent_name, file_path, ttl_hours):
    """Check if agent data is fresh."""
    now = now_cairo()
    
    if not file_path.exists():
        return {
            "agent": agent_name,
            "status": "missing",
            "file": str(file_path)
        }
    
    try:
        data = load_json(file_path)
        meta = data.get("meta", {})
        generated_at = meta.get("generated_at")
        
        if generated_at:
            gen_time = datetime.fromisoformat(generated_at)
            age_hours = (now - gen_time).total_seconds() / 3600
            is_fresh = age_hours <= ttl_hours
            return {
                "agent": agent_name,
                "status": "healthy" if is_fresh else "stale",
                "age_hours": round(age_hours, 1),
                "ttl_hours": ttl_hours,
                "last_run": generated_at,
                "last_status": meta.get("status")
            }
    except Exception as e:
        return {
            "agent": agent_name,
            "status": "error",
            "error": str(e)
        }
    
    return {
        "agent": agent_name,
        "status": "unknown"
    }


def check_cron_health():
    """Check OpenClaw cron jobs."""
    try:
        result = subprocess.run(
            ["openclaw", "cron", "list"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            # Filter known noise: plugin warnings, gateway transient reconnects
            stderr = result.stderr or ""
            noise_patterns = [
                "loaded without install/load-path provenance",
                "gateway closed (1000",
                "gateway connect failed",
                "plugins] camofox",
            ]
            is_noise = all(
                any(noise in line for noise in noise_patterns)
                for line in stderr.strip().split('\n')
                if line.strip()
            )
            if is_noise and result.stdout.strip():
                # Cron output is fine, stderr is just noise
                pass
            else:
                return {"status": "error", "error": stderr[:200]}
        
        # Parse cron output
        lines = result.stdout.strip().split('\n')
        cron_jobs = []
        for line in lines:
            if line and not line.startswith('ID') and not line.startswith('─'):
                cron_jobs.append(line)
        
        return {
            "status": "healthy",
            "job_count": len(cron_jobs),
            "raw_output": result.stdout[:500]  # First 500 chars
        }
    except FileNotFoundError:
        return {"status": "unavailable", "error": "openclaw command not found"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@retry_with_backoff(max_retries=2, base_delay=1)
def check_notion_api():
    """Check if Notion API is reachable."""
    try:
        # Simple test query to check connectivity
        req = urllib.request.Request(
            "https://api.notion.com/v1/users/me",
            headers={
                "Authorization": f"Bearer {NOTION_TOKEN}",
                "Notion-Version": "2022-06-28"
            },
            method='GET'
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                return {"status": "reachable", "code": 200}
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return {"status": "auth_error", "code": 401}
        return {"status": "error", "code": e.code}
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}
    return {"status": "unknown"}


def check_himalaya():
    """Check if Himalaya is working."""
    try:
        result = subprocess.run(
            ["himalaya", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return {"status": "available", "version": result.stdout.strip()}
    except FileNotFoundError:
        return {"status": "not_installed"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    return {"status": "unknown"}


def check_for_interview_alerts():
    """Check email-summary.json for interview invites."""
    email_summary = load_json(DATA_DIR / "email-summary.json")
    if not email_summary:
        return []
    
    data = email_summary.get("data", {})
    interview_invites = data.get("interview_invites", [])
    
    alerts = []
    for invite in interview_invites:
        if invite.get("unread", True):
            alerts.append({
                "type": "interview_detected",
                "urgency": "critical",
                "message": f"Interview invite from {invite.get('from', 'Unknown')}: {invite.get('subject', '')}",
                "timestamp": now_iso()
            })
    
    return alerts


def send_telegram_alert(message):
    """Send critical alert to Telegram immediately."""
    try:
        subprocess.run(
            ["openclaw", "message", "send", "--channel", "telegram",
             "--to", "866838380", "--message", message],
            timeout=15, capture_output=True
        )
        print(f"  Telegram alert sent: {message[:60]}...")
    except Exception as e:
        print(f"  Telegram alert failed: {e}")


def write_immediate_alerts(alerts):
    """Write immediate alerts to file and send critical ones to Telegram."""
    if not alerts:
        return
    
    # Send critical alerts to Telegram immediately
    critical = [a for a in alerts if a.get("urgency") == "critical"]
    if critical:
        msg_lines = ["🚨 CRITICAL ALERT"]
        for a in critical[:3]:
            msg_lines.append(f"\n{a.get('message', 'Unknown alert')}")
        send_telegram_alert("\n".join(msg_lines))
    
    existing = load_json(ALERTS_PATH, default={"alerts": []})
    existing_alerts = existing.get("alerts", [])
    
    # Add new alerts
    for alert in alerts:
        alert["id"] = f"alert-{len(existing_alerts)}-{datetime.now().strftime('%H%M%S')}"
        existing_alerts.append(alert)
    
    # Keep only last 100 alerts
    existing_alerts = existing_alerts[-100:]
    
    output = {
        "last_updated": now_iso(),
        "alerts": existing_alerts,
        "active_count": len([a for a in existing_alerts if not a.get("acknowledged")])
    }
    
    if not is_dry_run():
        ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(ALERTS_PATH, 'w') as f:
            json.dump(output, f, indent=2)


def run_system_agent(result: AgentResult):
    """Main agent logic."""
    now = now_cairo()
    immediate_alerts = []
    
    print("  Checking system resources...")
    disk_usage = get_disk_usage()
    memory = get_memory_usage()
    
    print("  Checking gateway health...")
    gateway = check_gateway_health()
    
    print("  Checking OpenClaw process...")
    openclaw_proc = check_openclaw_process()
    
    print("  Checking agent freshness...")
    agent_health = []
    agents_healthy = 0
    agents_stale = 0
    
    for agent_name, file_path, ttl in AGENT_DATA_FILES:
        health = check_agent_freshness(agent_name, file_path, ttl)
        agent_health.append(health)
        if health["status"] == "healthy":
            agents_healthy += 1
        elif health["status"] == "stale":
            agents_stale += 1
    
    print("  Checking cron health...")
    cron = check_cron_health()
    
    print("  Checking external services...")
    notion = check_notion_api()
    himalaya = check_himalaya()
    
    # Check for interview alerts
    print("  Checking for interview alerts...")
    interview_alerts = check_for_interview_alerts()
    immediate_alerts.extend(interview_alerts)
    
    # Gateway down alert
    if gateway.get("status") == "down":
        immediate_alerts.append({
            "type": "gateway_down",
            "urgency": "critical",
            "message": f"Gateway is down: {gateway.get('error', 'Unknown error')}",
            "timestamp": now_iso()
        })
    
    # Write immediate alerts
    if immediate_alerts:
        print(f"  Writing {len(immediate_alerts)} immediate alerts...")
        write_immediate_alerts(immediate_alerts)
    
    # Build data
    result.set_data({
        "scan_time": now_iso(),
        "system": {
            "disk_usage_pct": disk_usage,
            "memory": memory,
            "gateway": gateway,
            "openclaw_process": openclaw_proc
        },
        "agents": {
            "health": agent_health,
            "healthy_count": agents_healthy,
            "stale_count": agents_stale,
            "total": len(AGENT_DATA_FILES)
        },
        "cron": cron,
        "external_services": {
            "notion": notion,
            "himalaya": himalaya
        },
        "alerts": {
            "immediate_count": len(immediate_alerts),
            "recent": immediate_alerts[:5]
        }
    })
    
    # KPIs
    result.set_kpi({
        "system_uptime": 100 if openclaw_proc.get("running") else 0,  # Simple binary for now
        "agents_healthy": agents_healthy,
        "agents_stale": agents_stale,
        "cron_success_rate": 100 if cron.get("status") == "healthy" else 0,
        "alerts_active": len(immediate_alerts)
    })
    
    # Recommendations
    if disk_usage > 80:
        result.add_recommendation(
            action="cleanup_disk",
            target="Disk space",
            reason=f"Disk usage at {disk_usage}%",
            urgency="high" if disk_usage > 90 else "medium"
        )
    
    if memory.get("used_pct", 0) > 85:
        result.add_recommendation(
            action="investigate_memory",
            target="Memory usage",
            reason=f"Memory usage at {memory.get('used_pct')}%",
            urgency="medium"
        )
    
    if gateway.get("status") != "healthy":
        result.add_recommendation(
            action="restart_gateway",
            target="OpenClaw gateway",
            reason=f"Gateway status: {gateway.get('status')}",
            urgency="high"
        )
    
    if agents_stale > 0:
        stale_agents = [a["agent"] for a in agent_health if a["status"] == "stale"]
        result.add_recommendation(
            action="run_agents",
            target=f"{agents_stale} stale agent(s): {', '.join(stale_agents)}",
            reason="Agent data is past TTL",
            urgency="medium"
        )
    
    if notion.get("status") != "reachable":
        result.add_recommendation(
            action="check_notion_auth",
            target="Notion API",
            reason=f"Notion status: {notion.get('status')}",
            urgency="medium"
        )
    
    if interview_alerts:
        result.add_recommendation(
            action="respond_immediately",
            target=f"{len(interview_alerts)} interview invite(s)",
            reason="Interview invitations detected in email",
            urgency="critical"
        )


if __name__ == "__main__":
    agent_main(
        agent_name="system-agent",
        run_func=run_system_agent,
        output_path=OUTPUT_PATH,
        ttl_hours=1,  # System health should be checked frequently
        version="1.0.0"
    )
