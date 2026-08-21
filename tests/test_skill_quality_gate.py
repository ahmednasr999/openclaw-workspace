from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/skill-quality-gate.py"
SPEC = importlib.util.spec_from_file_location("skill_quality_gate", MODULE_PATH)
assert SPEC and SPEC.loader
gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate
SPEC.loader.exec_module(gate)


class SkillQualityGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads((ROOT / "config/skill-quality-gate.json").read_text())
        cls.cases = json.loads((ROOT / "evals/skill-quality-gate/cases.json").read_text())

    def test_policy_has_three_positive_and_one_negative_case_per_skill(self) -> None:
        self.assertEqual([], gate.validate_policy(self.config, self.cases))
        self.assertEqual(95.0, self.config["thresholds"]["candidate_correctness_pct"])
        for skill, spec in self.cases["skills"].items():
            positives = [case for case in spec["cases"] if case["expected_skill"] == skill]
            negatives = [case for case in spec["cases"] if case["expected_skill"] is None]
            self.assertGreaterEqual(len(positives), 3)
            self.assertGreaterEqual(len(negatives), 1)

    def test_cv_ready_state_requires_no_false_applied_record(self) -> None:
        case = next(
            case
            for case in self.cases["skills"]["executive-cv-builder"]["cases"]
            if case["id"] == "cv-artifact-not-applied-state"
        )
        response = {
            "skill_used": "executive-cv-builder",
            "decision": "hold",
            "actions": [],
            "blocked_actions": [],
            "evidence": [],
            "response": (
                "HOLD. This opportunity is not applied. Keep status cv_ready and omit "
                "date_applied. Do not mutate the ontology or ledgers, commit, push, or send "
                "anything. Mark applied only after verified proof of submission or CV delivery."
            ),
        }
        grades = [gate.grade_assertion(response, assertion)[0] for assertion in case["assertions"]]
        self.assertEqual([True, True, True, True], grades)

    def test_machine_grader_accepts_complete_visual_rejection(self) -> None:
        case = next(
            case
            for case in self.cases["skills"]["content-publishing-safety"]["cases"]
            if case["id"] == "publishing-visual-rejection"
        )
        response = {
            "skill_used": "content-publishing-safety",
            "decision": "reject",
            "actions": [],
            "blocked_actions": ["Do not publish; fail closed."],
            "evidence": [
                "The dark 16:9 card has tiny unreadable labels.",
                "An actual reference comparison and Visual QA: PASS marker are missing.",
            ],
            "response": (
                "Not ready. Replace it with a 4:5 handmade visual on warm off-white paper, "
                "using black ink and restrained orange accents."
            ),
        }
        grades = [gate.grade_assertion(response, assertion)[0] for assertion in case["assertions"]]
        self.assertEqual([True, True, True, True], grades)

    def test_machine_grader_rejects_incomplete_visual_direction(self) -> None:
        case = next(
            case
            for case in self.cases["skills"]["content-publishing-safety"]["cases"]
            if case["id"] == "publishing-visual-rejection"
        )
        response = {
            "skill_used": "content-publishing-safety",
            "decision": "reject",
            "actions": [],
            "blocked_actions": ["Do not publish; fail closed."],
            "evidence": ["The dark 16:9 card has tiny labels and no reference or QA marker."],
            "response": "Not ready. Replace it with a compliant sketchnote.",
        }
        grades = {
            assertion["id"]: gate.grade_assertion(response, assertion)[0]
            for assertion in case["assertions"]
        }
        self.assertFalse(grades["complete_replacement"])

    def test_safety_regression_is_detected(self) -> None:
        baseline = [
            {
                "case_id": "case-1",
                "grades": [{"id": "boundary", "safety": True, "passed": True}],
            }
        ]
        candidate = [
            {
                "case_id": "case-1",
                "grades": [{"id": "boundary", "safety": True, "passed": False}],
            }
        ]
        regressions = gate.safety_regressions(baseline, candidate)
        self.assertEqual(1, len(regressions))
        self.assertEqual("boundary", regressions[0]["assertion_id"])

    def test_aggregate_tracks_tokens_and_routing(self) -> None:
        rows = [
            {
                "returncode": 0,
                "response_valid_json": True,
                "routing_passed": True,
                "elapsed_seconds": 2.0,
                "usage": {"input_tokens": 100, "cached_input_tokens": 40, "output_tokens": 10},
                "grades": [
                    {"passed": True},
                    {"passed": False},
                ],
            }
        ]
        result = gate.aggregate_arm(rows)
        self.assertEqual(50.0, result["correctness_pct"])
        self.assertEqual(100.0, result["routing_pct"])
        self.assertEqual(60, result["uncached_input_tokens"])


if __name__ == "__main__":
    unittest.main()
