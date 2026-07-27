from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "production_workflow_contract.py"
SPEC = importlib.util.spec_from_file_location("production_workflow_contract", SCRIPT)
assert SPEC and SPEC.loader
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)


class StageWorkflowTests(unittest.TestCase):
    def create(self, root: Path, *, inputs: dict | None = None):
        return contract.StageWorkflow.create(
            root,
            workflow="fixture",
            run_id="run-1",
            stages=["source", "validate", "approval"],
            inputs=inputs or {"slot": "1500"},
            max_attempts=2,
        )

    def test_completed_stage_is_reused_without_another_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workflow = self.create(Path(tmp))
            first, reused = workflow.run_stage("source", lambda: {"items": [1, 2]})
            second, reused_again = workflow.run_stage(
                "source",
                lambda: self.fail("completed stage should not execute again"),
            )
            self.assertFalse(reused)
            self.assertTrue(reused_again)
            self.assertEqual(first, second)
            self.assertEqual(workflow.manifest["stages"]["source"]["attempts"], 1)

    def test_resume_rejects_input_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create(root)
            with self.assertRaises(contract.WorkflowError):
                contract.StageWorkflow.create(
                    root,
                    workflow="fixture",
                    run_id="run-1",
                    stages=["source", "validate", "approval"],
                    inputs={"slot": "1100"},
                )

    def test_run_id_and_stage_names_cannot_escape_state_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(contract.WorkflowError, "run_id"):
                contract.StageWorkflow.create(
                    root,
                    workflow="fixture",
                    run_id="../escape",
                    stages=["source"],
                    inputs={},
                )
            with self.assertRaisesRegex(contract.WorkflowError, "stage"):
                contract.StageWorkflow.create(
                    root,
                    workflow="fixture",
                    run_id="run-1",
                    stages=["../source"],
                    inputs={},
                )

    def test_corrupt_completed_stage_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workflow = self.create(Path(tmp))
            workflow.run_stage("source", lambda: {"items": [1]})
            workflow.stage_output_path("source").write_text('{"items":[]}\n', encoding="utf-8")
            with self.assertRaisesRegex(contract.WorkflowError, "hash mismatch"):
                workflow.start_stage("source")
            self.assertEqual(workflow.manifest["status"], "exhausted")

    def test_failure_is_resumable_once_then_exhausted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = self.create(root)
            for expected_status in ("blocked", "exhausted"):
                with self.assertRaisesRegex(RuntimeError, "injected"):
                    workflow.run_stage(
                        "source",
                        lambda: (_ for _ in ()).throw(RuntimeError("injected")),
                    )
                self.assertEqual(workflow.manifest["status"], expected_status)
            with self.assertRaises(contract.WorkflowExhausted):
                workflow.start_stage("source")
            self.assertEqual(workflow.manifest["stages"]["source"]["attempts"], 2)

    def test_find_resumable_uses_matching_inputs_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = self.create(root)
            workflow.run_stage("source", lambda: {"items": [1]})
            found = contract.StageWorkflow.find_resumable(
                root,
                workflow="fixture",
                inputs={"slot": "1500"},
                run_id_prefix="run",
            )
            missing = contract.StageWorkflow.find_resumable(
                root,
                workflow="fixture",
                inputs={"slot": "1100"},
            )
            self.assertEqual(found.manifest["run_id"], "run-1")
            self.assertIsNone(missing)

    def test_artifact_hashes_and_terminal_state_are_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = self.create(root)
            for stage in workflow.manifest["stage_order"]:
                workflow.run_stage(stage, lambda stage=stage: {"stage": stage})
            artifact = root / "artifact.txt"
            artifact.write_text("evidence\n", encoding="utf-8")
            workflow.record_artifacts({"report": artifact, "optional": None})
            workflow.record_judge({"ok": True, "failures": []})
            workflow.finish("approval_required", "awaiting explicit approval")
            persisted = json.loads(workflow.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["status"], "approval_required")
            self.assertEqual(persisted["artifacts"]["report"]["sha256"], contract.sha256_file(artifact))
            self.assertTrue(persisted["judge"]["ok"])


if __name__ == "__main__":
    unittest.main()
