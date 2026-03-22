#!/usr/bin/env python3
"""
NASR Doctor - Unified system health check.
Run: python3 scripts/nasr-doctor.py
"""

import json
import os
import subprocess
import sys
import socket
import imaplib
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
OPENCLAW_DIR = Path("/root/.openclaw")

# ── Results tracking ──

class Result:
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"

results = []

def check(name, status, detail=""):
    icon = {"ok": "✅", "warn": "⚠️ ", "fail": "❌"}[status]
    results.append({"name": name, "status": status, "detail": detail})
    print(f"  {icon} {name:<22} {detail}")


# ── 1. OpenClaw Gateway ──

def check_gateway():
    try:
        pid_out = subprocess.run(
            ["pgrep", "-f", "openclaw.*gateway\\|openclaw-gateway"],
            capture_output=True, text=True, timeout=5
        )
        if pid_out.returncode == 0:
            pid = pid_out.stdout.strip().split("\n")[0]
            # Check uptime
            try:
                stat = Path(f"/proc/{pid}").stat()
                start = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc)
                uptime = datetime.now(timezone.utc) - start
                days = uptime.days
                hours = uptime.seconds // 3600
                check("OpenClaw Gateway", Result.OK, f"PID {pid}, uptime {days}d {hours}h")
            except Exception:
                check("OpenClaw Gateway", Result.OK, f"PID {pid}")
        else:
            # Check if websocket port is listening
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(("127.0.0.1", 18789))
            sock.close()
            if result == 0:
                check("OpenClaw Gateway", Result.OK, "Port 18789 listening")
            else:
                check("OpenClaw Gateway", Result.FAIL, "Not running")
    except Exception as e:
        check("OpenClaw Gateway", Result.FAIL, str(e)[:60])


# ── 2. Disk Space ──

def check_disk():
    try:
        st = os.statvfs("/")
        total = st.f_frsize * st.f_blocks
        free = st.f_frsize * st.f_bavail
        used_pct = int((1 - free / total) * 100)
        free_gb = free / (1024**3)
        if used_pct > 90:
            check("Disk Space", Result.FAIL, f"{used_pct}% used ({free_gb:.1f}GB free)")
        elif used_pct > 80:
            check("Disk Space", Result.WARN, f"{used_pct}% used ({free_gb:.1f}GB free)")
        else:
            check("Disk Space", Result.OK, f"{used_pct}% used ({free_gb:.1f}GB free)")
    except Exception as e:
        check("Disk Space", Result.WARN, str(e)[:60])


# ── 3. Cron Jobs ──

def check_crons():
    cron_dir = OPENCLAW_DIR / "cron" / "runs"
    if not cron_dir.exists():
        check("Cron Jobs", Result.WARN, "No cron runs directory")
        return

    cron_files = sorted(cron_dir.glob("*.jsonl"))
    if not cron_files:
        check("Cron Jobs", Result.WARN, "No cron run logs found")
        return

    ok_count = 0
    warn_count = 0
    fail_count = 0

    for cf in cron_files:
        name = cf.stem
        try:
            # Read last line (most recent run)
            lines = cf.read_text().strip().split("\n")
            last_lines = [l for l in lines if '"action":"finished"' in l]
            if not last_lines:
                continue

            last = json.loads(last_lines[-1])
            status = last.get("status", "unknown")
            ts = last.get("ts", 0)

            if ts:
                run_time = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                ago = datetime.now(timezone.utc) - run_time
                if ago.days > 0:
                    ago_str = f"{ago.days}d ago"
                else:
                    hours = ago.seconds // 3600
                    ago_str = f"{hours}h ago"
            else:
                ago_str = "unknown"

            if status == "ok":
                ok_count += 1
            elif status == "error":
                error_msg = last.get("error", "")[:40]
                check(f"Cron: {name[:20]}", Result.WARN, f"ERROR ({ago_str}) {error_msg}")
                fail_count += 1
            else:
                warn_count += 1
        except Exception:
            continue

    if fail_count == 0:
        check("Cron Jobs", Result.OK, f"{ok_count} ok, {warn_count} warn, {fail_count} failed")
    else:
        # Individual failures already printed above
        pass


# ── 4. API Connections ──

def check_firehose():
    config_file = WORKSPACE / "config" / "firehose.json"
    if not config_file.exists():
        check("Firehose API", Result.WARN, "No config file")
        return

    try:
        config = json.loads(config_file.read_text())
        tap_token = config.get("tap_token", "")
        if not tap_token:
            check("Firehose API", Result.WARN, "No tap token")
            return

        req = urllib.request.Request(
            "https://api.firehose.com/v1/rules",
            headers={"Authorization": f"Bearer {tap_token}"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            rules = data.get("data", [])
            count = data.get("meta", {}).get("count", len(rules))
            check("Firehose API", Result.OK, f"Connected ({count} rules)")
    except Exception as e:
        check("Firehose API", Result.FAIL, str(e)[:60])


def check_gmail():
    try:
        creds_file = Path("/root/.config/gmail-smtp.json")
        if not creds_file.exists():
            # Try env or other locations
            check("Gmail IMAP", Result.WARN, "No credentials file")
            return

        creds = json.loads(creds_file.read_text())
        user = creds.get("user", creds.get("email", ""))
        password = creds.get("password", creds.get("app_password", ""))

        if not user or not password:
            check("Gmail IMAP", Result.WARN, "Missing credentials")
            return

        imap = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=10)
        imap.login(user, password)
        imap.select("INBOX", readonly=True)
        typ, data = imap.search(None, "ALL")
        count = len(data[0].split()) if data[0] else 0
        imap.logout()
        check("Gmail IMAP", Result.OK, f"Connected ({count} msgs)")
    except imaplib.IMAP4.error as e:
        check("Gmail IMAP", Result.FAIL, f"Auth error: {str(e)[:40]}")
    except (socket.timeout, ConnectionRefusedError):
        check("Gmail IMAP", Result.FAIL, "Connection timeout")
    except Exception as e:
        check("Gmail IMAP", Result.FAIL, str(e)[:60])


def check_composio_linkedin():
    # Just check if the connection config exists
    tools_md = WORKSPACE / "TOOLS.md"
    if tools_md.exists():
        content = tools_md.read_text()
        if "ACTIVE" in content and "linkedin" in content.lower():
            check("LinkedIn (Composio)", Result.OK, "Config shows ACTIVE")
        else:
            check("LinkedIn (Composio)", Result.WARN, "Status unclear in TOOLS.md")
    else:
        check("LinkedIn (Composio)", Result.WARN, "TOOLS.md missing")


# ── 5. Key Scripts ──

def check_scripts():
    scripts = [
        "firehose-monitor.py",
        "email-agent.py",
        "linkedin-auto-poster.py",
        "nasr-doctor.py",
    ]
    missing = []
    for s in scripts:
        path = WORKSPACE / "scripts" / s
        if not path.exists():
            missing.append(s)

    if missing:
        check("Key Scripts", Result.WARN, f"Missing: {', '.join(missing)}")
    else:
        check("Key Scripts", Result.OK, f"All {len(scripts)} present")


# ── 6. Pipeline Status ──

def check_pipeline():
    pipeline = WORKSPACE / "jobs-bank" / "pipeline.md"
    if not pipeline.exists():
        check("Pipeline", Result.WARN, "pipeline.md missing")
        return

    try:
        content = pipeline.read_text()
        new_count = content.lower().count("| new |") + content.count("| ⭐ New |")
        applied_count = content.lower().count("applied")
        review_count = content.lower().count("review")
        check("Pipeline", Result.OK, f"{new_count} New, ~{applied_count} Applied refs")
    except Exception as e:
        check("Pipeline", Result.WARN, str(e)[:60])


# ── 7. Memory Files ──

def check_memory():
    now = datetime.now(timezone(timedelta(hours=2)))  # Cairo
    today_file = WORKSPACE / "memory" / f"{now.strftime('%Y-%m-%d')}.md"

    files = {
        "MEMORY.md": WORKSPACE / "MEMORY.md",
        "active-tasks.md": WORKSPACE / "memory" / "active-tasks.md",
        "Today's notes": today_file,
    }

    missing = [name for name, path in files.items() if not path.exists()]
    if missing:
        check("Memory Files", Result.WARN, f"Missing: {', '.join(missing)}")
    else:
        check("Memory Files", Result.OK, "All present")


# ── 8. Git Status ──

def check_git():
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=5,
            cwd=str(WORKSPACE)
        )
        changes = len([l for l in result.stdout.strip().split("\n") if l.strip()])

        log_result = subprocess.run(
            ["git", "log", "-1", "--format=%cr"],
            capture_output=True, text=True, timeout=5,
            cwd=str(WORKSPACE)
        )
        last_commit = log_result.stdout.strip()

        if changes == 0:
            check("Git Status", Result.OK, f"Clean (last commit {last_commit})")
        elif changes < 5:
            check("Git Status", Result.WARN, f"{changes} uncommitted files (last commit {last_commit})")
        else:
            check("Git Status", Result.WARN, f"{changes} uncommitted files!")
    except Exception as e:
        check("Git Status", Result.WARN, str(e)[:60])


# ── Main ──

def main():
    print()
    print("  🩺 NASR Doctor - System Health Check")
    print("  " + "━" * 42)
    print()

    check_gateway()
    check_disk()
    check_crons()
    check_firehose()
    check_gmail()
    check_composio_linkedin()
    check_scripts()
    check_pipeline()
    check_memory()
    check_git()

    print()
    print("  " + "━" * 42)

    ok = sum(1 for r in results if r["status"] == Result.OK)
    warn = sum(1 for r in results if r["status"] == Result.WARN)
    fail = sum(1 for r in results if r["status"] == Result.FAIL)

    print(f"  Summary: {ok} ✅  {warn} ⚠️   {fail} ❌")
    print()

    if fail > 0:
        sys.exit(2)
    elif warn > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
