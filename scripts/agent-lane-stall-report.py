#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path('/root/.openclaw/workspace')
AGENTS_DIR = Path('/root/.openclaw/agents')
CAIRO = ZoneInfo('Africa/Cairo')
DEFAULT_AGENTS = ('cmo', 'hr')
DEFAULT_RECOVERY_LOG = ROOT / 'reports' / 'agent-lane-recoveries.jsonl'


@dataclass
class Finding:
    severity: str
    agent: str
    kind: str
    key: str
    status: str
    age_minutes: float
    detail: str
    next_action: str


def now_ms() -> int:
    return int(time.time() * 1000)


def fmt_age(minutes: float) -> str:
    if minutes >= 1440:
        return f'{minutes / 1440:.1f}d'
    if minutes >= 60:
        return f'{minutes / 60:.1f}h'
    return f'{minutes:.0f}m'


def load_sessions(agent: str) -> dict:
    path = AGENTS_DIR / agent / 'sessions' / 'sessions.json'
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        return {
            f'agent:{agent}:sessions-json-error': {
                'status': 'error',
                'updatedAt': now_ms(),
                'label': str(exc),
            }
        }


def rec_time(rec: dict) -> int:
    return int(rec.get('updatedAt') or rec.get('endedAt') or rec.get('startedAt') or 0)


def rec_duration_minutes(rec: dict) -> float | None:
    started = rec.get('startedAt')
    ended = rec.get('endedAt')
    if not started or not ended:
        return None
    return max(0.0, (int(ended) - int(started)) / 60000)


def display_label(key: str, rec: dict) -> str:
    return str(rec.get('label') or rec.get('displayName') or key)


def load_recoveries(path: str | Path | None) -> set[tuple[str, str]]:
    if not path:
        return set()
    recovery_path = Path(path)
    if not recovery_path.exists():
        return set()

    recovered: set[tuple[str, str]] = set()
    for line in recovery_path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get('status') not in {'recovered', 'resolved', 'closed'}:
            continue
        key = item.get('sessionKey') or item.get('key')
        kind = item.get('kind') or '*'
        if key:
            recovered.add((str(key), str(kind)))
    return recovered


def is_recovered(recovered: set[tuple[str, str]], key: str, kind: str) -> bool:
    return (key, kind) in recovered or (key, '*') in recovered


def scan(agents: list[str], min_running_minutes: int, recent_hours: int, recovered: set[tuple[str, str]] | None = None) -> list[Finding]:
    recovered = recovered or set()
    loaded = {agent: load_sessions(agent) for agent in agents}
    flat: dict[str, tuple[str, dict]] = {}
    for agent, data in loaded.items():
        for key, rec in data.items():
            flat[key] = (agent, rec)

    findings: list[Finding] = []
    cutoff_ms = now_ms() - recent_hours * 3600 * 1000

    for agent, data in loaded.items():
        for key, rec in data.items():
            status = str(rec.get('status') or 'unknown')
            updated = rec_time(rec)
            age_min = max(0.0, (now_ms() - updated) / 60000) if updated else 0.0
            label = display_label(key, rec)

            if status == 'running' and age_min >= min_running_minutes:
                live_topic = ':telegram:group:' in key or key.endswith(':main')
                findings.append(Finding(
                    severity='high' if live_topic else 'medium',
                    agent=agent,
                    kind='running_without_recent_closeout',
                    key=key,
                    status=status,
                    age_minutes=age_min,
                    detail=f'{label} is still marked running after {fmt_age(age_min)}.',
                    next_action='Inspect the session history and force a terminal closeout: done, blocked, approval-required, or retry-scheduled.',
                ))

            if (
                updated >= cutoff_ms
                and (status == 'killed' or rec.get('abortedLastRun'))
                and not is_recovered(recovered, key, 'recent_interrupted_session')
            ):
                findings.append(Finding(
                    severity='high',
                    agent=agent,
                    kind='recent_interrupted_session',
                    key=key,
                    status=status,
                    age_minutes=age_min,
                    detail=f'{label} was interrupted recently; abortedLastRun={bool(rec.get("abortedLastRun"))}.',
                    next_action='Recover the task from source evidence or write a blocked report so Ahmed does not have to push manually.',
                ))

            spawned_by = rec.get('spawnedBy')
            duration = rec_duration_minutes(rec)
            parent = flat.get(spawned_by) if spawned_by else None
            if (
                updated >= cutoff_ms
                and spawned_by
                and status == 'done'
                and duration is not None
                and duration < min_running_minutes
                and parent
                and str(parent[1].get('status') or '') == 'running'
            ):
                findings.append(Finding(
                    severity='medium',
                    agent=agent,
                    kind='child_finished_parent_still_running',
                    key=key,
                    status=status,
                    age_minutes=age_min,
                    detail=f'{label} ended after {duration:.1f}m but parent remains running: {spawned_by}.',
                    next_action='Avoid delayed foreground sleeps/yields for retries. Use a durable retry record or scheduled runner, then close the parent session.',
                ))

    order = {'high': 0, 'medium': 1, 'low': 2}
    return sorted(findings, key=lambda f: (order.get(f.severity, 9), f.agent, f.kind, -f.age_minutes))


def render_markdown(findings: list[Finding], agents: list[str], min_running_minutes: int, recent_hours: int) -> str:
    ts = datetime.now(CAIRO).isoformat(timespec='seconds')
    lines = [
        '# Agent Lane Stall Report',
        '',
        f'Generated: {ts}',
        f'Agents: {", ".join(agents)}',
        f'Running threshold: {min_running_minutes} minutes',
        f'Recent interruption window: {recent_hours} hours',
        '',
    ]
    if not findings:
        lines += [
            '## Verdict',
            '',
            'No stalled or recently interrupted CMO/HR lane sessions found.',
            '',
        ]
        return '\n'.join(lines)

    high = sum(1 for f in findings if f.severity == 'high')
    medium = sum(1 for f in findings if f.severity == 'medium')
    lines += [
        '## Verdict',
        '',
        f'Attention needed: {len(findings)} finding(s), high={high}, medium={medium}.',
        '',
        '## Findings',
        '',
        '| Severity | Agent | Kind | Age | Status | Detail | Next action |',
        '|---|---|---|---:|---|---|---|',
    ]
    for f in findings:
        detail = f.detail.replace('|', '\\|')
        action = f.next_action.replace('|', '\\|')
        lines.append(f'| {f.severity} | {f.agent} | {f.kind} | {fmt_age(f.age_minutes)} | {f.status} | {detail} | {action} |')

    lines += ['', '## Session Keys', '']
    for f in findings:
        lines.append(f'- {f.agent} {f.kind}: `{f.key}`')
    lines.append('')
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description='Read-only CMO/HR agent lane stall detector')
    parser.add_argument('--agent', action='append', choices=['cmo', 'hr', 'main', 'cto', 'jobzoom'], help='Agent to scan. Defaults to cmo and hr.')
    parser.add_argument('--min-running-minutes', type=int, default=15, help='Warn when running sessions exceed this age.')
    parser.add_argument('--recent-hours', type=int, default=48, help='Lookback for killed/aborted sessions.')
    parser.add_argument('--report', default=str(ROOT / 'reports' / 'agent-lane-stall-latest.md'), help='Markdown report path. Use empty string to skip writing.')
    parser.add_argument('--recovery-log', default=str(DEFAULT_RECOVERY_LOG), help='JSONL recovery markers for already handled sessions. Use empty string to disable.')
    parser.add_argument('--strict', action='store_true', help='Exit 1 when findings exist.')
    args = parser.parse_args()

    agents = args.agent or list(DEFAULT_AGENTS)
    recovered = load_recoveries(args.recovery_log)
    findings = scan(agents, args.min_running_minutes, args.recent_hours, recovered)
    markdown = render_markdown(findings, agents, args.min_running_minutes, args.recent_hours)

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(markdown + '\n', encoding='utf-8')

    print(markdown)
    if args.strict and findings:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
