#!/usr/bin/env python3
"""Run a complete brand-demo workflow from website URL to sandbox branded showcase."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / 'scripts'
NODE_PATH = str(ROOT / 'node_modules')


def run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env, check=True, text=True)


def slugify(value: str) -> str:
    return ''.join(ch.lower() if ch.isalnum() else '-' for ch in value).strip('-') or 'brand'


def main() -> int:
    parser = argparse.ArgumentParser(description='Run the slides brand demo workflow.')
    parser.add_argument('--url', required=True, help='Live website URL for brand extraction')
    parser.add_argument('--name', required=True, help='Brand name label for sandbox output')
    parser.add_argument('--output', help='Optional sandbox output directory')
    parser.add_argument('--browser', action='store_true', help='Use browser-assisted brand extraction mode')
    parser.add_argument('--copy-to-media', action='store_true', help='Copy the generated PPTX into /root/.openclaw/media for easy delivery')
    args = parser.parse_args()

    brand_slug = slugify(args.name)
    output_dir = Path(args.output).expanduser().resolve() if args.output else (ROOT / 'examples' / f'{brand_slug}-branded-showcase')
    proposal_path = output_dir.parent / f'{brand_slug}-brand-proposal.md'

    if output_dir.exists():
        shutil.rmtree(output_dir)
    proposal_path.parent.mkdir(parents=True, exist_ok=True)

    onboarding_cmd = [
        'python3',
        str(SCRIPTS / 'slides_brand_onboarding.py'),
        '--url', args.url,
        '--output', str(proposal_path),
    ]
    if args.browser:
        onboarding_cmd.append('--browser')
    run(onboarding_cmd)

    run([
        'python3',
        str(SCRIPTS / 'slides_apply_brand_example.py'),
        str(proposal_path),
        '--name', args.name,
        '--output', str(output_dir),
    ])

    env = os.environ.copy()
    env['NODE_PATH'] = NODE_PATH
    run(['node', 'deck.js'], cwd=output_dir, env=env)

    pptx_name = f"{brand_slug}-branded-showcase.pptx"
    pptx_path = output_dir / 'exports' / pptx_name
    render_dir = output_dir / 'rendered'
    montage_path = output_dir / 'montage.png'

    run([
        'python3',
        str(SCRIPTS / 'render_slides.py'),
        str(pptx_path),
        '--output_dir', str(render_dir),
    ])
    run([
        'python3',
        str(SCRIPTS / 'create_montage.py'),
        '--input_dir', str(render_dir),
        '--output_file', str(montage_path),
    ])

    media_path = None
    if args.copy_to_media:
        media_dir = Path('/root/.openclaw/media')
        media_dir.mkdir(parents=True, exist_ok=True)
        media_path = media_dir / pptx_name
        shutil.copy2(pptx_path, media_path)

    print(f'Brand proposal: {proposal_path}')
    print(f'Sandbox deck: {output_dir / "deck.js"}')
    print(f'PPTX: {pptx_path}')
    print(f'Montage: {montage_path}')
    if media_path:
        print(f'Media copy: {media_path}')
    summary = {
        'brandName': args.name,
        'brandSlug': brand_slug,
        'url': args.url,
        'browserMode': args.browser,
        'proposalPath': str(proposal_path),
        'sandboxDeckPath': str(output_dir / 'deck.js'),
        'pptxPath': str(pptx_path),
        'montagePath': str(montage_path),
        'mediaPath': str(media_path) if media_path else None,
        'sendHint': {
            'messageToolFilePath': str(media_path) if media_path else str(pptx_path),
            'caption': f'{args.name} branded showcase',
        },
    }
    print('SUMMARY_JSON:' + json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
