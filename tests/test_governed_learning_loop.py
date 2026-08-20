import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills" / "governed-learning-loop" / "scripts" / "learning_loop.py"
SPEC = importlib.util.spec_from_file_location("governed_learning_loop", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class GovernedLearningLoopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.data_dir = root / "data"
        self.report = root / "report.md"

    def tearDown(self):
        self.temp.cleanup()

    def args(self, run_id="run-1", evidence=None, target_type="skill-update"):
        return argparse.Namespace(
            data_dir=self.data_dir,
            report=self.report,
            pattern_key="workflow.verify-before-adapt",
            summary="Use an independent read-only verifier before adapting an operational workflow.",
            run_id=run_id,
            source=f"reports/{run_id}.md",
            evidence=evidence or [f"tests/{run_id}: passed"],
            verification=f"Focused verification for {run_id} passed with no production mutation.",
            target_type=target_type,
            occurred_at="2026-07-18T10:00:00+00:00",
        )

    def build_candidate(self):
        MODULE.capture(self.args("run-1", ["evidence-one"]))
        MODULE.capture(self.args("run-2", ["evidence-two"]))
        MODULE.build(argparse.Namespace(data_dir=self.data_dir, report=self.report))
        return MODULE.load_registry(self.data_dir)["candidates"][0]

    def write_suite(self):
        suite = Path(self.temp.name) / "suite.json"
        suite.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "name": "Curated governed-loop replay",
                    "data_policy": "curated-sanitized",
                    "tasks": [
                        {"id": "validation-normal", "split": "validation", "critical": False},
                        {"id": "locked-safety", "split": "locked-test", "critical": True},
                    ],
                    "thresholds": {
                        "required_runs": 2,
                        "min_absolute_improvement": 0.1,
                        "max_candidate_cost_per_run": 4.0,
                        "max_cost_increase_ratio": 1.5,
                    },
                }
            ),
            encoding="utf-8",
        )
        return suite

    def create_proposal(self):
        candidate = self.build_candidate()
        artifact = Path(self.temp.name) / "SKILL.md"
        artifact.write_text("candidate artifact\n", encoding="utf-8")
        suite = self.write_suite()
        result = MODULE.create_proposal(
            argparse.Namespace(
                data_dir=self.data_dir,
                candidate=candidate["id"],
                target_path="skills/example/SKILL.md",
                artifact=artifact,
                suite=suite,
                edit=["Add deterministic replay evaluation gate."],
            )
        )
        return result["proposal"], suite

    def write_results(self, proposal, candidate_scores=(0.8, 1.0), candidate_cost=1.2):
        packet = Path(self.temp.name) / f"results-{candidate_scores[0]}-{candidate_cost}.json"
        tasks = []
        for task_id, baseline, candidate in (
            ("validation-normal", 0.5, candidate_scores[0]),
            ("locked-safety", 0.9, candidate_scores[1]),
        ):
            tasks.append(
                {
                    "task_id": task_id,
                    "baseline_score": baseline,
                    "candidate_score": candidate,
                    "baseline_cost": 1.0,
                    "candidate_cost": candidate_cost,
                }
            )
        packet.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "proposal_id": proposal["id"],
                    "suite_sha256": proposal["suite_sha256"],
                    "runs": [
                        {"run_id": "independent-run-1", "tasks": tasks},
                        {"run_id": "independent-run-2", "tasks": tasks},
                    ],
                }
            ),
            encoding="utf-8",
        )
        return packet

    def test_capture_is_idempotent(self):
        first = MODULE.capture(self.args())
        second = MODULE.capture(self.args())
        registry = MODULE.load_registry(self.data_dir)
        self.assertEqual("created", first["status"])
        self.assertEqual("existing", second["status"])
        self.assertEqual(1, len(registry["observations"]))

    def test_build_requires_distinct_runs_and_evidence(self):
        MODULE.capture(self.args("run-1", ["same-evidence"]))
        MODULE.capture(self.args("run-2", ["same-evidence"]))
        result = MODULE.build(argparse.Namespace(data_dir=self.data_dir, report=self.report))
        self.assertEqual(0, result["candidates"])
        MODULE.capture(self.args("run-3", ["different-evidence"]))
        result = MODULE.build(argparse.Namespace(data_dir=self.data_dir, report=self.report))
        self.assertEqual(1, result["candidates"])
        self.assertIn("Automatic deployments performed by this loop: 0", self.report.read_text())

    def test_build_is_idempotent(self):
        MODULE.capture(self.args("run-1", ["evidence-one"]))
        MODULE.capture(self.args("run-2", ["evidence-two"]))
        first = MODULE.build(argparse.Namespace(data_dir=self.data_dir, report=self.report))
        registry_before = json.loads((self.data_dir / "registry.json").read_text())
        second = MODULE.build(argparse.Namespace(data_dir=self.data_dir, report=self.report))
        registry_after = json.loads((self.data_dir / "registry.json").read_text())
        self.assertEqual(1, first["created"])
        self.assertEqual(0, second["created"])
        self.assertEqual(0, second["updated"])
        self.assertEqual(registry_before, registry_after)

    def test_conflicting_target_types_do_not_form_candidate(self):
        MODULE.capture(self.args("run-1", ["evidence-one"], "skill-update"))
        MODULE.capture(self.args("run-2", ["evidence-two"], "rule"))
        result = MODULE.build(argparse.Namespace(data_dir=self.data_dir, report=self.report))
        self.assertEqual(0, result["candidates"])

    def test_validate_candidate_rechecks_registry_evidence(self):
        MODULE.capture(self.args("run-1", ["evidence-one"]))
        MODULE.capture(self.args("run-2", ["evidence-two"]))
        MODULE.build(argparse.Namespace(data_dir=self.data_dir, report=self.report))
        registry = MODULE.load_registry(self.data_dir)
        candidate = registry["candidates"][0]
        result = MODULE.validate_candidate(
            argparse.Namespace(data_dir=self.data_dir, candidate=candidate["id"])
        )
        self.assertEqual("valid", result["status"])

        registry["observations"] = registry["observations"][:1]
        MODULE.atomic_write_json(self.data_dir / "registry.json", registry)
        with self.assertRaises(MODULE.LearningLoopError):
            MODULE.validate_candidate(
                argparse.Namespace(data_dir=self.data_dir, candidate=candidate["id"])
            )

    def test_rejects_secret_like_content(self):
        args = self.args()
        args.verification = "api_key=super-secret-value"
        with self.assertRaises(MODULE.LearningLoopError):
            MODULE.capture(args)

    def test_promotion_request_never_writes_target(self):
        proposal, _ = self.create_proposal()
        packet = self.write_results(proposal)
        MODULE.evaluate_proposal(
            argparse.Namespace(data_dir=self.data_dir, proposal=proposal["id"], results=packet)
        )
        target = Path(self.temp.name) / "skills" / "example" / "SKILL.md"
        result = MODULE.request_promotion(
            argparse.Namespace(
                data_dir=self.data_dir,
                proposal=proposal["id"],
                target_path="skills/example/SKILL.md",
                approved_by="Ahmed Nasr",
                approval_ref="telegram-message-12345",
            )
        )
        self.assertEqual("created", result["status"])
        self.assertFalse(result["target_written"])
        self.assertFalse(target.exists())

        repeated = MODULE.request_promotion(
            argparse.Namespace(
                data_dir=self.data_dir,
                proposal=proposal["id"],
                target_path="skills/example/SKILL.md",
                approved_by="Ahmed Nasr",
                approval_ref="telegram-message-12345",
            )
        )
        self.assertEqual("existing", repeated["status"])
        self.assertEqual(1, len(MODULE.load_registry(self.data_dir)["promotion_requests"]))

    def test_candidate_only_promotion_is_rejected(self):
        candidate = self.build_candidate()
        with self.assertRaises(MODULE.LearningLoopError):
            MODULE.request_promotion(
                argparse.Namespace(
                    data_dir=self.data_dir,
                    candidate=candidate["id"],
                    proposal=None,
                    target_path="skills/example/SKILL.md",
                    approved_by="Ahmed Nasr",
                    approval_ref="telegram-message-12345",
                )
            )

    def test_rejects_unsafe_target_path(self):
        with self.assertRaises(MODULE.LearningLoopError):
            MODULE.validate_target_path("../AGENTS.md")
        with self.assertRaises(MODULE.LearningLoopError):
            MODULE.validate_target_path("config/openclaw.json")

    def test_proposal_requires_one_to_four_edits_and_curated_locked_suite(self):
        candidate = self.build_candidate()
        artifact = Path(self.temp.name) / "SKILL.md"
        artifact.write_text("candidate artifact\n", encoding="utf-8")
        suite = self.write_suite()
        args = argparse.Namespace(
            data_dir=self.data_dir,
            candidate=candidate["id"],
            target_path="skills/example/SKILL.md",
            artifact=artifact,
            suite=suite,
            edit=[f"bounded edit {index}" for index in range(5)],
        )
        with self.assertRaises(MODULE.LearningLoopError):
            MODULE.create_proposal(args)
        args.edit = ["Add one bounded gate."]
        suite_payload = json.loads(suite.read_text())
        suite_payload["data_policy"] = "raw-transcripts"
        suite.write_text(json.dumps(suite_payload), encoding="utf-8")
        with self.assertRaises(MODULE.LearningLoopError):
            MODULE.create_proposal(args)

    def test_replay_accepts_repeated_improvement_without_critical_regression(self):
        proposal, _ = self.create_proposal()
        packet = self.write_results(proposal)
        result = MODULE.evaluate_proposal(
            argparse.Namespace(data_dir=self.data_dir, proposal=proposal["id"], results=packet)
        )
        self.assertEqual("accepted", result["status"])
        registry = MODULE.load_registry(self.data_dir)
        self.assertEqual("evaluation-passed", registry["proposals"][0]["status"])
        self.assertEqual([], registry["negative_evidence"])
        self.assertFalse(result["evaluation"]["automatic_deployment"])

    def test_replay_rejects_and_retains_critical_regression(self):
        proposal, _ = self.create_proposal()
        packet = self.write_results(proposal, candidate_scores=(0.9, 0.8))
        result = MODULE.evaluate_proposal(
            argparse.Namespace(data_dir=self.data_dir, proposal=proposal["id"], results=packet)
        )
        self.assertEqual("rejected", result["status"])
        registry = MODULE.load_registry(self.data_dir)
        self.assertEqual(1, len(registry["negative_evidence"]))
        self.assertTrue(
            any("critical regression" in item for item in result["evaluation"]["failures"])
        )

    def test_replay_rejects_cost_overrun(self):
        proposal, _ = self.create_proposal()
        packet = self.write_results(proposal, candidate_cost=2.1)
        result = MODULE.evaluate_proposal(
            argparse.Namespace(data_dir=self.data_dir, proposal=proposal["id"], results=packet)
        )
        self.assertEqual("rejected", result["status"])
        self.assertTrue(any("candidate cost" in item for item in result["evaluation"]["failures"]))

    def test_replay_rejects_added_cost_over_zero_cost_baseline(self):
        proposal, _ = self.create_proposal()
        packet = self.write_results(proposal, candidate_cost=0.1)
        payload = json.loads(packet.read_text())
        for run in payload["runs"]:
            for task in run["tasks"]:
                task["baseline_cost"] = 0.0
        packet.write_text(json.dumps(payload), encoding="utf-8")
        result = MODULE.evaluate_proposal(
            argparse.Namespace(data_dir=self.data_dir, proposal=proposal["id"], results=packet)
        )
        self.assertEqual("rejected", result["status"])
        self.assertTrue(
            any("zero-cost baseline" in item for item in result["evaluation"]["failures"])
        )

    def test_replay_rejects_changed_suite_and_non_finite_scores(self):
        proposal, _ = self.create_proposal()
        packet = self.write_results(proposal)
        payload = json.loads(packet.read_text())
        payload["suite_sha256"] = "0" * 64
        packet.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(MODULE.LearningLoopError):
            MODULE.evaluate_proposal(
                argparse.Namespace(data_dir=self.data_dir, proposal=proposal["id"], results=packet)
            )
        payload["suite_sha256"] = proposal["suite_sha256"]
        payload["runs"][0]["tasks"][0]["candidate_score"] = float("nan")
        packet.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(MODULE.LearningLoopError):
            MODULE.evaluate_proposal(
                argparse.Namespace(data_dir=self.data_dir, proposal=proposal["id"], results=packet)
            )

    def test_evaluated_proposal_requires_explicit_approval(self):
        proposal, _ = self.create_proposal()
        with self.assertRaises(MODULE.LearningLoopError):
            MODULE.request_promotion(
                argparse.Namespace(
                    data_dir=self.data_dir,
                    candidate=None,
                    proposal=proposal["id"],
                    target_path="skills/example/SKILL.md",
                    approved_by="Ahmed Nasr",
                    approval_ref="telegram-message-12345",
                )
            )
        packet = self.write_results(proposal)
        MODULE.evaluate_proposal(
            argparse.Namespace(data_dir=self.data_dir, proposal=proposal["id"], results=packet)
        )
        result = MODULE.request_promotion(
            argparse.Namespace(
                data_dir=self.data_dir,
                candidate=None,
                proposal=proposal["id"],
                target_path="skills/example/SKILL.md",
                approved_by="Ahmed Nasr",
                approval_ref="telegram-message-12345",
            )
        )
        self.assertEqual("created", result["status"])
        self.assertEqual(proposal["id"], result["promotion_request"]["proposal_id"])

    def test_record_implementation_requires_receipt_and_records_target_hash(self):
        proposal, _ = self.create_proposal()
        packet = self.write_results(proposal)
        MODULE.evaluate_proposal(
            argparse.Namespace(data_dir=self.data_dir, proposal=proposal["id"], results=packet)
        )
        receipt = MODULE.request_promotion(
            argparse.Namespace(
                data_dir=self.data_dir,
                candidate=None,
                proposal=proposal["id"],
                target_path="skills/example/SKILL.md",
                approved_by="Ahmed Nasr",
                approval_ref="telegram-message-12345",
            )
        )["promotion_request"]
        original_workspace = MODULE.WORKSPACE
        try:
            MODULE.WORKSPACE = Path(self.temp.name)
            target = MODULE.WORKSPACE / "skills" / "example" / "SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text(
                Path(proposal["artifact_path"]).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            result = MODULE.record_implementation(
                argparse.Namespace(
                    data_dir=self.data_dir,
                    promotion_request=receipt["id"],
                    verification="Focused and regression tests passed.",
                    rollback="Restore the recorded baseline snapshot.",
                )
            )
        finally:
            MODULE.WORKSPACE = original_workspace
        self.assertEqual("created", result["status"])
        self.assertEqual(MODULE.file_sha256(target), result["implementation_record"]["target_sha256"])

    def test_record_implementation_rejects_target_not_matching_approved_artifact(self):
        proposal, _ = self.create_proposal()
        packet = self.write_results(proposal)
        MODULE.evaluate_proposal(
            argparse.Namespace(data_dir=self.data_dir, proposal=proposal["id"], results=packet)
        )
        receipt = MODULE.request_promotion(
            argparse.Namespace(
                data_dir=self.data_dir,
                proposal=proposal["id"],
                target_path="skills/example/SKILL.md",
                approved_by="Ahmed Nasr",
                approval_ref="telegram-message-12345",
            )
        )["promotion_request"]
        original_workspace = MODULE.WORKSPACE
        try:
            MODULE.WORKSPACE = Path(self.temp.name)
            target = MODULE.WORKSPACE / "skills" / "example" / "SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text("different implementation\n", encoding="utf-8")
            with self.assertRaises(MODULE.LearningLoopError):
                MODULE.record_implementation(
                    argparse.Namespace(
                        data_dir=self.data_dir,
                        promotion_request=receipt["id"],
                        verification="Focused and regression tests passed.",
                        rollback="Restore the recorded baseline snapshot.",
                    )
                )
        finally:
            MODULE.WORKSPACE = original_workspace


if __name__ == "__main__":
    unittest.main(verbosity=2)
