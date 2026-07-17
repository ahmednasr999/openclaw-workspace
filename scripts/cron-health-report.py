#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path('/root/.openclaw/workspace')
STATUS_DIR = ROOT / 'logs' / 'cron' / 'status'
REPORT = ROOT / 'reports' / 'cron-health-latest.md'
CAIRO = ZoneInfo('Africa/Cairo')
WRAPPER = '/root/.openclaw/workspace/scripts/cron-run-with-alert.sh'


def now() -> datetime:
    return datetime.now(CAIRO)


def parse_crontab_tasks() -> list[dict]:
    try:
        text = subprocess.check_output(['crontab', '-l'], text=True, timeout=10)
    except Exception:
        return []
    tasks = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or line.startswith('CRON_TZ='):
            continue
        parts = line.split()
        if len(parts) < 10 or parts[5] != WRAPPER:
            continue
        schedule = ' '.join(parts[:5])
        task = parts[6]
        lock = parts[7]
        log = parts[8]
        tasks.append({'task': task, 'schedule': schedule, 'lock': lock, 'log': log})
    return tasks


def freshness_limit(schedule: str) -> timedelta | None:
    minute, hour, dom, month, dow = schedule.split()[:5]
    if dom != '*' or month != '*' or dow != '*':
        return None
    if minute.startswith('*/') or hour == '*':
        return timedelta(hours=1)
    if hour.startswith('*/'):
        return timedelta(hours=4)
    return timedelta(hours=30)


def load_status(task: str) -> dict | None:
    path = STATUS_DIR / f'{task}.json'
    if not path.exists():
        return None
    last_error = ''
    for attempt in range(3):
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception as exc:
            last_error = str(exc)
            if attempt < 2:
                time.sleep(0.1)
    return {'task': task, 'status': 'unreadable', 'error': last_error, 'returncode': 1}


def send_alert(message: str) -> None:
    subprocess.run([
        'openclaw', 'message', 'send', '--channel', 'telegram', '--target', '-1003882622947',
        '--thread-id', '10', '--message', message, '--json'
    ], text=True, capture_output=True, timeout=30)


def main() -> int:
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    tasks = parse_crontab_tasks()
    ts = now()
    problems = []
    rows = []

    for item in tasks:
        task = item['task']
        status = load_status(task)
        lock_path = Path(item['lock'])
        lock_note = 'present' if lock_path.exists() else 'missing'
        if status is None:
            rows.append(f"- {task}: unknown; no wrapper status yet; log `{item['log']}`; lock {lock_note}")
            continue
        if task == 'cron-health-report':
            status = {
                **status,
                'status': 'ok',
                'returncode': 0,
                'finished_at': ts.isoformat(),
                'duration_seconds': 0,
            }
        finished = status.get('finished_at') or ''
        rc = status.get('returncode')
        state = status.get('status', 'unknown')
        stale = False
        limit = freshness_limit(item['schedule'])
        if limit and finished:
            try:
                dt = datetime.fromisoformat(finished)
                stale = ts - dt > limit
            except ValueError:
                stale = True
        if task == 'cron-health-report':
            stale = False
        elif rc not in (0, None) or state == 'failed' or stale:
            problems.append((task, state, rc, finished, item['log'], 'stale' if stale else 'failed'))
        stale_text = '; stale' if stale else ''
        rows.append(f"- {task}: {state}, rc={rc}, last={finished or 'unknown'}, duration={status.get('duration_seconds', '?')}s{stale_text}; lock {lock_note}")

    lines = [
        '# Cron Health Report',
        '',
        f'Generated: {ts.isoformat()}',
        f'Tracked wrapper jobs: {len(tasks)}',
        f'Problems: {len(problems)}',
        '',
        '## Status',
        *rows,
        '',
        '## Problem Details',
    ]
    if problems:
        for task, state, rc, finished, log, why in problems:
            lines.append(f'- {task}: {why}; state={state}; rc={rc}; last={finished}; log `{log}`')
    else:
        lines.append('- None')
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    if problems:
        body = 'Cron health report found problems.\n' + '\n'.join(
            f'- {task}: {why}, rc={rc}, log={log}' for task, state, rc, finished, log, why in problems[:8]
        ) + f'\nReport: {REPORT}'
        try:
            send_alert(body)
        except Exception:
            pass
    print(f'Cron health report written: {REPORT} problems={len(problems)}')
    # Finding an unhealthy job is report data, not a failure of this reporting
    # job itself. The detailed alert above already carries the finding. Keep
    # the wrapper status green when the report was generated successfully so
    # it does not emit a second, misleading "cron-health-report failed" alert.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
