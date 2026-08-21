---
name: governed-learning-loop-cron
description: "Weekly deterministic build of governed learning candidates. Use when running or auditing the Saturday learning-loop cron, its local registry/report writes, failure alert, or no-promotion boundary."
metadata:
  schedule: "Saturday 10:00 Cairo (Africa/Cairo)"
  skill_type: cron
---

# Governed Learning Loop Cron

Run only:

```bash
python3 /root/.openclaw/workspace/skills/governed-learning-loop/scripts/learning_loop.py build
```

## Boundaries

- Read observations from `data/learning-loop/registry.json`.
- Write only the registry and `reports/learning-loop/latest.md`.
- Do not inspect raw sessions, invent observations, edit active skills, update core instructions, change runtime configuration, or perform external actions.
- Keep successful runs silent. Use the existing failure alert for command failures.

## Success

- Exit code 0.
- Registry remains valid JSON.
- Report is non-empty.
- `active_promotions` remains zero.
- Repeating the build does not change the registry when observations are unchanged.
