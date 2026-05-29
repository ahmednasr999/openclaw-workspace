# Skill Bundles

Local bundle contracts for repeatable OpenClaw workflows.

These files are intentionally not live Telegram slash-command routing yet. They define a small, inspectable layer that maps one command name to existing skills plus a standing instruction, approval boundary, output shape, and verification bar.

## Contract

Each bundle is a YAML file with:

- `name`: stable bundle id, matching the filename.
- `command`: intended slash command, for example `/cv-pack`.
- `owner`: lane owner.
- `permission_profile`: `read-only`, `local-write`, `external-write`, `runtime-change`, or `disruptive`.
- `skills`: existing workspace skill ids, resolved as `skills/<id>/SKILL.md`.
- `standing_instruction`: the frozen workflow behavior.
- `approval_boundary`: what the bundle may do without asking Ahmed, and what remains gated.
- `verification`: how the agent proves the outcome, not just that a tool ran.
- `forbidden`: behaviors that invalidate the run.

## Use

Manual use:

1. Open the relevant YAML file.
2. Load every listed skill that applies to the task.
3. Treat `standing_instruction` as the bundle-level instruction above the individual skill files.
4. Stop at the approval boundary.
5. Verify against the listed checks before reporting done.

Validate bundles:

```bash
python3 scripts/skill-bundles-check.py
```

Resolve a bundle command for manual use:

```bash
python3 scripts/skill-bundles-resolve.py /cv-pack
```

## Runtime Status

This layer is local-contract only. Turning these into real slash commands requires a separate runtime/router change and must follow gateway/runtime approval rules.
