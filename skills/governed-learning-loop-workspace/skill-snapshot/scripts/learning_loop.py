#!/usr/bin/env python3
"""Deterministic, human-governed learning candidate registry."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
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
    return {"schema_version": 1, "observations": [], "candidates": [], "promotion_requests": []}


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
    if registry.get("schema_version") != 1:
        raise LearningLoopError("unsupported registry schema")
    for key in ("observations", "candidates", "promotion_requests"):
        if not isinstance(registry.get(key), list):
            raise LearningLoopError(f"registry field {key} must be a list")
    return registry


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
        f"- Promotion requests: {len(registry['promotion_requests'])}",
        "- Active promotions performed by this loop: 0",
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
                "- Decision required: approve exact target, reject, or collect more evidence",
                "",
                "### Evidence",
                "",
            ]
        )
        for observation_id in candidate["observation_ids"]:
            item = observations_by_id[observation_id]
            lines.append(f"- `{item['run_id']}`: {item['verification']} Source: `{item['source']}`.")
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


def request_promotion(args: argparse.Namespace) -> dict[str, Any]:
    target_path = validate_target_path(args.target_path)
    approved_by = ensure_safe_text("approved-by", args.approved_by, 3, 100)
    approval_ref = ensure_safe_text("approval-ref", args.approval_ref, 6, 300)
    with locked_registry(args.data_dir) as registry:
        candidate = find_candidate(registry, args.candidate)
        observations_by_id = {item["id"]: item for item in registry["observations"]}
        observations = [observations_by_id[item] for item in candidate["observation_ids"]]
        ready, failures = candidate_readiness(observations)
        if not ready or candidate.get("readiness") != "eligible":
            raise LearningLoopError("candidate is not eligible: " + "; ".join(failures))
        request_id = "glp-" + digest(candidate["id"], target_path, approved_by, approval_ref)
        existing = next((item for item in registry["promotion_requests"] if item["id"] == request_id), None)
        if existing:
            return {"status": "existing", "promotion_request": existing, "target_written": False}
        receipt = {
            "id": request_id,
            "candidate_id": candidate["id"],
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


def status(args: argparse.Namespace) -> dict[str, Any]:
    registry = load_registry(args.data_dir)
    return {
        "status": "ok",
        "observations": len(registry["observations"]),
        "candidates": len(registry["candidates"]),
        "promotion_requests": len(registry["promotion_requests"]),
        "active_promotions": 0,
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

    promotion_parser = subparsers.add_parser("request-promotion", help="record explicit approval without writing the target")
    promotion_parser.add_argument("--candidate", required=True)
    promotion_parser.add_argument("--target-path", required=True)
    promotion_parser.add_argument("--approved-by", required=True)
    promotion_parser.add_argument("--approval-ref", required=True)
    promotion_parser.set_defaults(handler=request_promotion)

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
