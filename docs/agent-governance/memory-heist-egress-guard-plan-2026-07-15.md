# Memory Heist Egress Guard Plan

## Plan Metadata

- Status: ready
- Owner: NASR
- Planned at: commit `b9dd6ae9e` on `2026-07-15`
- Depends on: OpenClaw 2026.7.1 plugin hooks and the approved Memory Heist defense request

> **Executor contract:** Read the full plan before editing. Stay inside scope, run each verification gate, and report evidence. If a stop condition is met or reality conflicts with the plan, stop and report the mismatch instead of improvising.

> **Drift check:** `git diff --stat b9dd6ae9e..HEAD -- plugins/memory-heist-guard docs/agent-governance/memory-heist-egress-guard-plan-2026-07-15.md reports/security/memory-heist-egress-guard-2026-07-15.md`
> If an in-scope path changed, compare current source with the evidence anchors below. Refresh or supersede the plan before execution when the intended change or verification no longer matches.

## Objective

- Target outcome: add a fail-closed OpenClaw hook that denies native web navigation to URLs that were neither supplied in the current user prompt nor returned as structured `web_search` results.
- User-visible success condition: a Memory Heist page may be fetched once when Ahmed supplies its URL, but links or character-by-character exfiltration URLs derived from that page are blocked before network access.
- Why this matters: untrusted page content must not gain authority to turn private memory or conversation data into attacker-visible outbound URL paths.

## Evidence And Current State

- Source anchors: `/usr/lib/node_modules/openclaw/dist/openclaw-tools-CIBcX9Ku.js:14002` - built-in `web_fetch` accepts a model-supplied URL and executes it after SSRF checks; `/usr/lib/node_modules/openclaw/dist/hook-types-DQ9eTy2x.d.ts:705` - `before_tool_call` receives host-authoritative tool name, params, and run identity; `/usr/lib/node_modules/openclaw/dist/hook-types-DQ9eTy2x.d.ts:738` - `after_tool_call` exposes structured search results for bounded provenance promotion.
- Existing convention to follow: `/usr/lib/node_modules/openclaw/docs/plugins/building-plugins.md:86` - native plugins declare a manifest and startup activation; `/usr/lib/node_modules/openclaw/docs/tools/plugin.md:181` - local plugins require explicit allowlisting and enablement.
- Reproduction or baseline: the live Gateway is healthy, `web_fetch` has SSRF and untrusted-content wrapping, but no loaded plugin owns a `before_tool_call` egress-provenance guard.
- Raw evidence to preserve: current Gateway probe, plugin inventory, exact policy tests, runtime hook inspection, and post-reload Gateway health.

## Scope

- In scope: exact URL provenance for `web_fetch` and explicit browser `open`/`navigate`/`goto` actions; structured `web_search` result promotion; bounded in-memory run state; deterministic Memory Heist regression fixtures; plugin installation and live hook verification.
- Files likely touched: `plugins/memory-heist-guard/*`, this plan, `reports/security/memory-heist-egress-guard-2026-07-15.md`, and the dated memory note.
- Do not touch: OpenClaw dist bundles, model routing, active-memory behavior, Telegram delivery, unrelated plugins, or existing dirty workspace changes.
- Non-goals: intercepting arbitrary subprocess-created sockets, browser click navigation without a destination URL in tool params, or creating a general outbound proxy.

## Authority And Safety

- Permission profile: runtime-change
- Approval boundary: Ahmed's `Go ahead` authorizes the named Memory Heist regression guard, local plugin install/enablement, and the controlled Gateway reload needed to activate it; no public write, credential change, OpenClaw update, or unrelated config change is authorized.
- Rollback path: disable/uninstall `memory-heist-guard`, restore the pre-install OpenClaw config backup, restart through the approved maintenance lane, and verify the prior plugin inventory and Gateway health.
- External/public/credential/paid/runtime action involved: yes, a local plugin activation and Gateway reload only.

## Owner And Helpers

- Owning session/agent: NASR main Telegram session
- Helpers, if explicitly permitted: no helpers permitted or required
- Independent assignment and expected evidence for each helper: local owner performs both mandated review passes with distinct correctness and adversarial-safety mandates
- Maximum concurrency: 1

## Ordered Implementation Steps

### Step 1: Build the deterministic provenance policy and regression suite

- Files: `plugins/memory-heist-guard/policy.js`, `plugins/memory-heist-guard/index.js`, `plugins/memory-heist-guard/test.mjs`, `plugins/memory-heist-guard/package.json`, `plugins/memory-heist-guard/openclaw.plugin.json`, `plugins/memory-heist-guard/README.md`
- Change: capture exact prompt URLs per run, promote only structured URL fields from successful `web_search` results, and block unproven web fetch or explicit browser navigation URLs.
- Preserve: legitimate exact user URLs, exact search-result URLs, SSRF controls, and all non-navigation tool calls.
- Verify command/check: `node --test plugins/memory-heist-guard/test.mjs`, a direct ESM module-contract import, and JSON parsing of both manifests.
- Expected result: all Memory Heist regression cases pass, the hook plugin exposes the expected id/register contract, and both manifests parse.

### Step 2: Install and activate the local plugin safely

- Files: OpenClaw managed plugin install metadata and config only through `openclaw plugins install --link`.
- Change: add `memory-heist-guard` to the plugin allowlist and enable it, after backing up the live config.
- Preserve: all existing plugin entries, slots, model routing, credentials, and channel settings.
- Verify command/check: `openclaw config validate && openclaw plugins inspect memory-heist-guard --json`
- Expected result: valid config and cold registry metadata showing the intended local plugin and startup activation.

### Step 3: Reload and prove the live hook behavior

- Files: no additional source files; live Gateway process only.
- Change: use the approved controlled restart path so the startup hook loads.
- Preserve: Gateway port, Telegram connectivity, model selection, and all existing runtime patches.
- Verify command/check: `openclaw plugins inspect memory-heist-guard --runtime --json`, `python3 scripts/check-openclaw-runtime-patches.py`, `openclaw gateway probe --json`, plus a source-blind hook contract probe.
- Expected result: the runtime reports the guard's hooks, the exact supplied URL is allowed, derived character/query/path variants are blocked before tool execution, all prior runtime patches remain green, and Gateway/Telegram stay healthy.

### Step 4: Complete high-risk reviews and closeout evidence

- Files: `reports/security/memory-heist-egress-guard-2026-07-15.md`, `memory/2026-07-15.md`
- Change: record correctness review, adversarial-safety review, focused tests, runtime proof, rollback, and residual boundaries; run structured autoreview on the scoped diff.
- Preserve: unrelated dirty files and prior daily-note entries.
- Verify command/check: `skills/autoreview/scripts/autoreview --mode local --engine codex --model gpt-5.6-sol --thinking high`, `python3 scripts/check-high-risk-engineering-record.py reports/security/memory-heist-egress-guard-2026-07-15.md`, and `python3 scripts/check-agentic-engineering-plan.py docs/agent-governance/memory-heist-egress-guard-plan-2026-07-15.md`
- Expected result: no accepted actionable findings, both review mandates are independently recorded, and both validators pass.

## Test Plan

- Existing tests to run: OpenClaw config validation, plugin validation/inspection, Gateway probe, and the runtime patch checker.
- New or changed tests: direct supplied URL allow; fragment normalization; path/query/character-by-character denial; private-data URL denial; structured search-result allow; search-snippet and fetched-page link non-promotion; browser explicit-navigation denial; missing-run fail closed; bounded state cleanup.
- Original reproduction after implementation: supply one benign attacker-controlled page URL, simulate its content instructing successive `/N`, `/NA`, and query-string fetches, and prove every derived request is denied while the original exact URL remains allowed.
- Actual artifact or behavior to inspect: loaded plugin hook inventory and a source-blind policy contract probe executed against the built plugin entry.

## Stop Conditions

- An evidence anchor or in-scope file has materially drifted.
- A required dependency or approval is missing.
- A verification gate fails twice after bounded repair.
- The smallest credible fix requires out-of-scope files or a new external/runtime/destructive action.

## Done Criteria

- [ ] Every ordered step completed or explicitly skipped with evidence.
- [ ] Focused tests and original reproduction pass.
- [ ] Actual user-visible or operational outcome inspected.
- [ ] Changed files remain inside scope.
- [ ] Accepted review findings repaired and reverified.
- [ ] Remaining risk and rollback evidence recorded.

## Review Handoff

- Diff base and target: commit `b9dd6ae9e` to the scoped local plugin and evidence files
- Reviewer focus: URL canonicalization, provenance promotion boundaries, run-state isolation, fail-closed behavior, memory bounds, hook lifecycle, and false-positive impact on ordinary browsing
- Known trade-offs: page-discovered links require `web_search` or a new user-supplied exact URL; browser clicks and arbitrary subprocess egress remain outside this guard
- Deliberately deferred work: host-wide egress proxying and browser-click destination interception
