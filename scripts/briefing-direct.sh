#!/bin/bash
# Direct morning briefing - no LLM, runs script and sends to Telegram

cd /root/.openclaw/workspace

# Run the orchestrator
OUTPUT=$(python3 scripts/morning-briefing-orchestrator.py 2>&1)
EXIT_CODE=$?

# Save output to temp file
echo "$OUTPUT" > /tmp/briefing-output-$(date +%Y-%m-%d).txt

# Send to Telegram
if [ $EXIT_CODE -eq 0 ]; then
    # Extract Telegram message (everything after "☀️ Morning Brief")
    TELEGRAM_MSG=$(sed -n '/☀️ Morning Brief/,$p' /tmp/briefing-output-$(date +%Y-%m-%d).txt | head -50)
    
    # Send via message tool
    curl -s -X POST "https://api.telegram.org/bot$(cat /root/.openclaw/config/telegram.json | jq -r .token)/sendMessage" \
        -d "chat_id=866838380" \
        -d "text=$(echo "$TELEGRAM_MSG" | head -40)" \
        -d "parse_mode=Markdown"
else
    echo "BRIEFING FAILED: $OUTPUT" | mail -s "BRIEFING FAILED" ahmed@example.com 2>/dev/null || true
fi

exit $EXIT_CODE
