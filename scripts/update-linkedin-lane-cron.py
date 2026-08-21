#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

CRON_NAME = 'Windows LinkedIn Lane Guard'
WORKSPACE = Path('/root/.openclaw/workspace')
message = '''Windows LinkedIn Lane Guard. Use the authenticated Windows OpenClaw-managed Chrome profile through browser.proxy only. This lane is extension-free: do not request extension installation, pairing, or tab attachment. Do not use Ahmed-Mac, VPS browsers, exported cookies, or server-side authenticated fallbacks.

Checks:
1. Run `openclaw browser --browser-profile openclaw status`.
2. If the Windows managed profile is unreachable, stop and report that exact blocker.
3. Run `openclaw browser --browser-profile openclaw tabs`.
4. Open `https://www.linkedin.com/feed/` only if no feed tab exists.
5. Snapshot the feed.

Do not post, like, comment, message, apply, or perform external LinkedIn actions.
If LinkedIn feed/nav is visible and Ahmed is logged in, final answer exactly: `OK: Windows LinkedIn managed Chrome lane ready; no alert sent.`
If blocked, final answer must state the exact blocker.'''
listed = subprocess.run(
    ['openclaw', 'cron', 'list', '--json'],
    cwd=WORKSPACE,
    text=True,
    capture_output=True,
    timeout=120,
    check=True,
)
jobs = json.loads(listed.stdout).get('jobs', [])
matches = [job for job in jobs if job.get('name') == CRON_NAME]
if not matches:
    print(f'SKIP: cron job not installed: {CRON_NAME}')
    raise SystemExit(0)
if len(matches) != 1:
    raise SystemExit(f'BLOCKED: expected one cron named {CRON_NAME!r}, found {len(matches)}')
cron_id = matches[0]['id']

cmd = [
    'openclaw', 'cron', 'edit', cron_id,
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
