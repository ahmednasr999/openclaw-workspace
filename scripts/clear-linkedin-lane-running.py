#!/usr/bin/env python3
import json, shutil
from datetime import datetime
from pathlib import Path
CID='bef6e2d8-fce7-44dc-acde-a76fbcb01a7e'
p=Path('/root/.openclaw/cron/jobs-state.json')
data=json.loads(p.read_text())
state=data['jobs'][CID]['state']
old=state.pop('runningAtMs', None)
stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
bak=p.with_name(f'jobs-state.json.bak-linkedin-lane-running-{stamp}')
if old is not None:
    shutil.copy2(p,bak)
    p.write_text(json.dumps(data, indent=2)+'\n')
    json.loads(p.read_text())
print(f'runningAtMs_removed={old}')
if old is not None:
    print(f'backup={bak}')
