#!/usr/bin/env python3
import subprocess
import sys

PROFILE = 'openclaw'
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
    raise SystemExit('BLOCKED: Windows OpenClaw-managed Chrome lane is not reachable through browser.proxy')

tabs = run(['tabs'], required=False)
combined = f"{tabs.stdout}\n{tabs.stderr}"
if FEED not in combined and 'linkedin.com/feed' not in combined:
    run(['open', FEED, '--label', 'linkedin-profile'], timeout=90)
    tabs = run(['tabs'], timeout=60)
    combined = f"{tabs.stdout}\n{tabs.stderr}"

if 'linkedin.com/login' in combined or 'checkpoint' in combined:
    raise SystemExit('BLOCKED: Windows OpenClaw-managed Chrome is reachable but LinkedIn requires manual sign-in')

snapshot = run(['snapshot', '--format', 'aria', '--limit', '220'], timeout=90, required=False)
snapshot_text = f"{snapshot.stdout}\n{snapshot.stderr}"
if snapshot.returncode != 0:
    raise SystemExit('BLOCKED: Windows OpenClaw-managed Chrome is reachable but the LinkedIn feed snapshot failed')
if 'Ahmed Nasr' not in snapshot_text:
    raise SystemExit('BLOCKED: LinkedIn is open but Ahmed Nasr account identity was not visibly verified')

print('OK: Windows LinkedIn managed Chrome lane ready; no alert sent.')
