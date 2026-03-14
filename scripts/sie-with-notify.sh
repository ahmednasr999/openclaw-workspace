#!/bin/bash
cd /root/.openclaw/workspace

# Run SIE
python3 scripts/self-improvement-engine.py --dry-run 2>&1 | tail -20

# Read insights and send notification
if [ -f memory/insights.md ]; then
    HEALTH=$(grep "System Health Score" memory/insights.md | grep -oP '\d+/100')
    WARNINGS=$(grep "^## Warnings" -A 5 memory/insights.md | grep -c "^-" || echo "0")
    
    if [ "$WARNINGS" -gt 0 ] || [ "$HEALTH" != "98/100" ]; then
        echo "Sending notification..."
        # Will be picked up by notification handler
        echo "🎯 SIE: $HEALTH" > /root/.openclaw/workspace/.notifications/sie-daily.txt
    fi
fi
