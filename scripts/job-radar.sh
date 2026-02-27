#!/bin/bash
# Daily job search - autonomous radar
export TAVILY_API_KEY="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"
DATE=$(date +%Y-%m-%d)

# GCC coverage: UAE, Saudi Arabia, Qatar, Bahrain, Kuwait, Oman
GCC_COUNTRIES="UAE Dubai Abu Dhabi Saudi Arabia Riyadh Jeddah Qatar Doha Bahrain Manama Kuwait Oman Muscat GCC"

echo "=== Job Radar - $DATE ===" >> /root/.openclaw/workspace/memory/job-radar.md
echo "" >> /root/.openclaw/workspace/memory/job-radar.md

# Search 1: VP/C-Suite Digital Transformation across GCC
RESULT1=$(node /root/.openclaw/workspace/skills/tavily-search/scripts/search.mjs "VP Director CTO COO CEO \"Digital Transformation\" OR \"AI\" OR \"HealthTech\" OR \"FinTech\" $GCC_COUNTRIES 2026 site:linkedin.com" -n 10 2>&1)
echo "### Search 1: VP/C-Suite Digital Transformation" >> /root/.openclaw/workspace/memory/job-radar.md
echo "$RESULT1" >> /root/.openclaw/workspace/memory/job-radar.md
echo "" >> /root/.openclaw/workspace/memory/job-radar.md

# Search 2: PMO/Transformation leadership roles
RESULT2=$(node /root/.openclaw/workspace/skills/tavily-search/scripts/search.mjs "\"Head of PMO\" OR \"Director PMO\" OR \"VP PMO\" OR \"Head of Technology\" OR \"Head of AI\" $GCC_COUNTRIES 2026" -n 10 2>&1)
echo "### Search 2: PMO / Technology Leadership" >> /root/.openclaw/workspace/memory/job-radar.md
echo "$RESULT2" >> /root/.openclaw/workspace/memory/job-radar.md
echo "" >> /root/.openclaw/workspace/memory/job-radar.md

# Search 3: HealthTech / FinTech executive roles
RESULT3=$(node /root/.openclaw/workspace/skills/tavily-search/scripts/search.mjs "\"VP\" OR \"Director\" OR \"Head\" HealthTech OR FinTech OR \"Digital Health\" executive $GCC_COUNTRIES 2026 job opening" -n 10 2>&1)
echo "### Search 3: HealthTech / FinTech Executives" >> /root/.openclaw/workspace/memory/job-radar.md
echo "$RESULT3" >> /root/.openclaw/workspace/memory/job-radar.md
echo "" >> /root/.openclaw/workspace/memory/job-radar.md

echo "---" >> /root/.openclaw/workspace/memory/job-radar.md
echo "" >> /root/.openclaw/workspace/memory/job-radar.md

# Auto-commit and push
cd /root/.openclaw/workspace
git add memory/job-radar.md scripts/job-radar.sh
git commit -m "Job radar update - $DATE (GCC: UAE, KSA, Qatar, Bahrain, Kuwait, Oman)" >/dev/null 2>&1
git push >/dev/null 2>&1
