from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/check-high-risk-skill-promotion.py"
SPEC = importlib.util.spec_from_file_location("high_risk_skill_promotion", MODULE_PATH)
assert SPEC and SPEC.loader
promotion = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = promotion
SPEC.loader.exec_module(promotion)


class HighRiskSkillPromotionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skills = [
            "gateway-runtime-safety",
            "content-publishing-safety",
            "executive-cv-builder",
            "linkedin",
        ]

    def test_unrelated_staged_file_checks_no_skills(self) -> None:
        self.assertEqual([], promotion.affected_skills({"memory/notes.md"}, self.skills))

    def test_changed_skill_checks_only_that_skill(self) -> None:
        self.assertEqual(
            ["executive-cv-builder"],
            promotion.affected_skills(
                {"skills/executive-cv-builder/instructions/pre-flight.md"}, self.skills
            ),
        )

    def test_gate_infrastructure_change_checks_full_portfolio(self) -> None:
        self.assertEqual(
            self.skills,
            promotion.affected_skills({"evals/skill-quality-gate/cases.json"}, self.skills),
        )


if __name__ == "__main__":
    unittest.main()
