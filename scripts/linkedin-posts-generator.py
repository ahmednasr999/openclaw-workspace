#!/usr/bin/env python3
"""
LinkedIn Posts Generator - Premium Google Docs Output
=====================================================
Reads all posts from linkedin/posts/ and produces a master Google Doc.
Zero LLM dependency for formatting. Quality is deterministic.

Usage:
    python3 linkedin-posts-generator.py                    # Create new doc
    python3 linkedin-posts-generator.py --doc-id <id>      # Update existing
"""

import json, sys, os, re, subprocess
from datetime import datetime
import requests as req
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Constants
GOG_TOKEN_PATH = "/tmp/gog-token.json"
GOG_CREDS_PATH = "/root/.config/gogcli/credentials.json"
ACCOUNT = "ahmednasr999@gmail.com"
POSTS_DIR = "/root/.openclaw/workspace/linkedin/posts"


def get_access_token():
    """Get fresh Google access token via refresh token."""
    # Load token data
    with open(GOG_TOKEN_PATH) as f:
        token_data = json.load(f)
    
    # Load creds
    with open(GOG_CREDS_PATH) as f:
        creds_data = json.load(f)
    
    # Refresh
    resp = req.post("https://oauth2.googleapis.com/token", data={
        "client_id": creds_data["client_id"],
        "client_secret": creds_data["client_secret"],
        "refresh_token": token_data["refresh_token"],
        "grant_type": "refresh_token"
    })
    
    if resp.status_code != 200:
        raise Exception(f"Token refresh failed: {resp.text}")
    
    return resp.json()["access_token"]


def get_gdocs_service():
    """Build Google Docs service."""
    creds = Credentials(token=get_access_token())
    return build("docs", "v1", credentials=creds)


def parse_post_file(filepath):
    """Parse a single post markdown file."""
    with open(filepath, "r") as f:
        content = f.read()
    
    # Extract frontmatter
    title = ""
    date = ""
    status = "drafted"
    platform = "linkedin"
    
    lines = content.split("\n")
    in_frontmatter = False
    body_lines = []
    
    for line in lines:
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip()
            elif line.startswith("date:"):
                date = line.split(":", 1)[1].strip()
            elif line.startswith("status:"):
                status = line.split(":", 1)[1].strip()
            elif line.startswith("platform:"):
                platform = line.split(":", 1)[1].strip()
        else:
            body_lines.append(line)
    
    body = "\n".join(body_lines).strip()
    
    # Extract image reference
    img_match = re.search(r'!\[.*?\]\(([^)]+)', body)
    image = img_match.group(1) if img_match else None
    
    return {
        "filename": os.path.basename(filepath),
        "title": title,
        "date": date,
        "status": status,
        "platform": platform,
        "body": body,
        "image": image
    }


def build_document_lines(posts):
    """Build document content - returns list of (text, style) tuples."""
    lines = []
    
    # Header
    lines.append(("LinkedIn Posts Collection", "TITLE"))
    lines.append(("Master archive of all drafted posts", "SUBTITLE"))
    lines.append(("", "NORMAL_TEXT"))
    lines.append((f"Last updated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))
    lines.append(("=" * 60, "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))
    
    # Stats
    total = len(posts)
    drafted = sum(1 for p in posts if p["status"] == "drafted")
    posted = sum(1 for p in posts if p["status"] == "posted")
    
    lines.append(("📊 Collection Stats", "HEADING_1"))
    lines.append((f"Total Posts: {total}", "NORMAL_TEXT"))
    lines.append((f"Drafted: {drafted}", "NORMAL_TEXT"))
    lines.append((f"Posted: {posted}", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))
    lines.append(("=" * 60, "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))
    
    # Sort by date (newest first)
    sorted_posts = sorted(posts, key=lambda x: x["date"] or "", reverse=True)
    
    # Each post
    for i, post in enumerate(sorted_posts, 1):
        # Post header
        status_emoji = "✅" if post["status"] == "posted" else "📝"
        lines.append((f"{status_emoji} Post #{i}: {post['title'] or post['date']}", "HEADING_1"))
        
        # Metadata
        lines.append((f"Date: {post['date']}", "NORMAL_TEXT"))
        lines.append((f"Status: {post['status'].upper()}", "NORMAL_TEXT"))
        if post["image"]:
            lines.append((f"Image: {post['image']}", "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))
        
        # Body - handle markdown
        body = post["body"]
        
        # Process body line by line
        for line in body.split("\n"):
            line = line.strip()
            if not line:
                lines.append(("", "NORMAL_TEXT"))
                continue
            
            # Headers
            if line.startswith("### "):
                lines.append((line[4:], "HEADING_3"))
            elif line.startswith("## "):
                lines.append((line[3:], "HEADING_2"))
            elif line.startswith("# "):
                lines.append((line[2:], "HEADING_1"))
            # Bold
            elif "**" in line:
                # Keep markdown, we'll bold in docs
                lines.append((line, "NORMAL_TEXT"))
            # Lists
            elif line.startswith("- ") or line.startswith("* "):
                lines.append((line[2:], "NORMAL_TEXT"))
            # Numbered
            elif re.match(r'^\d+\.', line):
                lines.append((line, "NORMAL_TEXT"))
            # Normal
            else:
                lines.append((line, "NORMAL_TEXT"))
        
        lines.append(("", "NORMAL_TEXT"))
        lines.append(("-" * 60, "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))
    
    return lines


def create_doc(service, title, lines):
    """Create a new Google Doc with content."""
    doc = service.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]
    
    # Insert all text at once
    full_text = "\n".join(text for text, _ in lines)
    
    requests = [{
        'insertText': {'location': {'index': 1}, 'text': full_text}
    }]
    
    # Apply heading styles
    current_pos = 1
    for text, style in lines:
        line_end = current_pos + len(text)
        if style not in ("NORMAL_TEXT",) and text:
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': current_pos, 'endIndex': line_end + 1},
                    'paragraphStyle': {'namedStyleType': style},
                    'fields': 'namedStyleType'
                }
            })
        current_pos = line_end + 1
    
    # Bold **text** patterns
    current_pos = 1
    for text, style in lines:
        if style == "NORMAL_TEXT" and text:
            import re
            for match in re.finditer(r'\*\*([^*]+)\*\*', text):
                start = current_pos + match.start()
                end = current_pos + match.end()
                requests.append({
                    'updateTextStyle': {
                        'range': {'startIndex': start, 'endIndex': end},
                        'textStyle': {'bold': True},
                        'fields': 'bold'
                    }
                })
        current_pos += len(text) + 1
    
    if requests:
        service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
    
    return doc_id


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc-id", help="Existing doc ID to update")
    args = parser.parse_args()
    
    print("📋 LinkedIn Posts Generator")
    print("=" * 40)
    
    # Load all posts
    posts = []
    for f in sorted(os.listdir(POSTS_DIR)):
        if f.endswith(".md"):
            filepath = os.path.join(POSTS_DIR, f)
            post = parse_post_file(filepath)
            posts.append(post)
    
    print(f"Loaded {len(posts)} posts")
    
    # Build document lines
    lines = build_document_lines(posts)
    
    # Create doc
    service = get_gdocs_service()
    title = f"LinkedIn Posts Collection - {datetime.now().strftime('%B %Y')}"
    
    if args.doc_id:
        print(f"Updating existing doc: {args.doc_id}")
        # For now, just create new - update later
        doc_id = create_doc(service, title, lines)
    else:
        print("Creating new doc...")
        doc_id = create_doc(service, title, lines)
    
    print(f"✅ Done! Doc ID: {doc_id}")
    print(f"🔗 https://docs.google.com/document/d/{doc_id}/edit")


if __name__ == "__main__":
    main()
