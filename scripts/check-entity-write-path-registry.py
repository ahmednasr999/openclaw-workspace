#!/usr/bin/env python3
"""Fail-closed validator for the NASR entity and write-path registry.

Default mode validates the contract only. ``--live`` performs read-only checks
against declared local files and SQLite schemas. It never contacts providers or
changes production state.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path("/root/.openclaw/workspace")
DEFAULT_REGISTRY = ROOT / "config/entity-write-path-registry.json"
ALLOWED_WRITE_MODES = {"controlled", "external_approval", "read_only"}
ALLOWED_GATE_STATUSES = {"enforced", "documented"}
ALLOWED_EVIDENCE_TYPES = {"path_exists", "sqlite_table", "file_contains", "json_path"}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _add_missing(errors: list[str], obj: dict[str, Any], fields: list[str], prefix: str) -> None:
    for field in fields:
        if field not in obj or obj[field] in (None, "", [], {}):
            errors.append(f"{prefix}: missing {field}")


def validate_registry(registry: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if registry.get("schema_version") != 1:
        errors.append("registry: schema_version must equal 1")

    policy = registry.get("policy")
    if not isinstance(policy, dict):
        return ["registry: policy must be an object"], warnings

    policy_fields = [
        "required_entities",
        "required_governance_gates",
        "required_workflows",
        "required_metrics",
        "conflict_rule",
        "automation_rule",
    ]
    _add_missing(errors, policy, policy_fields, "policy")

    entities = registry.get("entities")
    if not isinstance(entities, list) or not entities:
        return errors + ["registry: entities must be a non-empty list"], warnings

    entity_ids: list[str] = []
    for index, entity in enumerate(entities):
        prefix = f"entities[{index}]"
        if not isinstance(entity, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        _add_missing(
            errors,
            entity,
            ["id", "scope", "owner", "owner_workspace", "record_key", "authority", "write_contract", "governance", "live_evidence"],
            prefix,
        )
        entity_id = entity.get("id")
        if _nonempty(entity_id):
            entity_ids.append(entity_id)
            prefix = f"entity {entity_id}"

        if not _nonempty(entity.get("owner")) or any(ch in str(entity.get("owner", "")) for ch in (",", "/")) and entity.get("owner") not in {"NASR/main"}:
            errors.append(f"{prefix}: owner must name one accountable owner")
        if not str(entity.get("owner_workspace", "")).startswith("/root/.openclaw/"):
            errors.append(f"{prefix}: owner_workspace must be an absolute OpenClaw workspace path")

        authority = entity.get("authority", {})
        if isinstance(authority, dict):
            _add_missing(errors, authority, ["primary_system", "primary_locator", "precedence"], f"{prefix} authority")
            if not isinstance(authority.get("operational_stores", []), list):
                errors.append(f"{prefix} authority: operational_stores must be a list")
        else:
            errors.append(f"{prefix}: authority must be an object")

        contract = entity.get("write_contract", {})
        if not isinstance(contract, dict):
            errors.append(f"{prefix}: write_contract must be an object")
        else:
            _add_missing(
                errors,
                contract,
                ["mode", "direction", "forbidden", "dedupe", "audit_evidence", "rollback", "kill_switch"],
                f"{prefix} write_contract",
            )
            mode = contract.get("mode")
            if mode not in ALLOWED_WRITE_MODES:
                errors.append(f"{prefix} write_contract: invalid mode {mode!r}")
            entry_points = contract.get("entry_points")
            if not isinstance(entry_points, list):
                errors.append(f"{prefix} write_contract: entry_points must be a list")
                entry_points = []
            if mode == "read_only" and entry_points:
                errors.append(f"{prefix} write_contract: read_only entities cannot declare write entry points")
            if mode in {"controlled", "external_approval"} and not entry_points:
                errors.append(f"{prefix} write_contract: writable entity needs a controlled entry point")
            for entry_index, entry in enumerate(entry_points):
                entry_prefix = f"{prefix} entry_points[{entry_index}]"
                if not isinstance(entry, dict):
                    errors.append(f"{entry_prefix}: must be an object")
                    continue
                _add_missing(errors, entry, ["kind", "locator", "authority"], entry_prefix)
            if mode == "external_approval":
                permission_evidence = str(entity.get("governance", {}).get("permissions", {}).get("evidence", "")).lower()
                if "approval" not in permission_evidence and "explicit" not in permission_evidence:
                    errors.append(f"{prefix}: external_approval mode needs explicit approval evidence")

        governance = entity.get("governance", {})
        required_gates = policy.get("required_governance_gates", [])
        if not isinstance(governance, dict):
            errors.append(f"{prefix}: governance must be an object")
        else:
            for gate in required_gates:
                gate_value = governance.get(gate)
                if not isinstance(gate_value, dict):
                    errors.append(f"{prefix}: missing governance gate {gate}")
                    continue
                if gate_value.get("status") not in ALLOWED_GATE_STATUSES:
                    errors.append(f"{prefix} gate {gate}: invalid or missing status")
                if not _nonempty(gate_value.get("evidence")):
                    errors.append(f"{prefix} gate {gate}: missing evidence")

        evidence = entity.get("live_evidence", [])
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{prefix}: live_evidence must be a non-empty list")
        else:
            for evidence_index, check in enumerate(evidence):
                check_prefix = f"{prefix} live_evidence[{evidence_index}]"
                if not isinstance(check, dict):
                    errors.append(f"{check_prefix}: must be an object")
                    continue
                if check.get("type") not in ALLOWED_EVIDENCE_TYPES:
                    errors.append(f"{check_prefix}: unsupported type {check.get('type')!r}")
                if not _nonempty(check.get("path")):
                    errors.append(f"{check_prefix}: missing path")
                if check.get("type") == "sqlite_table" and not _nonempty(check.get("table")):
                    errors.append(f"{check_prefix}: missing table")
                if check.get("type") == "file_contains" and not _nonempty(check.get("needle")):
                    errors.append(f"{check_prefix}: missing needle")
                if check.get("type") == "json_path" and not _nonempty(check.get("key_path")):
                    errors.append(f"{check_prefix}: missing key_path")

    duplicates = sorted({entity_id for entity_id in entity_ids if entity_ids.count(entity_id) > 1})
    if duplicates:
        errors.append(f"registry: duplicate entity ids: {', '.join(duplicates)}")

    missing_entities = sorted(set(policy.get("required_entities", [])) - set(entity_ids))
    if missing_entities:
        errors.append(f"registry: missing required entities: {', '.join(missing_entities)}")

    workflows = registry.get("workflows")
    if not isinstance(workflows, list) or not workflows:
        return errors + ["registry: workflows must be a non-empty list"], warnings

    workflow_ids: list[str] = []
    for index, workflow in enumerate(workflows):
        prefix = f"workflows[{index}]"
        if not isinstance(workflow, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        _add_missing(
            errors,
            workflow,
            ["id", "owner", "entities", "start_evidence", "end_evidence", "metrics", "collection", "baseline"],
            prefix,
        )
        workflow_id = workflow.get("id")
        if _nonempty(workflow_id):
            workflow_ids.append(workflow_id)
            prefix = f"workflow {workflow_id}"
        references = workflow.get("entities", [])
        if not isinstance(references, list) or not references:
            errors.append(f"{prefix}: entities must be a non-empty list")
        else:
            unknown = sorted(set(references) - set(entity_ids))
            if unknown:
                errors.append(f"{prefix}: unknown entity references: {', '.join(unknown)}")
        metrics = workflow.get("metrics", {})
        if not isinstance(metrics, dict):
            errors.append(f"{prefix}: metrics must be an object")
        else:
            for metric in policy.get("required_metrics", []):
                if not _nonempty(metrics.get(metric)):
                    errors.append(f"{prefix}: missing metric {metric}")
        baseline = workflow.get("baseline", {})
        if not isinstance(baseline, dict):
            errors.append(f"{prefix}: baseline must be an object")
        else:
            _add_missing(errors, baseline, ["status", "observation_window_days", "starts_on", "review_on"], f"{prefix} baseline")
            if baseline.get("status") not in {"instrumentation_defined", "observing", "complete"}:
                errors.append(f"{prefix} baseline: invalid status")
            if not isinstance(baseline.get("observation_window_days"), int) or baseline.get("observation_window_days", 0) <= 0:
                errors.append(f"{prefix} baseline: observation_window_days must be positive")
            if baseline.get("status") != "complete" and baseline.get("values") is None:
                warnings.append(f"{prefix}: baseline values pending observed data")
            if baseline.get("status") == "complete" and not isinstance(baseline.get("values"), dict):
                errors.append(f"{prefix} baseline: complete status requires values")

    workflow_duplicates = sorted({item for item in workflow_ids if workflow_ids.count(item) > 1})
    if workflow_duplicates:
        errors.append(f"registry: duplicate workflow ids: {', '.join(workflow_duplicates)}")
    missing_workflows = sorted(set(policy.get("required_workflows", [])) - set(workflow_ids))
    if missing_workflows:
        errors.append(f"registry: missing required workflows: {', '.join(missing_workflows)}")

    return errors, warnings


def _json_path_exists(path: Path, key_path: str) -> bool:
    value: Any = json.loads(path.read_text(encoding="utf-8"))
    for key in key_path.split("."):
        if not isinstance(value, dict) or key not in value:
            return False
        value = value[key]
    return value not in (None, "", [], {})


def run_live_checks(entities: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    for entity in entities:
        entity_id = entity.get("id", "unknown")
        for check in entity.get("live_evidence", []):
            check_type = check.get("type")
            path = Path(str(check.get("path", "")))
            ok = False
            detail = ""
            try:
                if check_type == "path_exists":
                    ok = path.exists()
                    detail = "exists" if ok else "missing"
                elif check_type == "sqlite_table":
                    if not path.is_file():
                        detail = "database missing"
                    else:
                        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=2)
                        try:
                            row = connection.execute(
                                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                                (check["table"],),
                            ).fetchone()
                            ok = row is not None
                            detail = f"table {check['table']} {'present' if ok else 'missing'}"
                        finally:
                            connection.close()
                elif check_type == "file_contains":
                    if not path.is_file():
                        detail = "file missing"
                    else:
                        ok = check["needle"] in path.read_text(encoding="utf-8")
                        detail = "marker present" if ok else "marker missing"
                elif check_type == "json_path":
                    if not path.is_file():
                        detail = "JSON file missing"
                    else:
                        ok = _json_path_exists(path, check["key_path"])
                        detail = f"key {check['key_path']} {'present' if ok else 'missing'}"
                else:
                    detail = f"unsupported check type {check_type}"
            except (OSError, ValueError, KeyError, sqlite3.Error, json.JSONDecodeError) as exc:
                detail = f"{type(exc).__name__}: {exc}"
            result = {
                "entity": entity_id,
                "type": check_type,
                "path": str(path),
                "ok": ok,
                "detail": detail,
            }
            results.append(result)
            if not ok:
                failures.append(f"entity {entity_id}: {check_type} failed for {path}: {detail}")
    return results, failures


def build_report(registry: dict[str, Any], live: bool) -> dict[str, Any]:
    errors, warnings = validate_registry(registry)
    live_results: list[dict[str, Any]] = []
    if live and not errors:
        live_results, live_failures = run_live_checks(registry.get("entities", []))
        errors.extend(live_failures)
    return {
        "ok": not errors,
        "schema_version": registry.get("schema_version"),
        "registry_id": registry.get("registry_id"),
        "mode": "live-read-only" if live else "structural",
        "counts": {
            "entities": len(registry.get("entities", [])),
            "workflows": len(registry.get("workflows", [])),
            "governance_gates_per_entity": len(registry.get("policy", {}).get("required_governance_gates", [])),
            "live_checks": len(live_results),
            "live_checks_passed": sum(1 for result in live_results if result["ok"]),
        },
        "errors": errors,
        "warnings": warnings,
        "live_evidence": live_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--live", action="store_true", help="Run declared local evidence checks read-only")
    parser.add_argument("--output", type=Path, help="Write the JSON report to this local path")
    args = parser.parse_args()

    try:
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report = {
            "ok": False,
            "mode": "live-read-only" if args.live else "structural",
            "errors": [f"cannot load registry: {type(exc).__name__}: {exc}"],
            "warnings": [],
            "live_evidence": [],
        }
    else:
        report = build_report(registry, args.live)

    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
