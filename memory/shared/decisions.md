# Decisions Log - Ahmed-Approved

<!-- CEO 2026-04-01 --> Dream Mode runs at 4 AM Cairo, Sun-Thu. Memory consolidation is automated.
<!-- CEO 2026-04-01 --> Verification Agent: sub-agents touching 3+ files get independent quality review. FAIL = fix, double FAIL = escalate to Ahmed.
<!-- CEO 2026-04-01 --> Tool Hooks system deployed (all tiers). Pre/post hooks, permissions, audit, AFK enforcement, rate limits, error recovery. Ahmed approved full implementation.
<!-- CEO 2026-04-01 --> Agent permissions: HR (no gateway/crons), CTO (no LinkedIn posting), CMO (no gateway config). CEO has full access.
<!-- CEO 2026-04-01 --> Startup prefetch: 4-phase cache-optimized boot sequence. Static → semi-static → dynamic → on-demand.
<!-- CEO 2026-04-01 --> Structured output mode for cron jobs and sub-agent returns (JSON schema in skills/tool-hooks/instructions/structured-output.md).
<!-- CEO 2026-04-01 --> SKIP list (Ahmed approved): Plugin system, remote transport, anti-distillation, KAIROS, fork subagent, coordinator mode. These are not needed.
<!-- CEO 2026-04-01 --> Tool concurrency declarations, wildcard permissions, tool presets deployed. Permissions now use pattern matching.
<!-- CEO 2026-04-01 --> Batch skill + stuck skill deployed. Agent summary service + AFK queue consumer integrated.
<!-- CEO 2026-04-01 --> FULL SKIP LIST (from actual source analysis): Bridge/IDE integration, plugin marketplace, voice system, LSP, x402 payments, vim mode, React/Ink UI, GrowthBook, remote sessions, PowerShell - all not applicable to our Telegram-native architecture.
