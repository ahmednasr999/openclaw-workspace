import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCRIPT = Path("/root/.openclaw/workspace/scripts/open-work-resolver.py")
SPEC = importlib.util.spec_from_file_location("open_work_resolver", SCRIPT)
resolver = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(resolver)


class OpenWorkResolverTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 7, 20, 14, 0, tzinfo=timezone.utc)
        self.item = {
            "id": "pilot",
            "title": "Pilot",
            "owner": "HR",
            "resolver_owner": "NASR",
            "authority": "read-only",
            "target": 30,
            "unit": "strict applications",
            "stale_after_seconds": 900,
            "ledger": "/evidence/ledger.jsonl",
            "state_file": "/evidence/state.json",
            "service": "pilot.service",
        }
        self.supervisor = {
            "verified": 8,
            "heartbeat_at": (self.now - timedelta(seconds=30)).isoformat(),
            "supervisor_pid": 100,
            "reason": "await_fresh_easy_apply_jobs",
        }
        self.ledger = {
            "verified": 8,
            "source_of_truth": "/evidence/ledger.jsonl",
            "exclusions": [{}, {}],
        }
        self.service = {
            "ActiveState": "active",
            "SubState": "running",
            "Result": "success",
            "MainPID": "100",
        }
        self.original_pid_check = resolver.pid_is_alive
        resolver.pid_is_alive = lambda pid: int(pid) == 100

    def tearDown(self):
        resolver.pid_is_alive = self.original_pid_check

    def evaluate(self, previous=None):
        return resolver.evaluate_linkedin_plus30(
            self.item,
            self.supervisor,
            self.ledger,
            self.service,
            self.now,
            previous,
        )

    def test_fresh_active_evidence_is_in_progress(self):
        result = self.evaluate()
        self.assertEqual(result["status"], "in_progress")
        self.assertEqual(result["verified"], 8)
        self.assertEqual(result["remaining"], 22)
        self.assertIsNone(result["blocker"])

    def test_verified_advance_is_progress(self):
        result = self.evaluate({"verified": 6})
        self.assertEqual(result["status"], "progress")
        self.assertEqual(result["progress_delta"], 2)

    def test_recovers_from_prior_blocked_snapshot_with_null_verified(self):
        result = self.evaluate({"verified": None, "status": "blocked"})
        self.assertEqual(result["status"], "in_progress")
        self.assertEqual(result["progress_delta"], 0)

    def test_stale_heartbeat_requires_intervention(self):
        self.supervisor["heartbeat_at"] = (self.now - timedelta(seconds=901)).isoformat()
        result = self.evaluate()
        self.assertEqual(result["status"], "intervention_required")
        self.assertIn("stale", result["blocker"])

    def test_supervisor_overclaim_requires_intervention(self):
        self.supervisor["verified"] = 9
        result = self.evaluate()
        self.assertEqual(result["status"], "intervention_required")
        self.assertIn("overclaims", result["blocker"])

    def test_fresh_strict_ledger_advance_is_progress_while_supervisor_catches_up(self):
        self.supervisor["verified"] = 7
        result = self.evaluate()
        self.assertEqual(result["status"], "progress")
        self.assertIsNone(result["blocker"])
        self.assertIn("trails", result["evidence"]["notes"][0])

    def test_inactive_executor_requires_intervention_before_close(self):
        self.service["ActiveState"] = "inactive"
        self.service["SubState"] = "dead"
        result = self.evaluate()
        self.assertEqual(result["status"], "intervention_required")
        self.assertIn("inactive/dead", result["blocker"])

    def test_strict_target_produces_verified_close(self):
        self.supervisor["verified"] = 30
        self.ledger["verified"] = 30
        self.service["ActiveState"] = "inactive"
        self.service["SubState"] = "dead"
        result = self.evaluate()
        self.assertEqual(result["status"], "verified_closed")
        self.assertTrue(result["verified_close"]["achieved"])

    def test_terminal_done_closes_after_service_retirement(self):
        self.supervisor.update(
            {
                "verified": 30,
                "heartbeat_at": (self.now - timedelta(days=2)).isoformat(),
                "supervisor_pid": 999,
                "child_event": {"event": "done", "submitted": 30, "target": 30},
            }
        )
        self.ledger["verified"] = 30
        self.service.update(
            {
                "LoadState": "not-found",
                "ActiveState": "inactive",
                "SubState": "dead",
                "MainPID": "0",
            }
        )
        result = self.evaluate()
        self.assertEqual(result["status"], "verified_closed")
        self.assertTrue(result["verified_close"]["achieved"])
        self.assertIn("terminal completion", result["evidence"]["notes"][0])

    def test_target_does_not_close_when_supervisor_overclaims_ledger(self):
        self.item["target"] = 30
        self.supervisor["verified"] = 31
        self.ledger["verified"] = 30
        result = self.evaluate()
        self.assertEqual(result["status"], "intervention_required")
        self.assertFalse(result["verified_close"]["achieved"])

    def test_briefing_contains_only_three_operational_buckets(self):
        item = self.evaluate()
        briefing = resolver.build_briefing({"generated_at": self.now.isoformat(), "items": [item]})
        self.assertEqual(set(briefing), {"generated_at", "progress", "intervention", "closures"})
        self.assertEqual(len(briefing["progress"]), 1)


if __name__ == "__main__":
    unittest.main()
