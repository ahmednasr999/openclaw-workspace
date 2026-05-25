#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path
WORKSPACE=Path('/root/.openclaw/workspace')
CID='bef6e2d8-fce7-44dc-acde-a76fbcb01a7e'
cmd=['openclaw','cron','run',CID,'--wait','--wait-timeout','12m','--poll-interval','5s']
print('$ '+' '.join(cmd), flush=True)
p=subprocess.run(cmd,cwd=WORKSPACE,text=True,capture_output=True,timeout=780)
if p.stdout:
    print(p.stdout.strip())
if p.stderr:
    print(p.stderr.strip(), file=sys.stderr)
print('exit=',p.returncode, flush=True)
sys.exit(p.returncode)
