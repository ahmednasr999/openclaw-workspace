#!/usr/bin/env python3
"""Parse openclaw cron list --json output and extract failed crons."""
import json, sys

try:
    with open('/tmp/heartbeat_cron_raw.txt') as f:
        text = f.read()
    start = text.find('{')
    if start == -1:
        print('[]')
        sys.exit(0)
    # Find matching closing brace (skip trailing log metadata)
    depth = 0
    end = start
    for i in range(start, len(text)):
        if text[i] == '{': depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    data = json.loads(text[start:end])
    jobs = data.get('jobs', [])
    failed = []
    for j in jobs:
        if not isinstance(j, dict): continue
        state = j.get('state', {})
        last_status = state.get('lastStatus', state.get('lastRunStatus', ''))
        if last_status == 'error':
            failed.append({
                'id': j.get('id', ''),
                'name': j.get('name', ''),
                'error': state.get('lastError', 'unknown'),
                'last_run': state.get('lastRunAtMs', 0),
                'duration_ms': state.get('lastDurationMs', 0)
            })
    print(json.dumps(failed))
except Exception:
    print('[]')
