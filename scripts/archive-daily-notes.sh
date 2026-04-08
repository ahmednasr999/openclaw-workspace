#!/bin/bash
# Archive daily notes older than 30 days
# Moves memory/YYYY-MM-DD.md → memory/archive/YYYY-MM/YYYY-MM-DD.md
# Then re-indexes memory

cd ~/.openclaw/workspace

CUTOFF=$(date -d "-30 days" +%Y-%m-%d)
MOVED=0

for f in memory/2???-??-??.md; do
    [ -f "$f" ] || continue
    DATE=$(basename "$f" .md)
    if [[ "$DATE" < "$CUTOFF" ]]; then
        MONTH=${DATE:0:7}
        mkdir -p "memory/archive/$MONTH"
        mv "$f" "memory/archive/$MONTH/"
        MOVED=$((MOVED + 1))
    fi
done

if [ "$MOVED" -gt 0 ]; then
    echo "$(date -u +%Y-%m-%d_%H:%M) Archived $MOVED daily notes"
    openclaw memory index 2>&1
else
    echo "$(date -u +%Y-%m-%d_%H:%M) Nothing to archive"
fi
