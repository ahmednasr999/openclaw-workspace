#!/usr/bin/env python3
"""
LinkedIn Posts Generator - Premium Google Docs Output
====================================================
Uses same formatting approach as daily-briefing-generator.
"""

import json, os, re
from datetime import datetime
import requests as req
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

GOG_TOKEN_PATH = "/tmp/gog-token.json"
GOG_CREDS_PATH = "/root/.config/gogcli/credentials.json"
POSTS_DIR = "/root/.openclaw/workspace/linkedin/posts"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/ahmednasr999/openclaw-workspace/master/linkedin/posts"

BOLD_LABELS = ["Total Posts:", "Drafted:", "Posted:", "With Images:", "Date:", "Status:", "Image:"]


def get_access_token():
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
    return resp.json()["access_token"]


def get_gdocs_service():
    return build("docs", "v1", credentials=Credentials(token=get_access_token()))


def parse_post_file(filepath):
    with open(filepath) as f:
        content = f.read()
    
    title, date, status = "", "", "drafted"
    in_frontmatter = False
    body_lines = []
    
    for line in content.split("\n"):
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
    return {"title": title, "date": date, "status": status, "body": body, "image": img_match.group(1) if img_match else None}


def build_lines(posts):
    lines = []
    
    # Title
    lines.append(("LinkedIn Posts Collection", "TITLE"))
    lines.append(("Master archive with image links", "SUBTITLE"))
    lines.append(("", "NORMAL_TEXT"))
    lines.append((f"Last updated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))
    lines.append(("=" * 60, "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))
    
    # Stats - H1
    lines.append(("📊 Collection Stats", "HEADING_1"))
    lines.append(("", "NORMAL_TEXT"))
    
    total = len(posts)
    drafted = sum(1 for p in posts if p["status"] == "drafted")
    posted = sum(1 for p in posts if p["status"] == "posted")
    with_images = sum(1 for p in posts if p["image"])
    
    lines.append((f"Total Posts: {total}", "NORMAL_TEXT"))
    lines.append((f"Drafted: {drafted}", "NORMAL_TEXT"))
    lines.append((f"Posted: {posted}", "NORMAL_TEXT"))
    lines.append((f"With Images: {with_images}", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))
    lines.append(("=" * 60, "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))
    
    # Posts - sorted by date
    sorted_posts = sorted(posts, key=lambda x: x["date"] or "", reverse=True)
    
    for i, post in enumerate(sorted_posts, 1):
        status_emoji = "✅" if post["status"] == "posted" else "📝"
        
        # H2: Post title
        lines.append((f"{status_emoji} Post #{i}: {post['title'] or post['date']}", "HEADING_2"))
        lines.append(("", "NORMAL_TEXT"))
        
        # Metadata
        if post["date"]:
            lines.append((f"Date: {post['date']}", "NORMAL_TEXT"))
        if post["status"]:
            lines.append((f"Status: {post['status'].upper()}", "NORMAL_TEXT"))
        if post["image"]:
            img_url = f"{GITHUB_RAW_BASE}/{post['image']}"
            lines.append((f"Image: {post['image']}", "NORMAL_TEXT"))
            lines.append((f"[View Image]({img_url})", "NORMAL_TEXT"))
        
        lines.append(("", "NORMAL_TEXT"))
        
        # Body
        for line in post["body"].split("\n"):
            line = line.strip()
            if not line:
                lines.append(("", "NORMAL_TEXT"))
                continue
            if line.startswith("### "):
                lines.append((line[4:], "HEADING_3"))
            elif line.startswith("## "):
                lines.append((line[3:], "HEADING_2"))
            elif line.startswith("# ") and len(line) < 50:
                lines.append((line[2:], "HEADING_2"))
            else:
                lines.append((line, "NORMAL_TEXT"))
        
        lines.append(("", "NORMAL_TEXT"))
        lines.append(("-" * 60, "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))
    
    return lines


def apply_formatting(docs, doc_id, lines):
    """Insert text and apply all formatting - same pattern as daily-briefing-generator."""
    all_requests = []
    
    # Insert all text at once
    full_text = "\n".join(text for text, _ in lines)
    all_requests.append({'insertText': {'location': {'index': 1}, 'text': full_text}})
    
    # Apply heading styles
    current_pos = 1
    for text, style in lines:
        line_end = current_pos + len(text)
        if style not in ("NORMAL_TEXT",) and text:
            all_requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': current_pos, 'endIndex': line_end + 1},
                    'paragraphStyle': {'namedStyleType': style},
                    'fields': 'namedStyleType'
                }
            })
        current_pos = line_end + 1
    
    # Bold key labels
    current_pos = 1
    for text, style in lines:
        if style == "NORMAL_TEXT" and text:
            for label in BOLD_LABELS:
                idx = text.find(label)
                if idx >= 0:
                    all_requests.append({
                        'updateTextStyle': {
                            'range': {
                                'startIndex': current_pos + idx,
                                'endIndex': current_pos + idx + len(label)
                            },
                            'textStyle': {'bold': True},
                            'fields': 'bold'
                        }
                    })
        current_pos += len(text) + 1
    
    docs.documents().batchUpdate(documentId=doc_id, body={'requests': all_requests}).execute()
    
    # Make URLs clickable
    doc = docs.documents().get(documentId=doc_id).execute()
    url_pattern = re.compile(r'https?://[^\s\n]+')
    link_requests = []
    
    for el in doc.get('body', {}).get('content', []):
        if 'paragraph' in el:
            for elem in el['paragraph'].get('elements', []):
                text_run = elem.get('textRun', {})
                text = text_run.get('content', '')
                start_idx = elem.get('startIndex', 0)
                
                if text_run.get('textStyle', {}).get('link'):
                    continue
                
                for match in url_pattern.finditer(text):
                    link_start = start_idx + match.start()
                    link_end = start_idx + match.end()
                    link_requests.append({
                        'updateTextStyle': {
                            'range': {'startIndex': link_start, 'endIndex': link_end},
                            'textStyle': {
                                'link': {'url': match.group()},
                                'foregroundColor': {'color': {'rgbColor': {'red': 0.0, 'green': 0.4, 'blue': 0.8}}}
                            },
                            'fields': 'link,foregroundColor'
                        }
                    })
    
    if link_requests:
        docs.documents().batchUpdate(documentId=doc_id, body={'requests': link_requests}).execute()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc-id", help="Existing doc ID")
    args = parser.parse_args()
    
    print("📋 LinkedIn Posts Generator (Premium Formatting)")
    print("=" * 50)
    
    # Load posts
    posts = [parse_post_file(f"{POSTS_DIR}/{f}") for f in sorted(os.listdir(POSTS_DIR)) if f.endswith(".md")]
    print(f"Loaded {len(posts)} posts")
    
    # Build lines
    lines = build_lines(posts)
    
    # Create/update doc
    docs = get_gdocs_service()
    title = f"LinkedIn Posts - {datetime.now().strftime('%B %Y')}"
    
    if args.doc_id:
        # Clear and rewrite
        try:
            doc = docs.documents().get(documentId=args.doc_id).execute()
            content = doc.get('body', {}).get('content', [])
            if content:
                end_idx = max(el.get('endIndex', 1) for el in content) - 1
                if end_idx > 1:
                    docs.documents().batchUpdate(
                        documentId=args.doc_id,
                        body={'requests': [{'deleteContentRange': {'range': {'startIndex': 1, 'endIndex': end_idx}}}]}
                    ).execute()
            doc_id = args.doc_id
        except:
            doc = docs.documents().create(body={"title": title}).execute()
            doc_id = doc["documentId"]
    else:
        doc = docs.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]
    
    print("Applying premium formatting...")
    apply_formatting(docs, doc_id, lines)
    
    print(f"✅ Done! Doc ID: {doc_id}")
    print(f"🔗 https://docs.google.com/document/d/{doc_id}/edit")


if __name__ == "__main__":
    main()
