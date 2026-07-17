import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/resource-pressure-guard.py"
SPEC = importlib.util.spec_from_file_location("resource_pressure_guard", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


CONFIG = {
    "warning": {
        "mem_available_pct_below": 20,
        "swap_used_pct_above": 50,
        "root_disk_used_pct_above": 80,
        "memory_psi_some_avg60_above": 10,
        "memory_psi_full_avg60_above": 2,
    },
    "critical": {
        "mem_available_pct_below": 15,
        "swap_used_pct_above": 70,
        "root_disk_used_pct_above": 88,
        "memory_psi_some_avg60_above": 20,
        "memory_psi_full_avg60_above": 5,
    },
    "immediate": {
        "mem_available_pct_below": 8,
        "swap_used_pct_above": 90,
        "root_disk_used_pct_above": 95,
        "memory_psi_full_avg60_above": 15,
    },
    "recovery": {
        "mem_available_pct_above": 22,
        "swap_used_pct_below": 48,
        "root_disk_used_pct_below": 79,
        "memory_psi_some_avg60_below": 8,
        "memory_psi_full_avg60_below": 1.5,
    },
    "critical_samples_to_block": 2,
    "recovery_samples_to_unblock": 3,
}


def metrics(mem=40, swap=10, disk=50, some=0, full=0):
    return {
        "mem_available_pct": mem,
        "swap_used_pct": swap,
        "root_disk_used_pct": disk,
        "memory_psi_some_avg60": some,
        "memory_psi_full_avg60": full,
    }


class ResourcePressureGuardTests(unittest.TestCase):
    def test_two_critical_samples_block(self):
        state, alert = MODULE.advance_state({}, metrics(mem=12, some=30), CONFIG, 1)
        self.assertFalse(state["blocked"])
        self.assertIn("warning", alert)
        state, alert = MODULE.advance_state(state, metrics(mem=12, some=30), CONFIG, 2)
        self.assertTrue(state["blocked"])
        self.assertIn("blocked", alert)

    def test_immediate_threshold_blocks_on_first_sample(self):
        state, _ = MODULE.advance_state({}, metrics(mem=6), CONFIG, 1)
        self.assertTrue(state["blocked"])

    def test_requires_three_clean_samples_to_recover(self):
        state = {"blocked": True, "level": "critical", "critical_samples": 2}
        for now in (1, 2):
            state, alert = MODULE.advance_state(state, metrics(), CONFIG, now)
            self.assertTrue(state["blocked"])
            self.assertIsNone(alert)
        state, alert = MODULE.advance_state(state, metrics(), CONFIG, 3)
        self.assertFalse(state["blocked"])
        self.assertIn("recovered", alert)

    def test_warning_does_not_block(self):
        state, alert = MODULE.advance_state({}, metrics(mem=18, swap=55), CONFIG, 1)
        self.assertEqual(state["level"], "warning")
        self.assertFalse(state["blocked"])
        self.assertIn("warning", alert)


if __name__ == "__main__":
    unittest.main()
