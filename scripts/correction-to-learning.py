#!/usr/bin/env python3
"""Capture a user correction into the governed learning loop without raw-session mining."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path("/root/.openclaw/workspace")
LEARNING_SCRIPT = ROOT / "skills" / "governed-learning-loop" / "scripts" / "learning_loop.py"
DATA_DIR = ROOT / "data" / "learning-loop"
REPORT = ROOT / "reports" / "learning-loop" / "latest.md"
INTAKE_DIR = ROOT / "data" / "correction-intake"
LESSONS_FILE = ROOT / ".learnings" / "LEARNINGS.md"
MAX_OBSERVATIONS_PER_PATTERN = 4
TARGET_TYPES = {"rule", "skill-update", "new-skill", "script", "test", "solution"}
SECRET_PATTERNS = (
    re.compile(r"(?i)\b(?:api[_-]?key|token|password|secret)\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/-]{12,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b[A-Za-z0-9_+/=-]{40,}\b"),
)


class CorrectionIntakeError(ValueError):
    pass


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def safe_text(label: str, value: str, minimum: int = 8, maximum: int = 1000) -> str:
    text = " ".join(value.split()).strip()
    if not minimum <= len(text) <= maximum:
        raise CorrectionIntakeError(f"{label} must be {minimum}-{maximum} characters")
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        raise CorrectionIntakeError(f"{label} looks like a secret or credential")
    return text


def validate_pattern_key(value: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9-]*(?:\.[a-z0-9-]+)+", value):
        raise CorrectionIntakeError("pattern-key must be a stable dotted lowercase key")
    return value


def load_registry(data_dir: Path) -> dict[str, Any]:
    path = data_dir / "registry.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"observations": []}


def pattern_count(data_dir: Path, pattern_key: str) -> int:
    return sum(
        item.get("pattern_key") == pattern_key
        for item in load_registry(data_dir).get("observations", [])
    )


def record_aggregate(intake_dir: Path, pattern_key: str, run_id: str, summary: str, occurred_at: str) -> Path:
    aggregate_dir = intake_dir / "aggregates"
    path = aggregate_dir / f"{pattern_key.replace('.', '-')}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"pattern_key": pattern_key, "occurrence_count": 0, "recent_run_ids": []}
    data["occurrence_count"] = int(data.get("occurrence_count") or 0) + 1
    data["latest_at"] = occurred_at
    data["latest_summary"] = summary
    recent = [item for item in data.get("recent_run_ids", []) if item != run_id]
    data["recent_run_ids"] = ([run_id] + recent)[:5]
    atomic_write(path, json.dumps(data, indent=2, sort_keys=True) + "\n")
    return path


def append_lesson(path: Path, record: dict[str, Any]) -> None:
    marker = f"Correction-Run: {record['run_id']}"
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Learnings Log\n"
    if marker in existing:
        return
    entry = f"""

## {record['occurred_at'][:10]} - Governed correction: {record['pattern_key']}

- Summary: {record['summary']}
- Do differently: {record['verification']}
- Target type: {record['target_type']}
- {marker}
- Status: observation only; no active rule or skill changed.
"""
    atomic_write(path, existing.rstrip() + entry + "\n")


def invoke_learning_loop(args: argparse.Namespace, evidence_path: Path) -> dict[str, Any]:
    command = [
        "python3",
        str(args.learning_script),
        "--data-dir",
        str(args.data_dir),
        "--report",
        str(args.report),
        "capture",
        "--pattern-key",
        args.pattern_key,
        "--summary",
        args.summary,
        "--run-id",
        args.run_id,
        "--source",
        str(evidence_path),
        "--evidence",
        str(evidence_path),
        "--verification",
        args.verification,
        "--target-type",
        args.target_type,
        "--occurred-at",
        args.occurred_at,
    ]
    captured = subprocess.run(command, text=True, capture_output=True, timeout=30, check=False)
    if captured.returncode != 0:
        raise CorrectionIntakeError(f"learning capture failed: {(captured.stdout or captured.stderr).strip()}")
    built = subprocess.run(
        [
            "python3",
            str(args.learning_script),
            "--data-dir",
            str(args.data_dir),
            "--report",
            str(args.report),
            "build",
        ],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if built.returncode != 0:
        raise CorrectionIntakeError(f"learning build failed: {(built.stdout or built.stderr).strip()}")
    return {"capture": json.loads(captured.stdout), "build": json.loads(built.stdout)}


def capture_correction(args: argparse.Namespace) -> dict[str, Any]:
    args.pattern_key = validate_pattern_key(args.pattern_key)
    args.summary = safe_text("summary", args.summary, 12, 500)
    args.verification = safe_text("verification", args.verification, 12, 800)
    args.run_id = safe_text("run-id", args.run_id, 4, 160)
    if args.target_type not in TARGET_TYPES:
        raise CorrectionIntakeError("invalid target-type")
    args.occurred_at = args.occurred_at or dt.datetime.now().astimezone().isoformat()
    try:
        dt.datetime.fromisoformat(args.occurred_at)
    except ValueError as exc:
        raise CorrectionIntakeError("occurred-at must be ISO-8601") from exc

    count = pattern_count(args.data_dir, args.pattern_key)
    if count >= MAX_OBSERVATIONS_PER_PATTERN:
        aggregate = record_aggregate(args.intake_dir, args.pattern_key, args.run_id, args.summary, args.occurred_at)
        return {
            "status": "aggregated",
            "pattern_key": args.pattern_key,
            "observation_cap": MAX_OBSERVATIONS_PER_PATTERN,
            "aggregate": str(aggregate),
            "active_target_changed": False,
        }

    digest = hashlib.sha256(f"{args.pattern_key}|{args.run_id}".encode()).hexdigest()[:16]
    evidence_path = args.intake_dir / "observations" / f"correction-{digest}.json"
    record = {
        "schema_version": 1,
        "kind": "user-correction",
        "pattern_key": args.pattern_key,
        "summary": args.summary,
        "verification": args.verification,
        "run_id": args.run_id,
        "target_type": args.target_type,
        "occurred_at": args.occurred_at,
        "raw_session_mined": False,
        "active_target_changed": False,
    }
    atomic_write(evidence_path, json.dumps(record, indent=2, sort_keys=True) + "\n")
    append_lesson(args.lessons_file, record)
    learning = invoke_learning_loop(args, evidence_path)
    return {
        "status": "captured",
        "pattern_key": args.pattern_key,
        "evidence": str(evidence_path),
        "learning": learning,
        "active_target_changed": False,
        "automatic_deployment": False,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--data-dir", type=Path, default=DATA_DIR)
    root.add_argument("--report", type=Path, default=REPORT)
    root.add_argument("--intake-dir", type=Path, default=INTAKE_DIR)
    root.add_argument("--lessons-file", type=Path, default=LESSONS_FILE)
    root.add_argument("--learning-script", type=Path, default=LEARNING_SCRIPT)
    root.add_argument("--pattern-key", required=True)
    root.add_argument("--summary", required=True)
    root.add_argument("--run-id", required=True)
    root.add_argument("--verification", required=True)
    root.add_argument("--target-type", choices=sorted(TARGET_TYPES), required=True)
    root.add_argument("--occurred-at")
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        result = capture_correction(args)
    except CorrectionIntakeError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
