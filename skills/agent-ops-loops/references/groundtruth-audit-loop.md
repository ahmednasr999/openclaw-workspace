# Groundtruth Audit Loop

Use before trusting claims about a project, workflow, runtime, security posture, platform behavior, scheduled job, or data pipeline.

## Inputs

- Audit target and exact claim set.
- Areas to inspect.
- Source-of-truth artifacts: code, config, DB schema, logs, reports, primary docs, live probes.
- Approval boundary. This loop is read-only by default.

## Loop

1. Define audit areas before inspecting. Common areas:
   - architecture
   - platform compatibility
   - security and privileged surfaces
   - data handling
   - scheduled jobs and queues
   - model/router behavior
   - external integrations
   - performance and capacity
   - deployment/runtime state
   - code quality and tests
2. For each area, inspect direct evidence, not framework assumptions or memory.
3. Mark each area:
   - `proved`: direct evidence supports the claim.
   - `no-issue`: direct evidence found no material issue.
   - `weak`: evidence suggests risk or incomplete proof.
   - `unverified`: required evidence is unavailable.
   - `n/a`: area is not relevant, with reason.
4. Verify external limits from current primary sources when the audit depends on them.
5. Calculate numbers instead of estimating when capacity, quota, cost, or timing matters.
6. Ask before changing code, config, infrastructure, credentials, or production state.

## Stop States

- `success`: every area has a status, severity where relevant, and evidence.
- `blocked`: one or more required areas cannot be verified because access or evidence is missing.
- `approval-required`: audit found a fix, but applying it would exceed read-only authority.

## Evidence

Close with a plain-language overview and an area-to-evidence table. Do not expose secrets. Do not convert missing access into a clean result.
