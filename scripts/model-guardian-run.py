#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

WORKSPACE = Path('/root/.openclaw/workspace')
CHECK_SCRIPT = WORKSPACE / 'scripts' / 'model-guardian-check.py'
USAGE_FILE = WORKSPACE / 'data' / 'model-guardian-usage.jsonl'
STATE_FILE = WORKSPACE / 'data' / 'model-guardian-state.json'
STATUS_CACHE = WORKSPACE / 'data' / 'model-guardian-status-cache.json'
CAIRO = ZoneInfo('Africa/Cairo')
AHMED_DM_TARGET = '866838380'
CEO_GENERAL_TARGET = '-1003882622947:10'
TRANSIENT_FAILURE_THRESHOLD = 2
CHECK_TIMEOUT_SECONDS = 140
STATUS_PROBE_TIMEOUT_SECONDS = 30
CODEX_USAGE_PROVIDERS = {'openai', 'openai-codex'}

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


def send_telegram(target: str, text: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ['openclaw', 'message', 'send', '--channel', 'telegram', '--target', target, '--message', text],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = ((result.stdout or '') + '\n' + (result.stderr or '')).strip()
        if result.returncode == 0:
            return True, output
        return False, output or f'exit code {result.returncode}'
    except subprocess.TimeoutExpired:
        return False, 'timeout after 60s'
    except Exception as e:
        return False, str(e)


def parse_json_from_mixed_output(text: str):
    start = text.find('{')
    if start == -1:
        raise ValueError('no JSON object found in command output')
    return json.loads(text[start:])


def load_state():
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True) + '\n')


def reset_transient_failures(state: dict):
    if state.get('consecutiveTransientProbeFailures'):
        state['consecutiveTransientProbeFailures'] = 0
        save_state(state)


def is_transient_probe_failure(text: str):
    lower = text.lower()
    if 'model-router default is' in lower:
        return False
    is_abort = 'operation was aborted' in lower or 'this operation was aborted' in lower
    if ('provider error' in lower and not is_abort) or 'provider missing' in lower:
        return False
    if 'config invalid' in lower or 'problem:' in lower:
        return False
    if is_abort or 'timed out' in lower or 'timeout:' in lower:
        return True
    return False


def run_subprocess(args, timeout: int, env=None):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, env=env)
        return result.returncode, (result.stdout or ''), (result.stderr or '')
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or '') if isinstance(e.stdout, str) else (e.stdout.decode(errors='ignore') if e.stdout else '')
        stderr = (e.stderr or '') if isinstance(e.stderr, str) else (e.stderr.decode(errors='ignore') if e.stderr else '')
        command = ' '.join(str(arg) for arg in args)
        timeout_note = f'TIMEOUT: {command} exceeded {timeout}s'
        stderr = '\n'.join(part for part in [stderr.strip(), timeout_note] if part)
        return 124, stdout, stderr


def format_remaining(ms_until_reset: int):
    if ms_until_reset <= 0:
        return 'reset due'
    total_minutes = ms_until_reset // 60000
    days, rem_minutes = divmod(total_minutes, 60 * 24)
    hours, minutes = divmod(rem_minutes, 60)
    if days > 0:
        return f'{days}d {hours}h'
    if hours > 0:
        return f'{hours}h {minutes}m'
    return f'{minutes}m'


def append_snapshot(snapshot: dict):
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with USAGE_FILE.open('a') as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + '\n')


def load_previous_snapshots():
    if not USAGE_FILE.exists():
        return []
    rows = []
    for line in USAGE_FILE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def estimate_burn(previous_rows, current_left, now_ms, reset_at_ms):
    candidates = []
    for row in previous_rows:
        pct = row.get('weeklyPercentLeft')
        ts = row.get('timestampMs')
        if pct is None or ts is None or ts >= now_ms:
            continue
        age_hours = (now_ms - ts) / 3600000
        candidates.append((abs(age_hours - 24), age_hours, pct, ts))
    if not candidates:
        return None, None

    preferred = [c for c in candidates if 18 <= c[1] <= 30]
    chosen = min(preferred or candidates, key=lambda x: x[0])
    _, age_hours, prev_left, prev_ts = chosen
    if prev_left <= current_left:
        return None, None
    delta_days = max((now_ms - prev_ts) / 86400000, 1 / 24)
    daily_burn = (prev_left - current_left) / delta_days
    days_until_reset = max((reset_at_ms - now_ms) / 86400000, 0)
    projected = max(0, current_left - (daily_burn * days_until_reset))
    return round(daily_burn, 1), round(projected, 1)


def extract_codex_usage():
    if STATUS_CACHE.exists():
        data = json.loads(STATUS_CACHE.read_text())
    else:
        rc, stdout, stderr = run_subprocess(['openclaw', 'status', '--usage', '--json'], timeout=STATUS_PROBE_TIMEOUT_SECONDS)
        mixed = stdout if stdout else stderr
        if rc != 0 and not mixed.strip():
            raise RuntimeError(f'openclaw status usage exited {rc} with no output')
        data = parse_json_from_mixed_output(mixed)
    usage = data.get('usage', {}) if isinstance(data, dict) else {}
    providers = usage.get('providers', []) if isinstance(usage, dict) else []
    provider = next((p for p in providers if p.get('provider') in CODEX_USAGE_PROVIDERS), None)
    if not provider:
        raise RuntimeError('Codex usage provider missing from usage status')
    if provider.get('error'):
        raise RuntimeError(f"Codex usage provider error: {provider['error']}")
    windows = provider.get('windows') or []
    week = next((w for w in windows if str(w.get('label', '')).lower() == 'week'), None)
    if not week:
        raise RuntimeError('weekly Codex quota window missing from usage status')
    used = week.get('usedPercent')
    reset_at = week.get('resetAt')
    if used is None or reset_at is None:
        raise RuntimeError('weekly Codex quota window missing usedPercent/resetAt')
    left = max(0, 100 - float(used))
    return left, int(reset_at)


def first_fail_reason(text: str):
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('FAIL:'):
            return line
        if line.startswith('TIMEOUT:'):
            return line
    stripped = text.strip()
    return stripped.splitlines()[-1] if stripped else 'unknown failure'


def main():
    dm_alerts = []
    ceo_alerts = []
    info = []
    state = load_state()
    transient_probe_failure = False

    try:
        STATUS_CACHE.unlink()
    except FileNotFoundError:
        pass

    check_env = dict(os.environ)
    check_env['MODEL_GUARDIAN_STATUS_CACHE'] = str(STATUS_CACHE)
    rc, stdout, stderr = run_subprocess(['python3', str(CHECK_SCRIPT)], timeout=CHECK_TIMEOUT_SECONDS, env=check_env)
    combined = '\n'.join(part for part in [stdout.strip(), stderr.strip()] if part).strip()
    if combined:
        info.extend(line for line in combined.splitlines() if line.strip())
    if rc != 0:
        reason = first_fail_reason(combined)
        if is_transient_probe_failure(reason):
            transient_probe_failure = True
            count = int(state.get('consecutiveTransientProbeFailures') or 0) + 1
            state['consecutiveTransientProbeFailures'] = count
            save_state(state)
            info.append(f'TRANSIENT_SUPPRESSED: probe transient count {count}: {reason}')
        else:
            dm_alerts.append(f"Model Guardian alert: {reason}")

    now_utc = datetime.now(timezone.utc)
    now_cairo = now_utc.astimezone(CAIRO)
    now_ms = int(now_utc.timestamp() * 1000)

    try:
        weekly_left, reset_at_ms = extract_codex_usage()
        weekly_left = round(weekly_left, 1)
        time_left = format_remaining(reset_at_ms - now_ms)
        prev_rows = load_previous_snapshots()
        daily_burn, projected = estimate_burn(prev_rows, weekly_left, now_ms, reset_at_ms)
        snapshot = {
            'timestampMs': now_ms,
            'timestampUtc': now_utc.isoformat(),
            'timestampCairo': now_cairo.isoformat(),
            'weeklyPercentLeft': weekly_left,
            'weeklyTimeLeft': time_left,
            'thinkModeExpected': 'high',
            'source': 'model-guardian-cron',
            'dailyBurnPercent': daily_burn,
            'projectedPercentAtReset': projected,
        }
        append_snapshot(snapshot)
        info.append(f'SNAPSHOT: weekly={weekly_left}% left, reset in {time_left}')

        burn_text = f'{daily_burn}% per day' if daily_burn is not None else 'n/a'
        if weekly_left < 15:
            ceo_alerts.append(
                f"🚨 Model Guardian urgent quota alert: weekly GPT-5.5 quota is below 15% remaining ({weekly_left}% left, reset in {time_left}). Estimated burn rate: {burn_text}. Think: high may not be sustainable on Pro at this rate. Recommendation: temporarily switch Think to medium until the window resets."
            )
        elif weekly_left < 30:
            ceo_alerts.append(
                f"⚠️ Model Guardian quota alert: weekly GPT-5.5 quota is below 30% remaining ({weekly_left}% left, reset in {time_left}). Estimated burn rate: {burn_text}. Think: high may be increasing burn rate. Review usage sustainability."
            )
    except Exception as e:
        reason = f'usage snapshot failed - {e}'
        if is_transient_probe_failure(reason):
            if transient_probe_failure:
                info.append(f'TRANSIENT_SUPPRESSED: usage snapshot skipped after check probe failure: {reason}')
            else:
                transient_probe_failure = True
                count = int(state.get('consecutiveTransientProbeFailures') or 0) + 1
                state['consecutiveTransientProbeFailures'] = count
                save_state(state)
                info.append(f'TRANSIENT_SUPPRESSED: usage transient count {count}: {reason}')
        else:
            dm_alerts.append(f'Model Guardian alert: {reason}')

    if not transient_probe_failure and not dm_alerts:
        reset_transient_failures(state)

    delivery_failures = []

    for line in info:
        print(f'INFO: {line}')
    for alert in dm_alerts:
        print(f'DM_ALERT: {alert}')
        ok, detail = send_telegram(AHMED_DM_TARGET, alert)
        print(f'INFO: DM delivery {"OK" if ok else "FAILED"}: {detail}')
        if not ok:
            delivery_failures.append(f'DM delivery failed: {detail}')
    for alert in ceo_alerts:
        print(f'CEO_ALERT: {alert}')
        ok, detail = send_telegram(CEO_GENERAL_TARGET, alert)
        print(f'INFO: CEO delivery {"OK" if ok else "FAILED"}: {detail}')
        if not ok:
            delivery_failures.append(f'CEO delivery failed: {detail}')
    if delivery_failures:
        print('WARN: ' + '; '.join(delivery_failures))
    if not dm_alerts and not ceo_alerts:
        print('NO_ALERTS')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'SCRIPT_ERROR: {e}')
        sys.exit(1)
