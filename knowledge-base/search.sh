#!/bin/bash
# Knowledge Base Search Script
# Usage: ./search.sh <query> [type]

DB="/root/.openclaw/workspace/knowledge-base/kb.db"
QUERY="$1"
TYPE="$2"

if [ -n "$TYPE" ]; then
    FILTER="AND source_type = '$TYPE'"
else
    FILTER=""
fi

sqlite3 -header -column "$DB" "
SELECT id, title, source_type, domain, tags, 
       substr(summary, 1, 200) as summary_preview,
       ingested_at
FROM sources 
WHERE (title LIKE '%$QUERY%' OR summary LIKE '%$QUERY%' OR content LIKE '%$QUERY%' OR tags LIKE '%$QUERY%' OR key_entities LIKE '%$QUERY%')
$FILTER
ORDER BY ingested_at DESC
LIMIT 20;
"

# Log the query
sqlite3 "$DB" "INSERT INTO queries (query, results_count) VALUES ('$QUERY', (SELECT COUNT(*) FROM sources WHERE title LIKE '%$QUERY%' OR summary LIKE '%$QUERY%' OR content LIKE '%$QUERY%'));"
