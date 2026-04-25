# Doctor mismatch note - 2026-04-17

## Summary
Post-upgrade on OpenClaw 2026.4.15, `openclaw doctor --non-interactive` reports two likely false-positive / doctor-path issues while the live gateway runtime remains healthy:

1. `plugins.allow is empty` warning, even though `/root/.openclaw/openclaw.json` contains a populated `plugins.allow` array.
2. `Bundled plugin public surface access blocked for "memory-core" via memory-core/runtime-api.js: disabled in config`, even though `plugins.slots.memory = "none"` and `plugins.entries.memory-core.enabled = false` appear intentional.

## Live state confirmed
- Gateway healthy after upgrade
- OpenClaw version: 2026.4.15 (4850cdc)
- Repo branch: `update/v2026.4.15-local-fleet`
- `plugins.allow` in config file includes:
  - camofox-browser
  - telegram
  - slack
  - composio
  - lossless-claw
  - minimax
  - anthropic
  - openrouter
  - moonshot
  - openai
  - active-memory
- `plugins.slots.memory = "none"`
- `plugins.entries.memory-core.enabled = false`

## Safe cleanup already completed
Archived the 6 confirmed orphan transcript files under:
`/root/.openclaw/agents/main/sessions/*.jsonl.deleted.20260417T112422`

## Evidence collected
### 1) Config normalizer preserves allowlist
`src/plugins/config-normalization-shared.ts`
- `normalizePluginsConfigWithResolver()` maps `config?.allow` via `normalizeList(...)`
- no evidence that a populated allowlist is intentionally discarded in the normalizer

### 2) Warning emitter only fires if normalized allowlist length is zero
`src/plugins/loader.ts`
- `warnWhenAllowlistIsOpen(...)` returns early when `params.allow.length > 0`
- the warning therefore implies the loader received an empty normalized allowlist in that code path

### 3) Plugin loader can operate on `{}` when no config is passed
`src/plugins/loader.ts`
- `resolvePluginLoadCacheContext(options)` does:
  - `const cfg = applyTestPluginDefaults(options.config ?? {}, env)`
  - `const normalized = normalizePluginsConfig(cfg.plugins)`
- if a caller omits `options.config`, the loader normalizes an empty config object
- this is a plausible cause of the false `plugins.allow is empty` warning in some CLI/doctor path

### 4) Doctor memory search imports memory-core runtime facade directly
`src/commands/doctor-memory-search.ts`
- imports from `../plugin-sdk/memory-core-engine-runtime.js`
- `noteMemoryRecallHealth()` and `maybeRepairMemoryRecallHealth()` call:
  - `auditShortTermPromotionArtifacts(...)`
  - `auditDreamingArtifacts(...)`
  - `repairShortTermPromotionArtifacts(...)`
  - `repairDreamingArtifacts(...)`
- these are facade calls into memory-core runtime surface

### 5) memory-core runtime facade enforces plugin activation
`src/plugin-sdk/memory-core-engine-runtime.ts`
- uses `loadActivatedBundledPluginPublicSurfaceModuleSync({ dirName: "memory-core", artifactBasename: "runtime-api.js" })`
- when memory-core is intentionally not activated, this can throw the exact doctor error observed

## Working hypothesis
There are likely two doctor-path issues:

### A. Allowlist false-positive
A CLI/doctor plugin-loading path is likely invoking the plugin loader without supplying the resolved runtime config, causing `options.config ?? {}` to normalize to an empty plugin config and emit `plugins.allow is empty`.

### B. Memory-core false-positive
Doctor's memory-search contribution appears to call memory-core runtime facades unconditionally, even when memory is intentionally disabled (`plugins.slots.memory = "none"`, `memory-core.enabled = false`). That should probably be skipped or downgraded when memory is intentionally off.

## Recommendation
Do not change gateway config based on these doctor findings alone.

Recommended next engineering action:
1. Trace the exact doctor / CLI call path that reaches `loadOpenClawPluginCliRegistry(...)` or related loader entrypoints without a real config object.
2. Gate doctor memory-recall facade usage behind active memory-slot / plugin activation checks.
3. Re-run doctor after code fix, not after speculative config changes.

## Not recommended
- Do **not** blindly enable `memory-core`
- Do **not** edit `plugins.allow` just to silence this warning
- Do **not** change `plugins.slots.memory` from `none` without runtime evidence that memory should be active
