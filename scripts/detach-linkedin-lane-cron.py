#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path
WORKSPACE=Path('/root/.openclaw/workspace')
CID='bef6e2d8-fce7-44dc-acde-a76fbcb01a7e'
for cmd in [
    ['openclaw','cron','edit',CID,'--agent','cto','--clear-session-key','--model','openai-codex/gpt-5.5','--timeout-seconds','900'],
    ['openclaw','cron','show',CID],
    ['openclaw','cron','run',CID],
    ['openclaw','cron','show',CID],
]:
    print('$ '+' '.join(cmd), flush=True)
    p=subprocess.run(cmd,cwd=WORKSPACE,text=True,capture_output=True,timeout=120)
    if p.stdout: print(p.stdout.strip())
    if p.stderr: print(p.stderr.strip(), file=sys.stderr)
    print('exit=',p.returncode, flush=True)
    if p.returncode != 0: sys.exit(p.returncode)
