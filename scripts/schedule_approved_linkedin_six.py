#!/usr/bin/env python3
"""Idempotently schedule Ahmed's six approved August 2026 LinkedIn posts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


CMO_SCRIPTS = Path("/root/.openclaw/workspace-cmo/scripts")
sys.path.insert(0, str(CMO_SCRIPTS))

import cmo_notion_posting as notion  # noqa: E402
from finalize_2026_08_linkedin_six_post_recovery import ITEMS, rich_text  # noqa: E402


APPROVAL_MARKER = "ITEM-LEVEL-CONTENT-VISUAL-APPROVAL-TELEGRAM-63195"
SCHEDULING_MARKER = "SCHEDULING-AUTHORIZATION-TELEGRAM-63200"
ACTIVE_STATUSES = {"Approved", "Scheduled", "Publishing", "Posted", "Failed"}


def body_for(page_id: str) -> str:
    return notion.extract_page_body(page_id)["text"]


def exact_date_rows(target_date: str) -> list[dict]:
    query = {
        "filter": {"property": "Planned Date", "date": {"equals": target_date}},
        "page_size": 100,
    }
    return notion.notion_request(
        "POST", f"databases/{notion.content_db_id()}/query", query
    ).get("results", [])


def summarize(page: dict, item: dict) -> dict:
    props = page.get("properties", {})
    assets = notion.file_values(props, "Approved Asset")
    body = body_for(item["page_id"])
    return {
        "date": notion.date_value(props, "Planned Date"),
        "title": notion.title_text(props),
        "page_id": item["page_id"],
        "status": notion.select_value(props, "Status"),
        "caption_exact": notion.rich_text_value(props, "Draft") == item["caption"],
        "approval_marker": APPROVAL_MARKER in body,
        "scheduling_marker": SCHEDULING_MARKER in body,
        "approved_asset_names": [asset["name"] for asset in assets],
        "post_url": notion.url_value(props, "Post URL"),
        "published_at": notion.date_value(props, "Published At"),
    }


def validate(page: dict, item: dict) -> None:
    props = page.get("properties", {})
    status = notion.select_value(props, "Status")
    if status not in {"Draft", "Scheduled"}:
        raise RuntimeError(f"Refusing {item['date']}: unexpected status {status!r}")
    if notion.title_text(props) != item["title"]:
        raise RuntimeError(f"Refusing {item['date']}: title mismatch")
    if notion.date_value(props, "Planned Date") != item["date"]:
        raise RuntimeError(f"Refusing {item['date']}: planned-date mismatch")
    if notion.rich_text_value(props, "Draft") != item["caption"]:
        raise RuntimeError(f"Refusing {item['date']}: approved caption mismatch")
    body = body_for(item["page_id"])
    intent = notion.rich_text_value(props, "Image Intent")
    if APPROVAL_MARKER not in body or APPROVAL_MARKER not in intent:
        raise RuntimeError(f"Refusing {item['date']}: approval marker missing")
    if "Content approval: APPROVED" not in body:
        raise RuntimeError(f"Refusing {item['date']}: content approval missing")
    expected_visual_state = (
        "Visual approval: APPROVED" if "asset" in item else "Visual approval: NOT_APPLICABLE"
    )
    if expected_visual_state not in body:
        raise RuntimeError(f"Refusing {item['date']}: visual approval mismatch")
    actual_assets = [asset["name"] for asset in notion.file_values(props, "Approved Asset")]
    expected_assets = [Path(item["asset"]).name] if "asset" in item else []
    if actual_assets != expected_assets:
        raise RuntimeError(
            f"Refusing {item['date']}: expected assets {expected_assets!r}, got {actual_assets!r}"
        )
    if notion.url_value(props, "Post URL") or notion.date_value(props, "Published At"):
        raise RuntimeError(f"Refusing {item['date']}: published-state fields are populated")

    date_rows = exact_date_rows(item["date"])
    if len(date_rows) != 1 or date_rows[0].get("id") != item["page_id"]:
        details = [
            {
                "id": row.get("id"),
                "title": notion.title_text(row.get("properties", {})),
                "status": notion.select_value(row.get("properties", {}), "Status"),
            }
            for row in date_rows
        ]
        raise RuntimeError(f"Refusing {item['date']}: date collision/duplicate {details!r}")


def scheduling_blocks(item: dict) -> list[dict]:
    lines = [
        SCHEDULING_MARKER,
        "Scheduling source: Ahmed Nasr, Telegram message 63200 on 2026-08-15.",
        f"Scheduling scope: exact approved caption/visual pair for {item['date']} only.",
        "Workflow state authorized: Scheduled.",
        "Publish slot: 09:30 Africa/Cairo on Planned Date via the approved auto-poster.",
        "Immediate publishing: NOT AUTHORIZED; no public action was performed by this scheduling write.",
    ]
    blocks = []
    for index, line in enumerate(lines):
        kind = "heading_2" if index == 0 else "paragraph"
        blocks.append({"object": "block", "type": kind, kind: {"rich_text": rich_text(line)}})
    return blocks


def run(apply: bool) -> dict:
    before_pages = [notion.get_page(item["page_id"]) for item in ITEMS]
    for page, item in zip(before_pages, ITEMS):
        validate(page, item)

    if apply:
        for page, item in zip(before_pages, ITEMS):
            status = notion.select_value(page.get("properties", {}), "Status")
            if status == "Draft":
                notion.notion_request(
                    "PATCH",
                    f"pages/{item['page_id']}",
                    {"properties": {"Status": {"select": {"name": "Scheduled"}}}},
                )
            if SCHEDULING_MARKER not in body_for(item["page_id"]):
                notion.notion_request(
                    "PATCH",
                    f"blocks/{item['page_id']}/children",
                    {"children": scheduling_blocks(item)},
                )

    after_pages = [notion.get_page(item["page_id"]) for item in ITEMS]
    rows = [summarize(page, item) for page, item in zip(after_pages, ITEMS)]
    expected_status = "Scheduled" if apply else None
    ok = all(
        row["date"] == item["date"]
        and row["title"] == item["title"]
        and row["caption_exact"]
        and row["approval_marker"]
        and (row["scheduling_marker"] if apply else True)
        and (row["status"] == expected_status if apply else row["status"] in {"Draft", "Scheduled"})
        and not row["post_url"]
        and not row["published_at"]
        for row, item in zip(rows, ITEMS)
    )
    return {
        "ok": ok,
        "apply": apply,
        "database_id": notion.content_db_id(),
        "approval_marker": APPROVAL_MARKER,
        "scheduling_marker": SCHEDULING_MARKER,
        "publish_slot": "09:30 Africa/Cairo on each Planned Date",
        "rows": rows,
        "anything_published": any(row["post_url"] or row["published_at"] for row in rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.apply), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
