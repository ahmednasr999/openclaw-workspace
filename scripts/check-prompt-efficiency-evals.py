#!/usr/bin/env python3
"""Validate the prompt-efficiency representative regression manifest."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "prompt-efficiency-evals.json"
REQUIRED_LANES = {"research", "content", "nasr", "hr", "jobzoom", "email", "runtime", "delivery"}
REQUIRED_CRITICAL_CASES = {"gateway-config-change", "model-preservation"}


def main() -> int:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cases = payload.get("cases") or []
    errors: list[str] = []
    ids = [case.get("id") for case in cases]
    lanes = {case.get("lane") for case in cases}
    risks = Counter(case.get("risk") for case in cases)

    if len(cases) != 20:
        errors.append(f"expected 20 cases, found {len(cases)}")
    if len(ids) != len(set(ids)):
        errors.append("case ids must be unique")
    missing_lanes = sorted(REQUIRED_LANES - lanes)
    if missing_lanes:
        errors.append(f"missing lanes: {', '.join(missing_lanes)}")
    if not REQUIRED_CRITICAL_CASES.issubset(set(ids)):
        errors.append("missing critical gateway/model preservation cases")
    if risks["low"] < 6:
        errors.append("need at least six low-risk pilot cases")
    if risks["high"] + risks["critical"] < 10:
        errors.append("need at least ten protected-workflow regression cases")
    for index, case in enumerate(cases, start=1):
        if not case.get("required"):
            errors.append(f"case {index} has no required behavior")
        if not case.get("forbidden"):
            errors.append(f"case {index} has no forbidden behavior")

    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print(f"OK {len(cases)} cases; lanes={len(lanes)}; low={risks['low']}; protected={risks['high'] + risks['critical']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
