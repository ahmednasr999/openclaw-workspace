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


# Legacy deterministic scoring contract kept for NASR Doctor regression tests.
# Runtime publish readiness is resolved from Notion annotations only.
SCORED_QUESTIONS = [
    ("SCROLL_STOPPER", "Opening line earns the scroll stop", 1, True),
    ("CLEAR_POINT", "Post has one clear point", 1, False),
    ("AUDIENCE_FIT", "Audience is Ahmed's executive network", 1, False),
    ("METRIC", "Includes a concrete metric or outcome", 2, False),
    ("SPECIFICITY", "Avoids generic advice", 1, False),
    ("VOICE", "Matches Ahmed's voice", 1, False),
    ("STRUCTURE", "Readable structure", 1, False),
    ("NOT_PRESS_RELEASE", "Does not sound like a press release", 2, False),
    ("CONTEXT_RICH", "Adds useful context", 2, False),
    ("CTA", "Ends with a question or CTA", 1, True),
]

WATCHDOG_PATH = WORKSPACE / 'data' / 'linkedin-watchdog.json'
# Notion annotations are the single source of truth for rich text formatting.

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
        'image_staging_required': bool(asset_value),
        'image_staging_status': 'not_required' if not asset_value else 'required',
        'image_staging_rule': 'If image_required is true, stage the image through COMPOSIO_REMOTE_WORKBENCH upload_local_file() first and pass only the returned s3key to LINKEDIN_CREATE_LINKED_IN_POST. Never pass a raw URL or local path as s3key.',
    }

    if not asset_value:
        return payload

    if isinstance(asset_value, str) and asset_value.startswith(('http://', 'https://')):
        payload['image_url'] = asset_value
        payload['image_source_kind'] = 'public_url'
        payload['image_mimetype'] = mimetypes.guess_type(asset.get('name') or asset_value)[0] or 'image/png'
        payload['image_name'] = asset.get('name') or Path(asset_value.split('?')[0]).name or 'image.png'
        payload['image_s3key'] = None
        payload['image_s3key_required'] = True
        return payload

    path = Path(asset_value)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f'Asset path does not exist: {asset_value}')

    # Local files are not visible to the Composio workbench. The cron agent must
    # transfer the bytes into the workbench, then call upload_local_file() there.
    payload['image_name'] = path.name
    payload['image_source_kind'] = 'local_path'
    payload['image_mimetype'] = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    payload['image_local_path'] = str(path.resolve())
    payload['image_size_bytes'] = path.stat().st_size
    payload['image_s3key'] = None
    payload['image_s3key_required'] = True
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
