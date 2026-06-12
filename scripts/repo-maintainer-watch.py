#!/usr/bin/env python3
"""Bounded repo-maintainer watcher.

Detects repository maintenance signals, writes a local report, dedupes events,
and optionally dispatches one narrowly scoped CTO agent turn. The watcher itself
never edits repo content, pushes, merges, restarts services, or sends public
messages.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path('/root/.openclaw/workspace')
DEFAULT_CONFIG = ROOT / 'config' / 'repo-maintainer-lane.json'
CAIRO = ZoneInfo('Africa/Cairo')
PRIORITY_ORDER = {'info': 0, 'low': 1, 'medium': 2, 'high': 3, 'critical': 4}


@dataclass
class CommandResult:
    cmd: list[str]
    cwd: str | None
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


@dataclass
class Finding:
    repo: str
    kind: str
    priority: str
    title: str
    details: str
    url: str = ''
    key: str = ''

    @property
    def signature(self) -> str:
        raw = '|'.join([self.repo, self.kind, self.key or self.title, self.details[:300]])
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]


def now() -> datetime:
    return datetime.now(CAIRO)


def run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 30) -> CommandResult:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return CommandResult(cmd, str(cwd) if cwd else None, proc.returncode, proc.stdout, proc.stderr)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ''
        stderr = exc.stderr if isinstance(exc.stderr, str) else ''
        return CommandResult(cmd, str(cwd) if cwd else None, 124, stdout, stderr, True)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def priority_at_least(value: str, minimum: str) -> bool:
    return PRIORITY_ORDER.get(value, 0) >= PRIORITY_ORDER.get(minimum, 0)


def clean_path(raw: str) -> str:
    path = raw.strip()
    if ' -> ' in path:
        path = path.split(' -> ', 1)[1]
    return path.strip()


def ignored(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def watched(path: str, prefixes: list[str]) -> bool:
    for prefix in prefixes:
        if prefix.endswith('/') and path.startswith(prefix):
            return True
        if path == prefix:
            return True
    return False


def scan_dirty(repo: dict[str, Any]) -> list[Finding]:
    repo_path = Path(repo['path'])
    result = run(['git', 'status', '--porcelain=v1', '--untracked-files=normal'], cwd=repo_path, timeout=20)
    if result.returncode != 0:
        return [Finding(
            repo=repo['name'],
            kind='git_status_error',
            priority='medium',
            title='Git status failed',
            details=(result.stderr or result.stdout).strip()[:800],
            key='git-status-error',
        )]

    ignore_patterns = repo.get('ignore_dirty', [])
    watch_paths = repo.get('watch_dirty_paths', [])
    important: list[str] = []
    other: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        status = line[:2].strip() or '??'
        path = clean_path(line[3:])
        if ignored(path, ignore_patterns):
            continue
        item = f'{status} {path}'
        if watched(path, watch_paths):
            important.append(item)
        else:
            other.append(item)

    findings: list[Finding] = []
    if important:
        digest = hashlib.sha256('\n'.join(sorted(important)).encode('utf-8')).hexdigest()[:12]
        details = '\n'.join(sorted(important)[:40])
        if len(important) > 40:
            details += f'\n... {len(important) - 40} more important dirty paths'
        findings.append(Finding(
            repo=repo['name'],
            kind='dirty_important_paths',
            priority='high',
            title=f'{len(important)} important dirty repo path(s)',
            details=details,
            key=f'important-dirty-{digest}',
        ))
    if other:
        digest = hashlib.sha256('\n'.join(sorted(other)).encode('utf-8')).hexdigest()[:12]
        details = '\n'.join(sorted(other)[:40])
        if len(other) > 40:
            details += f'\n... {len(other) - 40} more dirty paths'
        findings.append(Finding(
            repo=repo['name'],
            kind='dirty_other_paths',
            priority='medium',
            title=f'{len(other)} non-ignored dirty repo path(s)',
            details=details,
            key=f'other-dirty-{digest}',
        ))
    return findings


def gh_json(cmd: list[str], timeout: int = 35) -> tuple[Any | None, str | None]:
    result = run(cmd, timeout=timeout)
    if result.returncode != 0:
        return None, (result.stderr or result.stdout).strip()[:1000]
    try:
        return json.loads(result.stdout or 'null'), None
    except json.JSONDecodeError as exc:
        return None, f'JSON parse failed: {exc}: {(result.stdout or "")[:500]}'


def label_names(item: dict[str, Any]) -> list[str]:
    names = []
    for label in item.get('labels') or []:
        if isinstance(label, dict) and label.get('name'):
            names.append(str(label['name']).lower())
        elif isinstance(label, str):
            names.append(label.lower())
    return names


def scan_github(repo: dict[str, Any]) -> list[Finding]:
    gh_repo = repo.get('github')
    if not gh_repo:
        return []

    findings: list[Finding] = []
    repo_name = repo['name']
    default_branch = repo.get('default_branch') or 'main'

    runs, error = gh_json([
        'gh', 'run', 'list', '--repo', gh_repo, '--limit', '12',
        '--json', 'databaseId,workflowName,conclusion,status,createdAt,headBranch,event,url'
    ])
    if error:
        findings.append(Finding(repo_name, 'github_read_error', 'medium', 'GitHub run scan failed', error, key='gh-runs-error'))
    else:
        for run_item in runs or []:
            conclusion = str(run_item.get('conclusion') or '').lower()
            status = str(run_item.get('status') or '').lower()
            branch = str(run_item.get('headBranch') or '')
            if conclusion in {'failure', 'timed_out', 'action_required', 'cancelled'}:
                priority = 'critical' if branch == default_branch else 'high'
                findings.append(Finding(
                    repo=repo_name,
                    kind='ci_failure',
                    priority=priority,
                    title=f"CI {conclusion}: {run_item.get('workflowName') or 'workflow'} on {branch or 'unknown branch'}",
                    details=f"status={status}; conclusion={conclusion}; created={run_item.get('createdAt')}; event={run_item.get('event')}",
                    url=str(run_item.get('url') or ''),
                    key=f"ci-{run_item.get('databaseId')}",
                ))

    issues, error = gh_json([
        'gh', 'issue', 'list', '--repo', gh_repo, '--state', 'open', '--limit', '20',
        '--json', 'number,title,labels,updatedAt,url'
    ])
    if error:
        findings.append(Finding(repo_name, 'github_read_error', 'medium', 'GitHub issue scan failed', error, key='gh-issues-error'))
    else:
        for issue in issues or []:
            labels = label_names(issue)
            priority = 'medium'
            if any(name in {'security', 'vulnerability'} for name in labels):
                priority = 'critical'
            elif any(name in {'bug', 'regression', 'broken'} for name in labels):
                priority = 'high'
            if priority_at_least(priority, 'high'):
                findings.append(Finding(
                    repo=repo_name,
                    kind='issue_attention',
                    priority=priority,
                    title=f"Issue #{issue.get('number')}: {issue.get('title')}",
                    details=f"labels={', '.join(labels) or 'none'}; updated={issue.get('updatedAt')}",
                    url=str(issue.get('url') or ''),
                    key=f"issue-{issue.get('number')}",
                ))

    prs, error = gh_json([
        'gh', 'pr', 'list', '--repo', gh_repo, '--state', 'open', '--limit', '20',
        '--json', 'number,title,isDraft,updatedAt,headRefName,url'
    ])
    if error:
        findings.append(Finding(repo_name, 'github_read_error', 'medium', 'GitHub PR scan failed', error, key='gh-prs-error'))
    else:
        ready = [pr for pr in (prs or []) if not pr.get('isDraft')]
        if ready:
            details = '\n'.join(
                f"#{pr.get('number')} {pr.get('title')} ({pr.get('headRefName')}, updated {pr.get('updatedAt')})"
                for pr in ready[:10]
            )
            findings.append(Finding(
                repo=repo_name,
                kind='open_prs',
                priority='medium',
                title=f'{len(ready)} ready open PR(s)',
                details=details,
                key='ready-open-prs-' + hashlib.sha256(details.encode('utf-8')).hexdigest()[:10],
            ))

    return findings


def scan_repo(repo: dict[str, Any]) -> list[Finding]:
    repo_path = Path(repo['path'])
    if not repo_path.exists():
        return [Finding(repo['name'], 'repo_missing', 'high', 'Configured repo path missing', str(repo_path), key='repo-missing')]
    if not (repo_path / '.git').exists():
        return [Finding(repo['name'], 'repo_not_git', 'medium', 'Configured path is not a git repo', str(repo_path), key='repo-not-git')]
    findings = []
    findings.extend(scan_dirty(repo))
    findings.extend(scan_github(repo))
    return findings


def write_report(config: dict[str, Any], findings: list[Finding], dispatches: list[dict[str, Any]], mode: str) -> Path:
    report_path = Path(config['report_path'])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    ts = now().isoformat()
    sorted_findings = sorted(findings, key=lambda f: (-PRIORITY_ORDER.get(f.priority, 0), f.repo, f.kind, f.title))
    lines = [
        '# Repo Maintainer Lane',
        '',
        f'Generated: {ts}',
        f'Mode: {mode}',
        f'Findings: {len(sorted_findings)}',
        f'Dispatches: {len(dispatches)}',
        '',
    ]
    if dispatches:
        lines.append('## Dispatch')
        for item in dispatches:
            lines.append(f"- {item.get('status')}: {item.get('finding', {}).get('title', 'unknown')} ({item.get('returncode')})")
        lines.append('')
    if sorted_findings:
        lines.append('## Findings')
        for finding in sorted_findings:
            lines.append(f'- [{finding.priority.upper()}] {finding.repo} / {finding.kind}: {finding.title}')
            if finding.url:
                lines.append(f'  URL: {finding.url}')
            for detail_line in finding.details.splitlines()[:8]:
                lines.append(f'  {detail_line}')
        lines.append('')
    else:
        lines.append('No findings.')
        lines.append('')
    lines.append('## Guardrails')
    lines.append('- Watcher is read-only except local state/report writes by default.')
    lines.append('- Worker dispatch requires both config dispatch_enabled=true and an explicit --dispatch run flag.')
    lines.append('- No push, merge, public post, credential change, destructive delete, gateway restart, or service change without approval.')
    report_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return report_path


def write_event(config: dict[str, Any], payload: dict[str, Any]) -> Path:
    events_dir = Path(config['events_dir'])
    events_dir.mkdir(parents=True, exist_ok=True)
    path = events_dir / f"{now():%Y%m%d-%H%M%S}.json"
    save_json(path, payload)
    return path


def build_worker_prompt(finding: Finding, report_path: Path) -> str:
    parts = [
        'Repo maintainer lane detected a maintenance finding.',
        '',
        f'Repo: {finding.repo}',
        f'Priority: {finding.priority}',
        f'Kind: {finding.kind}',
        f'Title: {finding.title}',
        f'Report: {report_path}',
    ]
    if finding.url:
        parts.append(f'URL: {finding.url}')
    parts.extend([
        '',
        'Details:',
        finding.details,
        '',
        'Success criteria:',
        '- Inspect the actual repo/source/logs before acting.',
        '- Fix only safe local/code/documentation issues that are clearly in scope.',
        '- Do not push, merge, delete, restart services, edit gateway/runtime config, change credentials, post publicly, or message third parties.',
        '- Ask Ahmed before any external-impact, destructive, paid, credential, or runtime/gateway action.',
        '- Verify the outcome with concrete checks, then close with files changed, checks run, evidence, and residual risk.',
    ])
    return '\n'.join(parts)


def dispatch_worker(config: dict[str, Any], finding: Finding, report_path: Path) -> dict[str, Any]:
    cmd = [
        'openclaw', 'agent',
        '--agent', str(config.get('owner_agent') or 'cto'),
        '--session-key', str(config.get('session_key') or 'agent:cto:repo-maintainer'),
        '--message', build_worker_prompt(finding, report_path),
        '--timeout', str(config.get('dispatch_timeout_seconds') or 900),
        '--json',
    ]
    env = os.environ.copy()
    env.setdefault('OPENCLAW_LOG_LEVEL', 'error')
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=int(config.get('dispatch_timeout_seconds') or 900) + 30, env=env)
        return {
            'status': 'dispatched' if proc.returncode == 0 else 'dispatch_failed',
            'returncode': proc.returncode,
            'stdout_tail': proc.stdout[-2000:],
            'stderr_tail': proc.stderr[-2000:],
            'finding': asdict(finding),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            'status': 'dispatch_timeout',
            'returncode': 124,
            'stdout_tail': (exc.stdout or '')[-2000:] if isinstance(exc.stdout, str) else '',
            'stderr_tail': (exc.stderr or '')[-2000:] if isinstance(exc.stderr, str) else '',
            'finding': asdict(finding),
        }


def update_state(state: dict[str, Any], findings: list[Finding], *, prime: bool) -> None:
    state.setdefault('findings', {})
    ts = now().isoformat()
    for finding in findings:
        entry = state['findings'].setdefault(finding.signature, {})
        entry.setdefault('first_seen_at', ts)
        entry['last_seen_at'] = ts
        entry['repo'] = finding.repo
        entry['kind'] = finding.kind
        entry['priority'] = finding.priority
        entry['title'] = finding.title
        if prime:
            entry.setdefault('primed_at', ts)


def eligible_findings(config: dict[str, Any], state: dict[str, Any], findings: list[Finding]) -> list[Finding]:
    minimum = str(config.get('dispatch_min_priority') or 'high')
    cooldown = timedelta(minutes=int(config.get('dispatch_cooldown_minutes') or 180))
    ts = now()
    eligible = []
    for finding in sorted(findings, key=lambda f: -PRIORITY_ORDER.get(f.priority, 0)):
        if not priority_at_least(finding.priority, minimum):
            continue
        entry = state.get('findings', {}).get(finding.signature, {})
        if entry.get('primed_at') and not entry.get('dispatched_at'):
            continue
        attempt_at = entry.get('last_dispatch_attempt_at') or entry.get('dispatched_at') or entry.get('last_dispatch_error_at')
        if attempt_at:
            try:
                last = datetime.fromisoformat(attempt_at)
                if ts - last < cooldown:
                    continue
            except ValueError:
                pass
        eligible.append(finding)
    return eligible


def main() -> int:
    parser = argparse.ArgumentParser(description='Bounded repo-maintainer watcher')
    parser.add_argument('--config', default=str(DEFAULT_CONFIG))
    parser.add_argument('--dispatch', action='store_true', help='Allow worker dispatch when enabled in config')
    parser.add_argument('--no-dispatch', action='store_true')
    parser.add_argument('--prime-state', action='store_true', help='Mark current findings as baseline and do not dispatch')
    parser.add_argument('--validate', action='store_true', help='Validate config and scan read-only without dispatch')
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_json(config_path, None)
    if not isinstance(config, dict):
        print(json.dumps({'ok': False, 'error': f'invalid config: {config_path}'}, ensure_ascii=False))
        return 2
    if not config.get('enabled', True):
        print(json.dumps({'ok': True, 'disabled': True}, ensure_ascii=False))
        return 0

    state_path = Path(config['state_path'])
    state = load_json(state_path, {'findings': {}, 'runs': []})
    findings: list[Finding] = []
    for repo in config.get('repos') or []:
        findings.extend(scan_repo(repo))

    mode = 'validate' if args.validate else 'prime-state' if args.prime_state else 'normal'
    update_state(state, findings, prime=args.prime_state or args.validate)
    dispatches: list[dict[str, Any]] = []
    report_path = write_report(config, findings, dispatches, mode)

    should_dispatch = bool(config.get('dispatch_enabled')) and args.dispatch and not args.no_dispatch and not args.prime_state and not args.validate
    if should_dispatch:
        max_dispatches = int(config.get('max_dispatches_per_run') or 1)
        for finding in eligible_findings(config, state, findings)[:max_dispatches]:
            attempt_ts = now().isoformat()
            entry = state.setdefault('findings', {}).setdefault(finding.signature, {})
            entry['last_dispatch_attempt_at'] = attempt_ts
            result = dispatch_worker(config, finding, report_path)
            dispatches.append(result)
            if result['status'] == 'dispatched':
                entry['dispatched_at'] = now().isoformat()
            else:
                entry['last_dispatch_error_at'] = now().isoformat()
                entry['last_dispatch_error'] = result['status']
        if dispatches:
            report_path = write_report(config, findings, dispatches, mode)

    run_record = {
        'ts': now().isoformat(),
        'mode': mode,
        'findings': len(findings),
        'dispatches': len(dispatches),
        'report_path': str(report_path),
    }
    state.setdefault('runs', []).append(run_record)
    state['runs'] = state['runs'][-200:]
    save_json(state_path, state)
    event_path = write_event(config, {
        'run': run_record,
        'findings': [asdict(f) | {'signature': f.signature} for f in findings],
        'dispatches': dispatches,
    })

    failed_dispatch = any(d.get('status') != 'dispatched' for d in dispatches)
    summary = {
        'ok': not failed_dispatch,
        'mode': mode,
        'findings': len(findings),
        'dispatches': len(dispatches),
        'report_path': str(report_path),
        'event_path': str(event_path),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 1 if failed_dispatch else 0


if __name__ == '__main__':
    raise SystemExit(main())
