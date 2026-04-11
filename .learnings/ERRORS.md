# Error Log

*Structured error tracking for continuous improvement.*
*Format: [ERR-YYYYMMDD-XXX]*

---

## 2026-04-08
### What I Did Wrong
Tried to log a cron task to the Mission Control Task Board at http://localhost:3001/api/tasks/agent, but the local service was unavailable and the request failed with curl exit code 7.
### Why
I followed the workspace logging rule, but did not first confirm the local task board service was reachable during this cron run.
### Fix
For future cron/routine runs, treat Mission Control logging as best-effort, and if localhost:3001 is unreachable, continue the primary task and record the infrastructure issue in .learnings/ERRORS.md.

## 2026-03-28
### What I Did Wrong
Used em dashes (—) repeatedly in replies despite a clear rule in MEMORY.md: "Never use em dashes (—) anywhere. Use hyphens (-) or commas instead."
Examples from this session: "position — but", "vs 49 before — the extra", "shows it — meaning"
### Why
Rule exists in MEMORY.md but I'm not consistently checking it at reply-generation time. Rule is passive (read at session start) but not enforced in the moment.
### Fix
Before sending any reply, scan for — character. Replace with hyphen (-) or restructure the sentence. No exceptions.

## 2026-04-08
### What I Did Wrong
Tried to apply a gateway config patch using the `patch` object field, but this gateway tool expects the config payload in `raw` for `config.patch`, so the call failed with `raw required`.
### Why
I assumed the gateway tool accepted the same structured `patch` field shape used by the cron tool, instead of following the gateway tool's exact parameter contract.
### Fix
For future gateway config changes, send the patch body as JSON in the `raw` field, and use `baseHash` only as a concurrency guard.

## 2026-04-08
### What I Did Wrong
Tried to re-embed multiple per-agent QMD stores in parallel. They share the same node-llama-cpp build/cache path, so the jobs contended on the CUDA build lock and produced noisy lock failures before falling back.
### Why
I optimized for concurrency before checking whether QMD embeddings share a global model/build cache.
### Fix
Run QMD embedding serially on this host, especially when node-llama-cpp may probe/build shared backends. Parallelize reads/status checks, not embed passes.
## [ERR-20260408-001] mission-control-task-board

**Logged**: 2026-04-08T22:01:58Z
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
Mission Control task board was unreachable on localhost:3001 during Model Guardian cron execution

### Error
```
curl: (7) Failed to connect to localhost port 3001 after 0 ms: Could not connect to server
```

### Context
- Command/operation attempted: POST http://localhost:3001/api/tasks/agent
- Purpose: required pre-task Mission Control logging for cron automation work
- Environment details: OpenClaw workspace cron run on srv1352768

### Suggested Fix
Check whether the local task board service is running and listening on port 3001 before cron tasks depend on it

### Metadata
- Reproducible: unknown
- Related Files: AGENTS.md

---

## [ERR-20260409-001] mission-control-task-board

**Logged**: 2026-04-09T05:00:00Z
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
Mission Control task board was unreachable on localhost:3001 during the scheduled email agent cron run

### Error
```
curl: (7) Failed to connect to localhost port 3001 after 0 ms: Could not connect to server
```

### Context
- Command/operation attempted: POST http://localhost:3001/api/tasks/agent
- Purpose: required pre-task Mission Control logging before running scripts/email-agent.py
- Environment details: OpenClaw workspace cron run on srv1352768

### Suggested Fix
Treat Mission Control logging as best-effort for cron runs when localhost:3001 is down, and separately restore the local task board service

### Metadata
- Reproducible: unknown
- Related Files: AGENTS.md, scripts/email-agent.py
- See Also: ERR-20260408-001

---

## [ERR-20260409-001] mission-control-task-board

**Logged**: 2026-04-09T07:00:00Z
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
Failed to log scheduled email-agent task to Mission Control before execution because the local task board endpoint was unreachable.

### Error
```
curl: (7) Failed to connect to localhost port 3001 after 2 ms: Could not connect to server
```

### Context
- Command attempted: curl -sS -X POST http://localhost:3001/api/tasks/agent ...
- Workflow: scheduled cron run for scripts/email-agent.py
- Environment: /root/.openclaw/workspace on srv1352768

### Suggested Fix
Check whether Mission Control service is running on port 3001 before scheduled agent runs, or add a fallback queue/log when the service is unavailable.

### Metadata
- Reproducible: unknown
- Related Files: AGENTS.md

---
## [ERR-20260409-003] mission-control-task-post

**Logged**: 2026-04-09T07:11:10Z
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
Mission Control task board on localhost:3001 was unreachable when attempting to log a cron task before execution.

### Error


### Context
- Command attempted: curl -sS -X POST http://localhost:3001/api/tasks/agent ...
- Purpose: log Model Guardian cron run before starting work
- Environment: OpenClaw workspace on srv1352768

### Suggested Fix
Check whether the Mission Control task board service is running and listening on port 3001 before enforcing pre-task logging.

### Metadata
- Reproducible: unknown
- Related Files: AGENTS.md

---

## [ERR-20260409-004] mission-control-task-post

**Logged**: 2026-04-09T07:11:18Z
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
Mission Control task board on localhost:3001 was unreachable when attempting to log a cron task before execution.

### Error
```
curl: (7) Failed to connect to localhost port 3001 after 0 ms: Could not connect to server
```

### Context
- Command attempted: curl -sS -X POST http://localhost:3001/api/tasks/agent ...
- Purpose: log Model Guardian cron run before starting work
- Environment: OpenClaw workspace on srv1352768

### Suggested Fix
Check whether the Mission Control task board service is running and listening on port 3001 before enforcing pre-task logging.

### Metadata
- Reproducible: unknown
- Related Files: AGENTS.md

---
## [ERR-20260409-005] sayyad-midday-schema-sync

**Logged**: 2026-04-09T10:30:00Z
**Priority**: low
**Status**: pending
**Area**: pipeline

### Summary
SAYYAD midday scoring hit two avoidable workflow issues: wrong SQLite column assumptions during inspection, and partial NocoDB bulk score sync failures because legacy `CONDITIONAL` verdict values are still present.

### Error
```text
SQLite inspection failed on non-existent columns `url` and `job_description`; the live schema uses `job_url` and `jd_text`.
NocoDB bulk score sync returned 400 for batches containing verdict `CONDITIONAL` because the NocoDB Verdict field only accepts SUBMIT, REVIEW, SKIP.
```

### Context
- Workflow: 2026-04-09 12:20 Cairo SAYYAD midday score run
- Primary task still completed: SQLite updated, targeted NocoDB patch for the two midday jobs succeeded
- Environment: /root/.openclaw/workspace on srv1352768

### Suggested Fix
Before ad hoc DB inspection, read `.schema jobs` first and use canonical column names. For NocoDB sync, normalize legacy `CONDITIONAL` to `REVIEW` (or skip those rows) before batch patching so score syncs do not partially fail.

### Metadata
- Reproducible: yes
- Related Files: data/nasr-pipeline.db, scripts/push-to-nocodb.py

---

## 2026-04-09 - Mission Control task board unavailable during email cron
- What happened: POST to http://localhost:3001/api/tasks/agent failed with connection refused before the scheduled email scan.
- Impact: The cron task ran successfully, but the run was not logged to Mission Control.
- Do differently: Check task board service health before relying on logging, and surface board availability issues separately from agent status.

## 2026-04-09 - Mission Control task board unavailable during Model Guardian cron
- What happened: POST to http://localhost:3001/api/tasks/agent failed with connection refused before running model-guardian-run.py.
- Impact: The Model Guardian check still completed, but this cron run was not logged to Mission Control.
- Do differently: Treat task-board logging as best-effort for routine cron runs, and log the board outage separately when localhost:3001 is unavailable.
## [ERR-20260409-001] mission-control-task-board

**Logged**: $TS
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
Mission Control task board could not be reached before the scheduled email-agent run.

### Error
```
curl: (7) Failed to connect to localhost port 3001 after 0 ms: Could not connect to server
```

### Context
- Command attempted: POST http://localhost:3001/api/tasks/agent
- Purpose: log cron task before running scripts/email-agent.py
- Environment: /root/.openclaw/workspace on srv1352768

### Suggested Fix
Verify the local Mission Control service on port 3001 is running before cron tasks that require pre-log discipline.

### Metadata
- Reproducible: unknown
- Related Files: AGENTS.md

---

## [ERR-20260410-001] last30days-phase3-timeout

**Logged**: 2026-04-10T05:58:00Z
**Priority**: medium
**Status**: pending
**Area**: research

### Summary
Phase 3 upgrade attempt for NASR Research v2 timed out before delivering a valid result.

### Error
```
Sub-agent timed out after only partial progress.
Observed output:
[resolver] saved  → /root/.cache/nasr-research/peter-steinberger/resolve.json
[resolver] backend → fallback
```

### Context
- Operation attempted: Phase 3 upgrade (stronger resolver/synthesis path, Reddit lane, ranking rebalance)
- Environment: /root/.openclaw/workspace/skills/last30days-lite
- Impact: No trustworthy Phase 3 result to report; work must be split into smaller passes.

### Suggested Fix
Split the upgrade into narrower passes, validate each lane separately, and avoid bundling model-path changes with new-source integration in one run.

### Metadata
- Reproducible: unknown
- Related Files: skills/last30days-lite/scripts/resolver.py, skills/last30days-lite/scripts/nasr_research.py

---
