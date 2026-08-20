import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "correction-to-learning.py"
LEARNING_SCRIPT = ROOT / "skills" / "governed-learning-loop" / "scripts" / "learning_loop.py"
SPEC = importlib.util.spec_from_file_location("correction_to_learning", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class CorrectionToLearningTests(unittest.TestCase):
    def args(self, root: Path, run_id="telegram-1"):
        return argparse.Namespace(
            data_dir=root / "learning",
            report=root / "report.md",
            intake_dir=root / "intake",
            lessons_file=root / "LEARNINGS.md",
            learning_script=LEARNING_SCRIPT,
            pattern_key="workflow.correction-example",
            summary="Use the verified governing route when this correction recurs.",
            run_id=run_id,
            verification="The correction is captured as evidence but no active rule is changed.",
            target_type="rule",
            occurred_at="2026-08-17T10:00:00+03:00",
        )

    def test_capture_is_sanitized_and_does_not_deploy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = MODULE.capture_correction(self.args(root))
            self.assertEqual("captured", result["status"])
            self.assertFalse(result["active_target_changed"])
            evidence = json.loads(Path(result["evidence"]).read_text())
            self.assertFalse(evidence["raw_session_mined"])
            registry = json.loads((root / "learning" / "registry.json").read_text())
            self.assertEqual(1, len(registry["observations"]))
            self.assertIn("observation only", (root / "LEARNINGS.md").read_text())

    def test_rejects_secret_before_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            args = self.args(root)
            args.summary = "Capture api_key=super-secret-value in the rule."
            with self.assertRaises(MODULE.CorrectionIntakeError):
                MODULE.capture_correction(args)
            self.assertFalse((root / "intake").exists())

    def test_caps_observations_and_aggregates_recurrence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index in range(MODULE.MAX_OBSERVATIONS_PER_PATTERN):
                MODULE.capture_correction(self.args(root, f"telegram-{index}"))
            result = MODULE.capture_correction(self.args(root, "telegram-over-cap"))
            self.assertEqual("aggregated", result["status"])
            registry = json.loads((root / "learning" / "registry.json").read_text())
            self.assertEqual(MODULE.MAX_OBSERVATIONS_PER_PATTERN, len(registry["observations"]))
            self.assertTrue(Path(result["aggregate"]).exists())


if __name__ == "__main__":
    unittest.main()
