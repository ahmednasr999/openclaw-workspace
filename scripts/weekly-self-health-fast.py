#!/usr/bin/env python3
"""Bounded weekly OpenClaw health decision-card for cron delivery."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path("/root/.openclaw/workspace")
REPORT_DIR = ROOT / "reports" / "weekly-self-health"
SELF_HEALTH_JOB_ID = "c7cf8709-4d01-4b9d-a8a3-64ebfe559d7f"


def run_json(cmd: list[str], timeout: int) -> tuple[dict | None, str | None]:
    try:
        cp = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=timeout,
            start_new_session=True,
        )
    except subprocess.TimeoutExpired:
        kill_children(cmd)
        return None, f"{' '.join(cmd)} timed out after {timeout}s"
    if cp.returncode != 0:
        err = (cp.stderr or cp.stdout or "").strip().splitlines()
        return None, f"{' '.join(cmd)} exited {cp.returncode}: {(err[-1] if err else 'no output')}"
    try:
        return json.loads(cp.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"{' '.join(cmd)} returned invalid JSON: {exc}"


def run_text(cmd: list[str], timeout: int) -> tuple[str | None, str | None]:
    try:
        cp = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=timeout,
            start_new_session=True,
        )
    except subprocess.TimeoutExpired:
        kill_children(cmd)
        return None, f"{' '.join(cmd)} timed out after {timeout}s"
    if cp.returncode != 0:
        err = (cp.stderr or cp.stdout or "").strip().splitlines()
        return None, f"{' '.join(cmd)} exited {cp.returncode}: {(err[-1] if err else 'no output')}"
    return cp.stdout.strip(), None


def kill_children(cmd: list[str]) -> None:
    # subprocess.run kills only the direct child. OpenClaw CLI commands can spawn
    # worker threads/processes, so kill matching process groups defensively.
    joined = " ".join(cmd)
    try:
        subprocess.run(["pkill", "-9", "-f", joined], timeout=5)
    except Exception:
        pass


def disk_line() -> tuple[str, str | None]:
    usage = shutil.disk_usage("/")
    used_pct = round((usage.used / usage.total) * 100)
    free_gb = usage.free / (1024**3)
    line = f"{used_pct}% used, {free_gb:.0f}G free"
    issue = None
    if used_pct >= 90:
        issue = f"Disk is near full: {line}"
    elif used_pct >= 80:
        issue = f"Disk is high: {line}"
    return line, issue


def model_line() -> tuple[str, str | None]:
    out, err = run_text(["openclaw", "models", "status"], 25)
    if err:
        return "model status unavailable", err
    default = "unknown"
    for line in out.splitlines():
        if line.strip().startswith("Default"):
            default = line.split(":", 1)[-1].strip()
            break
    return default, None


def cron_findings(cron_data: dict | None) -> tuple[list[str], list[str]]:
    critical: list[str] = []
    monitor: list[str] = []
    if not cron_data:
        return critical, monitor
    jobs = cron_data.get("jobs") or []
    error_jobs = []
    for job in jobs:
        state = job.get("state") or {}
        status = job.get("status") or state.get("lastRunStatus") or state.get("lastStatus")
        if status == "error":
            error_jobs.append(job)
    for job in error_jobs[:5]:
        state = job.get("state") or {}
        name = job.get("name") or job.get("id")
        errors = state.get("consecutiveErrors") or 0
        detail = state.get("lastDiagnosticSummary") or state.get("lastError") or "last run errored"
        text = f"{name}: {detail}"
        if job.get("id") == SELF_HEALTH_JOB_ID:
            monitor.append(f"{name}: previous failures before this bounded run - {detail}")
            continue
        if errors >= 2:
            critical.append(text)
        else:
            monitor.append(text)
    if len(error_jobs) > 5:
        monitor.append(f"{len(error_jobs) - 5} additional errored cron job(s) not listed")
    return critical, monitor


def format_card(write_report: bool) -> str:
    now = datetime.now(ZoneInfo("Africa/Cairo"))
    health, health_err = run_json(["openclaw", "health", "--json"], 30)
    crons, cron_err = run_json(["openclaw", "cron", "list", "--json"], 35)
    security, security_err = run_json(["openclaw", "security", "audit", "--json"], 60)
    model, model_err = model_line()
    disk, disk_issue = disk_line()

    critical: list[str] = []
    important: list[tuple[str, str, str]] = []
    monitor: list[str] = []

    if health_err:
        critical.append(f"Gateway health probe failed: {health_err}")
        gateway = "unknown - health probe failed"
        channels = "unknown"
    else:
        ok = bool(health.get("ok"))
        event_loop = health.get("eventLoop") or {}
        gateway = "healthy" if ok else "degraded"
        if event_loop.get("degraded"):
            gateway = f"degraded - event loop {','.join(event_loop.get('reasons') or ['degraded'])}"
            critical.append(f"Gateway event loop degraded: {event_loop.get('reasons')}")
        channels_data = health.get("channels") or {}
        telegram = channels_data.get("telegram") or {}
        connected = telegram.get("connected")
        channels = f"Telegram {'connected' if connected else 'not connected'}"
        if not connected:
            critical.append("Telegram channel is not connected")

    if model_err:
        important.append(("Model status probe failed", model_err, "Check model/auth status before relying on agent-heavy crons."))

    if cron_err:
        important.append(("Cron inventory probe failed", cron_err, "Run cron diagnostics separately."))
    else:
        cron_critical, cron_monitor = cron_findings(crons)
        critical.extend(cron_critical)
        monitor.extend(cron_monitor)

    if security_err:
        important.append(("Security audit probe failed", security_err, "Run the security audit separately."))
        security_line = "unavailable"
    else:
        summary = security.get("summary") or {}
        c = summary.get("critical", 0)
        w = summary.get("warn", 0)
        i = summary.get("info", 0)
        security_line = f"{c} critical, {w} warn, {i} info"
        if c:
            critical.append(f"Security audit reports {c} critical finding(s)")
        elif w:
            important.append(("Security posture warnings remain", security_line, "Keep staged hardening on the maintenance backlog."))

    if disk_issue:
        target = critical if "near full" in disk_issue else monitor
        target.append(disk_issue)

    if critical:
        verdict = "🚨 Action needed"
        urgency = "act now"
        recommendation = "Fix the critical item(s) below before treating weekly health as green."
    elif important:
        verdict = "⚠️ Attention needed"
        urgency = "schedule"
        recommendation = "Schedule the listed hardening or diagnostic follow-up."
    else:
        verdict = "✅ Healthy"
        urgency = "none"
        recommendation = "No action required."

    lines: list[str] = [
        f"{verdict} Weekly OpenClaw health",
        "",
        "Bottom line:",
        f"- Core system: {gateway} - {channels}, default model {model}",
        f"- Urgency: {urgency}",
        f"- Recommendation: {recommendation}",
        "",
        "🚨 Critical",
    ]
    if critical:
        lines.extend(f"{idx}. {item}" for idx, item in enumerate(critical[:5], 1))
    else:
        lines.append("- None.")

    lines.append("")
    lines.append("⚠️ Important")
    if important:
        for idx, (issue, impact, rec) in enumerate(important[:5], 1):
            lines.extend([f"{idx}. {issue}", f"   Impact: {impact}", f"   Recommendation: {rec}"])
    else:
        lines.append("- None.")

    lines.append("")
    lines.append("ℹ️ Monitor")
    if monitor:
        lines.extend(f"- {item}" for item in monitor[:6])
    else:
        lines.append("- No non-blocking warnings.")

    lines.extend([
        "",
        "Evidence checked:",
        f"- Gateway: {gateway}",
        f"- Channels: {channels}",
        f"- Disk/memory: {disk}",
        f"- Security audit: {security_line}",
    ])

    output = "\n".join(lines)
    if write_report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report = REPORT_DIR / f"{now:%Y-%m-%d}.md"
        report.write_text(output + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    print(format_card(write_report=args.write_report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
