from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/job-search-operation-safety-probe.py"
SPEC = importlib.util.spec_from_file_location("job_search_operation_safety_probe", MODULE_PATH)
assert SPEC and SPEC.loader
probe = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = probe
SPEC.loader.exec_module(probe)


class JobSearchOperationSafetyProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = {
            "nationality": "egyptian",
            "applied_urls": {"https://example.invalid/applied"},
            "applied_job_ids": {"123"},
            "applied_signatures": {"vp transformation|example|dubai"},
        }

    def test_applied_role_is_excluded_before_scoring(self) -> None:
        result = probe.evaluate_job({"job_id": "123"}, self.state)
        self.assertEqual("exclude_applied", result["decision"])
        self.assertFalse(result["score_allowed"])
        self.assertFalse(result["cv_allowed"])

    def test_linkedin_without_description_requires_full_jd_fetch(self) -> None:
        result = probe.evaluate_job({"source": "linkedin", "description": ""}, self.state)
        self.assertEqual("fetch_description", result["decision"])
        self.assertTrue(result["linkedin_fetch_description"])
        self.assertFalse(result["score_allowed"])

    def test_nationality_restriction_excludes_before_scoring(self) -> None:
        result = probe.evaluate_job(
            {"nationality_restriction": "UAEN only", "description": "complete"}, self.state
        )
        self.assertEqual("exclude_ineligible", result["decision"])
        self.assertFalse(result["apply_now"])

    def test_non429_health_failure_is_not_quota_exhaustion(self) -> None:
        result = probe.evaluate_scoring_health(504, True)
        self.assertFalse(result["quota_exhausted"])
        self.assertTrue(result["retain_batch_results"])
        self.assertTrue(result["warning"])

    def test_missing_salary_is_verify_compensation(self) -> None:
        result = probe.evaluate_job(
            {"source": "indeed", "description": "complete", "salary_source": None}, self.state
        )
        self.assertEqual("verify_compensation", result["decision"])
        self.assertFalse(result["apply_now"])


if __name__ == "__main__":
    unittest.main()
