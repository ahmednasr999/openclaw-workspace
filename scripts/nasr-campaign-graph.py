#!/usr/bin/env python3
"""NASR Campaign Graph: local campaign intake, gates, assets, and feedback.

This tool never publishes, schedules, messages, or changes Notion. It creates
and validates local campaign records that complement the live Notion Content
Calendar.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


DEFAULT_ROOT = Path(
    os.environ.get(
        "NASR_CAMPAIGN_GRAPH_ROOT",
        "/root/.openclaw/workspace-cmo/data/campaign-graph",
    )
)
SCHEMA_VERSION = "1.0"
CAIRO = ZoneInfo("Africa/Cairo")

PILLARS = {
    "ai_execution_and_governance",
    "pmo_and_decision_discipline",
    "healthcare_transformation",
    "fintech_operations",
    "gcc_transformation_leadership",
}
FUNNEL_ROLES = {"reach", "authority", "conversion"}
STAGES = (
    "intake",
    "angles",
    "evidence",
    "campaign_plan",
    "signoff",
    "build",
    "publish",
    "feedback",
)
DECISIONS = {"pass", "loop_back"}
PUBLISHABLE_NOTION_STATUSES = {"approved", "scheduled"}

GATE_CRITERIA = {
    "intake": [
        "Raw input is preserved.",
        "Audience, objective, pillar, funnel role, intended outcome, and success signal are explicit.",
    ],
    "angles": [
        "A chosen angle is recorded.",
        "The angle creates a specific executive implication rather than generic advice.",
    ],
    "evidence": [
        "At least one internal source and one external source are recorded.",
        "Claims are supportable and no Ahmed-specific facts are invented.",
    ],
    "campaign_plan": [
        "At least one asset is planned.",
        "Every asset has an owner, purpose, success signal, funnel role, and intended outcome.",
        "Derivative relationships use valid parent asset IDs.",
    ],
    "signoff": [
        "Ahmed explicitly approves the campaign direction.",
        "Approval applies to direction only; publishing still requires the live Notion workflow.",
    ],
    "build": [
        "Required asset artifacts exist.",
        "Each completed asset passed its format-specific quality gate.",
    ],
    "publish": [
        "The matching Notion row is Approved or Scheduled.",
        "Publisher QA passed and the asset is matched to the approved copy.",
        "The local campaign graph performs no publishing action.",
    ],
    "feedback": [
        "Published assets have a performance record or an explicit measurement-unavailable note.",
        "The result includes a lesson and next-cycle action.",
    ],
}

METRIC_FIELDS = (
    "impressions",
    "reactions",
    "comments",
    "substantive_comments",
    "reposts",
    "saves",
    "profile_views",
    "qualified_profile_visits",
    "qualified_conversations",
    "attributable_opportunities",
    "conversion_count",
)


class CampaignError(ValueError):
    """Raised for a user-correctable campaign record error."""


def now_iso() -> str:
    return datetime.now(CAIRO).isoformat(timespec="seconds")


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:60] or "campaign"


def campaign_dir(root: Path, campaign_id: str) -> Path:
    return root / "campaigns" / campaign_id


def manifest_path(root: Path, campaign_id: str) -> Path:
    return campaign_dir(root, campaign_id) / "manifest.json"


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def load_manifest(root: Path, campaign_id: str) -> dict[str, Any]:
    path = manifest_path(root, campaign_id)
    if not path.exists():
        raise CampaignError(f"Campaign not found: {campaign_id}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CampaignError(f"Invalid manifest JSON: {path}: {exc}") from exc


def latest_gate_decision(manifest: dict[str, Any], stage: str) -> str:
    history = manifest["stage_gates"][stage]["history"]
    return history[-1]["decision"] if history else "pending"


def first_open_stage(manifest: dict[str, Any]) -> str:
    for stage in STAGES:
        if latest_gate_decision(manifest, stage) != "pass":
            return stage
    return "complete"


def refresh_state(manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = now_iso()
    manifest["next_stage"] = first_open_stage(manifest)
    if manifest["next_stage"] == "complete":
        manifest["status"] = "complete"
    elif any(
        latest_gate_decision(manifest, stage) == "loop_back" for stage in STAGES
    ):
        manifest["status"] = "needs_revision"
    elif latest_gate_decision(manifest, "signoff") == "pass":
        manifest["status"] = "approved_direction"
    else:
        manifest["status"] = "draft"


def render_brief(manifest: dict[str, Any]) -> str:
    brief = manifest["brief"]
    assets = manifest["assets"]
    lines = [
        f"# {brief['title']}",
        "",
        f"- Campaign ID: `{manifest['campaign_id']}`",
        f"- Status: `{manifest['status']}`",
        f"- Next stage: `{manifest['next_stage']}`",
        f"- Source type: `{manifest['source']['type']}`",
        f"- Pillar: `{brief['pillar']}`",
        f"- Funnel role: `{brief['funnel_role']}`",
        f"- Audience: {brief['audience']}",
        f"- Objective: {brief['objective']}",
        f"- Intended outcome: {brief['intended_outcome']}",
        f"- Success signal: {brief['success_signal']}",
        "",
        "## Raw input",
        "",
        manifest["source"]["raw_input"],
        "",
        "## Campaign direction",
        "",
        f"- Core tension: {brief['core_tension'] or 'To be decided'}",
        f"- Chosen angle: {brief['chosen_angle'] or 'To be decided'}",
        f"- Primary hook: {brief['primary_hook'] or 'To be decided'}",
        "",
        "## Asset graph",
        "",
    ]
    if assets:
        for asset in assets:
            parent = asset["parent_asset_id"] or "root"
            lines.append(
                f"- `{asset['asset_id']}`: {asset['platform']} / {asset['format']} "
                f"(parent: `{parent}`, status: `{asset['status']}`)"
            )
    else:
        lines.append("- No assets planned.")

    if brief.get("rejected_angles"):
        lines.extend(["", "### Rejected angles", ""])
        lines.extend(f"- {angle}" for angle in brief["rejected_angles"])

    lines.extend(["", "## Stage gates", ""])
    for stage in STAGES:
        lines.append(f"- `{stage}`: `{latest_gate_decision(manifest, stage)}`")

    lines.extend(
        [
            "",
            "## Governance",
            "",
            "- Notion Content Calendar remains the live approval and publishing source of truth.",
            "- This campaign record does not authorize publishing, scheduling, messaging, or email.",
            "- Ahmed sign-off is required for campaign direction and live publishing controls still apply per asset.",
            "",
        ]
    )
    return "\n".join(lines)


def save_manifest(root: Path, manifest: dict[str, Any]) -> Path:
    refresh_state(manifest)
    path = manifest_path(root, manifest["campaign_id"])
    atomic_write_json(path, manifest)
    (path.parent / "brief.md").write_text(render_brief(manifest), encoding="utf-8")
    return path


def new_asset(
    *,
    asset_id: str,
    platform: str,
    format_name: str,
    purpose: str,
    owner: str,
    funnel_role: str,
    intended_outcome: str,
    success_signal: str,
    hook: str = "",
    parent_asset_id: str | None = None,
) -> dict[str, Any]:
    return {
        "asset_id": asset_id,
        "parent_asset_id": parent_asset_id,
        "platform": clean_text(platform).lower(),
        "format": clean_text(format_name).lower(),
        "purpose": clean_text(purpose),
        "owner": clean_text(owner),
        "hook": clean_text(hook),
        "funnel_role": clean_text(funnel_role).lower(),
        "intended_outcome": clean_text(intended_outcome),
        "success_signal": clean_text(success_signal),
        "status": "planned",
        "artifact_path": None,
        "notion_page_id": None,
        "post_url": None,
        "quality_gate": "pending",
        "performance_recorded": False,
    }


def cmd_intake(args: argparse.Namespace) -> int:
    root = Path(args.root)
    title = clean_text(args.title)
    campaign_id = args.campaign_id or (
        f"{datetime.now(CAIRO).date().isoformat()}-{slugify(title)}"
    )
    if manifest_path(root, campaign_id).exists():
        raise CampaignError(
            f"Campaign already exists: {campaign_id}. Use a different --campaign-id."
        )

    pillar = clean_text(args.pillar).lower()
    funnel_role = clean_text(args.funnel_role).lower()
    if pillar not in PILLARS:
        raise CampaignError(f"Unsupported pillar: {pillar}")
    if funnel_role not in FUNNEL_ROLES:
        raise CampaignError(f"Unsupported funnel role: {funnel_role}")

    raw_input = clean_text(args.raw_input)
    required = {
        "title": title,
        "raw_input": raw_input,
        "objective": clean_text(args.objective),
        "audience": clean_text(args.audience),
        "intended_outcome": clean_text(args.intended_outcome),
        "success_signal": clean_text(args.success_signal),
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise CampaignError(f"Missing required intake fields: {', '.join(missing)}")

    primary = new_asset(
        asset_id=clean_text(args.primary_asset_id),
        platform=args.primary_platform,
        format_name=args.primary_format,
        purpose=args.primary_purpose,
        owner=args.owner,
        funnel_role=funnel_role,
        intended_outcome=required["intended_outcome"],
        success_signal=required["success_signal"],
        hook=args.primary_hook,
    )
    created_at = now_iso()
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "campaign_id": campaign_id,
        "created_at": created_at,
        "updated_at": created_at,
        "status": "draft",
        "next_stage": "intake",
        "source": {
            "type": args.source_type,
            "raw_input": raw_input,
            "source_refs": list(args.source_ref or []),
        },
        "brief": {
            "title": title,
            "objective": required["objective"],
            "audience": required["audience"],
            "pillar": pillar,
            "funnel_role": funnel_role,
            "intended_outcome": required["intended_outcome"],
            "success_signal": required["success_signal"],
            "core_tension": clean_text(args.core_tension),
            "chosen_angle": clean_text(args.chosen_angle),
            "rejected_angles": [],
            "primary_hook": clean_text(args.primary_hook),
        },
        "evidence": {"internal": [], "external": []},
        "assets": [primary],
        "stage_gates": {
            stage: {"criteria": GATE_CRITERIA[stage], "history": []}
            for stage in STAGES
        },
        "feedback_summary": {
            "records": 0,
            "last_observed_at": None,
            "latest_lesson": None,
            "next_cycle_action": None,
        },
        "governance": {
            "owner": "CMO",
            "human_signoff_required": True,
            "notion_is_live_publish_source": True,
            "external_writes_allowed": False,
            "auto_publish_allowed": False,
            "approval_note": (
                "Campaign direction sign-off does not replace per-asset approval "
                "or the Notion publishing workflow."
            ),
        },
    }
    path = save_manifest(root, manifest)
    print(path)
    print(f"CREATED {campaign_id}")
    print("NEXT gate intake")
    return 0


def cmd_direction(args: argparse.Namespace) -> int:
    root = Path(args.root)
    manifest = load_manifest(root, args.campaign_id)
    brief = manifest["brief"]
    brief.setdefault("rejected_angles", [])
    if args.core_tension is not None:
        brief["core_tension"] = clean_text(args.core_tension)
    if args.chosen_angle is not None:
        brief["chosen_angle"] = clean_text(args.chosen_angle)
    if args.primary_hook is not None:
        brief["primary_hook"] = clean_text(args.primary_hook)
        if manifest["assets"]:
            manifest["assets"][0]["hook"] = brief["primary_hook"]
    for rejected in args.rejected_angle or []:
        value = clean_text(rejected)
        if value and value not in brief["rejected_angles"]:
            brief["rejected_angles"].append(value)
    if not brief["chosen_angle"]:
        raise CampaignError("Campaign direction requires a non-empty chosen angle.")
    save_manifest(root, manifest)
    print(f"UPDATED direction {args.campaign_id}")
    return 0


def cmd_add_evidence(args: argparse.Namespace) -> int:
    root = Path(args.root)
    manifest = load_manifest(root, args.campaign_id)
    record = {
        "label": clean_text(args.label),
        "source": clean_text(args.source),
        "note": clean_text(args.note),
        "captured_at": now_iso(),
    }
    if not record["label"] or not record["source"]:
        raise CampaignError("Evidence requires --label and --source.")
    manifest["evidence"][args.kind].append(record)
    save_manifest(root, manifest)
    print(f"ADDED {args.kind} evidence to {args.campaign_id}")
    return 0


def cmd_add_asset(args: argparse.Namespace) -> int:
    root = Path(args.root)
    manifest = load_manifest(root, args.campaign_id)
    existing_ids = {asset["asset_id"] for asset in manifest["assets"]}
    if args.asset_id in existing_ids:
        raise CampaignError(f"Asset already exists: {args.asset_id}")
    if args.parent_asset_id and args.parent_asset_id not in existing_ids:
        raise CampaignError(f"Unknown parent asset: {args.parent_asset_id}")

    brief = manifest["brief"]
    funnel_role = (args.funnel_role or brief["funnel_role"]).lower()
    if funnel_role not in FUNNEL_ROLES:
        raise CampaignError(f"Unsupported funnel role: {funnel_role}")
    asset = new_asset(
        asset_id=clean_text(args.asset_id),
        parent_asset_id=args.parent_asset_id,
        platform=args.platform,
        format_name=args.format,
        purpose=args.purpose,
        owner=args.owner,
        hook=args.hook,
        funnel_role=funnel_role,
        intended_outcome=args.intended_outcome or brief["intended_outcome"],
        success_signal=args.success_signal or brief["success_signal"],
    )
    if not all(
        asset[key]
        for key in (
            "asset_id",
            "platform",
            "format",
            "purpose",
            "owner",
            "intended_outcome",
            "success_signal",
        )
    ):
        raise CampaignError("Asset fields cannot be empty.")
    manifest["assets"].append(asset)
    save_manifest(root, manifest)
    print(f"ADDED asset {args.asset_id} to {args.campaign_id}")
    return 0


def cmd_update_asset(args: argparse.Namespace) -> int:
    root = Path(args.root)
    manifest = load_manifest(root, args.campaign_id)
    asset = next(
        (item for item in manifest["assets"] if item["asset_id"] == args.asset_id),
        None,
    )
    if asset is None:
        raise CampaignError(f"Unknown asset: {args.asset_id}")
    for field in (
        "status",
        "artifact_path",
        "notion_page_id",
        "post_url",
        "quality_gate",
    ):
        value = getattr(args, field)
        if value is not None:
            asset[field] = clean_text(value)
    if asset["quality_gate"] == "pass" and not asset["artifact_path"]:
        raise CampaignError("A passing asset quality gate requires --artifact-path.")
    if (
        asset["quality_gate"] == "pass"
        and asset["artifact_path"]
        and not Path(asset["artifact_path"]).exists()
    ):
        raise CampaignError(
            f"Quality-passed artifact does not exist: {asset['artifact_path']}"
        )
    save_manifest(root, manifest)
    print(f"UPDATED asset {args.asset_id}")
    return 0


def require_previous_gates(manifest: dict[str, Any], stage: str) -> None:
    index = STAGES.index(stage)
    missing = [
        prior
        for prior in STAGES[:index]
        if latest_gate_decision(manifest, prior) != "pass"
    ]
    if missing:
        raise CampaignError(
            f"Cannot pass {stage}; earlier gates not passed: {', '.join(missing)}"
        )


def validate_stage_pass(
    manifest: dict[str, Any], stage: str, args: argparse.Namespace
) -> None:
    require_previous_gates(manifest, stage)
    if not args.evidence:
        raise CampaignError("A pass decision requires at least one --evidence item.")
    if stage == "angles" and not manifest["brief"]["chosen_angle"]:
        raise CampaignError("Angles gate requires a chosen angle in the intake brief.")
    if stage == "evidence":
        if not manifest["evidence"]["internal"] or not manifest["evidence"]["external"]:
            raise CampaignError(
                "Evidence gate requires at least one internal and one external source."
            )
    if stage == "campaign_plan" and not manifest["assets"]:
        raise CampaignError("Campaign plan requires at least one asset.")
    if stage == "campaign_plan":
        required = (
            "asset_id",
            "platform",
            "format",
            "purpose",
            "owner",
            "funnel_role",
            "intended_outcome",
            "success_signal",
        )
        incomplete = [
            asset.get("asset_id", "unknown")
            for asset in manifest["assets"]
            if not all(asset.get(field) for field in required)
        ]
        if incomplete:
            raise CampaignError(
                "Campaign assets are incomplete: " + ", ".join(incomplete)
            )
        graph_errors = [
            error
            for error in validate_manifest(manifest)
            if "asset" in error or "parent" in error or "cycle" in error
        ]
        if graph_errors:
            raise CampaignError("; ".join(graph_errors))
    if stage == "signoff":
        approver = clean_text(args.decided_by).lower()
        if not re.fullmatch(r"ahmed(?:\s+nasr)?(?:\s+\([^)]+\))?", approver):
            raise CampaignError(
                "Campaign sign-off must be explicitly recorded by Ahmed."
            )
    if stage == "build":
        built = [
            asset
            for asset in manifest["assets"]
            if asset["status"] in {"completed", "approved", "published"}
        ]
        if not built:
            raise CampaignError(
                "Build gate requires at least one completed or approved asset."
            )
        incomplete = [
            asset["asset_id"]
            for asset in built
            if (
                asset["quality_gate"] != "pass"
                or not asset["artifact_path"]
                or not Path(asset["artifact_path"]).exists()
            )
        ]
        if incomplete:
            raise CampaignError(
                "Completed assets missing artifact/quality pass: "
                + ", ".join(incomplete)
            )
    if stage == "publish":
        notion_status = clean_text(args.notion_status).lower()
        if notion_status not in PUBLISHABLE_NOTION_STATUSES:
            raise CampaignError(
                "Publish gate requires --notion-status Approved or Scheduled."
            )
        if clean_text(args.publisher_qa).lower() != "pass":
            raise CampaignError("Publish gate requires --publisher-qa pass.")
        ready = [
            asset
            for asset in manifest["assets"]
            if asset["status"] in {"approved", "completed", "published"}
            and asset["quality_gate"] == "pass"
            and asset["artifact_path"]
            and Path(asset["artifact_path"]).exists()
            and asset["notion_page_id"]
        ]
        if not ready:
            raise CampaignError(
                "Publish gate requires a quality-passed asset with an artifact "
                "path and matching Notion page ID."
            )
    if stage == "feedback" and manifest["feedback_summary"]["records"] < 1:
        raise CampaignError(
            "Feedback gate requires at least one tied performance record."
        )


def cmd_gate(args: argparse.Namespace) -> int:
    root = Path(args.root)
    manifest = load_manifest(root, args.campaign_id)
    if args.decision == "pass":
        validate_stage_pass(manifest, args.stage, args)
    elif not clean_text(args.reason):
        raise CampaignError("A loop_back decision requires --reason.")

    event = {
        "decision": args.decision,
        "decided_at": now_iso(),
        "decided_by": clean_text(args.decided_by),
        "reason": clean_text(args.reason),
        "evidence": [clean_text(item) for item in (args.evidence or [])],
    }
    if args.stage == "publish":
        event["notion_status"] = clean_text(args.notion_status)
        event["publisher_qa"] = clean_text(args.publisher_qa)
    manifest["stage_gates"][args.stage]["history"].append(event)
    save_manifest(root, manifest)
    print(f"GATE {args.stage} {args.decision}")
    print(f"NEXT {manifest['next_stage']}")
    return 0


def append_feedback(root: Path, record: dict[str, Any]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "performance-feedback.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def cmd_feedback(args: argparse.Namespace) -> int:
    root = Path(args.root)
    manifest = load_manifest(root, args.campaign_id)
    asset = next(
        (item for item in manifest["assets"] if item["asset_id"] == args.asset_id),
        None,
    )
    if asset is None:
        raise CampaignError(f"Unknown asset: {args.asset_id}")

    metrics = {field: getattr(args, field) for field in METRIC_FIELDS}
    negative = [field for field, value in metrics.items() if value is not None and value < 0]
    if negative:
        raise CampaignError(
            "Performance metrics cannot be negative: " + ", ".join(negative)
        )
    if not any(value is not None for value in metrics.values()) and not args.metrics_unavailable:
        raise CampaignError(
            "Provide at least one metric or use --metrics-unavailable with a reason."
        )
    if args.metrics_unavailable and not clean_text(args.measurement_note):
        raise CampaignError("--metrics-unavailable requires --measurement-note.")
    if not clean_text(args.lesson) or not clean_text(args.next_action):
        raise CampaignError("Feedback requires --lesson and --next-action.")

    observed_at = args.observed_at or now_iso()
    record = {
        "schema_version": SCHEMA_VERSION,
        "campaign_id": manifest["campaign_id"],
        "asset_id": asset["asset_id"],
        "observed_at": observed_at,
        "published_at": clean_text(args.published_at),
        "post_url": asset["post_url"],
        "pillar": manifest["brief"]["pillar"],
        "hook": asset["hook"] or manifest["brief"]["primary_hook"],
        "format": asset["format"],
        "platform": asset["platform"],
        "funnel_role": asset["funnel_role"],
        "intended_outcome": asset["intended_outcome"],
        "success_signal": asset["success_signal"],
        "metrics": metrics,
        "metric_source": clean_text(args.metric_source),
        "metrics_unavailable": bool(args.metrics_unavailable),
        "measurement_note": clean_text(args.measurement_note),
        "lesson": clean_text(args.lesson),
        "next_cycle_action": clean_text(args.next_action),
    }
    append_feedback(root, record)
    asset["performance_recorded"] = True
    manifest["feedback_summary"] = {
        "records": manifest["feedback_summary"]["records"] + 1,
        "last_observed_at": observed_at,
        "latest_lesson": record["lesson"],
        "next_cycle_action": record["next_cycle_action"],
    }
    save_manifest(root, manifest)
    print(f"RECORDED feedback {args.campaign_id}/{args.asset_id}")
    return 0


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version is missing or unsupported")
    if not manifest.get("campaign_id"):
        errors.append("campaign_id is missing")
    governance = manifest.get("governance", {})
    if governance.get("notion_is_live_publish_source") is not True:
        errors.append("Notion live-source governance is not enabled")
    if governance.get("external_writes_allowed") is not False:
        errors.append("external writes must remain disabled")
    if governance.get("auto_publish_allowed") is not False:
        errors.append("auto publishing must remain disabled")

    assets = manifest.get("assets", [])
    asset_ids = [asset.get("asset_id") for asset in assets]
    if len(asset_ids) != len(set(asset_ids)):
        errors.append("asset IDs must be unique")
    known = set(asset_ids)
    for asset in assets:
        parent = asset.get("parent_asset_id")
        if parent and parent not in known:
            errors.append(
                f"asset {asset.get('asset_id')} references unknown parent {parent}"
            )
        if asset.get("funnel_role") not in FUNNEL_ROLES:
            errors.append(f"asset {asset.get('asset_id')} has invalid funnel role")
        if (
            asset.get("quality_gate") == "pass"
            and asset.get("artifact_path")
            and not Path(asset["artifact_path"]).exists()
        ):
            errors.append(
                f"asset {asset.get('asset_id')} artifact path does not exist"
            )

    parents = {
        asset["asset_id"]: asset.get("parent_asset_id")
        for asset in assets
        if asset.get("asset_id")
    }
    for asset_id in parents:
        seen: set[str] = set()
        current: str | None = asset_id
        while current:
            if current in seen:
                errors.append(f"asset graph contains a cycle at {current}")
                break
            seen.add(current)
            current = parents.get(current)

    stage_gates = manifest.get("stage_gates", {})
    for stage in STAGES:
        if stage not in stage_gates:
            errors.append(f"missing stage gate: {stage}")
            continue
        for event in stage_gates[stage].get("history", []):
            if event.get("decision") not in DECISIONS:
                errors.append(f"invalid decision in {stage} gate")
    return sorted(set(errors))


def cmd_validate(args: argparse.Namespace) -> int:
    manifest = load_manifest(Path(args.root), args.campaign_id)
    errors = validate_manifest(manifest)
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print(f"VALID {args.campaign_id}")
    print(f"NEXT {manifest['next_stage']}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    manifest = load_manifest(Path(args.root), args.campaign_id)
    print(render_brief(manifest))
    return 0


def add_common_campaign_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--campaign-id", required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage local NASR Campaign Graph records."
    )
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    sub = parser.add_subparsers(dest="command", required=True)

    intake = sub.add_parser("intake", help="Create a structured campaign intake.")
    intake.add_argument("--campaign-id")
    intake.add_argument(
        "--source-type",
        choices=["voice_note", "rough_idea", "article", "research_signal", "other"],
        default="rough_idea",
    )
    intake.add_argument("--raw-input", required=True)
    intake.add_argument("--source-ref", action="append")
    intake.add_argument("--title", required=True)
    intake.add_argument("--objective", required=True)
    intake.add_argument("--audience", required=True)
    intake.add_argument("--pillar", choices=sorted(PILLARS), required=True)
    intake.add_argument("--funnel-role", choices=sorted(FUNNEL_ROLES), required=True)
    intake.add_argument("--intended-outcome", required=True)
    intake.add_argument("--success-signal", required=True)
    intake.add_argument("--core-tension", default="")
    intake.add_argument("--chosen-angle", default="")
    intake.add_argument("--primary-hook", default="")
    intake.add_argument("--primary-asset-id", default="primary-linkedin-post")
    intake.add_argument("--primary-platform", default="linkedin")
    intake.add_argument("--primary-format", default="static_post")
    intake.add_argument("--primary-purpose", default="Primary campaign asset")
    intake.add_argument("--owner", default="CMO")
    intake.set_defaults(func=cmd_intake)

    direction = sub.add_parser(
        "direction", help="Record the selected angle after ideation."
    )
    add_common_campaign_arg(direction)
    direction.add_argument("--core-tension")
    direction.add_argument("--chosen-angle")
    direction.add_argument("--rejected-angle", action="append")
    direction.add_argument("--primary-hook")
    direction.set_defaults(func=cmd_direction)

    evidence = sub.add_parser("evidence", help="Add internal or external evidence.")
    add_common_campaign_arg(evidence)
    evidence.add_argument("--kind", choices=["internal", "external"], required=True)
    evidence.add_argument("--label", required=True)
    evidence.add_argument("--source", required=True)
    evidence.add_argument("--note", default="")
    evidence.set_defaults(func=cmd_add_evidence)

    asset = sub.add_parser("asset", help="Add a campaign asset or derivative.")
    add_common_campaign_arg(asset)
    asset.add_argument("--asset-id", required=True)
    asset.add_argument("--parent-asset-id")
    asset.add_argument("--platform", required=True)
    asset.add_argument("--format", required=True)
    asset.add_argument("--purpose", required=True)
    asset.add_argument("--owner", default="CMO")
    asset.add_argument("--hook", default="")
    asset.add_argument("--funnel-role", choices=sorted(FUNNEL_ROLES))
    asset.add_argument("--intended-outcome")
    asset.add_argument("--success-signal")
    asset.set_defaults(func=cmd_add_asset)

    update = sub.add_parser("update-asset", help="Update artifact and live-link fields.")
    add_common_campaign_arg(update)
    update.add_argument("--asset-id", required=True)
    update.add_argument(
        "--status",
        choices=["planned", "draft", "review", "approved", "completed", "published"],
    )
    update.add_argument("--artifact-path")
    update.add_argument("--notion-page-id")
    update.add_argument("--post-url")
    update.add_argument(
        "--quality-gate", choices=["pending", "pass", "loop_back", "not_applicable"]
    )
    update.set_defaults(func=cmd_update_asset)

    gate = sub.add_parser("gate", help="Record an explicit stage pass or loop-back.")
    add_common_campaign_arg(gate)
    gate.add_argument("--stage", choices=STAGES, required=True)
    gate.add_argument("--decision", choices=sorted(DECISIONS), required=True)
    gate.add_argument("--decided-by", required=True)
    gate.add_argument("--reason", default="")
    gate.add_argument("--evidence", action="append")
    gate.add_argument("--notion-status")
    gate.add_argument("--publisher-qa")
    gate.set_defaults(func=cmd_gate)

    feedback = sub.add_parser("feedback", help="Record tied performance feedback.")
    add_common_campaign_arg(feedback)
    feedback.add_argument("--asset-id", required=True)
    feedback.add_argument("--observed-at")
    feedback.add_argument("--published-at", default="")
    feedback.add_argument("--metric-source", default="manual")
    for field in METRIC_FIELDS:
        feedback.add_argument(f"--{field.replace('_', '-')}", type=int)
    feedback.add_argument("--metrics-unavailable", action="store_true")
    feedback.add_argument("--measurement-note", default="")
    feedback.add_argument("--lesson", required=True)
    feedback.add_argument("--next-action", required=True)
    feedback.set_defaults(func=cmd_feedback)

    validate = sub.add_parser("validate", help="Validate a campaign manifest.")
    add_common_campaign_arg(validate)
    validate.set_defaults(func=cmd_validate)

    status = sub.add_parser("status", help="Render a campaign status brief.")
    add_common_campaign_arg(status)
    status.set_defaults(func=cmd_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except CampaignError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
