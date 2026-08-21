#!/usr/bin/env python3
"""Idempotently seed two draft-only authority posts in the Notion calendar."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


CMO_SCRIPTS = Path("/root/.openclaw/workspace-cmo/scripts")
sys.path.insert(0, str(CMO_SCRIPTS))

from cmo_notion_posting import (  # noqa: E402
    content_db_id,
    date_value,
    extract_page_body,
    notion_request,
    number_value,
    rich_text_value,
    select_value,
    title_text,
)


POSTS = [
    {
        "date": "2026-09-02",
        "day": "Wednesday",
        "title": "One SuperApp can hide four operating models.",
        "topic": "FinTech",
        "funnel_role": "Authority",
        "draft": """One SuperApp can hide four operating models.

I once designed the architecture for a platform combining payments, banking, e-commerce, and lifestyle services.

From the customer side, the promise was one experience.

From the operating side, every added service brought another owner, exception path, partner dependency, and control boundary.

That is the part enterprise architecture diagrams often understate.

A unified interface does not create unified accountability.

Before scaling a multi-service platform, leadership needs four answers:

• Who owns the end-to-end customer journey?
• Which team resolves cross-service failures?
• Which rules remain common across every service?
• Where can a partner dependency stop the whole journey?

The platform becomes credible when the operating model is as integrated as the interface.

Where does your customer experience look unified while accountability remains fragmented?

#FinTech #ProductStrategy #OperatingModel #DigitalTransformation""",
        "image_intent": (
            "Draft-only visual concept. Premium hand-drawn sketchnote on warm off-white paper with black ink and restrained "
            "orange accents. Show one customer-facing SuperApp opening into four backstage operating lanes: payments, banking, "
            "e-commerce, and lifestyle. Use one shared journey owner and control boundary as the system metaphor. No final asset "
            "exists and no visual is approved. Do not schedule or publish until Ahmed approves the exact caption and paired visual."
        ),
        "evidence": (
            "Verified source: memory/master-cv-data.md, PaySky Country Manager role. Ahmed designed the SuperApp architecture "
            "integrating payments, banking, e-commerce, and lifestyle services."
        ),
        "visual_asset": "/root/.openclaw/workspace/output/linkedin/one-superapp-four-operating-models-visual-2026-09-02.png",
        "visual_message_id": "63575",
        "visual_sha256": "2821a5f87b5afa78a3c92c38e5cbe4a26dbfd4463a11226b1d54060397fd0ae9",
    },
    {
        "date": "2026-09-05",
        "day": "Saturday",
        "title": "One execution risk followed me across four industries.",
        "topic": "Career Story",
        "funnel_role": "Conversion",
        "draft": """After 20+ years across telecom infrastructure, e-commerce, payments, and healthcare transformation, one execution risk kept returning.

The handoff.

A strategy can be sound.
A platform can be capable.
A team can be competent.

Work still slows when one function believes another owns the next decision.

The sectors changed. The symptoms did not:

• evidence arrives after the decision window
• exceptions have no named owner
• local teams wait for central approval
• executives see the delay only after the milestone slips

The leadership response is to govern the handoff, not only the function.

For every critical transition, define what moves, who accepts it, how long they have, and what triggers escalation.

Most operating models describe boxes. Execution performance is decided between them.

Which handoff creates the most invisible delay in your organization?

#Leadership #OperatingModel #DigitalTransformation #Execution""",
        "image_intent": (
            "Intentional draft-only text post for a controlled format test against the 16 August breakout. No visual planned. "
            "Do not schedule or publish until Ahmed approves the exact caption and confirms the text-only format."
        ),
        "evidence": (
            "Verified source: memory/master-cv-data.md. Ahmed has 20+ years across telecom infrastructure, e-commerce, "
            "payments, and healthcare transformation. The handoff diagnosis is explicitly presented as his operating judgment."
        ),
        "visual_asset": "/root/.openclaw/workspace/output/linkedin/execution-breaks-at-handoff-visual-2026-09-05.png",
        "visual_message_id": "63576",
        "visual_sha256": "043dbaa1c554a02436e89258ddc1928564f792cba23eb21cde1ca571e65f6bbb",
    },
]


CAPTION_APPROVAL_MARKER = (
    "Caption approval: Ahmed explicitly approved the exact caption in the current Telegram conversation on 2026-08-17. "
    "This approval does not approve a visual, text-only format, scheduling, or publishing. Status must remain Draft until "
    "the remaining asset and action gates are explicitly approved."
)


def exact_caption_approval_marker(post: dict) -> str:
    caption_sha256 = hashlib.sha256(post["draft"].encode("utf-8")).hexdigest()
    return (
        f"Exact caption approval: Ahmed explicitly approved the current {post['date']} caption in the Telegram "
        f"conversation on 2026-08-17. Caption SHA-256: {caption_sha256}. This approval does not schedule or "
        "publish the post. Status must remain Draft until the action gate is explicitly approved."
    )

CAPTION_REVISION_MARKER = (
    "Caption revision: On 2026-08-17 Ahmed requested removal of the company name from the 2 September caption. "
    "The earlier exact-caption approval is superseded for this post. The revised caption remains Draft and requires "
    "fresh exact-caption, visual, scheduling, and publishing approval."
)

VISUAL_QA_MARKER = "Visual QA: PASS - reference-checked handmade sketchnote"


def visual_approval_marker(post: dict) -> str:
    return (
        "Visual approval: Ahmed explicitly approved this exact paired visual in the current Telegram conversation on "
        f"2026-08-17 (Telegram message {post['visual_message_id']}). {VISUAL_QA_MARKER}. "
        f"Verified SHA-256: {post['visual_sha256']}. This approval does not approve scheduling or publishing; "
        "Status must remain Draft until those action gates are explicitly approved."
    )


def approved_image_intent(post: dict) -> str:
    return (
        "Approved paired visual. "
        f"Final local asset: `{post['visual_asset']}`\n"
        f"{VISUAL_QA_MARKER}\n"
        f"Visual approval: APPROVED by Ahmed on 2026-08-17 via Telegram message {post['visual_message_id']}.\n"
        "Publishing boundary: visual approval only; scheduling and publishing are not approved."
    )


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


def query_date(target_date: str) -> list[dict]:
    body = {
        "filter": {"property": "Planned Date", "date": {"equals": target_date}},
        "page_size": 20,
    }
    return notion_request("POST", f"databases/{content_db_id()}/query", body).get("results", [])


def query_title(title: str) -> list[dict]:
    body = {
        "filter": {"property": "Title", "title": {"equals": title}},
        "page_size": 20,
    }
    return notion_request("POST", f"databases/{content_db_id()}/query", body).get("results", [])


def validate(post: dict) -> list[str]:
    errors = []
    if "—" in post["draft"] or "--" in post["draft"]:
        errors.append("contains_em_dash")
    if not post["draft"].rstrip().splitlines()[-1].startswith("#"):
        errors.append("hashtags_not_last")
    if "?" not in post["draft"]:
        errors.append("missing_question")
    if not 120 <= len(post["draft"].split()) <= 250:
        errors.append(f"word_count:{len(post['draft'].split())}")
    return errors


def create_page(post: dict) -> dict:
    body = {
        "parent": {"database_id": content_db_id()},
        "properties": {
            "Title": {"title": rich_text(post["title"])},
            "Status": {"select": {"name": "Draft"}},
            "Planned Date": {"date": {"start": post["date"]}},
            "Day": {"select": {"name": post["day"]}},
            "Owner": {"select": {"name": "CMO"}},
            "Funnel Role": {"select": {"name": post["funnel_role"]}},
            "Topic": {"select": {"name": post["topic"]}},
            "Hook": {"rich_text": rich_text(post["draft"].splitlines()[0])},
            "Draft": {"rich_text": rich_text(post["draft"])},
            "Image Intent": {"rich_text": rich_text(post["image_intent"])},
            "Retry Count": {"number": 0},
        },
        "children": [
            paragraph("Series: Experience-backed authority series"),
            paragraph(f"Evidence: {post['evidence']}"),
            paragraph(f"Funnel role: {post['funnel_role']}"),
            paragraph("Publishing boundary: Draft only. Exact caption and visual state require Ahmed approval before scheduling or publishing."),
            paragraph("Performance review: compare after 72 hours with the 16 August benchmark and rolling 28-day median."),
        ],
    }
    return notion_request("POST", "pages", body)


def record_caption_approval(page_id: str, post: dict, existing_body: str) -> str:
    marker = exact_caption_approval_marker(post)
    if marker in existing_body:
        return "caption_approval_already_recorded"
    notion_request(
        "PATCH",
        f"blocks/{page_id}/children",
        {"children": [paragraph(marker)]},
    )
    verified_body = extract_page_body(page_id)["text"]
    if marker not in verified_body:
        raise RuntimeError(f"Caption approval marker was not persisted for {page_id}")
    return "caption_approval_recorded"


def sync_revision(page_id: str, post: dict, existing_body: str) -> str:
    notion_request(
        "PATCH",
        f"pages/{page_id}",
        {
            "properties": {
                "Hook": {"rich_text": rich_text(post["draft"].splitlines()[0])},
                "Draft": {"rich_text": rich_text(post["draft"])},
                "Image Intent": {"rich_text": rich_text(post["image_intent"])},
            }
        },
    )
    if post["date"] == "2026-09-02" and CAPTION_REVISION_MARKER not in existing_body:
        notion_request(
            "PATCH",
            f"blocks/{page_id}/children",
            {"children": [paragraph(CAPTION_REVISION_MARKER)]},
        )
    return "revision_synced"


def record_visual_approval(page_id: str, post: dict, existing_body: str) -> str:
    asset = Path(post["visual_asset"])
    if not asset.is_file():
        raise RuntimeError(f"Visual asset is missing: {asset}")
    actual_sha256 = hashlib.sha256(asset.read_bytes()).hexdigest()
    if actual_sha256 != post["visual_sha256"]:
        raise RuntimeError(
            f"Visual hash mismatch for {post['title']}: expected {post['visual_sha256']}, got {actual_sha256}"
        )

    marker = visual_approval_marker(post)
    notion_request(
        "PATCH",
        f"pages/{page_id}",
        {"properties": {"Image Intent": {"rich_text": rich_text(approved_image_intent(post))}}},
    )
    if marker not in existing_body:
        notion_request(
            "PATCH",
            f"blocks/{page_id}/children",
            {"children": [paragraph(marker)]},
        )

    refreshed = query_title(post["title"])
    refreshed_exact = [
        row for row in refreshed if date_value(row.get("properties", {})) == post["date"]
    ]
    if len(refreshed_exact) != 1:
        raise RuntimeError(f"Visual approval row could not be uniquely verified for {post['title']}")
    props = refreshed_exact[0].get("properties", {})
    body = extract_page_body(page_id)["text"]
    if select_value(props, "Status") != "Draft":
        raise RuntimeError(f"Visual approval changed Draft status for {post['title']}")
    if rich_text_value(props, "Image Intent") != approved_image_intent(post):
        raise RuntimeError(f"Approved Image Intent was not persisted for {post['title']}")
    if marker not in body:
        raise RuntimeError(f"Visual approval marker was not persisted for {post['title']}")
    return "visual_approval_recorded" if marker not in existing_body else "visual_approval_already_recorded"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Create missing draft-only rows")
    parser.add_argument(
        "--record-caption-approval",
        action="store_true",
        help="Record exact-caption approval while deliberately keeping the row Draft",
    )
    parser.add_argument(
        "--caption-date",
        choices=[post["date"] for post in POSTS],
        help="Limit exact-caption approval recording to one post date",
    )
    parser.add_argument(
        "--sync-revisions",
        action="store_true",
        help="Synchronize explicitly requested Draft caption revisions without changing publish status",
    )
    parser.add_argument(
        "--record-visual-approval",
        action="store_true",
        help="Record approval for the exact paired visuals while deliberately keeping both rows Draft",
    )
    args = parser.parse_args()

    results = []
    failed = False
    for post in POSTS:
        errors = validate(post)
        date_rows = query_date(post["date"])
        title_rows = query_title(post["title"])
        exact = [
            row
            for row in title_rows
            if date_value(row.get("properties", {})) == post["date"]
        ]

        if errors:
            results.append({"date": post["date"], "title": post["title"], "action": "invalid", "errors": errors})
            failed = True
            continue
        if len(exact) == 1:
            props = exact[0].get("properties", {})
            body = extract_page_body(exact[0].get("id", ""))["text"]
            if args.sync_revisions and post["date"] == "2026-09-02":
                action = sync_revision(exact[0].get("id", ""), post, body)
                refreshed = query_title(post["title"])
                refreshed_exact = [
                    row
                    for row in refreshed
                    if date_value(row.get("properties", {})) == post["date"]
                ]
                if len(refreshed_exact) != 1:
                    raise RuntimeError(f"Revised row could not be uniquely verified for {post['title']}")
                props = refreshed_exact[0].get("properties", {})
                body = extract_page_body(refreshed_exact[0].get("id", ""))["text"]
                if select_value(props, "Status") != "Draft":
                    raise RuntimeError(f"Revision changed Draft status for {post['title']}")
            approved_visual = visual_approval_marker(post) in body
            expected_image_intent = approved_image_intent(post) if approved_visual else post["image_intent"]
            checks = {
                "status_draft": select_value(props, "Status") == "Draft",
                "owner_cmo": select_value(props, "Owner") == "CMO",
                "day_exact": select_value(props, "Day") == post["day"],
                "funnel_role_exact": select_value(props, "Funnel Role") == post["funnel_role"],
                "topic_exact": select_value(props, "Topic") == post["topic"],
                "hook_exact": rich_text_value(props, "Hook") == post["draft"].splitlines()[0],
                "draft_exact": rich_text_value(props, "Draft") == post["draft"],
                "image_intent_exact": rich_text_value(props, "Image Intent") == expected_image_intent,
                "retry_count_zero": number_value(props, "Retry Count") == 0,
                "body_has_evidence": post["evidence"] in body,
                "body_has_publish_boundary": "Draft only. Exact caption and visual state require Ahmed approval" in body,
            }
            if not all(checks.values()):
                results.append(
                    {
                        "date": post["date"],
                        "title": post["title"],
                        "action": "existing_mismatch_refused",
                        "checks": checks,
                        "page_id": exact[0].get("id", ""),
                        "url": exact[0].get("url", ""),
                    }
                )
                failed = True
                continue
            action = action if args.sync_revisions and post["date"] == "2026-09-02" else "existing_verified"
            if args.record_caption_approval and (
                args.caption_date is None or args.caption_date == post["date"]
            ):
                action = record_caption_approval(exact[0].get("id", ""), post, body)
                refreshed = query_title(post["title"])
                refreshed_exact = [
                    row
                    for row in refreshed
                    if date_value(row.get("properties", {})) == post["date"]
                ]
                if len(refreshed_exact) != 1 or select_value(
                    refreshed_exact[0].get("properties", {}), "Status"
                ) != "Draft":
                    raise RuntimeError(f"Approval recording changed or lost Draft status for {post['title']}")
            if args.record_visual_approval:
                action = record_visual_approval(exact[0].get("id", ""), post, body)
            results.append(
                {
                    "date": post["date"],
                    "title": post["title"],
                    "action": action,
                    "checks": checks,
                    "status_remains_draft": True,
                    "page_id": exact[0].get("id", ""),
                    "url": exact[0].get("url", ""),
                }
            )
            continue
        if date_rows or title_rows:
            results.append(
                {
                    "date": post["date"],
                    "title": post["title"],
                    "action": "collision_refused",
                    "date_row_titles": [title_text(row.get("properties", {})) for row in date_rows],
                    "title_row_dates": [date_value(row.get("properties", {})) for row in title_rows],
                }
            )
            failed = True
            continue
        if not args.apply:
            results.append({"date": post["date"], "title": post["title"], "action": "would_create_draft"})
            continue

        created = create_page(post)
        results.append(
            {
                "date": post["date"],
                "title": post["title"],
                "action": "created_draft",
                "page_id": created.get("id", ""),
                "url": created.get("url", ""),
            }
        )

    print(json.dumps({"ok": not failed, "apply": args.apply, "results": results}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
