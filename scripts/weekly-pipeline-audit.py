#!/usr/bin/env python3
"""
weekly-pipeline-audit.py — Deep structural audit of the Morning Briefing Pipeline.

Runs every Sunday. Goes beyond the daily Doctor (which checks outputs) to check
the CODE ITSELF for structural problems.

Checks:
1. Syntax: bash -n on shell scripts, python -m py_compile on Python
2. Undefined variables in shell scripts
3. Data flow: every file read by a consumer must be written by a producer
4. Dead imports / unused files
5. Hardcoded secrets (bot tokens, API keys in source)
6. Timeout consistency (script timeout vs pipeline timeout)
7. Error handling (try/except, set -e)

Usage:
  python3 weekly-pipeline-audit.py              # Full audit + Telegram
  python3 weekly-pipeline-audit.py --dry-run    # Preview only
"""

import json, os, sys, re, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, str(Path(__file__).parent))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

# Pipeline DB (safe fallback)
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pipeline_db as _pdb
except ImportError:
    _pdb = None

WORKSPACE = Path("/root/.openclaw/workspace")
SCRIPTS = WORKSPACE / "scripts"
DATA_DIR = WORKSPACE / "data"
HISTORY_FILE = DATA_DIR / "weekly-audit-history.json"
CAIRO = timezone(timedelta(hours=2))
CHAT_ID = "866838380"

now = datetime.now(CAIRO)
today = now.strftime("%Y-%m-%d")

# ── Pipeline scripts (the 17 that matter) ──
PIPELINE_PYTHON = [
    "jobs-source-linkedin.py", "jobs-source-indeed.py", "jobs-source-google.py",
    "jobs-source-common.py", "jobs-merge.py", "jobs-enrich-jd.py", "jobs-review.py",
    "push-submit-to-notion.py", "email-agent.py", "linkedin-auto-poster.py",
    "comment-radar-agent.py", "outreach-agent.py", "outreach-followup-tracker.py",
    "system-agent.py", "briefing-agent.py", "pam-telegram.py", "briefing-doctor.py",
    "pipeline-agent.py", "linkedin-content-agent.py", "linkedin-post-agent.py",
    "sync-applied-from-notion.py", "heartbeat-checker.py",
]

PIPELINE_SHELL = ["run-briefing-pipeline.sh"]

# ── Data flow map: file → who writes it → who reads it ──
DATA_FLOW = {
    "jobs-raw/linkedin.json": {"writer": "jobs-source-linkedin.py", "readers": ["jobs-merge.py"]},
    "jobs-raw/indeed.json": {"writer": "jobs-source-indeed.py", "readers": ["jobs-merge.py"]},
    "jobs-raw/google-jobs.json": {"writer": "jobs-source-google.py", "readers": ["jobs-merge.py"]},
    "jobs-merged.json": {"writer": "jobs-merge.py", "readers": ["jobs-enrich-jd.py", "jobs-review.py"]},
    "jobs-summary.json": {"writer": "jobs-review.py", "readers": ["briefing-agent.py", "pam-telegram.py", "push-submit-to-notion.py"]},
    "email-summary.json": {"writer": "email-agent.py", "readers": ["briefing-agent.py", "pam-telegram.py"]},
    "system-health.json": {"writer": "system-agent.py", "readers": ["briefing-agent.py", "pam-telegram.py"]},
    "comment-radar.json": {"writer": "comment-radar-agent.py", "readers": ["briefing-agent.py", "pam-telegram.py"]},
    "outreach-suggestions.json": {"writer": "outreach-agent.py", "readers": ["briefing-agent.py", "pam-telegram.py"]},
    "content-schedule.json": {"writer": "linkedin-content-agent.py", "readers": ["briefing-agent.py"]},
    "pipeline-status.json": {"writer": "pipeline-agent.py", "readers": ["briefing-agent.py"]},
    "linkedin-post.json": {"writer": "linkedin-post-agent.py", "readers": ["briefing-agent.py", "pam-telegram.py"]},
}

# Secrets patterns to flag
SECRET_PATTERNS = [
    (r'\b\d{10}:AA[A-Za-z0-9_-]{30,}\b', "Telegram bot token"),
    (r'\bak_[a-zA-Z0-9]{20,}\b', "Composio API key"),
    (r'\bsk-[a-zA-Z0-9]{20,}\b', "OpenAI API key"),
    (r'xoxb-[0-9]+-[0-9]+-[a-zA-Z0-9]+', "Slack bot token"),
    (r'APP_PASSWORD\s*=\s*"[^"]{10,}"', "Hardcoded app password"),
    (r'BOT_TOKEN\s*=\s*"[^"]{10,}"', "Hardcoded bot token"),
    (r'GMAIL_APP_PASSWORD\s*=\s*"[^"]{8,}"', "Hardcoded Gmail password"),
    (r'"app_password"\s*:\s*"[^"]{8,}"', "Hardcoded password in JSON literal"),
]

# Allowed: Notion token (needed in scripts that call Notion API directly)
SECRET_ALLOW = ["ntn_"]

findings = []


def finding(severity, category, script, message):
    findings.append({
        "severity": severity,  # CRITICAL, WARNING, INFO
        "category": category,
        "script": script,
        "message": message,
    })


# ── CHECK 1: Syntax ──
def check_syntax():
    print("  [1/7] Syntax check...")
    
    for script in PIPELINE_PYTHON:
        path = SCRIPTS / script
        if not path.exists():
            finding("WARNING", "missing", script, f"Script not found: {path}")
            continue
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(path)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            finding("CRITICAL", "syntax", script, f"Python syntax error: {result.stderr[:120]}")
    
    for script in PIPELINE_SHELL:
        path = SCRIPTS / script
        if not path.exists():
            finding("WARNING", "missing", script, f"Script not found: {path}")
            continue
        result = subprocess.run(
            ["bash", "-n", str(path)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            finding("CRITICAL", "syntax", script, f"Bash syntax error: {result.stderr[:120]}")


# ── CHECK 2: Undefined variables in shell ──
def check_shell_vars():
    print("  [2/7] Shell variable check...")
    
    for script in PIPELINE_SHELL:
        path = SCRIPTS / script
        if not path.exists():
            continue
        content = path.read_text()
        
        # Find all variable definitions
        defined = set(re.findall(r'^([A-Z_][A-Z_0-9]*)=', content, re.MULTILINE))
        defined.update(re.findall(r'\blocal\s+([a-z_][a-z_0-9]*)=', content, re.MULTILINE))
        # Add common builtins
        defined.update(["HOME", "PATH", "PWD", "USER", "BASH_SOURCE", "FUNCNAME",
                       "PIPESTATUS", "RANDOM", "SECONDS", "LINENO", "HOSTNAME",
                       "WORKSPACE", "SCRIPTS", "DATA_DIR", "LOG_FILE", "DATE",
                       "SCRIPTS_DIR", "LOG"])
        
        # Find all variable usages
        used = set(re.findall(r'\$\{?([A-Z_][A-Z_0-9]*)\}?', content))
        
        # Undefined = used but not defined
        undefined = used - defined
        # Filter noise (function params, loop vars)
        undefined = {v for v in undefined if len(v) > 2 and v not in [
            "PHASE2_FAILURES", "TRANSIENT_COUNT", "FAILED_SOURCES",
            "OPTARG", "OPTIND", "IFS",
            "CONFIG_COUNT", "LOGIC_COUNT", "LOCK_PID",  # defined via $() subshell
        ]}
        
        for var in sorted(undefined):
            finding("WARNING", "undefined_var", script, f"${var} used but may not be defined")


# ── CHECK 3: Data flow integrity ──
def check_data_flow():
    print("  [3/7] Data flow integrity...")
    
    for data_file, flow in DATA_FLOW.items():
        writer = flow["writer"]
        readers = flow["readers"]
        
        # Check writer exists
        writer_path = SCRIPTS / writer
        if not writer_path.exists():
            finding("CRITICAL", "data_flow", writer, f"Writer for {data_file} doesn't exist")
            continue
        
        # Check writer actually writes this file
        writer_content = writer_path.read_text()
        # Simplified check: does the writer reference the filename?
        base = Path(data_file).name
        if base not in writer_content and data_file not in writer_content:
            finding("WARNING", "data_flow", writer, f"Writer may not produce {data_file} (filename not in source)")
        
        # Check readers exist and reference the file
        for reader in readers:
            reader_path = SCRIPTS / reader
            if not reader_path.exists():
                finding("WARNING", "data_flow", reader, f"Reader of {data_file} doesn't exist")
                continue
            reader_content = reader_path.read_text()
            if base not in reader_content and data_file not in reader_content:
                finding("INFO", "data_flow", reader, f"Reader may not consume {data_file} (filename not in source)")


# ── CHECK 4: Hardcoded secrets ──
def check_secrets():
    print("  [4/7] Secret scan...")
    
    all_scripts = PIPELINE_PYTHON + PIPELINE_SHELL
    for script in all_scripts:
        path = SCRIPTS / script
        if not path.exists():
            continue
        content = path.read_text()
        
        for pattern, label in SECRET_PATTERNS:
            matches = re.findall(pattern, content)
            for match in matches:
                # Check if it's in the allow list
                if any(match.startswith(a) for a in SECRET_ALLOW):
                    continue
                finding("WARNING", "secret", script, f"Possible {label} found: {match[:15]}...")


# ── CHECK 5: Error handling ──
def check_error_handling():
    print("  [5/7] Error handling...")
    
    for script in PIPELINE_PYTHON:
        path = SCRIPTS / script
        if not path.exists():
            continue
        content = path.read_text()
        
        # Scripts that do HTTP/API calls should have try/except
        has_http = any(w in content for w in ["requests.", "urllib", "urlopen", "http.client"])
        has_try = "try:" in content
        
        if has_http and not has_try:
            finding("WARNING", "error_handling", script, "Does HTTP calls but has no try/except")
        
        # Scripts that write output files should handle write errors
        has_json_dump = "json.dump" in content
        if has_json_dump and "try:" not in content:
            finding("INFO", "error_handling", script, "Writes JSON but no error handling around it")


# ── CHECK 6: Timeout consistency ──
def check_timeouts():
    print("  [6/7] Timeout consistency...")
    
    # Parse timeouts from run-briefing-pipeline.sh
    pipeline_path = SCRIPTS / "run-briefing-pipeline.sh"
    if not pipeline_path.exists():
        return
    
    content = pipeline_path.read_text()
    
    # Find run_agent calls with timeouts
    agent_calls = re.findall(r'run_agent\s+"(\w+)"\s+"([^"]+)"\s+(\d+)', content)
    
    for name, script, timeout_str in agent_calls:
        timeout = int(timeout_str)
        
        # Check if script has internal timeout that conflicts
        script_path = SCRIPTS / script
        if not script_path.exists():
            continue
        script_content = script_path.read_text()
        
        # Look for requests.get timeout or similar
        internal_timeouts = re.findall(r'timeout[=:]\s*(\d+)', script_content)
        for it in internal_timeouts:
            if int(it) > timeout:
                finding("WARNING", "timeout", script, f"Internal timeout {it}s > pipeline timeout {timeout}s (will be killed)")


# ── CHECK 7: Orphaned files ──
def check_orphans():
    print("  [7/7] Orphaned files...")
    
    # Check data files that exist but aren't in DATA_FLOW
    known_files = set(DATA_FLOW.keys())
    
    for f in DATA_DIR.glob("*.json"):
        rel = f.name
        if rel not in known_files and rel not in [
            "pam-newsletter.json", "briefing-doctor-history.json",
            "weekly-audit-history.json", "immediate-alerts.json",
            "source-failures.jsonl", "linkedin-engagement.json",
            "github-discovery.json", "outreach-history.json",
            "linkedin-research-log.json",
        ]:
            finding("INFO", "orphan", rel, f"Data file exists but not in pipeline data flow map")


# ── MAIN ──
def check_pipeline_db_health():
    """Check pipeline DB integrity and add findings."""
    db_path = WORKSPACE / "data" / "nasr-pipeline.db"
    if not db_path.exists():
        finding("WARNING", "pipeline_db", "nasr-pipeline.db", "DB file does not exist — run migrate_to_db.py")
        return
    if not _pdb:
        finding("WARNING", "pipeline_db", "pipeline_db.py", "pipeline_db module not importable")
        return
    try:
        stats = _pdb.get_db_stats()
        if stats.get("error"):
            finding("CRITICAL", "pipeline_db", "nasr-pipeline.db", f"DB error: {stats['error'][:80]}")
            return
        jobs = stats.get("jobs_count", 0)
        if jobs == 0:
            finding("WARNING", "pipeline_db", "nasr-pipeline.db", "DB has 0 jobs — migration may not have run")
            return
        # Check for duplicate job_ids
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        dupes = conn.execute(
            "SELECT job_id, COUNT(*) as n FROM jobs GROUP BY job_id HAVING n > 1"
        ).fetchall()
        conn.close()
        if dupes:
            finding("WARNING", "pipeline_db", "nasr-pipeline.db",
                    f"{len(dupes)} duplicate job_ids found")
        # Funnel sanity
        funnel = _pdb.get_funnel()
        applied = funnel.get("applied", 0)
        if applied < 10:
            finding("INFO", "pipeline_db", "nasr-pipeline.db",
                    f"Only {applied} applied jobs in DB — check migration")
    except Exception as e:
        finding("WARNING", "pipeline_db", "nasr-pipeline.db", str(e)[:80])


# ── CHECK 8: Notion-SQLite drift ──
def check_notion_drift():
    """Check if Notion and SQLite record counts are in sync."""
    print("  [8/11] Notion-SQLite drift...")
    if not _pdb:
        return
    try:
        stats = _pdb.get_db_stats()
        db_count = stats.get("jobs_count", 0)
        # Read notion page count from last sync output
        sync_output = WORKSPACE / "data" / "pipeline-status.json"
        if sync_output.exists():
            import json
            data = json.load(open(sync_output))
            notion_count = data.get("total_applications", 0) + data.get("discovered_count", 0)
            drift = abs(db_count - notion_count)
            if drift > 50:
                finding("CRITICAL", "drift", "notion-sync", f"Notion ({notion_count}) vs SQLite ({db_count}) drift: {drift} records")
            elif drift > 20:
                finding("WARNING", "drift", "notion-sync", f"Notion ({notion_count}) vs SQLite ({db_count}) drift: {drift} records")
            else:
                finding("INFO", "drift", "notion-sync", f"Drift: {drift} records (Notion={notion_count}, SQLite={db_count})")
    except Exception as e:
        finding("INFO", "drift", "notion-sync", f"Could not check drift: {e}")


# ── CHECK 9: Near-duplicate detection ──
def check_near_duplicates():
    """Check for near-duplicate jobs by company+title."""
    print("  [9/11] Near-duplicate detection...")
    if not _pdb:
        return
    try:
        import sqlite3
        conn = sqlite3.connect(str(WORKSPACE / "data" / "nasr-pipeline.db"))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT company, title, COUNT(*) as cnt FROM jobs
            WHERE company IS NOT NULL AND title IS NOT NULL
            GROUP BY LOWER(TRIM(company)), LOWER(TRIM(title))
            HAVING cnt > 1
        """).fetchall()
        conn.close()
        if rows:
            finding("WARNING", "duplicates", "nasr-pipeline.db",
                    f"{len(rows)} near-duplicate groups (same company+title): " +
                    ", ".join(f"{r['company']}|{r['title']}({r['cnt']})" for r in rows[:3]))
    except Exception as e:
        finding("INFO", "duplicates", "nasr-pipeline.db", f"Could not check: {e}")


# ── CHECK 10: LinkedIn cookie expiry ──
def check_cookie_expiry():
    """Check if LinkedIn cookies are still valid."""
    print("  [10/11] LinkedIn cookie expiry...")
    cookie_path = WORKSPACE / "data" / "linkedin-cookies.txt"
    if not cookie_path.exists():
        finding("WARNING", "cookies", "linkedin-cookies.txt", "Cookie file missing")
        return
    try:
        li_at = None
        for line in cookie_path.read_text().splitlines():
            if line.startswith('#') or not line.strip():
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 7 and parts[5] == 'li_at':
                li_at = parts[6]
                # Check expiry timestamp
                try:
                    exp = int(parts[4])
                    from datetime import datetime as dt
                    exp_date = dt.fromtimestamp(exp)
                    days_left = (exp_date - dt.now()).days
                    if days_left < 0:
                        finding("CRITICAL", "cookies", "linkedin-cookies.txt",
                                f"li_at cookie EXPIRED {abs(days_left)} days ago")
                    elif days_left < 7:
                        finding("WARNING", "cookies", "linkedin-cookies.txt",
                                f"li_at cookie expires in {days_left} days")
                except (ValueError, OSError):
                    pass
                break
        if not li_at:
            finding("WARNING", "cookies", "linkedin-cookies.txt", "No li_at cookie found")
    except Exception as e:
        finding("INFO", "cookies", "linkedin-cookies.txt", f"Could not check: {e}")


# ── CHECK 11: Cron last-run verification ──
def check_cron_health():
    """Verify that critical crons actually ran recently."""
    print("  [11/11] Cron last-run health...")
    critical_outputs = {
        "Scanner": WORKSPACE / "jobs-bank" / "scraped",
        "Pipeline status": WORKSPACE / "data" / "pipeline-status.json",
    }
    for name, path in critical_outputs.items():
        if not path.exists():
            finding("WARNING", "cron_health", name, f"Output path doesn't exist: {path}")
            continue
        try:
            if path.is_dir():
                files = sorted(path.glob("*"), key=lambda f: f.stat().st_mtime, reverse=True)
                if not files:
                    finding("WARNING", "cron_health", name, "No output files found")
                    continue
                last_mod = datetime.fromtimestamp(files[0].stat().st_mtime)
            else:
                last_mod = datetime.fromtimestamp(path.stat().st_mtime)
            
            hours_ago = (datetime.now() - last_mod).total_seconds() / 3600
            if hours_ago > 48:
                finding("WARNING", "cron_health", name,
                        f"Last output {hours_ago:.0f}h ago (>48h) - cron may be stale")
        except Exception as e:
            finding("INFO", "cron_health", name, f"Could not check: {e}")


def run_audit():
    print("🔍 Running weekly pipeline audit...")
    
    check_syntax()
    check_shell_vars()
    check_data_flow()
    check_secrets()
    check_error_handling()
    check_timeouts()
    check_orphans()
    check_pipeline_db_health()
    check_notion_drift()
    check_near_duplicates()
    check_cookie_expiry()
    check_cron_health()
    
    # Score
    critical = sum(1 for f in findings if f["severity"] == "CRITICAL")
    warnings = sum(1 for f in findings if f["severity"] == "WARNING")
    infos = sum(1 for f in findings if f["severity"] == "INFO")
    
    # Score: start at 100, -20 per critical, -5 per warning, -1 per info
    score = max(0, 100 - (critical * 20) - (warnings * 5) - (infos * 1))
    
    if score >= 90:
        grade, emoji = "A", "🟢"
    elif score >= 75:
        grade, emoji = "B", "🟡"
    elif score >= 50:
        grade, emoji = "C", "🟠"
    else:
        grade, emoji = "F", "🔴"
    
    return {
        "date": today,
        "score": score,
        "grade": grade,
        "emoji": emoji,
        "critical": critical,
        "warnings": warnings,
        "infos": infos,
        "findings": findings,
    }


def save_history(audit):
    try:
        history = json.load(open(HISTORY_FILE))
    except Exception:
        history = {"audits": []}
    
    audits = history.get("audits", [])
    audits = [a for a in audits if a.get("date") != today]
    audits.append({
        "date": audit["date"],
        "score": audit["score"],
        "grade": audit["grade"],
        "critical": audit["critical"],
        "warnings": audit["warnings"],
        "infos": audit["infos"],
    })
    audits = sorted(audits, key=lambda a: a["date"])[-12:]  # 12 weeks
    
    history["audits"] = audits
    history["updated"] = now.isoformat()
    
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def get_db_metrics() -> dict:
    """Get pipeline metrics from SQLite DB for the weekly audit."""
    if not _pdb:
        return {}
    try:
        funnel = _pdb.get_funnel()
        stale = _pdb.get_stale(days=7)
        stats = _pdb.get_db_stats()
        conversion = _pdb.funnel_conversion()
        gaps = _pdb.keyword_gaps()
        return {
            "funnel": funnel,
            "stale_count": len(stale),
            "db_stats": stats,
            "conversion": conversion,
            "top_gaps": [g["keyword"] for g in gaps[:5]],
        }
    except Exception:
        return {}


def format_telegram(audit):
    lines = []
    lines.append(f"{audit['emoji']} Weekly Pipeline Audit: {audit['score']}/100 (Grade {audit['grade']})")
    lines.append(f"🔴 {audit['critical']} critical | ⚠️ {audit['warnings']} warnings | ℹ️ {audit['infos']} info")
    lines.append("")
    
    # Show critical + warning findings
    shown = 0
    for f in audit["findings"]:
        if f["severity"] in ("CRITICAL", "WARNING") and shown < 8:
            icon = "🔴" if f["severity"] == "CRITICAL" else "⚠️"
            lines.append(f"  {icon} [{f['category']}] {f['script']}: {f['message'][:70]}")
            shown += 1
    
    if shown == 0:
        lines.append("  ✅ No critical or warning issues found")
    
    # Trend
    try:
        history = json.load(open(HISTORY_FILE))
        recent = history.get("audits", [])[-4:]
        if len(recent) > 1:
            trend = " -> ".join(str(a["score"]) for a in recent)
            lines.append(f"\n📈 Trend: {trend}")
    except Exception:
        pass
    
    return "\n".join(lines)


def send_telegram(text):
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
    
    audit = run_audit()
    
    print(f"\n{'='*50}")
    print(f"Score: {audit['score']}/100 (Grade {audit['grade']})")
    print(f"Critical: {audit['critical']} | Warnings: {audit['warnings']} | Info: {audit['infos']}")
    print(f"{'='*50}")
    
    for f in findings:
        icon = {"CRITICAL": "🔴", "WARNING": "⚠️", "INFO": "ℹ️"}[f["severity"]]
        print(f"  {icon} [{f['category']}] {f['script']}: {f['message']}")
    
    # ── DB metrics addition to audit ─────────────────────────────────────────
    db_metrics = get_db_metrics()
    if db_metrics:
        print("\nDB Metrics:")
        funnel = db_metrics.get("funnel", {})
        print(f"  Total jobs in DB: {funnel.get('_total', 0)}")
        print(f"  Applied: {funnel.get('applied', 0)} | Stale (7d): {db_metrics.get('stale_count', 0)}")
        conversion = db_metrics.get("conversion", {})
        if conversion:
            print(f"  CV→Applied: {conversion.get('cv_to_applied', 0)}%")
            print(f"  Applied→Response: {conversion.get('applied_to_response', 0)}%")
        gaps = db_metrics.get("top_gaps", [])
        if gaps:
            print(f"  Keyword gaps: {', '.join(gaps)}")
    # ─────────────────────────────────────────────────────────────────────────

    msg = format_telegram(audit)
    print(f"\nTelegram ({len(msg)} chars):\n{msg}")
    
    if not dry_run:
        save_history(audit)
        ok = send_telegram(msg)
        print(f"\n{'✅ Sent' if ok else '❌ Send failed'}")
    else:
        print("\n[DRY RUN]")
