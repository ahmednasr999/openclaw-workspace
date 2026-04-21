# Skill Audit Utility

## Purpose

Read-only local scanner for third-party skills and small repositories before adoption.

It is meant to catch obvious problems early, not to certify code as safe.

## Script

- `scripts/skill-audit.py`

## What it checks

- possible hardcoded secrets
- suspicious outbound network write patterns
- dangerous shell commands
- persistence or startup-hook modifications

## What it does not do

- execute code
- install anything
- prove a skill is safe
- understand full runtime intent or complex obfuscation

## Usage

```bash
python3 scripts/skill-audit.py /path/to/skill-or-repo
python3 scripts/skill-audit.py /path/to/skill-or-repo --json
python3 scripts/skill-audit.py /path/to/skill-or-repo --fail-on high
```

## Output

Human mode reports:
- total findings
- severity counts
- category counts
- file, line, rule, and redacted excerpt

JSON mode returns:
- target
- summary
- findings array

## Recommended use

Use this before:
- copying in a third-party skill
- adapting shell scripts from GitHub
- trusting automation that touches credentials, cron, launch agents, or system services

## Interpretation

- High does not always mean malicious, but it does mean stop and inspect.
- Medium often means operational risk or hidden side effects.
- Low is a prompt to review context, not panic.

Treat this as a triage filter, not a final judgment.
