#!/usr/bin/env python3
import subprocess
import sys

PROFILE = 'nasr-linkedin'
FEED = 'https://www.linkedin.com/feed/'

def run(args, timeout=60, required=True):
    cmd = ['openclaw', 'browser', '--browser-profile', PROFILE, *args]
    p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
    out = (p.stdout or '').strip()
    err = (p.stderr or '').strip()
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)
    if required and p.returncode != 0:
        raise SystemExit(f"BLOCKED: {' '.join(cmd)} failed with exit {p.returncode}")
    return p

status = run(['status'], required=False)
if status.returncode != 0:
    run(['start'], timeout=90)
    run(['status'])

tabs = run(['tabs'], required=False)
combined = f"{tabs.stdout}\n{tabs.stderr}"
if FEED not in combined and 'linkedin.com/feed' not in combined:
    run(['open', FEED], timeout=90)
    run(['tabs'], timeout=60)

print('OK: Ahmed-Mac LinkedIn lane ready; no alert sent.')
