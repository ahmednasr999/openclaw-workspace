#!/usr/bin/env python3
"""
Knowledge Base Ingestion — URLs, YouTube, PDFs
"""

import sys, subprocess, json, os
from datetime import datetime

DB_PATH = "/root/.openclaw/workspace/knowledge-base/kb.db"

def fetch_url(url):
    """Fetch and extract content from URL"""
    result = subprocess.run(
        ["curl", "-s", "-L", "--max-time", "30", url],
        capture_output=True, text=True, timeout=60
    )
    
    if result.returncode == 0:
        return result.stdout[:50000]
    else:
        return None

def extract_video_id(url):
    """Extract YouTube video ID"""
    import re
    patterns = [
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]+)",
        r"youtu\.be/([a-zA-Z0-9_-]+)",
        r"youtube\.com/shorts/([a-zA-Z0-9_-]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_youtube_transcript(video_id):
    """Get YouTube transcript (placeholder - requires yt-dlp or similar)"""
    # Check if yt-dlp is available
    result = subprocess.run(["which", "yt-dlp"], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    
    # Try to get transcript
    result = subprocess.run(
        ["yt-dlp", "--write-subs", "--skip-download", video_id],
        capture_output=True, text=True, timeout=120
    )
    
    if result.returncode == 0:
        # Look for transcript file
        import glob
        files = glob.glob(f"*{video_id}*.vtt") + glob.glob(f"*{video_id}*.txt")
        if files:
            with open(files[0]) as f:
                content = f.read()
            os.remove(files[0])
            return content
    
    return None

def extract_entities(content):
    """Extract key entities from content (simple version)"""
    entities = {
        "people": [],
        "companies": [],
        "technologies": [],
        "topics": []
    }
    
    # Simple patterns
    import re
    
    # Look for capitalized words followed by common terms
    patterns = {
        "companies": [r"([A-Z][a-z]+ (?:Inc|LLC|Corp|Company|Ltd))"],
        "topics": [r"(AI|ML|machine learning|automation|agent|workflow)"]
    }
    
    for category, pats in patterns.items():
        for pattern in pats:
            matches = re.findall(pattern, content, re.IGNORECASE)
            entities[category].extend(list(set(matches)))
    
    return entities

def ingest(url, source_type="article"):
    """Main ingestion function"""
    print(f"\n📥 INGESTING: {url}")
    print("-" * 50)
    
    # Determine source type
    if "youtube.com" in url or "youtu.be" in url:
        source_type = "video"
    elif url.endswith(".pdf"):
        source_type = "pdf"
    elif "twitter.com" in url or "x.com" in url:
        source_type = "tweet"
    
    # Fetch content
    if source_type == "video":
        video_id = extract_video_id(url)
        if video_id:
            transcript = get_youtube_transcript(video_id)
            if transcript:
                content = f"Video ID: {video_id}\n\nTranscript:\n{transcript[:10000]}"
            else:
                print("⚠️ Could not get transcript, fetching page instead")
                content = fetch_url(url)
        else:
            content = fetch_url(url)
    else:
        content = fetch_url(url)
    
    if not content:
        print("❌ Failed to fetch content")
        return False
    
    print(f"✅ Fetched {len(content)} characters")
    
    # Extract title (first line or from URL)
    title = url.split("/")[-1][:100]
    if "\n" in content:
        first_line = content.split("\n")[0].strip()
        if len(first_line) < 200:
            title = first_line
    
    # Extract entities
    entities = extract_entities(content[:5000])
    
    # Store in database
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    
    # Extract summary (first 500 chars)
    summary = content[:500] + "..." if len(content) > 500 else content
    
    conn.execute("""
        INSERT OR IGNORE INTO sources (url, title, source_type, domain, content, key_entities, ingested_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (url, title, source_type, url.split("/")[2], content[:10000], json.dumps(entities)))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Stored: {title[:50]}...")
    print(f"   Type: {source_type}")
    print(f"   Entities: {', '.join(entities['topics'][:5])}")
    
    return True

def search(query, limit=10):
    """Simple keyword search"""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    
    results = conn.execute("""
        SELECT id, url, title, source_type, domain, ingested_at
        FROM sources
        WHERE url LIKE ? OR title LIKE ? OR content LIKE ? OR key_entities LIKE ?
        ORDER BY ingested_at DESC
        LIMIT ?
    """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit)).fetchall()
    
    conn.close()
    
    return results

def list_sources(limit=20):
    """List recent sources"""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    
    results = conn.execute("""
        SELECT id, url, title, source_type, domain, ingested_at
        FROM sources
        ORDER BY ingested_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    
    conn.close()
    return results

def init_db():
    """Initialize sources table"""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            source_type TEXT,
            content TEXT,
            entities TEXT,
            ingested_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sources_url ON sources(url)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(source_type)")
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

if __name__ == "__main__":
    init_db()
    
    if len(sys.argv) < 2:
        print("\n📚 Knowledge Base Ingestion")
        print("=" * 50)
        print("\nUsage:")
        print("  python3 ingest.py <url>           # Ingest URL")
        print("  python3 ingest.py <url> video       # Force video type")
        print("  python3 ingest.py search <query>     # Search")
        print("  python3 ingest.py list              # List sources")
        print("  python3 ingest.py init             # Initialize DB")
        
        # List recent
        print("\n📚 Recent Sources:")
        for r in list_sources(5):
            print(f"   • {r[2][:50]}... ({r[3]})")
        
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "init":
        init_db()
    elif cmd == "list":
        print("\n📚 Sources:")
        for r in list_sources(20):
            print(f"   • {r[2][:60]}... ({r[3]})")
    elif cmd == "search":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        if query:
            print(f"\n🔍 Search: {query}")
            for r in search(query):
                print(f"   • {r[2][:50]}... ({r[1][:50]})")
        else:
            print("Usage: python3 ingest.py search <query>")
    elif cmd.startswith("http"):
        source_type = sys.argv[2] if len(sys.argv) > 2 else "article"
        ingest(cmd, source_type)
    else:
        print("Unknown command. Use: init, list, search <query>, or <url>")
