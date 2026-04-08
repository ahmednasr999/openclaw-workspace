#!/bin/bash
# GitHub Radar - Auto-scraping daily trending with relevance filter
# Cron: Daily 6 AM Cairo
# Output: memory/github-radar.md

OUTPUT="/root/.openclaw/workspace/memory/github-radar.md"
DATE=$(date +%Y-%m-%d)

echo "Fetching GitHub trending..."

# Keywords for relevance filter
KEYWORDS="agent|claude|openclaw|mcp|skill|automation|workflow|memory|context|skill-graph|swarm|orchestrat|contextdb|notebooklm|nanochat|tts|whisper|voice|transcription|browser|headless|scraper|api|llm|gpt|embedding|vector|rag|prompt|tool|execution|sandbox"

# Fetch raw HTML
HTML=$(curl -s "https://github.com/trending?since=weekly")

# Extract repos - clean patterns
REPOS=$(echo "$HTML" | grep -oP '(?<=/)[a-zA-Z0-9][a-zA-Z0-9-]*/[a-zA-Z0-9][a-zA-Z0-9-]+' | grep -vE '(stargazers|forks|issues|pulls|actions|settings|security|discussions|releases|commits|blob|tree|users|trending|browser|orgs|assets)' | sort -u | head -30)

# Filter relevant
RELEVANT=$(echo "$REPOS" | grep -iE "$KEYWORDS")

# Build output
cat > "$OUTPUT" << EOF
---
description: "Daily GitHub trending scan: auto-scraped repos with relevance filter for OpenClaw, AI agents, automation"
type: log
topics: [knowledge, system-ops]
updated: $DATE
---

# GitHub Radar — $DATE

## Relevant Repos (Auto-Filtered)

EOF

# Known descriptions (curated list for quality)
declare -A KNOWN_DESC
KNOWN_DESC["msitarzewski/agency-agents"]="Complete AI agency with specialized agents (frontend, Reddit, etc)"
KNOWN_DESC[" NousResearch/hermes-agent"]="Agent that grows with you"
KNOWN_DESC["teng-lin/notebooklm-py"]="Python API for NotebookLM (supports OpenClaw)"
KNOWN_DESC["volcengine/OpenViking"]="Context DB for AI Agents (mentions OpenClaw)"
KNOWN_DESC["bytedance/deer-flow"]="ByteDance SuperAgent harness"
KNOWN_DESC["karpathy/nanochat"]="Karpathy's minimal chat"
KNOWN_DESC["lightpanda-io/browser"]="Headless browser for AI"
KNOWN_DESC["promptfoo/promptfoo"]="Prompt testing and red teaming"
KNOWN_DESC["666ghj/MiroFish"]="Swarm Intelligence Engine"
KNOWN_DESC["666ghj/BettaFish"]="Multi-Agent sentiment analysis"

if [ -n "$RELEVANT" ]; then
    echo "$RELEVANT" | grep -vE "^$" | while read repo; do
        repo_clean=$(echo "$repo" | xargs)  # trim whitespace
        DESC="${KNOWN_DESC[$repo_clean]}"
        if [ -z "$DESC" ]; then
            DESC="Trending AI/automation project"
        fi
        echo "- **[$repo_clean](https://github.com/$repo_clean)**: $DESC" >> "$OUTPUT"
    done
else
    echo "No highly relevant repos found this week." >> "$OUTPUT"
fi

# Add top trending for context
cat >> "$OUTPUT" << 'EOF'

## Top Trending (All)

EOF

echo "$REPOS" | head -15 | grep -vE "^$" | while read repo; do
    echo "- $repo" >> "$OUTPUT"
done

cat >> "$OUTPUT" << EOF

## Filters

**Keywords:** agent, claude, openclaw, mcp, skill, automation, workflow, memory, context, notebooklm, browser, headless, sandbox

**Note:** SIE reads this file and generates integration recommendations.

---
*Scanned: $(date)*
EOF

echo "GitHub radar complete: $OUTPUT"
