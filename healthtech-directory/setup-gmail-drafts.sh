#!/bin/bash
# HealthTech Directory - Gmail Setup & Draft Creator
# 
# This script will:
# 1. Check gog installation
# 2. Authenticate with Gmail (if needed)
# 3. Create 47 email drafts in Gmail
# 4. Organize in "HealthTech Outreach" label

WORKSPACE="/root/.openclaw/workspace/healthtech-directory"
OUTREACH_DIR="$WORKSPACE/outreach"

echo "========================================"
echo "  Gmail Draft Setup"
echo "========================================"
echo ""

# Step 1: Check gog
echo "Step 1: Checking gog installation..."
if ! command -v gog &> /dev/null; then
    echo "❌ gog not installed"
    echo ""
    echo "Installing gog..."
    brew install steipete/tap/gogcli
    if [ $? -ne 0 ]; then
        echo "❌ Installation failed"
        exit 1
    fi
fi
echo "✅ gog installed: $(gog --version)"
echo ""

# Step 2: Check authentication
echo "Step 2: Checking Gmail authentication..."
if gog auth list &> /dev/null; then
    ACCOUNTS=$(gog auth list 2>/dev/null | grep "@" | head -1)
    echo "✅ Authenticated: $ACCOUNTS"
else
    echo "❌ Not authenticated"
    echo ""
    echo "Setting up Gmail authentication..."
    echo ""
    echo "IMPORTANT: This will open a browser for OAuth login."
    echo "1. Click the link that appears"
    echo "2. Sign in to Gmail"
    echo "3. Allow access"
    echo "4. Come back here"
    echo ""
    read -p "Press Enter to continue..."
    
    gog auth add --services gmail
    if [ $? -ne 0 ]; then
        echo "❌ Authentication failed"
        exit 1
    fi
fi
echo ""

# Step 3: Check data
echo "Step 3: Checking decision makers..."
if [ ! -f "$OUTREACH_DIR/decision-makers.csv" ]; then
    echo "❌ Decision makers not found"
    exit 1
fi

COUNT=$(tail -n +2 "$OUTREACH_DIR/decision-makers.csv" | wc -l)
echo "✅ Found $COUNT decision makers"
echo ""

# Step 4: Create drafts
echo "Step 4: Creating Gmail drafts..."
echo ""

# Create the label first
echo "Creating label: HealthTech Outreach"
gog gmail labels create "HealthTech Outreach" 2>/dev/null || echo "Label exists or cannot create (may need Gmail admin)"

TOTAL=0
SENT=0
FAILED=0

while IFS=',' read -r priority company website location category decision_maker title linkedin email; do
    # Skip header
    if [ "$priority" = "priority" ]; then
        continue
    fi
    
    # Clean fields
    email=$(echo "$email" | tr -d '[:space:]')
    first_name=$(echo "$decision_maker" | awk '{print $1}')
    subject="Executive PMO Leadership - $company"
    
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
    
    # Save body to temp file
    TEMP_FILE=$(mktemp)
    echo "$body" > "$TEMP_FILE"
    
    # Create draft
    echo -n "  [$priority] $company -> $email... "
    
    RESULT=$(gog gmail drafts create \
        --to "$email" \
        --subject "$subject" \
        --body-file "$TEMP_FILE" \
        2>&1)
    
    if echo "$RESULT" | grep -q "success\|Created\|draft"; then
        echo "✅"
        ((SENT++))
    else
        # Check if already exists
        if echo "$RESULT" | grep -qi "already\|exist"; then
            echo "⏭️  (already exists)"
            ((SENT++))
        else
            echo "❌"
            ((FAILED++))
        fi
    fi
    
    rm "$TEMP_FILE"
    ((TOTAL++))
    
    # Rate limiting
    sleep 1
    
done < "$OUTREACH_DIR/decision-makers.csv"

echo ""
echo "========================================"
echo "  Done!"
echo "========================================"
echo ""
echo "Results:"
echo "  Total: $TOTAL"
echo "  Created: $SENT"
echo "  Failed: $FAILED"
echo ""
echo "Next:"
echo "  1. Open Gmail: https://mail.google.com/mail/u/0/#drafts"
echo "  2. Review drafts"
echo "  3. Edit if needed"
echo "  4. Send!"
echo ""
echo "To send all drafts:"
echo "  gog gmail drafts list | grep -v '^\[' | xargs -I {} gog gmail drafts send {}"
