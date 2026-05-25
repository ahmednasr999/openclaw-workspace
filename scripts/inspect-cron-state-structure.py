#!/usr/bin/env python3
import json
from pathlib import Path
p=Path('/root/.openclaw/cron/jobs-state.json')
data=json.loads(p.read_text())
print(type(data), list(data.keys())[:20])
CID='bef6e2d8-fce7-44dc-acde-a76fbcb01a7e'
for path, obj in [('root', data), ('jobs', data.get('jobs',{})), ('states', data.get('states',{}))]:
    if isinstance(obj, dict) and CID in obj:
        print('found in', path)
        print(json.dumps(obj[CID], indent=2)[:4000])
