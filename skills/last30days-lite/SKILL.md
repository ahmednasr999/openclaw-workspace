---
name: last30days
description: Research any topic across Reddit, X/Twitter, and the web from the last 30 days. Uses Tavily for search.
metadata: {"openclaw":{"emoji":"📅"}}
---

# last30days 📅

Research any topic using recent (last 30 days) discussions. Returns synthesized insights.

## Requirements
- Tavily API (already configured in OpenClaw)
- No extra API keys needed

## Usage

When user asks "what's trending in [topic]" or "/last30days [topic]":

### Step 1: Search via Tavily

Use this curl command (Tavily API key already set in env):
```bash
curl -s "https://api.tavily.com/search" -H "Content-Type: application/json" -d '{"api_key":"'"$TAVILY_API_KEY"'","query":"[topic] March 2026","max_results":10}'
```

Or use exec to run it directly.

### Step 2: Synthesize
Combine findings into:
1. **Key patterns** - What's actually working?
2. **Key sources** - Where info came from

## Output Format

```markdown
## 📅 Last 30 Days: [Topic]

### What's Trending
- [Pattern 1]
- [Pattern 2]

### Sources
- [URL] - [description]
```
