#!/usr/bin/env python3
"""Produce a daily health card for the email agent."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "email-health.json"


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def cron_summary():
    try:
        jobs = json.loads(Path("/root/.openclaw/cron/jobs.json").read_text(encoding="utf-8")).get("jobs", [])
    except Exception:
        return []
    rows = []
    for job in jobs:
        if not isinstance(job, dict) or not job.get("name", "").startswith("Email Agent"):
            continue
        rows.append({
            "name": job.get("name"),
            "enabled": job.get("enabled"),
            "schedule": job.get("schedule"),
            "delivery": job.get("delivery"),
            "sessionTarget": job.get("sessionTarget"),
            "model": (job.get("payload") or {}).get("model"),
        })
    return rows


def run_formatter() -> str:
    try:
        cp = subprocess.run(["python3", str(ROOT / "scripts/format-email-alert.py"), "--input", str(DATA / "email-summary.json")], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return cp.stdout.strip() if cp.returncode == 0 else f"formatter_error: {cp.stderr.strip()[:300]}"
    except Exception as exc:
        return f"formatter_error: {exc}"


def main() -> int:
    now = datetime.now(ZoneInfo("Africa/Cairo")).isoformat()
    state = load_json(DATA / "email-state.json", {})
    summary = load_json(DATA / "email-summary.json", {})
    latest_data = summary.get("data") or summary
    feedback_lines = 0
    if (DATA / "email-feedback.jsonl").exists():
        feedback_lines = sum(1 for line in (DATA / "email-feedback.jsonl").read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())
    pipeline_review_lines = 0
    if (DATA / "email-pipeline-review.jsonl").exists():
        pipeline_review_lines = sum(1 for line in (DATA / "email-pipeline-review.jsonl").read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())
    health = {
        "generated_at": now,
        "status": latest_data.get("status", "unknown"),
        "last_scan_time": latest_data.get("scan_time") or (summary.get("meta") or {}).get("generated_at"),
        "last_total_scanned": latest_data.get("total_scanned"),
        "last_actionable_count": latest_data.get("actionable_count"),
        "last_hot_alerts": len(latest_data.get("hot_alerts") or []),
        "last_llm_status": "present" if latest_data.get("llm_analysis") is not None else "skipped_or_unavailable",
        "last_seen_uid": state.get("last_seen_uid"),
        "last_success": state.get("last_success"),
        "processed_count": state.get("processed_count"),
        "feedback_rules": feedback_lines,
        "pipeline_review_candidates": pipeline_review_lines,
        "cron_jobs": cron_summary(),
        "formatter_preview": run_formatter(),
    }
    OUT.write_text(json.dumps(health, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("📬 Email health")
    print(f"Status: {health['status']}")
    print(f"Last scan: {health['last_scan_time']} | scanned {health['last_total_scanned']} | actionable {health['last_actionable_count']} | hot {health['last_hot_alerts']}")
    print(f"UID: {health['last_seen_uid']} | last success: {health['last_success']} | processed: {health['processed_count']}")
    print(f"LLM: {health['last_llm_status']} | feedback rules: {feedback_lines} | review queue: {pipeline_review_lines}")
    print(f"Cron jobs: {len(health['cron_jobs'])} configured to DM")
    print(f"Snapshot: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
