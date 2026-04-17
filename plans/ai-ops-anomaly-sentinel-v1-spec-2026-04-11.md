# AI Ops Anomaly Sentinel v1 - Implementation Spec

Date: 2026-04-11
Owner: CTO lane
Status: spec only, no implementation yet

## Objective
Build a narrow, low-noise ops sentinel that detects and summarizes the highest-value OpenClaw failure modes:
- routing drift
- false alarms
- gateway instability

It should output one concise verdict, not a dashboard.

## Success criteria
The v1 sentinel must:
1. detect active model/provider drift on production routes
2. detect likely false alarms where a probe failed but runtime is healthy
3. detect gateway instability or restart/reconnect churn
4. emit one short PASS/WARN/FAIL summary with next action
5. stay silent on PASS by default

## Explicit non-goals for v1
- no autonomous fixing
- no broad memory ingestion
- no LLM-first reasoning loop
- no UI/dashboard
- no chatty all-clear messages
- no cost optimization logic yet, except optional evidence capture

## Recommended file layout

### New files
- `scripts/ops-sentinel-check.py`
  - deterministic collector + classifier
  - prints structured stdout lines
- `scripts/ops-sentinel-run.py`
  - wrapper for cron
  - calls `ops-sentinel-check.py`
  - converts structured stdout into alert lines like `DM_ALERT:` / `TOPIC_ALERT:` / `NO_ALERTS`
- `data/ops-sentinel-history.jsonl`
  - append-only verdict history
- `data/ops-sentinel-known-false-alarms.json`
  - known benign signatures and suppressions
- `plans/ai-ops-anomaly-sentinel-v1-spec-2026-04-11.md`
  - this spec

### Existing files to reuse, not replace
- `scripts/model-guardian-run.py`
- `scripts/nasr-doctor.py`
- `scripts/session-cleanup.sh`
- `scripts/session-watchdog.sh`
- `/root/.openclaw/openclaw.json`
- `/root/.openclaw/agents/*/sessions/sessions.json`

## Data sources for v1

### 1. Live config
Read only these targeted areas from `/root/.openclaw/openclaw.json`:
- `agents.defaults.model.primary`
- `agents.defaults.heartbeat`
- per-agent `main/hr/cto/cmo/jobzoom` model + heartbeat sections
- telegram topic bindings

### 2. Active session registries
Inspect:
- `/root/.openclaw/agents/main/sessions/sessions.json`
- `/root/.openclaw/agents/hr/sessions/sessions.json`
- `/root/.openclaw/agents/cto/sessions/sessions.json`
- `/root/.openclaw/agents/cmo/sessions/sessions.json`
- `/root/.openclaw/agents/jobzoom/sessions/sessions.json`

Only compare the expected production route sessions when present. Ignore deep historical noise unless it conflicts with an active route.

### 3. Gateway health evidence
Collect:
- `systemctl --user is-active openclaw-gateway`
- last 150-300 journal lines for `openclaw-gateway.service`
- recent restarts count in a short window
- reconnect patterns like stale socket loops

### 4. Doctor summary
Use `openclaw doctor --non-interactive` only as secondary evidence.
Doctor warnings alone must never trigger FAIL without runtime evidence.

### 5. Optional cron inventory
Use `cron list` or direct jobs file only to verify critical model fields exist on key operational jobs.
This is WARN-level evidence only unless a live route is proven wrong.

## Core anomaly classes
Use exactly these classes in v1:

1. `routing_drift`
- session-level model/provider override conflicts with intended config
- heartbeat target conflicts with expected topic/DM
- critical cron job model missing or conflicting

2. `gateway_instability`
- gateway inactive
- repeated restart loop
- repeated socket reconnect churn with live impact
- critical plugin/runtime load failure affecting operation

3. `false_alarm`
- a probe/doctor/schema lookup failed, but no live runtime break is visible
- example: schema path lookup failure surfaced as heartbeat failure

4. `maintenance_noise`
- many warnings, little actual impact
- use only as WARN, never FAIL in v1

## Expected route baseline for v1
Treat these as production routes unless config says otherwise:
- `main` -> Telegram DM `866838380`
- `hr` -> Telegram topic `9`
- `cto` -> Telegram topic `8`
- `cmo` -> Telegram topic `7`
- `jobzoom` -> Telegram topic `5247`

Expected active model path:
- primary route model: `openai-codex/gpt-5.4`
- session-level overrides should not conflict with that

Expected heartbeat policy:
- `main`: `directPolicy allow`
- `hr/cto/cmo/jobzoom`: `directPolicy block`

## Detection rules

### A. Routing drift
Raise `routing_drift` when any active route shows one of:
- `modelOverride` != `gpt-5.4`
- `providerOverride` != `openai-codex`
- heartbeat target mismatch against expected route
- active session metadata conflicts with current config for same route

Severity:
- FAIL if active production route is wrong
- WARN if only critical cron metadata is missing or a stale route is suspected but not confirmed

Confidence:
- high if both config and active session evidence agree
- medium if only one source shows the mismatch
- low if mismatch is inferred from status text only

### B. Gateway instability
Raise `gateway_instability` when any of:
- service inactive
- 2+ restarts in short window
- repeated reconnect loop plus user-facing degradation
- critical startup/runtime error in logs

Severity:
- FAIL if service unhealthy or core routing affected
- WARN for reconnect churn without confirmed impact

### C. False alarm
Raise `false_alarm` when:
- alert source is schema/probe/doctor-only
- no matching runtime failure exists in logs or live checks
- gateway and route health remain intact

Severity:
- WARN at most
- usually silent if signature already known and suppressed

### D. Maintenance noise
Raise `maintenance_noise` when:
- recurring low-value warnings dominate logs
- doctor reports advisory-only clutter
- success announcements are too noisy

Severity:
- WARN only

## Output contract for `ops-sentinel-check.py`
The checker prints structured plain-text lines only.

Required lines:
- `VERDICT: PASS|WARN|FAIL`
- `CLASS: <routing_drift|gateway_instability|false_alarm|maintenance_noise|none>`
- `CONFIDENCE: low|medium|high`
- `TARGET: <agent/topic/lane/or none>`
- `SUMMARY: <one sentence>`
- `NEXT: <recommended next step>`

Optional lines:
- `EVIDENCE: <short evidence line>` repeated as needed, max 5 lines
- `KNOWN_FALSE_ALARM: <signature-id>`
- `SUPPRESS: yes`

Example FAIL:
- `VERDICT: FAIL`
- `CLASS: routing_drift`
- `CONFIDENCE: high`
- `TARGET: hr/topic:9`
- `SUMMARY: Active HR session override conflicts with GPT-5.4 route config.`
- `NEXT: Patch active session metadata before touching router defaults.`

## Output contract for `ops-sentinel-run.py`
Wrapper behavior:
- call `ops-sentinel-check.py`
- append a compact JSON record to `data/ops-sentinel-history.jsonl`
- convert verdict into delivery lines

Allowed wrapper output:
- `DM_ALERT: ...`
- `TOPIC_ALERT: ...`
- `INFO: ...`
- `NO_ALERTS`

Delivery policy:
- FAIL -> `DM_ALERT:` to Ahmed DM, optional `TOPIC_ALERT:` to CTO topic 8
- WARN -> `TOPIC_ALERT:` to CTO topic 8 only
- PASS -> `NO_ALERTS`
- suppressed known false alarm -> `NO_ALERTS`

## Known false alarm registry
Use `data/ops-sentinel-known-false-alarms.json` with entries like:
```json
[
  {
    "id": "schema-lookup-heartbeat-path",
    "match": "config schema path not found",
    "class": "false_alarm",
    "note": "Diagnostic lookup failure, not heartbeat runtime failure",
    "suppress": true
  }
]
```

Rules:
- only suppress if no runtime contradiction exists
- store the signature id in history when suppression fires

## History schema
Append one JSON object per run to `data/ops-sentinel-history.jsonl`:
```json
{
  "timestampUtc": "2026-04-11T18:00:00Z",
  "verdict": "WARN",
  "class": "false_alarm",
  "confidence": "high",
  "target": "main/heartbeat",
  "summary": "Schema lookup failure triggered alert, runtime healthy.",
  "next": "Ignore alert and avoid invalid schema path lookup.",
  "evidence": ["gateway active", "no heartbeat runtime failure in logs"],
  "suppressed": false
}
```

## Cron design recommendation
Create one isolated cron job owned by CTO lane.

Recommendation:
- schedule: every 4 hours, Cairo time, during active hours only
- session target: isolated
- model: `openai-codex/gpt-5.4`
- delivery: none at cron level, let wrapper decide via stdout rules

Suggested prompt pattern:
- run `python3 /root/.openclaw/workspace/scripts/ops-sentinel-run.py`
- for each `DM_ALERT:` line, send to Ahmed DM
- for each `TOPIC_ALERT:` line, send to CTO topic 8
- if `NO_ALERTS`, send nothing
- if script fails entirely, send one DM: `AI Ops Sentinel ERROR: script failed to run.`

## Suggested implementation sequence

### Phase 1 - checker only
Build `scripts/ops-sentinel-check.py` with:
- config reader
- session registry comparator
- gateway log/service probe
- doctor as advisory input
- classifier

### Phase 2 - wrapper + history
Build `scripts/ops-sentinel-run.py`:
- run checker
- parse structured lines
- write history
- emit alert lines

### Phase 3 - cron wiring
Add cron after manual dry-run proves:
- PASS stays silent
- known false alarm is suppressed
- a forced route mismatch produces FAIL

## Manual test cases before cron
1. Healthy state
- expected result: `PASS`, no alerts

2. Simulated false alarm
- inject known schema-path failure signature without runtime break
- expected result: `WARN false_alarm` or silent suppression if configured

3. Simulated routing drift
- temporary fixture or sample JSON showing wrong `modelOverride`
- expected result: `FAIL routing_drift`

4. Gateway down fixture
- simulate inactive service response in test mode
- expected result: `FAIL gateway_instability`

## Guardrails
- never auto-edit config or session files in v1
- never classify from doctor alone
- never scan full raw config dumps with secrets unless absolutely required
- ignore historical session noise unless it conflicts with active routes
- cap evidence lines to avoid noisy alerts

## Recommended next step after v1
Only after v1 is stable, add:
- simple baselines for restart frequency and runtime spikes
- cost leak detection for polling-heavy jobs
- remediation playbooks per anomaly class

## Final recommendation
Build this as a deterministic ops classifier, not an agentic fixer.
If it becomes chatty, you failed the design.