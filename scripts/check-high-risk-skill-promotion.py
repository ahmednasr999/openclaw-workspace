#!/usr/bin/env python3
"""Fail closed when promoted high-risk skill trees lack matching attestations."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config/skill-quality-gate.json"
GATE = ROOT / "scripts/skill-quality-gate.py"
INFRA_PATHS = {
    "config/skill-quality-gate.json",
    "evals/skill-quality-gate/cases.json",
    "evals/skill-quality-gate/response-schema.json",
    "scripts/skill-quality-gate.py",
    "docs/standards/high-risk-skill-quality-gate.md",
}


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, check=False)


def load_skills() -> list[str]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    skills = config.get("high_risk_skills") or []
    if not isinstance(skills, list) or not all(isinstance(item, str) and item for item in skills):
        raise ValueError("high_risk_skills must be a non-empty string list")
    return skills


def staged_paths() -> set[str]:
    result = run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "could not inspect staged paths")
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def affected_skills(paths: set[str], skills: list[str]) -> list[str]:
    if paths & INFRA_PATHS:
        return skills
    return [skill for skill in skills if any(path.startswith(f"skills/{skill}/") for path in paths)]


def gate_command(*args: str) -> tuple[bool, str]:
    result = run([sys.executable, str(GATE), *args])
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    return result.returncode == 0, output


def check_portfolio(targets: list[str]) -> list[str]:
    errors: list[str] = []
    for command in (("validate",), ("verify-baseline",)):
        ok, output = gate_command(*command)
        if output:
            print(output)
        if not ok:
            errors.append(f"{' '.join(command)} failed")
    for skill in targets:
        ok, output = gate_command("check-promotion", "--skill", skill)
        if output:
            print(output)
        if not ok:
            errors.append(f"promotion attestation failed for {skill}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true", help="Check staged high-risk skill changes")
    mode.add_argument("--all", action="store_true", help="Check the full promoted high-risk portfolio")
    args = parser.parse_args()

    try:
        skills = load_skills()
        paths = staged_paths() if args.staged else set()
        targets = skills if args.all else affected_skills(paths, skills)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if not targets:
        print("PASS: no staged high-risk skill or gate-infrastructure changes")
        return 0

    errors = check_portfolio(targets)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"PASS: high-risk promotion portfolio verified ({', '.join(targets)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
