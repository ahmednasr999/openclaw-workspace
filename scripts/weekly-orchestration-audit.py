#!/usr/bin/env python3
"""Deterministic weekly audit of recurring OpenClaw work.

The audit is advisory. It reads cron state and local coordination evidence,
classifies routines, and writes durable JSON/Markdown reports. It never edits,
disables, combines, or schedules jobs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path("/root/.openclaw/workspace")
DEFAULT_REPORT_DIR = ROOT / "reports" / "orchestration-audit"
COORDINATION_FILES = (
    ROOT / "coordination" / "dashboard.json",
    ROOT / "coordination" / "pipeline.json",
    ROOT / "coordination" / "content-calendar.json",
    ROOT / "coordination" / "outreach-queue.json",
)
ACCOUNT_REGISTRY = ROOT / "data" / "account-experts" / "registry.json"
LEARNING_REGISTRY = ROOT / "data" / "learning-loop" / "registry.json"
STATE_DB = Path("/root/.openclaw/state/openclaw.sqlite")


def cairo_now() -> dt.datetime:
    return dt.datetime.now().astimezone()


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def load_cron_database(path: Path = STATE_DB) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)
    try:
        rows = connection.execute(
            "SELECT job_json, state_json FROM cron_jobs ORDER BY sort_order, updated_at, job_id"
        ).fetchall()
    finally:
        connection.close()
    jobs = []
    for job_text, state_text in rows:
        job = json.loads(job_text)
        state = json.loads(state_text or "{}")
        if isinstance(state, dict):
            job["state"] = {**(job.get("state") or {}), **state}
        job["status"] = job.get("status") or (job.get("state") or {}).get("lastRunStatus")
        jobs.append(job)
    return {"jobs": jobs, "source": "sqlite-read-only"}


def load_cron(path: Path | None) -> dict[str, Any]:
    if path:
        return load_json(path, {"jobs": []})
    try:
        return load_cron_database()
    except Exception as database_error:
        errors = [f"read-only database: {database_error}"]
    for _attempt in range(2):
        result = subprocess.run(
            ["openclaw", "cron", "list", "--json"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        errors.append((result.stderr or result.stdout).strip())
    raise RuntimeError(
        "read-only cron database and two CLI attempts failed: " + "; ".join(errors[-3:])
    )


def family_name(name: str) -> str:
    value = name.lower()
    value = re.sub(r"\b(?:[01]?\d|2[0-3])(?::?\d{2})?\s*(?:am|pm|cairo)?\b", "", value)
    value = re.sub(r"\b(?:daily|weekly|nightly|midday|morning|evening)\b", "", value)
    value = re.sub(r"[^a-z]+", " ", value)
    return " ".join(value.split())


def deterministic_agent_turn(job: dict[str, Any]) -> bool:
    payload = job.get("payload") or {}
    if payload.get("kind") != "agentTurn":
        return False
    message = str(payload.get("message") or "").lower()
    command_markers = ("python3 ", "node ", ".sh", "run `/", "run /root/")
    judgment_markers = ("analyze", "research", "draft", "recommend", "review the", "inspect the")
    return any(marker in message for marker in command_markers) and not any(
        marker in message for marker in judgment_markers
    )


def classify_jobs(jobs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    families: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for job in jobs:
        families[family_name(str(job.get("name") or job.get("id") or "unnamed"))].append(job)

    rows: list[dict[str, Any]] = []
    counts = defaultdict(int)
    for job in jobs:
        state = job.get("state") or {}
        status = str(job.get("status") or state.get("lastRunStatus") or "unknown")
        errors = int(state.get("consecutiveErrors") or 0)
        enabled = bool(job.get("enabled", True))
        family = family_name(str(job.get("name") or job.get("id") or "unnamed"))
        reasons: list[str] = []

        if not enabled:
            action = "RETIRE-REVIEW"
            reasons.append("job is disabled; confirm whether its retained state still has rollback value")
        elif errors >= 2 or status == "error":
            action = "FIX"
            reasons.append(f"status={status}; consecutive_errors={errors}")
        elif deterministic_agent_turn(job):
            action = "AUTOMATE"
            reasons.append("agent turn appears to wrap a deterministic local command")
        elif len(families[family]) > 1:
            action = "COMBINE-REVIEW"
            reasons.append(f"{len(families[family])} routines share the same normalized family")
        else:
            action = "KEEP"
            reasons.append("enabled with no deterministic issue found")

        counts[action] += 1
        rows.append(
            {
                "id": job.get("id"),
                "name": job.get("name"),
                "action": action,
                "reason": "; ".join(reasons),
                "status": status,
                "consecutive_errors": errors,
                "payload_kind": (job.get("payload") or {}).get("kind"),
                "schedule": job.get("schedule") or {},
            }
        )
    return rows, dict(counts)


def coordination_status(now: dt.datetime) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in COORDINATION_FILES:
        if not path.exists():
            rows.append({"path": str(path), "state": "missing", "age_days": None, "bytes": 0})
            continue
        modified = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=now.tzinfo)
        age_days = max(0, (now - modified).days)
        size = path.stat().st_size
        state = "current" if age_days <= 7 and size > 2 else "stale-or-empty"
        rows.append({"path": str(path), "state": state, "age_days": age_days, "bytes": size})
    return rows


def parallel_candidates(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find conservative same-hour review clusters; never reschedule them."""
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for job in jobs:
        if not job.get("enabled", True):
            continue
        schedule = job.get("schedule") or {}
        if schedule.get("kind") != "cron":
            continue
        parts = str(schedule.get("expr") or "").split()
        if len(parts) != 5 or not parts[0].isdigit() or not parts[1].isdigit():
            continue
        name = str(job.get("name") or "")
        if re.search(r"linkedin|browser|publishing|comment radar", name, re.I):
            continue
        groups[(parts[4], parts[1])].append(job)
    results = []
    for (weekday, hour), cluster in groups.items():
        owners = {str(item.get("agentId") or item.get("ownerAgentId") or "default") for item in cluster}
        if len(cluster) < 2 or len(owners) < 2:
            continue
        results.append({
            "weekday": weekday,
            "hour": hour,
            "jobs": [item.get("name") for item in cluster],
            "owners": sorted(owners),
            "reason": "independent owners share the same cron hour; verify CPU/browser/database isolation before tightening the schedule",
        })
    return results


def learning_status() -> dict[str, int]:
    data = load_json(LEARNING_REGISTRY, {})
    candidates = data.get("candidates") or []
    return {
        "observations": len(data.get("observations") or []),
        "reviewable_candidates": sum(item.get("status") == "review" for item in candidates),
        "verified_candidates": sum(item.get("status") == "verified" for item in candidates),
        "automatic_deployments": 0,
    }


def account_status(now: dt.datetime) -> dict[str, Any]:
    data = load_json(ACCOUNT_REGISTRY, {"accounts": []})
    accounts = data.get("accounts") or []
    stale = 0
    for account in accounts:
        refreshed = account.get("last_refreshed_at")
        try:
            stamp = dt.datetime.fromisoformat(refreshed)
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=now.tzinfo)
            stale += (now - stamp).days > 14
        except (TypeError, ValueError):
            stale += 1
    return {"active": len(accounts), "stale_over_14_days": stale, "limit": data.get("active_limit", 7)}


def recommendations(rows: list[dict[str, Any]], coordination: list[dict[str, Any]], accounts: dict[str, Any], parallel: list[dict[str, Any]]) -> list[str]:
    priority = {"FIX": 0, "AUTOMATE": 1, "COMBINE-REVIEW": 2, "RETIRE-REVIEW": 3}
    candidates = [row for row in rows if row["action"] != "KEEP"]
    candidates.sort(key=lambda row: (priority[row["action"]], -row["consecutive_errors"], str(row["name"])))
    result = [f"{row['action']}: {row['name']} - {row['reason']}" for row in candidates[:8]]
    stale_files = [Path(row["path"]).name for row in coordination if row["state"] != "current"]
    if stale_files:
        result.append("COORDINATION-REVIEW: " + ", ".join(stale_files))
    if accounts.get("stale_over_14_days"):
        result.append(f"ACCOUNT-REFRESH: {accounts['stale_over_14_days']} priority employer dossier(s) are older than 14 days")
    for item in parallel[:2]:
        result.append(
            f"PARALLELIZE-REVIEW: weekday {item['weekday']} hour {item['hour']} - "
            + ", ".join(str(name) for name in item["jobs"])
            + f"; {item['reason']}"
        )
    return result


def render_markdown(payload: dict[str, Any]) -> str:
    counts = payload["counts"]
    job_lines = "\n".join(
        f"- **{row['action']}** - {row['name']}: {row['reason']}"
        for row in payload["jobs"]
    )
    coordination_lines = "\n".join(
        f"- `{row['path']}` - {row['state']} (age={row['age_days']}, bytes={row['bytes']})"
        for row in payload["coordination"]
    )
    rec_lines = "\n".join(f"- {item}" for item in payload["recommendations"]) or "- Clean-noop: no action recommended."
    return f"""# Weekly Orchestration Audit

Generated: {payload['generated_at']}
Terminal state: {payload['terminal_state']}

## Decision Summary

- Keep: {counts.get('KEEP', 0)}
- Fix: {counts.get('FIX', 0)}
- Automate: {counts.get('AUTOMATE', 0)}
- Combine-review: {counts.get('COMBINE-REVIEW', 0)}
- Retire-review: {counts.get('RETIRE-REVIEW', 0)}
- Parallelize-review clusters: {len(payload['parallelize_review'])}
- Account experts: {payload['accounts']['active']} active; {payload['accounts']['stale_over_14_days']} stale
- Governed learning: {payload['learning']['reviewable_candidates']} reviewable candidate(s); automatic deployments: 0

## Recommendations

{rec_lines}

## Recurring Jobs

{job_lines}

## Coordination Files

{coordination_lines}

## Guardrails

- Advisory only: no job was edited, disabled, combined, scheduled, or deleted.
- Learning candidates remain inactive until replay gates and Ahmed's exact promotion approval pass.
- Employer intelligence is local decision support; outbound contact remains approval-gated.
"""


def run(args: argparse.Namespace) -> dict[str, Any]:
    now = dt.datetime.fromisoformat(args.now) if args.now else cairo_now()
    cron = load_cron(args.cron_json)
    jobs = cron.get("jobs") or []
    rows, counts = classify_jobs(jobs)
    coordination = coordination_status(now)
    learning = learning_status()
    accounts = account_status(now)
    parallel = parallel_candidates(jobs)
    recs = recommendations(rows, coordination, accounts, parallel)
    payload = {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "terminal_state": "success" if recs else "clean-noop",
        "counts": counts,
        "jobs": rows,
        "coordination": coordination,
        "learning": learning,
        "accounts": accounts,
        "parallelize_review": parallel,
        "recommendations": recs,
        "mutations_performed": 0,
    }
    report_dir = args.report_dir
    dated = report_dir / f"orchestration-audit-{now:%Y-%m-%d}.md"
    atomic_write(dated, render_markdown(payload))
    atomic_write(report_dir / "latest.md", render_markdown(payload))
    atomic_write(report_dir / "latest.json", json.dumps(payload, indent=2, sort_keys=True) + "\n")
    payload["report"] = str(dated)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cron-json", type=Path)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--now", help="ISO timestamp override for tests")
    args = parser.parse_args()
    try:
        payload = run(args)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({
        "status": payload["terminal_state"],
        "keep": payload["counts"].get("KEEP", 0),
        "fix": payload["counts"].get("FIX", 0),
        "automate": payload["counts"].get("AUTOMATE", 0),
        "combine_review": payload["counts"].get("COMBINE-REVIEW", 0),
        "retire_review": payload["counts"].get("RETIRE-REVIEW", 0),
        "parallelize_review": len(payload["parallelize_review"]),
        "accounts": payload["accounts"]["active"],
        "report": payload["report"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
