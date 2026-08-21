# OpenClaw Native Skill Lifecycle

Date: 2026-08-14  
Owner: NASR  
Status: active governance; shadow enforcement

## Decision

Use OpenClaw's native on-demand skill loading and classify skills into three lifecycle tiers. Do not install `atskills` or make remote instructions executable.

## Tiers

1. **Resident** — a capped set of safety-critical or high-frequency controls. A resident entry needs a concrete reason and the tier may not exceed 13 skills.
2. **Local on-demand** — reviewed installed specialists grouped by operational lane. Their bodies load only when the user names them or their trigger clearly matches.
3. **Quarantined external** — inert candidates pinned to a full Git SHA. They cannot be model-visible, executable, network-enabled, or promoted without a separate approval.

The canonical classification is `config/skill-lifecycle.json`. The generated compact view is `reports/skill-lifecycle/INDEX.md`. The index is an operator artifact and is not injected into the system prompt, so this shadow phase adds no runtime prompt cost.

## Promotion gate

An external candidate can move into local on-demand only after:

- immutable revision and provenance evidence;
- suspicious-instruction and duplication review;
- inert representative evaluation;
- named owner, trigger, input, output, failure, and verification contracts;
- focused tests passing;
- Ahmed's separate promotion approval.

Promotion never makes a specialist resident automatically. Resident status requires demonstrated frequency or a global safety role and must remain inside the cap.

## Enforcement

`scripts/check-skill-lifecycle.py` fails when:

- a model-visible skill is unclassified;
- a skill appears in more than one active tier;
- the resident cap is exceeded;
- an external revision is mutable or incomplete;
- a quarantined candidate is executable or model-visible.

The checker also reports classified skills that are no longer model-visible as drift warnings.

## Current boundary

This phase changes workspace governance and adds a deterministic shadow check. It does not edit `/root/.openclaw/openclaw.json`, agent allowlists, plugins, cron, or the gateway. Runtime visibility changes require a separate, clean configuration change because the live config currently has unrelated unresolved edits.

## Run

```bash
openclaw skills list --json 2>/dev/null \
  | python3 scripts/check-skill-lifecycle.py \
      --config config/skill-lifecycle.json \
      --skills-json - \
      --report reports/skill-lifecycle/current.json \
      --index reports/skill-lifecycle/INDEX.md
```
