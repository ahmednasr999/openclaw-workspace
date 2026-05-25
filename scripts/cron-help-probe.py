#!/usr/bin/env python3
import subprocess
for cmd in [['openclaw','cron','edit','--help'], ['openclaw','cron','run','--help'], ['openclaw','cron','runs','--help']]:
    print('$ ' + ' '.join(cmd), flush=True)
    p = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
    print(p.stdout)
    print(p.stderr)
    print('exit=', p.returncode)
