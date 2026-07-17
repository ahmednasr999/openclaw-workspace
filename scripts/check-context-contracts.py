#!/usr/bin/env python3
"""Read-only sanity check for OpenClaw context-engineering docs."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / 'docs/agent-governance/context-contracts-2026-06-17.md'
EVALS = ROOT / 'docs/agent-governance/long-run-context-evals-2026-06-17.md'

REQUIRED_CONTRACT_TERMS = [
    'JobZoom Daily Lane',
    'CMO Content Lane',
    'Email Scan Lane',
    'Gateway Maintenance Lane',
    'Required sources',
    'Ignored context',
    'Approval boundary',
    'Verification gate',
    'Handoff packet',
    'Stop rule',
]

REQUIRED_EVAL_TERMS = [
    'Source discipline',
    'Context isolation',
    'Approval boundary',
    'Verification',
    'Handoff quality',
    'Memory writeback',
    'Critical failure',
    'Scenario 1 - JobZoom Daily Run',
    'Scenario 2 - CMO Draft To Review',
    'Scenario 3 - Email Scan Triage',
    'Scenario 4 - Gateway Maintenance',
]


def check(path: Path, terms: list[str]) -> list[str]:
    if not path.exists():
        return [f'missing file: {path}']
    text = path.read_text(encoding='utf-8')
    missing = [term for term in terms if term not in text]
    return [f'{path}: missing term: {term}' for term in missing]


def main() -> int:
    errors = []
    errors.extend(check(CONTRACTS, REQUIRED_CONTRACT_TERMS))
    errors.extend(check(EVALS, REQUIRED_EVAL_TERMS))
    if errors:
        for err in errors:
            print(f'FAIL {err}')
        return 1
    print(f'OK {CONTRACTS}')
    print(f'OK {EVALS}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
