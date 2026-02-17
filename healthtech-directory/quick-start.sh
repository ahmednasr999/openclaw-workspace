#!/bin/bash
# HealthTech Directory - Quick Start
# One command to start everything

WORKSPACE="/root/.openclaw/workspace/healthtech-directory"
DATA_DIR="$WORKSPACE/data"

echo "=========================================="
echo "  HealthTech Directory - Quick Start"
echo "=========================================="
echo ""

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
echo ""

# Check for data directory
mkdir -p "$DATA_DIR"

# Check if raw data exists
if [ -f "$DATA_DIR/gcc-healthtech-raw.json" ]; then
    echo "✓ Raw data found"
    python -c "import json; data=json.load(open('$DATA_DIR/gcc-healthtech-raw.json')); print(f'  {len(data.get(\"companies\", data))} companies loaded')"
else
    echo "✗ Raw data missing"
    echo ""
    echo "Your task:"
    echo "1. Export LinkedIn company lists (UAE, KSA, Egypt)"
    echo "2. Run: python $WORKSPACE/csv-to-json.py companies.csv companies.json"
    echo "3. Save as: $DATA_DIR/gcc-healthtech-raw.json"
    echo ""
    echo "Example export format:"
    echo '  {"companies": [{"company_name": "...", "website": "...", ...}]}'
    echo ""
    exit 1
fi

# Step 2: Run pipeline
echo ""
echo "Step 2: Running pipeline..."
echo ""

python "$WORKSPACE/run-pipeline.py"

# Step 3: Show results
echo ""
echo "=========================================="
echo "  Pipeline Complete"
echo "=========================================="
echo ""

echo "Results:"
if [ -f "$DATA_DIR/gcc-healthtech-enriched.json" ]; then
    python -c "
import json
data=json.load(open('$DATA_DIR/gcc-healthtech-enriched.json'))
print(f'✓ {len(data.get(\"companies\", data))} companies enriched')
"
fi

if [ -f "$DATA_DIR/job-search-targets.json" ]; then
    python -c "
import json
data=json.load(open('$DATA_DIR/job-search-targets.json'))
print(f'✓ {data[\"total\"]} job search targets')
"
fi

if [ -f "$DATA_DIR/anco-prospects.json" ]; then
    python -c "
import json
data=json.load(open('$DATA_DIR/anco-prospects.json'))
print(f'✓ {data[\"total\"]} ANCO prospects')
"
fi

echo ""
echo "Files:"
ls -lh "$DATA_DIR"/*.json 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'

echo ""
echo "Next: Use data for job search and ANCO outreach"
