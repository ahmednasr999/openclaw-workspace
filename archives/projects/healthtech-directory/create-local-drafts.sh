#!/bin/bash
# Gmail Draft Creator - For Local Machine
#
# Run this on your LOCAL machine (not server)
# This will create 47 email drafts in your Gmail
#
# Usage:
#   chmod +x create-local-drafts.sh
#   ./create-local-drafts.sh
#
# PREREQUISITES:
# 1. Install gog: brew install steipete/tap/gogcli
# 2. Authenticate: gog auth add you@gmail.com --services gmail
# 3. Run: ./create-local-drafts.sh

WORKSPACE="${HOME}/.openclaw/workspace/healthtech-directory"
OUTREACH_DIR="${WORKSPACE}/outreach"

echo "========================================"
echo "  Gmail Draft Creator"
echo "========================================"
echo ""

# Check gog
if ! command -v gog &> /dev/null; then
    echo "❌ gog not installed"
    echo ""
    echo "Install with:"
    echo "  brew install steipete/tap/gogcli"
    exit 1
fi

echo "✅ gog installed"

# Check authentication
if ! gog auth list &> /dev/null; then
    echo "❌ Not authenticated"
    echo ""
    echo "Run:"
    echo "  gog auth add you@gmail.com --services gmail"
    exit 1
fi

ACCOUNT=$(gog auth list 2>/dev/null | grep "@" | head -1)
echo "✅ Authenticated: $ACCOUNT"
echo ""

# Check data
if [ ! -f "${OUTREACH_DIR}/decision-makers.csv" ]; then
    echo "❌ Decision makers not found"
    echo "Run this script from the healthtech-directory folder"
    exit 1
fi

COUNT=$(tail -n +2 "${OUTREACH_DIR}/decision-makers.csv" | wc -l)
echo "✅ Found ${COUNT} decision makers"
echo ""

# Create drafts
echo "Creating ${COUNT} email drafts..."
echo ""

SUCCESS=0
FAILED=0

while IFS=',' read -r priority company website location category decision_maker title linkedin email; do
    # Skip header
    if [ "$priority" = "priority" ]; then
        continue
    fi
    
    # Clean fields
    email=$(echo "$email" | tr -d '[:space:]')
    first_name=$(echo "$decision_maker" | awk '{print $1}')
    subject="Executive PMO Leadership - ${company}"
    
    # Create body
    body="Hi ${first_name},

I noticed ${company} is leading digital transformation in the GCC healthcare sector.

I'm a Senior Technology Executive with 20+ years experience:
• SGH (Egypt): Led \$50M transformation, reduced reporting by 97%
• Talabat (GCC): Scaled operations 233x in 18 months
• Network (8 countries): PMO for 300+ projects

I'm exploring senior leadership opportunities in HealthTech, particularly PMO, Digital Transformation, or CDO roles.

Would you have 15 minutes for a brief call this week?

Best regards,
Ahmed Nasr
Senior Technology Executive | PMO & AI Transformation"
    
    # Save body to temp file
    TEMP_FILE=$(mktemp)
    echo "$body" > "$TEMP_FILE"
    
    # Create draft
    RESULT=$(gog gmail drafts create \
        --to "$email" \
        --subject "$subject" \
        --body-file "$TEMP_FILE" \
        --label "HealthTech Outreach" \
        2>&1)
    
    if echo "$RESULT" | grep -qi "success\|created\|draft\|done"; then
        echo "  ✅ ${company} -> ${email}"
        ((SUCCESS++))
    else
        echo "  ❌ ${company} -> ${email}"
        ((FAILED++))
    fi
    
    rm "$TEMP_FILE"
    
    # Rate limiting
    sleep 1
    
done < "${OUTREACH_DIR}/decision-makers.csv"

echo ""
echo "========================================"
echo "  Done!"
echo "========================================"
echo ""
echo "Results:"
echo "  ✅ Created: ${SUCCESS}"
echo "  ❌ Failed: ${FAILED}"
echo ""
echo "Next:"
echo "  1. Open Gmail: mail.google.com"
echo "  2. Review drafts"
echo "  3. Edit if needed"
echo "  4. Send!"
