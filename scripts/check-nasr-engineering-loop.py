#!/usr/bin/env python3
"""Fail-closed validator for NASR Engineering Loop evidence records."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SHA = re.compile(r"^[0-9a-f]{7,40}$")
WORK_STATES = {
    "intake",
    "specified",
    "building",
    "review",
    "ready_for_approval",
    "approved",
    "merged",
}
EXCEPTION_STATES = {"blocked", "approval_required", "exhausted"}
ALLOWED_TRANSITIONS = {
    "intake": {"specified"},
    "specified": {"building"},
    "building": {"review"},
    "review": {"building", "ready_for_approval"},
    "ready_for_approval": {"approved"},
    "approved": {"merged"},
    "merged": set(),
}
REQUIRED_MANDATES = {"correctness_regression", "security_operability"}


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value)
    return value is not None


def validate(record: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    if record.get("version") != 1:
        failures.append("version must equal 1")

    issue = _mapping(record.get("issue"))
    for field in ("id", "title"):
        if not _nonempty(issue.get(field)):
            failures.append(f"missing issue.{field}")
    if issue.get("source_untrusted") is not True:
        failures.append("issue.source_untrusted must be true")
    if issue.get("instructions_treated_as_data") is not True:
        failures.append("issue.instructions_treated_as_data must be true")

    state = record.get("state")
    all_states = WORK_STATES | EXCEPTION_STATES
    if state not in all_states:
        failures.append("invalid current state")

    history = record.get("history")
    if not isinstance(history, list) or not history:
        failures.append("history must be a non-empty list")
        history = []
    event_ids: set[str] = set()
    prior: str | None = None
    for index, raw_event in enumerate(history):
        event = _mapping(raw_event)
        event_id = event.get("event_id")
        event_state = event.get("state")
        if not _nonempty(event_id):
            failures.append(f"history[{index}] missing event_id")
        elif event_id in event_ids:
            failures.append(f"duplicate history event_id: {event_id}")
        else:
            event_ids.add(str(event_id))
        if event_state not in all_states:
            failures.append(f"history[{index}] invalid state")
        if not _nonempty(event.get("evidence")):
            failures.append(f"history[{index}] missing evidence")
        if prior is not None and event_state in all_states:
            if event_state == prior:
                failures.append(f"duplicate consecutive state: {event_state}")
            elif event_state in EXCEPTION_STATES:
                pass
            elif prior in EXCEPTION_STATES or event_state not in ALLOWED_TRANSITIONS.get(prior, set()):
                failures.append(f"invalid state transition: {prior} -> {event_state}")
        prior = event_state if event_state in all_states else prior
    if history and history[-1].get("state") != state:
        failures.append("current state must equal final history state")

    scope = _mapping(record.get("scope"))
    for field in ("repository", "branch", "isolation", "authority", "rollback"):
        if not _nonempty(scope.get(field)):
            failures.append(f"missing scope.{field}")
    if scope.get("isolation") not in {"branch", "worktree", "clone", "fixture"}:
        failures.append("scope.isolation must be branch, worktree, clone, or fixture")

    if state in EXCEPTION_STATES:
        stop = _mapping(record.get("stop"))
        for field in ("reason", "evidence", "next_action"):
            if not _nonempty(stop.get(field)):
                failures.append(f"missing stop.{field}")
        if not _nonempty(record.get("remaining_risk")):
            failures.append("missing remaining_risk")
        return failures
    if record.get("stop") is not None:
        failures.append("stop must be null outside an exception state")

    execution = _mapping(record.get("execution"))
    for field in ("builder_context", "base_sha", "tested_sha", "changed_files"):
        if not _nonempty(execution.get(field)):
            failures.append(f"missing execution.{field}")
    for field in ("base_sha", "tested_sha"):
        value = execution.get(field)
        if _nonempty(value) and not SHA.fullmatch(str(value)):
            failures.append(f"execution.{field} must be a 7-40 character lowercase git SHA")
    repairs = execution.get("repair_rounds")
    if not isinstance(repairs, int) or repairs < 0 or repairs > 2:
        failures.append("execution.repair_rounds must be an integer from 0 to 2")

    checks = _mapping(record.get("checks"))
    for name in ("tests", "security", "preview"):
        check = _mapping(checks.get(name))
        allowed = {"passed"} if name != "preview" else {"passed", "not_applicable"}
        if check.get("status") not in allowed:
            failures.append(f"checks.{name}.status must be {' or '.join(sorted(allowed))}")
        for field in ("command", "evidence"):
            if not _nonempty(check.get(field)):
                failures.append(f"missing checks.{name}.{field}")

    reviews = record.get("reviews")
    if not isinstance(reviews, list):
        failures.append("reviews must be a list")
        reviews = []
    by_mandate: dict[str, dict[str, Any]] = {}
    for index, raw_review in enumerate(reviews):
        review = _mapping(raw_review)
        mandate = review.get("mandate")
        if mandate in by_mandate:
            failures.append(f"duplicate review mandate: {mandate}")
        if isinstance(mandate, str):
            by_mandate[mandate] = review
        if review.get("disposition") != "accept":
            failures.append(f"reviews[{index}] disposition must be accept")
        if review.get("blocking_findings") != []:
            failures.append(f"reviews[{index}] has unresolved blocking findings")
        for field in ("context_id", "evidence"):
            if not _nonempty(review.get(field)):
                failures.append(f"reviews[{index}] missing {field}")
    if set(by_mandate) != REQUIRED_MANDATES:
        failures.append("reviews must contain exactly correctness_regression and security_operability")
    contexts = [review.get("context_id") for review in by_mandate.values()]
    if len(contexts) == 2 and (contexts[0] == contexts[1] or execution.get("builder_context") in contexts):
        failures.append("review contexts must be independent from builder and each other")

    approval = record.get("approval")
    if approval is not None:
        approval_map = _mapping(approval)
        if approval_map.get("method") != "explicit_text":
            failures.append("approval.method must be explicit_text; emoji-only approval is invalid")
        for field in ("approver", "message", "approved_sha", "timestamp"):
            if not _nonempty(approval_map.get(field)):
                failures.append(f"missing approval.{field}")
        if approval_map.get("approved_sha") != execution.get("tested_sha"):
            failures.append("approval.approved_sha must equal execution.tested_sha")
        message = str(approval_map.get("message", "")).strip()
        if message and not re.search(r"[A-Za-z0-9]", message):
            failures.append("approval.message cannot be emoji-only")

    if state in {"approved", "merged"} and approval is None:
        failures.append(f"state {state} requires explicit approval")

    merge = record.get("merge")
    if state == "merged":
        merge_map = _mapping(merge)
        for field in ("sha", "merged_from_sha", "evidence"):
            if not _nonempty(merge_map.get(field)):
                failures.append(f"missing merge.{field}")
        if merge_map.get("merged_from_sha") != execution.get("tested_sha"):
            failures.append("merge.merged_from_sha must equal execution.tested_sha")
        if _nonempty(merge_map.get("sha")) and not SHA.fullmatch(str(merge_map.get("sha"))):
            failures.append("merge.sha must be a 7-40 character lowercase git SHA")
    elif merge is not None:
        failures.append("merge must be null until state is merged")

    if not _nonempty(record.get("remaining_risk")):
        failures.append("missing remaining_risk")
    return failures


def result(record: dict[str, Any]) -> dict[str, Any]:
    failures = validate(record)
    return {
        "ok": not failures,
        "state": record.get("state"),
        "merge_eligible": not failures and record.get("state") == "approved",
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "failures": [f"cannot read record: {exc}"]}, indent=2))
        return 2
    outcome = result(record)
    print(json.dumps(outcome, indent=2))
    return 0 if outcome["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
