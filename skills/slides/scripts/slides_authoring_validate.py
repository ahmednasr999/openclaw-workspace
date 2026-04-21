#!/usr/bin/env python3
"""Validate authoring-stub generation for Slides Lane v2."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import slides_init_authoring_task as authoring  # noqa: E402


FIXTURE_OUTLINE = [
    {
        "slideNumber": 1,
        "slideType": "cover",
        "pattern": "cover",
        "workingTitle": "Editorial Slide Pattern Showcase",
        "purpose": "Set the frame.",
        "keyMessage": "Pattern-aware planning should shape default output.",
        "dominantMessage": "Pattern-aware planning should shape default output.",
        "focalElement": "Editorial Slide Pattern Showcase",
        "densityTarget": "2/10",
        "visualRiskNotes": ["Keep the opening sparse and decisive."],
        "visualsNeeded": ["hero field"],
        "sourceIds": ["src-1"],
    },
    {
        "slideNumber": 2,
        "slideType": "toc",
        "pattern": "agenda",
        "workingTitle": "Agenda",
        "purpose": "Set the narrative path.",
        "keyMessage": "Show the major sections before going deeper.",
        "dominantMessage": "Show the major sections before going deeper.",
        "focalElement": "Narrative path",
        "densityTarget": "4/10",
        "starterLayout": "agenda-list",
        "agendaItems": ["Problem", "Recommendations", "Timeline", "Next step"],
        "visualRiskNotes": ["Agenda should scan fast."],
        "visualsNeeded": ["navigation block"],
        "sourceIds": ["src-1"],
    },
    {
        "slideNumber": 3,
        "slideType": "content",
        "pattern": "metric",
        "workingTitle": "Key KPI",
        "purpose": "Show the core KPI.",
        "keyMessage": "72% automation coverage.",
        "dominantMessage": "72% automation coverage.",
        "focalElement": "72% automation coverage",
        "densityTarget": "3/10",
        "visualRiskNotes": ["Do not bury the number inside cards."],
        "visualsNeeded": ["KPI block"],
        "sourceIds": ["src-1"],
    },
    {
        "slideNumber": 4,
        "slideType": "content",
        "pattern": "comparison",
        "workingTitle": "Decision framing",
        "purpose": "Compare two options.",
        "keyMessage": "Recommended lane should dominate visually.",
        "dominantMessage": "Recommended lane should dominate visually.",
        "focalElement": "Recommended lane",
        "densityTarget": "4/10",
        "comparisonLeftTitle": "Current / baseline",
        "comparisonRightTitle": "Recommended",
        "comparisonLeftBody": "Fragmented ownership and duplicated tooling.",
        "comparisonRightBody": "One office, one pilot, one accountable owner.",
        "visualRiskNotes": ["Avoid fake symmetry."],
        "visualsNeeded": ["comparison block"],
        "sourceIds": ["src-1"],
    },
    {
        "slideNumber": 5,
        "slideType": "content",
        "pattern": "process-timeline",
        "workingTitle": "Phased rollout",
        "purpose": "Show sequence.",
        "keyMessage": "The process spine should be obvious.",
        "dominantMessage": "The process spine should be obvious.",
        "focalElement": "Current priority phase",
        "densityTarget": "4/10",
        "timelinePhases": ["Pilot", "Scale", "Standardize", "Embed"],
        "timelineCurrentLabel": "Scale",
        "visualRiskNotes": ["Too many milestones will collapse the sequence."],
        "visualsNeeded": ["milestone view"],
        "sourceIds": ["src-1"],
    },
    {
        "slideNumber": 6,
        "slideType": "summary",
        "pattern": "closing",
        "workingTitle": "Summary and Next Step",
        "purpose": "Close decisively.",
        "keyMessage": "Make the default output feel designed.",
        "dominantMessage": "Make the default output feel designed.",
        "focalElement": "Make the default output feel designed.",
        "densityTarget": "3/10",
        "closingCta": "Approve the pilot",
        "closingSupport": "Smallest complete move that creates operating proof.",
        "visualRiskNotes": ["Do not end with administrative sludge."],
        "visualsNeeded": ["closing callout"],
        "sourceIds": ["src-1"],
    },
]

REQUIRED_SNIPPETS = [
    'require("./pptxgenjs_helpers/safe")',
    'const deckSpec = {',
    'const STARTER_PACK = deckSpec.starterPack || "executive-summary";',
    'const STARTER_PACK_HINTS = {',
    'function addStarterPackBadge(slide, spec) {',
    'function addStarterPackNotes(slide, spec) {',
    'function renderCover(slide, spec)',
    'function renderThesisSummary(slide, spec)',
    'function renderMetric(slide, spec)',
    'function renderComparison(slide, spec)',
    'function renderProcessTimeline(slide, spec)',
    'function renderTwoColumnExplainer(slide, spec)',
    'function renderClosing(slide, spec)',
    'spec.pattern === "thesis-summary"',
    'spec.pattern === "process-timeline"',
    'spec.pattern === "2-column-explainer"',
    'spec.pattern === "closing"',
    'dominantMessage',
    'visualRiskNotes',
    'starterLayout',
    'Density target:',
    'Risk notes:',
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate slides authoring stub generation.")
    parser.parse_args()

    deck_spec = {
        'objective': 'Test deck spec propagation.',
        'audience': 'executive / leadership',
        'tone': 'direct, decision-oriented',
        'targetSlideCount': len(FIXTURE_OUTLINE),
        'aspectRatio': '16:9',
        'styleMode': 'editorial-default',
        'brandMode': 'unbranded',
        'starterPack': 'executive-summary',
        'starterNarrative': 'Move from problem to decision with minimal friction.',
        'imagePolicy': 'optional-supporting-visuals',
        'editableOutputRequired': True,
        'polishLevel': 'working-draft',
        'confidence': 'high',
        'unresolvedAssumptions': [],
    }
    stub = authoring.build_deck_stub('Authoring Validation Deck', FIXTURE_OUTLINE, deck_spec)
    notes = authoring.build_authoring_notes('Authoring Validation Deck', FIXTURE_OUTLINE, deck_spec)
    manifest = authoring.build_authoring_manifest(Path('/tmp/authoring-validation'), 'Authoring Validation Deck', FIXTURE_OUTLINE, {'entries': [{'id': 'src-1'}]}, deck_spec)

    failures: list[str] = []

    for snippet in REQUIRED_SNIPPETS:
        if snippet not in stub:
            failures.append(f"Missing expected stub snippet: {snippet}")

    if '- Objective: Test deck spec propagation.' not in notes:
        failures.append('Authoring notes missing deck spec objective line')
    if '- Starter pack: executive-summary' not in notes:
        failures.append('Authoring notes missing starter pack line')
    if '- Starter narrative: Move from problem to decision with minimal friction.' not in notes:
        failures.append('Authoring notes missing starter narrative line')
    if '- Pattern: metric' not in notes:
        failures.append('Authoring notes missing pattern metadata for metric slide')
    if '- Focal element: 72% automation coverage' not in notes:
        failures.append('Authoring notes missing focal element line')
    if '- Starter layout:' not in notes:
        failures.append('Authoring notes missing starter layout line')
    if '- Agenda items: Problem, Recommendations, Timeline, Next step' not in notes:
        failures.append('Authoring notes missing agenda items line')
    if '- Visual risk notes:' not in notes:
        failures.append('Authoring notes missing visual risk notes block')

    if manifest.get('deckSpec', {}).get('starterPack') != 'executive-summary':
        failures.append('Manifest did not preserve deckSpec starterPack')
    if manifest.get('workflowState', {}).get('current') != 'authoring':
        failures.append('Manifest missing workflowState current phase')
    if manifest.get('deliveryContract', {}).get('required') is None:
        failures.append('Manifest missing deliveryContract')

    manifest_slide = manifest['slides'][2]
    if manifest_slide.get('pattern') != 'metric':
        failures.append('Manifest did not preserve metric pattern')
    if manifest_slide.get('focalElement') != '72% automation coverage':
        failures.append('Manifest did not preserve focalElement')
    if manifest_slide.get('densityTarget') != '3/10':
        failures.append('Manifest did not preserve densityTarget')
    if manifest_slide.get('starterLayout') != 'metric-kpi-hero':
        failures.append('Manifest did not preserve starterLayout')

    agenda_slide = manifest['slides'][1]
    if agenda_slide.get('agendaItems') != ['Problem', 'Recommendations', 'Timeline', 'Next step']:
        failures.append('Manifest did not preserve agendaItems')

    comparison_slide = manifest['slides'][3]
    if comparison_slide.get('comparisonRightBody') != 'One office, one pilot, one accountable owner.':
        failures.append('Manifest did not preserve comparison fields')

    timeline_slide = manifest['slides'][4]
    if timeline_slide.get('timelineCurrentLabel') != 'Scale':
        failures.append('Manifest did not preserve timeline fields')

    closing_slide = manifest['slides'][5]
    if closing_slide.get('closingCta') != 'Approve the pilot':
        failures.append('Manifest did not preserve closing CTA')

    print('\n## Stub validation summary')
    print(json.dumps({
        'checkedSnippets': len(REQUIRED_SNIPPETS),
        'workflowState': manifest.get('workflowState', {}),
        'deliveryContract': manifest.get('deliveryContract', {}),
        'deckSpec': manifest.get('deckSpec', {}),
        'manifestSlideExample': manifest_slide,
    }, indent=2, ensure_ascii=False))

    if failures:
        for failure in failures:
            print(f'FAIL {failure}')
        print(f'\nAuthoring validation failed with {len(failures)} issue(s).')
        return 1

    print('\nAuthoring stub validation passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
