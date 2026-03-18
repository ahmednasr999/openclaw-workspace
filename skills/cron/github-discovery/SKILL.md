---
name: github-discovery
description: "Daily GitHub radar: find new trending repos in AI, automation, and OpenClaw ecosystem."
---

# GitHub Discovery Radar

Find NEW repos published or trending in the last 24 hours relevant to Ahmed's interests.

## Prerequisites
- GitHub API access (gh CLI or web search)
- Interests: AI agents, OpenClaw skills/plugins, automation frameworks, LLM tools

## Steps

### Step 1: Search trending repos
Search GitHub for repos created/updated in last 24h matching:
- "openclaw" OR "ai agent" OR "llm automation"
- Stars gained today >10
- Language: Python, TypeScript, JavaScript

### Step 2: Filter for relevance
Score each repo 1-10 on:
- Relevance to Ahmed's work (AI automation, OpenClaw)
- Quality (docs, stars, recent commits)
- Actionability (can we use this?)

### Step 3: Top picks
Select top 5 repos. For each:
- Name and description
- Why it matters
- Star count and age
- Link

### Step 4: Report
Send Telegram summary of top 5 discoveries.

## Error Handling
- If GitHub rate limited: Use cached results or web search fallback
- If no relevant repos: Report "Quiet day on GitHub - no new discoveries"

## Output Rules
- No em dashes. Hyphens only.
- Include clickable GitHub links
