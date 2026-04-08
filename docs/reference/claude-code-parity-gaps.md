# Claude Code Architecture - Parity Gap Reference
# Sources: aired.sh report + claw-code PARITY.md + 777genius actual source (512K lines)
# Last updated: 2026-04-01
# Purpose: Reference for future architectural decisions

## Our Status vs Claude Code (FINAL - All Sources Analyzed)

### BUILT - Full Parity or Better
| System | Claude Code | NASR/OpenClaw | Source |
|--------|------------|---------------|--------|
| Tool Hooks (Pre/Post) | Built-in hook system | ✅ config/tool-hooks.yaml + 10-step workflow | claw-code |
| Permission Context | deny_names + deny_prefixes | ✅ Wildcard patterns (prefix, path, command scopes) | claw-code + actual source |
| Tool Concurrency | isConcurrencySafe() + isReadOnly() | ✅ tool_properties in hooks config | actual source |
| Tool Presets | Tool groups for different contexts | ✅ 6 presets (full/build/content/research/review/afk) | actual source |
| Team Memory Sync | Shared memory across agents | ✅ memory/shared/ (active-context, decisions, blockers) | aired.sh |
| Session Resume | By ID with context replay | ✅ OpenClaw native | claw-code |
| Compact/Context Mgmt | Compact service + token counting | ✅ LCM + cache-optimized prefetch | claw-code |
| Startup Prefetch | Parallel prefetch of MDM/keychain/API | ✅ 4-phase cache-optimized boot | claw-code |
| Audit Trail | Not explicit in CC | ✅ audit-log.jsonl + daily-actions.jsonl | claw-code |
| Error Recovery | Retry with backoff | ✅ Retry + alternative + escalation + full logging | claw-code |
| Batch Operations | bundled batch skill | ✅ skills/batch/ with chunking + checkpoints | actual source |
| Get Unstuck | bundled stuck skill | ✅ skills/stuck/ (7-step protocol, 5 min max) | actual source |
| Agent Summary | src/services/AgentSummary/ | ✅ Auto-generated JSON summaries | actual source |
| Structured Output | SyntheticOutputTool | ✅ JSON schema for cron/sub-agent returns | actual source |
| Verify/VerifyContent | Two separate verify skills | ✅ skills/verify/ (combined, split when triggered) | actual source |

### BUILT - Our Innovations (Not in Claude Code)
| System | What It Does | Why CC Doesn't Have It |
|--------|-------------|----------------------|
| Dream Mode | 4AM memory consolidation cron | CC has autoDream but it's background ideation, not consolidation |
| Effort Classification | 4-tier system (Low→Max) with model/verify/docs gates | CC has no effort-based gating |
| AFK/Fast Mode | Enforced overnight queue + lightweight cron mode | CC has no time-based mode switching |
| C-Suite Topology | Role-based multi-agent with topic routing | CC has generic coordinator, not domain-specialized |
| Ontology Knowledge Graph | Typed entity/relation store for structured memory | CC uses flat CLAUDE.md files |
| Task Budget Caps | Time limits per task type with hard kills | CC has no budget enforcement |
| Anti-Lazy Delegation | Spawn briefs require "do the work, don't return instructions" | CC spawns are unguarded |
| False-Claims Mitigation | "Never say done if output shows errors" | CC has no output verification |
| AFK Queue Consumer | Morning briefing processes overnight queue with approve/skip | CC has no queued action review |

### SKIPPED - Not Applicable
| System | Why Skip |
|--------|----------|
| Bridge/IDE Integration (src/bridge/) | Telegram-native, not IDE-native |
| Plugin Marketplace (src/plugins/) | Skills + ClawHub cover our needs |
| Voice System (src/voice/) | Chat-native, Telegram handles voice differently |
| LSP Integration (src/tools/LSPTool/) | We use gh, grep, direct reads |
| x402 Payment Protocol (src/services/x402/) | We don't charge for tool usage |
| Vim Mode (src/vim/) | Terminal UI feature, we're chat-based |
| React/Ink UI (src/components/) | Our UI is Telegram |
| GrowthBook Feature Flags | Effort tiers + mode flags suffice |
| Remote Sessions (src/remote/) | OpenClaw native session management |
| PowerShell (src/tools/PowerShellTool/) | Linux VPS only |
| KAIROS Autonomous Mode | Too dangerous without sandbox |
| Fork Subagent | sessions_spawn sufficient |
| Anti-Distillation | Not a public-facing model |
| Undercover Mode | We don't contribute to OSS repos |

### DEFERRED - Build When Triggered
| System | Trigger |
|--------|---------|
| PromptSuggestion (follow-up suggestions) | When Ahmed frequently follows predictable next steps |
| Tool Prompt Injection (per-tool system prompt) | When agents forget tool-specific rules |
| Split verify/verifyContent | When verification produces false positives on content |
| Session Memory vs Persistent | When Dream Mode over-promotes ephemeral items |

## Summary
- **28 items built** (21 in first pass + 7 in second pass)
- **4 items deferred** (build when triggered)
- **14 items skipped** (not applicable)
- **9 unique innovations** not found in Claude Code
- Total extraction: complete. Nothing left on the table.
