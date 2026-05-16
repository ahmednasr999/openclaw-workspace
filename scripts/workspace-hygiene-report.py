#!/usr/bin/env python3
"""Classify dirty OpenClaw workspace files by owner and risk."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import subprocess


WORKSPACE = Path("/root/.openclaw/workspace")
LANES = {
    "CEO/NASR": WORKSPACE,
    "HR": Path("/root/.openclaw/workspace-hr"),
    "CTO": Path("/root/.openclaw/workspace-cto"),
    "CMO": Path("/root/.openclaw/workspace-cmo"),
    "JobZoom": Path("/root/.openclaw/workspace-jobzoom"),
}


def git_status(repo: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(repo), "status", "--short"],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if proc.returncode != 0:
        return ["!! git status failed for {}: {}".format(repo, proc.stderr.strip())]
    return [line.rstrip() for line in proc.stdout.splitlines() if line.strip()]


def classify(path: str) -> tuple[str, str, str]:
    clean_path = path.strip()
    if clean_path.startswith("../openclaw.json"):
        return ("Core runtime config", "high", "review carefully, validate config, restart only in approved window")
    if clean_path.startswith("../cron/jobs.json"):
        return ("Cron runtime state/config", "medium", "review before cron mutation")
    if clean_path.startswith("../agents/"):
        return ("Agent runtime state", "medium", "runtime state, do not commit blindly")
    if clean_path.startswith("../workspace-jobzoom/") or clean_path.startswith("scripts/daily_run.py"):
        return ("JobZoom source", "high", "owner review before commit because daily scan behavior changes")
    if clean_path.startswith("reports/"):
        return ("Generated report", "low", "keep if useful, archive later if noisy")
    if clean_path.startswith("logs/") or clean_path.startswith("data/"):
        return ("Runtime state", "low", "expected job/runtime churn, usually do not commit")
    if clean_path.startswith("memory/") or clean_path == "MEMORY.md":
        return ("Memory/lessons", "medium", "intentional learning state, review then keep")
    if clean_path.startswith("intel/"):
        return ("Intelligence artifact", "low", "generated operational content")
    if clean_path.startswith("jobs-bank/"):
        return ("HR/job ledger", "medium", "ledger state, verify before committing")
    if clean_path.startswith("scripts/"):
        return ("Source script", "medium", "durable code change, review and test before commit")
    if clean_path.startswith("skills/"):
        return ("Skill instructions", "medium", "durable workflow change, review before commit")
    return ("Unclassified", "medium", "owner review needed")


def parse_status_line(line: str) -> tuple[str, str]:
    status = line[:2].strip() or "?"
    path = line[3:] if len(line) > 3 else line
    return status, path


def main() -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Workspace Hygiene Report - {}".format(now),
        "",
        "Scope: dirty-file classification only. No commits, reverts, deletes, cron changes, or runtime restarts.",
        "",
        "## Summary",
        "",
    ]

    total = 0
    lane_rows = []
    details = []

    for lane, repo in LANES.items():
        rows = git_status(repo)
        lane_rows.append((lane, len(rows)))
        total += len(rows)
        details.extend(["## {}".format(lane), ""])
        if not rows:
            details.extend(["No dirty files.", ""])
            continue
        details.append("| Status | Path | Owner bucket | Risk | Action |")
        details.append("|---|---|---|---|---|")
        for row in rows:
            status, path = parse_status_line(row)
            owner, risk, action = classify(path)
            details.append("| {} | `{}` | {} | {} | {} |".format(status, path, owner, risk, action))
        details.append("")

    lines.append("- Total dirty entries across visible lanes: {}".format(total))
    for lane, count in lane_rows:
        lines.append("- {}: {}".format(lane, count))
    lines.extend([
        "",
        "## Recommendation",
        "",
        "1. Treat runtime state and logs as non-commit noise unless a specific artifact must be preserved.",
        "2. Review durable source/script/skill changes as one controlled change set.",
        "3. Review core config and cron changes separately from source changes.",
        "4. Do not revert shared state blindly.",
        "5. Add cron scheduling for this report only after Ahmed approves cron mutation.",
        "",
    ])
    lines.extend(details)

    out_dir = WORKSPACE / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "workspace-hygiene-2026-05-16.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
