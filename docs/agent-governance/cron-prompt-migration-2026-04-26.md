# Cron Prompt Migration Inventory - 2026-04-26

Scope: read active/high-risk cron prompt sources and make file-only progress without editing gateway cron state, restarting services, running live workflows, or sending external messages.

## Active high-risk prompts

| Job | Enabled | Prompt length | Status |
| --- | --- | ---: | --- |
| `X Intelligence Crawler - Weekly` (`50461fbd-0cdd-4a3a-aebf-57f6a342527b`) | yes | 1678 | Skill created at `skills/cron/x-intelligence-crawler/SKILL.md`; cron payload not edited. |
| `CMO Weekly Drafting` (`543124b5-b2bd-445f-be84-d8407564cf9f`) | yes | 1415 | Skill created at `skills/cron/cmo-weekly-drafting/SKILL.md`; cron payload not edited. |

## Disabled SAYYAD prompts

These are present in `/root/.openclaw/cron/jobs.json` but disabled, so they were kept read-only:

| Job | Enabled | Prompt length | Note |
| --- | --- | ---: | --- |
| `SAYYAD - Score & Curate` (`099bd968-b75a-46cc-bd60-51a0de29bc3b`) | no | 1834 | Retired/disabled. Do not migrate or reactivate without explicit approval. |
| `SAYYAD - Score & Curate (midday)` (`ea668c66-f66e-49a9-8e72-e5e50ea07477`) | no | 1583 | Retired/disabled. Do not migrate or reactivate without explicit approval. |
| `SAYYAD Performance Watch - CEO Daily` (`2eb8d8d0-4bc2-4bde-b395-d9066cf03fe8`) | no | 268 | Retired/disabled. Do not migrate or reactivate without explicit approval. |
| `SAYYAD Fail Alert - CEO Daily` (`c5bda997-d015-466c-8754-8e7299cabe1d`) | no | 286 | Retired/disabled. Do not migrate or reactivate without explicit approval. |
| `SAYYAD Weekly Conversion Report - CEO Sunday` (`55b3604f-bec1-4efa-b9e4-e656bd44afb2`) | no | 184 | Retired/disabled. Do not migrate or reactivate without explicit approval. |

## Deferred gateway change

No cron payloads were edited in this pass. If Ahmed approves a gateway cron edit later, replace only the two active large inline prompts with the slim prompts documented inside the new skill files, preserving schedule, enabled state, delivery, session target, model, and timeout.

## Verification performed

- Parsed `/root/.openclaw/cron/jobs.json` read-only to identify active vs disabled prompt sizes.
- Queried `openclaw cron list --json` and `openclaw cron show --json` read-only for the two active jobs.
- Created file-only skill/runbook artifacts for active high-risk prompts.
