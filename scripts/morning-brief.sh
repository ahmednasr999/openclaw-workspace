#!/bin/bash
# Morning Brief - Daily Job Pipeline Summary
# Runs at 6 AM UTC (8 AM Cairo)

export TAVILY_API_KEY="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"
DATE=$(date +%Y-%m-%d)
TIME=$(date +"%I:%M %p")

echo "=== Morning Brief - $DATE $TIME ===" > /tmp/morning-brief.md
echo "" >> /tmp/morning-brief.md

# 1. Job Radar Results
echo "## Job Radar (from Tavily)" >> /tmp/morning-brief.md
SEARCH_RESULT=$(node /root/.openclaw/workspace/skills/tavily-search/scripts/search.mjs "VP Director PMO Digital Transformation healthcare UAE Dubai February 2026" -n 5 2>&1)
echo "$SEARCH_RESULT" >> /tmp/morning-brief.md
echo "" >> /tmp/morning-b 2. Gmailrief.md

# - New job-related emails
echo "## Gmail - New Opportunities" >> /tmp/morning-brief.md
node /root/.openclaw/workspace/scripts/gmail-scan.js >> /tmp/morning-brief.md 2>&1
echo "" >> /tmp/morning-brief.md

# 3. Save to memory
cat /tmp/morning-brief.md >> /root/.openclaw/workspace/memory/morning-briefs.md

# 4. Push to GitHub
cd /root/.openclaw/workspace
git add memory/morning-briefs.md
git commit -m "Morning brief - $DATE" >/dev/null 2>&1
git push >/dev/null 2>&1

echo "Morning brief complete - $DATE"
