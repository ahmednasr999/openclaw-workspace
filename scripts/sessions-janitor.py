#!/usr/bin/env python3
"""
sessions-janitor.py — Stale session registry cleaner

Safe, conservative cleanup of stale "running" entries in agent sessions.json files.
Never deletes transcripts or JSONL files. Only updates session registry status.

Usage:
    python3 sessions-janitor.py                    # dry-run (default)
    python3 sessions-janitor.py --apply            # actually clean
    python3 sessions-janitor.py --apply --force    # skip confirmation prompts
    python3 sessions-janitor.py --agent cto --apply # only specific agent

Safety guarantees:
  1. Dry-run by default — must pass --apply to write anything
  2. Backs up sessions.json before every write
  3. Never deletes JSONL files or transcripts
  4. Never modifies live topic sessions
  5. Cross-references cron state when available
  6. Never modifies entries younger than MIN_STALE_MINUTES (default 30)
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────

MIN_STALE_MINUTES = 30
AGENTS_DIR = Path("/root/.openclaw/agents")
BACKUP_DIR = Path("/root/.openclaw/workspace/backups/sessions-janitor")
LOG_FILE = Path("/root/.openclaw/workspace/logs/sessions-janitor.log")
CRON_JOB_IDS = {}  # populated by load_cron_state()

# Live Telegram topic session prefixes — NEVER touch these
LIVE_TOPIC_PREFIXES = (
    "agent:main:telegram:group:-1003882622947:topic:",
    "agent:cto:telegram:group:-1003882622947:topic:",
    "agent:cmo:telegram:group:-1003882622947:topic:",
    "agent:hr:telegram:group:-1003882622947:topic:",
    "agent:jobzoom:telegram:group:-1003882622947:topic:",
)

# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class SessionEntry:
    key: str
    agent: str
    status: str
    updated_at: int
    age_minutes: float
    session_id: str | None
    label: str | None
    safe_action: str | None  # "done" | "error" | None
    reason: str | None
    is_live_topic: bool
    is_cron: bool
    cron_id: str | None

# ── Logging ──────────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ── Cron state loader ────────────────────────────────────────────────────────

def load_cron_state() -> dict[str, dict]:
    """Fetch active cron jobs from gateway and return dict of id -> state."""
    import subprocess
    try:
        result = subprocess.run(
            ["openclaw", "gateway", "call", "cron.list", "--params",
             json.dumps({"includeDisabled": True}),
             "--json", "--timeout", "15000"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            log(f"WARN: cron.list failed: {result.stderr.strip()}")
            return {}
        data = json.loads(result.stdout)
        jobs = data.get("jobs", [])
        return {j["id"]: j for j in jobs if "id" in j}
    except Exception as e:
        log(f"WARN: could not load cron state: {e}")
        return {}


def cron_state_for_session(entry: SessionEntry, cron_state: dict) -> tuple[str, str]:
    """
    Determine safe action based on cron state.
    Returns (action, reason) where action is "done" | "error" | "unknown" | "skip".
    """
    if not entry.is_cron or not entry.cron_id:
        return "unknown", "not a cron session"

    job = cron_state.get(entry.cron_id)
    if not job:
        return "unknown", f"cron job {entry.cron_id} not found in cron.list"

    state = job.get("state", {})
    delivery = state.get("lastDeliveryStatus", "unknown")
    status = state.get("lastRunStatus", "unknown")
    error_reason = state.get("lastErrorReason", "")
    error_msg = state.get("lastError", "")

    if delivery == "delivered" and status == "ok":
        return "done", f"cron state=ok/delivered (lastRunAt={state.get('lastRunAtMs')})"
    elif status in ("error", "failed") or delivery == "failed":
        reason_str = error_reason or error_msg or "cron error"
        return "error", f"cron state=error ({reason_str})"
    elif delivery == "unknown" and status in ("ok", "success"):
        return "done", "cron state=ok/unknown-delivery"
    else:
        return "unknown", f"cron state ambiguous: delivery={delivery} status={status}"


# ── Session analysis ─────────────────────────────────────────────────────────

def analyze_agent(agent: str, cron_state: dict, min_stale_minutes: int = MIN_STALE_MINUTES) -> list[SessionEntry]:
    """Return list of stale session entries for an agent."""
    sessions_file = AGENTS_DIR / agent / "sessions" / "sessions.json"
    if not sessions_file.exists():
        return []

    data = json.loads(sessions_file.read_text())
    now_ms = time.time() * 1000
    entries = []

    for key, rec in data.items():
        status = rec.get("status")
        if status != "running":
            continue

        ts = rec.get("updatedAt") or rec.get("createdAt") or 0
        age_min = (now_ms - ts) / 60000 if ts else 0

        if age_min < min_stale_minutes:
            continue

        # Check if it's a live topic session
        is_live_topic = any(key.startswith(p) for p in LIVE_TOPIC_PREFIXES)

        # Extract cron ID
        is_cron = ":cron:" in key
        # Format: agent:AGENT:cron:JOBID or agent:AGENT:cron:JOBID:run:RUNID
        cron_id = None
        if is_cron:
            parts = key.split(":")
            if len(parts) >= 4:
                cron_id = parts[3]

        # Determine safe action
        if is_live_topic:
            safe_action = None
            reason = "LIVE_TOPIC: never modify live topic sessions"
        elif is_cron and cron_id:
            safe_action, reason = cron_state_for_session(
                SessionEntry(key=key, agent=agent, status=status,
                             updated_at=ts, age_minutes=age_min,
                             session_id=rec.get("sessionId"),
                             label=rec.get("label"),
                             safe_action=None, reason=None,
                             is_live_topic=is_live_topic,
                             is_cron=is_cron, cron_id=cron_id),
                cron_state
            )
        else:
            # Non-cron stale running session: be conservative
            safe_action = "unknown"
            reason = f"non-cron stale running session (age={age_min:.0f}m); verify manually"

        entry = SessionEntry(
            key=key, agent=agent, status=status,
            updated_at=ts, age_minutes=age_min,
            session_id=rec.get("sessionId"),
            label=rec.get("label"),
            safe_action=safe_action, reason=reason,
            is_live_topic=is_live_topic,
            is_cron=is_cron, cron_id=cron_id
        )
        entries.append(entry)

    return entries


# ── Reporter ─────────────────────────────────────────────────────────────────

def format_entry(e: SessionEntry) -> str:
    age_h = e.age_minutes / 60
    if age_h >= 24:
        age_str = f"{age_h/24:.1f}d"
    elif age_h >= 1:
        age_str = f"{age_h:.1f}h"
    else:
        age_str = f"{e.age_minutes:.0f}m"

    action_str = e.safe_action or "skip"
    label = e.label or e.key.split(":")[-1][:40]
    return (f"  [{action_str.upper():>4}] {e.agent:<8} {age_str:>6}  {label}\n"
            f"           key: {e.key[:90]}\n"
            f"           why: {e.reason}")


def print_report(all_entries: list[SessionEntry], dry_run: bool):
    by_agent = {}
    for e in all_entries:
        by_agent.setdefault(e.agent, []).append(e)

    print("\n" + "="*70)
    mode = "DRY RUN" if dry_run else "APPLY MODE"
    print(f"  sessions-janitor — {mode}")
    print("="*70)

    total = len(all_entries)
    safe_to_clean = sum(1 for e in all_entries if e.safe_action in ("done", "error"))
    skipped_live = sum(1 for e in all_entries if e.is_live_topic)
    skipped_unknown = sum(1 for e in all_entries if e.safe_action == "unknown")

    for agent, entries in sorted(by_agent.items()):
        print(f"\n  {agent.upper()}")
        for e in sorted(entries, key=lambda x: -x.age_minutes):
            print(format_entry(e))

    print(f"\n  Summary: {total} stale entries found")
    print(f"    safe to clean : {safe_to_clean}")
    print(f"    skipped (live topic) : {skipped_live}")
    print(f"    skipped (unknown/non-cron) : {skipped_unknown}")

    if dry_run:
        print(f"\n  [DRY RUN] No changes made. Pass --apply to clean.")
    print("="*70 + "\n")


# ── Applicator ───────────────────────────────────────────────────────────────

def apply_clean(all_entries: list[SessionEntry], force: bool):
    by_agent = {}
    for e in all_entries:
        if e.safe_action not in ("done", "error"):
            continue
        by_agent.setdefault(e.agent, []).append(e)

    if not by_agent:
        log("Nothing to clean.")
        return

    # Backup all affected sessions.json files
    backup_dir = BACKUP_DIR / datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)

    for agent, entries in sorted(by_agent.items()):
        sessions_file = AGENTS_DIR / agent / "sessions" / "sessions.json"
        bak = backup_dir / f"{agent}.sessions.json.bak"
        import shutil
        shutil.copy2(sessions_file, bak)
        log(f"Backup: {bak}")

    # Confirm unless --force
    if not force:
        total = sum(len(v) for v in by_agent.values())
        print(f"\n  About to clean {total} entries across {len(by_agent)} agents.")
        print(f"  Backups saved to: {backup_dir}")
        try:
            resp = input("  Continue? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return
        if resp != "y":
            print("Aborted.")
            return

    # Apply changes
    changes = []
    for agent, entries in sorted(by_agent.items()):
        sessions_file = AGENTS_DIR / agent / "sessions" / "sessions.json"
        data = json.loads(sessions_file.read_text())

        for e in entries:
            if e.key not in data:
                continue
            old_status = data[e.key].get("status")
            if old_status != "running":
                continue

            data[e.key]["status"] = e.safe_action
            data[e.key]["endedAt"] = data[e.key].get("endedAt") or e.updated_at
            data[e.key]["updatedAt"] = int(time.time() * 1000)
            data[e.key]["staleJanitorAt"] = int(time.time() * 1000)
            data[e.key]["staleJanitorNote"] = e.reason
            data[e.key]["abortedLastRun"] = False
            if e.safe_action == "error":
                data[e.key]["lastError"] = data[e.key].get("lastError") or "cron: job execution completed with error"
                data[e.key]["lastErrorReason"] = data[e.key].get("lastErrorReason") or "timeout/cleanup"

            changes.append({
                "agent": agent, "key": e.key,
                "old": old_status, "new": e.safe_action,
                "reason": e.reason, "age_min": round(e.age_minutes, 1)
            })

        tmp = sessions_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        os.replace(tmp, sessions_file)
        log(f"Cleaned {len(entries)} entries in {agent}/sessions.json")

    log(f"Done. {len(changes)} entries updated. Backups: {backup_dir}")

    print(f"\n  Cleaned {len(changes)} entries:")
    for c in changes:
        print(f"    {c['agent']}: {c['key'][:60]}… {c['old']}→{c['new']} ({c['age_min']}m stale)")
    print(f"  Backups: {backup_dir}")


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Safe stale session registry cleaner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--apply", action="store_true",
                        help="Actually write changes (default is dry-run)")
    parser.add_argument("--force", action="store_true",
                        help="Skip confirmation prompt")
    parser.add_argument("--agent", action="append", dest="agents",
                        help="Only process specific agent(s)")
    parser.add_argument("--min-stale-minutes", type=int, default=MIN_STALE_MINUTES,
                        help=f"Only touch entries older than this (default {MIN_STALE_MINUTES})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Explicit dry-run (default)")
    args = parser.parse_args()

    log(f"Starting. args={vars(args)}")

    # Determine which agents to scan
    all_agents = [d.name for d in AGENTS_DIR.iterdir() if d.is_dir()]
    target_agents = sorted(set(args.agents or all_agents))

    log(f"Scanning agents: {target_agents}")

    # Load cron state once
    cron_state = load_cron_state()
    log(f"Loaded {len(cron_state)} cron jobs")

    # Analyze all agents
    all_entries = []
    min_stale = args.min_stale_minutes
    for agent in target_agents:
        entries = analyze_agent(agent, cron_state, min_stale_minutes=min_stale)
        all_entries.extend(entries)

    # Print report
    print_report(all_entries, dry_run=not args.apply)

    # Apply if requested
    if args.apply:
        apply_clean(all_entries, force=args.force)
    else:
        log("Dry run complete. No changes made.")


if __name__ == "__main__":
    main()
