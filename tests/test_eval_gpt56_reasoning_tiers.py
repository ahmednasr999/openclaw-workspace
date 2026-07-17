from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "eval-gpt56-reasoning-tiers.py"
SPEC = importlib.util.spec_from_file_location("eval_gpt56_reasoning_tiers", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ReasoningEvalTests(unittest.TestCase):
    def test_same_model_for_every_level(self):
        self.assertEqual(MODULE.MODEL, "openai/gpt-5.6-sol")
        self.assertEqual(MODULE.LEVELS, ("low", "medium"))

    def test_fixtures_are_deterministic_json_contracts(self):
        self.assertGreaterEqual(len(MODULE.TASKS), 4)
        for task in MODULE.TASKS:
            self.assertIn("Return JSON only", task["prompt"])
            self.assertIsInstance(task["expected"], dict)


if __name__ == "__main__":
    unittest.main()
