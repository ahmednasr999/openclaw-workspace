#!/usr/bin/env python3
"""Pure no-write guard probe for governed job-search decisions."""

from __future__ import annotations

import json
from typing import Any


def evaluate_job(job: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    result = {
        "decision": "shortlist",
        "score_allowed": True,
        "cv_allowed": True,
        "apply_now": True,
        "linkedin_fetch_description": False,
        "reason": "eligible complete opportunity",
    }

    applied_match = bool(
        job.get("url") in set(state.get("applied_urls") or [])
        or job.get("job_id") in set(state.get("applied_job_ids") or [])
        or job.get("signature") in set(state.get("applied_signatures") or [])
        or job.get("jobs_applied") is True
    )
    if applied_match:
        result.update(
            decision="exclude_applied",
            score_allowed=False,
            cv_allowed=False,
            apply_now=False,
            reason="persistent applied ledger match before scoring",
        )
        return result

    restriction = str(job.get("nationality_restriction") or "").casefold()
    nationality = str(state.get("nationality") or "").casefold()
    if restriction and nationality not in restriction:
        result.update(
            decision="exclude_ineligible",
            score_allowed=False,
            cv_allowed=False,
            apply_now=False,
            reason="explicit nationality restriction mismatch before scoring",
        )
        return result

    if job.get("source") == "linkedin" and not job.get("description"):
        result.update(
            decision="fetch_description",
            score_allowed=False,
            cv_allowed=False,
            apply_now=False,
            linkedin_fetch_description=True,
            reason="full LinkedIn JD required before scoring",
        )
        return result

    if not job.get("salary_source"):
        result.update(
            decision="verify_compensation",
            apply_now=False,
            reason="compensation is not source-backed",
        )
    return result


def evaluate_scoring_health(health_status: int, batch_json_valid: bool) -> dict[str, Any]:
    return {
        "quota_exhausted": health_status == 429,
        "retain_batch_results": bool(batch_json_valid),
        "warning": health_status != 429 and health_status >= 400,
    }


def self_test() -> int:
    state = {
        "nationality": "egyptian",
        "applied_urls": {"https://example.invalid/applied"},
        "applied_job_ids": {"123"},
        "applied_signatures": {"vp transformation|example|dubai"},
    }
    cases = [
        evaluate_job({"url": "https://example.invalid/applied"}, state)["decision"] == "exclude_applied",
        evaluate_job({"job_id": "123"}, state)["decision"] == "exclude_applied",
        evaluate_job(
            {"source": "linkedin", "description": "", "job_id": "456"}, state
        )["linkedin_fetch_description"] is True,
        evaluate_job(
            {"nationality_restriction": "UAEN only", "description": "complete"}, state
        )["decision"] == "exclude_ineligible",
        evaluate_job(
            {"source": "indeed", "description": "complete", "salary_source": None}, state
        )["decision"] == "verify_compensation",
        evaluate_scoring_health(504, True)
        == {"quota_exhausted": False, "retain_batch_results": True, "warning": True},
        evaluate_scoring_health(429, False)["quota_exhausted"] is True,
    ]
    passed = sum(int(value) for value in cases)
    print(json.dumps({"mode": "no_write", "passed": passed, "total": len(cases)}))
    print(f"{'PASS' if passed == len(cases) else 'FAIL'}: {passed}/{len(cases)} job-search safety scenarios")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(self_test())
