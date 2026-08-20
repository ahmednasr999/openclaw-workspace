#!/usr/bin/env python3
"""Deterministic, human-governed learning candidate registry."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


WORKSPACE = Path("/root/.openclaw/workspace")
DEFAULT_DATA_DIR = WORKSPACE / "data" / "learning-loop"
DEFAULT_REPORT = WORKSPACE / "reports" / "learning-loop" / "latest.md"
PATTERN_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{2,159}$")
TARGET_TYPES = {"rule", "skill-update", "new-skill", "script", "test", "solution"}
ALLOWED_EXACT_TARGETS = {"AGENTS.md", "SOUL.md", "TOOLS.md"}
ALLOWED_TARGET_PREFIXES = ("skills/", "scripts/", "tests/", "docs/solutions/")
EVAL_SPLITS = {"validation", "locked-test"}
MAX_EVAL_FILE_BYTES = 1_000_000
SECRET_PATTERNS = (
    re.compile(r"(?i)\b(?:api[_-]?key|password|passwd|secret|access[_-]?token|refresh[_-]?token)\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{12,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:sk|ghp|github_pat)_[A-Za-z0-9_-]{20,}\b"),
)


class LearningLoopError(ValueError):
    """Raised for invalid or unsafe learning-loop input."""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def digest(*parts: str, length: int = 20) -> str:
    payload = "\x1f".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:length]


def ensure_safe_text(label: str, value: str, minimum: int = 1, maximum: int = 1000) -> str:
    value = value.strip()
    if not minimum <= len(value) <= maximum:
        raise LearningLoopError(f"{label} must be {minimum}-{maximum} characters")
    if any(pattern.search(value) for pattern in SECRET_PATTERNS):
        raise LearningLoopError(f"{label} appears to contain a secret")
    if "\x00" in value:
        raise LearningLoopError(f"{label} contains a null byte")
    return value


def validate_occurred_at(value: str) -> str:
    candidate = value.strip()
    try:
        datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LearningLoopError("occurred-at must be ISO-8601") from exc
    return candidate


def validate_target_path(value: str) -> str:
    target = value.strip().replace("\\", "/")
    path = Path(target)
    if not target or path.is_absolute() or ".." in path.parts or target.startswith("./"):
        raise LearningLoopError("target-path must be a normalized relative workspace path")
    if target in ALLOWED_EXACT_TARGETS or target.startswith(ALLOWED_TARGET_PREFIXES):
        return target
    raise LearningLoopError("target-path is outside approved learning-loop targets")


def empty_registry() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "observations": [],
        "candidates": [],
        "proposals": [],
        "evaluations": [],
        "negative_evidence": [],
        "promotion_requests": [],
        "implementation_records": [],
    }


def registry_path(data_dir: Path) -> Path:
    return data_dir / "registry.json"


def load_registry(data_dir: Path) -> dict[str, Any]:
    path = registry_path(data_dir)
    if not path.exists():
        return empty_registry()
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LearningLoopError(f"cannot read registry: {exc}") from exc
    if registry.get("schema_version") not in {1, 2}:
        raise LearningLoopError("unsupported registry schema")
    if registry["schema_version"] == 1:
        registry["schema_version"] = 2
    for key in (
        "observations",
        "candidates",
        "proposals",
        "evaluations",
        "negative_evidence",
        "promotion_requests",
        "implementation_records",
    ):
        registry.setdefault(key, [])
        if not isinstance(registry.get(key), list):
            raise LearningLoopError(f"registry field {key} must be a list")
    return registry


def file_sha256(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise LearningLoopError(f"expected a regular file: {path}")
    if path.stat().st_size > MAX_EVAL_FILE_BYTES:
        raise LearningLoopError(f"file exceeds {MAX_EVAL_FILE_BYTES} bytes: {path}")
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def read_json_object(path: Path, label: str) -> tuple[dict[str, Any], str]:
    sha256 = file_sha256(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LearningLoopError(f"cannot read {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise LearningLoopError(f"{label} must be a JSON object")
    return payload, sha256


def bounded_number(
    value: Any, label: str, minimum: float, maximum: float | None = None
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise LearningLoopError(f"{label} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise LearningLoopError(f"{label} must be finite")
    if number < minimum or (maximum is not None and number > maximum):
        range_text = f"{minimum}-{maximum}" if maximum is not None else f">= {minimum}"
        raise LearningLoopError(f"{label} must be {range_text}")
    return number


def validate_eval_suite(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema_version") != 1:
        raise LearningLoopError("evaluation suite schema_version must be 1")
    if payload.get("data_policy") != "curated-sanitized":
        raise LearningLoopError("evaluation suite data_policy must be curated-sanitized")
    name = ensure_safe_text("suite name", str(payload.get("name", "")), 3, 120)
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or len(tasks) < 2 or len(tasks) > 50:
        raise LearningLoopError("evaluation suite requires 2-50 tasks")
    normalized_tasks: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise LearningLoopError(f"task {index} must be an object")
        task_id = str(task.get("id", "")).strip()
        if not RUN_ID_RE.fullmatch(task_id) or task_id in seen_ids:
            raise LearningLoopError(f"task {index} has an invalid or duplicate id")
        split = task.get("split")
        if split not in EVAL_SPLITS:
            raise LearningLoopError(f"task {task_id} split must be validation or locked-test")
        if not isinstance(task.get("critical"), bool):
            raise LearningLoopError(f"task {task_id} critical must be boolean")
        seen_ids.add(task_id)
        normalized_tasks.append(
            {"id": task_id, "split": split, "critical": task["critical"]}
        )
    splits = {task["split"] for task in normalized_tasks}
    if splits != EVAL_SPLITS:
        raise LearningLoopError("evaluation suite requires validation and locked-test tasks")
    if not any(task["critical"] for task in normalized_tasks):
        raise LearningLoopError("evaluation suite requires at least one critical task")
    thresholds = payload.get("thresholds")
    if not isinstance(thresholds, dict):
        raise LearningLoopError("evaluation suite thresholds must be an object")
    required_runs_raw = thresholds.get("required_runs")
    if isinstance(required_runs_raw, bool) or not isinstance(required_runs_raw, int):
        raise LearningLoopError("required_runs must be an integer")
    if not 2 <= required_runs_raw <= 10:
        raise LearningLoopError("required_runs must be 2-10")
    normalized_thresholds = {
        "required_runs": required_runs_raw,
        "min_absolute_improvement": bounded_number(
            thresholds.get("min_absolute_improvement"),
            "min_absolute_improvement",
            0.0,
            1.0,
        ),
        "max_candidate_cost_per_run": bounded_number(
            thresholds.get("max_candidate_cost_per_run"),
            "max_candidate_cost_per_run",
            0.0,
        ),
        "max_cost_increase_ratio": bounded_number(
            thresholds.get("max_cost_increase_ratio"),
            "max_cost_increase_ratio",
            0.0,
        ),
    }
    return {"name": name, "tasks": normalized_tasks, "thresholds": normalized_thresholds}


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp_name)


def atomic_write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp_name)


@contextlib.contextmanager
def locked_registry(data_dir: Path) -> Iterator[dict[str, Any]]:
    data_dir.mkdir(parents=True, exist_ok=True)
    lock_path = data_dir / ".lock"
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        registry = load_registry(data_dir)
        yield registry


def observation_from_args(args: argparse.Namespace) -> dict[str, Any]:
    pattern_key = args.pattern_key.strip()
    if not PATTERN_RE.fullmatch(pattern_key):
        raise LearningLoopError("pattern-key must be 3-80 lowercase letters, digits, dots, underscores, or hyphens")
    run_id = args.run_id.strip()
    if not RUN_ID_RE.fullmatch(run_id):
        raise LearningLoopError("run-id must be a stable 3-160 character identifier")
    if args.target_type not in TARGET_TYPES:
        raise LearningLoopError(f"target-type must be one of {', '.join(sorted(TARGET_TYPES))}")
    evidence = sorted({ensure_safe_text("evidence", item, 3, 500) for item in args.evidence})
    if not evidence:
        raise LearningLoopError("at least one evidence item is required")
    summary = ensure_safe_text("summary", args.summary, 20, 500)
    source = ensure_safe_text("source", args.source, 3, 500)
    verification = ensure_safe_text("verification", args.verification, 10, 1000)
    occurred_at = validate_occurred_at(args.occurred_at or now_iso())
    observation_id = "glo-" + digest(pattern_key, run_id, source, *evidence, verification)
    return {
        "id": observation_id,
        "pattern_key": pattern_key,
        "summary": summary,
        "run_id": run_id,
        "source": source,
        "evidence": evidence,
        "verification": verification,
        "target_type": args.target_type,
        "occurred_at": occurred_at,
        "captured_at": now_iso(),
    }


def capture(args: argparse.Namespace) -> dict[str, Any]:
    observation = observation_from_args(args)
    with locked_registry(args.data_dir) as registry:
        existing = next((item for item in registry["observations"] if item["id"] == observation["id"]), None)
        if existing:
            result = {"status": "existing", "observation": existing}
        else:
            registry["observations"].append(observation)
            registry["observations"].sort(key=lambda item: (item["pattern_key"], item["occurred_at"], item["id"]))
            atomic_write_json(registry_path(args.data_dir), registry)
            result = {"status": "created", "observation": observation}
    return result


def candidate_readiness(observations: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if len(observations) < 2:
        failures.append("requires at least two observations")
    if len({item.get("run_id") for item in observations}) < 2:
        failures.append("requires at least two distinct runs")
    evidence_fingerprints = {
        digest(*sorted(item.get("evidence", [])), length=32) for item in observations if item.get("evidence")
    }
    if len(evidence_fingerprints) < 2:
        failures.append("requires at least two distinct evidence sets")
    if any(not item.get("verification", "").strip() for item in observations):
        failures.append("every observation requires verification")
    target_types = {item.get("target_type") for item in observations}
    if len(target_types) != 1:
        failures.append("observations have conflicting target types")
    return not failures, failures


def build_candidates(registry: dict[str, Any]) -> tuple[list[dict[str, Any]], int, int]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for observation in registry["observations"]:
        groups.setdefault(observation["pattern_key"], []).append(observation)
    existing_by_key = {item["pattern_key"]: item for item in registry["candidates"]}
    created = 0
    updated = 0
    candidates: list[dict[str, Any]] = []
    for pattern_key, observations in sorted(groups.items()):
        observations = sorted(observations, key=lambda item: (item["occurred_at"], item["id"]))
        ready, failures = candidate_readiness(observations)
        if not ready:
            continue
        previous = existing_by_key.get(pattern_key)
        candidate = {
            "id": "glc-" + digest(pattern_key),
            "pattern_key": pattern_key,
            "title": observations[-1]["summary"],
            "target_type": observations[-1]["target_type"],
            "status": previous.get("status", "review") if previous else "review",
            "observation_ids": [item["id"] for item in observations],
            "distinct_runs": len({item["run_id"] for item in observations}),
            "distinct_evidence_sets": len({digest(*sorted(item["evidence"]), length=32) for item in observations}),
            "readiness": "eligible",
            "readiness_failures": failures,
            "created_at": previous.get("created_at", now_iso()) if previous else now_iso(),
            "updated_at": previous.get("updated_at", now_iso()) if previous else now_iso(),
        }
        if previous is None:
            created += 1
        else:
            comparable_previous = {key: value for key, value in previous.items() if key != "updated_at"}
            comparable_candidate = {key: value for key, value in candidate.items() if key != "updated_at"}
            if comparable_previous != comparable_candidate:
                candidate["updated_at"] = now_iso()
                updated += 1
        candidates.append(candidate)
    return candidates, created, updated


def render_report(registry: dict[str, Any]) -> str:
    lines = [
        "# Governed Learning Loop Review",
        "",
        f"Generated: {now_iso()}",
        "",
        f"- Observations: {len(registry['observations'])}",
        f"- Reviewable candidates: {len(registry['candidates'])}",
        f"- Bounded proposals: {len(registry['proposals'])}",
        f"- Replay evaluations: {len(registry['evaluations'])}",
        f"- Rejected evaluations retained: {len(registry['negative_evidence'])}",
        f"- Promotion requests: {len(registry['promotion_requests'])}",
        f"- Verified implementations: {len(registry['implementation_records'])}",
        "- Automatic deployments performed by this loop: 0",
        "",
    ]
    if not registry["candidates"]:
        lines.extend(["No candidate has enough independent evidence yet.", ""])
        return "\n".join(lines)
    observations_by_id = {item["id"]: item for item in registry["observations"]}
    for candidate in registry["candidates"]:
        lines.extend(
            [
                f"## {candidate['id']} - {candidate['pattern_key']}",
                "",
                f"- Status: {candidate['status']}",
                f"- Target type: {candidate['target_type']}",
                f"- Method: {candidate['title']}",
                f"- Evidence: {candidate['distinct_runs']} distinct runs, {candidate['distinct_evidence_sets']} distinct evidence sets",
                (
                    "- Decision: implemented and verified; rollback evidence recorded"
                    if candidate["status"] == "verified"
                    else "- Decision required: approve exact target, reject, or collect more evidence"
                ),
                "",
                "### Evidence",
                "",
            ]
        )
        for observation_id in candidate["observation_ids"]:
            item = observations_by_id[observation_id]
            lines.append(f"- `{item['run_id']}`: {item['verification']} Source: `{item['source']}`.")
        lines.append("")
        for proposal in [item for item in registry["proposals"] if item["candidate_id"] == candidate["id"]]:
            lines.extend(
                [
                    f"### Proposal {proposal['id']}",
                    "",
                    f"- Status: {proposal['status']}",
                    f"- Target: `{proposal['target_path']}`",
                    f"- Edits: {len(proposal['edits'])}",
                    f"- Suite: {proposal['suite']['name']} ({len(proposal['suite']['tasks'])} tasks)",
                    "- Automatic deployment: disabled",
                    "",
                ]
            )
            for evaluation in [
                item for item in registry["evaluations"] if item["proposal_id"] == proposal["id"]
            ]:
                lines.append(
                    f"- Evaluation `{evaluation['id']}`: {evaluation['status']}; "
                    f"improvement {evaluation['metrics']['absolute_improvement']:.4f}; "
                    f"runs {evaluation['metrics']['runs']}."
                )
            lines.append("")
    return "\n".join(lines)


def build(args: argparse.Namespace) -> dict[str, Any]:
    with locked_registry(args.data_dir) as registry:
        candidates, created, updated = build_candidates(registry)
        registry["candidates"] = candidates
        atomic_write_json(registry_path(args.data_dir), registry)
        report = render_report(registry)
        atomic_write_text(args.report, report)
        return {
            "status": "ok",
            "observations": len(registry["observations"]),
            "candidates": len(candidates),
            "created": created,
            "updated": updated,
            "report": str(args.report),
        }


def find_candidate(registry: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    candidate = next((item for item in registry["candidates"] if item["id"] == candidate_id), None)
    if not candidate:
        raise LearningLoopError(f"candidate not found: {candidate_id}")
    return candidate


def find_proposal(registry: dict[str, Any], proposal_id: str) -> dict[str, Any]:
    proposal = next((item for item in registry["proposals"] if item["id"] == proposal_id), None)
    if not proposal:
        raise LearningLoopError(f"proposal not found: {proposal_id}")
    return proposal


def validate_candidate(args: argparse.Namespace) -> dict[str, Any]:
    registry = load_registry(args.data_dir)
    candidate = find_candidate(registry, args.candidate)
    observations_by_id = {item["id"]: item for item in registry["observations"]}
    try:
        observations = [observations_by_id[item] for item in candidate["observation_ids"]]
    except KeyError as exc:
        raise LearningLoopError(f"candidate references missing observation: {exc.args[0]}") from exc
    ready, failures = candidate_readiness(observations)
    if candidate.get("readiness") != "eligible":
        failures.append("candidate readiness is not eligible")
        ready = False
    result = {"status": "valid" if ready else "invalid", "candidate": candidate["id"], "failures": failures}
    if not ready:
        raise LearningLoopError(json.dumps(result, sort_keys=True))
    return result


def create_proposal(args: argparse.Namespace) -> dict[str, Any]:
    target_path = validate_target_path(args.target_path)
    edits = sorted({ensure_safe_text("edit", item, 5, 300) for item in args.edit})
    if not 1 <= len(edits) <= 4:
        raise LearningLoopError("a proposal must contain 1-4 distinct edits")
    suite_payload, suite_sha256 = read_json_object(args.suite, "evaluation suite")
    suite = validate_eval_suite(suite_payload)
    artifact_sha256 = file_sha256(args.artifact)
    with locked_registry(args.data_dir) as registry:
        candidate = find_candidate(registry, args.candidate)
        observations_by_id = {item["id"]: item for item in registry["observations"]}
        observations = [observations_by_id[item] for item in candidate["observation_ids"]]
        ready, failures = candidate_readiness(observations)
        if not ready or candidate.get("readiness") != "eligible":
            raise LearningLoopError("candidate is not eligible: " + "; ".join(failures))
        proposal_id = "glv-" + digest(
            candidate["id"], target_path, artifact_sha256, suite_sha256, *edits
        )
        existing = next((item for item in registry["proposals"] if item["id"] == proposal_id), None)
        if existing:
            return {"status": "existing", "proposal": existing}
        proposal = {
            "id": proposal_id,
            "candidate_id": candidate["id"],
            "target_path": target_path,
            "artifact_path": str(args.artifact),
            "artifact_sha256": artifact_sha256,
            "suite_path": str(args.suite),
            "suite_sha256": suite_sha256,
            "suite": suite,
            "edits": edits,
            "status": "awaiting-evaluation",
            "automatic_deployment": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        registry["proposals"].append(proposal)
        registry["proposals"].sort(key=lambda item: (item["created_at"], item["id"]))
        candidate["status"] = "evaluation-pending"
        candidate["updated_at"] = now_iso()
        atomic_write_json(registry_path(args.data_dir), registry)
        return {"status": "created", "proposal": proposal}


def normalize_evaluation_packet(
    payload: dict[str, Any], proposal: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    if payload.get("schema_version") != 1:
        raise LearningLoopError("evaluation packet schema_version must be 1")
    if payload.get("proposal_id") != proposal["id"]:
        raise LearningLoopError("evaluation packet proposal_id does not match")
    if payload.get("suite_sha256") != proposal["suite_sha256"]:
        raise LearningLoopError("evaluation packet suite hash does not match the locked suite")
    runs = payload.get("runs")
    if not isinstance(runs, list):
        raise LearningLoopError("evaluation packet runs must be a list")
    suite_tasks = {task["id"]: task for task in proposal["suite"]["tasks"]}
    thresholds = proposal["suite"]["thresholds"]
    required_runs = thresholds["required_runs"]
    if not required_runs <= len(runs) <= 20:
        raise LearningLoopError(f"evaluation packet requires {required_runs}-20 runs")
    normalized_runs: list[dict[str, Any]] = []
    failures: list[str] = []
    run_ids: set[str] = set()
    total_baseline_score = 0.0
    total_candidate_score = 0.0
    total_task_results = 0
    for run_index, run in enumerate(runs):
        if not isinstance(run, dict):
            raise LearningLoopError(f"run {run_index} must be an object")
        run_id = str(run.get("run_id", "")).strip()
        if not RUN_ID_RE.fullmatch(run_id) or run_id in run_ids:
            raise LearningLoopError(f"run {run_index} has an invalid or duplicate run_id")
        run_ids.add(run_id)
        task_results = run.get("tasks")
        if not isinstance(task_results, list):
            raise LearningLoopError(f"run {run_id} tasks must be a list")
        task_ids = [str(item.get("task_id", "")) for item in task_results if isinstance(item, dict)]
        if len(task_ids) != len(task_results) or set(task_ids) != set(suite_tasks) or len(task_ids) != len(set(task_ids)):
            raise LearningLoopError(f"run {run_id} must contain every locked suite task exactly once")
        normalized_tasks: list[dict[str, Any]] = []
        run_baseline_score = 0.0
        run_candidate_score = 0.0
        run_baseline_cost = 0.0
        run_candidate_cost = 0.0
        locked_baseline: list[float] = []
        locked_candidate: list[float] = []
        for item in task_results:
            task_id = item["task_id"]
            task = suite_tasks[task_id]
            baseline_score = bounded_number(
                item.get("baseline_score"), f"{run_id}/{task_id} baseline_score", 0.0, 1.0
            )
            candidate_score = bounded_number(
                item.get("candidate_score"), f"{run_id}/{task_id} candidate_score", 0.0, 1.0
            )
            baseline_cost = bounded_number(
                item.get("baseline_cost"), f"{run_id}/{task_id} baseline_cost", 0.0
            )
            candidate_cost = bounded_number(
                item.get("candidate_cost"), f"{run_id}/{task_id} candidate_cost", 0.0
            )
            if task["critical"] and candidate_score < baseline_score:
                failures.append(
                    f"critical regression in {run_id}/{task_id}: {candidate_score:.4f} < {baseline_score:.4f}"
                )
            if task["split"] == "locked-test":
                locked_baseline.append(baseline_score)
                locked_candidate.append(candidate_score)
            run_baseline_score += baseline_score
            run_candidate_score += candidate_score
            run_baseline_cost += baseline_cost
            run_candidate_cost += candidate_cost
            total_baseline_score += baseline_score
            total_candidate_score += candidate_score
            total_task_results += 1
            normalized_tasks.append(
                {
                    "task_id": task_id,
                    "baseline_score": baseline_score,
                    "candidate_score": candidate_score,
                    "baseline_cost": baseline_cost,
                    "candidate_cost": candidate_cost,
                }
            )
        task_count = len(normalized_tasks)
        run_improvement = (run_candidate_score - run_baseline_score) / task_count
        if run_improvement < thresholds["min_absolute_improvement"]:
            failures.append(
                f"run {run_id} improvement {run_improvement:.4f} is below {thresholds['min_absolute_improvement']:.4f}"
            )
        if sum(locked_candidate) / len(locked_candidate) < sum(locked_baseline) / len(locked_baseline):
            failures.append(f"locked-test regression in run {run_id}")
        if run_candidate_cost > thresholds["max_candidate_cost_per_run"]:
            failures.append(
                f"run {run_id} candidate cost {run_candidate_cost:.4f} exceeds {thresholds['max_candidate_cost_per_run']:.4f}"
            )
        if run_baseline_cost == 0.0:
            if run_candidate_cost > 0.0:
                failures.append(f"run {run_id} adds cost above a zero-cost baseline")
        elif run_candidate_cost / run_baseline_cost > thresholds["max_cost_increase_ratio"]:
            failures.append(
                f"run {run_id} cost ratio {run_candidate_cost / run_baseline_cost:.4f} exceeds {thresholds['max_cost_increase_ratio']:.4f}"
            )
        normalized_runs.append(
            {
                "run_id": run_id,
                "tasks": sorted(normalized_tasks, key=lambda item: item["task_id"]),
                "baseline_mean": run_baseline_score / task_count,
                "candidate_mean": run_candidate_score / task_count,
                "improvement": run_improvement,
                "baseline_cost": run_baseline_cost,
                "candidate_cost": run_candidate_cost,
            }
        )
    overall_improvement = (total_candidate_score - total_baseline_score) / total_task_results
    if overall_improvement < thresholds["min_absolute_improvement"]:
        failures.append(
            f"overall improvement {overall_improvement:.4f} is below {thresholds['min_absolute_improvement']:.4f}"
        )
    metrics = {
        "runs": len(normalized_runs),
        "task_results": total_task_results,
        "baseline_mean": total_baseline_score / total_task_results,
        "candidate_mean": total_candidate_score / total_task_results,
        "absolute_improvement": overall_improvement,
        "baseline_cost": sum(run["baseline_cost"] for run in normalized_runs),
        "candidate_cost": sum(run["candidate_cost"] for run in normalized_runs),
    }
    return normalized_runs, sorted(set(failures)), metrics


def evaluate_proposal(args: argparse.Namespace) -> dict[str, Any]:
    packet, packet_sha256 = read_json_object(args.results, "evaluation packet")
    with locked_registry(args.data_dir) as registry:
        proposal = find_proposal(registry, args.proposal)
        normalized_runs, failures, metrics = normalize_evaluation_packet(packet, proposal)
        evaluation_id = "gle-" + digest(proposal["id"], packet_sha256)
        existing = next((item for item in registry["evaluations"] if item["id"] == evaluation_id), None)
        if existing:
            return {"status": "existing", "evaluation": existing}
        accepted = not failures
        evaluation = {
            "id": evaluation_id,
            "proposal_id": proposal["id"],
            "results_path": str(args.results),
            "results_sha256": packet_sha256,
            "suite_sha256": proposal["suite_sha256"],
            "status": "accepted" if accepted else "rejected",
            "metrics": metrics,
            "failures": failures,
            "run_ids": [run["run_id"] for run in normalized_runs],
            "evaluated_at": now_iso(),
            "automatic_deployment": False,
        }
        registry["evaluations"].append(evaluation)
        proposal["status"] = "evaluation-passed" if accepted else "rejected"
        proposal["updated_at"] = now_iso()
        if not accepted:
            registry["negative_evidence"].append(
                {
                    "id": "gln-" + digest(evaluation_id, *failures),
                    "proposal_id": proposal["id"],
                    "evaluation_id": evaluation_id,
                    "failures": failures,
                    "results_sha256": packet_sha256,
                    "recorded_at": now_iso(),
                }
            )
        atomic_write_json(registry_path(args.data_dir), registry)
        return {"status": "accepted" if accepted else "rejected", "evaluation": evaluation}


def request_promotion(args: argparse.Namespace) -> dict[str, Any]:
    target_path = validate_target_path(args.target_path)
    approved_by = ensure_safe_text("approved-by", args.approved_by, 3, 100)
    approval_ref = ensure_safe_text("approval-ref", args.approval_ref, 6, 300)
    with locked_registry(args.data_dir) as registry:
        proposal_id = getattr(args, "proposal", None)
        if not proposal_id:
            raise LearningLoopError("promotion requires an evaluation-passed proposal")
        proposal = find_proposal(registry, proposal_id)
        if proposal["target_path"] != target_path:
            raise LearningLoopError("approved target does not match the evaluated proposal")
        accepted = [
            item
            for item in registry["evaluations"]
            if item["proposal_id"] == proposal["id"] and item["status"] == "accepted"
        ]
        if proposal.get("status") != "evaluation-passed" or not accepted:
            raise LearningLoopError("proposal has not passed replay evaluation")
        evaluation = sorted(accepted, key=lambda item: item["evaluated_at"])[-1]
        candidate = find_candidate(registry, proposal["candidate_id"])
        observations_by_id = {item["id"]: item for item in registry["observations"]}
        observations = [observations_by_id[item] for item in candidate["observation_ids"]]
        ready, failures = candidate_readiness(observations)
        if not ready or candidate.get("readiness") != "eligible":
            raise LearningLoopError("candidate is not eligible: " + "; ".join(failures))
        request_id = "glp-" + digest(
            candidate["id"], proposal_id, target_path, approved_by, approval_ref
        )
        existing = next((item for item in registry["promotion_requests"] if item["id"] == request_id), None)
        if existing:
            return {"status": "existing", "promotion_request": existing, "target_written": False}
        receipt = {
            "id": request_id,
            "candidate_id": candidate["id"],
            "proposal_id": proposal["id"],
            "evaluation_id": evaluation["id"],
            "target_path": target_path,
            "approved_by": approved_by,
            "approval_ref": approval_ref,
            "status": "promotion-requested",
            "requested_at": now_iso(),
            "target_written": False,
        }
        registry["promotion_requests"].append(receipt)
        candidate["status"] = "promotion-requested"
        candidate["updated_at"] = now_iso()
        atomic_write_json(registry_path(args.data_dir), registry)
        return {"status": "created", "promotion_request": receipt, "target_written": False}


def record_implementation(args: argparse.Namespace) -> dict[str, Any]:
    verification = ensure_safe_text("verification", args.verification, 10, 1000)
    rollback = ensure_safe_text("rollback", args.rollback, 10, 1000)
    with locked_registry(args.data_dir) as registry:
        receipt = next(
            (item for item in registry["promotion_requests"] if item["id"] == args.promotion_request),
            None,
        )
        if not receipt:
            raise LearningLoopError(f"promotion request not found: {args.promotion_request}")
        proposal_id = receipt.get("proposal_id")
        evaluation_id = receipt.get("evaluation_id")
        if not proposal_id or not evaluation_id:
            raise LearningLoopError("legacy candidate-only receipt cannot record implementation")
        proposal = find_proposal(registry, proposal_id)
        if not any(
            item["id"] == evaluation_id
            and item["proposal_id"] == proposal_id
            and item["status"] == "accepted"
            for item in registry["evaluations"]
        ):
            raise LearningLoopError("promotion receipt is not bound to an accepted evaluation")
        target = WORKSPACE / receipt["target_path"]
        target_sha256 = file_sha256(target)
        if target_sha256 != proposal["artifact_sha256"]:
            raise LearningLoopError("implemented target does not match the approved artifact hash")
        record_id = "gli-" + digest(receipt["id"], target_sha256, verification, rollback)
        existing = next(
            (item for item in registry["implementation_records"] if item["id"] == record_id),
            None,
        )
        if existing:
            return {"status": "existing", "implementation_record": existing}
        record = {
            "id": record_id,
            "promotion_request_id": receipt["id"],
            "candidate_id": receipt["candidate_id"],
            "proposal_id": receipt.get("proposal_id"),
            "evaluation_id": receipt.get("evaluation_id"),
            "target_path": receipt["target_path"],
            "target_sha256": target_sha256,
            "verification": verification,
            "rollback": rollback,
            "status": "verified",
            "recorded_at": now_iso(),
        }
        registry["implementation_records"].append(record)
        receipt["status"] = "implemented-verified"
        candidate = find_candidate(registry, receipt["candidate_id"])
        candidate["status"] = "verified"
        candidate["updated_at"] = now_iso()
        proposal["status"] = "verified"
        proposal["updated_at"] = now_iso()
        atomic_write_json(registry_path(args.data_dir), registry)
        return {"status": "created", "implementation_record": record}


def status(args: argparse.Namespace) -> dict[str, Any]:
    registry = load_registry(args.data_dir)
    return {
        "status": "ok",
        "observations": len(registry["observations"]),
        "candidates": len(registry["candidates"]),
        "proposals": len(registry["proposals"]),
        "evaluations": len(registry["evaluations"]),
        "rejected_evaluations": sum(
            item.get("status") == "rejected" for item in registry["evaluations"]
        ),
        "negative_evidence": len(registry["negative_evidence"]),
        "promotion_requests": len(registry["promotion_requests"]),
        "verified_implementations": len(registry["implementation_records"]),
        "automatic_deployments": 0,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    root.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    subparsers = root.add_subparsers(dest="command", required=True)

    capture_parser = subparsers.add_parser("capture", help="record one verified observation")
    capture_parser.add_argument("--pattern-key", required=True)
    capture_parser.add_argument("--summary", required=True)
    capture_parser.add_argument("--run-id", required=True)
    capture_parser.add_argument("--source", required=True)
    capture_parser.add_argument("--evidence", action="append", required=True)
    capture_parser.add_argument("--verification", required=True)
    capture_parser.add_argument("--target-type", choices=sorted(TARGET_TYPES), required=True)
    capture_parser.add_argument("--occurred-at")
    capture_parser.set_defaults(handler=capture)

    build_parser = subparsers.add_parser("build", help="build reviewable candidates and report")
    build_parser.set_defaults(handler=build)

    validate_parser = subparsers.add_parser("validate", help="validate one candidate")
    validate_parser.add_argument("--candidate", required=True)
    validate_parser.set_defaults(handler=validate_candidate)

    proposal_parser = subparsers.add_parser(
        "create-proposal", help="lock a bounded candidate artifact and curated replay suite"
    )
    proposal_parser.add_argument("--candidate", required=True)
    proposal_parser.add_argument("--target-path", required=True)
    proposal_parser.add_argument("--artifact", type=Path, required=True)
    proposal_parser.add_argument("--suite", type=Path, required=True)
    proposal_parser.add_argument("--edit", action="append", required=True)
    proposal_parser.set_defaults(handler=create_proposal)

    evaluate_parser = subparsers.add_parser(
        "evaluate-proposal", help="apply replay, regression, and cost gates to a result packet"
    )
    evaluate_parser.add_argument("--proposal", required=True)
    evaluate_parser.add_argument("--results", type=Path, required=True)
    evaluate_parser.set_defaults(handler=evaluate_proposal)

    promotion_parser = subparsers.add_parser("request-promotion", help="record explicit approval without writing the target")
    promotion_parser.add_argument("--proposal", required=True)
    promotion_parser.add_argument("--target-path", required=True)
    promotion_parser.add_argument("--approved-by", required=True)
    promotion_parser.add_argument("--approval-ref", required=True)
    promotion_parser.set_defaults(handler=request_promotion)

    implementation_parser = subparsers.add_parser(
        "record-implementation", help="record verified implementation evidence after an approved change"
    )
    implementation_parser.add_argument("--promotion-request", required=True)
    implementation_parser.add_argument("--verification", required=True)
    implementation_parser.add_argument("--rollback", required=True)
    implementation_parser.set_defaults(handler=record_implementation)

    status_parser = subparsers.add_parser("status", help="show registry counts")
    status_parser.set_defaults(handler=status)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        result = args.handler(args)
    except LearningLoopError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
