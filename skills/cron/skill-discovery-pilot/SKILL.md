---
name: cron-skill-discovery-pilot
description: Weekly deterministic GitHub workflow discovery for the quarantined skill-discovery pilot. Produces local evidence and review reports only; never installs, executes, merges, posts, or messages.
metadata:
  owner: NASR
  status: pilot
---

# Weekly Skill Discovery Pilot

## Schedule

Sunday 11:15 Africa/Cairo through root OS cron.

## Command

```bash
python3 /root/.openclaw/workspace/skills/skill-discovery-pilot/scripts/discover.py \
  --config /root/.openclaw/workspace/config/skill-discovery-pilot.json \
  --max-candidates 8
```

The command runs through `scripts/cron-run-with-alert.sh` with a lock, persistent log, and status JSON. Failure messaging is disabled for this pilot; cron health can inspect the status file.

## Outputs

- `reports/skill-discovery-pilot-latest.md`
- `data/skill-discovery-pilot/<timestamp>/results.json`
- `data/skill-discovery-pilot/<timestamp>/quarantine/`
- `logs/cron/skill-discovery-pilot.log`
- `logs/cron/status/skill-discovery-pilot.json`

## Source of truth

- Workflow and policy: `skills/skill-discovery-pilot/SKILL.md`
- Runtime configuration: `config/skill-discovery-pilot.json`
- Installed schedule: `config/root-crontab.managed`
- Current decision report: `reports/skill-discovery-pilot-latest.md`

## Safety boundary

Read-only GitHub metadata and README retrieval plus local report writes. No repository clone, execution, installation, dependency resolution, active-skill modification, pull request, external message, or promotion.

## Approval boundary

The scheduled run needs no approval because it is read-only externally and writes only local evidence. Any candidate promotion, active-skill change, repository interaction, credential use beyond an already-present optional `GITHUB_TOKEN`, or external message requires a separate approved task.

## Verification

Run `python3 -m unittest -v skills/skill-discovery-pilot/tests/test_discover.py` and inspect the latest report. Any candidate promotion is a separate user-approved workflow.

Read `references/owner.md` when changing the schedule or runner contract. Use `eval/checklist.md` before accepting changes.
