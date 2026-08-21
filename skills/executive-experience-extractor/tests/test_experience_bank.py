from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "experience_bank.py"
SPEC = importlib.util.spec_from_file_location("experience_bank", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def valid_bank() -> dict:
    return {
        "schema_version": "1.0",
        "subject": "Ahmed Nasr",
        "last_updated": "2026-08-18",
        "source_of_truth": ["memory/master-cv-data.md"],
        "records": [
            {
                "id": "exp-2014-network-pmo",
                "title": "Built a multi-country PMO",
                "organization": "Network International",
                "role": "PMO Section Head (Project Management Department Manager)",
                "period": "Sep 2014 - Jun 2017",
                "status": "verified",
                "domains": ["FinTech"],
                "competencies": ["Enterprise PMO"],
                "source_evidence": [
                    {
                        "id": "src-1",
                        "source": "memory/master-cv-data.md",
                        "locator": "Network International",
                        "claim": "Built and led enterprise PMO.",
                    }
                ],
                "situation": "A multi-country payments portfolio needed consistent governance.",
                "responsibility": "Ahmed led the PMO.",
                "actions": ["Built the PMO."],
                "outcomes": [
                    {"statement": "The portfolio operated across eight countries.", "attribution": "direct", "source_refs": ["src-1"]}
                ],
                "scope_metrics": [
                    {"label": "Countries", "value": "8", "verified": True, "source_refs": ["src-1"]}
                ],
                "story_angles": ["Governance at scale"],
                "questions_to_complete": [],
                "disclosure": {
                    "classification": "private",
                    "external_reuse_requires_approval": True,
                    "constraints": [],
                },
            }
        ],
    }


class ExperienceBankTests(unittest.TestCase):
    def test_valid_bank_passes(self) -> None:
        self.assertEqual(MODULE.validate_bank(valid_bank()), [])

    def test_unknown_outcome_source_fails(self) -> None:
        bank = valid_bank()
        bank["records"][0]["outcomes"][0]["source_refs"] = ["missing"]
        errors = MODULE.validate_bank(bank)
        self.assertTrue(any("unknown source refs" in error for error in errors))

    def test_duplicate_record_id_fails(self) -> None:
        bank = valid_bank()
        bank["records"].append(json.loads(json.dumps(bank["records"][0])))
        errors = MODULE.validate_bank(bank)
        self.assertTrue(any("duplicate record id" in error for error in errors))

    def test_attribution_is_required(self) -> None:
        bank = valid_bank()
        bank["records"][0]["outcomes"][0]["attribution"] = "solo"
        errors = MODULE.validate_bank(bank)
        self.assertTrue(any("attribution must be one of" in error for error in errors))

    def test_render_marks_private_bank(self) -> None:
        rendered = MODULE.render_markdown(valid_bank())
        self.assertIn("Private working evidence", rendered)
        self.assertIn("[direct]", rendered)


if __name__ == "__main__":
    unittest.main()

