#!/usr/bin/env python3
"""Lightweight OpenClaw skill hygiene checker.

Warns on missing progressive-disclosure, source-of-truth, approval-boundary,
and verification cues. This is intentionally advisory, not a hard gate.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOTS = [
    Path('/root/.openclaw/workspace/skills'),
    Path('/root/.openclaw/workspace-hr/skills'),
    Path('/root/.openclaw/workspace-cmo/skills'),
]

OPERATIONAL_HINTS = re.compile(
    r'(gateway|runtime|publish|linkedin|job|cv|email|message|post|config|restart|update|artifact|report|scan|apply|application|code|review|github|pr|branch|test|deploy|release)',
    re.I,
)

DESCRIPTION_ACTION_HINTS = re.compile(
    r'\b(use|run|create|generate|review|verify|fix|publish|inspect|analyze|triage|check|diagnose|deploy|release|write|update|send)\b',
    re.I,
)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith('---'):
        return {}, text
    parts = text.split('---', 2)
    if len(parts) < 3:
        return {}, text
    fm_text = parts[1]
    body = parts[2]
    fm: dict[str, str] = {}
    for line in fm_text.splitlines():
        if ':' in line and not line.startswith(' '):
            k, v = line.split(':', 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm, body


def check_skill(skill_md: Path) -> list[str]:
    text = skill_md.read_text(errors='replace')
    fm, body = parse_frontmatter(text)
    base = skill_md.parent
    warnings: list[str] = []
    name = fm.get('name')
    desc = fm.get('description')

    if not text.startswith('---\n'):
        warnings.append('frontmatter must start on line 1')

    if not name:
        warnings.append('missing frontmatter name')
    if not desc:
        warnings.append('missing frontmatter description')
    else:
        desc_lower = desc.lower()
        if len(desc) < 30 or desc_lower.startswith(('use for tasks', 'use when needed')):
            warnings.append('description may be too generic')
        if not DESCRIPTION_ACTION_HINTS.search(desc):
            warnings.append('description should be action-oriented for routing')
        if not re.search(r'\b([a-z0-9_/-]+|[A-Z][A-Za-z0-9]+)\b', desc) or len(set(re.findall(r'[A-Za-z0-9_-]{4,}', desc_lower))) < 4:
            warnings.append('description may lack specific routing nouns')

    operational = bool(OPERATIONAL_HINTS.search((name or '') + ' ' + (desc or '') + ' ' + body[:1000]))

    has_refs = (base / 'references').is_dir() or (base / 'reference').is_dir()
    has_checklists = (base / 'checklists').is_dir() or (base / 'eval').is_dir()

    if operational and not has_refs:
        warnings.append('operational skill missing references/ directory')
    if operational and not has_checklists:
        warnings.append('operational skill missing checklists/ or eval/ directory')

    lowered = text.lower()
    if operational and 'source' not in lowered and 'truth' not in lowered:
        warnings.append('operational skill lacks source-of-truth guidance')
    if operational and 'approval' not in lowered and 'ask' not in lowered:
        warnings.append('operational skill lacks approval-boundary guidance')
    if operational and 'verify' not in lowered and 'verification' not in lowered and 'done means' not in lowered:
        warnings.append('operational skill lacks verification/done guidance')

    if len(text.split()) > 2500 and has_refs:
        warnings.append('SKILL.md is long despite references; consider progressive disclosure')

    # Check referenced local markdown paths exist for references/checklists/examples.
    for match in re.findall(r'`((?:references|reference|checklists|examples|eval)/[^`]+?\.md)`', text):
        if not (base / match).exists():
            warnings.append(f'referenced file missing: {match}')

    return warnings


def iter_skills(paths: list[Path]):
    for root in paths:
        if root.is_file() and root.name == 'SKILL.md':
            yield root
        elif root.is_dir():
            own = root / 'SKILL.md'
            if own.exists():
                yield own
            else:
                yield from sorted(root.glob('*/SKILL.md'))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='*', help='Skill dirs or SKILL.md files. Defaults to known skill roots.')
    ap.add_argument('--quiet-ok', action='store_true', help='Only print warnings')
    args = ap.parse_args()
    paths = [Path(p).expanduser() for p in args.paths] if args.paths else ROOTS
    total = warned = 0
    for skill in iter_skills(paths):
        total += 1
        warnings = check_skill(skill)
        if warnings:
            warned += 1
            print(f'WARN {skill}')
            for w in warnings:
                print(f'  - {w}')
        elif not args.quiet_ok:
            print(f'OK {skill}')
    print(f'summary: checked={total} warned={warned}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
