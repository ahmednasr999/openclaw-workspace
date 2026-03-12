#!/usr/bin/env python3
"""
LinkedIn Posts Generator - Premium Google Docs Output
=====================================================
Reads all posts from linkedin/posts/ and produces a master Google Doc with images.
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


def build_document_content(posts):
    """Build document content with image markers."""
    content = []
    images = []
    
    # Header
    content.append(("LinkedIn Posts Collection", "TITLE"))
    content.append(("Master archive with visuals", "SUBTITLE"))
    content.append(("", "NORMAL_TEXT"))
    content.append((f"Last updated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", "NORMAL_TEXT"))
    content.append(("", "NORMAL_TEXT"))
    content.append(("=" * 60, "NORMAL_TEXT"))
    content.append(("", "NORMAL_TEXT"))
    
    # Stats
    total = len(posts)
    drafted = sum(1 for p in posts if p["status"] == "drafted")
    posted = sum(1 for p in posts if p["status"] == "posted")
    
    content.append(("📊 Collection Stats", "HEADING_1"))
    content.append((f"Total Posts: {total}", "NORMAL_TEXT"))
    content.append((f"Drafted: {drafted}", "NORMAL_TEXT"))
    content.append((f"Posted: {posted}", "NORMAL_TEXT"))
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
        
        # Image - store for later insertion
        if post["image"]:
            img_url = f"{GITHUB_RAW_BASE}/{post['image']}"
            # Add image marker
            marker = f"__IMAGE_{i}__"
            content.append((marker, "IMAGE"))
            images.append((marker, img_url, post['image']))
        
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
    
    return {"content": content, "images": images}


def create_doc_with_images(service, title, data):
    """Create Google Doc with text and images."""
    content = data["content"]
    images = data["images"]
    
    doc = service.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]
    
    # Build text only (skip IMAGE markers for now)
    lines = [(t, s) for t, s in content if s != "IMAGE"]
    
    # Insert all text
    full_text = "\n".join(text for text, _ in lines)
    
    requests = [{'insertText': {'location': {'index': 1}, 'text': full_text}}]
    
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
    
    # Bold **text**
    current_pos = 1
    for text, style in lines:
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
    
    # Insert images using inlineObjects
    # First get the document to find positions
    doc = service.documents().get(documentId=doc_id).execute()
    text_content = "\n".join(text for text, _ in lines)
    
    img_obj_id = 100
    img_requests = []
    
    for marker, img_url, img_name in images:
        # Find line with marker
        lines_list = text_content.split('\n')
        target_line = None
        for idx, line in enumerate(lines_list):
            if marker in line:
                target_line = idx
                break
        
        if target_line is None:
            continue
        
        # Calculate insert position
        pos = sum(len(l) + 1 for l in lines_list[:target_line]) + 1
        
        try:
            # Fetch image
            img_resp = req.get(img_url, timeout=15)
            if img_resp.status_code != 200:
                continue
            image_data = img_resp.content
            
            # Create inline image
            obj_id = f"image_{img_obj_id}"
            img_obj_id += 1
            
            img_requests.append({
                'createInlineImage': {
                    'uri': img_url,
                    'objectSize': {
                        'height': {'magnitude': 450, 'unit': 'PT'},
                        'width': {'magnitude': 600, 'unit': 'PT'}
                    },
                    'location': {'index': pos}
                }
            })
        except Exception as e:
            print(f"  Warning: Could not insert {img_name}: {e}")
            continue
    
    if img_requests:
        try:
            service.documents().batchUpdate(documentId=doc_id, body={"requests": img_requests}).execute()
            print(f"  Inserted {len(img_requests)} images")
        except Exception as e:
            print(f"  Image batch warning: {e}")
    
    return doc_id


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc-id", help="Existing doc ID to update")
    args = parser.parse_args()
    
    print("📋 LinkedIn Posts Generator (with images)")
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
    data = build_document_content(posts)
    images_with_content = sum(1 for _, s in data["content"] if s == "IMAGE")
    print(f"Found {images_with_content} images")
    
    # Create doc
    service = get_gdocs_service()
    title = f"LinkedIn Posts - {datetime.now().strftime('%B %Y')}"
    
    print("Creating doc with images...")
    doc_id = create_doc_with_images(service, title, data)
    
    print(f"✅ Done! Doc ID: {doc_id}")
    print(f"🔗 https://docs.google.com/document/d/{doc_id}/edit")


if __name__ == "__main__":
    main()
