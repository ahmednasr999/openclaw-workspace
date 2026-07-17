#!/usr/bin/env python3
"""Watch official GPT-5.6 availability signals and alert Ahmed once."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

WORKSPACE = Path('/root/.openclaw/workspace')
STATE_FILE = WORKSPACE / 'data' / 'gpt56-availability-watch-state.json'
LOG_FILE = WORKSPACE / 'data' / 'gpt56-availability-watch.jsonl'
LATEST_MODEL_URL = 'https://developers.openai.com/api/docs/guides/latest-model.md'
TARGET = '866838380'
CAIRO = ZoneInfo('Africa/Cairo')


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone(CAIRO).isoformat()


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True) + '\n')


def append_log(record: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open('a') as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n')


def fetch_text(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'OpenClaw GPT-5.6 availability watcher',
            'Accept': 'text/markdown,text/plain,text/html,*/*',
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
        encoding = response.headers.get_content_charset() or 'utf-8'
        return raw.decode(encoding, errors='replace')


def parse_latest_model(markdown: str) -> str:
    match = re.search(r'latestModelInfo:\s*\n\s*model:\s*([^\s]+)', markdown)
    if match:
        return match.group(1).strip().strip('`')
    match = re.search(r'^\s*model:\s*([^\s]+)', markdown, flags=re.MULTILINE)
    return match.group(1).strip().strip('`') if match else ''


def run(args: list[str], timeout: int = 30) -> tuple[int, str]:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return result.returncode, ((result.stdout or '') + '\n' + (result.stderr or '')).strip()
    except subprocess.TimeoutExpired:
        return 124, f'timeout after {timeout}s'
    except Exception as e:
        return 1, str(e)


def runtime_status() -> dict:
    status = {'currentModel': '', 'catalogMatches': []}

    rc, output = run(['openclaw', 'models', 'status', '--plain'], timeout=35)
    if rc == 0:
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        status['currentModel'] = lines[-1] if lines else ''
    else:
        status['currentModelError'] = output

    rc, output = run(['openclaw', 'models', 'list', '--all', '--json'], timeout=45)
    if rc == 0:
        try:
            start = output.find('{')
            payload = json.loads(output[start:]) if start >= 0 else {}
            matches = []
            for model in payload.get('models', []):
                key = str(model.get('key', ''))
                name = str(model.get('name', ''))
                if 'gpt-5.6' in key.lower() or 'gpt-5.6' in name.lower():
                    matches.append({
                        'key': key,
                        'name': name,
                        'available': bool(model.get('available')),
                        'tags': model.get('tags', []),
                    })
            status['catalogMatches'] = matches
        except Exception as e:
            status['catalogError'] = f'parse failed: {e}'
    else:
        status['catalogError'] = output

    return status


def send_telegram(text: str) -> tuple[bool, str]:
    rc, output = run(
        ['openclaw', 'message', 'send', '--channel', 'telegram', '--target', TARGET, '--message', text],
        timeout=60,
    )
    return rc == 0, output


def evaluate(latest_model: str, status: dict) -> tuple[bool, list[str]]:
    reasons = []
    if latest_model.lower().startswith('gpt-5.6'):
        reasons.append(f'official latest-model docs now point to `{latest_model}`')

    current_model = str(status.get('currentModel') or '')
    if 'gpt-5.6' in current_model.lower():
        reasons.append(f'OpenClaw runtime model status reports `{current_model}`')

    available_matches = [
        m for m in status.get('catalogMatches', [])
        if m.get('available') and 'gpt-5.6' in (m.get('key', '') + ' ' + m.get('name', '')).lower()
    ]
    if available_matches:
        keys = ', '.join(sorted(m['key'] for m in available_matches if m.get('key')))
        reasons.append(f'OpenClaw model catalog marks GPT-5.6 available: `{keys}`')

    return bool(reasons), reasons


def build_alert(latest_model: str, status: dict, reasons: list[str]) -> str:
    current = status.get('currentModel') or 'unknown'
    reason_text = '; '.join(reasons)
    return (
        'GPT-5.6 availability update\n\n'
        f'{reason_text}.\n\n'
        f'Official latest-model doc: `{latest_model or "unknown"}`\n'
        f'Current OpenClaw runtime: `{current}`\n\n'
        'I will treat this as the signal to verify whether we should switch OpenClaw from GPT-5.5.'
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--force-alert', action='store_true')
    args = parser.parse_args()

    state = load_state()
    record = {'checkedAt': now_iso(), 'source': 'gpt56-availability-watch'}

    try:
        latest_doc = fetch_text(LATEST_MODEL_URL)
        latest_model = parse_latest_model(latest_doc)
        record['latestModelDocModel'] = latest_model
    except urllib.error.URLError as e:
        record['error'] = f'latest-model fetch failed: {e}'
        append_log(record)
        print(record['error'])
        return 1
    except Exception as e:
        record['error'] = f'latest-model probe failed: {e}'
        append_log(record)
        print(record['error'])
        return 1

    status = runtime_status()
    record['runtime'] = status
    available, reasons = evaluate(latest_model, status)
    record['availableSignal'] = available
    record['reasons'] = reasons

    already_alerted = bool(state.get('alerted'))
    should_alert = (available and not already_alerted) or args.force_alert

    if should_alert:
        alert = build_alert(latest_model, status, reasons or ['manual forced alert'])
        record['alertText'] = alert
        if args.dry_run:
            record['delivery'] = 'dry-run'
            print(alert)
        else:
            ok, detail = send_telegram(alert)
            record['delivery'] = 'ok' if ok else 'failed'
            record['deliveryDetail'] = detail
            if not ok:
                append_log(record)
                print(f'alert delivery failed: {detail}')
                return 1
            state.update({'alerted': True, 'alertedAt': now_iso(), 'alertReason': reasons})
            save_state(state)
            print('ALERT_SENT')
    else:
        state.update({
            'lastCheckedAt': now_iso(),
            'lastLatestModelDocModel': latest_model,
            'lastRuntimeModel': status.get('currentModel') or '',
            'lastAvailableSignal': available,
        })
        save_state(state)
        print('NO_ALERT')

    append_log(record)
    return 0


if __name__ == '__main__':
    sys.exit(main())
