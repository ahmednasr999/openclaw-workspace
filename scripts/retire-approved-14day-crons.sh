#!/usr/bin/env bash
set -Eeuo pipefail

WORKSPACE="/root/.openclaw/workspace"
BACKUP_DIR="$WORKSPACE/config"
mkdir -p "$BACKUP_DIR"

backup="$BACKUP_DIR/root-crontab.before-approved-14day-retire-$(date +%Y%m%d-%H%M%S).bak"
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

crontab -l > "$backup"
grep -vE 'approved-14day-linkedin-11am|approved-14day-linkedin-engagement-12pm|approved-14day-retire' "$backup" > "$tmp"
crontab "$tmp"

echo "Retired approved 14-day LinkedIn campaign crons at $(date -Is). Backup: $backup"
