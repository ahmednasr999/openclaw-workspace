#!/bin/bash
# HealthTech Directory - Fully Automated Build
# ONE COMMAND TO RULE THEM ALL
#
# Usage: bash auto-build.sh
#
# This runs the complete 4-day pipeline automatically:
#   Day 1: Auto-scrape (generates sample data)
#   Day 2: Clean + structure + quality score
#   Day 3: Verify websites
#   Day 4: Enrich + export job targets + ANCO prospects

WORKSPACE="/root/.openclaw/workspace/healthtech-directory"
DATA_DIR="$WORKSPACE/data"

echo "========================================"
echo "  HealthTech Directory - AUTO BUILD"
echo "========================================"
echo ""
echo "Running fully automated 4-day build..."
echo ""

# Ensure data directory
mkdir -p "$DATA_DIR"

# Run the auto-builder
cd "$WORKSPACE"
python3 auto-build.py

# Check results
echo ""
echo "========================================"
echo "  RESULTS"
echo "========================================"
echo ""

if [ -f "$DATA_DIR/gcc-healthtech-enriched.json" ]; then
    python3 -c "
import json
data=json.load(open('$DATA_DIR/gcc-healthtech-enriched.json'))
print(f'✓ {len(data.get(\"companies\", data))} companies enriched')
"
fi

if [ -f "$DATA_DIR/job-search-targets.json" ]; then
    python3 -c "
import json
data=json.load(open('$DATA_DIR/job-search-targets.json'))
print(f'✓ {data[\"total\"]} job search targets')
"
fi

if [ -f "$DATA_DIR/anco-prospects.json" ]; then
    python3 -c "
import json
data=json.load(open('$DATA_DIR/anco-prospects.json'))
print(f'✓ {data[\"total\"]} ANCO prospects')
"
fi

echo ""
echo "Files created:"
ls -lh "$DATA_DIR"/*.json 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'

echo ""
echo "Next steps:"
echo "  1. Review: cat $DATA_DIR/job-search-targets.json | head -50"
echo "  2. Import to CRM: $DATA_DIR/directory-export.csv"
echo "  3. Launch MVP: Deploy $WORKSPACE to Cloudflare Pages"
