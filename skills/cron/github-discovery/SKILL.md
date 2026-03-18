---
name: github-discovery
description: "Daily GitHub radar: find new trending repos in AI, automation, and OpenClaw ecosystem."
---

# GitHub Discovery Radar

Find new repos published or trending in the last 24 hours relevant to Ahmed's work.

## Prerequisites
- GitHub CLI (gh) or web search access

## Steps

### Step 1: Search trending repos
```bash
# Search GitHub for recent relevant repos
echo "=== AI Agent repos (last 24h) ==="
gh search repos "ai agent" --created ">$(date -d '1 day ago' +%Y-%m-%d)" --sort stars --limit 5 2>/dev/null || echo "gh CLI not available, using web search"

echo ""
echo "=== OpenClaw ecosystem ==="
gh search repos "openclaw" --sort updated --limit 5 2>/dev/null || echo "Using web search fallback"

echo ""
echo "=== LLM tools ==="
gh search repos "llm automation tool" --created ">$(date -d '1 day ago' +%Y-%m-%d)" --sort stars --limit 5 2>/dev/null || echo "Using web search fallback"
```
If gh CLI unavailable, use web_search tool as fallback.

### Step 4: Save results for briefing
After collecting results, save to JSON for the morning briefing:
```bash
# Save to /tmp/github-discovery-YYYY-MM-DD.json
cat > /tmp/github-discovery-$(date +%Y-%m-%d).json << 'EOF'
[
  {"name": "repo-name", "desc": "one-line description", "stars": 0, "url": "https://github.com/...", "why": "relevance to Ahmed's work"}
]
EOF
```
This file is read by the morning briefing orchestrator.

### Step 2: Filter for relevance
Score each repo 1-10:
- Relevance to Ahmed's work (AI automation, OpenClaw, PMO tools)
- Quality (documentation, stars, recent activity)
- Actionability (can we use or learn from this?)

### Step 3: Top picks
Select top 5 repos. For each provide:
- Name, description, star count
- Why it matters to Ahmed
- Direct GitHub link

### Step 4: Report
```
GitHub Discovery - [DATE]

[X] repos scanned, [Y] relevant

Top Picks:
1. [repo-name] - [stars] stars - [one line why it matters]
   https://github.com/[owner/repo]
2. ...
```

## Error Handling
- If GitHub rate limited: Use web search fallback
- If no relevant repos: Report "Quiet day - no new discoveries matching our domains"
- If gh CLI unavailable: Use web search exclusively

## Quality Gates
- Must search at least 3 domain areas
- Top picks must have direct GitHub links
- Each pick must explain relevance to Ahmed's work specifically

## Output Rules
- No em dashes. Hyphens only.
- Include clickable GitHub URLs
- "Quiet day" is valid output - don't fabricate discoveries
