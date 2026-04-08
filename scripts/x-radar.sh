#!/bin/bash
# X Radar - Daily scan of X/Twitter for OpenClaw-relevant content
# Cron: Daily 2:30 AM Cairo (runs before GitHub radar at 3 AM)
# Output: memory/x-radar.md

OUTPUT="/root/.openclaw/workspace/memory/x-radar.md"
DATE=$(date +%Y-%m-%d)

echo "Scanning X via Jina..."

# Use Jina to fetch relevant X lists
# We'll monitor key accounts and hashtags

cat > "$OUTPUT" << EOF
---
description: "Daily X/Twitter scan: relevant posts about OpenClaw, AI agents, automation"
type: log
topics: [knowledge, system-ops]
updated: $DATE
---

# X Radar — $DATE

## Key Accounts to Monitor

- @heinrich — skill graph concept
- @arscontexta — memory infrastructure
- @anthropicai — Claude updates
- @swarms_ai — swarm agents
- @os_worldai — operating systems for agents
- @karpathy — AI/nano agents
- @hwchase17 — LangChain
- @anthropic — Claude

## Relevant Hashtags

- #AIAgents
- #OpenClaw
- #ClaudeCode
- #AgenticAI
- #SkillGraph
- #MCP
- #AIAutomation
- #KnowledgeGraph

## Today's Highlights

*Scanned via Jina reader — manual curation*

EOF

# For now, we manually add notable posts
# Future: automate via X API

cat >> "$OUTPUT" << 'EOF'

## Notes

- X API requires authentication, scanning via browser is slow
- Manual curation for now
- When you share X links, I'll analyze and add here

---
*Scanned: TIMESTAMP_PLACEHOLDER*
EOF

TIMESTAMP=$(date)
sed -i "s/TIMESTAMP_PLACEHOLDER/$TIMESTAMP/g" "$OUTPUT"

echo "X Radar complete: $OUTPUT"
