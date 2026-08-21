from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/linkedin-operation-safety-probe.py"
SPEC = importlib.util.spec_from_file_location("linkedin_operation_safety_probe", MODULE_PATH)
assert SPEC and SPEC.loader
probe = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = probe
SPEC.loader.exec_module(probe)


class LinkedInOperationSafetyProbeTests(unittest.TestCase):
    def test_helper_ok_does_not_mark_application_applied(self) -> None:
        result = probe.evaluate(
            {
                "operation": "application_upload",
                "helper_ok": True,
                "exact_file_visible": False,
                "submitted_visible": False,
            }
        )
        self.assertEqual("hold", result["decision"])
        self.assertFalse(result["mark_applied"])
        self.assertFalse(result["set_date_applied"])

    def test_ambiguous_message_cannot_retry_without_live_proof(self) -> None:
        result = probe.evaluate(
            {
                "operation": "message",
                "exact_pair_approved": True,
                "result_ambiguous": True,
                "retry_requested": True,
                "live_thread_verified": False,
            }
        )
        self.assertEqual("hold", result["decision"])
        self.assertFalse(result["retry_allowed"])


if __name__ == "__main__":
    unittest.main()
