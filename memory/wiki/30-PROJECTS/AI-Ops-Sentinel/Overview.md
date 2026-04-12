# AI Ops Sentinel

## Goal
Detect meaningful operational anomalies in the OpenClaw stack and report one clear verdict without autonomous fixing.

## Intended design
- deterministic classifier
- one verdict
- silent on PASS
- alert only on actionable WARN / FAIL

## Why it matters
This turns scattered operational signals into a reliable executive-level check instead of noisy maintenance chatter.

## Canonical spec
- `/root/.openclaw/workspace/plans/ai-ops-anomaly-sentinel-v1-spec-2026-04-11.md`

## Current status
- Spec written
- Implementation not yet started in this wiki scaffold

## Next build order
1. `scripts/ops-sentinel-check.py`
2. `scripts/ops-sentinel-run.py`
3. cron only after dry-run passes
