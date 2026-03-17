#!/usr/bin/env python3
"""
Platform Health Monitor
Checks cron jobs, storage, errors, and system health
"""

import subprocess, sqlite3, os, re
from datetime import datetime, timedelta
from pathlib import Path
import csv
from io import StringIO

DB_PATH = "/root/.openclaw/workspace/knowledge-base/kb.db"

def get_cron_jobs():
    """Get all cron jobs and their status (parse table output)"""
    result = subprocess.run(
        ["openclaw", "cron", "list"],
        capture_output=True, text=True, timeout=30
    )
    
    if result.returncode != 0:
        return {"error": result.stderr}
    
    lines = result.stdout.strip().split('\n')
    
    # Parse table (skip header, extract ID, Name, Status)
    jobs = []
    for line in lines[1:]:  # Skip header
        if not line.strip():
            continue
        # Split by whitespace, handle spaces in names
        parts = line.split()
        if len(parts) >= 7:
            job_id = parts[0]
            status = parts[-4]  # Status column
            name = " ".join(parts[1:-5])  # Name is between ID and Status
            jobs.append({
                "id": job_id,
                "name": name.strip(),
                "status": status
            })
    
    return jobs

def check_storage():
    """Check storage usage"""
    usage = {}
    
    # Check disk space (MAIN DISK)
    try:
        result = subprocess.run(
            ["df", "-h", "/"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            # Parse the line with /dev/sda1 or similar
            for line in lines[1:]:  # Skip header
                if line.startswith('/dev/'):
                    parts = line.split()
                    if len(parts) >= 5:
                        total = parts[1]
                        used = parts[2]
                        avail = parts[3]
                        use_pct = parts[4].replace('%', '')
                        usage["disk_total"] = total
                        usage["disk_used"] = used
                        usage["disk_avail"] = avail
                        usage["disk_usage_pct"] = int(use_pct)
                        
                        # Alert thresholds
                        if int(use_pct) >= 90:
                            usage["disk_status"] = "🔴 CRITICAL"
                        elif int(use_pct) >= 80:
                            usage["disk_status"] = "🟡 WARNING"
                        else:
                            usage["disk_status"] = "✅ HEALTHY"
                        break
    except Exception as e:
        usage["disk_error"] = str(e)
    
    # Check workspace size
    try:
        result = subprocess.run(
            ["du", "-sh", "/root/.openclaw/workspace"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            usage["workspace"] = result.stdout.split()[0]
    except:
        usage["workspace"] = "unknown"
    
    # Check knowledge base size
    try:
        result = subprocess.run(
            ["du", "-sh", "/root/.openclaw/workspace/knowledge-base"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            usage["knowledge_base"] = result.stdout.split()[0]
    except:
        usage["knowledge_base"] = "unknown"
    
    # Check database size
    if os.path.exists(DB_PATH):
        size = os.path.getsize(DB_PATH)
        usage["database"] = f"{size / 1024:.1f} KB"
    else:
        usage["database"] = "not found"
    
    # Check backup size
    try:
        result = subprocess.run(
            ["du", "-sh", "/root/openclaw-backups"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            usage["backups"] = result.stdout.split()[0]
    except:
        usage["backups"] = "unknown"
    
    return usage

def check_git_status():
    """Check git repo status"""
    status = {}
    
    try:
        # Check if behind remote
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, cwd="/root/.openclaw/workspace"
        )
        status["changes"] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        
        # Check last commit age
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci"],
            capture_output=True, text=True, cwd="/root/.openclaw/workspace"
        )
        if result.returncode == 0:
            last_commit = result.stdout.strip()
            try:
                last_dt = datetime.fromisoformat(last_commit.replace(" +00:00", ""))
                hours_ago = (datetime.now() - last_dt).total_seconds() / 3600
                status["hours_since_commit"] = round(hours_ago, 1)
            except:
                status["hours_since_commit"] = "unknown"
    except Exception as e:
        status["error"] = str(e)
    
    return status

def check_database_health():
    """Check database integrity and stats"""
    health = {}
    
    if not os.path.exists(DB_PATH):
        return {"status": "not_found"}
    
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Get table count
        cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        health["tables"] = cursor.fetchone()[0]
        
        # Get row counts for key tables
        for table in ["contacts", "interactions", "job_pipeline", "follow_ups"]:
            try:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                health[f"{table}_count"] = cursor.fetchone()[0]
            except:
                health[f"{table}_count"] = 0
        
        conn.close()
        health["status"] = "healthy"
    except Exception as e:
        health["status"] = "error"
        health["error"] = str(e)
    
    return health

def check_gateway():
    """Check OpenClaw gateway status"""
    result = subprocess.run(
        ["openclaw", "gateway", "status"],
        capture_output=True, text=True, timeout=10
    )
    
    if result.returncode == 0:
        return {"status": "running", "output": result.stdout[:200]}
    else:
        return {"status": "stopped", "error": result.stderr[:200]}

def generate_report():
    """Generate comprehensive health report"""
    print("\n🏥 PLATFORM HEALTH REPORT")
    print("=" * 55)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # Cron Jobs
    print("📋 CRON JOBS")
    print("-" * 40)
    jobs = get_cron_jobs()
    
    if isinstance(jobs, dict) and "error" in jobs:
        print(f"   ❌ Error: {jobs['error']}")
    else:
        enabled = sum(1 for j in jobs if j.get("status") not in ["disabled"])
        errors = sum(1 for j in jobs if j.get("status") == "error")
        idle = sum(1 for j in jobs if j.get("status") == "idle")
        
        print(f"   Total: {len(jobs)} | ✅ {enabled} running | ❌ {errors} error | 💤 {idle} idle")
        
        # Show recent/error jobs
        print(f"\n   Recent status:")
        for j in jobs[:8]:
            name = j.get("name", "Unknown")[:30]
            status = j.get("status", "?")
            if status == "ok":
                emoji = "✅"
            elif status == "error":
                emoji = "❌"
            elif status == "idle":
                emoji = "💤"
            else:
                emoji = "•"
            print(f"   {emoji} {name:<32} {status}")
    
    print()
    
    # Storage
    print("💾 STORAGE")
    print("-" * 40)
    storage = check_storage()
    
    # Disk space with alert
    if "disk_status" in storage:
        status = storage["disk_status"]
        disk = storage.get("disk_usage_pct", 0)
        print(f"   Main Disk: {storage.get('disk_total', '?')} | Used: {storage.get('disk_used', '?')} ({disk}%) | {status}")
        
        if disk >= 80:
            print(f"   ⚠️  WARNING: Disk usage at {disk}%!")
        elif disk >= 90:
            print(f"   🚨 CRITICAL: Disk usage at {disk}%! Free space immediately!")
    
    print(f"   Workspace:  {storage.get('workspace', '?')}")
    print(f"   Knowledge: {storage.get('knowledge_base', '?')}")
    print(f"   Database:   {storage.get('database', '?')}")
    print(f"   Backups:   {storage.get('backups', '?')}")
    
    print()
    
    # Git
    print("📦 GIT STATUS")
    print("-" * 40)
    git = check_git_status()
    if "error" in git:
        print(f"   ❌ {git['error']}")
    else:
        changes = git.get("changes", 0)
        hours = git.get("hours_since_commit", "?")
        print(f"   Uncommitted changes: {changes}")
        print(f"   Hours since commit: {hours}")
        if changes > 10:
            print(f"   ⚠️  Many uncommitted changes — run git sync!")
    
    print()
    
    # Database
    print("🗄️ DATABASE")
    print("-" * 40)
    db = check_database_health()
    if db.get("status") == "healthy":
        print(f"   Status: ✅ Healthy")
        print(f"   Tables: {db.get('tables', 0)}")
        print(f"   Contacts: {db.get('contacts_count', 0)}")
        print(f"   Interactions: {db.get('interactions_count', 0)}")
        print(f"   Job Pipeline: {db.get('job_pipeline_count', 0)}")
    else:
        print(f"   Status: ❌ {db.get('error', 'unknown')}")
    
    print()
    
    # Gateway
    print("🦞 GATEWAY")
    print("-" * 40)
    gw = check_gateway()
    if gw.get("status") == "running":
        print(f"   Status: ✅ Running")
    else:
        print(f"   Status: ❌ {gw.get('status', 'unknown')}")
    
    print()
    
    # Summary
    print("=" * 55)
    print("SUMMARY")
    print("=" * 55)
    
    issues = []
    alerts = []
    
    # Check disk space
    disk_pct = storage.get("disk_usage_pct", 0)
    if disk_pct >= 90:
        issues.append(f"CRITICAL: Disk at {disk_pct}% - free space immediately!")
        alerts.append(f"🚨 CRITICAL: Disk {disk_pct}% full!")
    elif disk_pct >= 80:
        issues.append(f"Disk space warning: {disk_pct}% used")
        alerts.append(f"⚠️ WARNING: Disk {disk_pct}% full")
    
    if git.get("changes", 0) > 10:
        issues.append("Many uncommitted changes")
    
    if db.get("status") != "healthy":
        issues.append("Database issue")
    
    errors = sum(1 for j in jobs if j.get("status") == "error") if isinstance(jobs, list) else 0
    if errors > 0:
        issues.append(f"{errors} cron job(s) with errors")
    
    # Print alerts first
    if alerts:
        print("⚠️  ALERTS:")
        for a in alerts:
            print(f"   {a}")
        print()
    
    if issues:
        print("⚠️  Issues to address:")
        for i in issues:
            print(f"   • {i}")
    else:
        print("✅ All systems healthy!")
    
    result = {
        "cron": jobs,
        "storage": storage,
        "git": git,
        "database": db,
        "issues": issues,
        "disk_alerts": alerts,
        "disk_issues": issues
    }
    
    return result

def send_telegram_report():
    """Send summary to Telegram"""
    jobs = get_cron_jobs()
    storage = check_storage()
    git = check_git_status()
    db = check_database_health()
    
    enabled = sum(1 for j in jobs if j.get("status") not in ["disabled"]) if isinstance(jobs, list) else 0
    errors = sum(1 for j in jobs if j.get("status") == "error") if isinstance(jobs, list) else 0
    
    text = f"🏥 *Platform Health*\n\n"
    text += f"📋 Cron: {enabled} running"
    if errors > 0:
        text += f" | ❌ {errors} errors"
    text += "\n"
    text += f"💾 Disk: {storage.get('disk_usage_pct', '?')}% ({storage.get('disk_status', '')})"
    if storage.get("disk_usage_pct", 0) >= 80:
        text += f"\n⚠️ Disk space low! Available: {storage.get('disk_avail', '?')}"
    text += "\n"
    text += f"🗄️ DB: {db.get('contacts_count', 0)} contacts\n"
    
    if git.get("changes", 0) > 0:
        text += f"\n⚠️ {git['changes']} uncommitted changes"
    
    subprocess.run(
        ["openclaw", "message", "send", "--target", "telegram:866838380", "--message", text],
        capture_output=True
    )

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--telegram":
            send_telegram_report()
            print("✅ Sent to Telegram")
        elif sys.argv[1] == "--check":
            result = check_database_health()
            print(result)
        else:
            generate_report()
    else:
        generate_report()

# Journalctl disk usage (added for monitoring)
def check_logs():
    """Check system logs disk usage"""
    try:
        result = subprocess.run(
            ["journalctl", "--disk-usage"],
            capture_output=True, text=True, timeout=10
        )
        logs = {}
        if result.returncode == 0:
            # Parse "Archived and active journals take up 218.9M in the file system."
            match = re.search(r'(\d+\.?\d*)([KMG])', result.stdout)
            if match:
                size = float(match.group(1))
                unit = match.group(2)
                logs["journal_size"] = f"{size}{unit}"
                # Alert if > 500MB
                if (unit == 'M' and size > 500) or (unit == 'G' and size >= 1):
                    logs["journal_status"] = "⚠️ Large"
                else:
                    logs["journal_status"] = "✅ Normal"
        return logs
    except Exception as e:
        return {"error": str(e)}
