#!/usr/bin/env python3
"""Pure no-write guard probe for high-risk LinkedIn operation plans."""

from __future__ import annotations

import json
from typing import Any


def evaluate(plan: dict[str, Any]) -> dict[str, Any]:
    operation = str(plan.get("operation") or "")
    result = {
        "decision": "proceed",
        "external_action_allowed": True,
        "mark_applied": False,
        "set_date_applied": False,
        "retry_allowed": False,
        "reasons": [],
    }

    if operation in {"message", "connection"} and not plan.get("exact_pair_approved"):
        result.update(decision="hold", external_action_allowed=False)
        result["reasons"].append("exact text-target-action approval is missing")

    if plan.get("current_employer_contact") and not plan.get("contact_specific_exception"):
        result.update(decision="reject", external_action_allowed=False)
        result["reasons"].append("current-employer career outreach has no contact-specific exception")

    if operation == "application_upload":
        visible_proof = bool(plan.get("exact_file_visible") and plan.get("submitted_visible"))
        if not visible_proof:
            result.update(decision="hold", external_action_allowed=False)
            result["reasons"].append("exact visible file and submitted confirmation are required")
        result["mark_applied"] = visible_proof
        result["set_date_applied"] = visible_proof

    if plan.get("result_ambiguous"):
        resolved = bool(
            plan.get("live_thread_verified")
            and plan.get("exact_target_verified")
            and plan.get("exact_text_verified")
        )
        if not resolved:
            result.update(decision="hold", external_action_allowed=False)
            result["reasons"].append("ambiguous send lacks fresh exact live-thread proof")
        result["retry_allowed"] = resolved and bool(plan.get("retry_requested"))

    return result


def self_test() -> int:
    cases = [
        (
            {"operation": "message", "exact_pair_approved": False},
            lambda result: result["decision"] == "hold" and not result["external_action_allowed"],
        ),
        (
            {
                "operation": "connection",
                "exact_pair_approved": True,
                "current_employer_contact": True,
                "contact_specific_exception": False,
            },
            lambda result: result["decision"] == "reject" and not result["external_action_allowed"],
        ),
        (
            {
                "operation": "application_upload",
                "helper_ok": True,
                "exact_file_visible": False,
                "submitted_visible": False,
            },
            lambda result: result["decision"] == "hold"
            and not result["mark_applied"]
            and not result["set_date_applied"],
        ),
        (
            {
                "operation": "message",
                "exact_pair_approved": True,
                "result_ambiguous": True,
                "retry_requested": True,
                "live_thread_verified": False,
            },
            lambda result: result["decision"] == "hold" and not result["retry_allowed"],
        ),
        (
            {"operation": "message", "exact_pair_approved": True},
            lambda result: result["decision"] == "proceed" and result["external_action_allowed"],
        ),
    ]
    results = [evaluate(plan) for plan, _ in cases]
    passed = sum(int(check(result)) for result, (_, check) in zip(results, cases))
    print(json.dumps({"mode": "no_write", "passed": passed, "total": len(cases), "results": results}))
    print(f"{'PASS' if passed == len(cases) else 'FAIL'}: {passed}/{len(cases)} LinkedIn safety scenarios")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(self_test())
