#!/bin/bash
# Daily job search - autonomous radar
export TAVILY_API_KEY="<redacted>"
DATE=$(date +%Y-%m-%d)
SEARCH_RESULT=$(node /root/.openclaw/workspace/skills/tavily-search/scripts/search.mjs "VP Director Digital Transformation PMO AI jobs UAE Dubai February 2026" -n 10 2>&1)
echo "=== Job Search - $DATE ===" >> /root/.openclaw/workspace/memory/job-radar.md
echo "$SEARCH_RESULT" >> /root/.openclaw/workspace/memory/job-radar.md
echo "" >> /root/.openclaw/workspace/memory/job-radar.md
