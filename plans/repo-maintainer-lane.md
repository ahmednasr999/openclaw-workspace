# Repo Maintainer Lane

Objective: run a bounded repository maintenance control loop for OpenClaw workspace repositories.

## Scope

- Watcher runs every 5 minutes through the existing hardened cron wrapper.
- Watcher is read-only except local state, event, and report files.
- Findings are deduped in `data/repo-maintainer-watch-state.json`.
- Latest report is `reports/repo-maintainer/latest.md`.
- At most one CTO worker turn is dispatched per watcher run.

## Guardrails

- No automatic push, merge, destructive delete, public post, credential change, gateway/runtime config edit, service restart, or paid action.
- Worker prompt requires source inspection, scoped local fixes only, verification, and a closeout with evidence.
- Current dirty workspace state is primed as baseline after installation to avoid noisy immediate dispatch.

## Verification

- `python3 -m py_compile scripts/repo-maintainer-watch.py`
- `python3 -m json.tool config/repo-maintainer-lane.json`
- `./scripts/repo-maintainer-watch.py --validate`
- `./scripts/repo-maintainer-watch.py --prime-state`
- `crontab -l` contains `repo-maintainer-watch`
