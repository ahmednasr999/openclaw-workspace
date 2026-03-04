#!/bin/bash
# HealthTech Directory - Cron Setup
# Schedule automated pipeline runs

# Configuration
WORKSPACE="/root/.openclaw/workspace/healthtech-directory"
PIPELINE="$WORKSPACE/run-pipeline.py"

echo "=== HealthTech Directory - Cron Setup ==="
echo ""

# Create cron job for daily pipeline check
echo "Creating cron jobs..."
echo ""

# Run pipeline check daily at 8 AM Cairo
CRON_LINE="0 8 * * * cd $WORKSPACE && python run-pipeline.py >> pipeline.log 2>&1"

echo "Cron job for daily check (8 AM Cairo):"
echo "$CRON_LINE"
echo ""

# Add to crontab (commented out for safety)
# echo "$CRON_LINE" | crontab -

echo "To activate, run:"
echo "  echo '$CRON_LINE' | crontab -"
echo ""

# Create systemd timer alternative
SYSTEMD_TIMER="[Unit]
Description=HealthTech Directory Pipeline

[Timer]
OnCalendar=*-*-* 08:00:00
Timezone=Africa/Cairo
Persistent=true

[Install]
WantedBy=timers.target
"

SYSTEMD_SERVICE="[Unit]
Description=HealthTech Directory Pipeline
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory=$WORKSPACE
ExecStart=/usr/bin/python3 $PIPELINE
User=root

[Install]
WantedBy=multi-user.target
"

echo "Systemd timer (alternative to cron):"
echo ""
echo "Save as: /etc/systemd/system/healthtech-directory.timer"
echo ""

# Manual run options
echo "=== Manual Run Options ==="
echo ""
echo "Run complete pipeline:"
echo "  python $WORKSPACE/run-pipeline.py"
echo ""
echo "Run specific day:"
echo "  python $WORKSPACE/run-pipeline.py 1  # Day 1"
echo "  python $WORKSPACE/run-pipeline.py 2  # Day 2"
echo "  python $WORKSPACE/run-pipeline.py 3  # Day 3"
echo "  python $WORKSPACE/run-pipeline.py 4  # Day 4"
echo ""

# Health check
echo "=== Health Check ==="
echo ""
echo "Check pipeline status:"
echo "  cat $WORKSPACE/pipeline.log"
echo ""
echo "Check outputs:"
echo "  ls -la $WORKSPACE/data/"
echo ""

echo "=== Setup Complete ==="
