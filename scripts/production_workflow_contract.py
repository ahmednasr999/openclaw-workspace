#!/usr/bin/env python3
"""Reusable persisted-stage contract for bounded production workflows."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
TERMINAL_STATES = {
    "success",
    "clean_noop",
    "blocked",
    "approval_required",
    "exhausted",
}
RESUMABLE_STATES = {"running", "blocked"}
SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SAFE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")


class WorkflowError(RuntimeError):
    """Base error for invalid workflow state or evidence."""


class WorkflowExhausted(WorkflowError):
    """Raised when a stage has consumed its bounded attempt budget."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_bytes(path, canonical_json_bytes(value))


class StageWorkflow:
    """Persist ordered stage evidence with idempotent resume semantics."""

    def __init__(self, run_dir: Path, manifest: dict[str, Any]):
        self.run_dir = run_dir
        self.manifest_path = run_dir / "checkpoint.json"
        self.manifest = manifest
        self._validate_manifest()

    @classmethod
    def create(
        cls,
        root: Path,
        *,
        workflow: str,
        run_id: str,
        stages: list[str] | tuple[str, ...],
        inputs: dict[str, Any],
        max_attempts: int = 2,
    ) -> "StageWorkflow":
        stage_names = list(stages)
        if not SAFE_NAME.fullmatch(workflow):
            raise WorkflowError("workflow must be a safe identifier")
        if not SAFE_RUN_ID.fullmatch(run_id) or run_id in {".", ".."}:
            raise WorkflowError("run_id must be a safe path component")
        if not stage_names or len(stage_names) != len(set(stage_names)):
            raise WorkflowError("stages must be a non-empty unique ordered list")
        if any(not SAFE_NAME.fullmatch(stage) for stage in stage_names):
            raise WorkflowError("each stage must be a safe identifier")
        if max_attempts < 1:
            raise WorkflowError("max_attempts must be positive")
        run_dir = root / run_id
        manifest_path = run_dir / "checkpoint.json"
        if manifest_path.exists():
            existing = cls.open(run_dir)
            existing.assert_inputs(inputs)
            if existing.manifest["workflow"] != workflow:
                raise WorkflowError("existing workflow name does not match")
            if existing.manifest["stage_order"] != stage_names:
                raise WorkflowError("existing stage order does not match")
            return existing
        if run_dir.exists() and any(run_dir.iterdir()):
            raise WorkflowError(f"run directory is not empty: {run_dir}")
        now = utc_now()
        manifest: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "workflow": workflow,
            "run_id": run_id,
            "status": "running",
            "created_at": now,
            "updated_at": now,
            "max_attempts_per_stage": max_attempts,
            "inputs": inputs,
            "input_sha256": sha256_bytes(canonical_json_bytes(inputs)),
            "stage_order": stage_names,
            "stages": {
                stage: {
                    "status": "pending",
                    "attempts": 0,
                    "output": None,
                    "output_sha256": None,
                    "started_at": None,
                    "completed_at": None,
                    "error": None,
                    "failure_classification": None,
                }
                for stage in stage_names
            },
            "artifacts": {},
            "judge": None,
            "terminal_reason": None,
        }
        run_dir.mkdir(parents=True, exist_ok=True)
        atomic_write_json(manifest_path, manifest)
        return cls(run_dir, manifest)

    @classmethod
    def open(cls, run_dir: Path) -> "StageWorkflow":
        manifest_path = run_dir / "checkpoint.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise WorkflowError(f"cannot read checkpoint {manifest_path}: {exc}") from exc
        if not isinstance(manifest, dict):
            raise WorkflowError("checkpoint must be a JSON object")
        return cls(run_dir, manifest)

    @classmethod
    def find_resumable(
        cls,
        root: Path,
        *,
        workflow: str,
        inputs: dict[str, Any],
        run_id_prefix: str | None = None,
    ) -> "StageWorkflow | None":
        if not root.exists():
            return None
        input_sha = sha256_bytes(canonical_json_bytes(inputs))
        matches: list[StageWorkflow] = []
        for checkpoint in root.glob("*/checkpoint.json"):
            try:
                candidate = cls.open(checkpoint.parent)
            except WorkflowError:
                continue
            manifest = candidate.manifest
            if manifest.get("workflow") != workflow:
                continue
            if manifest.get("input_sha256") != input_sha:
                continue
            if manifest.get("status") not in RESUMABLE_STATES:
                continue
            if run_id_prefix and not str(manifest.get("run_id", "")).startswith(run_id_prefix):
                continue
            matches.append(candidate)
        if not matches:
            return None
        return max(
            matches,
            key=lambda item: (
                str(item.manifest.get("updated_at", "")),
                str(item.manifest.get("run_id", "")),
            ),
        )

    def _validate_manifest(self) -> None:
        manifest = self.manifest
        if manifest.get("schema_version") != SCHEMA_VERSION:
            raise WorkflowError("unsupported checkpoint schema")
        run_id = str(manifest.get("run_id") or "")
        if (
            not SAFE_RUN_ID.fullmatch(run_id)
            or run_id in {".", ".."}
            or self.run_dir.name != run_id
        ):
            raise WorkflowError("checkpoint run_id is invalid or mismatched")
        if not SAFE_NAME.fullmatch(str(manifest.get("workflow") or "")):
            raise WorkflowError("checkpoint workflow name is invalid")
        order = manifest.get("stage_order")
        stages = manifest.get("stages")
        if not isinstance(order, list) or not order or len(order) != len(set(order)):
            raise WorkflowError("invalid stage order")
        if any(not isinstance(stage, str) or not SAFE_NAME.fullmatch(stage) for stage in order):
            raise WorkflowError("invalid stage name")
        if not isinstance(stages, dict) or set(stages) != set(order):
            raise WorkflowError("checkpoint stages do not match stage order")
        expected_input_sha = sha256_bytes(canonical_json_bytes(manifest.get("inputs")))
        if manifest.get("input_sha256") != expected_input_sha:
            raise WorkflowError("checkpoint input hash mismatch")

    def _persist(self) -> None:
        self.manifest["updated_at"] = utc_now()
        atomic_write_json(self.manifest_path, self.manifest)

    def assert_inputs(self, inputs: dict[str, Any]) -> None:
        actual = sha256_bytes(canonical_json_bytes(inputs))
        if actual != self.manifest.get("input_sha256"):
            raise WorkflowError("resume inputs do not match the checkpoint")

    def stage_output_path(self, stage: str) -> Path:
        self._stage(stage)
        return self.run_dir / "stages" / f"{stage}.json"

    def _stage(self, stage: str) -> dict[str, Any]:
        try:
            value = self.manifest["stages"][stage]
        except KeyError as exc:
            raise WorkflowError(f"unknown stage: {stage}") from exc
        if not isinstance(value, dict):
            raise WorkflowError(f"invalid stage record: {stage}")
        return value

    def start_stage(self, stage: str) -> bool:
        record = self._stage(stage)
        if record.get("status") == "completed":
            try:
                self.load_stage(stage)
            except WorkflowError as exc:
                self.finish(
                    "exhausted",
                    f"{stage} completed evidence is invalid and immutable: {exc}",
                )
                raise
            return False
        index = self.manifest["stage_order"].index(stage)
        incomplete = [
            predecessor
            for predecessor in self.manifest["stage_order"][:index]
            if self._stage(predecessor).get("status") != "completed"
        ]
        if incomplete:
            raise WorkflowError(
                f"cannot start {stage}; incomplete predecessors: {', '.join(incomplete)}"
            )
        attempts = int(record.get("attempts", 0))
        maximum = int(self.manifest["max_attempts_per_stage"])
        if attempts >= maximum:
            self.finish("exhausted", f"{stage} exhausted after {attempts} attempts")
            raise WorkflowExhausted(self.manifest["terminal_reason"])
        record.update(
            {
                "status": "running",
                "attempts": attempts + 1,
                "started_at": utc_now(),
                "completed_at": None,
                "error": None,
                "failure_classification": None,
            }
        )
        self.manifest["status"] = "running"
        self.manifest["terminal_reason"] = None
        self._persist()
        return True

    def complete_stage(self, stage: str, output: Any) -> Path:
        record = self._stage(stage)
        if record.get("status") != "running":
            raise WorkflowError(f"stage is not running: {stage}")
        output_path = self.stage_output_path(stage)
        if output_path.exists():
            raise WorkflowError(f"refusing to overwrite stage evidence: {output_path}")
        payload = canonical_json_bytes(output)
        atomic_write_bytes(output_path, payload)
        record.update(
            {
                "status": "completed",
                "output": str(output_path),
                "output_sha256": sha256_bytes(payload),
                "completed_at": utc_now(),
                "error": None,
                "failure_classification": None,
            }
        )
        self._persist()
        return output_path

    def fail_stage(
        self,
        stage: str,
        error: str,
        *,
        classification: str = "transient",
    ) -> None:
        record = self._stage(stage)
        if record.get("status") != "running":
            raise WorkflowError(f"stage is not running: {stage}")
        attempts = int(record.get("attempts", 0))
        maximum = int(self.manifest["max_attempts_per_stage"])
        record.update(
            {
                "status": "failed",
                "error": str(error),
                "failure_classification": classification,
            }
        )
        if attempts >= maximum:
            self.manifest["status"] = "exhausted"
            self.manifest["terminal_reason"] = (
                f"{stage} exhausted after {attempts} attempts: {error}"
            )
        else:
            self.manifest["status"] = "blocked"
            self.manifest["terminal_reason"] = f"{stage} failed: {error}"
        self._persist()

    def load_stage(self, stage: str) -> Any:
        record = self._stage(stage)
        if record.get("status") != "completed":
            raise WorkflowError(f"stage is not completed: {stage}")
        output = record.get("output")
        if not output:
            raise WorkflowError(f"stage output is missing: {stage}")
        path = Path(str(output))
        if path != self.stage_output_path(stage):
            raise WorkflowError(f"stage output path mismatch: {stage}")
        if not path.exists():
            raise WorkflowError(f"stage output file is missing: {path}")
        actual_hash = sha256_file(path)
        if actual_hash != record.get("output_sha256"):
            raise WorkflowError(f"stage output hash mismatch: {stage}")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise WorkflowError(f"stage output is invalid JSON: {stage}: {exc}") from exc

    def run_stage(self, stage: str, action) -> tuple[Any, bool]:
        if not self.start_stage(stage):
            return self.load_stage(stage), True
        try:
            output = action()
            self.complete_stage(stage, output)
            return output, False
        except Exception as exc:
            self.fail_stage(stage, str(exc), classification=exc.__class__.__name__)
            raise

    def record_artifacts(self, artifacts: dict[str, Path | str | None]) -> None:
        evidence: dict[str, dict[str, Any] | None] = {}
        for name, raw_path in artifacts.items():
            if raw_path is None:
                evidence[name] = None
                continue
            path = Path(raw_path)
            if not path.exists() or not path.is_file():
                raise WorkflowError(f"artifact is missing: {name}: {path}")
            evidence[name] = {
                "path": str(path),
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
            }
        self.manifest["artifacts"] = evidence
        self._persist()

    def record_judge(self, result: dict[str, Any]) -> None:
        self.manifest["judge"] = result
        self._persist()

    def finish(self, status: str, reason: str) -> None:
        if status not in TERMINAL_STATES:
            raise WorkflowError(f"invalid terminal state: {status}")
        if status in {"success", "approval_required"}:
            incomplete = [
                stage
                for stage in self.manifest["stage_order"]
                if self._stage(stage).get("status") != "completed"
            ]
            if incomplete:
                raise WorkflowError(
                    f"cannot finish {status}; incomplete stages: {', '.join(incomplete)}"
                )
        self.manifest["status"] = status
        self.manifest["terminal_reason"] = reason
        self._persist()

    def completed_stages(self) -> list[str]:
        return [
            stage
            for stage in self.manifest["stage_order"]
            if self._stage(stage).get("status") == "completed"
        ]
