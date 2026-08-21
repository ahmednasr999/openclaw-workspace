#!/usr/bin/env python3
"""Pure no-write guard probe for public CMO operations."""

from __future__ import annotations

import json
from typing import Any


def evaluate(plan: dict[str, Any]) -> dict[str, Any]:
    operation = str(plan.get("operation") or "")
    result = {
        "decision": "proceed",
        "external_action_allowed": True,
        "text_only_allowed": False,
        "retry_allowed": False,
        "mark_posted": False,
        "reschedule_allowed": False,
        "reasons": [],
    }

    if operation == "publish":
        matched_live_pair = bool(
            plan.get("live_row_verified")
            and plan.get("exact_pair_approved")
            and plan.get("caption_matches_live")
            and plan.get("visual_matches_live")
            and plan.get("author_date_verified")
            and plan.get("duplicate_clear")
        )
        if not matched_live_pair:
            result.update(decision="hold", external_action_allowed=False)
            result["reasons"].append("live approved text-visual pair is not fully verified")

        if plan.get("visual_expected") and not (
            plan.get("image_upload_ok") and plan.get("real_s3key")
        ):
            result.update(decision="hold", external_action_allowed=False)
            result["reasons"].append("expected visual lacks a successful upload and real s3key")

        if plan.get("result_ambiguous"):
            checked = bool(
                plan.get("live_feed_checked")
                and plan.get("local_success_log_checked")
                and plan.get("notion_state_checked")
            )
            live = bool(plan.get("live_post_verified") and plan.get("live_post_url"))
            if live:
                result.update(decision="already_live", external_action_allowed=False, mark_posted=True)
            elif checked and plan.get("verified_not_live") and matched_live_pair:
                result["retry_allowed"] = True
            else:
                result.update(decision="hold", external_action_allowed=False)
                result["reasons"].append("ambiguous publish lacks conclusive three-state proof")

    if operation in {"comment", "like", "comment_and_like"}:
        if not plan.get("exact_public_action_approved"):
            result.update(decision="hold", external_action_allowed=False)
            result["reasons"].append("exact content-target-action approval is missing")

    if operation == "reschedule":
        safe_slot = bool(
            plan.get("failure_confirmed")
            and plan.get("next_free_date_verified")
            and not plan.get("date_collision")
        )
        if safe_slot:
            result["reschedule_allowed"] = True
        else:
            result.update(decision="hold", external_action_allowed=False)
            result["reasons"].append("next free collision-free calendar date is not verified")

    return result


def self_test() -> int:
    cases = [
        (
            {"operation": "publish", "live_row_verified": False},
            lambda result: result["decision"] == "hold" and not result["external_action_allowed"],
        ),
        (
            {
                "operation": "publish",
                "live_row_verified": True,
                "exact_pair_approved": True,
                "caption_matches_live": True,
                "visual_matches_live": True,
                "author_date_verified": True,
                "duplicate_clear": True,
                "visual_expected": True,
                "image_upload_ok": False,
            },
            lambda result: result["decision"] == "hold" and not result["text_only_allowed"],
        ),
        (
            {
                "operation": "publish",
                "live_row_verified": True,
                "exact_pair_approved": True,
                "caption_matches_live": True,
                "visual_matches_live": True,
                "author_date_verified": True,
                "duplicate_clear": True,
                "result_ambiguous": True,
            },
            lambda result: result["decision"] == "hold" and not result["retry_allowed"],
        ),
        (
            {"operation": "reschedule", "failure_confirmed": True, "date_collision": True},
            lambda result: result["decision"] == "hold" and not result["reschedule_allowed"],
        ),
        (
            {"operation": "comment_and_like", "exact_public_action_approved": False},
            lambda result: result["decision"] == "hold" and not result["external_action_allowed"],
        ),
        (
            {
                "operation": "publish",
                "live_row_verified": True,
                "exact_pair_approved": True,
                "caption_matches_live": True,
                "visual_matches_live": True,
                "author_date_verified": True,
                "duplicate_clear": True,
                "visual_expected": True,
                "image_upload_ok": True,
                "real_s3key": "safe/test/image.png",
            },
            lambda result: result["decision"] == "proceed" and result["external_action_allowed"],
        ),
    ]
    results = [evaluate(plan) for plan, _ in cases]
    passed = sum(int(check(result)) for result, (_, check) in zip(results, cases))
    print(json.dumps({"mode": "no_write", "passed": passed, "total": len(cases), "results": results}))
    print(f"{'PASS' if passed == len(cases) else 'FAIL'}: {passed}/{len(cases)} CMO safety scenarios")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(self_test())
