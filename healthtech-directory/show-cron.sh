# HealthTech Directory - Cron Schedule
# Set up automatic daily runs

echo "=== HealthTech Directory - Cron Setup ==="
echo ""

# Check current cron
echo "Current crontab:"
crontab -l
echo ""

# Cron is already set up!
if crontab -l | grep -q "auto-build.py"; then
    echo "✅ Cron job already active!"
    echo ""
    echo "Schedule: Daily at 8:00 AM Cairo"
    echo "Command: python3 auto-build.py"
    echo "Log: auto-build.log"
    echo ""
    echo "What it does:"
    echo "  - Runs auto-build.py daily at 8 AM"
    echo "  - Processes any new data"
    echo "  - Updates job-search-targets.json"
    echo "  - Updates anco-prospects.json"
    echo ""
    echo "Manual run:"
    echo "  cd /root/.openclaw/workspace/healthtech-directory"
    echo "  bash auto-build.sh"
else
    echo "Setting up cron job..."
    echo ""
    
    # Create cron job
    CRON_JOB="0 8 * * * cd /root/.openclaw/workspace/healthtech-directory && python3 auto-build.py >> auto-build.log 2>&1"
    echo "$CRON_JOB" | crontab -
    
    echo "✅ Cron job added!"
    echo ""
    echo "Schedule: Daily at 8:00 AM Cairo"
    echo "Command: python3 auto-build.py"
    echo ""
    
    # Verify
    echo "Verification:"
    crontab -l
fi

echo ""
echo "=== Ready ==="
