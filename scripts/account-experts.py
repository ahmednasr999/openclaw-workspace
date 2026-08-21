#!/usr/bin/env python3
"""Maintain bounded, evidence-linked employer intelligence dossiers."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path("/root/.openclaw/workspace")
DATA_DIR = ROOT / "data" / "account-experts"
ACCOUNTS_DIR = DATA_DIR / "accounts"
REGISTRY_PATH = DATA_DIR / "registry.json"
REPORT_DIR = ROOT / "reports" / "account-experts"
ACTIVE_LIMIT = 7
REQUIRED_FIELDS = {"schema_version", "slug", "employer", "identity_status", "priority", "roles", "sources", "last_refreshed_at"}
IDENTITY_STATES = {"verified", "probable", "ambiguous"}


class AccountExpertError(ValueError):
    pass


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise AccountExpertError(f"invalid or missing JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise AccountExpertError(f"expected JSON object: {path}")
    return data


def validate(dossier: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_FIELDS - dossier.keys())
    if missing:
        raise AccountExpertError("missing required fields: " + ", ".join(missing))
    slug = str(dossier["slug"])
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise AccountExpertError("slug must be lowercase kebab-case")
    if dossier["identity_status"] not in IDENTITY_STATES:
        raise AccountExpertError("invalid identity_status")
    if not isinstance(dossier["roles"], list) or not dossier["roles"]:
        raise AccountExpertError("at least one role is required")
    if not isinstance(dossier["sources"], list) or not dossier["sources"]:
        raise AccountExpertError("at least one evidence source is required")
    try:
        dt.datetime.fromisoformat(str(dossier["last_refreshed_at"]))
    except ValueError as exc:
        raise AccountExpertError("last_refreshed_at must be ISO-8601") from exc
    for collection in ("strategy", "decision_makers", "signals", "application_history", "hypotheses", "next_actions"):
        value = dossier.get(collection, [])
        if not isinstance(value, list):
            raise AccountExpertError(f"{collection} must be a list")


def source_label(source: dict[str, Any]) -> str:
    title = source.get("title") or source.get("url") or source.get("path") or "source"
    locator = source.get("url") or source.get("path") or ""
    return f"{title} ({locator})" if locator and locator != title else str(title)


def render_dossier(dossier: dict[str, Any]) -> str:
    def bullets(items: list[Any], formatter=lambda item: str(item)) -> str:
        return "\n".join(f"- {formatter(item)}" for item in items) or "- No verified entries yet."

    def evidence_item(item: dict[str, Any]) -> str:
        statement = item.get("statement") or item.get("name") or item.get("event") or str(item)
        source = item.get("source") or "source not recorded"
        confidence = item.get("confidence") or "unspecified"
        return f"{statement} [confidence: {confidence}; source: {source}]"

    def role_item(item: dict[str, Any]) -> str:
        return f"{item.get('title')} - score {item.get('score', '?')}; status {item.get('status', 'unknown')}; {item.get('url', '')}".strip()

    return f"""# Account Expert: {dossier['employer']}

- Identity: {dossier['identity_status']}
- Priority: {dossier['priority']}
- Last refreshed: {dossier['last_refreshed_at']}
- Owner: {dossier.get('owner', 'NASR/main with HR evidence input')}

## Active Roles

{bullets(dossier['roles'], role_item)}

## Verified Strategy and Context

{bullets(dossier.get('strategy', []), evidence_item)}

## Decision-Makers

{bullets(dossier.get('decision_makers', []), evidence_item)}

## Recent Signals

{bullets(dossier.get('signals', []), evidence_item)}

## Application History

{bullets(dossier.get('application_history', []), evidence_item)}

## Hypotheses — Not Facts

{bullets(dossier.get('hypotheses', []), evidence_item)}

## Next Actions

{bullets(dossier.get('next_actions', []), evidence_item)}

## Evidence Sources

{bullets(dossier['sources'], source_label)}

## Guardrail

This dossier is decision support, not authority to contact anyone. Identity, relationship, and hiring-chain claims require source evidence before use.
"""


def refresh_registry(data_dir: Path = DATA_DIR, report_dir: Path = REPORT_DIR) -> dict[str, Any]:
    accounts_dir = data_dir / "accounts"
    dossiers = []
    for path in sorted(accounts_dir.glob("*.json")):
        dossier = load_json(path)
        validate(dossier)
        dossiers.append((path, dossier))
    if len(dossiers) > ACTIVE_LIMIT:
        raise AccountExpertError(f"active dossier limit exceeded: {len(dossiers)} > {ACTIVE_LIMIT}")
    dossiers.sort(key=lambda pair: (-int(pair[1].get("priority", 0)), pair[1]["employer"]))
    rows = []
    for path, dossier in dossiers:
        report_path = report_dir / f"{dossier['slug']}.md"
        atomic_write(report_path, render_dossier(dossier))
        rows.append({
            "slug": dossier["slug"],
            "employer": dossier["employer"],
            "priority": dossier["priority"],
            "identity_status": dossier["identity_status"],
            "last_refreshed_at": dossier["last_refreshed_at"],
            "dossier": str(path),
            "report": str(report_path),
            "active_roles": len(dossier["roles"]),
        })
    registry = {
        "schema_version": 1,
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "active_limit": ACTIVE_LIMIT,
        "accounts": rows,
        "guardrails": {
            "outbound_actions": "approval-required",
            "auto_delete": False,
            "identity_claims_require_evidence": True,
        },
    }
    atomic_write(data_dir / "registry.json", json.dumps(registry, indent=2, sort_keys=True) + "\n")
    index = ["# Priority Account Experts", "", f"Active: {len(rows)}/{ACTIVE_LIMIT}", ""]
    index.extend(f"- [{row['employer']}]({Path(row['report']).name}) - priority {row['priority']}; identity {row['identity_status']}" for row in rows)
    atomic_write(report_dir / "latest.md", "\n".join(index) + "\n")
    return registry


def upsert(input_path: Path, data_dir: Path, report_dir: Path) -> dict[str, Any]:
    dossier = load_json(input_path)
    validate(dossier)
    target = data_dir / "accounts" / f"{dossier['slug']}.json"
    atomic_write(target, json.dumps(dossier, indent=2, sort_keys=True) + "\n")
    registry = refresh_registry(data_dir, report_dir)
    return {"status": "ok", "dossier": str(target), "accounts": len(registry["accounts"])}


def audit(data_dir: Path = DATA_DIR, now: dt.datetime | None = None) -> dict[str, Any]:
    now = now or dt.datetime.now().astimezone()
    registry_path = data_dir / "registry.json"
    registry = load_json(registry_path)
    stale = []
    ambiguous = []
    for row in registry.get("accounts", []):
        try:
            stamp = dt.datetime.fromisoformat(row["last_refreshed_at"])
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=now.tzinfo)
            if (now - stamp).days > 14:
                stale.append(row["slug"])
        except (KeyError, ValueError, TypeError):
            stale.append(row.get("slug", "unknown"))
        if row.get("identity_status") == "ambiguous":
            ambiguous.append(row.get("slug", "unknown"))
    return {
        "status": "attention" if stale or ambiguous else "ok",
        "active": len(registry.get("accounts", [])),
        "limit": registry.get("active_limit", ACTIVE_LIMIT),
        "stale": stale,
        "ambiguous_identity": ambiguous,
        "mutations_performed": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--report-dir", type=Path, default=REPORT_DIR)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("refresh")
    upsert_parser = sub.add_parser("upsert")
    upsert_parser.add_argument("--file", type=Path, required=True)
    sub.add_parser("audit")
    args = parser.parse_args()
    try:
        if args.command == "refresh":
            result = refresh_registry(args.data_dir, args.report_dir)
            output = {"status": "ok", "accounts": len(result["accounts"]), "registry": str(args.data_dir / "registry.json")}
        elif args.command == "upsert":
            output = upsert(args.file, args.data_dir, args.report_dir)
        else:
            output = audit(args.data_dir)
    except AccountExpertError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
