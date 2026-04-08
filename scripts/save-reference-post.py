#!/usr/bin/env python3
"""
Save a LinkedIn post to the reference folder.
Usage:
  python3 save-reference-post.py --post "Post text here..." --label "Results-led authority"
  python3 save-reference-post.py --post "Post text here..." --label "GCC insight" --notes "Performed well, 45 likes"
  python3 save-reference-post.py --interactive

The reference folder is: memory/linkedin-reference-posts.md
Posts saved here are used as examples when drafting new content.
Compounds over time — the more posts, the sharper the drafts.
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
REF_FILE = WORKSPACE / "memory/linkedin-reference-posts.md"


def format_new_post(post_text: str, label: str, notes: str) -> str:
    """Format a new post entry for the reference folder."""
    date = datetime.now().strftime("%Y-%m-%d")
    entry = f"\n---\n\n## Reference Post — {label}\n**Date:** {date}"
    if notes:
        entry += f" | **Notes:** {notes}"
    entry += f"\n\n{post_text.strip()}\n"
    return entry


def append_post(post_text: str, label: str, notes: str) -> None:
    """Append a new post to the reference folder."""
    if not post_text.strip():
        print("ERROR: Post text is empty.")
        sys.exit(1)
    
    # Check file exists
    if not REF_FILE.exists():
        print(f"ERROR: Reference file not found at {REF_FILE}")
        print("Create it first: memory/linkedin-reference-posts.md")
        sys.exit(1)
    
    # Read current content
    current = REF_FILE.read_text()
    
    # Append new entry
    entry = format_new_post(post_text, label, notes)
    new_content = current.rstrip() + entry
    
    # Update "Last updated" in the header
    new_content = new_content.replace(
        "**Last updated:** 2026-04-05",
        f"**Last updated:** {date}"
    )
    
    REF_FILE.write_text(new_content)
    print(f"Added to reference folder: {label}")
    print(f"File: {REF_FILE}")


def interactive_mode():
    """Prompt user to paste post and metadata."""
    print("\n=== Save to LinkedIn Reference Folder ===\n")
    print("Paste the post text (press Enter twice to finish):")
    lines = []
    while True:
        try:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        except EOFError:
            break
    post_text = "\n".join(lines).strip()
    
    label = input("\nLabel (e.g. 'GCC insight', 'Personal story'): ").strip()
    if not label:
        label = "Untitled"
    
    notes = input("Notes (optional, e.g. 'Performed well, 45 likes'): ").strip()
    
    append_post(post_text, label, notes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save a LinkedIn post to the reference folder")
    parser.add_argument("--post", help="Post text (or use --interactive)")
    parser.add_argument("--label", default="Untitled", help="Short label for this post")
    parser.add_argument("--notes", default="", help="Notes about this post (e.g. performance)")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    elif args.post:
        append_post(args.post, args.label, args.notes)
    else:
        print("Usage: save-reference-post.py --post 'Post text' --label 'GCC insight'")
        print("   or: save-reference-post.py --interactive")
        sys.exit(1)
