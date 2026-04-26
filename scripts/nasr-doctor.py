#!/usr/bin/env python3
"""
NASR Doctor - Unified system health check with auto-fix.

Usage:
    python3 scripts/nasr-doctor.py          # Diagnose only
    python3 scripts/nasr-doctor.py --fix    # Diagnose + auto-fix safe issues
"""

import json
import os
import re
import subprocess
import sys
import socket
import imaplib
import shutil
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, str(Path(__file__).parent))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

WORKSPACE = Path("/root/.openclaw/workspace")
OPENCLAW_DIR = Path("/root/.openclaw")
FIX_MODE = "--fix" in sys.argv

# ── Results tracking ──

class Result:
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"
    FIXED = "fixed"

results = []
fixes_applied = []

def check(name, status, detail=""):
    icon = {"ok": "✅", "warn": "⚠️ ", "fail": "❌", "fixed": "🔧"}[status]
    results.append({"name": name, "status": status, "detail": detail})
    print(f"  {icon} {name:<22} {detail}")

def fix_applied(name, action):
    fixes_applied.append({"name": name, "action": action})


# ── 1. OpenClaw Gateway ──

def check_gateway():
    try:
        pid_out = subprocess.run(
            ["pgrep", "-f", "openclaw.*gateway\\|openclaw-gateway"],
            capture_output=True, text=True, timeout=5
        )
        if pid_out.returncode == 0:
            pid = pid_out.stdout.strip().split("\n")[0]
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
            port_result = sock.connect_ex(("127.0.0.1", 18789))
            sock.close()
            if port_result == 0:
                check("OpenClaw Gateway", Result.OK, "Port 18789 listening")
            elif FIX_MODE:
                # Auto-fix: restart gateway
                restart = subprocess.run(
                    ["openclaw", "gateway", "restart"],
                    capture_output=True, text=True, timeout=30
                )
                if restart.returncode == 0:
                    check("OpenClaw Gateway", Result.FIXED, "Restarted successfully")
                    fix_applied("OpenClaw Gateway", "Ran 'openclaw gateway restart'")
                else:
                    check("OpenClaw Gateway", Result.FAIL, "Restart failed")
            else:
                check("OpenClaw Gateway", Result.FAIL, "Not running (use --fix to restart)")
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
            if FIX_MODE:
                freed = _clean_disk()
                # Re-check
                st2 = os.statvfs("/")
                free2 = st2.f_frsize * st2.f_bavail
                new_pct = int((1 - free2 / total) * 100)
                new_free = free2 / (1024**3)
                check("Disk Space", Result.FIXED, f"{new_pct}% used ({new_free:.1f}GB free) - freed {freed}")
                fix_applied("Disk Space", f"Cleaned: {freed}")
            else:
                check("Disk Space", Result.FAIL, f"{used_pct}% used ({free_gb:.1f}GB free) (use --fix)")
        elif used_pct > 80:
            if FIX_MODE:
                freed = _clean_disk()
                st2 = os.statvfs("/")
                free2 = st2.f_frsize * st2.f_bavail
                new_pct = int((1 - free2 / total) * 100)
                new_free = free2 / (1024**3)
                check("Disk Space", Result.FIXED, f"{new_pct}% used ({new_free:.1f}GB free) - freed {freed}")
                fix_applied("Disk Space", f"Cleaned: {freed}")
            else:
                check("Disk Space", Result.WARN, f"{used_pct}% used ({free_gb:.1f}GB free)")
        else:
            check("Disk Space", Result.OK, f"{used_pct}% used ({free_gb:.1f}GB free)")
    except Exception as e:
        check("Disk Space", Result.WARN, str(e)[:60])

def _clean_disk():
    """Run safe disk cleanup operations. Returns description of what was freed."""
    cleaned = []

    # 1. apt autoremove
    try:
        subprocess.run(["apt-get", "autoremove", "-y", "-q"], capture_output=True, timeout=60)
        cleaned.append("apt autoremove")
    except Exception:
        pass

    # 2. apt clean
    try:
        subprocess.run(["apt-get", "clean", "-q"], capture_output=True, timeout=30)
        cleaned.append("apt clean")
    except Exception:
        pass

    # 3. Clear old journal logs (keep 3 days)
    try:
        subprocess.run(["journalctl", "--vacuum-time=3d"], capture_output=True, timeout=30)
        cleaned.append("journal vacuum 3d")
    except Exception:
        pass

    # 4. Clear /tmp files older than 7 days
    try:
        subprocess.run(
            ["find", "/tmp", "-type", "f", "-mtime", "+7", "-delete"],
            capture_output=True, timeout=30
        )
        cleaned.append("old /tmp files")
    except Exception:
        pass

    # 5. Clear archived cron logs
    archive_dir = OPENCLAW_DIR / "cron" / "runs" / "_archived"
    if archive_dir.exists():
        try:
            shutil.rmtree(archive_dir)
            cleaned.append("archived cron logs")
        except Exception:
            pass

    return ", ".join(cleaned) if cleaned else "nothing to clean"


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

    # Load active job IDs
    active_ids = set()
    jobs_file = OPENCLAW_DIR / "cron" / "jobs.json"
    if jobs_file.exists():
        try:
            with open(jobs_file) as f:
                data = json.load(f)
            for j in data.get("jobs", data if isinstance(data, list) else []):
                if isinstance(j, dict):
                    active_ids.add(j.get("id", ""))
        except Exception:
            pass

    ok_count = 0
    warn_count = 0
    fail_count = 0
    orphans_archived = 0

    for cf in cron_files:
        name = cf.stem

        # Auto-fix: archive orphan run logs
        if FIX_MODE and name not in active_ids:
            archive_dir = OPENCLAW_DIR / "cron" / "runs" / "_archived"
            archive_dir.mkdir(exist_ok=True)
            cf.rename(archive_dir / cf.name)
            orphans_archived += 1
            continue

        try:
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

    if orphans_archived > 0:
        check("Cron Cleanup", Result.FIXED, f"Archived {orphans_archived} orphan run logs")
        fix_applied("Cron Cleanup", f"Archived {orphans_archived} orphan run logs")

    if fail_count > 0 or warn_count > 0:
        check("Cron Jobs", Result.WARN, f"{ok_count} ok, {warn_count} warn, {fail_count} failed")
    else:
        check("Cron Jobs", Result.OK, f"{ok_count} ok, {warn_count} warn, {fail_count} failed")


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
        creds_file = WORKSPACE / "config" / "gmail-imap.json"
        fallback_file = Path("/root/.config/gmail-smtp.json")
        source_file = creds_file if creds_file.exists() else fallback_file
        if not source_file.exists():
            check("Gmail IMAP", Result.WARN, "No credentials file")
            return

        creds = json.loads(source_file.read_text())
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
    tools_md = WORKSPACE / "TOOLS.md"
    if not tools_md.exists():
        check("LinkedIn (Composio)", Result.WARN, "TOOLS.md missing")
        return

    content = tools_md.read_text().lower()
    signals = [
        "post tool:",
        "linkedin_create_linked_in_post",
        "person urn:",
        "auto-poster script:",
        "scripts/linkedin-auto-poster.py",
    ]
    found = [s for s in signals if s in content]
    if len(found) >= 3:
        check("LinkedIn (Composio)", Result.OK, "LinkedIn posting config documented")
    else:
        check("LinkedIn (Composio)", Result.WARN, "LinkedIn config incomplete in TOOLS.md")


def check_linkedin_cookies():
    """Test LinkedIn JD enrichment via tls-client (primary method, no cookies needed)."""
    try:
        import tls_client
        # Pick a recent job ID from raw data (avoids hardcoded stale IDs)
        test_id = None
        raw_file = WORKSPACE / "data" / "jobs-raw" / "linkedin.json"
        if raw_file.exists():
            import re as _re
            raw_jobs = json.loads(raw_file.read_text()).get("data", [])
            for j in raw_jobs[:10]:
                url = j.get("job_url", "") or j.get("url", "")
                m = _re.search(r"(\d{8,})", url)
                if m:
                    test_id = m.group(1)
                    break
        if not test_id:
            test_id = "4386681141"  # fallback

        session = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
        resp = session.get(f"https://www.linkedin.com/jobs/view/{test_id}", headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        }, timeout_seconds=10)
        if resp.status_code == 200 and "show-more-less-html" in resp.text:
            cache_dir = WORKSPACE / "data" / "jd-cache"
            cached = len(list(cache_dir.glob("*.json"))) if cache_dir.exists() else 0
            check("LinkedIn JD Fetch", Result.OK, f"tls-client working (job {test_id}, {cached} cached)")
        else:
            check("LinkedIn JD Fetch", Result.WARN, f"tls-client got {resp.status_code} for job {test_id}")
    except ImportError:
        check("LinkedIn JD Fetch", Result.FAIL, "tls_client not installed - run: pip install tls_client")
    except Exception as e:
        check("LinkedIn JD Fetch", Result.FAIL, f"tls-client failed: {e}")


# ── 5. Key Scripts ──

def check_linkedin_tests():
    """Run LinkedIn auto-poster test suite."""
    test_path = WORKSPACE / "scripts" / "test-linkedin-poster.py"
    if not test_path.exists():
        check("LinkedIn Tests", Result.WARN, "test-linkedin-poster.py missing")
        return
    try:
        r = subprocess.run(
            ["python3", str(test_path)],
            capture_output=True, text=True, timeout=30
        )
        lines = r.stdout.strip().split("\n")
        result_line = lines[-1] if lines else ""
        if r.returncode == 0:
            check("LinkedIn Tests", Result.OK, result_line)
        else:
            check("LinkedIn Tests", Result.WARN, f"Failures: {result_line}")
    except subprocess.TimeoutExpired:
        check("LinkedIn Tests", Result.WARN, "Timed out after 30s")
    except Exception as e:
        check("LinkedIn Tests", Result.WARN, f"Error: {e}")


def check_pipeline_db_tests():
    """Run pipeline_db test suite."""
    test_path = WORKSPACE / "scripts" / "test-pipeline-db.py"
    if not test_path.exists():
        check("Pipeline DB Tests", Result.WARN, "test-pipeline-db.py missing")
        return
    try:
        r = subprocess.run(
            ["python3", str(test_path)],
            capture_output=True, text=True, timeout=30
        )
        lines = r.stdout.strip().split("\n")
        result_line = lines[-1] if lines else ""
        if r.returncode == 0:
            check("Pipeline DB Tests", Result.OK, result_line)
        else:
            check("Pipeline DB Tests", Result.WARN, f"Failures: {result_line}")
    except subprocess.TimeoutExpired:
        check("Pipeline DB Tests", Result.WARN, "Timed out after 30s")
    except Exception as e:
        check("Pipeline DB Tests", Result.WARN, f"Error: {e}")


def check_content_tests():
    """Run content agent test suite."""
    test_path = WORKSPACE / "scripts" / "test-content-agent.py"
    if not test_path.exists():
        check("Content Tests", Result.WARN, "test-content-agent.py missing")
        return
    try:
        result = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=True, text=True, timeout=60
        )
        combined = "\n".join(filter(None, [result.stdout.strip(), result.stderr.strip()]))
        match = re.search(r"(\d+)/(\d+) passed", combined)
        if result.returncode == 0:
            detail = f"{match.group(1)}/{match.group(2)} passed" if match else "tests passed"
            check("Content Tests", Result.OK, detail)
        else:
            tail = combined.splitlines()[-1][:80] if combined else "unknown failure"
            check("Content Tests", Result.WARN, f"Failures: {tail}")
    except subprocess.TimeoutExpired:
        check("Content Tests", Result.WARN, "Timed out after 60s")
    except Exception as e:
        check("Content Tests", Result.WARN, f"Error: {e}")


def check_email_tests():
    """Run Email Agent test suite."""
    test_path = WORKSPACE / "scripts" / "test-email-agent.py"
    if not test_path.exists():
        check("Email Tests", Result.WARN, "test-email-agent.py missing")
        return
    try:
        r = subprocess.run(
            ["python3", str(test_path)],
            capture_output=True, text=True, timeout=30
        )
        lines = r.stdout.strip().split("\n")
        result_line = lines[-1] if lines else ""
        if r.returncode == 0:
            check("Email Tests", Result.OK, result_line)
        else:
            check("Email Tests", Result.WARN, f"Failures: {result_line}")
    except subprocess.TimeoutExpired:
        check("Email Tests", Result.WARN, "Timed out after 30s")
    except Exception as e:
        check("Email Tests", Result.WARN, f"Error: {e}")


def check_cv_tests():
    """Run CV builder test suite."""
    test_path = WORKSPACE / "scripts" / "test-cv-builder.py"
    if not test_path.exists():
        check("CV Tests", Result.WARN, "test-cv-builder.py missing")
        return
    try:
        r = subprocess.run(
            ["python3", str(test_path)],
            capture_output=True, text=True, timeout=30
        )
        # Parse last line for results
        lines = r.stdout.strip().split("\n")
        result_line = lines[-1] if lines else ""
        if r.returncode == 0:
            check("CV Tests", Result.OK, result_line)
        else:
            check("CV Tests", Result.WARN, f"Failures: {result_line}")
    except subprocess.TimeoutExpired:
        check("CV Tests", Result.WARN, "Timed out after 30s")
    except Exception as e:
        check("CV Tests", Result.WARN, f"Error: {e}")


def check_scripts():
    scripts = [
        "firehose-monitor.py",
        "email-agent.py",
        "linkedin-auto-poster.py",
        "nasr-doctor.py",
        "cv_validator.py",
        "test-cv-builder.py",
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

    if FIX_MODE and "Today's notes" in missing:
        # Auto-fix: create today's daily note
        today_file.parent.mkdir(parents=True, exist_ok=True)
        today_file.write_text(f"# Daily Notes - {now.strftime('%Y-%m-%d')}\n\n")
        missing.remove("Today's notes")
        fix_applied("Memory Files", f"Created {today_file.name}")

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
        dirty_lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        changes = len(dirty_lines)

        log_result = subprocess.run(
            ["git", "log", "-1", "--format=%cr"],
            capture_output=True, text=True, timeout=5,
            cwd=str(WORKSPACE)
        )
        last_commit = log_result.stdout.strip()

        if changes == 0:
            check("Git Status", Result.OK, f"Clean (last commit {last_commit})")
        elif FIX_MODE and changes > 0:
            # Auto-fix: commit data and log files
            # Only auto-commit safe paths (data/, logs/, memory/, jobs-bank/)
            safe_prefixes = ("data/", "logs/", "memory/", "jobs-bank/", "coordination/")
            safe_files = [l[3:] for l in dirty_lines if any(l[3:].startswith(p) for p in safe_prefixes)]
            unsafe_count = changes - len(safe_files)

            if safe_files:
                for f in safe_files:
                    subprocess.run(["git", "add", f], capture_output=True, cwd=str(WORKSPACE))
                subprocess.run(
                    ["git", "commit", "-m", f"chore(auto): daily data commit ({len(safe_files)} files)"],
                    capture_output=True, text=True, timeout=15,
                    cwd=str(WORKSPACE)
                )
                fix_applied("Git Status", f"Auto-committed {len(safe_files)} data/log files")

            if unsafe_count > 0:
                check("Git Status", Result.FIXED, f"Committed {len(safe_files)} safe files, {unsafe_count} remaining")
            else:
                check("Git Status", Result.FIXED, f"Committed {len(safe_files)} files (last commit {last_commit})")
        elif changes < 5:
            check("Git Status", Result.WARN, f"{changes} uncommitted files (last commit {last_commit})")
        else:
            check("Git Status", Result.WARN, f"{changes} uncommitted files!")
    except Exception as e:
        check("Git Status", Result.WARN, str(e)[:60])


# ── Pipeline DB Health Check ──

def check_pipeline_db():
    """Check nasr-pipeline.db exists, has recent data, no corruption."""
    db_path = WORKSPACE / "data" / "nasr-pipeline.db"

    if not db_path.exists():
        check("Pipeline DB", Result.WARN, "nasr-pipeline.db not found")
        return

    # Check file size (empty or corrupt if < 10KB)
    size_kb = db_path.stat().st_size / 1024
    if size_kb < 10:
        check("Pipeline DB", Result.WARN, f"DB suspiciously small: {size_kb:.0f} KB")
        return

    if not _pdb:
        check("Pipeline DB", Result.WARN, f"pipeline_db module not importable ({size_kb:.0f} KB)")
        return

    try:
        stats = _pdb.get_db_stats()
        if "error" in stats:
            check("Pipeline DB", Result.FAIL, f"DB error: {stats['error'][:60]}")
            return

        jobs_count = stats.get("jobs_count", 0)
        last_update = stats.get("last_update", "")

        if jobs_count == 0:
            check("Pipeline DB", Result.WARN, "DB has 0 job records — run migrate_to_db.py")
            return

        # Check data freshness (last update within 48h)
        if last_update:
            try:
                lu = datetime.fromisoformat(last_update)
                age_hours = (datetime.now() - lu.replace(tzinfo=None)).total_seconds() / 3600
                if age_hours > 48:
                    check("Pipeline DB", Result.WARN,
                          f"{jobs_count} jobs | last update {age_hours:.0f}h ago (stale)")
                    return
            except Exception:
                pass

        check("Pipeline DB", Result.OK,
              f"{jobs_count} jobs | {stats.get('interactions_count', 0)} interactions | "
              f"{size_kb:.0f} KB | keywords: {stats.get('keywords_count', 0)}")

        # Auto-backup if fix mode
        if FIX_MODE:
            backup_path = _pdb.backup()
            if backup_path:
                fix_applied("Pipeline DB", f"Backup created: {Path(backup_path).name}")

    except Exception as e:
        check("Pipeline DB", Result.WARN, f"Check failed: {str(e)[:60]}")


# ── Main ──

def main():
    print()
    mode_label = "DIAGNOSE + AUTO-FIX" if FIX_MODE else "DIAGNOSE ONLY"
    print(f"  🩺 NASR Doctor - {mode_label}")
    print("  " + "━" * 42)
    print()

    check_gateway()
    check_disk()
    check_crons()
    check_firehose()
    check_gmail()
    check_composio_linkedin()
    check_linkedin_cookies()
    check_scripts()
    check_cv_tests()
    check_linkedin_tests()
    check_pipeline_db_tests()
    check_email_tests()
    check_content_tests()
    check_pipeline()
    check_pipeline_db()
    check_memory()
    check_git()

    print()
    print("  " + "━" * 42)

    ok = sum(1 for r in results if r["status"] == Result.OK)
    warn = sum(1 for r in results if r["status"] == Result.WARN)
    fail = sum(1 for r in results if r["status"] == Result.FAIL)
    fixed = sum(1 for r in results if r["status"] == Result.FIXED)

    summary = f"  Summary: {ok} ✅  {warn} ⚠️   {fail} ❌"
    if fixed > 0:
        summary += f"  {fixed} 🔧"
    print(summary)

    if fixes_applied:
        print()
        print("  Fixes applied:")
        for f in fixes_applied:
            print(f"    🔧 {f['name']}: {f['action']}")

    print()

    if fail > 0:
        sys.exit(2)
    elif warn > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
