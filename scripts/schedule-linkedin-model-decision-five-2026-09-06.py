#!/usr/bin/env python3
"""Idempotently schedule the approved Model Decision #5 LinkedIn post.

Dry-run is the default. ``--apply`` creates the Notion row only after all
approval, collision, asset, and duplicate guards pass. This script never
publishes to LinkedIn.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path


WORKSPACE = Path("/root/.openclaw/workspace")
CMO_SCRIPTS = Path("/root/.openclaw/workspace-cmo/scripts")
sys.path.insert(0, str(CMO_SCRIPTS))

from cmo_notion_posting import (  # noqa: E402
    content_db_id,
    date_value,
    notion_request,
    resolve_publish_candidate,
    select_value,
    title_text,
    url_value,
)


TARGET_DATE = "2026-09-06"
TITLE = "The model is decision #5"
PACKAGE = WORKSPACE / "output/linkedin/the-model-is-decision-five-authority-draft-2026-08-18.md"
ASSET = WORKSPACE / "output/linkedin/the-model-is-decision-five-authority-visual-2026-08-18.png"
EXPECTED_ASSET_SHA256 = "88778688e58498449a67a35c6a169df3e139504bdbea251a627b3be4ad5d9ae4"
EXPECTED_DIMENSIONS = (1122, 1402)
CAPTION_APPROVAL_MESSAGE = "63633"
SCHEDULING_APPROVAL_MESSAGE = "63635"
VISUAL_QA_MARKER = "Visual QA: PASS - reference-checked handmade sketchnote"

CAPTION = """The model should be decision #5 in an enterprise AI program.

Across eight countries and 300+ concurrent projects, I learned a hard operating lesson: a tool only scales after ownership, workflow, and decision rules are explicit. AI does not change that.

Most teams start with the model, vendor, or framework.

Start here instead:

1. Outcome: What business result must change?
2. Workflow: Where will AI enter the work?
3. Trusted context: Which data and institutional knowledge can it use?
4. Controls: What can it decide, what requires approval, and how do we stop it?
5. Model: Which capability is sufficient for this job?
6. Measurement: Did time, cost, risk, or decision quality improve?

A stronger model cannot repair unclear ownership. It cannot create trusted context from scattered files. And it cannot decide an organisation's risk appetite.

The model matters. It just arrives later than most teams think.

If your AI initiative started tomorrow, which of the first four decisions would still be unresolved?"""


def rich_text(value: str) -> list[dict]:
    return [
        {"type": "text", "text": {"content": value[index : index + 1900]}}
        for index in range(0, len(value), 1900)
    ]


def paragraph(value: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": rich_text(value)},
    }


def png_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", data[16:24])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def query_date() -> list[dict]:
    payload = {
        "filter": {"property": "Planned Date", "date": {"equals": TARGET_DATE}},
        "page_size": 20,
    }
    return notion_request("POST", f"databases/{content_db_id()}/query", payload).get("results", [])


def query_title() -> list[dict]:
    payload = {
        "filter": {"property": "Title", "title": {"equals": TITLE}},
        "page_size": 20,
    }
    return notion_request("POST", f"databases/{content_db_id()}/query", payload).get("results", [])


def image_intent(asset_hash: str) -> str:
    return (
        "Approved paired visual for the governed execution stack Authority post. "
        f"Final local asset: `{ASSET}`\n"
        f"{VISUAL_QA_MARKER}\n"
        f"Visual SHA-256: {asset_hash}.\n"
        f"Exact caption and visual approved by Ahmed on 2026-08-18 via Telegram message {CAPTION_APPROVAL_MESSAGE}.\n"
        f"Scheduling approved by Ahmed on 2026-08-18 via Telegram message {SCHEDULING_APPROVAL_MESSAGE}.\n"
        "Publish slot: 09:30 Africa/Cairo on 2026-09-06.\n"
        "LinkedIn dimension override: approved exact 1122 x 1402 px visual; preserve the approved asset without resampling."
    )


def validate() -> list[str]:
    errors: list[str] = []
    if not PACKAGE.is_file():
        errors.append(f"missing_package:{PACKAGE}")
    elif f"Telegram message `{CAPTION_APPROVAL_MESSAGE}`" not in PACKAGE.read_text():
        errors.append("caption_visual_approval_not_recorded_in_package")
    if not ASSET.is_file():
        errors.append(f"missing_asset:{ASSET}")
        return errors
    actual_hash = sha256(ASSET)
    if actual_hash != EXPECTED_ASSET_SHA256:
        errors.append(f"asset_hash_mismatch:{actual_hash}")
    dimensions = png_dimensions(ASSET)
    if dimensions != EXPECTED_DIMENSIONS:
        errors.append(f"asset_dimensions_mismatch:{dimensions}")
    if len(CAPTION) > 3000:
        errors.append(f"caption_too_long:{len(CAPTION)}")
    if CAPTION.count("?") < 1:
        errors.append("missing_question")
    return errors


def create_page(asset_hash: str) -> dict:
    caption_hash = hashlib.sha256(CAPTION.encode("utf-8")).hexdigest()
    details = [
        "Series: Experience-backed authority series",
        "Pillar: AI execution and governance",
        "Funnel role: Authority",
        "Intended reader action: Reorder an AI initiative around the operating system before selecting the model.",
        "Evidence: verified Network International scope across eight countries and 300+ concurrent projects; the post does not claim those projects were AI projects.",
        f"Exact caption and visual approval: Ahmed, Telegram message {CAPTION_APPROVAL_MESSAGE}, 2026-08-18. Caption SHA-256: {caption_hash}. Visual SHA-256: {asset_hash}.",
        f"Scheduling authorization: Ahmed, Telegram message {SCHEDULING_APPROVAL_MESSAGE}, 2026-08-18, for the first open Authority slot after 2026-09-05.",
        "Publish slot: 2026-09-06 at 09:30 Africa/Cairo through the approved daily publisher.",
        "Immediate publishing: NOT AUTHORIZED by this write; Post URL and Published At must remain empty until the scheduled publisher succeeds.",
        f"Final copy package: {PACKAGE}",
        f"Final local asset: {ASSET}",
        VISUAL_QA_MARKER,
    ]
    payload = {
        "parent": {"database_id": content_db_id()},
        "properties": {
            "Title": {"title": rich_text(TITLE)},
            "Status": {"select": {"name": "Scheduled"}},
            "Planned Date": {"date": {"start": TARGET_DATE}},
            "Day": {"select": {"name": "Sunday"}},
            "Owner": {"select": {"name": "CMO"}},
            "Funnel Role": {"select": {"name": "Authority"}},
            "Topic": {"select": {"name": "AI Automation"}},
            "Hook": {"rich_text": rich_text(CAPTION.splitlines()[0])},
            "Draft": {"rich_text": rich_text(CAPTION)},
            "Image Intent": {"rich_text": rich_text(image_intent(asset_hash))},
            "Retry Count": {"number": 0},
        },
        "children": [paragraph(item) for item in details],
    }
    return notion_request("POST", "pages", payload)


def verified_result(action: str, page: dict) -> dict:
    candidate = resolve_publish_candidate(TARGET_DATE)
    record = candidate.get("record") or {}
    rows = query_date()
    checks = {
        "single_row_on_date": len(rows) == 1 and rows[0].get("id") == page.get("id"),
        "single_publish_candidate": candidate.get("ok") is True,
        "title_exact": record.get("title") == TITLE,
        "status_scheduled": record.get("status") == "Scheduled",
        "date_exact": record.get("planned_date") == TARGET_DATE,
        "owner_cmo": record.get("owner") == "CMO",
        "funnel_authority": record.get("funnel_role") == "Authority",
        "caption_exact": record.get("content") == CAPTION,
        "asset_source_exact": (record.get("asset") or {}).get("source") == "image_intent_final_asset",
        "asset_path_exact": (record.get("asset") or {}).get("value") == str(ASSET),
        "asset_dimensions_exact": record.get("asset_dimensions") == {"width": 1122, "height": 1402},
        "dimension_override_recorded": any(
            warning == "approved_linkedin_dimension_override:1122x1402"
            for warning in record.get("warnings", [])
        ),
        "not_published": not record.get("post_url") and not record.get("published_at"),
        "no_preflight_errors": not record.get("errors"),
    }
    return {
        "ok": all(checks.values()),
        "action": action,
        "date": TARGET_DATE,
        "time": "09:30 Africa/Cairo",
        "page_id": page.get("id", ""),
        "url": page.get("url", ""),
        "anything_published": False,
        "checks": checks,
        "warnings": record.get("warnings", []),
        "errors": record.get("errors", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    errors = validate()
    date_rows = query_date()
    title_rows = query_title()
    exact = [
        page
        for page in title_rows
        if date_value(page.get("properties", {})) == TARGET_DATE
        and select_value(page.get("properties", {}), "Status") == "Scheduled"
    ]

    if len(exact) == 1 and len(date_rows) == 1 and exact[0].get("id") == date_rows[0].get("id"):
        result = verified_result("existing_scheduled_verified", exact[0])
        if errors:
            result["ok"] = False
            result["validation_errors"] = errors
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if errors or date_rows or title_rows:
        result = {
            "ok": False,
            "action": "blocked",
            "validation_errors": errors,
            "date_conflicts": [
                {
                    "page_id": page.get("id"),
                    "title": title_text(page.get("properties", {})),
                    "status": select_value(page.get("properties", {}), "Status"),
                    "post_url": url_value(page.get("properties", {})),
                }
                for page in date_rows
            ],
            "title_conflicts": [
                {
                    "page_id": page.get("id"),
                    "date": date_value(page.get("properties", {})),
                    "status": select_value(page.get("properties", {}), "Status"),
                    "post_url": url_value(page.get("properties", {})),
                }
                for page in title_rows
            ],
        }
        print(json.dumps(result, indent=2))
        return 1

    if not args.apply:
        print(
            json.dumps(
                {
                    "ok": True,
                    "action": "dry_run_ready",
                    "date": TARGET_DATE,
                    "time": "09:30 Africa/Cairo",
                    "title": TITLE,
                    "asset": str(ASSET),
                    "asset_sha256": EXPECTED_ASSET_SHA256,
                    "asset_dimensions": list(EXPECTED_DIMENSIONS),
                    "caption_chars": len(CAPTION),
                    "anything_published": False,
                },
                indent=2,
            )
        )
        return 0

    created = create_page(sha256(ASSET))
    result = verified_result("created_and_verified", created)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
