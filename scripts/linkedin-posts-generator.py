#!/usr/bin/env python3
"""
LinkedIn Posts Generator - Premium Google Docs Output
=====================================================
Reads all posts from linkedin/posts/ and produces a master Google Doc with image links.
"""

import json, os, re, subprocess, base64
from datetime import datetime
import requests as req
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Constants
GOG_TOKEN_PATH = "/tmp/gog-token.json"
GOG_CREDS_PATH = "/root/.config/gogcli/credentials.json"
ACCOUNT = "ahmednasr999@gmail.com"
POSTS_DIR = "/root/.openclaw/workspace/linkedin/posts"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/ahmednasr999/openclaw-workspace/master/linkedin/posts"


def get_access_token():
    """Get fresh Google access token via refresh token."""
    with open(GOG_TOKEN_PATH) as f:
        token_data = json.load(f)
    with open(GOG_CREDS_PATH) as f:
        creds_data = json.load(f)
    
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
    
    title = ""
    date = ""
    status = "drafted"
    
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
        else:
            body_lines.append(line)
    
    body = "\n".join(body_lines).strip()
    
    img_match = re.search(r'!\[.*?\]\(([^)]+)', body)
    image = img_match.group(1) if img_match else None
    
    return {
        "filename": os.path.basename(filepath),
        "title": title,
        "date": date,
        "status": status,
        "body": body,
        "image": image
    }


def build_document_content(posts):
    """Build document content with image links."""
    content = []
    
    # Header
    content.append(("LinkedIn Posts Collection", "TITLE"))
    content.append(("Master archive with image links", "SUBTITLE"))
    content.append(("", "NORMAL_TEXT"))
    content.append((f"Last updated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", "NORMAL_TEXT"))
    content.append(("", "NORMAL_TEXT"))
    content.append(("=" * 60, "NORMAL_TEXT"))
    content.append(("", "NORMAL_TEXT"))
    
    # Stats
    total = len(posts)
    drafted = sum(1 for p in posts if p["status"] == "drafted")
    posted = sum(1 for p in posts if p["status"] == "posted")
    with_images = sum(1 for p in posts if p["image"])
    
    content.append(("📊 Collection Stats", "HEADING_1"))
    content.append((f"Total Posts: {total}", "NORMAL_TEXT"))
    content.append((f"Drafted: {drafted}", "NORMAL_TEXT"))
    content.append((f"Posted: {posted}", "NORMAL_TEXT"))
    content.append((f"With Images: {with_images}", "NORMAL_TEXT"))
    content.append(("", "NORMAL_TEXT"))
    content.append(("=" * 60, "NORMAL_TEXT"))
    content.append(("", "NORMAL_TEXT"))
    
    # Sort by date (newest first)
    sorted_posts = sorted(posts, key=lambda x: x["date"] or "", reverse=True)
    
    # Each post
    for i, post in enumerate(sorted_posts, 1):
        status_emoji = "✅" if post["status"] == "posted" else "📝"
        content.append((f"{status_emoji} Post #{i}: {post['title'] or post['date']}", "HEADING_1"))
        
        # Metadata
        content.append((f"Date: {post['date']}", "NORMAL_TEXT"))
        content.append((f"Status: {post['status'].upper()}", "NORMAL_TEXT"))
        
        # Image link
        if post["image"]:
            img_url = f"{GITHUB_RAW_BASE}/{post['image']}"
            content.append(("🖼️ Image", "NORMAL_TEXT"))
            content.append((post['image'], "LINK", img_url))
        
        content.append(("", "NORMAL_TEXT"))
        
        # Body
        body = post["body"]
        for line in body.split("\n"):
            line = line.strip()
            if not line:
                content.append(("", "NORMAL_TEXT"))
                continue
            
            if line.startswith("### "):
                content.append((line[4:], "HEADING_3"))
            elif line.startswith("## "):
                content.append((line[3:], "HEADING_2"))
            elif line.startswith("# "):
                content.append((line[2:], "HEADING_1"))
            else:
                content.append((line, "NORMAL_TEXT"))
        
        content.append(("", "NORMAL_TEXT"))
        content.append(("-" * 60, "NORMAL_TEXT"))
        content.append(("", "NORMAL_TEXT"))
    
    return content


def create_doc(service, title, content):
    """Create Google Doc with text and links."""
    # Extract lines and handle LINK type
    lines = [(t, s) for t, s, *extra in content]
    
    # Insert all text
    full_text = "\n".join(text for text, _ in lines)
    
    requests = [{'insertText': {'location': {'index': 1}, 'text': full_text}}]
    
    # Apply heading styles
    current_pos = 1
    for item in content:
        text = item[0]
        style = item[1]
        
        line_end = current_pos + len(text)
        if style not in ("NORMAL_TEXT", "LINK") and text:
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': current_pos, 'endIndex': line_end + 1},
                    'paragraphStyle': {'namedStyleType': style},
                    'fields': 'namedStyleType'
                }
            })
        current_pos = line_end + 1
    
    # Bold **text**
    current_pos = 1
    for item in content:
        text, style = item[0], item[1]
        if style == "NORMAL_TEXT" and text:
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
    
    service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
    
    # Second pass: make image links clickable
    link_requests = []
    current_pos = 1
    
    for item in content:
        text, style = item[0], item[1]
        if style == "LINK" and len(item) > 2:
            url = item[2]
            start = current_pos
            end = current_pos + len(text)
            link_requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': start, 'endIndex': end},
                    'textStyle': {
                        'link': {'url': url},
                        'foregroundColor': {'color': {'rgbColor': {'red': 0.0, 'green': 0.4, 'blue': 0.8}}}
                    },
                    'fields': 'link,foregroundColor'
                }
            })
        current_pos += len(text) + 1
    
    if link_requests:
        try:
            service.documents().batchUpdate(documentId=doc_id, body={"requests": link_requests}).execute()
            print(f"  Added {len(link_requests)} image links")
        except Exception as e:
            print(f"  Link warning: {e}")
    
    return doc_id


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc-id", help="Existing doc ID to update")
    args = parser.parse_args()
    
    print("📋 LinkedIn Posts Generator (with image links)")
    print("=" * 45)
    
    # Load posts
    posts = []
    for f in sorted(os.listdir(POSTS_DIR)):
        if f.endswith(".md"):
            filepath = os.path.join(POSTS_DIR, f)
            post = parse_post_file(filepath)
            posts.append(post)
    
    print(f"Loaded {len(posts)} posts")
    
    # Build content
    content = build_document_content(posts)
    images_with_content = sum(1 for t, s, *e in content if s == "LINK")
    print(f"Found {images_with_content} image links")
    
    # Create doc
    service = get_gdocs_service()
    title = f"LinkedIn Posts - {datetime.now().strftime('%B %Y')}"
    
    print("Creating doc...")
    global doc_id
    doc_id = args.doc_id if args.doc_id else None
    
    if doc_id:
        # Clear existing and rewrite
        from googleapiclient.errors import HttpError
        try:
            doc = service.documents().get(documentId=doc_id).execute()
            title = doc.get('title', title)
            # Clear content
            content_elem = doc.get('body', {}).get('content', [])
            if content_elem:
                end_idx = max(el.get('endIndex', 1) for el in content_elem)
                if end_idx > 1:
                    service.documents().batchUpdate(
                        documentId=doc_id,
                        body={'requests': [{'deleteContentRange': {'range': {'startIndex': 1, 'endIndex': end_idx - 1}}}]}
                    ).execute()
        except:
            doc_id = None
    
    if not doc_id:
        doc = service.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]
    
    doc_id = create_doc(service, title, content)
    
    print(f"✅ Done! Doc ID: {doc_id}")
    print(f"🔗 https://docs.google.com/document/d/{doc_id}/edit")


if __name__ == "__main__":
    main()
