#!/bin/bash
# LinkedIn Job Scout - Daily job search automation
# Searches LinkedIn for executive roles in GCC
# Runs: Daily at 6 AM UTC (8 AM Cairo)

OUTPUT_FILE="/root/.openclaw/workspace/memory/linkedin-job-scout.md"
PIPELINE_FILE="/root/.openclaw/workspace/jobs-bank/pipeline.md"
LOG_FILE="/root/.openclaw/workspace/logs/linkedin-scout.log"

# Target keywords (10 executive-level searches)
KEYWORDS=(
  "PMO%20Director"
  "VP%20Digital%20Transformation"
  "VP%20Technology"
  "CTO"
  "Head%20of%20AI"
  "Director%20Digital%20Transformation"
  "Chief%20Digital%20Officer"
  "Head%20of%20Product"
  "Senior%20Director%20Technology"
  "VP%20HealthTech"
)

# All 6 GCC countries
LOCATIONS=(
  "United%20Arab%20Emirates"
  "Saudi%20Arabia"
  "Qatar"
  "Bahrain"
  "Kuwait"
  "Oman"
)

echo "=== LinkedIn Job Scout - $(date) ===" >> "$LOG_FILE"

# Function to fetch jobs
fetch_jobs() {
  local keyword="$1"
  local location="$2"
  local url="https://www.linkedin.com/jobs/search/?keywords=${keyword}&location=${location}&f_TPR=r604800&f_E=1"
  
  curl -s -L "$url" 2>/dev/null | grep -oP '<h3[^>]*class="[^"]*job-card-list__title[^"]*"[^>]*>.*?</h3>' | \
    sed 's/<[^>]*>//g' | head -20
}

# Main search loop
> "$OUTPUT_FILE"
echo "# LinkedIn Job Scout — $(date -u +%Y-%m-%d)" >> "$OUTPUT_FILE" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

for location in "${LOCATIONS[@]}"; do
  echo "## $location" >> "$OUTPUT_FILE"
  echo "" >> "$OUTPUT_FILE"
  
  for keyword in "${KEYWORDS[@]}"; do
    echo "Searching: $keyword in $location" >> "$LOG_FILE"
    
    JOBS=$(curl -s -L "https://www.linkedin.com/jobs/search/?keywords=${keyword}&location=${location}&f_TPR=r604800" 2>/dev/null | \
      grep -oP '(?<=<h3 class="job-card-list__title">)[^<]+' | head -10)
    
    if [ -n "$JOBS" ]; then
      echo "### $keyword (replacing spaces)" >> "$OUTPUT_FILE"
      echo "$JOBS" | while read -r job; do
        echo "- $job" >> "$OUTPUT_FILE"
      done
      echo "" >> "$OUTPUT_FILE"
    fi
  done
done

echo "Job scout complete. Results saved to $OUTPUT_FILE" >> "$LOG_FILE"
echo "=== End ===" >> "$LOG_FILE"

# Notify via Telegram (if configured)
echo "Job scout complete: $(date)"
