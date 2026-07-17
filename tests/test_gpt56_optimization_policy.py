from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check-gpt56-optimization-policy.py"
SPEC = importlib.util.spec_from_file_location("check_gpt56_optimization_policy", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class OptimizationPolicyTests(unittest.TestCase):
    def test_audit_accepts_expected_state(self):
        jobs = [
            {"id": job_id, "name": name, "enabled": True, "payload": {"kind": "agentTurn", "model": "openai/gpt-5.6-sol", "thinking": "low"}}
            for job_id, name in MODULE.EXPECTED_LOW.items()
        ]
        config = {"agents": {"defaults": {"model": {"primary": "openai/gpt-5.6-sol"}}}, "tools": {}}
        self.assertTrue(MODULE.audit(config, jobs)["ok"])

    def test_audit_rejects_experimental_tool_search(self):
        jobs = [
            {"id": job_id, "name": name, "enabled": True, "payload": {"kind": "agentTurn", "model": "openai/gpt-5.6-sol", "thinking": "low"}}
            for job_id, name in MODULE.EXPECTED_LOW.items()
        ]
        config = {"agents": {"defaults": {"model": {"primary": "openai/gpt-5.6-sol"}}}, "tools": {"toolSearch": True}}
        self.assertIn("experimental_tool_search_enabled", MODULE.audit(config, jobs)["failures"])


if __name__ == "__main__":
    unittest.main()
