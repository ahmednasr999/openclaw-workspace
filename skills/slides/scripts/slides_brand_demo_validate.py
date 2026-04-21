#!/usr/bin/env python3
"""Validate the chained brand-demo workflow."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / 'scripts'
FIXTURE_URL = (ROOT / 'examples' / 'brand-site.html').resolve().as_uri()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix='slides-brand-demo-') as tmp:
        output_dir = Path(tmp) / 'brand-fixture-showcase'
        subprocess.run([
            'python3',
            str(SCRIPTS / 'slides_brand_demo.py'),
            '--url', FIXTURE_URL,
            '--name', 'Brand Fixture',
            '--output', str(output_dir),
            '--browser',
            '--copy-to-media',
        ], check=True, text=True)

        proposal_path = output_dir.parent / 'brand-fixture-brand-proposal.md'
        pptx_path = output_dir / 'exports' / 'brand-fixture-branded-showcase.pptx'
        montage_path = output_dir / 'montage.png'
        media_path = Path('/root/.openclaw/media') / 'brand-fixture-branded-showcase.pptx'

        failures: list[str] = []
        if not proposal_path.exists():
            failures.append('proposal markdown was not created')
        if not pptx_path.exists():
            failures.append('sandbox pptx was not created')
        if not montage_path.exists():
            failures.append('montage image was not created')
        if not media_path.exists():
            failures.append('media copy was not created')

        if failures:
            for failure in failures:
                print(f'FAIL {failure}')
            print(f'\nBrand demo validation failed with {len(failures)} issue(s).')
            return 1

    print('\nBrand demo validation passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
