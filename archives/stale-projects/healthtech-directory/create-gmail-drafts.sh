#!/bin/bash
# HealthTech Directory - Gmail Draft Creator
# Creates drafts in Gmail using gog CLI
#
# PREREQUISITE: Authenticate with Gmail first:
#   gog auth add you@gmail.com --services gmail
#
# Usage: ./create-gmail-drafts.sh

WORKSPACE="/root/.openclaw/workspace/healthtech-directory"
OUTREACH_DIR="$WORKSPACE/outreach"

echo "========================================"
echo "Gmail Draft Creator"
echo "========================================"
echo ""

# Check if gog is installed
if ! command -v gog &> /dev/null; then
    echo "❌ gog not installed"
    echo ""
    echo "Install with:"
    echo "  brew install steipete/tap/gogcli"
    exit 1
fi

# Check if authenticated
if ! gog auth list &> /dev/null; then
    echo "❌ Not authenticated with Gmail"
    echo ""
    echo "Run this first:"
    echo "  gog auth add you@gmail.com --services gmail"
    echo ""
    echo "This will open a browser for OAuth login."
    exit 1
fi

echo "✓ gog installed"
echo "✓ Authenticated"
echo ""

# Check if CSV exists
if [ ! -f "$OUTREACH_DIR/decision-makers.csv" ]; then
    echo "❌ Decision makers not found"
    echo "Run first: python3 prepare-emails.py"
    exit 1
fi

echo "Creating drafts..."
echo ""

# Read CSV and create drafts
while IFS=',' read -r priority company website location category decision_maker title linkedin email; do
    # Skip header
    if [ "$priority" = "priority" ]; then
        continue
    fi
    
    # Clean email (remove any whitespace)
    email=$(echo "$email" | tr -d '[:space:]')
    
    # Create subject
    subject="Executive PMO Leadership - $company"
    
    # Get first name
    first_name=$(echo "$decision_maker" | awk '{print $1}')
    
    # Create body
    body="Hi $first_name,

I noticed $company is leading digital transformation in the GCC healthcare sector.

I'm a Senior Technology Executive with 20+ years experience:
• SGH (Egypt): Led \$50M transformation, reduced reporting by 97%
• Talabat (GCC): Scaled operations 233x in 18 months
• Network (8 countries): PMO for 300+ projects

I'm exploring senior leadership opportunities in HealthTech, particularly PMO, Digital Transformation, or CDO roles.

Would you have 15 minutes for a brief call this week?

Best regards,
Ahmed Nasr
Senior Technology Executive | PMO & AI Transformation"

    # Create draft
    echo "  Creating draft for: $company -> $email"
    
    # Save body to temp file
    echo "$body" > /tmp/email-body-$priority.txt
    
    # Create draft using gog
    gog gmail drafts create \
        --to "$email" \
        --subject "$subject" \
        --body-file /tmp/email-body-$priority.txt \
        --label "HealthTech Outreach" \
        2>&1 | grep -v "^{" || true
    
    # Clean up
    rm /tmp/email-body-$priority.txt
    
    # Rate limiting (be nice to Gmail)
    sleep 2
    
done < "$OUTREACH_DIR/decision-makers.csv"

echo ""
echo "========================================"
echo "Drafts Created!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Open Gmail: https://mail.google.com/mail/u/0/#label/HealthTech+Outreach"
echo "  2. Review each draft"
echo "  3. Edit if needed"
echo "  4. Send when ready"
echo ""
echo "To send all drafts:"
echo "  gog gmail drafts list | grep HealthTech | xargs -I {} gog gmail drafts send {}"
