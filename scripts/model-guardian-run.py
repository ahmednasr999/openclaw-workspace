#!/usr/bin/env python3
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

WORKSPACE = Path('/root/.openclaw/workspace')
CHECK_SCRIPT = WORKSPACE / 'scripts' / 'model-guardian-check.py'
USAGE_FILE = WORKSPACE / 'data' / 'model-guardian-usage.jsonl'
CAIRO = ZoneInfo('Africa/Cairo')


def parse_json_from_mixed_output(text: str):
    start = text.find('{')
    if start == -1:
        raise ValueError('no JSON object found in command output')
    return json.loads(text[start:])


def run_subprocess(args, timeout: int):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return result.returncode, (result.stdout or ''), (result.stderr or '')
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or '') if isinstance(e.stdout, str) else (e.stdout.decode(errors='ignore') if e.stdout else '')
        stderr = (e.stderr or '') if isinstance(e.stderr, str) else (e.stderr.decode(errors='ignore') if e.stderr else '')
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
    delta_days = max((now_ms - prev_ts) / 86400000, 1 / 24)
    daily_burn = (prev_left - current_left) / delta_days
    days_until_reset = max((reset_at_ms - now_ms) / 86400000, 0)
    projected = current_left - (daily_burn * days_until_reset)
    return round(daily_burn, 1), round(projected, 1)


def extract_codex_usage():
    rc, stdout, stderr = run_subprocess(['openclaw', 'status', '--usage', '--json'], timeout=40)
    mixed = stdout if stdout else stderr
    data = parse_json_from_mixed_output(mixed)
    usage = data.get('usage', {}) if isinstance(data, dict) else {}
    providers = usage.get('providers', []) if isinstance(usage, dict) else []
    provider = next((p for p in providers if p.get('provider') == 'openai-codex'), None)
    if not provider:
        raise RuntimeError('openai-codex provider missing from usage status')
    if provider.get('error'):
        raise RuntimeError(f"openai-codex provider error: {provider['error']}")
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
    stripped = text.strip()
    return stripped.splitlines()[-1] if stripped else 'unknown failure'


def main():
    dm_alerts = []
    ceo_alerts = []
    info = []

    rc, stdout, stderr = run_subprocess(['python3', str(CHECK_SCRIPT)], timeout=70)
    combined = '\n'.join(part for part in [stdout.strip(), stderr.strip()] if part).strip()
    if combined:
        info.extend(line for line in combined.splitlines() if line.strip())
    if rc != 0:
        dm_alerts.append(f"Model Guardian alert: {first_fail_reason(combined)}")

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
                f"🚨 Model Guardian urgent quota alert: weekly GPT-5.4 quota is below 15% remaining ({weekly_left}% left, reset in {time_left}). Estimated burn rate: {burn_text}. Think: high may not be sustainable on Pro at this rate. Recommendation: temporarily switch Think to medium until the window resets."
            )
        elif weekly_left < 30:
            ceo_alerts.append(
                f"⚠️ Model Guardian quota alert: weekly GPT-5.4 quota is below 30% remaining ({weekly_left}% left, reset in {time_left}). Estimated burn rate: {burn_text}. Think: high may be increasing burn rate. Review usage sustainability."
            )
    except Exception as e:
        dm_alerts.append(f'Model Guardian alert: usage snapshot failed - {e}')

    for line in info:
        print(f'INFO: {line}')
    for alert in dm_alerts:
        print(f'DM_ALERT: {alert}')
    for alert in ceo_alerts:
        print(f'CEO_ALERT: {alert}')
    if not dm_alerts and not ceo_alerts:
        print('NO_ALERTS')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'SCRIPT_ERROR: {e}')
        sys.exit(1)
