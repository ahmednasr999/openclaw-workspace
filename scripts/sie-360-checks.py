#!/usr/bin/env python3
"""
SIE 360 Deterministic Checks - Standalone Script
Runs all mechanical checks and outputs results to data/sie-360.json.
This script has NO LLM dependency - runs on system crontab at 3:50 AM Cairo.
"""

import json
import os
import re
import subprocess
import ssl
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
OUTPUT_FILE = os.path.join(WORKSPACE, "data/sie-360.json")
CRONS_RAW_TMP = "/tmp/sie_crons_raw.txt"

findings = []
auto_fixed = []
needs_attention = []


def add_finding(category, level, message):
    findings.append({"category": category, "level": level, "message": message})


# ─────────────────────────────────────────────
# STEP 1: WORKSPACE HEALTH
# ─────────────────────────────────────────────

def check_workspace():
    result = {}

    # Root file count
    try:
        r = subprocess.run(
            ["find", WORKSPACE, "-maxdepth", "1", "-type", "f"],
            capture_output=True, text=True
        )
        root_files = len([l for l in r.stdout.strip().split("\n") if l])
        result["root_files"] = root_files
        if root_files < 60:
            add_finding("workspace", "ok", f"Root files: {root_files} (healthy)")
        elif root_files < 100:
            add_finding("workspace", "warn", f"Root files: {root_files} (approaching clutter threshold of 100)")
        else:
            add_finding("workspace", "alert", f"Root files: {root_files} (exceeded 100 - needs cleanup)")
    except Exception as e:
        result["root_files"] = -1
        add_finding("workspace", "warn", f"Root file count failed: {e}")

    # Disk usage
    try:
        r = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
        lines = r.stdout.strip().split("\n")
        if len(lines) >= 2:
            parts = lines[1].split()
            disk_used = parts[2] if len(parts) > 2 else "?"
            disk_total = parts[1] if len(parts) > 1 else "?"
            disk_pct_str = parts[4] if len(parts) > 4 else "0%"
            disk_pct = int(disk_pct_str.rstrip("%"))
            result["disk_percent"] = disk_pct
            result["disk_used"] = disk_used
            result["disk_total"] = disk_total
            if disk_pct < 80:
                add_finding("workspace", "ok", f"Disk: {disk_pct}% used ({disk_used}/{disk_total})")
            elif disk_pct < 90:
                add_finding("workspace", "warn", f"Disk: {disk_pct}% used - approaching 90% threshold")
            else:
                add_finding("workspace", "alert", f"Disk: {disk_pct}% used - CRITICAL, manual cleanup required")
        else:
            result["disk_percent"] = -1
            result["disk_used"] = "?"
            result["disk_total"] = "?"
    except Exception as e:
        result["disk_percent"] = -1
        result["disk_used"] = "?"
        result["disk_total"] = "?"
        add_finding("workspace", "warn", f"Disk check failed: {e}")

    # Memory
    try:
        r = subprocess.run(["free", "-h"], capture_output=True, text=True)
        for line in r.stdout.split("\n"):
            if line.startswith("Mem:"):
                parts = line.split()
                result["ram_total"] = parts[1] if len(parts) > 1 else "?"
                result["ram_used"] = parts[2] if len(parts) > 2 else "?"
                break
    except Exception as e:
        result["ram_total"] = "?"
        result["ram_used"] = "?"

    # Large files (>5MB) in .openclaw
    try:
        r = subprocess.run(
            ["find", "/root/.openclaw", "-size", "+5M", "-type", "f"],
            capture_output=True, text=True, timeout=30
        )
        large_files = [l for l in r.stdout.strip().split("\n") if l]
        # Never print file contents, just paths
        result["large_files"] = large_files
        if large_files:
            add_finding("workspace", "warn", f"Large files (>5MB): {len(large_files)} found in .openclaw")
    except Exception as e:
        result["large_files"] = []
        add_finding("workspace", "warn", f"Large file scan failed: {e}")

    # Session size
    try:
        session_dir = "/root/.openclaw/agents/main/sessions/"
        if os.path.exists(session_dir):
            r = subprocess.run(["du", "-sb", session_dir], capture_output=True, text=True)
            if r.stdout:
                size_bytes = int(r.stdout.split()[0])
                size_mb = round(size_bytes / 1024 / 1024, 1)
                result["session_mb"] = size_mb
                if size_mb < 50:
                    add_finding("workspace", "ok", f"Session size: {size_mb}MB (healthy)")
                elif size_mb < 100:
                    add_finding("workspace", "warn", f"Session size: {size_mb}MB (approaching 100MB threshold)")
                else:
                    add_finding("workspace", "alert", f"Session size: {size_mb}MB - bloated, review sessions")
                    needs_attention.append(f"Session bloat: {size_mb}MB - review before deleting (needs human decision)")
            else:
                result["session_mb"] = -1
        else:
            result["session_mb"] = 0
    except Exception as e:
        result["session_mb"] = -1
        add_finding("workspace", "warn", f"Session size check failed: {e}")

    return result


# ─────────────────────────────────────────────
# STEP 2: LEARNINGS ENFORCEMENT
# ─────────────────────────────────────────────

def check_learnings():
    result = {"total": 0, "enforced": 0, "unenforced": 0, "unenforced_list": []}
    learnings_path = os.path.join(WORKSPACE, ".learnings/LEARNINGS.md")

    if not os.path.exists(learnings_path):
        add_finding("learnings", "warn", "LEARNINGS.md not found")
        return result

    try:
        with open(learnings_path) as f:
            content = f.read()

        entries = re.split(r'\n(?=## 20)', content)
        entries = [e for e in entries if e.strip().startswith("## 20")]
        total = len(entries)
        enforced = sum(1 for e in entries if "### Enforcement" in e)
        unenforced = total - enforced
        unenforced_list = []
        for e in entries:
            if "### Enforcement" not in e:
                title = e.split("\n")[0][:80].strip()
                unenforced_list.append(title)

        result["total"] = total
        result["enforced"] = enforced
        result["unenforced"] = unenforced
        result["unenforced_list"] = unenforced_list

        if total == 0:
            add_finding("learnings", "warn", "No learning entries found in LEARNINGS.md")
        elif unenforced == 0:
            add_finding("learnings", "ok", f"Learnings enforcement: {enforced}/{total} (100%)")
        else:
            pct = round(100 * enforced / total)
            if pct >= 90:
                add_finding("learnings", "warn", f"Learnings enforcement: {enforced}/{total} ({pct}%) - {unenforced} untagged")
            else:
                add_finding("learnings", "alert", f"Learnings enforcement: {enforced}/{total} ({pct}%) - {unenforced} untagged entries need ### Enforcement")

    except Exception as e:
        add_finding("learnings", "warn", f"Learnings check failed: {e}")

    return result


# ─────────────────────────────────────────────
# STEP 3: INTEGRATION HEALTH
# ─────────────────────────────────────────────

def check_integrations():
    result = {
        "gmail": "missing",
        "notion": "missing",
        "linkedin": "missing",
        "gateway": "down",
        "details": {}
    }

    # Gmail - himalaya app password check
    try:
        himalaya_config = os.path.expanduser("~/.config/himalaya/config.toml")
        if os.path.exists(himalaya_config):
            with open(himalaya_config) as f:
                content = f.read()
            if 'auth.type = "password"' in content:
                result["gmail"] = "ok"
                result["details"]["gmail"] = "App Password configured (himalaya IMAP/SMTP)"
                add_finding("integrations", "ok", "Gmail: App Password configured via himalaya")
            else:
                result["gmail"] = "warn"
                result["details"]["gmail"] = "himalaya config found but no password auth"
                add_finding("integrations", "warn", "Gmail: himalaya config exists but no App Password auth found")
        else:
            result["gmail"] = "missing"
            result["details"]["gmail"] = "himalaya config not found"
            add_finding("integrations", "warn", "Gmail: himalaya config not found")
    except Exception as e:
        result["gmail"] = "warn"
        result["details"]["gmail"] = f"check failed: {e}"

    # Notion - token + databases
    try:
        notion_config = os.path.join(WORKSPACE, "config/notion.json")
        if os.path.exists(notion_config):
            with open(notion_config) as f:
                notion_data = json.load(f)
            token = notion_data.get("token", "")
            if token:
                result["details"]["notion_token"] = f"present ({len(token)} chars)"
                # Count databases
                db_config = os.path.join(WORKSPACE, "config/notion-databases.json")
                if os.path.exists(db_config):
                    with open(db_config) as f:
                        dbs = json.load(f)
                    db_count = len(dbs) if isinstance(dbs, (list, dict)) else 0
                    result["details"]["notion_databases"] = db_count
                    result["notion"] = "ok"
                    add_finding("integrations", "ok", f"Notion: token present, {db_count} databases configured")
                else:
                    result["notion"] = "warn"
                    result["details"]["notion_databases"] = 0
                    add_finding("integrations", "warn", "Notion: token present but notion-databases.json missing")
            else:
                result["notion"] = "missing"
                result["details"]["notion_token"] = "empty"
                add_finding("integrations", "alert", "Notion: token is empty in config/notion.json")
        else:
            result["notion"] = "missing"
            result["details"]["notion_token"] = "config file not found"
            add_finding("integrations", "alert", "Notion: config/notion.json not found")
    except Exception as e:
        result["notion"] = "warn"
        result["details"]["notion_error"] = str(e)
        add_finding("integrations", "warn", f"Notion check failed: {e}")

    # LinkedIn cookies
    try:
        cookie_file = os.path.expanduser("~/.openclaw/cookies/linkedin.txt")
        if os.path.exists(cookie_file):
            with open(cookie_file) as f:
                lines = [l for l in f.readlines() if l.strip()]
            line_count = len(lines)
            age_days = (datetime.now().timestamp() - os.path.getmtime(cookie_file)) / 86400
            result["details"]["linkedin_lines"] = line_count
            result["details"]["linkedin_age_days"] = round(age_days, 1)
            if line_count < 5:
                result["linkedin"] = "warn"
                add_finding("integrations", "warn", f"LinkedIn: cookies file suspiciously small ({line_count} lines)")
            elif age_days > 14:
                result["linkedin"] = "stale"
                add_finding("integrations", "warn", f"LinkedIn: cookies are {round(age_days)}d old (>14d may be stale)")
            else:
                result["linkedin"] = "ok"
                add_finding("integrations", "ok", f"LinkedIn: cookies OK ({line_count} lines, {round(age_days)}d old)")
        else:
            result["linkedin"] = "missing"
            result["details"]["linkedin_lines"] = 0
            add_finding("integrations", "warn", "LinkedIn: no cookies file at ~/.openclaw/cookies/linkedin.txt")
    except Exception as e:
        result["linkedin"] = "warn"
        result["details"]["linkedin_error"] = str(e)

    # Gateway status
    try:
        r = subprocess.run(
            ["openclaw", "gateway", "status"],
            capture_output=True, text=True, timeout=30
        )
        output = r.stdout + r.stderr
        # Filter plugin log lines
        clean = "\n".join(l for l in output.split("\n") if not l.startswith("[plugins]"))
        if "running" in clean.lower() or "active" in clean.lower() or r.returncode == 0:
            result["gateway"] = "ok"
            add_finding("integrations", "ok", "Gateway: running")
        else:
            result["gateway"] = "down"
            result["details"]["gateway_output"] = clean[:200]
            add_finding("integrations", "warn", "Gateway: status unclear or not running")
    except Exception as e:
        result["gateway"] = "down"
        result["details"]["gateway_error"] = str(e)
        add_finding("integrations", "warn", f"Gateway check failed: {e}")

    return result


# ─────────────────────────────────────────────
# STEP 4: CRON HEALTH
# ─────────────────────────────────────────────

def check_crons():
    result = {
        "total": 0,
        "enabled": 0,
        "disabled": 0,
        "skill_first": 0,
        "skill_first_pct": 0,
        "raw_prompt_list": [],
        "failing": []
    }

    try:
        r = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            capture_output=True, text=True, timeout=30
        )
        raw_output = r.stdout + r.stderr

        # Save raw for reference
        with open(CRONS_RAW_TMP, "w") as f:
            f.write(raw_output)

        # Strip plugin log lines
        clean_lines = [l for l in raw_output.split("\n") if not l.startswith("[plugins]")]
        clean = "\n".join(clean_lines)

        # Find JSON
        decoder = json.JSONDecoder()
        data = None
        for i, ch in enumerate(clean):
            if ch == "{":
                try:
                    data, _ = decoder.raw_decode(clean[i:])
                    break
                except json.JSONDecodeError:
                    continue

        if data is None:
            add_finding("crons", "warn", "Could not parse cron list JSON output")
            return result

        jobs = data.get("jobs", [])
        total = len(jobs)
        enabled = sum(1 for j in jobs if j.get("enabled", False))
        disabled = total - enabled

        skill_first = 0
        raw_prompt_list = []
        failing = []

        for j in jobs:
            msg = j.get("payload", {}).get("message", "")
            name = j.get("name", "?")
            if "Read and follow" in msg and ".md" in msg:
                skill_first += 1
            else:
                raw_prompt_list.append(name)

            state = j.get("state", {})
            consec = state.get("consecutiveErrors", 0)
            if consec > 0:
                last_err = str(state.get("lastError", ""))[:100]
                failing.append({
                    "name": name,
                    "consecutive_errors": consec,
                    "last_error": last_err
                })
                if consec >= 3:
                    needs_attention.append(f"'{name}' has {consec} consecutive errors - investigate manually")

        skill_first_pct = round(100 * skill_first / total) if total > 0 else 100

        result["total"] = total
        result["enabled"] = enabled
        result["disabled"] = disabled
        result["skill_first"] = skill_first
        result["skill_first_pct"] = skill_first_pct
        result["raw_prompt_list"] = raw_prompt_list
        result["failing"] = failing

        if skill_first_pct == 100:
            add_finding("crons", "ok", f"Cron skill-first: {skill_first}/{total} (100%)")
        elif skill_first_pct >= 90:
            add_finding("crons", "warn", f"Cron skill-first: {skill_first}/{total} ({skill_first_pct}%) - {len(raw_prompt_list)} raw-prompt crons")
        else:
            add_finding("crons", "alert", f"Cron skill-first: {skill_first}/{total} ({skill_first_pct}%) - too many raw-prompt crons")

        if failing:
            add_finding("crons", "warn", f"Failing crons: {len(failing)} with consecutive errors")
        else:
            add_finding("crons", "ok", "No failing crons")

        if disabled > 0:
            add_finding("crons", "warn", f"{disabled} crons are disabled")

    except Exception as e:
        add_finding("crons", "warn", f"Cron check failed: {e}")

    return result


# ─────────────────────────────────────────────
# STEP 5: CRON DELIVERY VERIFICATION
# Notion briefing page check REMOVED 2026-03-31
# Briefing pipeline migrated to NocoDB + Telegram alerts - no Notion page is created.

def check_briefing_notion():
    # No-op: Notion briefing page no longer created. NocoDB is source of truth.
    add_finding("briefing", "ok", "Notion briefing check disabled - pipeline uses NocoDB+Telegram")
    return {"skipped": True, "reason": "migrated to NocoDB+Telegram"}


# ─────────────────────────────────────────────
# STEP 6: AUTO-REMEDIATION (safe GREEN LIGHT only)
# ─────────────────────────────────────────────

def run_auto_remediation(crons_data):
    """
    Safe auto-fixes only:
    - Single transient errors: note only (no re-run)
    - DO NOT do raw-prompt-to-skill conversion (too risky unattended)
    - DO NOT auto-create Notion pages
    - DO NOT edit jobs.json
    """
    for item in crons_data.get("failing", []):
        name = item["name"]
        consec = item.get("consecutive_errors", 0)
        last_err = item.get("last_error", "").lower()
        if consec == 1 and "timed out" not in last_err:
            auto_fixed.append(f"'{name}' had 1 transient error - will auto-clear on next scheduled run")
        elif consec >= 3:
            # already added to needs_attention in check_crons
            pass

    # Disk > 80% - flag only
    disk_pct = -1
    for f in findings:
        if f["category"] == "workspace" and "Disk:" in f["message"]:
            m = re.search(r"Disk: (\d+)%", f["message"])
            if m:
                disk_pct = int(m.group(1))
    if disk_pct > 80:
        needs_attention.append(f"Disk usage {disk_pct}% - needs cleanup decision (do not auto-delete)")


# ─────────────────────────────────────────────
# STEP 7: HEALTH SCORE
# ─────────────────────────────────────────────

def compute_health_score():
    score = 100
    ok_count = 0
    warn_count = 0
    alert_count = 0

    for f in findings:
        level = f["level"]
        if level == "alert":
            score -= 5
            alert_count += 1
        elif level == "warn":
            score -= 2
            warn_count += 1
        elif level == "info":
            score -= 1
        else:
            ok_count += 1

    score = max(0, score)
    return score, {"ok": ok_count, "warn": warn_count, "alert": alert_count}


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print("SIE 360 Checks starting...")

    workspace_data = check_workspace()
    print("  Step 1: Workspace health done")

    learnings_data = check_learnings()
    print("  Step 2: Learnings enforcement done")

    integrations_data = check_integrations()
    print("  Step 3: Integration health done")

    crons_data = check_crons()
    print("  Step 4: Cron health done")

    briefing_data = check_briefing_notion()
    print("  Step 5: Briefing verification done")

    run_auto_remediation(crons_data)
    print("  Step 6: Auto-remediation done")

    health_score, summary = compute_health_score()
    print(f"  Step 7: Health score = {health_score}/100")

    output = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "health_score": health_score,
        "summary": summary,
        "workspace": workspace_data,
        "learnings": learnings_data,
        "integrations": integrations_data,
        "crons": crons_data,
        "briefing_notion": briefing_data,
        "findings": findings,
        "auto_fixed": auto_fixed,
        "needs_attention": needs_attention
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Output written to {OUTPUT_FILE}")
    print(f"Health score: {health_score}/100 | OK:{summary['ok']} WARN:{summary['warn']} ALERT:{summary['alert']}")
    if needs_attention:
        print(f"Needs attention: {len(needs_attention)} items")


if __name__ == "__main__":
    main()
