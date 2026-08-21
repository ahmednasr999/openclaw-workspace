import datetime as dt
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "ceo-nasr-operating-review.py"
SPEC = importlib.util.spec_from_file_location("ceo_nasr_operating_review", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class CeoNasrOperatingReviewTests(unittest.TestCase):
    def test_jobzoom_latest_accepts_current_lowercase_report_names(self):
        original = MODULE.JOBZOOM_REPORTS
        try:
            with tempfile.TemporaryDirectory() as temp:
                MODULE.JOBZOOM_REPORTS = Path(temp)
                current = MODULE.JOBZOOM_REPORTS / "jobzoom-20260817.pdf"
                legacy = MODULE.JOBZOOM_REPORTS / "JobZoom_Daily_2026-07-18.pdf"
                current.write_bytes(b"current")
                legacy.write_bytes(b"legacy")
                latest = MODULE.jobzoom_latest()
                self.assertIn(str(current), latest)
                self.assertIn(str(legacy), latest)
        finally:
            MODULE.JOBZOOM_REPORTS = original

    def test_report_includes_governed_orchestration_and_accounts(self):
        now = dt.datetime.fromisoformat("2026-08-17T10:00:00+03:00")
        report = MODULE.build_report(
            now,
            {"overall": "OK", "checks": []},
            {"HR": "healthy", "CTO": "healthy", "CMO": "healthy"},
            [],
            {
                "terminal_state": "success",
                "counts": {"KEEP": 2, "FIX": 1, "AUTOMATE": 1, "COMBINE-REVIEW": 0, "RETIRE-REVIEW": 0},
                "recommendations": ["FIX: example"],
                "mutations_performed": 0,
            },
            {"accounts": [{"employer": "Example", "priority": 90, "identity_status": "verified", "active_roles": 1}]},
        )
        self.assertIn("Persistent Account Experts", report)
        self.assertIn("Weekly Orchestration Audit", report)
        self.assertIn("Audit state: success", report)
        self.assertIn("Automatic mutations: 0", report)


if __name__ == "__main__":
    unittest.main()
