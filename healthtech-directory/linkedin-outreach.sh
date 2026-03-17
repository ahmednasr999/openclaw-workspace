#!/bin/bash
# HealthTech Directory - LinkedIn Outreach Automation
# Automated LinkedIn message sending
#
# Usage: ./linkedin-outreach.sh [number_of_messages]
#
# This script prepares messages for sending via LinkedIn
# WARNING: LinkedIn has strict automation policies

WORKSPACE="/root/.openclaw/workspace/healthtech-directory"
OUTREACH_DIR="$WORKSPACE/outreach"
DATA_DIR="$WORKSPACE/data"

echo "========================================"
echo "LinkedIn Outreach Automation"
echo "========================================"
echo ""

# Check for messages
QUEUE_FILE="$OUTREACH_DIR/automation-queue.json"
LINKS_FILE="$OUTREACH_DIR/linkedin-urls.json"

if [ ! -f "$QUEUE_FILE" ]; then
    echo "Creating automation queue..."
    python3 "$WORKSPACE/create-automation-messages.py"
fi

# Show pending messages
echo "Pending messages:"
python3 -c "
import json
with open('$QUEUE_FILE') as f:
    data = json.load(f)
    pending = [m for m in data['queue'] if m['status'] == 'pending']
    print(f'Total pending: {len(pending)}')
    for m in pending[:5]:
        print(f\"  • {m['company']} - Day {m['touch']}\")
"

echo ""
echo "========================================"
echo "LinkedIn URLs to Process"
echo "========================================"
echo ""

python3 -c "
import json
with open('$LINKS_FILE') as f:
    data = json.load(f)
    for i, url in enumerate(data['urls'][:10], 1):
        print(f\"{i:2}. {url['company']}\")
        print(f\"    → {url['linkedin_url']}\")
"

echo ""
echo "========================================"
echo "Email Blast Ready"
echo "========================================"
echo ""

EMAIL_FILE="$OUTREACH_DIR/email-blast.json"
python3 -c "
import json
with open('$EMAIL_FILE') as f:
    data = json.load(f)
    print(f'Total emails: {len(data[\"emails\"])}')
    print()
    print('Sample email:')
    print('To:', data['emails'][0]['to'])
    print('Subject:', data['emails'][0]['subject'][:60], '...')
"

echo ""
echo "========================================"
echo "Files Ready"
echo "========================================"
echo ""
echo "1. linkedin-urls.json - URLs for browser automation"
echo "2. automation-queue.json - All messages with status tracking"
echo "3. email-blast.json - Ready-to-send emails"
echo "4. tracking-sheet.csv - Import to Google Sheets"
echo ""
echo "To send messages:"
echo "  • LinkedIn: Open URLs from linkedin-urls.json"
echo "  • Email: Import email-blast.json to email client"
echo "  • Track: Import tracking-sheet.csv to Google Sheets"
