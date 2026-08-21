#!/usr/bin/env python3
"""Deterministic evidence-to-experiment bridge for governed product learning."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


WORKSPACE = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = WORKSPACE / "config" / "governed-product-learning.json"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")
SECRET_PATTERNS = (
    re.compile(r"(?i)\b(?:api[_-]?key|password|secret|access[_-]?token)\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{12,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


class ProductLearningError(ValueError):
    """Raised when an input violates the governed-learning contract."""


def file_sha256(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise ProductLearningError(f"expected a regular file: {path}")
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def digest(*parts: str, length: int = 20) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:length]


def read_json_object(path: Path, label: str) -> tuple[dict[str, Any], str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProductLearningError(f"cannot read {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ProductLearningError(f"{label} must be a JSON object")
    return payload, file_sha256(path)


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
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def safe_text(label: str, value: Any, minimum: int = 1, maximum: int = 500) -> str:
    if not isinstance(value, str):
        raise ProductLearningError(f"{label} must be text")
    cleaned = value.strip()
    if not minimum <= len(cleaned) <= maximum:
        raise ProductLearningError(f"{label} must be {minimum}-{maximum} characters")
    if any(pattern.search(cleaned) for pattern in SECRET_PATTERNS):
        raise ProductLearningError(f"{label} appears to contain a secret")
    return cleaned


def safe_id(label: str, value: Any) -> str:
    text = safe_text(label, value, 3, 80)
    if not ID_RE.fullmatch(text):
        raise ProductLearningError(
            f"{label} must use lowercase letters, digits, dots, underscores, or hyphens"
        )
    return text


def bounded_number(
    label: str, value: Any, minimum: float = 0.0, maximum: float | None = None
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProductLearningError(f"{label} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ProductLearningError(f"{label} must be finite")
    if number < minimum or (maximum is not None and number > maximum):
        raise ProductLearningError(f"{label} is outside the allowed range")
    return number


def whole_number(label: str, value: Any, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ProductLearningError(f"{label} must be an integer >= {minimum}")
    return value


def parse_time(label: str, value: Any) -> datetime:
    text = safe_text(label, value, 10, 40)
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProductLearningError(f"{label} must be ISO-8601") from exc


def validate_config(config: dict[str, Any]) -> dict[str, float | int]:
    if config.get("schema_version") != 1:
        raise ProductLearningError("config schema_version must be 1")
    dropoff_weight = bounded_number(
        "weights.dropoff", config.get("weights", {}).get("dropoff"), 0.0, 1.0
    )
    error_weight = bounded_number(
        "weights.error", config.get("weights", {}).get("error"), 0.0, 1.0
    )
    if not math.isclose(dropoff_weight + error_weight, 1.0, abs_tol=1e-9):
        raise ProductLearningError("friction weights must sum to 1")
    return {
        "dropoff_weight": dropoff_weight,
        "error_weight": error_weight,
        "min_sample_size": whole_number(
            "analysis.min_sample_size", config.get("analysis", {}).get("min_sample_size"), 1
        ),
        "min_friction_score": bounded_number(
            "analysis.min_friction_score",
            config.get("analysis", {}).get("min_friction_score"),
            0.0,
            1.0,
        ),
    }


def analyze_snapshot(snapshot: dict[str, Any], snapshot_sha256: str, config: dict[str, Any]) -> dict[str, Any]:
    normalized_config = validate_config(config)
    if snapshot.get("schema_version") != 1:
        raise ProductLearningError("snapshot schema_version must be 1")
    if snapshot.get("data_policy") != "aggregated-sanitized":
        raise ProductLearningError("snapshot data_policy must be aggregated-sanitized")
    privacy = snapshot.get("privacy")
    if not isinstance(privacy, dict):
        raise ProductLearningError("snapshot privacy contract is required")
    if privacy.get("contains_pii") is not False or privacy.get("aggregated") is not True:
        raise ProductLearningError("snapshot must be aggregated and explicitly PII-free")

    snapshot_id = safe_id("snapshot_id", snapshot.get("snapshot_id"))
    workflow = safe_text("workflow", snapshot.get("workflow"), 3, 120)
    source_type = safe_text("source_type", snapshot.get("source_type"), 3, 80)
    window = snapshot.get("window")
    if not isinstance(window, dict):
        raise ProductLearningError("snapshot window is required")
    start = parse_time("window.start", window.get("start"))
    end = parse_time("window.end", window.get("end"))
    if end <= start:
        raise ProductLearningError("window.end must be after window.start")

    raw_steps = snapshot.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise ProductLearningError("snapshot requires at least one step")
    seen_ids: set[str] = set()
    eligible: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_steps):
        if not isinstance(raw, dict):
            raise ProductLearningError(f"steps[{index}] must be an object")
        step_id = safe_id(f"steps[{index}].id", raw.get("id"))
        if step_id in seen_ids:
            raise ProductLearningError(f"duplicate step id: {step_id}")
        seen_ids.add(step_id)
        name = safe_text(f"steps[{index}].name", raw.get("name"), 3, 120)
        entered = whole_number(f"steps[{index}].entered", raw.get("entered"), 0)
        completed = whole_number(f"steps[{index}].completed", raw.get("completed"), 0)
        errors = whole_number(f"steps[{index}].errors", raw.get("errors"), 0)
        dropoff_classification = raw.get("dropoff_classification")
        if dropoff_classification not in {"friction", "intentional-filter"}:
            raise ProductLearningError(
                f"steps[{index}].dropoff_classification must be friction or intentional-filter"
            )
        if completed > entered:
            raise ProductLearningError(f"{step_id} completed cannot exceed entered")
        raw_dropoff_rate = (entered - completed) / entered if entered else 0.0
        dropoff_rate = 0.0 if dropoff_classification == "intentional-filter" else raw_dropoff_rate
        error_rate = min(errors / entered, 1.0) if entered else 0.0
        score = (
            normalized_config["dropoff_weight"] * dropoff_rate
            + normalized_config["error_weight"] * error_rate
        )
        normalized = {
            "id": step_id,
            "name": name,
            "entered": entered,
            "completed": completed,
            "errors": errors,
            "dropoff_classification": dropoff_classification,
            "raw_dropoff_rate": round(raw_dropoff_rate, 6),
            "dropoff_rate": round(dropoff_rate, 6),
            "error_rate": round(error_rate, 6),
            "friction_score": round(score, 6),
        }
        if dropoff_classification == "intentional-filter":
            normalized["intentional_exit_count"] = entered - completed
            normalized["dropoff_excluded_reason"] = "intentional-editorial-filter"
        if entered < normalized_config["min_sample_size"]:
            normalized["reason"] = "below-minimum-sample"
            rejected.append(normalized)
        else:
            eligible.append(normalized)

    base = {
        "schema_version": 1,
        "snapshot_id": snapshot_id,
        "snapshot_sha256": snapshot_sha256,
        "workflow": workflow,
        "source_type": source_type,
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "automatic_change": False,
        "excluded_steps": rejected,
    }
    if not eligible:
        return {
            **base,
            "status": "insufficient-evidence",
            "lesson": None,
            "reason": "no step reached the minimum sample size",
        }

    selected = max(eligible, key=lambda item: (item["friction_score"], item["entered"], item["id"]))
    if selected["friction_score"] < normalized_config["min_friction_score"]:
        return {
            **base,
            "status": "clean-noop",
            "lesson": None,
            "reason": "no eligible step crossed the friction threshold",
        }
    lesson_id = "gpl-" + digest(snapshot_id, snapshot_sha256, selected["id"])
    return {
        **base,
        "status": "review",
        "lesson": {
            "id": lesson_id,
            "step": selected,
            "highest_leverage_unknown": (
                f"Why do users fail or abandon the '{selected['name']}' step, and which single "
                "change would improve completion without breaching a guardrail?"
            ),
            "selection_rule": "highest weighted dropoff/error score among adequately sampled steps",
            "next_state": "stage-one-controlled-intervention",
        },
    }


def normalize_metric(label: str, raw: Any, require_threshold: bool) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ProductLearningError(f"{label} must be an object")
    metric = {
        "name": safe_id(f"{label}.name", raw.get("name")),
        "direction": raw.get("direction"),
        "baseline": bounded_number(f"{label}.baseline", raw.get("baseline")),
    }
    if metric["direction"] not in {"increase", "decrease"}:
        raise ProductLearningError(f"{label}.direction must be increase or decrease")
    threshold_key = "min_improvement" if require_threshold else "max_regression"
    metric[threshold_key] = bounded_number(f"{label}.{threshold_key}", raw.get(threshold_key))
    return metric


def stage_experiment(
    lesson: dict[str, Any], lesson_sha256: str, spec: dict[str, Any], spec_sha256: str
) -> dict[str, Any]:
    if lesson.get("schema_version") != 1 or lesson.get("status") != "review":
        raise ProductLearningError("lesson must be a reviewable schema-version-1 analysis")
    lesson_record = lesson.get("lesson")
    if not isinstance(lesson_record, dict):
        raise ProductLearningError("lesson record is missing")
    if spec.get("schema_version") != 1:
        raise ProductLearningError("experiment spec schema_version must be 1")
    if spec.get("lesson_id") != lesson_record.get("id"):
        raise ProductLearningError("experiment spec lesson_id does not match")
    mode = spec.get("mode")
    if mode not in {"shadow", "production"}:
        raise ProductLearningError("experiment mode must be shadow or production")

    intervention = spec.get("intervention")
    if not isinstance(intervention, dict) or set(intervention) != {"variable", "change"}:
        raise ProductLearningError("intervention must contain exactly variable and change")
    variable = safe_id("intervention.variable", intervention.get("variable"))
    change = safe_text("intervention.change", intervention.get("change"), 10, 300)
    hypothesis = safe_text("hypothesis", spec.get("hypothesis"), 20, 500)
    rollback = safe_text("rollback", spec.get("rollback"), 10, 500)
    raw_comparator = spec.get("comparator")
    if not isinstance(raw_comparator, dict) or set(raw_comparator) != {
        "method", "control", "treatment", "unit"
    }:
        raise ProductLearningError(
            "comparator must contain exactly method, control, treatment, and unit"
        )
    comparator_method = raw_comparator.get("method")
    if comparator_method not in {"paired-control-treatment", "matched-pre-post"}:
        raise ProductLearningError(
            "comparator.method must be paired-control-treatment or matched-pre-post"
        )
    comparator = {
        "method": comparator_method,
        "control": safe_text("comparator.control", raw_comparator.get("control"), 10, 300),
        "treatment": safe_text(
            "comparator.treatment", raw_comparator.get("treatment"), 10, 300
        ),
        "unit": safe_id("comparator.unit", raw_comparator.get("unit")),
    }
    primary = normalize_metric("primary_metric", spec.get("primary_metric"), True)
    raw_guardrails = spec.get("guardrails")
    if not isinstance(raw_guardrails, list) or not 1 <= len(raw_guardrails) <= 5:
        raise ProductLearningError("experiment requires 1-5 guardrails")
    guardrails = [
        normalize_metric(f"guardrails[{index}]", item, False)
        for index, item in enumerate(raw_guardrails)
    ]
    metric_names = [primary["name"], *[item["name"] for item in guardrails]]
    if len(metric_names) != len(set(metric_names)):
        raise ProductLearningError("primary and guardrail metric names must be distinct")

    evaluation = spec.get("evaluation")
    if not isinstance(evaluation, dict):
        raise ProductLearningError("evaluation contract is required")
    min_sample_size = whole_number("evaluation.min_sample_size", evaluation.get("min_sample_size"), 1)
    min_window_days = whole_number("evaluation.min_window_days", evaluation.get("min_window_days"), 1)
    max_window_days = whole_number("evaluation.max_window_days", evaluation.get("max_window_days"), min_window_days)
    if max_window_days < min_window_days:
        raise ProductLearningError("evaluation.max_window_days cannot be below min_window_days")

    approval = spec.get("approval")
    if approval is not None:
        if not isinstance(approval, dict) or approval.get("method") != "explicit_text":
            raise ProductLearningError("approval must use explicit_text")
        approval = {
            "method": "explicit_text",
            "approved_by": safe_text("approval.approved_by", approval.get("approved_by"), 3, 100),
            "approval_ref": safe_text("approval.approval_ref", approval.get("approval_ref"), 6, 300),
        }
    if mode == "production" and approval is None:
        state = "approval-required"
    else:
        state = "ready-for-shadow" if mode == "shadow" else "ready-for-approved-execution"
    staged_id = "gpe-" + digest(lesson_sha256, spec_sha256, variable)
    return {
        "schema_version": 1,
        "id": staged_id,
        "state": state,
        "mode": mode,
        "lesson_id": lesson_record["id"],
        "lesson_sha256": lesson_sha256,
        "spec_sha256": spec_sha256,
        "hypothesis": hypothesis,
        "intervention": {"variable": variable, "change": change},
        "comparator": comparator,
        "primary_metric": primary,
        "guardrails": guardrails,
        "evaluation": {
            "min_sample_size": min_sample_size,
            "min_window_days": min_window_days,
            "max_window_days": max_window_days,
        },
        "approval": approval,
        "rollback": rollback,
        "automatic_execution": False,
        "automatic_promotion": False,
    }


def directional_improvement(direction: str, baseline: float, current: float) -> float:
    return current - baseline if direction == "increase" else baseline - current


def evaluate_experiment(stage: dict[str, Any], stage_sha256: str, result: dict[str, Any]) -> dict[str, Any]:
    if stage.get("schema_version") != 1:
        raise ProductLearningError("staged experiment schema_version must be 1")
    if result.get("schema_version") != 1:
        raise ProductLearningError("result schema_version must be 1")
    if result.get("experiment_id") != stage.get("id"):
        raise ProductLearningError("result experiment_id does not match")
    if result.get("stage_sha256") != stage_sha256:
        raise ProductLearningError("result is not bound to this staged experiment")
    comparison = result.get("comparison")
    if not isinstance(comparison, dict):
        raise ProductLearningError("result comparison is required")
    stage_comparator = stage.get("comparator")
    if not isinstance(stage_comparator, dict):
        raise ProductLearningError("staged experiment comparator is missing")
    if comparison.get("method") != stage_comparator.get("method"):
        raise ProductLearningError("result comparison method does not match the staged comparator")
    control_sample_size = whole_number(
        "result.comparison.control_sample_size", comparison.get("control_sample_size"), 0
    )
    treatment_sample_size = whole_number(
        "result.comparison.treatment_sample_size", comparison.get("treatment_sample_size"), 0
    )
    if (
        stage_comparator.get("method") == "paired-control-treatment"
        and control_sample_size != treatment_sample_size
    ):
        raise ProductLearningError("paired comparison sample sizes must match")
    sample_size = min(control_sample_size, treatment_sample_size)
    window = result.get("window")
    if not isinstance(window, dict):
        raise ProductLearningError("result window is required")
    start = parse_time("result.window.start", window.get("start"))
    end = parse_time("result.window.end", window.get("end"))
    if end <= start:
        raise ProductLearningError("result window.end must be after start")
    window_days = (end - start).total_seconds() / 86400
    control_metrics = comparison.get("control_metrics")
    treatment_metrics = comparison.get("treatment_metrics")
    if not isinstance(control_metrics, dict) or not isinstance(treatment_metrics, dict):
        raise ProductLearningError("comparison control_metrics and treatment_metrics are required")

    expected_names = [stage["primary_metric"]["name"], *[item["name"] for item in stage["guardrails"]]]
    if set(control_metrics) != set(expected_names) or set(treatment_metrics) != set(expected_names):
        raise ProductLearningError(
            "control and treatment metrics must contain every locked metric exactly once"
        )
    normalized_control = {
        name: bounded_number(f"result.comparison.control_metrics.{name}", control_metrics[name])
        for name in expected_names
    }
    normalized_treatment = {
        name: bounded_number(
            f"result.comparison.treatment_metrics.{name}", treatment_metrics[name]
        )
        for name in expected_names
    }
    evidence_failures: list[str] = []
    contract = stage["evaluation"]
    if sample_size < contract["min_sample_size"]:
        evidence_failures.append("sample size is below the locked minimum")
    if window_days < contract["min_window_days"]:
        evidence_failures.append("evaluation window is shorter than the locked minimum")
    if window_days > contract["max_window_days"]:
        evidence_failures.append("evaluation window exceeds the locked maximum")

    primary = stage["primary_metric"]
    primary_control_value = normalized_control[primary["name"]]
    primary_value = normalized_treatment[primary["name"]]
    primary_improvement = directional_improvement(
        primary["direction"], primary_control_value, primary_value
    )
    guardrail_results: list[dict[str, Any]] = []
    breaches: list[str] = []
    for guardrail in stage["guardrails"]:
        control_value = normalized_control[guardrail["name"]]
        value = normalized_treatment[guardrail["name"]]
        regression = -directional_improvement(
            guardrail["direction"], control_value, value
        )
        breached = regression > guardrail["max_regression"]
        if breached:
            breaches.append(guardrail["name"])
        guardrail_results.append(
            {
                "name": guardrail["name"],
                "control_value": control_value,
                "treatment_value": value,
                "value": value,
                "regression": round(regression, 6),
                "max_regression": guardrail["max_regression"],
                "breached": breached,
            }
        )

    if evidence_failures:
        outcome = "insufficient-evidence"
    elif breaches:
        outcome = "rollback-required"
    elif primary_improvement >= primary["min_improvement"]:
        outcome = "success"
    else:
        outcome = "inconclusive"
    return {
        "schema_version": 1,
        "experiment_id": stage["id"],
        "stage_sha256": stage_sha256,
        "outcome": outcome,
        "primary": {
            "name": primary["name"],
            "control_value": primary_control_value,
            "treatment_value": primary_value,
            "value": primary_value,
            "improvement": round(primary_improvement, 6),
            "min_improvement": primary["min_improvement"],
        },
        "guardrails": guardrail_results,
        "sample_size": sample_size,
        "comparison": {
            "method": stage_comparator["method"],
            "control_sample_size": control_sample_size,
            "treatment_sample_size": treatment_sample_size,
        },
        "window_days": round(window_days, 6),
        "evidence_failures": evidence_failures,
        "rollback": stage["rollback"] if outcome == "rollback-required" else None,
        "eligible_for_learning_capture": outcome == "success",
        "automatic_promotion": False,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="select one evidence-backed friction lesson")
    analyze.add_argument("--snapshot", type=Path, required=True)
    analyze.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    analyze.add_argument("--output", type=Path, required=True)

    stage = subparsers.add_parser("stage", help="stage exactly one controlled intervention")
    stage.add_argument("--lesson", type=Path, required=True)
    stage.add_argument("--spec", type=Path, required=True)
    stage.add_argument("--output", type=Path, required=True)

    evaluate = subparsers.add_parser("evaluate", help="classify a measured experiment outcome")
    evaluate.add_argument("--stage", type=Path, required=True)
    evaluate.add_argument("--result", type=Path, required=True)
    evaluate.add_argument("--output", type=Path, required=True)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "analyze":
            snapshot, snapshot_sha = read_json_object(args.snapshot, "snapshot")
            config, _ = read_json_object(args.config, "config")
            output = analyze_snapshot(snapshot, snapshot_sha, config)
        elif args.command == "stage":
            lesson, lesson_sha = read_json_object(args.lesson, "lesson")
            spec, spec_sha = read_json_object(args.spec, "experiment spec")
            output = stage_experiment(lesson, lesson_sha, spec, spec_sha)
        else:
            stage, stage_sha = read_json_object(args.stage, "staged experiment")
            result, _ = read_json_object(args.result, "experiment result")
            output = evaluate_experiment(stage, stage_sha, result)
        atomic_write_json(args.output, output)
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except ProductLearningError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
