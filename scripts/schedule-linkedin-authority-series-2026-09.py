#!/usr/bin/env python3
"""Idempotently schedule the two approved September 2026 authority posts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


WORKSPACE = Path("/root/.openclaw/workspace")
CMO_SCRIPTS = Path("/root/.openclaw/workspace-cmo/scripts")
sys.path.insert(0, str(CMO_SCRIPTS))
sys.path.insert(0, str(WORKSPACE / "scripts"))

import cmo_notion_posting as notion  # noqa: E402
from post_approved_14day_batch import existing_success_for_date  # noqa: E402

SEED_PATH = WORKSPACE / "scripts" / "seed-linkedin-authority-series-2026-09.py"
seed_spec = importlib.util.spec_from_file_location("seed_linkedin_authority_series_2026_09", SEED_PATH)
if seed_spec is None or seed_spec.loader is None:
    raise RuntimeError(f"Could not load seed module from {SEED_PATH}")
seed = importlib.util.module_from_spec(seed_spec)
seed_spec.loader.exec_module(seed)

POSTS = seed.POSTS
CAPTION_APPROVAL_MARKER = seed.CAPTION_APPROVAL_MARKER
VISUAL_QA_MARKER = seed.VISUAL_QA_MARKER
approved_image_intent = seed.approved_image_intent
exact_caption_approval_marker = seed.exact_caption_approval_marker
rich_text = seed.rich_text
visual_approval_marker = seed.visual_approval_marker


SCHEDULING_MARKER = "SCHEDULING-AUTHORIZATION-TELEGRAM-63582"
PUBLISH_SLOT = "09:30 Africa/Cairo on each Planned Date"


def paragraph(value: str, heading: bool = False) -> dict:
    kind = "heading_2" if heading else "paragraph"
    return {
        "object": "block",
        "type": kind,
        kind: {"rich_text": rich_text(value)},
    }


def query_date(target_date: str) -> list[dict]:
    payload = {
        "filter": {"property": "Planned Date", "date": {"equals": target_date}},
        "page_size": 20,
    }
    return notion.notion_request(
        "POST", f"databases/{notion.content_db_id()}/query", payload
    ).get("results", [])


def scheduling_image_intent(post: dict) -> str:
    return (
        "Approved paired visual. "
        f"Final local asset: `{post['visual_asset']}`\n"
        f"{VISUAL_QA_MARKER}\n"
        f"Visual approval: APPROVED by Ahmed on 2026-08-17 via Telegram message {post['visual_message_id']}.\n"
        "Scheduling authorization: APPROVED by Ahmed on 2026-08-17 via Telegram message 63582.\n"
        f"Publish slot: {PUBLISH_SLOT}."
    )


def scheduling_blocks(post: dict) -> list[dict]:
    caption_sha = hashlib.sha256(post["draft"].encode("utf-8")).hexdigest()
    return [
        paragraph(SCHEDULING_MARKER, heading=True),
        paragraph("Scheduling source: Ahmed Nasr, Telegram message 63582 on 2026-08-17."),
        paragraph(
            f"Scheduling scope: exact approved caption and visual pair for {post['date']} only. "
            f"Caption SHA-256: {caption_sha}. Visual SHA-256: {post['visual_sha256']}."
        ),
        paragraph("Workflow state authorized: Scheduled."),
        paragraph(f"Publish slot: {PUBLISH_SLOT} via the approved daily publisher."),
        paragraph("Immediate publishing: NOT AUTHORIZED; no public post was created by this scheduling write."),
    ]


def validate_row(page: dict, post: dict) -> dict:
    props = page.get("properties", {})
    page_id = page.get("id", "")
    body = notion.extract_page_body(page_id)["text"]
    status = notion.select_value(props, "Status")
    asset = Path(post["visual_asset"])
    actual_sha = hashlib.sha256(asset.read_bytes()).hexdigest() if asset.is_file() else ""
    success = existing_success_for_date(post["date"])
    date_rows = query_date(post["date"])

    checks = {
        "status_schedulable": status in {"Draft", "Scheduled"},
        "one_row_on_date": len(date_rows) == 1 and date_rows[0].get("id") == page_id,
        "title_exact": notion.title_text(props) == post["title"],
        "date_exact": notion.date_value(props, "Planned Date") == post["date"],
        "owner_cmo": notion.select_value(props, "Owner") == "CMO",
        "caption_exact": notion.rich_text_value(props, "Draft") == post["draft"],
        "caption_approval_recorded": exact_caption_approval_marker(post) in body
        or CAPTION_APPROVAL_MARKER in body,
        "visual_approval_exact": visual_approval_marker(post) in body,
        "visual_qa_recorded": VISUAL_QA_MARKER in body,
        "asset_exists": asset.is_file(),
        "asset_hash_exact": actual_sha == post["visual_sha256"],
        "image_intent_approved": notion.rich_text_value(props, "Image Intent")
        in {approved_image_intent(post), scheduling_image_intent(post)},
        "retry_count_zero": notion.number_value(props, "Retry Count") == 0,
        "not_published": not notion.url_value(props, "Post URL")
        and not notion.date_value(props, "Published At"),
        "no_success_ledger_entry": not bool(success),
    }
    if not all(checks.values()):
        raise RuntimeError(
            f"Refusing to schedule {post['date']}: "
            + json.dumps({"checks": checks, "existing_success": success}, ensure_ascii=False)
        )
    return {"page_id": page_id, "status": status, "body": body, "checks": checks}


def run(apply: bool) -> dict:
    validated = []
    for post in POSTS:
        rows = query_date(post["date"])
        if len(rows) != 1:
            raise RuntimeError(f"Expected exactly one row for {post['date']}; found {len(rows)}")
        validated.append(validate_row(rows[0], post))

    if apply:
        for post, row in zip(POSTS, validated):
            if row["status"] == "Draft" or notion.rich_text_value(
                notion.get_page(row["page_id"]).get("properties", {}), "Image Intent"
            ) != scheduling_image_intent(post):
                notion.notion_request(
                    "PATCH",
                    f"pages/{row['page_id']}",
                    {
                        "properties": {
                            "Status": {"select": {"name": "Scheduled"}},
                            "Image Intent": {"rich_text": rich_text(scheduling_image_intent(post))},
                        }
                    },
                )
            if SCHEDULING_MARKER not in row["body"]:
                notion.notion_request(
                    "PATCH",
                    f"blocks/{row['page_id']}/children",
                    {"children": scheduling_blocks(post)},
                )

    results = []
    for post in POSTS:
        candidate = notion.resolve_publish_candidate(post["date"])
        record = candidate.get("record") or {}
        expected_status = "Scheduled" if apply else None
        ok = (
            candidate.get("ok") is True
            if apply
            else candidate.get("kind") == "no_approved_or_scheduled"
            or candidate.get("ok") is True
        )
        if apply:
            ok = bool(
                ok
                and record.get("status") == expected_status
                and record.get("content") == post["draft"]
                and record.get("asset", {}).get("source") == "image_intent_final_asset"
                and record.get("asset", {}).get("value") == post["visual_asset"]
                and record.get("asset_dimensions") == {"width": 1080, "height": 1350}
                and not record.get("errors")
            )
        results.append(
            {
                "date": post["date"],
                "title": post["title"],
                "ok": ok,
                "status": record.get("status") if record else "Draft",
                "page_id": record.get("page_id") or validated[len(results)]["page_id"],
                "asset": record.get("asset"),
                "asset_dimensions": record.get("asset_dimensions"),
                "warnings": record.get("warnings", []),
                "errors": record.get("errors", []),
            }
        )

    return {
        "ok": all(item["ok"] for item in results),
        "apply": apply,
        "scheduling_marker": SCHEDULING_MARKER,
        "publish_slot": PUBLISH_SLOT,
        "anything_published": False,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    result = run(args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
