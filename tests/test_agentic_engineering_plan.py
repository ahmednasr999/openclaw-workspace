from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check-agentic-engineering-plan.py"
SPEC = importlib.util.spec_from_file_location("agentic_plan", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def valid_plan() -> str:
    return """# Agentic Engineering Plan
## Plan Metadata
- Status: ready
- Owner: main
- Planned at: commit `abcdef1` on `2026-07-11`
- Depends on: none
> **Drift check:** `git diff --stat abcdef1..HEAD -- app.py tests/test_app.py`
## Objective
- Target outcome: Reject invalid requests.
- User-visible success condition: Invalid requests return HTTP 400.
## Evidence And Current State
- Source anchors: `app.py:42` accepts the invalid request.
## Scope
- In scope: request validation
- Do not touch: authentication
## Authority And Safety
- Permission profile: local-write
- Approval boundary: stop before deployment
- Rollback path: revert the focused patch
## Ordered Implementation Steps
### Step 1: Validate requests
- Verify command/check: `python3 -m unittest tests.test_app`
- Expected result: all tests pass
## Test Plan
- Existing tests to run: request tests
## Stop Conditions
- Stop on scope expansion.
## Done Criteria
- [ ] Tests pass.
## Review Handoff
- Reviewer focus: validation boundary
"""


class AgenticEngineeringPlanTests(unittest.TestCase):
    def test_complete_plan_passes(self):
        self.assertEqual(MODULE.validate(valid_plan()), [])

    def test_missing_file_line_evidence_fails(self):
        failures = MODULE.validate(valid_plan().replace("`app.py:42`", "app.py"))
        self.assertIn("Source anchors must include file:line evidence", failures)

    def test_missing_drift_check_fails(self):
        failures = MODULE.validate(valid_plan().replace("> **Drift check:** `git diff --stat abcdef1..HEAD -- app.py tests/test_app.py`\n", ""))
        self.assertIn("missing drift check", failures)

    def test_each_step_requires_expected_result(self):
        failures = MODULE.validate(valid_plan().replace("- Expected result: all tests pass\n", ""))
        self.assertIn("each step requires Expected result", failures)

    def test_possible_secret_fails(self):
        failures = MODULE.validate(valid_plan() + "\n- token: abcdefghijklmnopqrstuvwxyz123456\n")
        self.assertIn("possible secret value embedded in plan", failures)


if __name__ == "__main__":
    unittest.main()
