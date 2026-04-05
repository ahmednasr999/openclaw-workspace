# Active Context - Cross-Agent Awareness

<!-- CEO 2026-04-01 --> Dream Mode (memory consolidation) and Verification Agent deployed. All agents should be aware these exist.
<!-- CEO 2026-04-01 --> Sub-agent spawn briefs now require anti-lazy-delegation, false-claims mitigation, and assertiveness lines.
<!-- CEO 2026-04-01 --> TOOL HOOKS DEPLOYED. All agents MUST follow config/tool-hooks.yaml and config/tool-permissions.yaml. Read skills/tool-hooks/SKILL.md for the 10-step enforcement workflow. Pre-check every tool call. Post-log every external action.
<!-- CEO 2026-04-01 --> Per-agent permissions active: HR cannot touch gateway/crons. CTO cannot post to LinkedIn. CMO cannot modify gateway config. Escalate to CEO if genuinely needed.
<!-- CEO 2026-04-01 --> AFK enforcement live: midnight-6AM Cairo, blocked actions queue to memory/agents/afk-queue.jsonl. Morning briefing presents queue.
<!-- CEO 2026-04-01 --> Startup prefetch: 4-phase cache-optimized load order in AGENTS.md. Static first, dynamic last.
<!-- CEO 2026-04-01 --> Error recovery protocol: retry transient errors once, try alternatives, then report. Never paraphrase errors. See skills/tool-hooks/instructions/error-recovery.md.
<!-- CEO 2026-04-01 --> Session handoff enforcement: 9-section template mandatory for all work sessions. Auto-generate from audit log if agent crashes.
<!-- CEO 2026-04-01 --> TOOL CONCURRENCY: Check tool_properties before parallel execution. concurrent:true = safe to parallelize. concurrent:false = serialize. Two writes to same target = always serialize.
<!-- CEO 2026-04-01 --> TOOL PRESETS: Agents have default presets. CEO=full, CTO=build, CMO=content. AFK mode auto-switches to "afk" preset. Tools not in preset are DENIED.
<!-- CEO 2026-04-01 --> WILDCARD PERMISSIONS: Patterns replace flat deny lists. Prefix wildcards (LINKEDIN_*), path scopes (edit:memory/*.md), command scopes (exec:rm -rf *). Allow checked before deny.
<!-- CEO 2026-04-01 --> BATCH SKILL (skills/batch/): Standardized bulk operations with chunking, checkpoints, rate-limit awareness, error collection.
<!-- CEO 2026-04-01 --> STUCK SKILL (skills/stuck/): 7-step get-unstuck protocol. Try alternatives different in kind, search memory, decompose, then escalate. Max 5 minutes.
<!-- CEO 2026-04-01 --> AGENT SUMMARY: Auto-generated after every sub-agent completes. JSON schema with status, outputs, files, decisions, follow-ups. Logged to audit + daily-actions.
<!-- CEO 2026-04-01 --> AFK QUEUE CONSUMER: Morning briefing now processes overnight queue. Approve/modify/skip buttons per item. Auto-approve for pre-approved items.
