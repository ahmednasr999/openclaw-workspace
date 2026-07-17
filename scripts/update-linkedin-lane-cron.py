#!/usr/bin/env python3
import subprocess
from pathlib import Path

CRON_ID = 'bef6e2d8-fce7-44dc-acde-a76fbcb01a7e'
WORKSPACE = Path('/root/.openclaw/workspace')
message = '''Ahmed-Mac LinkedIn Lane Guard. Use only the OpenClaw CLI through sandbox_exec without host override. Do not use host=gateway or node tools.

Checks:
1. Run `openclaw browser --browser-profile nasr-linkedin status`.
2. If not running, run `openclaw browser --browser-profile nasr-linkedin start`.
3. Run `openclaw browser --browser-profile nasr-linkedin tabs`.
4. Open `https://www.linkedin.com/feed/` only if no feed tab exists.
5. Snapshot the feed.

Do not post, like, comment, message, apply, or perform external LinkedIn actions.
If LinkedIn feed/nav is visible and Ahmed is logged in, final answer exactly: `OK: Ahmed-Mac LinkedIn lane ready; no alert sent.`
If blocked, final answer must state the exact blocker.'''
cmd = [
    'openclaw', 'cron', 'edit', CRON_ID,
    '--message', message,
    '--agent', 'cto',
    '--clear-session-key',
    '--model', 'openai/gpt-5.6-sol',
    '--timeout-seconds', '300',
]
print('$ ' + ' '.join(cmd[:5]) + ' ...', flush=True)
p = subprocess.run(cmd, cwd=WORKSPACE, text=True, capture_output=True, timeout=120)
print(p.stdout.strip())
print(p.stderr.strip())
print('exit=', p.returncode)
raise SystemExit(p.returncode)
