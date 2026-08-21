import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "governed-product-learning.py"
SPEC = importlib.util.spec_from_file_location("governed_product_learning", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class GovernedProductLearningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = {
            "schema_version": 1,
            "weights": {"dropoff": 0.7, "error": 0.3},
            "analysis": {"min_sample_size": 20, "min_friction_score": 0.15},
        }

    def tearDown(self):
        self.temp.cleanup()

    def snapshot(self):
        return {
            "schema_version": 1,
            "snapshot_id": "pilot-window-001",
            "data_policy": "aggregated-sanitized",
            "source_type": "synthetic-control-fixture",
            "workflow": "OpenClaw task completion",
            "window": {
                "start": "2026-08-01T00:00:00+00:00",
                "end": "2026-08-08T00:00:00+00:00",
            },
            "privacy": {"contains_pii": False, "aggregated": True},
            "steps": [
                {"id": "task-start", "name": "Task start", "entered": 100, "completed": 95, "errors": 1, "dropoff_classification": "friction"},
                {"id": "tool-execution", "name": "Tool execution", "entered": 90, "completed": 54, "errors": 18, "dropoff_classification": "friction"},
                {"id": "verification", "name": "Verification", "entered": 54, "completed": 50, "errors": 2, "dropoff_classification": "friction"},
            ],
        }

    def lesson(self):
        return MODULE.analyze_snapshot(self.snapshot(), "1" * 64, self.config)

    def spec(self, mode="shadow", approval=None):
        return {
            "schema_version": 1,
            "lesson_id": self.lesson()["lesson"]["id"],
            "mode": mode,
            "hypothesis": "A bounded change will increase completion without increasing the error rate.",
            "intervention": {"variable": "tool-guidance", "change": "Add one contextual tool-selection hint."},
            "comparator": {
                "method": "paired-control-treatment",
                "control": "Replay the frozen candidate pool with the current workflow.",
                "treatment": "Replay the same candidate pool with one bounded change.",
                "unit": "candidate-signal",
            },
            "primary_metric": {
                "name": "completion-rate",
                "direction": "increase",
                "baseline": 0.6,
                "min_improvement": 0.1,
            },
            "guardrails": [
                {
                    "name": "error-rate",
                    "direction": "decrease",
                    "baseline": 0.2,
                    "max_regression": 0.03,
                }
            ],
            "evaluation": {"min_sample_size": 50, "min_window_days": 7, "max_window_days": 14},
            "approval": approval,
            "rollback": "Restore the prior guidance and retain the result as negative evidence.",
        }

    def staged(self, mode="shadow", approval=None):
        return MODULE.stage_experiment(self.lesson(), "2" * 64, self.spec(mode, approval), "3" * 64)

    def result(self, stage, stage_sha, completion=0.75, error=0.19, sample=80, days=7):
        return {
            "schema_version": 1,
            "experiment_id": stage["id"],
            "stage_sha256": stage_sha,
            "window": {
                "start": "2026-08-01T00:00:00+00:00",
                "end": f"2026-08-{1 + days:02d}T00:00:00+00:00",
            },
            "comparison": {
                "method": "paired-control-treatment",
                "control_sample_size": sample,
                "treatment_sample_size": sample,
                "control_metrics": {"completion-rate": 0.6, "error-rate": 0.2},
                "treatment_metrics": {"completion-rate": completion, "error-rate": error},
            },
        }

    def test_selects_one_highest_leverage_unknown(self):
        output = self.lesson()
        self.assertEqual("review", output["status"])
        self.assertEqual("tool-execution", output["lesson"]["step"]["id"])
        self.assertFalse(output["automatic_change"])

    def test_rejects_non_aggregated_or_pii_snapshot(self):
        snapshot = self.snapshot()
        snapshot["privacy"]["contains_pii"] = True
        with self.assertRaises(MODULE.ProductLearningError):
            MODULE.analyze_snapshot(snapshot, "1" * 64, self.config)

    def test_intentional_editorial_filter_is_not_scored_as_dropoff(self):
        snapshot = self.snapshot()
        snapshot["steps"][1].update({
            "completed": 20,
            "errors": 0,
            "dropoff_classification": "intentional-filter",
        })
        config = json.loads(json.dumps(self.config))
        config["analysis"]["min_friction_score"] = 0
        output = MODULE.analyze_snapshot(snapshot, "1" * 64, config)
        selected = output["lesson"]["step"]
        self.assertNotEqual("tool-execution", selected["id"])

    def test_snapshot_requires_explicit_dropoff_classification(self):
        snapshot = self.snapshot()
        del snapshot["steps"][0]["dropoff_classification"]
        with self.assertRaises(MODULE.ProductLearningError):
            MODULE.analyze_snapshot(snapshot, "1" * 64, self.config)

    def test_stops_on_insufficient_sample_and_clean_noop(self):
        snapshot = self.snapshot()
        for step in snapshot["steps"]:
            step["entered"] = min(step["entered"], 10)
            step["completed"] = min(step["completed"], step["entered"])
            step["errors"] = 0
        output = MODULE.analyze_snapshot(snapshot, "1" * 64, self.config)
        self.assertEqual("insufficient-evidence", output["status"])

        snapshot = self.snapshot()
        for step in snapshot["steps"]:
            step["completed"] = step["entered"]
            step["errors"] = 0
        output = MODULE.analyze_snapshot(snapshot, "1" * 64, self.config)
        self.assertEqual("clean-noop", output["status"])

    def test_stage_enforces_one_variable_and_production_approval(self):
        staged = self.staged(mode="production")
        self.assertEqual("approval-required", staged["state"])
        self.assertFalse(staged["automatic_execution"])
        approved = self.staged(
            mode="production",
            approval={
                "method": "explicit_text",
                "approved_by": "Ahmed Nasr",
                "approval_ref": "telegram-message-63709",
            },
        )
        self.assertEqual("ready-for-approved-execution", approved["state"])

        spec = self.spec()
        spec["intervention"]["second_variable"] = "not allowed"
        with self.assertRaises(MODULE.ProductLearningError):
            MODULE.stage_experiment(self.lesson(), "2" * 64, spec, "3" * 64)

        spec = self.spec()
        del spec["comparator"]
        with self.assertRaises(MODULE.ProductLearningError):
            MODULE.stage_experiment(self.lesson(), "2" * 64, spec, "3" * 64)

    def test_success_requires_metric_lift_and_no_guardrail_breach(self):
        stage = self.staged()
        stage_sha = "4" * 64
        outcome = MODULE.evaluate_experiment(stage, stage_sha, self.result(stage, stage_sha))
        self.assertEqual("success", outcome["outcome"])
        self.assertTrue(outcome["eligible_for_learning_capture"])
        self.assertFalse(outcome["automatic_promotion"])

    def test_inconclusive_and_insufficient_evidence_are_terminal(self):
        stage = self.staged()
        stage_sha = "4" * 64
        inconclusive = MODULE.evaluate_experiment(
            stage, stage_sha, self.result(stage, stage_sha, completion=0.65)
        )
        self.assertEqual("inconclusive", inconclusive["outcome"])
        insufficient = MODULE.evaluate_experiment(
            stage, stage_sha, self.result(stage, stage_sha, sample=10)
        )
        self.assertEqual("insufficient-evidence", insufficient["outcome"])

    def test_guardrail_breach_requires_rollback(self):
        stage = self.staged()
        stage_sha = "4" * 64
        outcome = MODULE.evaluate_experiment(
            stage, stage_sha, self.result(stage, stage_sha, completion=0.8, error=0.25)
        )
        self.assertEqual("rollback-required", outcome["outcome"])
        self.assertIsNotNone(outcome["rollback"])
        self.assertFalse(outcome["eligible_for_learning_capture"])

    def test_result_must_bind_to_locked_stage_hash(self):
        stage = self.staged()
        with self.assertRaises(MODULE.ProductLearningError):
            MODULE.evaluate_experiment(stage, "4" * 64, self.result(stage, "5" * 64))

    def test_paired_comparator_requires_equal_samples(self):
        stage = self.staged()
        stage_sha = "4" * 64
        result = self.result(stage, stage_sha)
        result["comparison"]["treatment_sample_size"] -= 1
        with self.assertRaises(MODULE.ProductLearningError):
            MODULE.evaluate_experiment(stage, stage_sha, result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
