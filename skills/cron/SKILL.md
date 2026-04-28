---
name: cron-skills-index
description: "Index skill for scheduled/cron-owned OpenClaw workflows. Use when auditing, routing, or maintaining recurring cron skills under skills/cron/."
metadata:
  owner: CTO
  status: index
---

# Cron Skills Index

This directory contains one subdirectory per scheduled workflow skill.

Use this top-level skill only as an index or audit target. Do not treat it as the owner of every cron workflow.

## Rules

- Each child cron workflow should keep its own `SKILL.md`.
- Time-based recurring work belongs in cron when it is proven useful and safe.
- Public, destructive, paid, credential, gateway/config/runtime-changing actions remain approval-gated.
- If a cron skill repeatedly fails or needs Ahmed to babysit, apply the NASR Skillify Protocol.

## Audit

Run:

```bash
python3 scripts/skillify-audit.py
```

For deeper safety review of imported cron skills, use:

```bash
python3 scripts/skill-audit.py skills/cron
```
