# Entity and Write-Path Registry

## Decision

Keep the architecture federated, but assign exactly one accountable owner and one declared write direction to every core entity. Do not build an all-in-one database and do not let local caches, indexes, reports, or execution logs become accidental sources of truth.

The machine-readable contract is `config/entity-write-path-registry.json`. The checker is `scripts/check-entity-write-path-registry.py`.

## Authority map

| Entity | Accountable owner | Primary authority | Controlled direction |
|---|---|---|---|
| Jobs | HR | `data/nasr-pipeline.db#jobs` | collectors/JobZoom -> declared bridge -> main pipeline |
| Applications | HR | main pipeline application state | confirmed event -> owning ledger -> reconciliation bridge |
| Career contacts | HR | `data/nasr-pipeline.db#recruiters` | verified interaction -> HR review -> recruiter record |
| Content | CMO | Notion Content Calendar | approved CMO workflow -> Notion -> publisher -> verified writeback |
| Tasks | NASR/main | `memory/active-tasks.md` | verified decision/state -> owner-reviewed task update |
| Calendar | NASR/main | Google Calendar | explicit intent -> provider write -> provider readback |
| Email | HR | Gmail | Gmail -> sentinel read/classify/alert; no mailbox write path |
| Knowledge | NASR/main | curated workspace Markdown | verified evidence -> daily note -> reviewed single-owner promotion |
| Runtime operations | CTO | live OpenClaw/runtime state | approved maintenance -> first-class write -> live verification |

## Important precedence rules

- A local cache or read model never outranks its provider or canonical store.
- For applications, a positive applied marker in either the main pipeline or JobZoom blocks duplicate action. The conflict is reconciled one way into the main pipeline; a negative marker never clears a positive one automatically.
- Notion alone owns content approval, scheduling, and publishing state. Campaign files are coordination and learning artifacts.
- Gmail owns message state. The HR Career Sentinel owns only checkpoints, classifications, dedupe, and alert-delivery state.
- Google Calendar owns event state. `/tmp/calendar-events-*.json` is only a briefing cache.
- `memory/active-tasks.md` owns cross-workflow commitments. Taskflow/OpenClaw run databases are execution evidence, not task intent.
- Curated Markdown owns durable knowledge. `knowledge.db`, search indexes, and conversation summaries are read models or evidence sources.
- Live OpenClaw state outranks reports and cold snapshots for runtime claims.

## Production automation gate

Every entity must document and pass these seven controls before a new production automation is added:

1. Ownership
2. Validation
3. Permissions
4. Audit log
5. Idempotency
6. Rollback
7. Kill switch

The registry records evidence for each control. Passing the registry audit means the control contract is complete and its declared local evidence is present. It does not grant new external-write or runtime authority.

## Workflow measurement

The first measurement window covers the five busiest lanes: job search, content, email, knowledge, and runtime operations. Each lane uses the same four measures:

- Volume
- Manual touch minutes
- Cycle time
- Exception count

Historical manual effort is not invented. Instrumentation is defined now; the first seven-day observation window runs from 18 to 25 August 2026 using existing timestamps plus a bounded manual-touch sample. Any later automation decision should cite that baseline and identify which manual step it removes.

## Validation

```bash
python3 scripts/check-entity-write-path-registry.py
python3 scripts/check-entity-write-path-registry.py --live \
  --output reports/entity-write-path-registry-audit-latest.json
python3 -m unittest -v tests/test_entity_write_path_registry.py
```

Structural validation fails on missing required entities/workflows, duplicate entity IDs, ambiguous ownership, undeclared write paths, incomplete governance gates, invalid workflow references, or missing measurement fields. Live validation additionally checks declared local files, JSON keys, markers, and SQLite tables without changing them.

## Boundary

This release is a read-only governance layer. It does not migrate data, change production writers, alter cron, edit OpenClaw configuration, restart services, contact third parties, or publish content. Production enforcement inside individual owner workflows is a later decision after the registry survives the observation window and owner review.
