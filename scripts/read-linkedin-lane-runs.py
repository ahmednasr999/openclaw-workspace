#!/usr/bin/env python3
from pathlib import Path
p=Path('/root/.openclaw/cron/runs/bef6e2d8-fce7-44dc-acde-a76fbcb01a7e.jsonl')
print('exists=', p.exists(), 'size=', p.stat().st_size if p.exists() else None)
if p.exists():
    lines=p.read_text(errors='replace').splitlines()
    print('lines=', len(lines))
    for line in lines[-8:]:
        print(line[:2500])
