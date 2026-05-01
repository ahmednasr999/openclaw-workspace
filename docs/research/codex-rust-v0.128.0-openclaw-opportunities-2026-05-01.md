# Codex rust-v0.128.0 - OpenClaw/NASR opportunity map

Source: `https://api.github.com/repos/openai/codex/releases/tags/rust-v0.128.0`  
Release: `0.128.0` / `rust-v0.128.0`  
Published: `2026-04-30T16:40:28Z`

## Decision

Do not install or change anything now.

Use this release as a pattern source for OpenClaw/NASR governance, especially durable goals, explicit permission profiles, external session handoffs, and multi-agent controls. The useful move is selective adoption into our workflows, not importing Codex behavior wholesale.

## Why it matters

Codex is moving in the same direction we want OpenClaw/NASR to move: from prompt-response chat toward durable, inspectable, permissioned operating workflows.

The release is useful because it validates several directions we already started:
- goal-oriented execution instead of loose task chatter
- explicit safety/permission profiles
- better resume/session continuity
- structured multi-agent controls
- plugin/skill packaging that keeps workflows reusable

## Feature-to-opportunity map

| Codex 0.128.0 item | What it signals | OpenClaw/NASR opportunity | Priority |
|---|---|---|---|
| Persisted `/goal` workflows | Durable objectives with pause/resume/clear and runtime continuation | Design an OpenClaw/NASR "goal contract" for long-running workstreams: objective, success criteria, owner, evidence, pause/resume state, stop rule | High |
| Expanded permission profiles | Safer execution through named trust/sandbox profiles | Map our approval/tool boundaries into reusable profiles: read-only, workspace-write, external-write, gateway-risk, public-posting | High |
| External agent session import | Agent-to-agent handoff becomes a first-class workflow | Improve handoff templates between main, CTO, CMO, HR, and coding sub-agents, including evidence and unresolved risk | Medium-high |
| MultiAgentV2 configuration | Multi-agent work needs caps, wait controls, and root/subagent hints | Add explicit sub-agent caps and wait/timeout guidance to dispatch patterns, especially for research and coding-agent sessions | Medium-high |
| Plugin marketplace/cache/uninstall/hooks | Skills/plugins are moving toward packageable workflows | Keep our skills selective and owner-scoped. Avoid global imports. Use plugin ideas only where they reduce repeated manual work | Medium |
| Resume/interruption fixes | Reliability of interrupted long tasks is core agent infrastructure | Add resume/interruption checks to CTO runtime baselines after updates | Medium |
| `codex update`, keymaps, `/statusline`, `/title` | Better operator feedback and live control | Consider small OpenClaw status/title conventions for long-running sub-agent sessions, but only if it reduces confusion | Low-medium |
| Bundled OpenAI docs skill updates for GPT-5.5 | Model/platform docs are becoming operational dependencies | Keep source-driven rules for model/API/config work. Never rely on stale model assumptions | Medium |

## Release evidence extracted

### New Features
- Added persisted `/goal` workflows with app-server APIs, model tools, runtime continuation, and TUI controls for create, pause, resume, and clear. (#18073, #18074, #18075, #18076, #18077, #20082)
- Added `codex update`, configurable TUI keymaps, plan-mode nudges, action-required terminal titles, and active-turn `/statusline` and `/title` edits. (#19933, #18593, #19901, #18372, #19917)
- Expanded permission profiles with built-in defaults, sandbox CLI profile selection, cwd controls, and active-profile metadata for clients. (#19900, #20117, #20118, #20095)
- Improved plugin workflows with marketplace installation, remote bundle caching, remote uninstall, plugin-bundled hooks, hook enablement state, and external-agent config import. (#18704, #19914, #19456, #19705, #19840, #19949)
- Added external agent session import, including background imports and imported-session title handling. (#19895, #20284, #20261)
- Made MultiAgentV2 configuration more explicit with thread caps, wait-time controls, root/subagent hints, and v2-specific depth handling. (#19360, #19792, #19805, #20052, #20180)

### Bug Fixes
- Fixed several resume and interruption issues, including stale interrupt hangs, persisted provider restoration, large remote resume responses, and slow filtered resume lists. (#18392, #19287, #19920, #19591)
- Improved TUI reliability around terminal resize reflow, markdown list spacing, slash-command popup layout, keyboard cleanup, shell-mode escape, and working status updates. (#18575, #19706, #19511, #19625, #19986, #19939)
- Hardened managed network behavior for deferred denials, proxy bypass defaults, resolved target checks, IPv6 host matching, and `git -C` approval handling. (#19184, #20002, #19999, #19995, #20085)
- Fixed Windows sandbox and PTY edge cases, including pseudoconsole startup, elevated runner process handling, core shell environment inheritance, and named-pipe validation. (#20042, #19211, #20089, #19283)
- Fixed Bedrock model support for `apply_patch`, GPT-5.4 reasoning levels, and updated Bedrock GPT-5.4 endpoint/model metadata. (#19416, #19461, #20109)
- Fixed MCP/plugin edge cases around stdio server cleanup, plugin MCP approval persistence, and custom MCP metadata isolation. (#19753, #19537, #19836, #19875)

### Documentation
- Updated the bundled OpenAI Docs skill for GPT-5.5, `gpt-image-2`, and clearer upgrade guidance. (#19407, #19443, #19422)
- Clarified contributor-facing docs, including the PR template, Rust async trait guidance, and README wording. (#19912, #20242, #19514)
- Added a checked-in `codex-core` public API listing and a ThreadManager sample crate. (#20243, #20141)

### Chores
- Published `codex-app-server` release artifacts, stopped publishing GNU Linux binaries, and increased release workflow timeouts. (#19447, #19445, #20271, #20343)
- Added Codex-pinned versioning for the Python app-server SDK package. (#18996)
- Deprecated `--full-auto` while steering users toward explicit permission profiles and trust flows. (#20133)
- Stabilized CI and release plumbing with Bazel setup migration, release smoke-test pinning, and updated workflow pins/timeouts. (#19851, #19854, #19472, #19609)

## Recommended adoption sequence

### 1. Create a NASR goal contract

Build a compact template, not a big system:
- goal name
- why it matters to Ahmed
- owner agent
- success criteria
- verification evidence
- current state
- pause/resume rule
- stop/escalation rule

Best initial use cases:
- OpenClaw runtime stabilization
- JobZoom protected lane monitoring
- LinkedIn content production quality loop
- executive role search pipeline

### 2. Define permission profile language

Translate OpenClaw/NASR approval boundaries into named operating modes:
- `read-only-inspection`
- `workspace-write-docs`
- `local-code-change`
- `gateway-risk`
- `external-write`
- `public-posting`

This should stay as governance language first. Do not change tool policy until it has been proven useful.

### 3. Improve cross-agent handoffs

Update handoff/checklist patterns so imported or delegated sessions always include:
- objective
- current state
- source evidence
- files changed
- verification run
- unresolved risks
- next safe action

### 4. Add bounded multi-agent controls

For multi-agent research or coding:
- define max agents
- define wait timeout
- define evidence requirements
- forbid success claims without inspected artifacts
- require a synthesis owner

### 5. Watch Codex app-server, but do not adopt yet

The release includes app-server/API direction, but adoption should wait until there is a clear OpenClaw integration benefit. For now, treat it as a signal, not an implementation target.

## Explicit non-goals

- Do not install Codex on the VPS just because this release exists.
- Do not replace OpenClaw governance with Codex concepts.
- Do not import plugin/hook behavior wholesale.
- Do not add more prompt text unless it removes a real repeated failure.
- Do not touch gateway config or runtime patches for this research item.

## Suggested next experiment

Create one tiny `goal contract` pilot for an existing standing workstream, likely OpenClaw runtime stabilization. The pilot should be a document/checklist first, not an automation.

Success condition: the goal contract makes the next update/leak event easier to resume and verify without adding noise.
