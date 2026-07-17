#!/usr/bin/env python3
"""Fetch Codex quota without invoking the heavyweight OpenClaw status command."""

import json
import os
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path


AUTH_FILE = Path(
    os.environ.get(
        'MODEL_GUARDIAN_CODEX_AUTH_FILE',
        '/root/.openclaw/agents/main/agent/codex-home/auth.json',
    )
)
USAGE_URL = 'https://chatgpt.com/backend-api/wham/usage'
OPENCLAW_VERSION = os.environ.get('OPENCLAW_VERSION', '2026.7.1')
TIMEOUT_SECONDS = min(max(float(os.environ.get('MODEL_GUARDIAN_USAGE_TIMEOUT', '10')), 1), 30)
WEEKLY_RESET_GAP_SECONDS = 4320 * 60


def clamp_percent(value):
    try:
        return max(0, min(100, float(value)))
    except (TypeError, ValueError):
        return 0


def window_snapshot(window, label=None):
    window_seconds = int(window.get('limit_window_seconds') or 10800)
    hours = round(window_seconds / 3600)
    reset_at = window.get('reset_at')
    return {
        'label': label or f'{hours}h',
        'usedPercent': clamp_percent(window.get('used_percent') or 0),
        'resetAt': int(reset_at) * 1000 if reset_at else None,
    }


def secondary_window_label(primary, secondary):
    hours = round(int(secondary.get('limit_window_seconds') or 86400) / 3600)
    if hours >= 168:
        return 'Week'
    if hours < 24:
        return f'{hours}h'
    primary_reset = primary.get('reset_at') if primary else None
    secondary_reset = secondary.get('reset_at')
    if (
        isinstance(primary_reset, (int, float))
        and isinstance(secondary_reset, (int, float))
        and secondary_reset - primary_reset >= WEEKLY_RESET_GAP_SECONDS
    ):
        return 'Week'
    return 'Day'


def normalize_usage(data):
    rate_limit = data.get('rate_limit') or {}
    primary = rate_limit.get('primary_window')
    secondary = rate_limit.get('secondary_window')
    windows = []
    if isinstance(primary, dict):
        windows.append(window_snapshot(primary))
    if isinstance(secondary, dict):
        windows.append(window_snapshot(secondary, secondary_window_label(primary, secondary)))

    snapshot = {
        'provider': 'openai',
        'displayName': 'OpenAI',
        'windows': windows,
        'plan': data.get('plan_type'),
    }
    balance = (data.get('credits') or {}).get('balance')
    if balance is not None:
        try:
            amount = float(balance)
        except (TypeError, ValueError):
            amount = None
        if amount is not None and amount >= 0:
            snapshot['billing'] = [{'type': 'balance', 'amount': amount, 'unit': 'credits'}]
    return snapshot


def error_snapshot(message):
    return {
        'provider': 'openai',
        'displayName': 'OpenAI',
        'windows': [],
        'error': message,
    }


def load_credentials():
    data = json.loads(AUTH_FILE.read_text())
    tokens = data.get('tokens') or {}
    token = tokens.get('access_token')
    account_id = tokens.get('account_id')
    if not token:
        raise RuntimeError('Codex OAuth access token missing')
    return token, account_id


def fetch_usage():
    token, account_id = load_credentials()
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'originator': 'openclaw',
        'User-Agent': f'openclaw/{OPENCLAW_VERSION}',
    }
    if account_id:
        headers['ChatGPT-Account-Id'] = account_id
    request = urllib.request.Request(USAGE_URL, headers=headers, method='GET')
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return normalize_usage(json.load(response))


def main():
    try:
        snapshot = fetch_usage()
    except urllib.error.HTTPError as error:
        message = 'OAuth token expired' if error.code in {401, 403} else f'HTTP {error.code}'
        snapshot = error_snapshot(message)
    except (TimeoutError, socket.timeout, urllib.error.URLError) as error:
        print(f'TRANSIENT: Codex quota request failed: {error}', file=sys.stderr)
        return 75
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as error:
        snapshot = error_snapshot(str(error))

    print(json.dumps(snapshot, separators=(',', ':')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
