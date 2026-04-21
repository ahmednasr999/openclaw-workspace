#!/usr/bin/env python3
"""Validate sandbox brand application helper."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / 'scripts'
PROPOSAL = ROOT / 'examples' / 'littlemight-brand-proposal.md'


def run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env, check=True, capture_output=True, text=True)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix='slides-brand-apply-') as tmp:
        sandbox = Path(tmp) / 'sandbox-showcase'
        run([
            'python3',
            str(SCRIPTS / 'slides_apply_brand_example.py'),
            str(PROPOSAL),
            '--name', 'Little Might',
            '--output', str(sandbox),
        ])

        deck_js = (sandbox / 'deck.js').read_text(encoding='utf-8')
        failures: list[str] = []
        checks = [
            ("Instrument Serif", "display font not applied"),
            ("Inter", "body font not applied"),
            ("F5F4ED", "background token not applied"),
            ("F7591F", "accent token not applied"),
            ("little-might-branded-showcase.pptx", "output filename not updated"),
        ]
        for needle, message in checks:
            if needle not in deck_js:
                failures.append(message)

        env = os.environ.copy()
        env['NODE_PATH'] = str(ROOT / 'node_modules')
        run(['node', 'deck.js'], cwd=sandbox, env=env)

        pptx_path = sandbox / 'exports' / 'little-might-branded-showcase.pptx'
        if not pptx_path.exists():
            failures.append('sandbox branded pptx was not created')

        print('\n## Brand apply validation summary')
        print(json.dumps({
            'sandbox': str(sandbox),
            'pptxExists': pptx_path.exists(),
            'outputFile': str(pptx_path),
        }, indent=2, ensure_ascii=False))

        if failures:
            for failure in failures:
                print(f'FAIL {failure}')
            print(f'\nBrand apply validation failed with {len(failures)} issue(s).')
            return 1

    print('\nBrand apply validation passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
