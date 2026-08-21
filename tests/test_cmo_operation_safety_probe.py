from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/cmo-operation-safety-probe.py"
SPEC = importlib.util.spec_from_file_location("cmo_operation_safety_probe", MODULE_PATH)
assert SPEC and SPEC.loader
probe = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = probe
SPEC.loader.exec_module(probe)


class CmoOperationSafetyProbeTests(unittest.TestCase):
    def test_expected_visual_never_falls_back_to_text_only(self) -> None:
        result = probe.evaluate(
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
            }
        )
        self.assertEqual("hold", result["decision"])
        self.assertFalse(result["text_only_allowed"])
        self.assertFalse(result["external_action_allowed"])

    def test_ambiguous_publish_cannot_retry_without_three_state_proof(self) -> None:
        result = probe.evaluate(
            {
                "operation": "publish",
                "live_row_verified": True,
                "exact_pair_approved": True,
                "caption_matches_live": True,
                "visual_matches_live": True,
                "author_date_verified": True,
                "duplicate_clear": True,
                "result_ambiguous": True,
            }
        )
        self.assertEqual("hold", result["decision"])
        self.assertFalse(result["retry_allowed"])

    def test_reschedule_rejects_occupied_date(self) -> None:
        result = probe.evaluate(
            {"operation": "reschedule", "failure_confirmed": True, "date_collision": True}
        )
        self.assertEqual("hold", result["decision"])
        self.assertFalse(result["reschedule_allowed"])


if __name__ == "__main__":
    unittest.main()
