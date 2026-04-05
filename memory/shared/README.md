# Shared Memory - Cross-Agent Knowledge Store

This directory contains knowledge that ALL C-Suite agents need access to. It replaces the pattern of four agents reading/writing the same files without coordination.

## Rules

### What goes here (shared)
- Active decisions that affect multiple agents (e.g., "Ahmed is focusing on healthcare roles this week")
- Cross-agent context (e.g., "HR submitted application to X, CMO should not post about competitor Y")
- Shared preferences confirmed by Ahmed
- Active campaign briefs (job search focus, content themes, outreach priorities)

### What stays private (agent workspace)
- Agent-specific drafts and work-in-progress
- Agent-specific logs and reports
- Intermediate tool outputs
- Temporary files

### Write Rules
- Any agent can APPEND to shared files
- Only CEO agent can MODIFY or DELETE shared entries
- Each entry must include: agent name, date, content
- Format: `<!-- [AGENT] YYYY-MM-DD --> content`

### Files
- `active-context.md` - Current priorities, active campaigns, temporary focus areas
- `decisions.md` - Decisions made by Ahmed that affect all agents
- `blockers.md` - Cross-agent blockers and dependencies
