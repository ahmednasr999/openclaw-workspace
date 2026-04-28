#!/usr/bin/env python3
"""Advisory audit for NASR Skillify Protocol coverage.

Read-only by default. Scans agent lane learning logs and skill directories for
obvious drift:
- high/critical pending learnings older than N days
- error entries without a suggested fix section
- skill directories missing SKILL.md
- known runtime patch learning without post-update checker reference
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

LANES = {
    "ceo": Path("/root/.openclaw/workspace"),
    "hr": Path("/root/.openclaw/workspace-hr"),
    "cto": Path("/root/.openclaw/workspace-cto"),
    "cmo": Path("/root/.openclaw/workspace-cmo"),
}

ENTRY_RE = re.compile(r"^## \[(?P<id>[A-Z]+-\d{8}-\d{3})\] (?P<category>.+)$", re.M)
FIELD_RE = re.compile(r"^\*\*(?P<field>Logged|Priority|Status|Area)\*\*:\s*(?P<value>.+)$", re.M)


@dataclass
class Finding:
    severity: str
    lane: str
    kind: str
    path: str
    summary: str
    detail: str = ""


def parse_dt(raw: str) -> datetime | None:
    raw = raw.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def split_entries(text: str) -> list[tuple[str, str, str]]:
    matches = list(ENTRY_RE.finditer(text))
    entries = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        entries.append((match.group("id"), match.group("category").strip(), text[start:end]))
    return entries


def fields(entry: str) -> dict[str, str]:
    return {m.group("field").lower(): m.group("value").strip() for m in FIELD_RE.finditer(entry)}


def first_summary(entry: str) -> str:
    marker = "### Summary"
    if marker not in entry:
        return "No summary section"
    tail = entry.split(marker, 1)[1].strip().splitlines()
    for line in tail:
        line = line.strip()
        if line and not line.startswith("###"):
            return line[:180]
    return "Empty summary section"


def audit_learnings(lane: str, root: Path, max_age_days: int) -> list[Finding]:
    findings: list[Finding] = []
    learn_dir = root / ".learnings"
    now = datetime.now(timezone.utc)
    if not learn_dir.exists():
        findings.append(Finding("medium", lane, "missing_learnings_dir", str(learn_dir), "Missing .learnings directory"))
        return findings

    for name in ("LEARNINGS.md", "ERRORS.md", "FEATURE_REQUESTS.md"):
        path = learn_dir / name
        if not path.exists():
            if name == "FEATURE_REQUESTS.md":
                continue
            findings.append(Finding("medium", lane, "missing_learning_file", str(path), f"Missing {name}"))
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for entry_id, category, entry in split_entries(text):
            f = fields(entry)
            priority = f.get("priority", "").lower()
            status = f.get("status", "").lower()
            logged = parse_dt(f.get("logged", "")) if f.get("logged") else None
            summary = first_summary(entry)

            if priority in {"high", "critical"} and status in {"pending", "open", ""} and logged:
                age = (now - logged.astimezone(timezone.utc)).days
                if age > max_age_days:
                    findings.append(
                        Finding(
                            "high" if priority == "critical" else "medium",
                            lane,
                            "stale_high_priority_learning",
                            str(path),
                            f"{entry_id} pending for {age} days: {summary}",
                            f"priority={priority} category={category}",
                        )
                    )

            if name == "ERRORS.md" and "### Suggested Fix" not in entry and "### Suggested Action" not in entry:
                findings.append(
                    Finding("medium", lane, "error_without_fix", str(path), f"{entry_id} has no suggested fix: {summary}")
                )

    return findings


def audit_skills(lane: str, root: Path) -> list[Finding]:
    findings: list[Finding] = []
    skills_dir = root / "skills"
    if not skills_dir.exists():
        return findings
    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        if not (child / "SKILL.md").exists():
            findings.append(Finding("medium", lane, "skill_missing_contract", str(child), "Skill directory missing SKILL.md"))
    return findings


def audit_runtime_patch_check() -> list[Finding]:
    findings: list[Finding] = []
    checker = Path("/root/.openclaw/workspace/scripts/check-openclaw-runtime-patches.py")
    learnings = Path("/root/.openclaw/workspace/.learnings/LEARNINGS.md")
    if learnings.exists() and "session-resume fallback prefix" in learnings.read_text(encoding="utf-8", errors="replace"):
        if not checker.exists():
            findings.append(Finding("high", "cto", "missing_runtime_patch_checker", str(checker), "Known runtime patch exists but checker is missing"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only NASR skillify drift audit")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--max-age-days", type=int, default=7, help="Pending high-priority learning age threshold")
    parser.add_argument("--fail-on", choices=["none", "high", "any"], default="none")
    args = parser.parse_args()

    findings: list[Finding] = []
    for lane, root in LANES.items():
        if not root.exists():
            findings.append(Finding("medium", lane, "missing_workspace", str(root), "Workspace not found"))
            continue
        findings.extend(audit_learnings(lane, root, args.max_age_days))
        findings.extend(audit_skills(lane, root))
    findings.extend(audit_runtime_patch_check())

    summary = {
        "total": len(findings),
        "high": sum(1 for f in findings if f.severity == "high"),
        "medium": sum(1 for f in findings if f.severity == "medium"),
        "low": sum(1 for f in findings if f.severity == "low"),
    }

    if args.json:
        print(json.dumps({"summary": summary, "findings": [asdict(f) for f in findings]}, indent=2, sort_keys=True))
    else:
        print("NASR Skillify Audit")
        print(f"Findings: total={summary['total']} high={summary['high']} medium={summary['medium']} low={summary['low']}")
        if not findings:
            print("No findings.")
        for f in findings:
            print(f"[{f.severity.upper()}] {f.lane} {f.kind}: {f.summary}")
            print(f"  path: {f.path}")
            if f.detail:
                print(f"  detail: {f.detail}")

    if args.fail_on == "high" and summary["high"]:
        return 1
    if args.fail_on == "any" and findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
