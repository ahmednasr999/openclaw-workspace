#!/usr/bin/env python3
"""End-to-end validation for the redesigned slides workflow."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / 'scripts'
EXAMPLES = ROOT / 'examples'
SOURCE = EXAMPLES / 'integration-source.md'
NODE_PATH = str(ROOT / 'node_modules')


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True, capture_output=True, text=True)


def assert_true(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix='slides-int-') as tmp:
        task_dir = Path(tmp) / 'task'
        run(['python3', str(SCRIPTS / 'slides_ingest.py'), str(task_dir), str(SOURCE)])
        ingest_ok = True
        run(['python3', str(SCRIPTS / 'slides_extract_sources.py'), str(task_dir)])
        extraction_ok = True
        run(['python3', str(SCRIPTS / 'slides_plan_from_sources.py'), str(task_dir), '--slide-count', '7'])
        planning_ok = True
        run(['python3', str(SCRIPTS / 'slides_init_authoring_task.py'), str(task_dir)])
        authoring_init_ok = True

        outline_path = task_dir / 'planning' / 'slide_outline.json'
        deck_spec_path = task_dir / 'planning' / 'deck_spec.json'
        manifest_path = task_dir / 'authoring' / 'authoring_manifest.json'
        notes_path = task_dir / 'authoring' / 'authoring_notes.md'
        deck_js_path = task_dir / 'authoring' / 'deck.js'
        export_path = task_dir / 'exports' / 'Transformation-Brief.pptx'

        outline = json.loads(outline_path.read_text(encoding='utf-8'))
        deck_spec = json.loads(deck_spec_path.read_text(encoding='utf-8'))
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        notes = notes_path.read_text(encoding='utf-8')
        deck_js = deck_js_path.read_text(encoding='utf-8')

        assert_true(any(slide.get('pattern') == 'thesis-summary' for slide in outline), 'Outline missing thesis-summary slide', failures)
        assert_true(any(slide.get('pattern') == 'process-timeline' for slide in outline), 'Outline missing process-timeline slide', failures)
        assert_true(any(slide.get('pattern') == 'metric' for slide in outline), 'Outline missing metric slide', failures)
        assert_true(any(slide.get('pattern') == 'agenda' for slide in outline), 'Outline missing agenda slide', failures)
        assert_true(deck_spec.get('aspectRatio') == '16:9', 'Deck spec missing aspect ratio', failures)
        assert_true(deck_spec.get('starterPack') == 'transformation-roadmap', 'Deck spec starterPack did not match expected recommendation', failures)
        assert_true(bool(deck_spec.get('starterNarrative')), 'Deck spec missing starter narrative', failures)
        assert_true(manifest.get('deckSpec', {}).get('starterPack') == deck_spec.get('starterPack'), 'Manifest deckSpec did not preserve starterPack', failures)
        assert_true(manifest['slides'][0].get('pattern') == 'cover', 'Manifest first slide is not cover', failures)
        assert_true(any((slide.get('agendaItems') or []) for slide in manifest['slides']), 'Manifest missing agendaItems', failures)
        assert_true(any((slide.get('timelinePhases') or []) for slide in manifest['slides']), 'Manifest missing timelinePhases', failures)
        assert_true(any(slide.get('closingCta') for slide in manifest['slides']), 'Manifest missing closing CTA', failures)
        assert_true('- Pattern: thesis-summary' in notes, 'Authoring notes missing thesis-summary pattern line', failures)
        assert_true('- Starter pack: transformation-roadmap' in notes, 'Authoring notes missing starter pack line', failures)
        assert_true('- Starter narrative: Show sequence, ownership, and the next committed move clearly.' in notes, 'Authoring notes missing starter narrative line', failures)
        assert_true('require("./pptxgenjs_helpers/safe")' in deck_js, 'Generated deck.js missing safe helper import', failures)
        assert_true('const deckSpec = {' in deck_js, 'Generated deck.js missing deckSpec constant', failures)
        assert_true('const STARTER_PACK_HINTS = {' in deck_js, 'Generated deck.js missing starter pack hints', failures)
        assert_true('function renderMetric(slide, spec)' in deck_js, 'Generated deck.js missing renderMetric renderer', failures)
        assert_true('function renderProcessTimeline(slide, spec)' in deck_js, 'Generated deck.js missing renderProcessTimeline renderer', failures)
        assert_true('spec.comparisonRightBody' in deck_js, 'Generated deck.js missing pattern-aware comparison fields', failures)
        assert_true('spec.timelineCurrentLabel' in deck_js, 'Generated deck.js missing pattern-aware timeline fields', failures)
        assert_true('spec.closingCta' in deck_js, 'Generated deck.js missing pattern-aware closing fields', failures)

        env = os.environ.copy()
        env['NODE_PATH'] = NODE_PATH
        subprocess.run(['node', 'authoring/deck.js'], cwd=task_dir, env=env, check=True, capture_output=True, text=True)
        build_ok = True
        assert_true(export_path.exists(), 'Expected PPTX export was not created', failures)

        render_dir = task_dir / 'rendered-validation'
        run(['python3', str(SCRIPTS / 'render_slides.py'), str(export_path), '--output_dir', str(render_dir)])
        render_ok = True
        rendered_pngs = list(render_dir.glob('*.png'))
        assert_true(len(rendered_pngs) >= 1, 'Rendered PNG output missing', failures)

        print('\n## Slides integration summary')
        print(json.dumps({
            'taskDir': str(task_dir),
            'workflowState': {
                'ingestOk': ingest_ok,
                'extractionOk': extraction_ok,
                'planningOk': planning_ok,
                'authoringInitOk': authoring_init_ok,
                'buildOk': build_ok,
                'renderOk': render_ok,
            },
            'slideCount': len(outline),
            'deckSpecPresent': deck_spec_path.exists(),
            'starterPack': deck_spec.get('starterPack'),
            'patternsDetected': [slide.get('pattern') for slide in outline],
            'exportExists': export_path.exists(),
            'renderedPngCount': len(rendered_pngs),
        }, indent=2, ensure_ascii=False))

        if failures:
            for failure in failures:
                print(f'FAIL {failure}')
            print(f'\nIntegration validation failed with {len(failures)} issue(s).')
            return 1

    print('\nSlides integration validation passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
