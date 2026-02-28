#!/bin/bash
# Weekly Pipeline Archive Script
# Runs every Thursday at 11 PM Cairo (21:00 UTC)
# Archives current week's pipeline, preps for new week

WORKSPACE="/root/.openclaw/workspace"
PIPELINE="$WORKSPACE/jobs-bank/pipeline.md"
WEEKS_DIR="$WORKSPACE/jobs-bank/weeks"

# Get current week info
WEEK_NUM=$(date +%V)
YEAR=$(date +%Y)
START_DATE=$(date -d "last friday" +%b%d | sed 's/^0//')
END_DATE=$(date +%b%d | sed 's/^0//')
FILENAME="${YEAR}-W${WEEK_NUM}-$(date -d 'last friday' +%b%d)-$(date +%b%d).md"

# Create archive
mkdir -p "$WEEKS_DIR"
cp "$PIPELINE" "$WEEKS_DIR/$FILENAME"

echo "✅ Week $WEEK_NUM archived to: jobs-bank/weeks/$FILENAME"

# Git commit and push
cd "$WORKSPACE"
git add jobs-bank/
git commit -m "Archive Week $WEEK_NUM pipeline — $START_DATE to $END_DATE"
git push origin master

echo "✅ Pushed to GitHub"
echo "📋 Next: Start fresh pipeline for Week $(($WEEK_NUM + 1))"
