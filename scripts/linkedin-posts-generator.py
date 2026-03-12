#!/usr/bin/env python3
"""
LinkedIn Posts Generator v4 - Premium Google Docs
==================================================
Clean approach: text first, then batch all images in one request.
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

BOLD_LABELS = ["Total Posts:", "Drafted:", "Posted:", "With Images:", "Date:", "Status:"]


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
    filename = os.path.basename(filepath)
    with open(filepath) as f:
        content = f.read()
    
    title, date, status = "", "", "drafted"
    in_frontmatter = False
    body_lines = []
    frontmatter_ended = False
    
    for line in content.split("\n"):
        if line.strip() == "---":
            if not frontmatter_ended:
                # First "---" ends frontmatter
                frontmatter_ended = True
                continue
            else:
                # Subsequent "---" are content separators, not frontmatter
                body_lines.append(line)
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
    
    # Extract image
    img_match = re.search(r'!\[.*?\]\(([^)]+)', body)
    image = img_match.group(1) if img_match else None
    body = re.sub(r'!\[.*?\]\([^)]+\)\s*', '', body).strip()
    
    # Extract date from filename if not in frontmatter
    if not date:
        # Patterns: 2026-03-12-topic.md or day-month-dd-topic.md
        date_match = re.match(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            date = date_match.group(1)
        else:
            # Try "mon-mar09" pattern
            day_map = {"jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
                       "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12"}
            day_match = re.match(r'[a-z]+-([a-z]{3})(\d{2})', filename)
            if day_match:
                month = day_map.get(day_match.group(1), "01")
                day = day_match.group(2)
                date = f"2026-{month}-{day}"
    
    # Extract title from content if not in frontmatter
    if not title:
        # Try "# LinkedIn Post -- Day, Month DD, YYYY" header
        header_match = re.search(r'^#\s+LinkedIn Post\s*[—-]+\s*(.+)$', body, re.MULTILINE)
        if header_match:
            title = header_match.group(1).strip()
        else:
            # Try "## Post Draft" section and get first meaningful line after it
            draft_match = re.search(r'## Post Draft\s*\n+(.+)', body)
            if draft_match:
                first_line = draft_match.group(1).strip()
                # Use first line as title (truncate)
                title = first_line[:60] + ("..." if len(first_line) > 60 else "")
        
        # If still no title, use filename
        if not title:
            slug = filename.replace('.md', '')
            title = slug.replace('-', ' ').title()
    
    # Clean body: extract content
    # Format 1: Has "## Post Draft" - extract after it
    # Format 2: No "## Post Draft" - extract after image/metadata block
    body_lines_clean = []
    found_content = False
    
    for line in body.split("\n"):
        stripped = line.strip()
        
        # Skip all metadata/prologue lines
        if stripped.startswith("# LinkedIn Post"):
            continue
        if stripped.startswith("**Pillar:") or stripped.startswith("**Framework:") or stripped.startswith("**Hook Type:") or stripped.startswith("**CTA:"):
            continue
        if "## Post Draft" in stripped:
            found_content = True
            continue
        if "## Image Generated" in stripped:
            continue
        if stripped.startswith("File:") and ".png" in stripped:
            continue
        if stripped.startswith("---"):
            # "---" separator - if we've seen content before, stop. If not, skip it.
            if found_content:
                break
            else:
                continue
            
        # Start collecting content after we hit the first real content line
        if not found_content:
            # First non-skipped line marks start of content
            if stripped:
                found_content = True
                body_lines_clean.append(line)
        else:
            body_lines_clean.append(line)
    
    body = "\n".join(body_lines_clean).strip()
    
    return {"title": title, "date": date, "status": status, "body": body, "image": image}


def format_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
    except:
        return date_str


def build_lines(posts):
    """Build text lines. Track which post indices need images."""
    lines = []
    # Track: for each post with an image, record the line index where image should go
    image_after_line = {}  # line_index -> image_url
    
    lines.append(("LinkedIn Posts Collection", "TITLE"))
    lines.append(("Ahmed Nasr | Executive LinkedIn Content Archive", "SUBTITLE"))
    lines.append(("", "NORMAL_TEXT"))
    lines.append((f"Last updated: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))
    
    lines.append(("Collection Overview", "HEADING_1"))
    lines.append(("", "NORMAL_TEXT"))
    
    total = len(posts)
    drafted = sum(1 for p in posts if p["status"] == "drafted")
    posted = sum(1 for p in posts if p["status"] == "posted")
    with_images = sum(1 for p in posts if p["image"])
    
    lines.append((f"Total Posts: {total}  |  Drafted: {drafted}  |  Posted: {posted}  |  With Images: {with_images}", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))
    
    sorted_posts = sorted(posts, key=lambda x: x["date"] or "", reverse=True)
    
    for i, post in enumerate(sorted_posts, 1):
        status_emoji = "✅" if post["status"] == "posted" else "📝"
        title_text = post['title'] or 'Untitled'
        
        lines.append((f"{status_emoji} Post #{i}: {title_text}", "HEADING_2"))
        
        meta_parts = []
        if post["date"]:
            meta_parts.append(f"Date: {format_date(post['date'])}")
        meta_parts.append(f"Status: {post['status'].upper()}")
        lines.append((" | ".join(meta_parts), "NORMAL_TEXT"))
        
        # Mark this line index for image insertion (image goes after metadata)
        if post["image"]:
            img_url = f"{GITHUB_RAW_BASE}/{post['image']}"
            image_after_line[len(lines) - 1] = img_url
        
        lines.append(("", "NORMAL_TEXT"))
        
        for line in post["body"].split("\n"):
            line = line.strip()
            if not line:
                lines.append(("", "NORMAL_TEXT"))
                continue
            # All body content is NORMAL_TEXT - no headings inside posts
            lines.append((line, "NORMAL_TEXT"))
        
        lines.append(("", "NORMAL_TEXT"))
    
    lines.append(("Generated by NASR | OpenClaw", "NORMAL_TEXT"))
    
    return lines, image_after_line


def apply_formatting(docs, doc_id, lines, image_after_line):
    """Insert text, apply styles, then batch-insert all images."""
    
    # === PASS 1: Insert all text ===
    full_text = "\n".join(text for text, _ in lines)
    text_requests = [{'insertText': {'location': {'index': 1}, 'text': full_text}}]
    
    # Apply styles
    current_pos = 1
    for text, style in lines:
        line_end = current_pos + len(text)
        if style not in ("NORMAL_TEXT",) and text:
            text_requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': current_pos, 'endIndex': line_end + 1},
                    'paragraphStyle': {'namedStyleType': style},
                    'fields': 'namedStyleType'
                }
            })
        current_pos = line_end + 1
    
    # Bold labels
    current_pos = 1
    for text, style in lines:
        if style == "NORMAL_TEXT" and text:
            for label in BOLD_LABELS:
                idx = text.find(label)
                if idx >= 0:
                    text_requests.append({
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
    
    # Footer italic
    footer_text = "Generated by NASR | OpenClaw"
    footer_pos = full_text.rfind(footer_text) + 1
    if footer_pos > 0:
        text_requests.append({
            'updateTextStyle': {
                'range': {'startIndex': footer_pos, 'endIndex': footer_pos + len(footer_text)},
                'textStyle': {'italic': True, 'fontSize': {'magnitude': 8, 'unit': 'PT'},
                              'foregroundColor': {'color': {'rgbColor': {'red': 0.5, 'green': 0.5, 'blue': 0.5}}}},
                'fields': 'italic,fontSize,foregroundColor'
            }
        })
    
    docs.documents().batchUpdate(documentId=doc_id, body={'requests': text_requests}).execute()
    print("  Pass 1: text + styles done")
    
    # === PASS 2: Insert images one at a time ===
    # We search for a unique anchor text near each image position.
    # For each post with an image, we stored the line_idx of the metadata line.
    # We'll search for the metadata text in the doc and insert the image after it.
    
    # Build anchor text -> image_url mapping
    # Use the H2 post title (line before metadata) as anchor since it won't be split by bold
    image_anchors = []
    for line_idx, img_url in image_after_line.items():
        # The H2 title is 1 line before metadata (line_idx - 1 is the title)
        title_idx = line_idx - 1
        if title_idx >= 0 and lines[title_idx][1] == "HEADING_2":
            anchor_text = lines[title_idx][0]
        else:
            anchor_text = lines[line_idx][0]
        image_anchors.append((anchor_text, img_url))
    
    # Process from LAST post to FIRST (bottom-up) to avoid index shifting
    image_anchors.reverse()
    
    success = 0
    for anchor_text, img_url in image_anchors:
        try:
            # Re-read doc fresh each time
            doc = docs.documents().get(documentId=doc_id).execute()
            
            # Find the anchor text (H2 title) in the doc
            # Concatenate all text in each paragraph for matching
            insert_pos = None
            found_title = False
            for j, el in enumerate(doc.get('body', {}).get('content', [])):
                if 'paragraph' in el:
                    # Build full paragraph text
                    para_text = ''.join(
                        elem.get('textRun', {}).get('content', '')
                        for elem in el['paragraph'].get('elements', [])
                    ).strip()
                    
                    if not found_title:
                        if anchor_text and anchor_text.strip() in para_text:
                            found_title = True
                    elif found_title:
                        # This is the metadata line after the title
                        insert_pos = el.get('endIndex', 0) - 1
                        break
            
            if not insert_pos:
                print(f"    Anchor not found: {anchor_text[:40]}")
                continue
            
            # Insert newline + image
            docs.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': [
                    {'insertText': {'location': {'index': insert_pos}, 'text': '\n'}},
                    {'insertInlineImage': {
                        'uri': img_url,
                        'objectSize': {
                            'height': {'magnitude': 280, 'unit': 'PT'},
                            'width': {'magnitude': 450, 'unit': 'PT'}
                        },
                        'location': {'index': insert_pos + 1}
                    }}
                ]}
            ).execute()
            success += 1
        except Exception as e:
            fname = img_url.split('/')[-1]
            print(f"    Failed: {fname}: {str(e)[:60]}")
    
    print(f"  Pass 2: {success}/{len(image_anchors)} images embedded")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc-id", help="Existing doc ID")
    args = parser.parse_args()
    
    print("LinkedIn Posts Generator v4 (Premium)")
    print("=" * 50)
    
    posts = [parse_post_file(f"{POSTS_DIR}/{f}") for f in sorted(os.listdir(POSTS_DIR)) if f.endswith(".md")]
    print(f"Loaded {len(posts)} posts ({sum(1 for p in posts if p['image'])} with images)")
    
    lines, image_after_line = build_lines(posts)
    
    docs = get_gdocs_service()
    title = f"LinkedIn Posts - {datetime.now().strftime('%B %Y')}"
    
    if args.doc_id:
        try:
            doc = docs.documents().get(documentId=args.doc_id).execute()
            content_elems = doc.get('body', {}).get('content', [])
            end_idx = max(el.get('endIndex', 1) for el in content_elems) - 1
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
    
    print(f"Doc: {doc_id}")
    apply_formatting(docs, doc_id, lines, image_after_line)
    
    print(f"\n✅ Done!")
    print(f"🔗 https://docs.google.com/document/d/{doc_id}/edit")


if __name__ == "__main__":
    main()
