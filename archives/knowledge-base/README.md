# Knowledge Base System

## Overview
Personal knowledge base with SQLite storage. Ingest URLs, YouTube videos, PDFs — search with natural language.

## Database
`/root/.openclaw/workspace/knowledge-base/kb.db`

## Commands

### Ingest a URL
```bash
python3 ingest.py <url>           # Auto-detect type
python3 ingest.py <url> article   # Force type: article, video, pdf, tweet
```

### Search
```bash
python3 ingest.py search <query>   # Keyword search
```

### List
```bash
python3 ingest.py list            # Recent sources
```

## Current Sources
| Title | Type | Domain |
|-------|------|--------|
| OpenClaw Gist (26 prompts) | article | gist.github.com |
| Claude Sonnet 4.6 | article | anthropic.com |
| OpenClaw Use Cases | video | youtube.com |
| OpenClaw PDF | pdf | beehiiv.com |

## Source Types
- `article` — Web articles, blog posts
- `video` — YouTube videos
- `pdf` — PDF documents
- `tweet` — X/Twitter posts

## Integration

### When user drops a URL:
1. Run `python3 ingest.py <url>`
2. Confirm saved
3. User can later search

### When user asks about saved content:
1. Run `python3 ingest.py search <query>`
2. Return matching results with links
