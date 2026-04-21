#!/usr/bin/env python3
"""Initialize a task-local authoring workspace from Slides Lane v2 planning artifacts.

Copyright (c) OpenAI. All rights reserved.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from slides_ingest_lib import ensure_task_dirs, load_registry


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


def infer_starter_layout(slide: dict) -> str | None:
    return slide.get("starterLayout") or STARTER_LAYOUT_BY_PATTERN.get(slide.get("pattern"))


def build_authoring_manifest(task_dir: Path, deck_title: str, outline: list[dict], registry: dict, deck_spec: dict | None = None) -> dict:
    return {
        "version": 1,
        "taskDir": str(task_dir.resolve()),
        "deckTitle": deck_title,
        "slideCount": len(outline),
        "sourceCount": len(registry.get("entries", [])),
        "deckSpec": deck_spec or {},
        "workflowState": {
            "completed": ["intake", "planning", "authoring-init"],
            "current": "authoring",
            "next": "build",
        },
        "deliveryContract": {
            "required": [
                "exports/*.pptx",
                "authoring/deck.js",
                "authoring/authoring_manifest.json",
                "authoring/authoring_notes.md",
            ],
            "optional": [
                "rendered/*.png",
                "montage.png",
                "planning/deck_brief.md",
                "planning/content_map.md",
                "planning/deck_spec.json",
            ],
        },
        "artifacts": {
            "deckBrief": "planning/deck_brief.md",
            "slideOutline": "planning/slide_outline.json",
            "contentMap": "planning/content_map.md",
            "deckSpec": "planning/deck_spec.json",
            "sourceRegistry": "sources/sources.json",
            "authoringScript": "authoring/deck.js",
            "authoringNotes": "authoring/authoring_notes.md",
        },
        "slides": [
            {
                "slideNumber": slide.get("slideNumber"),
                "slideType": slide.get("slideType"),
                "pattern": slide.get("pattern"),
                "workingTitle": slide.get("workingTitle"),
                "purpose": slide.get("purpose"),
                "focalElement": slide.get("focalElement"),
                "dominantMessage": slide.get("dominantMessage"),
                "densityTarget": slide.get("densityTarget"),
                "starterLayout": infer_starter_layout(slide),
                "agendaItems": slide.get("agendaItems", []),
                "comparisonLeftTitle": slide.get("comparisonLeftTitle"),
                "comparisonRightTitle": slide.get("comparisonRightTitle"),
                "comparisonLeftBody": slide.get("comparisonLeftBody"),
                "comparisonRightBody": slide.get("comparisonRightBody"),
                "timelinePhases": slide.get("timelinePhases", []),
                "timelineCurrentLabel": slide.get("timelineCurrentLabel"),
                "closingCta": slide.get("closingCta"),
                "closingSupport": slide.get("closingSupport"),
                "visualRiskNotes": slide.get("visualRiskNotes", []),
                "sectionKind": slide.get("sectionKind"),
                "sourceIds": slide.get("sourceIds", []),
            }
            for slide in outline
        ],
    }


def build_authoring_notes(deck_title: str, outline: list[dict], deck_spec: dict | None = None) -> str:
    deck_spec = deck_spec or {}
    lines = [
        "# Authoring Notes",
        "",
        f"- Deck title: {deck_title}",
        f"- Planned slide count: {len(outline)}",
        "- Author in `authoring/deck.js` and keep output editable.",
        "- Use planning/deck_brief.md and planning/content_map.md as the narrative source of truth.",
        "- Run with: `NODE_PATH=/root/.openclaw/workspace/skills/slides/node_modules node authoring/deck.js`.",
        "- Keep final artifacts in `exports/` and rendered review assets in `rendered/`.",
        "- Start from the assigned pattern for each slide, do not redesign every slide from scratch.",
        "- Reuse composition families across the deck deliberately, but do not repeat the same layout back to back unless intentional.",
        "- Prefer upgrading a starter pattern over inventing a brand new structure under time pressure.",
        "",
        "## Deck spec",
        "",
        f"- Objective: {deck_spec.get('objective', 'not set')}",
        f"- Audience: {deck_spec.get('audience', 'not set')}",
        f"- Tone: {deck_spec.get('tone', 'not set')}",
        f"- Starter pack: {deck_spec.get('starterPack', 'not set')}",
        f"- Starter narrative: {deck_spec.get('starterNarrative', 'not set')}",
        f"- Style mode: {deck_spec.get('styleMode', 'editorial-default')}",
        f"- Image policy: {deck_spec.get('imagePolicy', 'optional-supporting-visuals')}",
        f"- Polish level: {deck_spec.get('polishLevel', 'working-draft')}",
        f"- Aspect ratio: {deck_spec.get('aspectRatio', '16:9')}",
        f"- Confidence: {deck_spec.get('confidence', 'medium')}",
        "",
        "## Starter pattern families",
        "",
        "- cover",
        "- agenda",
        "- section-divider",
        "- thesis-summary",
        "- metric",
        "- comparison",
        "- process-timeline",
        "- 2-column-explainer",
        "- closing",
        "",
        "## Planned slides",
        "",
    ]
    for slide in outline:
        lines.extend(
            [
                f"### Slide {slide.get('slideNumber')} - {slide.get('workingTitle')}",
                f"- Type: {slide.get('slideType')}",
                f"- Pattern: {slide.get('pattern') or 'not set'}",
                f"- Purpose: {slide.get('purpose')}",
                f"- Key message: {slide.get('keyMessage')}",
                f"- Dominant message: {slide.get('dominantMessage') or slide.get('keyMessage')}",
                f"- Focal element: {slide.get('focalElement') or 'not set'}",
                f"- Density target: {slide.get('densityTarget') or 'not set'}",
                f"- Starter layout: {infer_starter_layout(slide) or 'not set'}",
                f"- Visuals: {', '.join(slide.get('visualsNeeded', [])) or 'none specified'}",
                f"- Sources: {', '.join(slide.get('sourceIds', [])) or 'none'}",
                "",
            ]
        )
        agenda_items = slide.get("agendaItems") or []
        if agenda_items:
            lines.append(f"- Agenda items: {', '.join(agenda_items)}")
            lines.append("")
        risk_notes = slide.get("visualRiskNotes") or []
        if risk_notes:
            lines.append("- Visual risk notes:")
            for note in risk_notes:
                lines.append(f"  - {note}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_deck_stub(deck_title: str, outline: list[dict], deck_spec: dict | None = None) -> str:
    safe_title = json.dumps(deck_title)
    output_name = "-".join(part for part in deck_title.replace("_", " ").split() if part) or "slides-deck"
    output_name = "".join(ch for ch in output_name if ch.isalnum() or ch == "-").strip("-") or "slides-deck"
    slide_defs = json.dumps(outline, indent=2, ensure_ascii=False)
    deck_spec_json = json.dumps(deck_spec or {}, indent=2, ensure_ascii=False)
    return f'''// Slides Lane v2 authoring stub
// Default helper mode: safe
// Optional helpers for advanced text, code, or LaTeX workflows live under
// ./pptxgenjs_helpers/optional and may require extra packages.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const layoutHelpers = require("./pptxgenjs_helpers/safe");

const deckSpec = {deck_spec_json};
const STARTER_PACK = deckSpec.starterPack || "executive-summary";

const pptx = new pptxgen();
pptx.layout = deckSpec.aspectRatio === "4:3" ? "LAYOUT_STANDARD" : "LAYOUT_WIDE";
pptx.author = "OpenClaw";
pptx.company = "OpenClaw";
pptx.subject = {safe_title};
pptx.title = {safe_title};
pptx.lang = "en-US";
pptx.theme = {{
  headFontFace: "Aptos Display",
  bodyFontFace: "Aptos",
  lang: "en-US",
}};

const slidePlan = {slide_defs};
const outputFile = path.join(__dirname, "..", "exports", {json.dumps(output_name + '.pptx')});

const TOKENS = {{
  bgWarm: "F5F1EA",
  bgWhite: "FFFFFF",
  surface: "FCFAF7",
  surfaceAlt: "F3EEE8",
  textPrimary: "171411",
  textSecondary: "4B443D",
  textSoft: "7A6F66",
  rule: "D8CEC2",
  ruleStrong: "B9AB9B",
  accent: "C86432",
  accentSoft: "F3E1D8",
  darkPanel: "241F1A",
  darkPanelSoft: "3A322B",
  white: "FFFFFF",
  blue: "2E6FD0",
}};

const STARTER_PACK_HINTS = {{
  "executive-summary": {{
    eyebrow: "executive summary",
    narrative: "Move from problem to decision with minimal friction.",
    emphasis: "prioritize a decisive thesis, one metric, and one next move",
  }},
  "weekly-operating-review": {{
    eyebrow: "weekly operating review",
    narrative: "Scan status fast, isolate the blocker, end with action.",
    emphasis: "favor KPI movement, risk framing, and immediate actions",
  }},
  "kpi-story": {{
    eyebrow: "kpi story",
    narrative: "Lead with movement, then explain what changed and what to do.",
    emphasis: "make the number dominant, keep commentary subordinate",
  }},
  "transformation-roadmap": {{
    eyebrow: "transformation roadmap",
    narrative: "Show sequencing, ownership, and the next committed move.",
    emphasis: "favor timeline spine, recommendation clarity, and milestone discipline",
  }},
  "board-proposal": {{
    eyebrow: "board proposal",
    narrative: "Build the case, prove the economics, then land the ask cleanly.",
    emphasis: "use recommendation and ask slides with stronger formality",
  }},
}};

const ACTIVE_STARTER_PACK = STARTER_PACK_HINTS[STARTER_PACK] || STARTER_PACK_HINTS["executive-summary"];

function addPageBadge(slide, n) {{
  slide.addText(String(n), {{
    x: 12.5,
    y: 6.8,
    w: 0.5,
    h: 0.3,
    fontFace: "Aptos",
    fontSize: 10,
    bold: true,
    color: "666666",
    align: "center",
    margin: 0,
  }});
}}

function addEyebrow(slide, text, x, y, w) {{
  if (!text) return;
  slide.addText(text, {{
    x, y, w, h: 0.24,
    fontFace: "Aptos",
    fontSize: 9,
    bold: true,
    color: TOKENS.textSoft,
    charSpace: 1.2,
    margin: 0,
    breakLine: false,
  }});
}}

function addHairline(slide, x, y, w, color = TOKENS.rule) {{
  slide.addShape(pptx.ShapeType.line, {{
    x, y, w, h: 0,
    line: {{ color, pt: 1 }},
  }});
}}

function addChip(slide, text, x, y, w, opts = {{}}) {{
  const fill = opts.fill || TOKENS.accentSoft;
  const line = opts.line || TOKENS.accent;
  const color = opts.color || TOKENS.accent;
  slide.addShape(pptx.ShapeType.roundRect, {{
    x, y, w, h: 0.34,
    rectRadius: 0.08,
    line: {{ color: line, pt: 1 }},
    fill: {{ color: fill }},
  }});
  slide.addText(text, {{
    x: x + 0.08, y: y + 0.07, w: w - 0.16, h: 0.16,
    fontFace: "Aptos", fontSize: 9.5, bold: true,
    color, align: "center", margin: 0,
  }});
}}

function addVisualPlaceholder(slide, spec, opts = {{}}) {{
  const x = opts.x ?? 7.15;
  const y = opts.y ?? 1.45;
  const w = opts.w ?? 5.2;
  const h = opts.h ?? 3.6;
  const visuals = (spec.visualsNeeded || []).join(" • ");
  slide.addShape(pptx.ShapeType.roundRect, {{
    x, y, w, h,
    rectRadius: 0.08,
    line: {{ color: TOKENS.rule, pt: 1 }},
    fill: {{ color: opts.fill || TOKENS.surface }},
  }});
  slide.addText(spec.starterLayout || "starter-layout", {{
    x: x + 0.22,
    y: y + 0.2,
    w: w - 0.44,
    h: 0.18,
    fontFace: "Aptos",
    fontSize: 9,
    bold: true,
    color: TOKENS.textSoft,
    margin: 0,
    align: "left",
  }});
  slide.addText(visuals || "Visual treatment placeholder", {{
    x: x + 0.25,
    y: y + 0.52,
    w: w - 0.5,
    h: h - 1.0,
    fontFace: "Aptos",
    fontSize: 14,
    color: TOKENS.textSoft,
    align: "center",
    valign: "mid",
    margin: 0.08,
  }});
}}

function addStarterPackBadge(slide, spec) {{
  const label = ACTIVE_STARTER_PACK.eyebrow || STARTER_PACK;
  slide.addText(`starter pack: ${{label}}`, {{
    x: 9.6,
    y: 6.82,
    w: 2.1,
    h: 0.22,
    fontFace: "Aptos",
    fontSize: 8.5,
    color: TOKENS.textSoft,
    align: "right",
    margin: 0,
  }});
}}

function addStarterPackNotes(slide, spec) {{
  const narrative = spec.starterNarrative || deckSpec.starterNarrative || ACTIVE_STARTER_PACK.narrative;
  const emphasis = spec.starterEmphasis || ACTIVE_STARTER_PACK.emphasis;
  slide.addText(`Starter narrative: ${{narrative}}`, {{
    x: 0.7,
    y: 5.82,
    w: 6.2,
    h: 0.24,
    fontFace: "Aptos",
    fontSize: 8.5,
    color: TOKENS.textSoft,
    margin: 0,
  }});
  slide.addText(`Starter emphasis: ${{emphasis}}`, {{
    x: 0.7,
    y: 6.03,
    w: 6.2,
    h: 0.24,
    fontFace: "Aptos",
    fontSize: 8.5,
    color: TOKENS.textSoft,
    margin: 0,
  }});
}}

function addRiskNotes(slide, spec) {{
  const notes = spec.visualRiskNotes || [];
  if (!notes.length) return;
  slide.addText(`Risk notes: ${{notes.join("  ")}}`, {{
    x: 0.7,
    y: 6.25,
    w: 10.8,
    h: 0.35,
    fontFace: "Aptos",
    fontSize: 9,
    color: TOKENS.textSoft,
    margin: 0,
  }});
}}

function renderCover(slide, spec) {{
  slide.background = {{ color: TOKENS.bgWarm }};
  addEyebrow(slide, spec.pattern || "cover", 0.7, 0.5, 3.0);
  addHairline(slide, 0.72, 0.82, 2.1);
  slide.addText(spec.workingTitle || `Slide ${{spec.slideNumber}}`, {{
    x: 0.7,
    y: 1.0,
    w: 6.25,
    h: 1.6,
    fontFace: "Aptos Display",
    fontSize: 32,
    bold: true,
    color: TOKENS.textPrimary,
    margin: 0,
    breakLine: false,
  }});
  slide.addText(spec.dominantMessage || spec.keyMessage || "", {{
    x: 0.7,
    y: 2.75,
    w: 5.9,
    h: 1.15,
    fontFace: "Aptos",
    fontSize: 15,
    color: TOKENS.textSecondary,
    margin: 0,
    breakLine: false,
  }});
  addChip(slide, "hero focus", 0.72, 4.18, 1.45, {{ fill: TOKENS.surfaceAlt, line: TOKENS.ruleStrong, color: TOKENS.textSecondary }});
  slide.addText(spec.purpose || "", {{
    x: 2.35,
    y: 4.18,
    w: 3.9,
    h: 0.34,
    fontFace: "Aptos",
    fontSize: 10.5,
    color: TOKENS.textSoft,
    margin: 0,
  }});
  slide.addShape(pptx.ShapeType.roundRect, {{
    x: 7.15, y: 0.95, w: 5.15, h: 4.8,
    rectRadius: 0.1,
    line: {{ color: TOKENS.accent, pt: 1.2 }},
    fill: {{ color: TOKENS.accentSoft }},
  }});
  slide.addText((spec.visualsNeeded || []).join(" • ") || "hero visual field", {{
    x: 7.45, y: 2.15, w: 4.5, h: 1.1,
    fontFace: "Aptos", fontSize: 15, color: TOKENS.textSoft,
    align: "center", valign: "mid", margin: 0.08,
  }});
}}

function renderSectionDivider(slide, spec) {{
  slide.background = {{ color: TOKENS.bgWarm }};
  addEyebrow(slide, spec.pattern || "section-divider", 0.8, 0.75, 3.5);
  addHairline(slide, 0.82, 1.15, 1.4, TOKENS.accent);
  slide.addText(String(spec.slideNumber).padStart(2, "0"), {{
    x: 0.75,
    y: 1.4,
    w: 2.0,
    h: 1.3,
    fontFace: "Aptos Display",
    fontSize: 34,
    bold: true,
    color: TOKENS.accent,
    margin: 0,
  }});
  slide.addText(spec.workingTitle || "Section", {{
    x: 0.75,
    y: 3.0,
    w: 6.6,
    h: 0.9,
    fontFace: "Aptos Display",
    fontSize: 28,
    bold: true,
    color: TOKENS.textPrimary,
    margin: 0,
  }});
  slide.addText(spec.dominantMessage || spec.keyMessage || "", {{
    x: 0.8,
    y: 4.15,
    w: 5.6,
    h: 0.7,
    fontFace: "Aptos",
    fontSize: 12.5,
    color: TOKENS.textSecondary,
    margin: 0,
  }});
  addChip(slide, "chapter reset", 0.82, 5.15, 1.55, {{ fill: TOKENS.surfaceAlt, line: TOKENS.ruleStrong, color: TOKENS.textSecondary }});
}}

function renderAgenda(slide, spec) {{
  slide.background = {{ color: TOKENS.bgWhite }};
  addEyebrow(slide, spec.pattern || "agenda", 0.7, 0.45, 3.5);
  slide.addText(spec.workingTitle || "Agenda", {{
    x: 0.7,
    y: 0.9,
    w: 4.5,
    h: 0.6,
    fontFace: "Aptos Display",
    fontSize: 24,
    bold: true,
    color: TOKENS.textPrimary,
    margin: 0,
  }});
  slide.addText(spec.purpose || "", {{
    x: 0.7,
    y: 1.55,
    w: 5.5,
    h: 0.45,
    fontFace: "Aptos",
    fontSize: 11,
    color: TOKENS.textSecondary,
    margin: 0,
  }});
  addHairline(slide, 0.72, 1.95, 5.2);
  const agendaItems = (spec.agendaItems || []).length ? spec.agendaItems : ((spec.sourceIds || []).length ? spec.sourceIds : ["Section 1", "Section 2", "Section 3"]);
  let y = 2.2;
  agendaItems.slice(0, 5).forEach((item, idx) => {{
    slide.addText(String(idx + 1).padStart(2, "0"), {{
      x: 0.9,
      y,
      w: 0.55,
      h: 0.3,
      fontFace: "Aptos",
      fontSize: 14,
      bold: true,
      color: TOKENS.accent,
      margin: 0,
    }});
    slide.addText(item, {{
      x: 1.55,
      y: y - 0.02,
      w: 4.8,
      h: 0.35,
      fontFace: "Aptos",
      fontSize: 15,
      color: TOKENS.textPrimary,
      margin: 0,
    }});
    y += 0.7;
  }});
  slide.addShape(pptx.ShapeType.roundRect, {{
    x: 7.15, y: 1.45, w: 5.1, h: 4.05,
    rectRadius: 0.08,
    line: {{ color: TOKENS.rule, pt: 1 }},
    fill: {{ color: TOKENS.surfaceAlt }},
  }});
  slide.addText('Scan structure first. Decorate second.', {{
    x: 7.45, y: 2.1, w: 4.4, h: 0.8,
    fontFace: "Aptos Display", fontSize: 18, bold: true,
    color: TOKENS.textPrimary, align: "center", margin: 0,
  }});
  slide.addText((spec.visualsNeeded || []).join(" • ") || "navigation support field", {{
    x: 7.45, y: 3.1, w: 4.3, h: 1.0,
    fontFace: "Aptos", fontSize: 12, color: TOKENS.textSecondary,
    align: "center", valign: "mid", margin: 0.08,
  }});
}}

function renderThesisSummary(slide, spec) {{
  slide.background = {{ color: TOKENS.bgWhite }};
  addEyebrow(slide, spec.pattern || "thesis-summary", 0.7, 0.45, 3.8);
  slide.addText(spec.workingTitle || "Thesis", {{
    x: 0.7,
    y: 0.9,
    w: 4.8,
    h: 0.55,
    fontFace: "Aptos Display",
    fontSize: 23,
    bold: true,
    color: TOKENS.textPrimary,
    margin: 0,
  }});
  slide.addText(spec.dominantMessage || spec.keyMessage || "", {{
    x: 0.7,
    y: 1.7,
    w: 5.4,
    h: 1.55,
    fontFace: "Aptos Display",
    fontSize: 24,
    bold: true,
    color: TOKENS.textPrimary,
    margin: 0,
    breakLine: false,
  }});
  slide.addText(spec.purpose || "", {{
    x: 0.72,
    y: 3.45,
    w: 5.0,
    h: 0.8,
    fontFace: "Aptos",
    fontSize: 12,
    color: TOKENS.textSecondary,
    margin: 0,
  }});
  addChip(slide, spec.starterLayout || "thesis-hero-left", 0.72, 4.55, 1.9, {{ fill: TOKENS.surfaceAlt, line: TOKENS.ruleStrong, color: TOKENS.textSecondary }});
  addVisualPlaceholder(slide, spec, {{ x: 7.05, y: 1.45, w: 5.15, h: 3.95, fill: TOKENS.surfaceAlt }});
}}

function renderMetric(slide, spec) {{
  slide.background = {{ color: TOKENS.bgWhite }};
  addEyebrow(slide, spec.pattern || "metric", 0.7, 0.45, 3.5);
  slide.addText(spec.workingTitle || "Metric", {{
    x: 0.7,
    y: 0.9,
    w: 4.2,
    h: 0.5,
    fontFace: "Aptos Display",
    fontSize: 22,
    bold: true,
    color: TOKENS.textPrimary,
    margin: 0,
  }});
  slide.addText(spec.focalElement || spec.keyMessage || "KPI", {{
    x: 0.7,
    y: 1.85,
    w: 5.4,
    h: 1.3,
    fontFace: "Aptos Display",
    fontSize: 30,
    bold: true,
    color: TOKENS.accent,
    margin: 0,
    breakLine: false,
  }});
  addHairline(slide, 0.72, 3.12, 3.8, TOKENS.accent);
  slide.addText(spec.dominantMessage || spec.keyMessage || "", {{
    x: 0.72,
    y: 3.35,
    w: 5.6,
    h: 0.9,
    fontFace: "Aptos",
    fontSize: 14,
    color: TOKENS.textSecondary,
    margin: 0,
  }});
  slide.addShape(pptx.ShapeType.roundRect, {{
    x: 7.0, y: 1.25, w: 5.3, h: 4.05,
    rectRadius: 0.08,
    line: {{ color: TOKENS.rule, pt: 1 }},
    fill: {{ color: TOKENS.surfaceAlt }},
  }});
  slide.addText('support field', {{
    x: 7.35, y: 1.7, w: 1.9, h: 0.25,
    fontFace: "Aptos", fontSize: 9.5, bold: true,
    color: TOKENS.textSoft, margin: 0,
  }});
  slide.addText((spec.visualsNeeded || []).join(" • ") || "chart optional, not mandatory", {{
    x: 7.35, y: 2.45, w: 4.3, h: 1.2,
    fontFace: "Aptos", fontSize: 13, color: TOKENS.textSecondary,
    align: "center", valign: "mid", margin: 0.08,
  }});
}}

function renderComparison(slide, spec) {{
  slide.background = {{ color: TOKENS.bgWhite }};
  addEyebrow(slide, spec.pattern || "comparison", 0.7, 0.45, 3.5);
  slide.addText(spec.workingTitle || "Comparison", {{
    x: 0.7,
    y: 0.9,
    w: 5.4,
    h: 0.55,
    fontFace: "Aptos Display",
    fontSize: 23,
    bold: true,
    color: TOKENS.textPrimary,
    margin: 0,
  }});
  slide.addText(spec.dominantMessage || spec.keyMessage || "", {{
    x: 0.7,
    y: 1.55,
    w: 5.2,
    h: 0.6,
    fontFace: "Aptos",
    fontSize: 12,
    color: TOKENS.textSecondary,
    margin: 0,
  }});
  slide.addShape(pptx.ShapeType.roundRect, {{ x: 0.7, y: 2.25, w: 3.9, h: 2.6, rectRadius: 0.06, line: {{ color: TOKENS.rule, pt: 1 }}, fill: {{ color: TOKENS.surface }} }});
  slide.addShape(pptx.ShapeType.roundRect, {{ x: 4.95, y: 2.0, w: 4.5, h: 3.0, rectRadius: 0.06, line: {{ color: TOKENS.accent, pt: 1.2 }}, fill: {{ color: TOKENS.accentSoft }} }});
  slide.addText(spec.comparisonLeftTitle || "Current / baseline", {{ x: 1.0, y: 2.55, w: 2.8, h: 0.35, fontFace: "Aptos", fontSize: 17, bold: true, color: TOKENS.textPrimary, margin: 0 }});
  slide.addText(spec.comparisonRightTitle || "Recommended", {{ x: 5.25, y: 2.45, w: 3.0, h: 0.35, fontFace: "Aptos", fontSize: 18, bold: true, color: TOKENS.textPrimary, margin: 0 }});
  slide.addText(spec.comparisonLeftBody || "Lower emphasis, supporting lane", {{ x: 1.0, y: 3.08, w: 3.0, h: 0.9, fontFace: "Aptos", fontSize: 12, color: TOKENS.textSoft, margin: 0 }});
  slide.addText(spec.comparisonRightBody || spec.focalElement || "Recommended side should dominate", {{ x: 5.25, y: 3.05, w: 3.5, h: 0.95, fontFace: "Aptos", fontSize: 13, color: TOKENS.textSecondary, margin: 0 }});
  addChip(slide, "preferred", 8.15, 2.18, 1.0);
  addVisualPlaceholder(slide, spec, {{ x: 9.8, y: 2.15, w: 2.35, h: 2.85 }});
}}

function renderProcessTimeline(slide, spec) {{
  slide.background = {{ color: TOKENS.bgWhite }};
  addEyebrow(slide, spec.pattern || "process-timeline", 0.7, 0.45, 3.8);
  slide.addText(spec.workingTitle || "Timeline", {{
    x: 0.7, y: 0.9, w: 5.6, h: 0.55, fontFace: "Aptos Display", fontSize: 23, bold: true, color: TOKENS.textPrimary, margin: 0,
  }});
  slide.addText(spec.dominantMessage || spec.keyMessage || "", {{
    x: 0.7, y: 1.55, w: 6.0, h: 0.55, fontFace: "Aptos", fontSize: 12, color: TOKENS.textSecondary, margin: 0,
  }});
  const phases = (spec.timelinePhases || []).length ? spec.timelinePhases.slice(0, 4) : ["Phase 1", "Phase 2", "Phase 3", "Phase 4"];
  const stepXs = [1.0, 3.35, 5.7, 8.05];
  addHairline(slide, 0.72, 2.15, 6.0);
  slide.addShape(pptx.ShapeType.line, {{ x: 1.2, y: 3.55, w: 7.7, h: 0, line: {{ color: TOKENS.rule, pt: 1.2 }} }});
  stepXs.forEach((x, idx) => {{
    slide.addShape(pptx.ShapeType.ellipse, {{ x, y: 3.28, w: 0.32, h: 0.32, line: {{ color: idx === 1 ? TOKENS.accent : TOKENS.rule, pt: 1 }}, fill: {{ color: idx === 1 ? TOKENS.accent : TOKENS.surface }} }});
    slide.addText(phases[idx] || `Phase ${{idx + 1}}`, {{ x: x - 0.28, y: 2.65, w: 1.5, h: 0.4, fontFace: "Aptos", fontSize: 11, bold: true, color: idx === 1 ? TOKENS.accent : TOKENS.textPrimary, margin: 0, align: "center" }});
  }});
  slide.addText("Now", {{ x: 3.55, y: 3.95, w: 0.65, h: 0.22, fontFace: "Aptos", fontSize: 10, bold: true, color: TOKENS.accent, margin: 0, align: "center" }});
  slide.addText(spec.timelineCurrentLabel || spec.focalElement || "Current priority phase", {{ x: 3.1, y: 4.2, w: 2.1, h: 0.6, fontFace: "Aptos", fontSize: 12, color: TOKENS.textSecondary, margin: 0, align: "center" }});
  addChip(slide, "current focus", 3.35, 4.9, 1.35);
  addVisualPlaceholder(slide, spec, {{ x: 9.6, y: 2.1, w: 2.7, h: 2.8 }});
}}

function renderTwoColumnExplainer(slide, spec) {{
  slide.background = {{ color: TOKENS.bgWhite }};
  addEyebrow(slide, spec.pattern || "2-column-explainer", 0.7, 0.45, 4.2);
  slide.addText(spec.workingTitle || "Explainer", {{
    x: 0.7, y: 0.9, w: 5.2, h: 0.55, fontFace: "Aptos Display", fontSize: 23, bold: true, color: TOKENS.textPrimary, margin: 0,
  }});
  slide.addText(spec.dominantMessage || spec.keyMessage || "", {{
    x: 0.7, y: 1.6, w: 5.0, h: 1.0, fontFace: "Aptos", fontSize: 17, color: TOKENS.textPrimary, margin: 0, breakLine: false,
  }});
  slide.addText(spec.purpose || "", {{
    x: 0.75, y: 2.8, w: 4.7, h: 0.7, fontFace: "Aptos", fontSize: 11, color: TOKENS.textSecondary, margin: 0,
  }});
  addHairline(slide, 0.72, 3.75, 4.8);
  slide.addShape(pptx.ShapeType.roundRect, {{ x: 6.95, y: 1.45, w: 5.1, h: 3.95, rectRadius: 0.08, line: {{ color: TOKENS.rule, pt: 1 }}, fill: {{ color: TOKENS.surfaceAlt }} }});
  slide.addText(spec.focalElement || "Support block", {{ x: 7.25, y: 2.0, w: 4.4, h: 0.7, fontFace: "Aptos", fontSize: 16, bold: true, color: TOKENS.textPrimary, margin: 0, align: "left" }});
  slide.addText((spec.visualsNeeded || []).join(" • ") || "Evidence, quote, or supporting visual", {{ x: 7.25, y: 2.9, w: 4.2, h: 1.2, fontFace: "Aptos", fontSize: 12, color: TOKENS.textSecondary, margin: 0 }});
  addChip(slide, "support", 7.25, 4.7, 0.95, {{ fill: TOKENS.surface, line: TOKENS.ruleStrong, color: TOKENS.textSecondary }});
}}

function renderClosing(slide, spec) {{
  slide.background = {{ color: TOKENS.bgWarm }};
  addEyebrow(slide, spec.pattern || "closing", 0.7, 0.55, 3.0);
  addHairline(slide, 3.9, 1.22, 4.0, TOKENS.ruleStrong);
  slide.addText(spec.focalElement || spec.dominantMessage || spec.keyMessage || "Final takeaway", {{
    x: 0.9, y: 1.6, w: 10.4, h: 1.6, fontFace: "Aptos Display", fontSize: 28, bold: true, color: TOKENS.textPrimary, margin: 0, align: "center", breakLine: false,
  }});
  slide.addText(spec.dominantMessage || spec.keyMessage || "", {{ x: 2.0, y: 3.5, w: 8.2, h: 0.9, fontFace: "Aptos", fontSize: 14, color: TOKENS.textSecondary, margin: 0, align: "center" }});
  slide.addShape(pptx.ShapeType.roundRect, {{ x: 4.5, y: 4.9, w: 4.0, h: 0.6, rectRadius: 0.08, line: {{ color: TOKENS.accent, pt: 1.2 }}, fill: {{ color: TOKENS.accentSoft }} }});
  slide.addText(spec.closingCta || spec.purpose || "Next move", {{ x: 4.75, y: 5.08, w: 3.5, h: 0.22, fontFace: "Aptos", fontSize: 11, bold: true, color: TOKENS.accent, align: "center", margin: 0 }});
  slide.addText(spec.closingSupport || spec.starterLayout || "closing-takeaway", {{ x: 3.55, y: 5.68, w: 5.9, h: 0.22, fontFace: "Aptos", fontSize: 9, color: TOKENS.textSoft, align: "center", margin: 0 }});
}}

function renderEditorialDefault(slide, spec) {{
  slide.background = {{ color: spec.slideType === "cover" ? TOKENS.bgWarm : TOKENS.bgWhite }};
  addEyebrow(slide, spec.pattern || spec.slideType || "content", 0.7, 0.45, 3.5);
  slide.addText(spec.workingTitle || `Slide ${{spec.slideNumber}}`, {{
    x: 0.7,
    y: 0.85,
    w: 6.2,
    h: 0.6,
    fontFace: "Aptos Display",
    fontSize: spec.slideType === "cover" ? 26 : 22,
    bold: true,
    color: TOKENS.textPrimary,
    margin: 0,
  }});
  slide.addText(spec.purpose || "", {{
    x: 0.7,
    y: 1.5,
    w: 5.7,
    h: 0.45,
    fontFace: "Aptos",
    fontSize: 11,
    color: TOKENS.textSoft,
    margin: 0,
  }});
  slide.addText(spec.dominantMessage || spec.keyMessage || "", {{
    x: 0.7,
    y: 2.0,
    w: 5.8,
    h: 1.15,
    fontFace: "Aptos",
    fontSize: spec.pattern === "thesis-summary" ? 18 : 15,
    color: TOKENS.textPrimary,
    margin: 0,
    breakLine: false,
  }});
  slide.addText(`Focal: ${{spec.focalElement || "not set"}}`, {{
    x: 0.72,
    y: 3.35,
    w: 5.4,
    h: 0.3,
    fontFace: "Aptos",
    fontSize: 10,
    color: TOKENS.textSecondary,
    margin: 0,
  }});
  slide.addText(`Density target: ${{spec.densityTarget || "4/10"}}`, {{
    x: 0.72,
    y: 3.68,
    w: 5.4,
    h: 0.25,
    fontFace: "Aptos",
    fontSize: 9,
    color: TOKENS.textSoft,
    margin: 0,
  }});
  addVisualPlaceholder(slide, spec, {{ x: 7.1, y: 1.55, w: 5.2, h: 3.55 }});
}}

function renderSlide(slide, spec) {{
  if (spec.pattern === "cover") {{
    renderCover(slide, spec);
  }} else if (spec.pattern === "section-divider") {{
    renderSectionDivider(slide, spec);
  }} else if (spec.pattern === "agenda") {{
    renderAgenda(slide, spec);
  }} else if (spec.pattern === "thesis-summary") {{
    renderThesisSummary(slide, spec);
  }} else if (spec.pattern === "metric") {{
    renderMetric(slide, spec);
  }} else if (spec.pattern === "comparison") {{
    renderComparison(slide, spec);
  }} else if (spec.pattern === "process-timeline") {{
    renderProcessTimeline(slide, spec);
  }} else if (spec.pattern === "2-column-explainer") {{
    renderTwoColumnExplainer(slide, spec);
  }} else if (spec.pattern === "closing") {{
    renderClosing(slide, spec);
  }} else {{
    renderEditorialDefault(slide, spec);
  }}

  addStarterPackNotes(slide, spec);
  addRiskNotes(slide, spec);

  if (typeof layoutHelpers.warnIfSlideHasOverlaps === "function") {{
    layoutHelpers.warnIfSlideHasOverlaps(slide, pptx);
  }}
  if (typeof layoutHelpers.warnIfSlideElementsOutOfBounds === "function") {{
    layoutHelpers.warnIfSlideElementsOutOfBounds(slide, pptx);
  }}

  if (spec.slideType !== "cover") {{
    addPageBadge(slide, spec.slideNumber);
    addStarterPackBadge(slide, spec);
  }}
}}

for (const spec of slidePlan) {{
  const slide = pptx.addSlide();
  renderSlide(slide, spec);
}}

fs.mkdirSync(path.dirname(outputFile), {{ recursive: true }});

pptx.writeFile({{ fileName: outputFile }});
'''


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize Slides Lane v2 authoring files from planning artifacts.")
    parser.add_argument("task_dir", help="Task-local deck workspace directory.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite authoring files if they already exist.",
    )
    args = parser.parse_args()

    task_dir = Path(args.task_dir).expanduser().resolve()
    ensure_task_dirs(task_dir)
    planning_dir = task_dir / "planning"
    slide_outline_path = planning_dir / "slide_outline.json"
    deck_brief_path = planning_dir / "deck_brief.md"
    content_map_path = planning_dir / "content_map.md"
    deck_spec_path = planning_dir / "deck_spec.json"

    if not slide_outline_path.exists():
        raise SystemExit("Missing planning/slide_outline.json. Run slides_plan_from_sources.py first.")

    outline = json.loads(slide_outline_path.read_text(encoding="utf-8"))
    deck_spec = json.loads(deck_spec_path.read_text(encoding="utf-8")) if deck_spec_path.exists() else {}
    registry = load_registry(task_dir)
    deck_title = outline[0].get("workingTitle") if outline else task_dir.name

    authoring_dir = task_dir / "authoring"
    authoring_dir.mkdir(parents=True, exist_ok=True)

    helpers_src = Path(__file__).resolve().parent.parent / "assets" / "pptxgenjs_helpers"
    helpers_dst = authoring_dir / "pptxgenjs_helpers"
    if helpers_dst.exists() and args.force:
        shutil.rmtree(helpers_dst)
    if not helpers_dst.exists():
        shutil.copytree(helpers_src, helpers_dst)

    deck_js = authoring_dir / "deck.js"
    notes_md = authoring_dir / "authoring_notes.md"
    manifest_json = authoring_dir / "authoring_manifest.json"

    if not args.force:
        for path in [deck_js, notes_md, manifest_json]:
            if path.exists():
                raise SystemExit(f"Refusing to overwrite existing file without --force: {path}")

    deck_js.write_text(build_deck_stub(deck_title, outline, deck_spec), encoding="utf-8")
    notes_md.write_text(build_authoring_notes(deck_title, outline, deck_spec), encoding="utf-8")
    manifest = build_authoring_manifest(task_dir, deck_title, outline, registry, deck_spec)
    manifest["artifacts"]["runAuthoringCommand"] = (
        "NODE_PATH=/root/.openclaw/workspace/skills/slides/node_modules "
        "node authoring/deck.js"
    )
    manifest_json.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Initialized authoring workspace in {authoring_dir}")
    print(f"Deck stub: {deck_js}")
    print(f"Notes: {notes_md}")
    print(f"Manifest: {manifest_json}")
    print(f"Planning inputs: {deck_brief_path}, {content_map_path}, {slide_outline_path}, {deck_spec_path}")


if __name__ == "__main__":
    main()
