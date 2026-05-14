# Config Schema First

Use this workflow before any gateway config change.

## Source of truth

- First-class tool: `gateway` with `config.schema.lookup`, `config.get`, `config.patch`, `config.apply`.
- Local docs for broader guidance:
  - `/usr/lib/node_modules/openclaw/docs/gateway/configuration.md`
  - `/usr/lib/node_modules/openclaw/docs/gateway/configuration-reference.md`

## Required flow

1. Confirm Ahmed explicitly requested the config/runtime change or maintenance window.
2. Run `openclaw --version` when the change is version-sensitive.
3. Inspect the relevant schema path with `gateway config.schema.lookup`.
4. Read only the relevant config subtree with `gateway config.get` when possible.
5. Prefer `gateway config.patch` for narrow changes.
6. Use `gateway config.apply` only when replacing full config is necessary.
7. Change one thing at a time.
8. Verify post-change behavior.

## Do not

- Do not edit live config files directly through shell when the gateway tool can do it.
- Do not guess field names or types.
- Do not weaken tool/gateway policy to reduce approval friction.
- Do not chain `openclaw gateway stop` and `openclaw gateway start` as restart substitute.

## Evidence to capture

- Schema path inspected.
- Config path changed.
- Whether hot reload or restart occurred.
- Verification result.
