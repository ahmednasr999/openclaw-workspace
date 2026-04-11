#!/usr/bin/env python3
"""Model Guardian — checks model-router.json default and Codex provider health."""
import json
import subprocess
import sys
import time
from pathlib import Path

ALERTS = []


def parse_json_from_mixed_output(text: str):
    start = text.find('{')
    if start == -1:
        raise ValueError('no JSON object found in command output')
    return json.loads(text[start:])


def run_with_retries(args, timeouts, parser=None, ok_text=None, label='command'):
    last_error = None
    last_output = ''
    for i, timeout in enumerate(timeouts, start=1):
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            combined = ((result.stdout or '') + '\n' + (result.stderr or '')).strip()
            if parser:
                return parser(result.stdout or result.stderr or combined), combined, i, False
            if ok_text is None or ok_text in combined:
                return combined, combined, i, False
            last_error = f'unexpected output on attempt {i}'
            last_output = combined
        except subprocess.TimeoutExpired as e:
            stdout = (e.stdout or '') if isinstance(e.stdout, str) else (e.stdout.decode(errors='ignore') if e.stdout else '')
            stderr = (e.stderr or '') if isinstance(e.stderr, str) else (e.stderr.decode(errors='ignore') if e.stderr else '')
            combined = ((stdout or '') + '\n' + (stderr or '')).strip()
            if parser and combined:
                try:
                    return parser(combined), combined, i, True
                except Exception as parse_error:
                    last_error = f'timeout on attempt {i} with unusable output: {parse_error}'
            else:
                last_error = f'timed out after {timeout}s on attempt {i}'
            last_output = combined
        except Exception as e:
            last_error = f'attempt {i} failed: {e}'
        if i < len(timeouts):
            time.sleep(2)
    raise RuntimeError(last_error or f'{label} failed', last_output)


# 1. model-router.json default
try:
    with open('/root/.openclaw/workspace/config/model-router.json') as f:
        cfg = json.load(f)
    default = cfg.get('default_model', '')
    if default != 'openai-codex/gpt-5.4':
        ALERTS.append(f"model-router default is '{default}' — expected GPT-5.4")
    else:
        print('OK: model-router default is GPT-5.4')
except Exception as e:
    ALERTS.append(f'model-router.json read failed: {e}')


# 2. Codex provider health and quota visibility
status_data = None
status_probe_error = None
try:
    status_data, _, attempts, timed_out = run_with_retries(
        ['openclaw', 'status', '--usage', '--json'],
        timeouts=[30, 45],
        parser=parse_json_from_mixed_output,
        label='openclaw status usage probe',
    )
    if timed_out:
        print(f'OK: usage probe timed out but yielded parseable provider JSON on attempt {attempts}')
    elif attempts > 1:
        print(f'OK: usage probe succeeded on retry {attempts}')
except Exception as e:
    status_probe_error = str(e)

if not status_data and status_probe_error:
    ALERTS.append(f'openclaw status usage probe failed after retries: {status_probe_error}')

provider = None
if status_data:
    usage = status_data.get('usage', {})
    providers = usage.get('providers', []) if isinstance(usage, dict) else []
    provider = next((p for p in providers if p.get('provider') == 'openai-codex'), None)

    if not provider:
        ALERTS.append('openai-codex provider missing from usage status')
    else:
        if provider.get('error'):
            ALERTS.append(f"openai-codex provider error: {provider['error']}")
        else:
            windows = provider.get('windows') or []
            if windows:
                summary = ', '.join(
                    f"{w.get('label')}: {w.get('usedPercent')}% used"
                    for w in windows
                    if w.get('label')
                )
                print(f'OK: Codex usage visible — {summary}')
            else:
                print('OK: openai-codex provider present with no reported error')

# 3. Default model surface sanity check
try:
    _, combined, attempts, _ = run_with_retries(
        ['openclaw', 'models', 'status', '--plain'],
        timeouts=[20, 40],
        ok_text='openai-codex/gpt-5.4',
        label='models status probe',
    )
    if attempts > 1:
        print(f'OK: models status reports GPT-5.4 as configured default after retry {attempts}')
    else:
        print('OK: models status reports GPT-5.4 as configured default')
except Exception as e:
    ALERTS.append(f'models status probe failed after retries: {e}')

# 4. Optional evidence from recent usage snapshots
usage_file = Path('/root/.openclaw/workspace/data/model-guardian-usage.jsonl')
if usage_file.exists():
    try:
        lines = [l for l in usage_file.read_text().splitlines() if l.strip()]
        if lines:
            latest = json.loads(lines[-1])
            pct = latest.get('weeklyPercentLeft')
            if pct is not None:
                print(f'OK: latest guardian snapshot shows {pct}% weekly quota remaining')
    except Exception:
        pass

if ALERTS:
    print('FAIL: ' + '; '.join(ALERTS))
    sys.exit(1)
else:
    print('ALL_OK')
    sys.exit(0)
