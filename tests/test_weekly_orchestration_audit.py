import argparse
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "weekly-orchestration-audit.py"
SPEC = importlib.util.spec_from_file_location("weekly_orchestration_audit", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class WeeklyOrchestrationAuditTests(unittest.TestCase):
    def test_loads_read_only_cron_database_fallback_shape(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.sqlite"
            connection = sqlite3.connect(path)
            connection.execute("CREATE TABLE cron_jobs (job_json TEXT, state_json TEXT, sort_order INTEGER, updated_at INTEGER, job_id TEXT)")
            connection.execute(
                "INSERT INTO cron_jobs VALUES (?, ?, 1, 1, 'job-1')",
                (
                    json.dumps({"id": "job-1", "name": "Fixture", "enabled": True, "payload": {"kind": "command"}}),
                    json.dumps({"lastRunStatus": "ok", "consecutiveErrors": 0}),
                ),
            )
            connection.commit()
            connection.close()
            loaded = MODULE.load_cron_database(path)
            self.assertEqual("sqlite-read-only", loaded["source"])
            self.assertEqual("ok", loaded["jobs"][0]["status"])

    def test_classifies_failure_deterministic_turn_and_family(self):
        jobs = [
            {
                "id": "a",
                "name": "Broken Weekly Job",
                "enabled": True,
                "status": "error",
                "payload": {"kind": "command"},
                "state": {"consecutiveErrors": 3},
            },
            {
                "id": "b",
                "name": "Deterministic Wrapper",
                "enabled": True,
                "status": "ok",
                "payload": {"kind": "agentTurn", "message": "Run python3 /x/check.py"},
                "state": {},
            },
            {
                "id": "c1",
                "name": "Radar - 11am",
                "enabled": True,
                "status": "ok",
                "payload": {"kind": "command"},
                "state": {},
            },
            {
                "id": "c2",
                "name": "Radar - 3pm",
                "enabled": True,
                "status": "ok",
                "payload": {"kind": "command"},
                "state": {},
            },
        ]
        rows, counts = MODULE.classify_jobs(jobs)
        by_id = {row["id"]: row["action"] for row in rows}
        self.assertEqual("FIX", by_id["a"])
        self.assertEqual("AUTOMATE", by_id["b"])
        self.assertEqual("COMBINE-REVIEW", by_id["c1"])
        self.assertEqual("COMBINE-REVIEW", by_id["c2"])
        self.assertEqual(1, counts["FIX"])

    def test_finds_only_cross_owner_parallel_review_clusters(self):
        jobs = [
            {"name": "HR Review", "enabled": True, "agentId": "hr", "schedule": {"kind": "cron", "expr": "0 8 * * 0"}},
            {"name": "CTO Review", "enabled": True, "agentId": "cto", "schedule": {"kind": "cron", "expr": "30 8 * * 0"}},
            {"name": "LinkedIn Browser Work", "enabled": True, "agentId": "cmo", "schedule": {"kind": "cron", "expr": "45 8 * * 0"}},
        ]
        clusters = MODULE.parallel_candidates(jobs)
        self.assertEqual(1, len(clusters))
        self.assertEqual(["HR Review", "CTO Review"], clusters[0]["jobs"])

    def test_run_writes_advisory_reports_without_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture = root / "cron.json"
            fixture.write_text(json.dumps({"jobs": [{
                "id": "ok",
                "name": "Healthy Job",
                "enabled": True,
                "status": "ok",
                "payload": {"kind": "command"},
                "state": {"consecutiveErrors": 0},
            }]}), encoding="utf-8")
            report_dir = root / "reports"
            payload = MODULE.run(argparse.Namespace(
                cron_json=fixture,
                report_dir=report_dir,
                now="2026-08-17T10:00:00+03:00",
            ))
            self.assertEqual(0, payload["mutations_performed"])
            self.assertEqual(1, payload["counts"]["KEEP"])
            self.assertTrue((report_dir / "latest.json").exists())
            self.assertIn("Advisory only", (report_dir / "latest.md").read_text())


if __name__ == "__main__":
    unittest.main()
