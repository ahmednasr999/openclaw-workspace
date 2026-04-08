"""
briefing-adapters.py - Normalizes agent outputs for the morning briefing.
Each agent outputs its own schema; this adapts them to a consistent format.
"""

def adapt_email(raw):
    """Normalize email-agent output for briefing."""
    d = raw.get("data", {})
    return {
        "scanned_count": d.get("total_scanned", d.get("scanned_count", 0)),
        "actionable_count": d.get("actionable_count", 0),
        "categories": {
            "interview_invite": d.get("interview_invites", d.get("categories", {}).get("interview_invite", [])),
            "recruiter_reach": d.get("recruiter_messages", d.get("categories", {}).get("recruiter_reach", [])),
        },
        "action_required": d.get("follow_ups_needed", d.get("action_required", [])),
    }

def adapt_system(raw):
    """Normalize system-agent output for briefing."""
    d = raw.get("data", {})
    sys_data = d.get("system", {})
    disk = sys_data.get("disk_usage_pct", d.get("infrastructure", {}).get("disk_percent", "?"))
    mem = sys_data.get("memory", {})
    gw = sys_data.get("gateway", d.get("infrastructure", {}).get("gateway", {}))
    agents = d.get("agents", {})
    
    # Disk: could be int or dict
    disk_pct = disk if isinstance(disk, (int, float)) else disk.get("percent", "?") if isinstance(disk, dict) else "?"
    
    # RAM: could be dict with used_pct
    ram_pct = mem.get("used_pct", "?") if isinstance(mem, dict) else mem if isinstance(mem, (int, float)) else "?"
    
    # Gateway: could be dict with status, or bool
    if isinstance(gw, dict):
        gw_healthy = gw.get("status") == "healthy"
    elif isinstance(gw, bool):
        gw_healthy = gw
    else:
        gw_healthy = False
    
    # Agent health: could be list or dict
    agent_health = agents.get("health", d.get("agent_health", {}))
    if isinstance(agent_health, list):
        healthy_count = sum(1 for a in agent_health if a.get("status") == "healthy")
        total_count = len(agent_health)
    elif isinstance(agent_health, dict):
        healthy_count = sum(1 for v in agent_health.values() if isinstance(v, dict) and v.get("status") == "healthy")
        total_count = len(agent_health)
    else:
        healthy_count = agents.get("healthy_count", 0)
        total_count = agents.get("total", 0)
    
    # Uptime
    try:
        import subprocess
        result = subprocess.run(["uptime", "-s"], capture_output=True, text=True, timeout=5)
        from datetime import datetime
        boot = datetime.strptime(result.stdout.strip(), "%Y-%m-%d %H:%M:%S")
        uptime_days = (datetime.now() - boot).days
    except Exception:
        uptime_days = "?"
    
    # Alerts
    alerts_raw = d.get("alerts", {})
    if isinstance(alerts_raw, dict):
        alert_list = alerts_raw.get("recent", alerts_raw.get("immediate", []))
    elif isinstance(alerts_raw, list):
        alert_list = alerts_raw
    else:
        alert_list = []
    
    return {
        "infrastructure": {
            "disk_percent": disk_pct,
            "ram_percent": ram_pct,
            "gateway_healthy": gw_healthy,
            "uptime_days": uptime_days,
        },
        "agent_health_count": healthy_count,
        "agent_total_count": total_count,
        "alerts": alert_list,
    }

def adapt_pipeline(raw):
    """Pipeline is already in correct format after the fix."""
    return raw.get("data", {})

def adapt_content(raw):
    """Content is already in correct format."""
    return raw.get("data", {})

def adapt_outreach(raw):
    """Outreach is already in correct format."""
    return raw.get("data", {})

def adapt_jobs(raw):
    """Jobs is already in correct format."""
    return raw.get("data", {})
