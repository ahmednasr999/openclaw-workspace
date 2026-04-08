#!/bin/bash
# LinkedIn Job Scout - Cron Wrapper
# Usage: Run via cron to notify of new jobs
# Then run fetch manually or via scheduled session

SCRIPT_DIR="/root/.openclaw/workspace/scripts"
OUTPUT_FILE="/root/.openclaw/workspace/memory/linkedin-job-scout.md"

# Search URLs (will be fetched via web_fetch in session)
cat > "$OUTPUT_FILE" << 'EOF'
# LinkedIn Job Scout

Run these searches to find fresh jobs:

## PMO Director - UAE
https://www.linkedin.com/jobs/search/?keywords=PMO%20Director&location=United%20Arab%20Emirates&f_TPR=r604800

## Program Manager - UAE
https://www.linkedin.com/jobs/search/?keywords=Program%20Manager&location=United%20Arab%20Emirates&f_TPR=r604800

## CTO - Dubai
https://www.linkedin.com/jobs/search/?keywords=CTO&location=Dubai&f_TPR=r604800

## Head of AI - UAE
https://www.linkedin.com/jobs/search/?keywords=Head%20of%20AI&location=UAE&f_TPR=r604800

## Digital Transformation - GCC
https://www.linkedin.com/jobs/search/?keywords=Digital%20Transformation&location=GCC&f_TPR=r604800

---
Last updated: $(date)
EOF

# Update timestamp
sed -i "s/\$(date)/$(date -u +%Y-%m-%d\ %H:%M\ UTC)/" "$OUTPUT_FILE"

echo "Job scout URLs ready. Run web_fetch on each URL to get job listings."
echo "Output: $OUTPUT_FILE"
