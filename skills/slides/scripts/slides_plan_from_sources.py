#!/usr/bin/env python3
"""Build planning artifacts from a Slides Lane v2 intake package.

Copyright (c) OpenAI. All rights reserved.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from slides_ingest_lib import ensure_task_dirs, load_registry, task_abs

MAX_PREVIEW_CHARS = 1400
SECTION_PATTERNS: list[tuple[str, str]] = [
    ("risks", r"^(risks?|key risks?|main risks?)$"),
    ("next_steps", r"^(next steps?|next actions?|action items?)$"),
    ("recommendations", r"^(recommendations?|recommended actions?)$"),
    ("timeline", r"^(timeline|roadmap|milestones?)$"),
    ("ownership", r"^(owner|owners|ownership|roles?)$"),
    ("metrics", r"^(metrics?|kpis?|measure(s)? of success)$"),
    ("summary", r"^(summary|conclusion|close)$"),
    ("problem", r"^(problem|challenge|issues?)$"),
    ("opportunity", r"^(opportunity|opportunities|benefits?)$"),
]
SECTION_PRIORITY = {
    "problem": 1,
    "opportunity": 2,
    "risks": 3,
    "recommendations": 4,
    "timeline": 5,
    "ownership": 6,
    "metrics": 7,
    "next_steps": 8,
    "summary": 9,
}
CRITICAL_SECTION_KINDS = {"problem", "opportunity", "risks", "recommendations", "timeline", "next_steps"}
PATTERN_DENSITY_TARGET = {
    "cover": "2/10",
    "section-divider": "2/10",
    "agenda": "4/10",
    "thesis-summary": "3/10",
    "metric": "3/10",
    "comparison": "4/10",
    "process-timeline": "4/10",
    "2-column-explainer": "5/10",
    "closing": "3/10",
}
STARTER_LAYOUT_BY_PATTERN = {
    "cover": "cover-hero",
    "section-divider": "section-divider-signal",
    "agenda": "agenda-list",
    "thesis-summary": "thesis-hero-left",
    "metric": "metric-kpi-hero",
    "comparison": "comparison-weighted-split",
    "process-timeline": "timeline-spine",
    "2-column-explainer": "explainer-split-panel",
    "closing": "closing-takeaway",
}
SECTION_PATTERN_HINTS = {
    "problem": "thesis-summary",
    "opportunity": "thesis-summary",
    "recommendations": "thesis-summary",
    "summary": "thesis-summary",
    "metrics": "metric",
    "timeline": "process-timeline",
    "next_steps": "process-timeline",
    "ownership": "process-timeline",
    "risks": "comparison",
}


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def preview_text(text: str, limit: int = MAX_PREVIEW_CHARS) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def infer_deck_length(entries: list[dict[str, Any]]) -> int:
    strong = 0
    total_words = 0
    section_count = 0
    for entry in entries:
        quality = entry.get("extractionQuality")
        status = entry.get("extractionStatus")
        if status == "completed" and quality in {"full", "basic"}:
            strong += 1
        total_words += entry.get("wordCount", 0)
        section_count += len(entry.get("sections", []))

    if section_count >= 5 and total_words < 1500:
        return 7
    if strong <= 1 and total_words < 500:
        return 5
    if strong <= 3 and total_words < 1800:
        return 7
    if total_words < 4000:
        return 9
    return 12


def semantic_section_score(section: dict[str, Any]) -> int:
    kind = section.get("kind", "content")
    items = section.get("items") or []
    item_score = min(len(items), 4)
    priority_score = 20 - SECTION_PRIORITY.get(kind, 99)
    critical_bonus = 8 if kind in CRITICAL_SECTION_KINDS else 0
    return priority_score + critical_bonus + item_score


def infer_audience(entries: list[dict[str, Any]]) -> str:
    joined = "\n".join(entry.get("preview", "") for entry in entries).lower()
    if any(token in joined for token in ["board", "executive", "strategy", "ceo", "vp", "director"]):
        return "executive / leadership"
    if any(token in joined for token in ["customer", "market", "product", "launch", "brand"]):
        return "external stakeholders / clients"
    if any(token in joined for token in ["training", "guide", "how to", "tutorial"]):
        return "internal team / learners"
    return "mixed business audience"


def infer_tone(entries: list[dict[str, Any]]) -> str:
    joined = "\n".join(entry.get("preview", "") for entry in entries).lower()
    if any(token in joined for token in ["urgent", "risk", "issue", "problem", "decline"]):
        return "direct, decision-oriented"
    if any(token in joined for token in ["vision", "future", "opportunity", "growth", "transformation"]):
        return "strategic, forward-looking"
    if any(token in joined for token in ["guide", "steps", "process", "instruction"]):
        return "clear, instructional"
    return "professional, concise"


def infer_objective(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "Present the available source material clearly and convert it into a usable deck."
    top = max(entries, key=lambda entry: entry.get("wordCount", 0))
    kind = top.get("sourceKind", "source")
    if kind == "presentation":
        return "Reframe the source presentation into a clearer, more intentional deck."
    if kind == "pdf":
        return "Turn the imported document into a concise presentation with clear structure."
    if kind == "url":
        return "Translate the referenced web material into a presentation-ready narrative."
    return "Convert the imported materials into a presentation-ready story with stronger hierarchy."


def summarize_entry_contribution(entry: dict[str, Any]) -> str:
    kind = entry.get("sourceKind", "source")
    sections = entry.get("sections", [])
    if sections:
        top = sections[0]
        heading = top.get("title") or top.get("kind") or "section"
        first_item = (top.get("items") or [""])[0].strip()
        summary = f"{heading}: {first_item}" if first_item else heading
        if len(summary) > 120:
            summary = summary[:117].rstrip() + "..."
        return summary
    preview = entry.get("preview", "")
    if not preview:
        return f"{kind} reference"
    first_line = preview.splitlines()[0].strip()
    if len(first_line) > 120:
        first_line = first_line[:117].rstrip() + "..."
    return first_line or f"{kind} reference"


def recommend_layout_direction(slide_type: str, index: int, total: int) -> str:
    if slide_type == "cover":
        return "starter layout: cover, hero title with one dominant focal element"
    if slide_type == "toc":
        return "starter layout: agenda, clean agenda grid or numbered list"
    if slide_type == "section-divider":
        return "starter layout: section divider, strong divider with oversized type"
    if slide_type == "summary":
        return "starter layout: closing, decisive close with key takeaway and next step"
    variants = [
        "starter layout: thesis-summary, editorial left-right composition",
        "starter layout: 2-column-explainer, asymmetric text plus evidence block",
        "starter layout: metric, single-message hero with supporting proof",
        "starter layout: comparison, structured two-column analysis",
        "starter layout: thesis-summary, modular evidence cards with one dominant callout",
    ]
    return variants[(index - 1) % len(variants)]


def estimate_message_complexity(text: str) -> str:
    words = count_words(text)
    if words <= 10:
        return "low"
    if words <= 22:
        return "medium"
    return "high"


def infer_source_visual_bias(entry: dict[str, Any]) -> str:
    kind = (entry.get("sourceKind") or "").lower()
    if kind in {"image", "presentation"}:
        return "visual"
    if kind in {"data"}:
        return "data"
    if kind in {"pdf", "url", "markdown", "text"}:
        return "text"
    return "mixed"


def infer_pattern_from_message_shape(
    *,
    key_message: str,
    section_item_count: int,
    source_bias: str,
    source_count: int,
) -> str:
    complexity = estimate_message_complexity(key_message)
    if source_bias == "data":
        return "metric"
    if source_bias == "visual" and source_count == 1 and complexity != "high":
        return "2-column-explainer"
    if section_item_count >= 4:
        return "2-column-explainer"
    if complexity == "low":
        return "thesis-summary"
    if complexity == "high":
        return "2-column-explainer"
    return "thesis-summary"


def infer_editorial_pattern(
    slide_type: str,
    *,
    section_kind: str | None = None,
    section_item_count: int = 0,
    source_count: int = 1,
    key_message: str = "",
    source_bias: str = "mixed",
) -> str:
    if slide_type == "cover":
        return "cover"
    if slide_type == "toc":
        return "agenda"
    if slide_type == "section-divider":
        return "section-divider"
    if slide_type == "summary":
        return "closing"
    if section_kind in SECTION_PATTERN_HINTS:
        hinted = SECTION_PATTERN_HINTS[section_kind]
        if section_kind == "risks" and section_item_count <= 1:
            return "thesis-summary"
        return hinted
    if source_count >= 3 and source_bias != "data":
        return "2-column-explainer"
    return infer_pattern_from_message_shape(
        key_message=key_message,
        section_item_count=section_item_count,
        source_bias=source_bias,
        source_count=source_count,
    )


def infer_starter_layout(pattern: str) -> str:
    return STARTER_LAYOUT_BY_PATTERN.get(pattern, "editorial-flex")


def infer_focal_element(pattern: str, working_title: str, key_message: str) -> str:
    if pattern in {"cover", "section-divider"}:
        return working_title
    if pattern == "agenda":
        return "Narrative path"
    if pattern == "closing":
        return "Final takeaway and next move"
    return key_message or working_title


def infer_visual_risk_notes(
    *,
    pattern: str,
    confidence: str,
    key_message: str,
    source_count: int,
    section_item_count: int,
) -> list[str]:
    notes: list[str] = []
    if confidence == "low":
        notes.append("Low-confidence source extraction, verify claims against originals before final design.")
    if len(key_message) > 110:
        notes.append("Dominant message is long, tighten copy so the slide can sustain a stronger focal hierarchy.")
    if source_count > 1 and pattern not in {"agenda", "closing"}:
        notes.append("Multiple source inputs may dilute the focal story, keep the slide anchored on one dominant message.")
    if section_item_count >= 5 and pattern in {"comparison", "process-timeline", "thesis-summary", "2-column-explainer"}:
        notes.append("Section density is high, consider splitting content if the layout starts to feel crowded.")
    if pattern == "agenda" and section_item_count >= 6:
        notes.append("Agenda may scan slowly if too many sections are shown at equal weight.")
    return notes


def build_editorial_fields(
    *,
    slide_type: str,
    working_title: str,
    key_message: str,
    confidence: str,
    source_ids: list[str],
    section_kind: str | None = None,
    section_item_count: int = 0,
    source_bias: str = "mixed",
    context_source_count: int | None = None,
) -> dict[str, Any]:
    effective_source_count = context_source_count or len(source_ids)
    pattern = infer_editorial_pattern(
        slide_type,
        section_kind=section_kind,
        section_item_count=section_item_count,
        source_count=effective_source_count,
        key_message=key_message,
        source_bias=source_bias,
    )
    dominant_message = key_message.strip() or working_title
    if len(dominant_message) > 140:
        dominant_message = dominant_message[:137].rstrip() + "..."
    return {
        "pattern": pattern,
        "starterLayout": infer_starter_layout(pattern),
        "focalElement": infer_focal_element(pattern, working_title, dominant_message),
        "dominantMessage": dominant_message,
        "densityTarget": PATTERN_DENSITY_TARGET.get(pattern, "4/10"),
        "visualRiskNotes": infer_visual_risk_notes(
            pattern=pattern,
            confidence=confidence,
            key_message=dominant_message,
            source_count=effective_source_count,
            section_item_count=section_item_count,
        ),
    }


def visuals_needed(entry: dict[str, Any], section_kind: str | None = None) -> list[str]:
    if section_kind == "risks":
        return ["risk matrix or priority callout"]
    if section_kind == "next_steps":
        return ["sequenced action list or roadmap strip"]
    if section_kind == "timeline":
        return ["timeline or milestone view"]
    if section_kind == "metrics":
        return ["simple editable chart or KPI block"]
    if section_kind == "ownership":
        return ["owner matrix or role mapping"]
    kind = entry.get("sourceKind")
    if kind == "image":
        return ["use imported image reference"]
    if kind == "data":
        return ["simple editable chart or table"]
    if kind == "pdf":
        return ["document-derived summary visual or diagram"]
    if kind == "url":
        return ["supporting screenshot or abstract visual"]
    return []


def build_pattern_content_fields(
    *,
    pattern: str,
    title: str,
    purpose: str,
    key_message: str,
    items: list[str],
    section_kind: str | None = None,
) -> dict[str, Any]:
    fields: dict[str, Any] = {}

    if pattern == "comparison":
        left = items[0] if len(items) >= 1 else "Current state"
        right = items[1] if len(items) >= 2 else key_message or "Recommended state"
        fields["comparisonLeftTitle"] = "Current / baseline"
        fields["comparisonRightTitle"] = "Recommended"
        fields["comparisonLeftBody"] = left
        fields["comparisonRightBody"] = right
    elif pattern == "process-timeline":
        phases = items[:4] if items else [title, key_message]
        if len(phases) < 4:
            defaults = ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
            for default in defaults:
                if len(phases) >= 4:
                    break
                phases.append(default)
        fields["timelinePhases"] = phases[:4]
        fields["timelineCurrentLabel"] = items[0] if items else key_message or "Current priority phase"
    elif pattern == "closing":
        fields["closingCta"] = purpose or "Next move"
        fields["closingSupport"] = key_message
    elif pattern == "agenda":
        fields["agendaItems"] = items[:5]

    return fields


def select_sections_for_budget(
    semantic_sections: list[dict[str, Any]], content_budget: int
) -> list[dict[str, Any]]:
    if content_budget <= 0:
        return []

    scored_sections = sorted(
        semantic_sections,
        key=lambda item: semantic_section_score(item["section"]),
        reverse=True,
    )

    selected: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, str]] = set()

    def maybe_add(item: dict[str, Any]) -> bool:
        if len(selected) >= content_budget:
            return False
        entry = item["entry"]
        section = item["section"]
        dedupe_key = (entry["id"], section.get("kind", "content"), section.get("title", ""))
        if dedupe_key in seen_keys:
            return False
        selected.append(item)
        seen_keys.add(dedupe_key)
        return True

    must_cover_kinds = ["problem", "recommendations", "timeline", "metrics", "risks", "next_steps"]
    for kind in must_cover_kinds:
        if len(selected) >= content_budget:
            break
        if any(item["section"].get("kind") == kind for item in selected):
            continue
        for item in scored_sections:
            if item["section"].get("kind") == kind and maybe_add(item):
                break

    critical_candidates = [
        item for item in scored_sections if item["section"].get("kind") in CRITICAL_SECTION_KINDS
    ]
    for item in critical_candidates:
        if len(selected) >= content_budget:
            break
        maybe_add(item)

    for item in scored_sections:
        if len(selected) >= content_budget:
            break
        maybe_add(item)

    return selected[:content_budget]


def build_slide_outline(entries: list[dict[str, Any]], target_slide_count: int) -> list[dict[str, Any]]:
    outline: list[dict[str, Any]] = []
    if not entries:
        return outline

    agenda_items: list[str] = []
    seen_agenda: set[str] = set()

    def push_agenda(label: str | None) -> None:
        if not label:
            return
        cleaned = label.strip()
        if not cleaned:
            return
        normalized = cleaned.lower()
        if normalized in seen_agenda:
            return
        seen_agenda.add(normalized)
        agenda_items.append(cleaned)

    def cover_score(entry: dict[str, Any]) -> tuple[int, int, int]:
        section_kinds = {section.get("kind") for section in entry.get("sections", [])}
        strategic_bonus = 1 if section_kinds & {"problem", "opportunity", "recommendations", "summary", "metrics"} else 0
        non_generic_title_bonus = 1 if entry.get("titleHint") and entry.get("titleHint") not in {"Web Source", "Reference image", "Source"} else 0
        return (
            strategic_bonus,
            non_generic_title_bonus,
            entry.get("wordCount", 0),
        )

    lead = max(entries, key=cover_score)
    cover_confidence = lead.get("confidence", "medium")
    outline.append(
        {
            "slideNumber": 1,
            "slideType": "cover",
            "workingTitle": lead.get("titleHint") or "Presentation Title",
            "purpose": "Set context and establish the core topic.",
            "keyMessage": summarize_entry_contribution(lead),
            "sourceIds": [lead["id"]],
            "layoutDirection": recommend_layout_direction("cover", 1, target_slide_count),
            "visualsNeeded": visuals_needed(lead),
            "confidence": cover_confidence,
            **build_editorial_fields(
                slide_type="cover",
                working_title=lead.get("titleHint") or "Presentation Title",
                key_message=summarize_entry_contribution(lead),
                confidence=cover_confidence,
                source_ids=[lead["id"]],
                source_bias=infer_source_visual_bias(lead),
            ),
        }
    )

    semantic_sections: list[dict[str, Any]] = []
    for entry in entries:
        for section in entry.get("sections", []):
            semantic_sections.append({"entry": entry, "section": section})
    semantic_sections.sort(key=lambda item: SECTION_PRIORITY.get(item["section"].get("kind", "summary"), 99))

    for item in semantic_sections:
        section = item["section"]
        kind = section.get("kind", "content")
        title = section.get("title") or kind.replace("_", " ").title()
        if kind != "content":
            push_agenda(title)

    if not agenda_items:
        for entry in entries[: min(4, len(entries))]:
            push_agenda(entry.get("titleHint") or entry.get("displayName") or entry["id"])

    if target_slide_count >= 5:
        agenda_sources = [entry["id"] for entry in entries[: min(4, len(entries))]]
        outline.append(
            {
                "slideNumber": 2,
                "slideType": "toc",
                "workingTitle": "Agenda",
                "purpose": "Set the narrative path and expectation for the deck.",
                "keyMessage": "Show the major sections before going deeper.",
                "sourceIds": agenda_sources,
                "agendaItems": agenda_items[:5],
                "layoutDirection": recommend_layout_direction("toc", 2, target_slide_count),
                "visualsNeeded": [],
                "confidence": "high",
                **build_pattern_content_fields(
                    pattern="agenda",
                    title="Agenda",
                    purpose="Set the narrative path and expectation for the deck.",
                    key_message="Show the major sections before going deeper.",
                    items=agenda_items[:5],
                ),
                **build_editorial_fields(
                    slide_type="toc",
                    working_title="Agenda",
                    key_message="Show the major sections before going deeper.",
                    confidence="high",
                    source_ids=agenda_sources,
                    section_item_count=len(agenda_items[:5]) if agenda_items else len(agenda_sources),
                    source_bias="mixed",
                ),
            }
        )

    content_budget = max(target_slide_count - len(outline) - 1, 0)
    selected_sections = select_sections_for_budget(semantic_sections, content_budget)

    slide_no = len(outline) + 1
    add_section_divider = (
        target_slide_count >= 8
        and len(selected_sections) >= 4
        and content_budget > len(selected_sections)
    )
    added_section_divider = False

    for item in selected_sections:
        if slide_no > target_slide_count - 1:
            break
        entry = item["entry"]
        section = item["section"]
        kind = section.get("kind", "content")
        raw_title = section.get("title") or entry.get("titleHint") or "Content"
        if raw_title in {"Overview", "Key Points", "Content"} and entry.get("titleHint"):
            title = entry.get("titleHint")
        else:
            title = raw_title
        items = section.get("items") or []
        key_message = items[0] if items else summarize_entry_contribution(entry)
        if len(key_message) > 140:
            key_message = key_message[:137].rstrip() + "..."

        if not added_section_divider and add_section_divider and kind in {"risks", "recommendations", "next_steps", "timeline"}:
            outline.append(
                {
                    "slideNumber": slide_no,
                    "slideType": "section-divider",
                    "workingTitle": title,
                    "purpose": "Create a clean transition into the next decision block.",
                    "keyMessage": summarize_entry_contribution(entry),
                    "sourceIds": [entry["id"]],
                    "layoutDirection": recommend_layout_direction("section-divider", slide_no, target_slide_count),
                    "visualsNeeded": [],
                    "confidence": entry.get("confidence", "medium"),
                    **build_editorial_fields(
                        slide_type="section-divider",
                        working_title=title,
                        key_message=summarize_entry_contribution(entry),
                        confidence=entry.get("confidence", "medium"),
                        source_ids=[entry["id"]],
                        section_kind=kind,
                        section_item_count=len(items),
                        source_bias=infer_source_visual_bias(entry),
                    ),
                }
            )
            slide_no += 1
            added_section_divider = True
            if slide_no > target_slide_count - 1:
                break

        purpose_map = {
            "problem": "Define the main challenge or constraint.",
            "opportunity": "Frame the upside or strategic opening.",
            "risks": "Make the main risks explicit and discuss their implications.",
            "recommendations": "Present the recommended path clearly and directly.",
            "timeline": "Show sequencing and major milestones.",
            "ownership": "Clarify ownership and accountability.",
            "metrics": "Define how success should be measured.",
            "next_steps": "State the immediate actions and who should move next.",
            "summary": "Condense the main conclusion from this source section.",
        }

        editorial_fields = build_editorial_fields(
            slide_type="content",
            working_title=title,
            key_message=key_message,
            confidence=entry.get("confidence", "medium"),
            source_ids=[entry["id"]],
            section_kind=kind,
            section_item_count=len(items),
            source_bias=infer_source_visual_bias(entry),
            context_source_count=len(entries) if kind == "content" else 1,
        )

        outline.append(
            {
                "slideNumber": slide_no,
                "slideType": "content",
                "workingTitle": title,
                "purpose": purpose_map.get(kind, "Present and interpret one core part of the source material."),
                "keyMessage": key_message,
                "sourceIds": [entry["id"]],
                "layoutDirection": recommend_layout_direction("content", slide_no, target_slide_count),
                "visualsNeeded": visuals_needed(entry, kind),
                "confidence": entry.get("confidence", "medium"),
                "sectionKind": kind,
                "sectionTitle": title,
                **build_pattern_content_fields(
                    pattern=editorial_fields["pattern"],
                    title=title,
                    purpose=purpose_map.get(kind, "Present and interpret one core part of the source material."),
                    key_message=key_message,
                    items=items,
                    section_kind=kind,
                ),
                **editorial_fields,
            }
        )
        slide_no += 1

    if slide_no <= target_slide_count - 1:
        for idx, entry in enumerate(entries, start=1):
            if slide_no > target_slide_count - 1:
                break
            outline.append(
                {
                    "slideNumber": slide_no,
                    "slideType": "content",
                    "workingTitle": entry.get("titleHint") or f"Source {idx}",
                    "purpose": "Present supporting evidence or additional context.",
                    "keyMessage": summarize_entry_contribution(entry),
                    "sourceIds": [entry["id"]],
                    "layoutDirection": recommend_layout_direction("content", slide_no, target_slide_count),
                    "visualsNeeded": visuals_needed(entry),
                    "confidence": entry.get("confidence", "medium"),
                    "sectionTitle": entry.get("titleHint") or f"Source {idx}",
                    **build_editorial_fields(
                        slide_type="content",
                        working_title=entry.get("titleHint") or f"Source {idx}",
                        key_message=summarize_entry_contribution(entry),
                        confidence=entry.get("confidence", "medium"),
                        source_ids=[entry["id"]],
                        source_bias=infer_source_visual_bias(entry),
                        context_source_count=len(entries),
                    ),
                }
            )
            slide_no += 1

    while slide_no < target_slide_count:
        source_ids = [entry["id"] for entry in entries[: min(2, len(entries))]]
        outline.append(
            {
                "slideNumber": slide_no,
                "slideType": "content",
                "workingTitle": f"Synthesis {slide_no - 1}",
                "purpose": "Synthesize and connect the imported materials.",
                "keyMessage": "Pull the main evidence into one clear takeaway.",
                "sourceIds": source_ids,
                "layoutDirection": recommend_layout_direction("content", slide_no, target_slide_count),
                "visualsNeeded": ["supporting comparison or callout"],
                "confidence": "medium",
                **build_editorial_fields(
                    slide_type="content",
                    working_title=f"Synthesis {slide_no - 1}",
                    key_message="Pull the main evidence into one clear takeaway.",
                    confidence="medium",
                    source_ids=source_ids,
                    source_bias="mixed",
                ),
            }
        )
        slide_no += 1

    closing_editorial_fields = build_editorial_fields(
        slide_type="summary",
        working_title="Summary and Next Step",
        key_message="Condense the deck into the final takeaway and next move.",
        confidence="medium",
        source_ids=[entry["id"] for entry in entries[: min(3, len(entries))]],
        source_bias="mixed",
    )
    outline.append(
        {
            "slideNumber": target_slide_count,
            "slideType": "summary",
            "workingTitle": "Summary and Next Step",
            "purpose": "Close the story and state the action or conclusion.",
            "keyMessage": "Condense the deck into the final takeaway and next move.",
            "sourceIds": [entry["id"] for entry in entries[: min(3, len(entries))]],
            "layoutDirection": recommend_layout_direction("summary", target_slide_count, target_slide_count),
            "visualsNeeded": ["closing callout or recommendation block"],
            "confidence": "medium",
            **build_pattern_content_fields(
                pattern=closing_editorial_fields["pattern"],
                title="Summary and Next Step",
                purpose="Close the story and state the action or conclusion.",
                key_message="Condense the deck into the final takeaway and next move.",
                items=[],
            ),
            **closing_editorial_fields,
        }
    )
    return outline


def make_title_hint(entry: dict[str, Any]) -> str:
    preview = entry.get("preview", "")
    for line in preview.splitlines():
        cleaned = line.strip("#-• ")
        if 4 <= len(cleaned) <= 80:
            return cleaned
    if entry.get("sourceKind") == "url":
        return "Web Source"
    return Path(entry.get("displayName") or entry["id"]).stem.replace("_", " ").replace("-", " ").title()


def assess_confidence(entry: dict[str, Any]) -> str:
    if entry.get("extractionStatus") != "completed":
        return "low"
    quality = entry.get("extractionQuality")
    words = entry.get("wordCount", 0)
    sections = entry.get("sections", [])
    semantic_sections = [section for section in sections if section.get("kind") != "content"]
    if quality == "full" and (words >= 120 or len(semantic_sections) >= 3):
        return "high"
    if quality in {"full", "basic"} and (words >= 40 or len(sections) >= 2):
        return "medium"
    return "low"


def load_entry_text(task_dir: Path, entry: dict[str, Any]) -> str:
    normalized_path = entry.get("normalizedPath")
    if not normalized_path:
        return ""
    path = task_abs(normalized_path, task_dir)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def classify_section(title: str) -> str:
    normalized = re.sub(r"[^a-z0-9 ]+", "", title.strip().lower())
    for kind, pattern in SECTION_PATTERNS:
        if re.match(pattern, normalized):
            return kind
    return "content"


def extract_sections(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading_match:
            title = heading_match.group(2).strip()
            current = {"title": title, "kind": classify_section(title), "items": []}
            sections.append(current)
            continue

        bullet_match = re.match(r"^[-*•]\s+(.*)$", line)
        if bullet_match:
            if current is None:
                current = {"title": "Key Points", "kind": "content", "items": []}
                sections.append(current)
            current["items"].append(bullet_match.group(1).strip())
            continue

        if current is None:
            current = {"title": "Overview", "kind": "content", "items": []}
            sections.append(current)
        current["items"].append(line)

    cleaned_sections = []
    for section in sections:
        items = [item for item in section.get("items", []) if item]
        if not items:
            continue
        cleaned_sections.append({
            "title": section.get("title", "Content"),
            "kind": section.get("kind", "content"),
            "items": items,
        })
    return cleaned_sections


def enrich_entries(task_dir: Path, registry: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for raw in registry.get("entries", []):
        entry = dict(raw)
        text = load_entry_text(task_dir, entry)
        entry["normalizedText"] = text
        entry["preview"] = preview_text(text)
        entry["wordCount"] = count_words(text)
        entry["sections"] = extract_sections(text)
        entry["titleHint"] = make_title_hint(entry)
        entry["confidence"] = assess_confidence(entry)
        entries.append(entry)
    return entries


def infer_starter_pack(entries: list[dict[str, Any]], target_slide_count: int, outline: list[dict[str, Any]]) -> str:
    joined = "\n".join(entry.get("preview", "") for entry in entries).lower()
    audience = infer_audience(entries).lower()
    patterns = [slide.get("pattern") for slide in outline]
    section_kinds = {section.get("kind") for entry in entries for section in entry.get("sections", [])}
    source_kinds = {str(entry.get("sourceKind") or "").lower() for entry in entries}

    if any(token in joined for token in ["board", "investment", "investor", "funding", "breakeven", "ebitda", "the ask", "legal entity", "appoint gm", "seed investment"]):
        return "board-proposal"
    if any(token in joined for token in ["weekly", "status review", "operating review", "weekly review"]):
        return "weekly-operating-review"
    if source_kinds == {"data"} or (patterns.count("metric") >= 1 and section_kinds <= {"metrics", "content"}):
        return "kpi-story"
    if section_kinds & {"timeline", "next_steps", "ownership"}:
        return "transformation-roadmap"
    if "executive" in audience or target_slide_count <= 8:
        return "executive-summary"
    return "executive-summary"



def build_deck_spec(entries: list[dict[str, Any]], target_slide_count: int, outline: list[dict[str, Any]]) -> dict[str, Any]:
    objective = infer_objective(entries)
    audience = infer_audience(entries)
    tone = infer_tone(entries)
    strongest = sorted(entries, key=lambda entry: entry.get("wordCount", 0), reverse=True)[:3]
    gaps = [entry for entry in entries if entry.get("confidence") == "low"]
    confidence_rank = {"low": 0, "medium": 1, "high": 2}
    overall_confidence = "medium"
    if entries:
        min_confidence = min((entry.get("confidence", "medium") for entry in entries), key=lambda value: confidence_rank.get(value, 1))
        if all(entry.get("confidence") == "high" for entry in entries):
            overall_confidence = "high"
        elif min_confidence == "low":
            overall_confidence = "low"
    unresolved = [
        f"{entry['id']} needs review, confidence is low ({entry.get('extractionQuality')}, {entry.get('wordCount', 0)} words)."
        for entry in gaps
    ]
    if not unresolved:
        unresolved = ["No major planning gaps detected from the current intake package."]

    image_policy = "optional-supporting-visuals"
    if any((entry.get("sourceKind") or "").lower() == "image" for entry in entries):
        image_policy = "source-image-supported"
    elif any(slide.get("pattern") in {"metric", "comparison", "process-timeline"} for slide in outline):
        image_policy = "optional-abstract-supporting-visuals"

    starter_pack = infer_starter_pack(entries, target_slide_count, outline)
    starter_narrative_map = {
        "executive-summary": "Move from problem to recommendation with one dominant argument per slide.",
        "weekly-operating-review": "Scan status fast, isolate the blocker, and finish with actions.",
        "kpi-story": "Lead with KPI movement, then explain cause and management action.",
        "transformation-roadmap": "Show sequence, ownership, and the next committed move clearly.",
        "board-proposal": "Build the case, prove the economics, then land the ask cleanly.",
    }

    return {
        "objective": objective,
        "audience": audience,
        "tone": tone,
        "targetSlideCount": target_slide_count,
        "aspectRatio": "16:9",
        "styleMode": "editorial-default",
        "brandMode": "unbranded",
        "starterPack": starter_pack,
        "starterNarrative": starter_narrative_map.get(starter_pack, starter_narrative_map["executive-summary"]),
        "imagePolicy": image_policy,
        "editableOutputRequired": True,
        "polishLevel": "working-draft",
        "confidence": overall_confidence,
        "strongestSources": [entry["id"] for entry in strongest],
        "unresolvedAssumptions": unresolved,
    }



def build_deck_brief(entries: list[dict[str, Any]], target_slide_count: int, deck_spec: dict[str, Any]) -> str:
    objective = deck_spec["objective"]
    audience = deck_spec["audience"]
    tone = deck_spec["tone"]
    section_kinds = []
    for entry in entries:
        for section in entry.get("sections", []):
            kind = section.get("kind")
            if kind and kind != "content" and kind not in section_kinds:
                section_kinds.append(kind)
    arc_parts = ["Cover", "Context"]
    arc_parts.extend(kind.replace("_", " ").title() for kind in section_kinds[:4])
    arc_parts.append("Close")
    arc = " -> ".join(arc_parts)
    strongest = sorted(entries, key=lambda entry: entry.get("wordCount", 0), reverse=True)[:3]
    gaps = [entry for entry in entries if entry.get("confidence") == "low"]

    lines = [
        "# Deck Brief",
        "",
        f"- Objective: {objective}",
        f"- Audience: {audience}",
        f"- Tone: {tone}",
        f"- Recommended deck length: {target_slide_count} slides",
        f"- Narrative arc: {arc}",
        "",
        "## Deck spec",
        "",
        f"- Aspect ratio: {deck_spec.get('aspectRatio', '16:9')}",
        f"- Style mode: {deck_spec.get('styleMode', 'editorial-default')}",
        f"- Brand mode: {deck_spec.get('brandMode', 'unbranded')}",
        f"- Starter pack: {deck_spec.get('starterPack', 'executive-summary')}",
        f"- Image policy: {deck_spec.get('imagePolicy', 'optional-supporting-visuals')}",
        f"- Editable output required: {str(deck_spec.get('editableOutputRequired', True)).lower()}",
        f"- Polish level: {deck_spec.get('polishLevel', 'working-draft')}",
        f"- Overall confidence: {deck_spec.get('confidence', 'medium')}",
        "",
        "## Strongest source materials",
        "",
    ]
    if strongest:
        for entry in strongest:
            lines.append(f"- {entry['id']} - {entry.get('displayName')}: {summarize_entry_contribution(entry)}")
    else:
        lines.append("- No strong sources detected yet")

    lines.extend(["", "## Gaps / unresolved assumptions", ""])
    if gaps:
        for entry in gaps:
            lines.append(
                f"- {entry['id']} needs review, confidence is low ({entry.get('extractionQuality')}, {entry.get('wordCount', 0)} words)."
            )
    else:
        lines.append("- No major planning gaps detected from the current intake package.")

    lines.append("")
    return "\n".join(lines)


def build_content_map(entries: list[dict[str, Any]], outline: list[dict[str, Any]]) -> str:
    slide_lookup: dict[str, list[int]] = {}
    section_slide_lookup: dict[tuple[str, str, str], list[int]] = {}
    for slide in outline:
        for source_id in slide.get("sourceIds", []):
            slide_lookup.setdefault(source_id, []).append(slide["slideNumber"])
            section_key = (
                source_id,
                slide.get("sectionKind", "content"),
                slide.get("sectionTitle", slide.get("workingTitle", "")),
            )
            section_slide_lookup.setdefault(section_key, []).append(slide["slideNumber"])

    lines = ["# Content Map", ""]
    for entry in entries:
        slides = slide_lookup.get(entry["id"], [])
        strength = "strong" if entry.get("confidence") == "high" else "partial" if entry.get("confidence") == "medium" else "weak"
        lines.extend(
            [
                f"## {entry['id']} - {entry.get('displayName')}",
                f"- Contribution: {summarize_entry_contribution(entry)}",
                f"- Source strength: {strength}",
                f"- Suggested slides: {', '.join(map(str, slides)) if slides else 'not yet mapped'}",
                f"- Notes: {entry.get('preview') or 'No extracted preview available.'}",
                f"- Sections: {', '.join(section.get('kind', 'content') for section in entry.get('sections', [])) or 'none detected'}",
                "",
            ]
        )
        if entry.get("sections"):
            lines.append("### Section mapping")
            lines.append("")
            for section in entry.get("sections", []):
                section_key = (
                    entry["id"],
                    section.get("kind", "content"),
                    section.get("title", "Content"),
                )
                mapped = section_slide_lookup.get(section_key, [])
                first_item = (section.get("items") or [""])[0].strip()
                lines.append(
                    f"- {section.get('title', 'Content')} [{section.get('kind', 'content')}] -> "
                    f"slides {', '.join(map(str, mapped)) if mapped else 'not directly mapped'}"
                )
                if first_item:
                    lines.append(f"  - Lead point: {first_item}")
            lines.append("")
    return "\n".join(lines)


def write_outputs(task_dir: Path, deck_brief: str, outline: list[dict[str, Any]], content_map: str, deck_spec: dict[str, Any]) -> None:
    planning_dir = task_dir / "planning"
    planning_dir.mkdir(parents=True, exist_ok=True)
    (planning_dir / "deck_brief.md").write_text(deck_brief.rstrip() + "\n", encoding="utf-8")
    (planning_dir / "slide_outline.json").write_text(json.dumps(outline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (planning_dir / "content_map.md").write_text(content_map.rstrip() + "\n", encoding="utf-8")
    (planning_dir / "deck_spec.json").write_text(json.dumps(deck_spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate planning artifacts from a Slides Lane v2 intake package.")
    parser.add_argument("task_dir", help="Task-local deck workspace directory.")
    parser.add_argument("--slide-count", type=int, default=None, help="Optional explicit target slide count.")
    args = parser.parse_args()

    task_dir = Path(args.task_dir).expanduser().resolve()
    ensure_task_dirs(task_dir)
    registry = load_registry(task_dir)
    entries = enrich_entries(task_dir, registry)
    target_slide_count = args.slide_count or infer_deck_length(entries)
    target_slide_count = max(3, target_slide_count)

    outline = build_slide_outline(entries, target_slide_count)
    deck_spec = build_deck_spec(entries, target_slide_count, outline)
    deck_brief = build_deck_brief(entries, target_slide_count, deck_spec)
    content_map = build_content_map(entries, outline)
    write_outputs(task_dir, deck_brief, outline, content_map, deck_spec)

    print(f"Generated planning artifacts for {len(entries)} source(s)")
    print(f"Deck brief: {task_dir / 'planning' / 'deck_brief.md'}")
    print(f"Slide outline: {task_dir / 'planning' / 'slide_outline.json'}")
    print(f"Content map: {task_dir / 'planning' / 'content_map.md'}")
    print(f"Deck spec: {task_dir / 'planning' / 'deck_spec.json'}")
    print(f"Target slide count: {target_slide_count}")


if __name__ == "__main__":
    main()
