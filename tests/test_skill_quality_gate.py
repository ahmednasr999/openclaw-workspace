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
        self.assertIn("linkedin", self.config["high_risk_skills"])
        self.assertIn("cmo-agent", self.config["high_risk_skills"])
        self.assertIn("job-search-mcp", self.config["high_risk_skills"])
        for skill, spec in self.cases["skills"].items():
            positives = [case for case in spec["cases"] if case["expected_skill"] == skill]
            negatives = [case for case in spec["cases"] if case["expected_skill"] is None]
            self.assertGreaterEqual(len(positives), 3)
            self.assertGreaterEqual(len(negatives), 1)

    def test_job_search_cases_cover_governed_discovery_boundaries(self) -> None:
        cases = {
            case["id"]: case
            for case in self.cases["skills"]["job-search-mcp"]["cases"]
        }
        self.assertIn("job-search-applied-role-resurfacing", cases)
        self.assertIn("job-search-linkedin-incomplete-description", cases)
        self.assertIn("job-search-nationality-restriction", cases)
        self.assertIn("job-search-non429-health-check", cases)
        self.assertIn("job-search-unsupported-salary", cases)

    def test_job_search_grader_accepts_safe_synonyms(self) -> None:
        cases = {
            case["id"]: case
            for case in self.cases["skills"]["job-search-mcp"]["cases"]
        }
        eligibility = {
            "skill_used": "job-search-mcp",
            "decision": "reject",
            "actions": ["Exclude before scoring."],
            "blocked_actions": ["Do not mark Apply now or generate a CV."],
            "evidence": [
                "The vacancy requires UAE nationals only.",
                "Ahmed is Egyptian and does not meet the restriction.",
                "The 92% keyword score cannot override eligibility.",
            ],
            "response": "Reject as ineligible before scoring.",
        }
        assertion = next(
            item
            for item in cases["job-search-nationality-restriction"]["assertions"]
            if item["id"] == "recognize_restriction_mismatch"
        )
        self.assertTrue(gate.grade_assertion(eligibility, assertion)[0])

        salary = {
            "skill_used": "job-search-mcp",
            "decision": "hold",
            "actions": ["Rank as Verify compensation."],
            "blocked_actions": ["Do not place it in Apply now."],
            "evidence": [
                "The posting contains no direct compensation figure.",
                "A third-party blog is discovery evidence, not verified proof.",
            ],
            "response": "Verify compensation; do not claim it clears the salary floor.",
        }
        salary_assertions = {
            item["id"]: item
            for item in cases["job-search-unsupported-salary"]["assertions"]
        }
        self.assertTrue(gate.grade_assertion(salary, salary_assertions["salary_unknown"])[0])
        self.assertTrue(
            gate.grade_assertion(salary, salary_assertions["source_backed_salary_only"])[0]
        )

        health = {
            "skill_used": "job-search-mcp",
            "decision": "diagnose",
            "actions": ["Retain authoritative batch results."],
            "blocked_actions": ["Do not declare quota exhausted or discard scores."],
            "evidence": ["HTTP 504 is not 429; batch_scoring returned parseable JSON."],
            "response": "Treat the timeout as a warning, not quota exhaustion.",
        }
        health_assertion = next(
            item
            for item in cases["job-search-non429-health-check"]["assertions"]
            if item["id"] == "do_not_discard_results"
        )
        self.assertTrue(gate.grade_assertion(health, health_assertion)[0])

        applied = {
            "skill_used": "job-search-mcp",
            "decision": "reject",
            "actions": ["Exclude this previously applied role."],
            "blocked_actions": ["Do not shortlist or score it.", "Do not generate another CV."],
            "evidence": [
                "applied_jobs and jobs.applied match the URL, job ID, title, company, and location signature."
            ],
            "response": "A refreshed URL does not make this a new role.",
        }
        applied_assertion = next(
            item
            for item in cases["job-search-applied-role-resurfacing"]["assertions"]
            if item["id"] == "exclude_before_ranking"
        )
        self.assertTrue(gate.grade_assertion(applied, applied_assertion)[0])

        salary["evidence"] = [
            "The posting contains no direct compensation figure.",
            "A third-party blog is discovery evidence and does not prove the salary floor is met.",
        ]
        self.assertTrue(
            gate.grade_assertion(salary, salary_assertions["source_backed_salary_only"])[0]
        )

    def test_linkedin_upload_case_rejects_false_applied_state(self) -> None:
        case = next(
            case
            for case in self.cases["skills"]["linkedin"]["cases"]
            if case["id"] == "linkedin-upload-not-submitted"
        )
        response = {
            "skill_used": "linkedin",
            "decision": "hold",
            "actions": [],
            "blocked_actions": [],
            "evidence": [],
            "response": (
                "Hold. The upload helper returning ok is not proof. Do not submit until the "
                "visible UI shows the exact intended CV. This role is not applied: do not mark "
                "it applied or set date_applied without visible, verified submission proof."
            ),
        }
        grades = [gate.grade_assertion(response, assertion)[0] for assertion in case["assertions"]]
        self.assertEqual([True, True, True, True], grades)

    def test_cmo_image_failure_requires_hold_state_and_failure_report(self) -> None:
        case = next(
            case
            for case in self.cases["skills"]["cmo-agent"]["cases"]
            if case["id"] == "cmo-image-upload-failure"
        )
        response = {
            "skill_used": "cmo-agent",
            "decision": "hold",
            "actions": [],
            "blocked_actions": [
                "Do not publish text-only.",
                "Do not mark the row Posted.",
            ],
            "evidence": [
                "The expected visual has no real Composio s3key.",
                "Keep the row Scheduled.",
                "Send an upload-failure decision card when messaging is allowed.",
            ],
            "response": "Hold the full text-and-image post.",
        }
        grades = [gate.grade_assertion(response, assertion)[0] for assertion in case["assertions"]]
        self.assertEqual([True, True, True, True, True], grades)

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
