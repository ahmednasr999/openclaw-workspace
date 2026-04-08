#!/bin/bash
# Refresh applied-job-ids.txt from pipeline.md
# Run before each radar/scout scan to ensure dedup is current

PIPELINE="/root/.openclaw/workspace/jobs-bank/pipeline.md"
OUTPUT="/root/.openclaw/workspace/jobs-bank/applied-job-ids.txt"

grep -oP 'linkedin\.com/jobs/view/\K[0-9]+' "$PIPELINE" | sort -u > "$OUTPUT"
echo "$(wc -l < "$OUTPUT") applied job IDs extracted to $OUTPUT"
