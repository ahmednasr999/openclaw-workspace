#!/bin/bash
# Job Radar v2 — Upgraded with deduplication + profile matching
# Runs daily at 6 AM Cairo (4 AM UTC)
# Output: memory/job-radar-v2.md (structured, deduplicated, profile-matched)

export TAVILY_API_KEY="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"
DATE=$(date +%Y-%m-%d)
SEEN_FILE="/root/.openclaw/workspace/memory/job-radar-seen.txt"
OUTPUT="/root/.openclaw/workspace/memory/job-radar-v2.md"
WORKSPACE="/root/.openclaw/workspace"

# Create seen file if it doesn't exist
touch "$SEEN_FILE"

echo "=== Job Radar v2 — $DATE ===" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Run searches and collect raw JSON output
node "$WORKSPACE/scripts/job-radar-parse.mjs" "$DATE" "$SEEN_FILE" >> "$OUTPUT"

echo "" >> "$OUTPUT"
echo "---" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Auto-commit
cd "$WORKSPACE"
git add memory/job-radar-v2.md memory/job-radar-seen.txt scripts/
git commit -m "Job radar v2 — $DATE" >/dev/null 2>&1
git push >/dev/null 2>&1

echo "Job Radar v2 complete — $DATE"
