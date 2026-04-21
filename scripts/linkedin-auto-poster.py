#!/usr/bin/env python3
"""
LinkedIn Auto-Poster orchestrator.

Default mode:
- resolve today's publish candidate from Notion
- prepare the exact posting payload
- mark the row Publishing
- write /tmp/linkedin-post-payload.json
- print READY_TO_POST for the caller/agent

Compatibility modes:
- --start-publishing
- --update-url
- --dry-run
"""

import base64
import json
import mimetypes
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

WORKSPACE = Path('/root/.openclaw/workspace')
CMO_WORKSPACE = Path('/root/.openclaw/workspace-cmo')
CMO_SCRIPTS = CMO_WORKSPACE / 'scripts'
PREFLIGHT = CMO_SCRIPTS / 'linkedin-preflight.py'
START_PUBLISH = CMO_SCRIPTS / 'start-publish-attempt.py'
WRITEBACK = CMO_SCRIPTS / 'register-published-post.py'
FAILURE = CMO_SCRIPTS / 'report-publish-failure.py'
PAYLOAD_PATH = Path('/tmp/linkedin-post-payload.json')
PERSON_URN = 'urn:li:person:mm8EyA56mj'

sys.path.insert(0, str(CMO_SCRIPTS))
from cmo_notion_posting import mark_publishing, resolve_publish_candidate  # noqa: E402


def today_cairo():
    return datetime.now(ZoneInfo('Africa/Cairo')).date().isoformat()


def to_unicode_bold(text):
    result = []
    for ch in text:
        if 'A' <= ch <= 'Z':
            result.append(chr(0x1D5D4 + ord(ch) - ord('A')))
        elif 'a' <= ch <= 'z':
            result.append(chr(0x1D5EE + ord(ch) - ord('a')))
        elif '0' <= ch <= '9':
            result.append(chr(0x1D7EC + ord(ch) - ord('0')))
        else:
            result.append(ch)
    return ''.join(result)


def convert_bold_markdown(text):
    import re
    return re.sub(r'\*\*(.+?)\*\*', lambda m: to_unicode_bold(m.group(1)), text or '')


def run_script(script_path: Path, args: list[str]):
    return subprocess.run([sys.executable, str(script_path), *args])


def read_arg(argv, flag, default=None):
    if flag in argv:
        idx = argv.index(flag)
        if idx + 1 < len(argv):
            return argv[idx + 1]
    return default


def payload_from_record(record: dict):
    content = convert_bold_markdown(record['content'])
    asset = record.get('asset') or {}
    asset_value = asset.get('value')
    payload = {
        'action': 'post_to_linkedin',
        'author': PERSON_URN,
        'visibility': 'PUBLIC',
        'page_id': record['page_id'],
        'title': record['title'],
        'planned_date': record['planned_date'],
        'content': content,
        'content_length': len(content),
        'image_required': bool(asset_value),
        'asset_source': asset.get('source') or 'none',
        'asset_name': asset.get('name') or '',
    }

    if not asset_value:
        return payload

    if isinstance(asset_value, str) and asset_value.startswith(('http://', 'https://')):
        payload['image_url'] = asset_value
        payload['image_mimetype'] = mimetypes.guess_type(asset.get('name') or asset_value)[0] or 'image/png'
        payload['image_name'] = asset.get('name') or 'image.png'
        return payload

    path = Path(asset_value)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f'Asset path does not exist: {asset_value}')

    payload['image_name'] = path.name
    payload['image_mimetype'] = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    payload['image_base64'] = base64.b64encode(path.read_bytes()).decode('ascii')
    payload['image_size_bytes'] = path.stat().st_size
    return payload


def log_preflight_failure(target_date: str, message: str, dry_run: bool):
    if dry_run:
        return
    run_script(FAILURE, ['--date', target_date, '--step', 'preflight', '--error', message, '--no-telegram'])


def main():
    argv = sys.argv[1:]
    dry_run = '--dry-run' in argv

    if '--start-publishing' in argv:
        args = []
        if '--page-id' in argv:
            args += ['--page-id', read_arg(argv, '--page-id')]
        elif '--date' in argv:
            args += ['--date', read_arg(argv, '--date')]
        else:
            args += ['--date', today_cairo()]
        if dry_run:
            args.append('--dry-run')
        raise SystemExit(run_script(START_PUBLISH, args).returncode)

    if '--update-url' in argv:
        post_url = read_arg(argv, '--update-url')
        if not post_url:
            print('ERROR: --update-url requires a value')
            raise SystemExit(2)
        args = ['--post-url', post_url]
        if '--page-id' in argv:
            args += ['--page-id', read_arg(argv, '--page-id')]
        elif '--date' in argv:
            args += ['--date', read_arg(argv, '--date')]
        else:
            args += ['--date', today_cairo()]
        if dry_run:
            args.append('--dry-run')
        raise SystemExit(run_script(WRITEBACK, args).returncode)

    target_date = read_arg(argv, '--date', today_cairo())
    result = resolve_publish_candidate(target_date)

    if not result.get('ok'):
        kind = result.get('kind')
        message = result.get('message', 'Preflight failed.')
        if kind in {'no_rows', 'no_approved_or_scheduled'}:
            print(f'No scheduled post for {target_date}')
            return 0
        if kind == 'already_posted':
            print('ALREADY_POSTED')
            return 0
        log_preflight_failure(target_date, message, dry_run=dry_run)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print('PRECHECK_FAILED')
        return 1

    record = result['record']

    try:
        payload = payload_from_record(record)
    except Exception as exc:
        log_preflight_failure(target_date, f'Payload preparation failed: {exc}', dry_run=dry_run)
        print(f'ERROR: Payload preparation failed: {exc}')
        return 1

    patch = mark_publishing(record, dry_run=dry_run)
    PAYLOAD_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    print(json.dumps({
        'date': target_date,
        'dry_run': dry_run,
        'record': {
            'page_id': record['page_id'],
            'title': record['title'],
            'status': record['status'],
            'planned_date': record['planned_date'],
            'asset': record.get('asset'),
        },
        'patch': patch,
        'payload_preview': {
            'action': payload['action'],
            'author': payload['author'],
            'page_id': payload['page_id'],
            'image_required': payload['image_required'],
            'asset_source': payload['asset_source'],
            'content_length': payload['content_length'],
        },
        'payload_path': str(PAYLOAD_PATH),
    }, indent=2, ensure_ascii=False))
    print('READY_TO_POST')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
