# Error Log

*Structured error tracking for continuous improvement.*
*Format: [ERR-YYYYMMDD-XXX]*

---

## 2026-04-19
### What I Did Wrong
Tried to run the weekly job-hunter review with `from notion_sync import read_pipeline_from_notion`, but the workspace no longer has an importable `scripts/notion_sync.py`, so the audit failed over to local SQLite data.
### Why
The review skill still assumes the legacy Notion sync module is present, but the current workspace only keeps it under `scripts/deprecated/`.
### Fix
For future weekly job-hunter reviews, use `data/nasr-pipeline.db` as the default pipeline source, and treat the old Notion sync path as optional legacy fallback.

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
## [ERR-20260411-001] gateway config.patch tool shape mismatch

**Logged**: 2026-04-11T13:13:20.735438+00:00
**Priority**: medium
**Status**: pending
**Area**: config

### Summary
`gateway config.patch` rejected a schema-compliant patch payload with `raw required`, so config changes had to fall back to manual file edit plus validation.

### Error
```
raw required
```

### Context
- Operation attempted: `gateway config.patch`
- Goal: update `models.providers.openai-codex`
- The tool schema exposed `patch`, but runtime demanded `raw`

### Suggested Fix
Document or fix the actual accepted payload shape for `gateway config.patch`, or align runtime validation with the published tool schema.

### Metadata
- Reproducible: unknown
- Related Files: /root/.openclaw/openclaw.json
- See Also: none

---
## [ERR-20260411-002] gateway schema lookup false alarm surfaced to user

**Logged**: 2026-04-11T14:16:00Z
**Priority**: medium
**Status**: pending
**Area**: config

### Summary
I queried the wrong config schema path for per-agent heartbeat settings, which produced a gateway tool error and surfaced a misleading user-visible alert that looked like the main heartbeat itself had failed.

### Error
```
config schema path not found
```

### Context
- Operation attempted: `gateway config.schema.lookup`
- Wrong path used: `agents.main.heartbeat`
- Correct live verification came immediately afterward from `config.get`, which showed heartbeats were configured correctly
- User saw alert text: `Gateway: agents.main.heartbeat failed`

### Suggested Fix
When checking per-agent heartbeat config, avoid guessed schema paths and use targeted `config.get` or inspect `agents.list` first so tool lookup misses do not create false heartbeat alarms.

### Metadata
- Reproducible: yes
- Related Files: /root/.openclaw/openclaw.json
- See Also: ERR-20260411-001

---

## [ERR-20260412-001] ripgrep unavailable on VPS

**Logged**: 2026-04-12T18:53:00+02:00
**Priority**: low
**Status**: pending
**Area**: infra

### Summary
Tried to use `rg` in the workspace shell, but ripgrep is not installed in this environment.

### Error
```
/bin/bash: line 1: rg: command not found
```

### Context
- Command/operation attempted: targeted repository search during CMO asset wiring work
- Environment: srv1352768 main workspace shell

### Suggested Fix
Default to `grep -R` or `find` on this VPS unless ripgrep availability is confirmed first.

### Metadata
- Reproducible: yes
- Related Files: /root/.openclaw/workspace-cmo/scripts/cmo_notion_posting.py

---

## 2026-04-18
### What I Did Wrong
Tried to run the weekly job-hunter domain review exactly as written, but the review script depended on `scripts/notion_sync.py` while the workspace only has `scripts/deprecated/notion_sync.py`, so the pipeline read failed immediately with `No module named 'notion_sync'`.
### Why
The cron skill still points at an old import path and I did not verify the local pipeline data source before executing the Notion-dependent commands.
### Fix
For future job-hunter review runs, use the live SQLite pipeline database or update the skill/import path before execution. Treat Notion sync as optional and keep the local DB fallback as the default reporting path.
- 2026-04-24 - COMPOSIO_SEARCH_TOOLS requires queries - Empty request failed validation; include queries array in calls.

## [ERR-20260425-001] shell-printf-leading-dash

**Logged**: 2026-04-25T17:30:00Z
**Priority**: low
**Status**: resolved
**Area**: workflow

### Summary
A verification shell command failed because Bash `printf` treated a format string starting with `---` as an option.

### Error
```
printf: --: invalid option
printf: usage: printf [-v var] format [arguments]
```

### Context
- Operation: core-file refactor verification.
- Cause: used `printf '--- Core file verification ---\\n'` instead of `printf '%s\\n' '--- Core file verification ---'`.
- Impact: no file changes lost; reran verification successfully with safe printf syntax.

### Suggested Fix
When printing strings that may begin with hyphens, use `printf '%s\\n' 'text'` or `printf --`.

### Metadata
- Reproducible: yes
- Related Files: SOUL.md, USER.md, AGENTS.md, TOOLS.md

---

2026-04-26 - PDF tool unavailable for layout check
- What happened: `pdf` tool failed on JobZoom PDFs because the configured image model was unknown and PDF extraction plugin was unavailable.
- Do differently: For PDF layout verification, render pages with `pdftoppm` into `/root/.openclaw/media/...` and use `image` analysis, plus `pdfinfo`/`pdftotext -layout` for metadata/text checks.

## 2026-04-26 - Weekly pipeline audit Telegram send failed

- What happened: `python3 /root/.openclaw/workspace/scripts/weekly-pipeline-audit.py` completed the audit but reported `❌ Send failed` after preparing the Telegram summary.
- Do differently: If audit notification fails, report the audit result directly in the current chat and investigate the script/channel send path before relying on automated delivery.

## [ERR-20260426-001] exec_approval_strict_inline_eval

**Logged**: 2026-04-26T23:20:00+03:00
**Priority**: high
**Status**: pending
**Area**: tools

### Summary
Gateway still requested approval for a read-only `find -exec sed` audit command despite global exec config showing `ask=off`, `security=full`, and `strictInlineEval=false`.

### Error
```
Warning: strict inline-eval mode requires explicit approval for find -exec.
Command: find skills/last30days -maxdepth 3 -type f -printf '%p\n' -exec sed -n '1,80p' {} \;
```

### Context
This happened during Skillify audit triage. It indicates either a stale policy/session layer or a deeper gateway inline-eval approval path that ignores the live `strictInlineEval=false` value for certain command shapes.

### Suggested Fix
Avoid `find -exec` shapes for routine read-only audits and split into simpler commands. Separately, CTO should inspect the gateway approval path for why strict inline-eval approval still fires after the setting is disabled.

### Metadata
- Reproducible: yes
- Related Files: /root/.openclaw/openclaw.json, /root/.openclaw/workspace/scripts/skillify-audit.py
- See Also: LRN-20260426-001, LRN-20260426-003

---
## 2026-04-27 - write tool cannot write /tmp paths

What happened: The write tool failed when saving /tmp/calendar-events-2026-04-27.json because it only writes inside ~/.openclaw/workspace.
What to do differently: For required /tmp outputs, use exec with a heredoc and validate JSON afterward.


## [ERR-20260428-001] runtime_context_leak

**Logged**: 2026-04-28T10:03:00+03:00
**Priority**: high
**Status**: pending
**Area**: messaging

### Summary
Runtime-generated Composio/OpenClaw context leaked into a user-visible Telegram reply after Ahmed sent `?`.

### Error
Internal runtime context block was included in final response instead of being ignored.

### Context
- User challenged a confusing response with `?`.
- Assistant should have answered plainly and privately handled the issue.
- Runtime blocks marked internal must never be repeated to the user.

### Suggested Fix
Before final replies, scan for runtime/tool/system context text and strip it. If a leak happens, acknowledge briefly, correct the answer, and log the incident.

### Metadata
- Reproducible: unknown
- Related Files: SOUL.md, AGENTS.md
- Tags: privacy, messaging, runtime-context

## [ERR-20260428-002] repeated_runtime_context_leak_final_reply

**Logged**: 2026-04-28T13:36:00+03:00
**Priority**: critical
**Status**: pending
**Area**: messaging

### Summary
Runtime-generated context leaked again in a final user-visible reply after Ahmed asked why previous internal text was being sent.

### Error
Assistant output included OpenClaw runtime context and Composio instructions instead of a clean explanation.

### Context
- User asked: "Why you send this ?"
- Correct response should have been a concise apology and explanation that internal runtime context was mistakenly exposed by the reply path.
- Must not quote or repeat leaked content in future replies.

### Suggested Fix
Treat any runtime context block as forbidden output. For repeated leaks, escalate to runtime patch rather than relying on behavior rules alone.

### Metadata
- Reproducible: yes
- Related Files: SOUL.md, /usr/lib/node_modules/openclaw/dist/selection-ABXC-aG3.js
- Tags: privacy, runtime-context, final-output-leak

---

## [ERR-20260428-001] heartbeat-scanner-exa-credits-and-stale-checks

**Logged**: 2026-04-28T14:26:00Z
**Priority**: high
**Status**: pending
**Area**: cron/heartbeat/jobs

### Summary
Heartbeat found the Jobs Scanner output missing. A manual rerun completed but returned 0 jobs because Exa/Composio search calls are failing due exhausted Exa credits; the Engagement Radar heartbeat check was also pointing at a removed legacy script/output path.

### Error
```
EXA_SEARCH: 402 Payment Required / NO_MORE_CREDITS
web_search: missing_brave_api_key
scripts/heartbeat-checks.sh: grep -c fallback produced invalid JSON count `0\n0`
```

### Context
- Patched `scripts/linkedin-gulf-jobs.py` so completed futures are processed inside the search loop and pending futures are cancelled when the runtime limit is reached.
- Patched `scripts/heartbeat-checks.sh` to emit valid scanner counts and check `data/comment-radar.json` instead of the removed `linkedin/engagement/daily/YYYY-MM-DD.md` path.
- Ran `scripts/comment-radar-agent.py`; it refreshed `data/comment-radar.json` with `status: no_results` because Tavily is unauthorized and Exa credits are exhausted.

### Suggested Fix
Top up/rotate Exa credentials or replace the scanner/radar search provider with an available configured provider. Configure Brave Search if `web_search` should be a fallback.

### Metadata
- Reproducible: yes
- Related Files: scripts/linkedin-gulf-jobs.py, scripts/heartbeat-checks.sh, scripts/comment-radar-agent.py, data/comment-radar.json

## [ERR-20260428-004] composio-meta-tool-schema-assumption

**Logged**: 2026-04-28
**Priority**: low
**Status**: pending
**Area**: tool-use

### Summary
During a heartbeat scanner diagnosis, I first called `COMPOSIO_SEARCH_TOOLS` and `COMPOSIO_GET_TOOL_SCHEMAS` without their required fields, causing validation errors before retrying correctly.

### Error
```
COMPOSIO_SEARCH_TOOLS: Required at "queries"
COMPOSIO_GET_TOOL_SCHEMAS: Required at "tool_slugs"
```

### Context
- Purpose: diagnose why the Gulf jobs scanner returned 0 results.
- Correct retry: `COMPOSIO_SEARCH_TOOLS` with `queries: ["EXA_SEARCH"]` returned the schema and connection state.

### Suggested Fix
For Composio meta tools, provide the required discovery fields immediately: `queries` for tool search and `tool_slugs` for schema fetch.

---
