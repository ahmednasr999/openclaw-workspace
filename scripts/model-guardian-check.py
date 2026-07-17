#!/usr/bin/env python3
"""Model Guardian — checks model-router.json default and Codex provider health."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ALERTS = []

HOOKS_ENV_FILE = Path('/root/.config/openclaw-hooks.env')


def load_env_file(path: Path):
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('\"').strip("'")
        if key:
            os.environ.setdefault(key, value)


load_env_file(HOOKS_ENV_FILE)

WORKSPACE = Path('/root/.openclaw/workspace')
USAGE_PROBE_SCRIPT = WORKSPACE / 'scripts' / 'model-guardian-usage-probe.py'
OPENCLAW_CONFIG_FILE = Path('/root/.openclaw/openclaw.json')


def parse_json_from_mixed_output(text: str):
    start = text.find('{')
    if start == -1:
        raise ValueError('no JSON object found in command output')
    return json.loads(text[start:])


def is_transient_provider_error(text: str) -> bool:
    lower = str(text).lower()
    return (
        'operation was aborted' in lower
        or 'this operation was aborted' in lower
        or 'transient:' in lower
    )


def run_with_retries(args, timeouts, parser=None, ok_text=None, label='command'):
    last_error = None
    last_output = ''
    for i, timeout in enumerate(timeouts, start=1):
        combined = ''
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
            if combined:
                last_output = combined
        if i < len(timeouts):
            time.sleep(2)
    detail = ': '.join(part for part in [last_error or f'{label} failed', last_output] if part)
    raise RuntimeError(detail)


EXPECTED_DEFAULT_MODEL = 'openai/gpt-5.6-sol'
EXPECTED_DEFAULT_LABEL = 'GPT-5.6 Sol'
EXPECTED_DEFAULT_MODELS = {EXPECTED_DEFAULT_MODEL}
EXPECTED_STATUS_MODELS = EXPECTED_DEFAULT_MODELS
CODEX_USAGE_PROVIDERS = {'openai', 'openai-codex'}

# 1. model-router.json default
try:
    with open('/root/.openclaw/workspace/config/model-router.json') as f:
        cfg = json.load(f)
    default = cfg.get('default_model', '')
    if default not in EXPECTED_DEFAULT_MODELS:
        ALERTS.append(f"model-router default is '{default}' — expected {EXPECTED_DEFAULT_LABEL}")
    else:
        print(f'OK: model-router default is {EXPECTED_DEFAULT_LABEL}')
except Exception as e:
    ALERTS.append(f'model-router.json read failed: {e}')


# 2. Codex provider health and quota visibility. This quota-only probe avoids
# `openclaw status --usage`, which scans the wider runtime and can exceed 2 GB.
status_data = None
status_probe_error = None
try:
    provider_snapshot, _, attempts, timed_out = run_with_retries(
        ['/usr/bin/python3', str(USAGE_PROBE_SCRIPT)],
        timeouts=[12, 20],
        parser=parse_json_from_mixed_output,
        label='Codex quota-only probe',
    )
    status_data = {'usage': {'providers': [provider_snapshot]}}
    if timed_out:
        print(f'OK: quota-only probe timed out but yielded parseable provider JSON on attempt {attempts}')
    elif attempts > 1:
        print(f'OK: quota-only probe succeeded on retry {attempts}')
    cache_path = os.environ.get('MODEL_GUARDIAN_STATUS_CACHE')
    if cache_path:
        Path(cache_path).write_text(json.dumps(status_data) + '\n')
except Exception as e:
    status_probe_error = str(e)

if not status_data and status_probe_error:
    ALERTS.append(f'Codex quota-only probe failed after retries: {status_probe_error}')

provider = None
if status_data:
    usage = status_data.get('usage', {})
    providers = usage.get('providers', []) if isinstance(usage, dict) else []
    provider = next((p for p in providers if p.get('provider') in CODEX_USAGE_PROVIDERS), None)

    if not provider:
        ALERTS.append('Codex usage provider missing from usage status')
    else:
        if provider.get('error'):
            if is_transient_provider_error(provider.get('error')):
                print(f"OK: Codex usage provider returned transient probe abort: {provider['error']}")
            else:
                ALERTS.append(f"Codex usage provider error: {provider['error']}")
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
                print('OK: Codex usage provider present with no reported error')

# 3. Default model surface sanity check without loading the full OpenClaw CLI.
try:
    runtime_cfg = json.loads(OPENCLAW_CONFIG_FILE.read_text())
    agents_cfg = runtime_cfg.get('agents') or {}
    defaults = agents_cfg.get('defaults') or {}
    model_cfg = defaults.get('model') or {}
    reported_model = model_cfg.get('primary') if isinstance(model_cfg, dict) else model_cfg
    if reported_model not in EXPECTED_STATUS_MODELS:
        raise RuntimeError(f'unexpected OpenClaw default model {reported_model!r}')
    main_agent = next(
        (entry for entry in (agents_cfg.get('list') or []) if entry.get('id') == 'main'),
        {},
    )
    main_override = main_agent.get('model')
    if main_override and main_override not in EXPECTED_STATUS_MODELS:
        raise RuntimeError(f'unexpected main-agent model override {main_override!r}')
    configured_models = defaults.get('models') or {}
    expected_entry = configured_models.get(EXPECTED_DEFAULT_MODEL) or {}
    runtime_id = (expected_entry.get('agentRuntime') or {}).get('id')
    if runtime_id != 'codex':
        raise RuntimeError(f'{EXPECTED_DEFAULT_LABEL} agentRuntime is {runtime_id!r}, expected codex')
    print(f'OK: OpenClaw config reports {EXPECTED_DEFAULT_LABEL} as the Codex default')
except Exception as e:
    ALERTS.append(f'OpenClaw default-model config check failed: {e}')

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
