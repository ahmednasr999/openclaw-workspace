from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check-high-risk-engineering-record.py"
SPEC = importlib.util.spec_from_file_location("high_risk_record", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def record(review_b: str = "Rejected unsafe retry; no change required.") -> str:
    return """# Record
- Before evidence: failing test reproduced
- Changed files: app.py and test_app.py
- Focused tests: 8 passed
- Original reproduction after fix: passes
- Review A findings and disposition: accepted missing boundary test; repaired
- Review B findings and disposition: %s
- Repairs and retest evidence: boundary test added; 9 passed
- Actual outcome inspected: API response inspected
- Rollback evidence: patch backup recorded
- Remaining risk: low
- Status: success
""" % review_b


class HighRiskRecordTests(unittest.TestCase):
    def test_complete_record_passes(self):
        self.assertEqual(MODULE.validate(record()), [])

    def test_missing_second_review_fails(self):
        failures = MODULE.validate(record().replace("- Review B findings and disposition: Rejected unsafe retry; no change required.\n", ""))
        self.assertIn("missing: Review B findings and disposition", failures)

    def test_identical_reviews_fail(self):
        failures = MODULE.validate(record("accepted missing boundary test; repaired"))
        self.assertIn("reviews are identical", failures)

    def test_missing_terminal_status_fails(self):
        failures = MODULE.validate(record().replace("- Status: success\n", ""))
        self.assertIn("missing successful terminal Status", failures)


if __name__ == "__main__":
    unittest.main()
