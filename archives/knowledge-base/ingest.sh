#!/bin/bash
# Knowledge Base Ingestion Script
# Usage: ./ingest.sh <url> <source_type> <tags> <title> <summary> <content> <entities>

DB="/root/.openclaw/workspace/knowledge-base/kb.db"
URL="$1"
SOURCE_TYPE="$2"
TAGS="$3"
TITLE="$4"
SUMMARY="$5"
CONTENT="$6"
ENTITIES="$7"
DOMAIN=$(echo "$URL" | awk -F/ '{print $3}')

sqlite3 "$DB" "INSERT OR REPLACE INTO sources (url, title, source_type, domain, tags, summary, content, key_entities, updated_at) 
VALUES ('$(echo "$URL" | sed "s/'/''/g")', 
'$(echo "$TITLE" | sed "s/'/''/g")', 
'$SOURCE_TYPE', 
'$DOMAIN', 
'$(echo "$TAGS" | sed "s/'/''/g")', 
'$(echo "$SUMMARY" | sed "s/'/''/g")', 
'$(echo "$CONTENT" | sed "s/'/''/g")', 
'$(echo "$ENTITIES" | sed "s/'/''/g")', 
CURRENT_TIMESTAMP);"

echo "✅ Ingested: $TITLE ($SOURCE_TYPE)"
