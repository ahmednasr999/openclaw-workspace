# Knowledge Base System

## Overview
Personal knowledge base with SQLite storage. Drop any URL → it gets ingested, summarized, and stored for future queries.

## Database
`/root/.openclaw/workspace/knowledge-base/kb.db`

## How to Use

### Ingest a URL
User drops a URL in chat → Agent:
1. Fetches content with `web_fetch`
2. Extracts title, summary, key entities
3. Stores in SQLite via `ingest.sh`

### Search
```bash
./search.sh "OpenAI"           # Search all
./search.sh "OpenAI" article   # Filter by type
```

### Source Types
- `article` — Web articles, blog posts
- `tweet` — X/Twitter posts
- `video` — YouTube videos
- `pdf` — PDF documents
- `job_posting` — Job descriptions
- `company_research` — Company info
- `interview_prep` — Interview materials

### Direct SQL
```bash
sqlite3 kb.db "SELECT title, source_type FROM sources ORDER BY ingested_at DESC LIMIT 10;"
```

## Agent Workflow
When user says "save this" or drops a URL:
1. `web_fetch` the URL
2. Summarize content
3. Extract key entities (people, companies, technologies)
4. Tag appropriately
5. Store via ingest.sh
6. Confirm to user

When user asks about saved content:
1. Search via search.sh or direct SQL
2. Return matching results with links
3. Offer to show full content
