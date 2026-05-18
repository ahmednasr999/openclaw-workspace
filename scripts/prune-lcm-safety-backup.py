#!/usr/bin/env python3
"""Prune a specific LCM DB safety backup after a clean newer nightly report."""

import json
import re
import subprocess
import sys
from pathlib import Path


TARGET = Path("/root/.openclaw/backups/lcm.db.pre-conversation-id-compact-20260518T0922.sqlite")
REPORT_DIR = Path("/root/.openclaw/workspace/reports")


def emit(status: str, **extra: object) -> None:
    payload = {"status": status, "target": str(TARGET), **extra}
    print(json.dumps(payload, sort_keys=True))


def latest_report() -> Path | None:
    reports = sorted(REPORT_DIR.glob("lcm-nightly-*.md"), key=lambda path: path.stat().st_mtime, reverse=True)
    return reports[0] if reports else None


def report_verdict(path: Path) -> str | None:
    match = re.search(r"^Verdict:\s*([A-Z]+)\s*$", path.read_text(errors="replace"), re.MULTILINE)
    return match.group(1) if match else None


def main() -> int:
    if not TARGET.exists():
        emit("ALREADY_ABSENT")
        return 0

    report = latest_report()
    if report is None:
        emit("WAIT", reason="no_lcm_nightly_report")
        return 0

    target_mtime = TARGET.stat().st_mtime
    report_mtime = report.stat().st_mtime
    verdict = report_verdict(report)

    if report_mtime <= target_mtime:
        emit("WAIT", reason="latest_report_not_newer", report=str(report), verdict=verdict)
        return 0

    if verdict != "OK":
        emit("WAIT", reason="latest_report_not_ok", report=str(report), verdict=verdict)
        return 0

    size = TARGET.stat().st_size
    TARGET.unlink()
    if TARGET.exists():
        emit("ERROR", reason="delete_failed", report=str(report), verdict=verdict)
        return 1

    df = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, check=False)
    emit(
        "PRUNED",
        bytes_removed=size,
        report=str(report),
        verdict=verdict,
        df=df.stdout.strip(),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
