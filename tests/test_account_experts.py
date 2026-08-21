import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "account-experts.py"
SPEC = importlib.util.spec_from_file_location("account_experts", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class AccountExpertsTests(unittest.TestCase):
    def dossier(self, slug="example"):
        return {
            "schema_version": 1,
            "slug": slug,
            "employer": "Example",
            "identity_status": "verified",
            "priority": 90,
            "last_refreshed_at": "2026-08-17T10:00:00+03:00",
            "roles": [{"title": "VP", "status": "watch", "score": 90, "url": "https://example.test/job"}],
            "sources": [{"title": "Official", "url": "https://example.test"}],
            "strategy": [],
            "decision_makers": [],
            "signals": [],
            "application_history": [],
            "hypotheses": [],
            "next_actions": [],
        }

    def test_rejects_ambiguous_identity_value(self):
        dossier = self.dossier()
        dossier["identity_status"] = "guessed"
        with self.assertRaises(MODULE.AccountExpertError):
            MODULE.validate(dossier)

    def test_refresh_writes_bounded_registry_and_reports(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            accounts = root / "data" / "accounts"
            accounts.mkdir(parents=True)
            (accounts / "example.json").write_text(json.dumps(self.dossier()), encoding="utf-8")
            reports = root / "reports"
            registry = MODULE.refresh_registry(root / "data", reports)
            self.assertEqual(1, len(registry["accounts"]))
            self.assertTrue(registry["guardrails"]["identity_claims_require_evidence"])
            report = (reports / "example.md").read_text()
            self.assertIn("not authority to contact anyone", report)


if __name__ == "__main__":
    unittest.main()
