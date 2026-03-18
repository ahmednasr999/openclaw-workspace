---
name: github-discovery
description: "GitHub radar: find high-quality, immediately useful repos - not hobby projects."
---

# GitHub Discovery Radar v2

Find repos that solve problems we ACTUALLY have. Not random AI projects.

## NON-NEGOTIABLE RULES
1. **Minimum 50 stars** for daily picks. No zero-star hobby projects.
2. **Immediately actionable** - we can install it, use it, or learn a pattern from it TODAY.
3. **"Quiet day" is valid output** - 0 picks is better than 5 useless picks.
4. **Never pad the list** - if only 2 repos are good, report 2.

## Search Strategy

### Our actual problems (search for THESE):
- LinkedIn automation / posting / scraping / analytics
- Notion API tools / integrations / utilities
- Job application automation / ATS optimization / resume parsing
- PDF generation / HTML-to-PDF / CV builders
- Browser automation anti-detection (Playwright, Puppeteer, Camoufox alternatives)
- Cron scheduling / task orchestration for AI agents
- Email automation (IMAP tools, email parsing)
- Google Jobs scraping / job board APIs
- Multi-agent coordination / shared state
- AI-powered content writing / LinkedIn content tools

### Search tiers (run ALL):

**Tier 1 - DAILY (top trending, high signal)**
Search GitHub for repos with 50+ stars created or significantly updated in last 7 days:
```bash
# Job search automation
gh search repos "job application automation" --stars ">=50" --sort stars --limit 5

# LinkedIn tools
gh search repos "linkedin api automation" --stars ">=50" --sort stars --limit 5

# Browser anti-detection
gh search repos "browser automation anti-detection" --stars ">=50" --sort stars --limit 5

# AI agent orchestration
gh search repos "ai agent orchestration" --stars ">=100" --sort stars --limit 5
```

**Tier 2 - WEEKLY (broader sweep)**
Run on Sundays only. Search for repos with 200+ stars updated in last 30 days:
```bash
gh search repos "notion api integration" --stars ">=200" --sort updated --limit 10
gh search repos "resume builder ats" --stars ">=100" --sort updated --limit 10
gh search repos "linkedin scraper" --stars ">=200" --sort updated --limit 10
gh search repos "pdf generation html" --stars ">=200" --sort updated --limit 10
gh search repos "multi agent coordination" --stars ">=200" --sort updated --limit 10
```

**Tier 3 - MONTHLY (top of category)**
Run on 1st of month. Find the best-in-class for each problem domain:
```bash
gh search repos "linkedin automation" --stars ">=1000" --sort stars --limit 10
gh search repos "job search automation" --stars ">=500" --sort stars --limit 10
gh search repos "notion integration" --stars ">=1000" --sort stars --limit 10
gh search repos "browser automation" --stars ">=5000" --sort stars --limit 10
gh search repos "ai agent framework" --stars ">=5000" --sort stars --limit 10
```

### Determine which tier to run:
```bash
DAY_OF_WEEK=$(date +%u)  # 1=Mon, 7=Sun
DAY_OF_MONTH=$(date +%d)

if [ "$DAY_OF_MONTH" = "01" ]; then
    echo "TIER: monthly (all 3 tiers)"
elif [ "$DAY_OF_WEEK" = "7" ]; then
    echo "TIER: weekly (tier 1 + 2)"
else
    echo "TIER: daily (tier 1 only)"
fi
```

## Scoring (must pass ALL):
1. **Stars >= 50** (daily) / **>= 200** (weekly) / **>= 1000** (monthly)
2. **Updated within 30 days** (not abandoned)
3. **Solves a problem we have** - map to specific problem from list above
4. **Has README with setup instructions** - no empty repos
5. **Written in Python, Node, Rust, or Go** - languages we can run

## Output Format

### Save to JSON for briefing:
```bash
cat > /tmp/github-discovery-$(date +%Y-%m-%d).json << 'EOF'
[
  {
    "name": "repo-name",
    "desc": "one-line description",
    "stars": 1500,
    "url": "https://github.com/owner/repo",
    "why": "Solves: [specific problem]. We can use it for: [specific use case].",
    "problem": "linkedin-automation",
    "tier": "daily"
  }
]
EOF
```

### Telegram report:
```
🔭 GitHub Discovery - [DATE] ([TIER] scan)

[X] repos scanned, [Y] passed quality bar

Top Picks:
1. [repo-name] (⭐ 1.5k) - [what it does]
   Solves: [our specific problem]
   → https://github.com/owner/repo

Quiet areas: [domains with no new finds]
```

If zero repos pass the bar:
```
🔭 GitHub Discovery - [DATE] ([TIER] scan)
Quiet day - nothing new above quality bar. No action needed.
```

## Error Handling
- gh CLI unavailable: use web_search as fallback
- GitHub rate limited: reduce search count, report partial results
- Zero results is FINE - never fabricate or lower the bar

## Quality Gates
- Every pick must map to a problem from "Our actual problems" list
- Every pick must have 50+ stars (daily minimum)
- Every pick must explain specific use case for us, not generic "interesting"
- README must exist and have setup instructions
