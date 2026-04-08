#!/bin/bash
# recruiter-dossier.sh — Auto-generate company dossier on recruiter response
# Triggered by: email cron creating a .trigger file in jobs-bank/handoff/
# Usage: ./recruiter-dossier.sh <company-name> <role-title> <trigger-file-path>
#
# This script spawns a sub-agent to research the company and generate
# a 1-page intelligence dossier, then sends it to Ahmed via Telegram.

COMPANY="$1"
ROLE="$2"
TRIGGER_FILE="$3"
DATE=$(date -u +"%Y-%m-%d")
SLUG=$(echo "$COMPANY" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-')
OUTPUT_DIR="/root/.openclaw/workspace/jobs-bank/dossiers"
OUTPUT_FILE="$OUTPUT_DIR/${DATE}-${SLUG}-dossier.md"

mkdir -p "$OUTPUT_DIR"

echo "[$(date -u)] Dossier generation triggered for: $COMPANY — $ROLE"
echo "Output: $OUTPUT_FILE"
