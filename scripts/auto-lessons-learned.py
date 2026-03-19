#!/usr/bin/env python3
"""
Auto Lessons Learned - Extracts learnings from session transcripts.

Run this script at session end (via cron or heartbeat) to automatically
capture lessons learned from the day's sessions.

Usage:
    python scripts/auto-lessons-learned.py              # Process latest session
    python scripts/auto-lessons-learned.py --all        # Process all sessions from today
    python scripts/auto-lessons-learned.py --dry-run    # Show what would be extracted
"""

import argparse
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

SESSIONS_DIR = Path.home() / ".openclaw" / "agents" / "main" / "sessions"
LESSONS_FILE = Path("/root/.openclaw/workspace/memory/lessons-learned.md")
MIN_EXCHANGES = 5  # Skip sessions with fewer than 5 exchanges


def get_latest_session():
    """Get the most recent .jsonl session file."""
    sessions = sorted(
        [f for f in SESSIONS_DIR.glob("*.jsonl") if not f.name.endswith(".lock") and not f.name.endswith(".deleted")],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    return sessions[0] if sessions else None


def get_today_sessions():
    """Get all sessions modified today."""
    today = datetime.now()
    sessions = []
    for f in SESSIONS_DIR.glob("*.jsonl"):
        if f.name.endswith(".lock") or f.name.endswith(".deleted"):
            continue
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime.date() == today.date():
            sessions.append(f)
    return sorted(sessions, key=lambda x: x.stat().st_mtime)


def count_exchanges(messages: list) -> int:
    """Count number of user messages (exchanges) in session."""
    count = 0
    for msg in messages:
        if msg.get("type") == "message":
            inner = msg.get("message", {})
            if inner.get("role") == "user":
                count += 1
    return count


def parse_session(filepath: Path) -> dict:
    """Parse a session JSONL file and extract relevant info."""
    messages = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    msg = json.loads(line)
                    messages.append(msg)
                except json.JSONDecodeError:
                    continue
    
    # Get session info from first message
    session_info = messages[0] if messages else {}
    
    # Extract text content from messages
    full_text = ""
    for msg in messages:
        if msg.get("type") == "message":
            inner = msg.get("message", {})
            role = inner.get("role", "unknown")
            content = inner.get("content", "")
            if isinstance(content, str):
                full_text += f"\n{role}: {content}"
            elif isinstance(content, list):
                # Handle multimodal content
                text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
                full_text += f"\n{role}: {' '.join(text_parts)}"
    
    exchange_count = count_exchanges(messages)
    
    return {
        "filepath": filepath.name,
        "message_count": len(messages),
        "exchange_count": exchange_count,
        "text": full_text[:50000],  # Limit to first 50k chars for LLM
        "messages": messages
    }


def format_lesson_entry(lesson: dict, date: str = None) -> str:
    """Format a lesson for the lessons-learned.md file."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    category = lesson.get("category", "improvement")
    category_emoji = {
        "correction": "✏️",
        "error": "❌",
        "preference": "❤️",
        "improvement": "💡",
        "missed_opportunity": "🎯"
    }.get(category, "💡")
    
    return f"""## {date}

### {category_emoji} {category.title()}
- {lesson.get('what_happened', '')} → {lesson.get('what_to_do_differently', '')}
"""


def main():
    parser = argparse.ArgumentParser(description="Auto Lessons Learned")
    parser.add_argument("--all", action="store_true", help="Process all today's sessions")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be extracted")
    args = parser.parse_args()
    
    print(f"📚 Auto Lessons Learned")
    print(f"   Sessions dir: {SESSIONS_DIR}")
    print(f"   Lessons file: {LESSONS_FILE}")
    print()
    
    if args.all:
        sessions = get_today_sessions()
        print(f"📅 Found {len(sessions)} sessions from today")
    else:
        session = get_latest_session()
        sessions = [session] if session else []
        print(f"📄 Latest session: {session.name if session else 'None'}")
    
    if not sessions:
        print("❌ No sessions found")
        return
    
    total_lessons = 0
    significant_sessions = []
    
    for session_file in sessions:
        print(f"\n{'='*50}")
        print(f"Processing: {session_file.name}")
        
        session_data = parse_session(session_file)
        exchanges = session_data["exchange_count"]
        
        print(f"   Messages: {session_data['message_count']}, Exchanges: {exchanges}")
        
        if exchanges < MIN_EXCHANGES:
            print(f"   ⏭️  Skipping (fewer than {MIN_EXCHANGES} exchanges)")
            continue
        
        significant_sessions.append(session_data)
        
        if args.dry_run:
            print(f"   🔍 Would extract lessons from this session")
            print(f"   Preview (first 500 chars): {session_data['text'][:500]}...")
            continue
        
        # Actual lesson extraction would happen here via invoke_llm
        # For now, just mark as processed
        print(f"   ✅ Session ready for lesson extraction")
        total_lessons += 1
    
    print(f"\n{'='*50}")
    print(f"✅ Found {len(significant_sessions)} significant session(s) with {sum(s['exchange_count'] for s in significant_sessions)} total exchanges")
    
    if significant_sessions and not args.dry_run:
        print(f"\n📝 To extract lessons, call invoke_llm with the session text")
        print(f"   (The script returns session data; LLM call happens in workflow)")


if __name__ == "__main__":
    main()
