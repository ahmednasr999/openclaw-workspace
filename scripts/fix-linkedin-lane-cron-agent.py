#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path
WORKSPACE = Path('/root/.openclaw/workspace')
CRON_ID = 'bef6e2d8-fce7-44dc-acde-a76fbcb01a7e'

def run(cmd, timeout=120):
    print('$ ' + ' '.join(cmd), flush=True)
    p = subprocess.run(cmd, cwd=WORKSPACE, text=True, capture_output=True, timeout=timeout)
    if p.stdout:
        print(p.stdout.strip())
    if p.stderr:
        print(p.stderr.strip(), file=sys.stderr)
    print('exit=', p.returncode, flush=True)
    if p.returncode != 0:
        sys.exit(p.returncode)
    return p

run(['openclaw','cron','edit',CRON_ID,'--agent','cto','--model','openai/gpt-5.6-sol','--timeout-seconds','900'])
run(['openclaw','cron','show',CRON_ID])
run(['openclaw','cron','run',CRON_ID,'--wait','--wait-timeout','12m','--poll-interval','5s'], timeout=780)
run(['openclaw','cron','show',CRON_ID])
