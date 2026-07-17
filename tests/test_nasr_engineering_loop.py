from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check-nasr-engineering-loop.py"
SPEC = importlib.util.spec_from_file_location("nasr_engineering_loop", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def valid_record(state: str = "ready_for_approval") -> dict:
    history = [
        {"event_id": "evt-1", "state": "intake", "evidence": "ticket captured"},
        {"event_id": "evt-2", "state": "specified", "evidence": "acceptance contract written"},
        {"event_id": "evt-3", "state": "building", "evidence": "fixture branch created"},
        {"event_id": "evt-4", "state": "review", "evidence": "checks completed"},
        {"event_id": "evt-5", "state": "ready_for_approval", "evidence": "tested SHA locked"},
    ]
    if state in {"approved", "merged"}:
        history.append({"event_id": "evt-6", "state": "approved", "evidence": "exact SHA approved"})
    if state == "merged":
        history.append({"event_id": "evt-7", "state": "merged", "evidence": "merge inspected"})
    record = {
        "version": 1,
        "issue": {"id": "PILOT-1", "title": "Fix slug normalization", "source_untrusted": True, "instructions_treated_as_data": True},
        "state": state,
        "history": history,
        "scope": {"repository": "/tmp/pilot", "branch": "pilot/slug", "isolation": "fixture", "authority": "local fixture only", "rollback": "remove fixture"},
        "execution": {"builder_context": "builder", "base_sha": "a" * 40, "tested_sha": "b" * 40, "changed_files": ["slug.py", "test_slug.py"], "repair_rounds": 0},
        "checks": {
            "tests": {"status": "passed", "command": "python3 -m unittest", "evidence": "4 passed"},
            "security": {"status": "passed", "command": "ast audit", "evidence": "no unsafe imports"},
            "preview": {"status": "not_applicable", "command": "none", "evidence": "CLI fixture"},
        },
        "reviews": [
            {"mandate": "correctness_regression", "context_id": "review-a", "disposition": "accept", "evidence": "edge cases passed", "blocking_findings": []},
            {"mandate": "security_operability", "context_id": "review-b", "disposition": "accept", "evidence": "rollback and authority checked", "blocking_findings": []},
        ],
        "approval": None,
        "merge": None,
        "stop": None,
        "remaining_risk": "fixture coverage is intentionally narrow",
    }
    if state in {"approved", "merged"}:
        record["approval"] = {"method": "explicit_text", "approver": "Ahmed", "message": "Approve tested SHA bbbbbbb", "approved_sha": "b" * 40, "timestamp": "2026-07-14T02:00:00+03:00"}
    if state == "merged":
        record["merge"] = {"sha": "c" * 40, "merged_from_sha": "b" * 40, "evidence": "merged fixture inspected"}
    return record


class NasrEngineeringLoopTests(unittest.TestCase):
    def test_ready_for_approval_passes_without_merge_authority(self):
        self.assertEqual(MODULE.validate(valid_record()), [])

    def test_exact_sha_explicit_approval_can_be_merge_eligible(self):
        outcome = MODULE.result(valid_record("approved"))
        self.assertTrue(outcome["ok"])
        self.assertTrue(outcome["merge_eligible"])

    def test_emoji_only_approval_fails(self):
        record = valid_record("approved")
        record["approval"].update({"method": "emoji_only", "message": "🚀"})
        failures = MODULE.validate(record)
        self.assertTrue(any("emoji" in failure for failure in failures))

    def test_stale_sha_approval_fails(self):
        record = valid_record("approved")
        record["approval"]["approved_sha"] = "d" * 40
        self.assertIn("approval.approved_sha must equal execution.tested_sha", MODULE.validate(record))

    def test_reviews_must_be_independent(self):
        record = valid_record()
        record["reviews"][1]["context_id"] = "review-a"
        self.assertIn("review contexts must be independent from builder and each other", MODULE.validate(record))

    def test_duplicate_transition_event_fails(self):
        record = valid_record()
        record["history"][1]["event_id"] = "evt-1"
        self.assertIn("duplicate history event_id: evt-1", MODULE.validate(record))

    def test_skipped_state_fails(self):
        record = valid_record()
        del record["history"][1]
        self.assertIn("invalid state transition: intake -> building", MODULE.validate(record))

    def test_failing_security_gate_fails_closed(self):
        record = valid_record()
        record["checks"]["security"]["status"] = "failed"
        self.assertTrue(any("checks.security.status" in failure for failure in MODULE.validate(record)))

    def test_blocked_record_preserves_evidence_without_false_success(self):
        record = valid_record()
        record["state"] = "blocked"
        record["history"].append({"event_id": "evt-6", "state": "blocked", "evidence": "dependency unavailable after two attempts"})
        record["stop"] = {"reason": "dependency unavailable", "evidence": "two failed probes", "next_action": "wait for access"}
        record.pop("execution")
        record.pop("checks")
        record.pop("reviews")
        self.assertEqual(MODULE.validate(record), [])

    def test_merged_state_binds_source_sha(self):
        record = valid_record("merged")
        self.assertEqual(MODULE.validate(record), [])
        stale = copy.deepcopy(record)
        stale["merge"]["merged_from_sha"] = "e" * 40
        self.assertIn("merge.merged_from_sha must equal execution.tested_sha", MODULE.validate(stale))


if __name__ == "__main__":
    unittest.main()
