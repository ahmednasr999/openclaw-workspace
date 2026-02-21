#!/bin/bash
# HealthTech Directory - Day 1: Company Scraping
# Usage: bash scrape.sh

set -e

# Configuration
OUTPUT_DIR="./data"
RAW_FILE="$OUTPUT_DIR/gcc-healthtech-raw.json"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

mkdir -p "$OUTPUT_DIR"

echo "=== HealthTech Directory - Day 1: Scraping ==="
echo "Timestamp: $TIMESTAMP"
echo ""

# Method 1: Outscraper (requires API key)
# Uncomment and set your API key to use
# OUTSCRAPER_API_KEY="your-api-key"
# outscraper scrape companies \
#   --domain "linkedin.com" \
#   --query "HealthTech UAE" \
#   --limit 5000 \
#   --api-key "$OUTSCRAPER_API_KEY" \
#   --output "$RAW_FILE"

# Method 2: LinkedIn Company Export
# Export from LinkedIn Sales Navigator:
# 1. Go to LinkedIn Sales Navigator
# 2. Search: "HealthTech" + "United Arab Emirates"
# 3. Export to CSV
# 4. Convert to JSON using: python linkedin-to-json.py

# Method 3: Crunchbase/ CB Insights Export
# 1. Go to cb.com/insights
# 2. Search: HealthTech companies in UAE, KSA, Egypt
# 3. Export to CSV
# 4. Convert to JSON

# Method 4: Alternative Company Lists (Working Today)
echo "=== Method 1: LinkedIn Company Searches ==="
echo "Search these LinkedIn URLs and export to CSV:"
echo ""
echo "UAE:"
echo "  - https://www.linkedin.com/search/results/companies/?keywords=HealthTech&geo=UAE"
echo "  - https://www.linkedin.com/search/results/companies/?keywords=Hospital&geo=UAE"
echo "  - https://www.linkedin.com/search/results/companies/?keywords=Digital%20Health&geo=UAE"
echo ""
echo "KSA:"
echo "  - https://www.linkedin.com/search/results/companies/?keywords=HealthTech&geo=SA"
echo "  - https://www.linkedin.com/search/results/companies/?keywords=Hospital&geo=SA"
echo ""
echo "Egypt:"
echo "  - https://www.linkedin.com/search/results/companies/?keywords=HealthTech&geo=EG"
echo ""

# Method 5: Use web search to find company lists
echo "=== Method 2: Web Search for Company Lists ==="
echo "Search these URLs and extract company names:"
echo ""
echo "UAE Directories:"
echo "  - https://dha.gov.ae/health-services/health-facilities/"
echo "  - https://www.dha.gov.ae/dha-media/press-releases"
echo "  - https://www.auh.org.ae/find-a-doctor"
echo "  - https://www.cleardhaka.com/uae/hospitals"
echo ""
echo "KSA Directories:"
echo "  - https://www.scfhs.org.sa/search/establishments"
echo "  - https://www.moh.gov.sa/depts/
echo "  - https://www.ncg.com.sa/
echo ""
echo "Egypt Directories:"
echo "  - https://www.mohp.gov..eg/
echo "  - https://www.eda.org.eg/
echo ""

# Method 6: Use brave search to find HealthTech companies
echo "=== Method 3: Brave Search API ==="
echo "Search for HealthTech company lists:"
echo ""
echo "Run these searches:"
echo ""
echo "1. UAE HealthTech companies list"
echo "2. KSA HealthTech companies directory"
echo "3. Egypt HealthTech companies"
echo "4. GCC digital health startups"
echo "5. Hospital chains UAE KSA Egypt"
echo ""

# Method 7: Use LinkedIn connections export
echo "=== Method 4: Your LinkedIn Network ==="
echo "Export your LinkedIn connections who work at HealthTech companies:"
echo "1. Go to linkedin.com/myconnections"
echo "2. Export connections"
echo "3. Filter by company industry: HealthTech"
echo ""

# Create the raw data placeholder
echo "=== Creating Raw Data Placeholder ==="
cat > "$RAW_FILE" << EOF
{
  "metadata": {
    "scraped_at": "$TIMESTAMP",
    "source": "manual",
    "total_records": 0
  },
  "companies": []
}
EOF

echo "Created: $RAW_FILE"
echo ""

# Create scraping helper script
echo "=== Creating Helper Scripts ==="

# Script 1: Convert CSV to JSON
cat > "$OUTPUT_DIR/csv-to-json.py" << 'PYEOF'
#!/usr/bin/env python3
"""
Convert exported company CSV to structured JSON
"""
import csv
import json
import sys

def csv_to_json(csv_file, output_file):
    companies = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            company = {
                "company_name": row.get('Company Name', ''),
                "website": row.get('Website', ''),
                "linkedin": row.get('LinkedIn URL', ''),
                "location": {
                    "country": row.get('Country', ''),
                    "city": row.get('City', ''),
                    "address": row.get('Address', '')
                },
                "category": row.get('Industry', ''),
                "size": row.get('Company Size', ''),
                "source": "linkedin_export",
                "scraped_at": __import__('datetime').datetime.now().isoformat()
            }
            companies.append(company)
    
    output = {
        "metadata": {
            "scraped_at": __import__('datetime').datetime.now().isoformat(),
            "source": csv_file,
            "total_records": len(companies)
        },
        "companies": companies
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Converted {len(companies)} companies to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python csv-to-json.py <input.csv> <output.json>")
        sys.exit(1)
    
    csv_to_json(sys.argv[1], sys.argv[2])
PYEOF

chmod +x "$OUTPUT_DIR/csv-to-json.py"
echo "Created: $OUTPUT_DIR/csv-to-json.py"

# Script 2: Manual data entry template
cat > "$OUTPUT_DIR/company-template.json" << 'EOF'
{
  "company_name": "",
  "website": "",
  "linkedin": "",
  "location": {
    "country": "UAE",
    "city": "",
    "address": ""
  },
  "category": "HealthTech",
  "size": "SME",
  "funding": "Unknown",
  "contact": {
    "linkedin_url": "",
    "email_format": ""
  },
  "hiring": {
    "pmo_roles": false,
    "tech_roles": false,
    "url": ""
  },
  "data_quality": "Low"
}
EOF

echo "Created: $OUTPUT_DIR/company-template.json"
echo ""

# Summary
echo "=== Day 1 Summary ==="
echo ""
echo "Your task today:"
echo "1. ☐ Export LinkedIn company lists (5 searches)"
echo "2. ☐ Download 2-3 company CSV files"
echo "3. ☐ Run: python csv-to-json.py companies.csv companies.json"
echo "4. ☐ Goal: 5,000 companies in raw format"
echo ""
echo "Files created:"
echo "  - $OUTPUT_DIR/gcc-healthtech-raw.json"
echo "  - $OUTPUT_DIR/csv-to-json.py"
echo "  - $OUTPUT_DIR/company-template.json"
echo ""
echo "Next: Day 2 - Clean + Structure with Claude Code"
echo ""

# Instructions for Claude Code Pass
echo "=== Claude Code Instructions ==="
echo "After getting raw data, run Claude Code with:"
echo ""
echo 'Prompt: Clean this HealthTech company list:'
echo '1. Remove exact duplicates'
echo '2. Normalize company names'
echo '3. Structure with fields from company-template.json'
echo '4. Add quality score (1-10)'
echo ""
echo "Output: gcc-healthtech-clean.json"
