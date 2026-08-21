#!/bin/bash
# Morning Brief - Daily Job Pipeline Summary
# Runs at 6 AM UTC (8 AM Cairo)

if [ -z "${TAVILY_API_KEY:-}" ]; then
    export TAVILY_API_KEY="$(jq -r '.openclaw.skills.entries.tavily.apiKey // empty' /root/.openclaw/config/secrets.json)"
fi
DATE=$(date +%Y-%m-%d)
TIME=$(date +"%I:%M %p")

echo "=== Morning Brief - $DATE $TIME ===" > /tmp/morning-brief.md
echo "" >> /tmp/morning-brief.md

# Claude 2x Off-Peak Reminder (until March 27, 2026)
echo "## Claude 2x Usage Reminder" >> /tmp/morning-brief.md
CURRENT_EPOCH=$(date +%s)
END_EPOCH=$(date -d "2026-03-27" +%s 2>/dev/null || echo "1773772799")
if [ "$CURRENT_EPOCH" -lt "$END_EPOCH" ]; then
    echo "🎯 Claude 2x off-peak until March 27!" >> /tmp/morning-brief.md
    echo "- Off-peak: 8 PM - 2 PM Cairo (outside US peak)" >> /tmp/morning-brief.md
    echo "- Schedule heavy work (CVs, analysis) during off-peak" >> /tmp/morning-brief.md
fi
echo "" >> /tmp/morning-brief.md

# 0. Open-work Resolver: only progress, intervention, and verified closures.
RESOLVER_BRIEF="/root/.openclaw/workspace/reports/open-work-resolver/briefing.json"
if [ -s "$RESOLVER_BRIEF" ]; then
    RESOLVER_LINES=$(jq -r '
      (.progress[]? | "- Progress: \(.title) - \(.progress). \(.next_action)"),
      (.intervention[]? | "- Intervention: \(.title) - \(.progress). \(.blocker // .next_action)"),
      (.closures[]? | "- Closed: \(.title) - \(.progress). Verified closure recorded.")
    ' "$RESOLVER_BRIEF" 2>/dev/null)
    if [ -n "$RESOLVER_LINES" ]; then
        echo "## Open Work" >> /tmp/morning-brief.md
        echo "$RESOLVER_LINES" >> /tmp/morning-brief.md
        echo "" >> /tmp/morning-brief.md
    fi
fi

# 1. Job Radar Results
echo "## Job Radar (from Tavily)" >> /tmp/morning-brief.md
SEARCH_RESULT=$(node /root/.openclaw/workspace/skills/tavily-search/scripts/search.mjs "VP Director PMO Digital Transformation healthcare UAE Dubai Saudi 2026" -n 5 2>&1)
echo "$SEARCH_RESULT" >> /tmp/morning-brief.md
echo "" >> /tmp/morning-brief.md

# 2. Gmail career-monitor health. Actionable mail is alerted by the silent sentinel.
echo "## Gmail - Career Monitor" >> /tmp/morning-brief.md
if systemctl --user is-active --quiet hr-career-sentinel.service; then
    echo "- Real-time career monitor: active" >> /tmp/morning-brief.md
else
    echo "- Real-time career monitor: unavailable - scheduled reconciliation remains the fallback" >> /tmp/morning-brief.md
fi
if systemctl --user is-enabled --quiet hr-career-sentinel-reconcile.timer \
    && systemctl --user is-active --quiet hr-career-sentinel-reconcile.timer; then
    echo "- Scheduled reconciliation: active at 08:00, 12:00, 16:00, and 20:00 Cairo" >> /tmp/morning-brief.md
else
    echo "- Scheduled reconciliation: unavailable - investigate Gmail fallback coverage" >> /tmp/morning-brief.md
fi
echo "" >> /tmp/morning-brief.md

# 3. Calendar - Today's events (graceful failure for gog v0.12.0 bug)
echo "## Calendar - Today's Events" >> /tmp/morning-brief.md
CAL_RESULT=$(GOG_KEYRING_PASSWORD="" /usr/local/bin/gog calendar events ls --today 2>&1)
if echo "$CAL_RESULT" | grep -q "404\|notFound\|error"; then
    echo "*Calendar API unavailable (gog v0.12.0 bug - tracking fix)*" >> /tmp/morning-brief.md
else
    echo "$CAL_RESULT" | head -15 >> /tmp/morning-brief.md
fi
echo "" >> /tmp/morning-brief.md

# 4. Save to memory
cat /tmp/morning-brief.md >> /root/.openclaw/workspace/memory/morning-briefs.md

# 5. Push to GitHub
cd /root/.openclaw/workspace
git add memory/morning-briefs.md
git commit -m "Morning brief - $DATE" >/dev/null 2>&1
git push >/dev/null 2>&1

echo "Morning brief complete - $DATE"
