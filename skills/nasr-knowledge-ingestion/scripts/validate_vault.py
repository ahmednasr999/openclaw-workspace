#!/usr/bin/env python3
"""Validate a NASR/Obsidian-style pilot vault.

Checks:
- Markdown wikilinks roughly resolve by full path without .md or by basename.
- .canvas files parse as JSON.
- file nodes reference existing files inside the vault.
- edges reference existing node ids.
"""
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
if not root.exists():
    print(f'Vault not found: {root}', file=sys.stderr)
    sys.exit(2)

errors = []
md_files = list(root.rglob('*.md'))
all_rel = {p.relative_to(root).with_suffix('').as_posix() for p in md_files}
all_names = {p.stem for p in md_files}

for p in md_files:
    text = p.read_text(errors='replace')
    for link in re.findall(r'\[\[([^\]|#]+)', text):
        if link not in all_rel and pathlib.Path(link).name not in all_names:
            errors.append(f'{p.relative_to(root)}: unresolved wikilink [[{link}]]')

for canvas_path in root.rglob('*.canvas'):
    try:
        canvas = json.loads(canvas_path.read_text())
    except Exception as exc:
        errors.append(f'{canvas_path.relative_to(root)}: invalid JSON: {exc}')
        continue
    node_ids = {n.get('id') for n in canvas.get('nodes', [])}
    for node in canvas.get('nodes', []):
        if node.get('type') == 'file':
            f = root / node.get('file', '')
            if not f.exists():
                errors.append(f'{canvas_path.relative_to(root)}: missing canvas file node target: {node.get("file")}')
    for edge in canvas.get('edges', []):
        if edge.get('fromNode') not in node_ids or edge.get('toNode') not in node_ids:
            errors.append(f'{canvas_path.relative_to(root)}: bad edge endpoint: {edge}')

if errors:
    print('\n'.join(errors))
    sys.exit(1)

print(f'OK: {len(md_files)} markdown files, {len(list(root.rglob("*.canvas")))} canvas files')
