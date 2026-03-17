#!/usr/bin/env python3
"""
Daily Briefing Generator - Premium Google Docs Output
=====================================================
Reads a JSON data file and produces a perfectly formatted Google Doc.
Zero LLM dependency for formatting. Quality is deterministic.

Usage:
    python3 daily-briefing-generator.py --data /path/to/briefing-data.json
    python3 daily-briefing-generator.py --data /path/to/briefing-data.json --doc-id <optional-override>

Data JSON schema: see generate_sample_data() for structure.
"""

import json, sys, argparse, os, subprocess
from datetime import datetime, timezone, timedelta
import requests as req
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Constants
DEFAULT_DOC_ID = "1gtl5sXIsvXiXhODFs29FD9L09i9mGQlsBVIrZbVkTYs"
GOG_TOKEN_PATH = "/tmp/gog-token.json"
GOG_CREDS_PATH = "/root/.openclaw/workspace/config/ahmed-google.json"
ACCOUNT = "ahmednasr999@gmail.com"

# Bold labels to auto-detect and bold
BOLD_LABELS = [
    "Priority Focus:", "Scanner Status:", "LinkedIn:", "Calendar:",
    "Pipeline:", "Company:", "Location:", "ATS Score:", "Link:",
    "File:", "Image:", "GitHub:", "Action:", "Tailored CV:",
    "Fit:", "JD Length:", "Status:", "Author:", "Topic:",
    "Comment Angle:", "Today:", "Upcoming:", "Total Applications:",
    "Responses This Week:", "Follow-ups Overdue:", "Closed:",
    "Recent Applications:", "Top pick:", "Secondary:",
    "Priority engagement:", "New Today:", "Overdue:", "Next Action:",
    "Score:", "Sector:", "Source:", "Posted:", "Freshness:",
    "Applications Sent:", "Interview Stage:", "Awaiting Response:",
    "Ready-to-Post Comment:", "Target Layer:",
    "Improvement Streak:",
]


def get_access_token():
    """Get fresh Google access token via refresh token."""
    # First try to export fresh token from gog
    result = subprocess.run(
        f'GOG_KEYRING_PASSWORD="" gog auth tokens export {ACCOUNT} --out {GOG_TOKEN_PATH} --overwrite',
        shell=True, capture_output=True, text=True
    )

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
        print(f"ERROR: Token refresh failed: {resp.text}")
        sys.exit(1)

    return resp.json()["access_token"]


def clear_document(docs, doc_id):
    """Clear all content from document."""
    doc = docs.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])
    end_index = max((el.get('endIndex', 1) for el in content), default=1)
    if end_index > 2:
        docs.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': [{'deleteContentRange': {'range': {'startIndex': 1, 'endIndex': end_index - 1}}}]}
        ).execute()


def get_document_end(docs, doc_id):
    """Get the end index of existing document content."""
    doc = docs.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])
    return max((el.get('endIndex', 1) for el in content), default=1)


def document_has_content(docs, doc_id):
    """Check if document already has substantial content (not just empty)."""
    end = get_document_end(docs, doc_id)
    return end > 5  # More than just a newline


def build_header_lines():
    """Build document header (only used on first run). Returns list of (text, style) tuples."""
    lines = []
    lines.append(("Ahmed Nasr", "TITLE"))
    lines.append(("Executive Daily Briefing", "SUBTITLE"))
    lines.append(("", "NORMAL_TEXT"))
    return lines


def build_document_lines(data):
    """Build daily content from data JSON. Returns list of (text, style) tuples."""
    lines = []
    bullet = "\u2022"
    checkbox = "\u2610"

    # Get Cairo time
    cairo_tz = timezone(timedelta(hours=2))
    now_cairo = datetime.now(cairo_tz)
    date_str = data.get("date", now_cairo.strftime("%A, %B %d, %Y"))
    update_time = now_cairo.strftime("%B %d, %Y %H:%M Cairo")

    # ===== DATE HEADING (separator between days) =====
    lines.append(("\n", "NORMAL_TEXT"))
    lines.append((date_str, "HEADING_1"))
    lines.append(("", "NORMAL_TEXT"))

    # ===== 1. TODAY'S SUMMARY =====
    summary = data.get("summary", {})
    lines.append(("1. Today's Summary", "HEADING_2"))
    lines.append(("", "NORMAL_TEXT"))
    lines.append((f"Priority Focus: {summary.get('priority_focus', 'Job pipeline + LinkedIn engagement')}", "NORMAL_TEXT"))
    lines.append((f"Scanner Status: {summary.get('scanner_status', 'No scan data')}", "NORMAL_TEXT"))
    lines.append((f"LinkedIn: {summary.get('linkedin_status', 'No posts identified')}", "NORMAL_TEXT"))
    lines.append((f"Calendar: {summary.get('calendar_status', 'No events')}", "NORMAL_TEXT"))
    lines.append((f"Pipeline: {summary.get('pipeline_status', 'No pipeline data')}", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))

    # ===== 2. TODAY'S LINKEDIN POST =====
    todays_post = data.get("todays_post")
    if todays_post:
        lines.append(("2. Today's LinkedIn Post", "HEADING_2"))
        lines.append(("", "NORMAL_TEXT"))
        lines.append((f"File: {todays_post.get('file', 'N/A')}", "NORMAL_TEXT"))
        if todays_post.get("image_filename"):
            lines.append((f"Image: {todays_post['image_filename']} (pre-built, ready to attach)", "NORMAL_TEXT"))
        else:
            lines.append(("Image: No image found for today.", "NORMAL_TEXT"))
        if todays_post.get("github_link"):
            lines.append((f"GitHub: {todays_post['github_link']}", "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

        # Show post content (skip front matter lines starting with # or ---)
        content = todays_post.get("content", "")
        in_content = False
        for cline in content.split("\n"):
            cl = cline.strip()
            if cl.startswith("---"):
                in_content = True
                continue
            if not in_content:
                continue
            if cl.startswith("!["):  # Skip image markdown
                continue
            if cl:
                lines.append((cl, "NORMAL_TEXT"))
            else:
                lines.append(("", "NORMAL_TEXT"))

        lines.append(("", "NORMAL_TEXT"))
        lines.append(("Action: Copy post text above, attach the pre-built image, and publish to LinkedIn.", "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

    # ===== 3. JOBS RADAR =====
    jobs = data.get("jobs", {})
    qualified = jobs.get("qualified", [])
    borderline = jobs.get("borderline", [])
    scanner_note = jobs.get("scanner_note", "")

    lines.append(("3. Jobs Radar", "HEADING_2"))
    lines.append(("", "NORMAL_TEXT"))
    if scanner_note:
        lines.append((scanner_note, "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

    if qualified:
        lines.append(("Qualified Roles (Score 65+)", "HEADING_3"))
        lines.append(("", "NORMAL_TEXT"))

        for i, job in enumerate(qualified, 1):
            lines.append((f"2.{i} {job['title']}", "HEADING_3"))
            lines.append((f"Company: {job.get('company', 'N/A')}", "NORMAL_TEXT"))
            lines.append((f"Location: {job.get('location', 'N/A')}", "NORMAL_TEXT"))
            score_line = f"ATS Score: {job.get('score', 'N/A')}"
            if job.get('status'):
                score_line += f"  |  Status: {job['status']}"
            if job.get('priority'):
                score_line += f"  |  Priority: {job['priority']}"
            lines.append((score_line, "NORMAL_TEXT"))
            if job.get('link'):
                lines.append((f"Link: {job['link']}", "NORMAL_TEXT"))
            if job.get('jd_length'):
                lines.append((f"JD Length: {job['jd_length']}", "NORMAL_TEXT"))
            if job.get('fit'):
                lines.append((f"Fit: {job['fit']}", "NORMAL_TEXT"))
            if job.get('cv_link'):
                status = "Ready to apply" if job.get('cv_status') == 'ready' else 'Pending'
                lines.append((f"Tailored CV: {job['cv_link']} ({status})", "NORMAL_TEXT"))
            lines.append(("", "NORMAL_TEXT"))

    if borderline:
        lines.append(("Executive Leads", "HEADING_3"))
        lines.append(("", "NORMAL_TEXT"))
        for job in borderline:
            lead_line = f"{bullet} {job['title']} | {job.get('company', '')} | {job.get('location', '')}"
            if job.get('score'):
                lead_line += f" | {job['score']}"
            lines.append((lead_line, "NORMAL_TEXT"))
            # v3.1: Show JD flags if available
            if job.get('jd_flag'):
                lines.append((f"  JD Flag: {job['jd_flag'].strip()}", "NORMAL_TEXT"))
            if job.get('jd_fetched') is False:
                lines.append(("  JD: Could not fetch (verdict pending manual review)", "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

    if jobs.get("recommendation"):
        lines.append(("Recommendation", "HEADING_3"))
        lines.append((jobs["recommendation"], "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

    # ===== 3. LINKEDIN ENGAGEMENT =====
    linkedin = data.get("linkedin", {})
    posts = linkedin.get("posts", [])
    categories = linkedin.get("categories", [])

    lines.append(("4. LinkedIn Engagement Opportunities", "HEADING_2"))
    lines.append(("", "NORMAL_TEXT"))
    if linkedin.get("intro"):
        lines.append((linkedin["intro"], "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

    if categories:
        for cat in categories:
            lines.append((cat["name"], "HEADING_3"))
            lines.append(("", "NORMAL_TEXT"))
            for post in cat.get("posts", []):
                lines.append((f"3.{post.get('index', '')} {post['title']}", "HEADING_3"))
                if post.get('author'):
                    lines.append((f"Author: {post['author']}", "NORMAL_TEXT"))
                if post.get('topic'):
                    lines.append((f"Topic: {post['topic']}", "NORMAL_TEXT"))
                if post.get('link'):
                    lines.append((f"Link: {post['link']}", "NORMAL_TEXT"))
                if post.get('comment_angle'):
                    lines.append((f"Comment Angle: {post['comment_angle']}", "NORMAL_TEXT"))
                if post.get('ready_comment'):
                    lines.append(("", "NORMAL_TEXT"))
                    lines.append(("Ready-to-Post Comment:", "NORMAL_TEXT"))
                    lines.append((f"\u201c{post['ready_comment']}\u201d", "NORMAL_TEXT"))
                if post.get('target_layer'):
                    lines.append((f"Target Layer: {post['target_layer']}", "NORMAL_TEXT"))
                lines.append(("", "NORMAL_TEXT"))
    elif posts:
        for i, post in enumerate(posts, 1):
            lines.append((f"3.{i} {post['title']}", "HEADING_3"))
            if post.get('author'):
                lines.append((f"Author: {post['author']}", "NORMAL_TEXT"))
            if post.get('topic'):
                lines.append((f"Topic: {post['topic']}", "NORMAL_TEXT"))
            if post.get('link'):
                lines.append((f"Link: {post['link']}", "NORMAL_TEXT"))
            if post.get('comment_angle'):
                lines.append((f"Comment Angle: {post['comment_angle']}", "NORMAL_TEXT"))
            if post.get('ready_comment'):
                lines.append(("", "NORMAL_TEXT"))
                lines.append(("Ready-to-Post Comment:", "NORMAL_TEXT"))
                lines.append((f"\u201c{post['ready_comment']}\u201d", "NORMAL_TEXT"))
            if post.get('target_layer'):
                lines.append((f"Target Layer: {post['target_layer']}", "NORMAL_TEXT"))
            lines.append(("", "NORMAL_TEXT"))

    if linkedin.get("recommendation"):
        lines.append(("Recommendation", "HEADING_3"))
        lines.append((linkedin["recommendation"], "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

    # ===== 4b. ENGAGEMENT RADAR =====
    radar = data.get("engagement_radar", {})
    if radar.get("status") == "available":
        lines.append(("GCC Influencer Engagement Radar", "HEADING_3"))
        lines.append((f"Profiles scanned: 19 GCC influencers", "NORMAL_TEXT"))
        lines.append((f"Profiles with activity: {radar.get('profiles_with_activity', 'N/A')}", "NORMAL_TEXT"))
        lines.append((radar.get("note", ""), "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))
    elif radar.get("note"):
        lines.append(("GCC Influencer Engagement Radar", "HEADING_3"))
        lines.append((radar["note"], "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

    # ===== 4. CALENDAR & DEADLINES =====
    calendar = data.get("calendar", {})
    events = calendar.get("events", [])
    upcoming = calendar.get("upcoming", [])

    lines.append(("5. Calendar & Deadlines", "HEADING_2"))
    lines.append(("", "NORMAL_TEXT"))

    if events:
        for event in events:
            lines.append((f"{bullet} {event.get('time', '')} - {event.get('title', '')} {event.get('notes', '')}", "NORMAL_TEXT"))
    else:
        lines.append(("Today: No events scheduled", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))

    if upcoming:
        lines.append(("Upcoming:", "NORMAL_TEXT"))
        for item in upcoming:
            lines.append((f"{bullet} {item}", "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

    # ===== 5. PIPELINE STATUS =====
    pipeline = data.get("pipeline", {})

    lines.append(("6. Pipeline Status", "HEADING_2"))
    lines.append(("", "NORMAL_TEXT"))

    if pipeline.get("total_applications"):
        lines.append((f"Total Applications: {pipeline['total_applications']}", "NORMAL_TEXT"))
    if pipeline.get("responses_this_week") is not None:
        lines.append((f"Responses This Week: {pipeline['responses_this_week']}", "NORMAL_TEXT"))
    if pipeline.get("overdue"):
        lines.append((f"Follow-ups Overdue: {pipeline['overdue']}", "NORMAL_TEXT"))
    if pipeline.get("interview_stage"):
        lines.append((f"Interview Stage: {pipeline['interview_stage']}", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))

    if pipeline.get("recent"):
        lines.append(("Recent Applications:", "NORMAL_TEXT"))
        for app in pipeline["recent"]:
            lines.append((f"{bullet} {app}", "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

    if pipeline.get("closed"):
        lines.append((f"Closed: {pipeline['closed']}", "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

    if pipeline.get("recommendation"):
        lines.append(("Recommendation", "HEADING_3"))
        lines.append((pipeline["recommendation"], "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

    # ===== 6. STRATEGIC NOTES =====
    notes = data.get("strategic_notes", [])

    lines.append(("7. Strategic Notes", "HEADING_2"))
    lines.append(("", "NORMAL_TEXT"))
    for note in notes:
        lines.append((f"{bullet} {note}", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))

    # ===== 7. ACTION ITEMS =====
    actions = data.get("action_items", [])

    lines.append(("8. Action Items", "HEADING_2"))
    lines.append(("", "NORMAL_TEXT"))
    for action in actions:
        lines.append((f"{checkbox} {action}", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))

    # ===== FOOTER =====
    lines.append((f"Generated by NASR | OpenClaw | Updated: {update_time}", "NORMAL_TEXT"))

    return lines


def apply_formatting(docs, doc_id, lines, start_index=1):
    """Insert text and apply PREMIUM formatting to Google Doc.
    
    CRITICAL: All styling is applied to FULL PARAGRAPH RANGES to prevent
    split-run issues where Google Docs API splits text into multiple runs
    and only styles part of the text. NEVER style individual runs.
    
    Premium Quality Standard (LOCKED Mar 17, 2026):
    - H1: Date headers only (blue, bold)
    - H2: Section titles (dark, bold)
    - H3: Subsections (dark, bold)
    - KV labels: Bold label, normal value, 10pt
    - Body text: 10pt regular
    - Footer: 8pt grey italic
    - All URLs: clickable hyperlinks
    - Zero split-run tolerance
    """
    all_requests = []

    # Step 1: Insert all text at once
    full_text = "\n".join(text for text, _ in lines)
    all_requests.append({
        'insertText': {'location': {'index': start_index}, 'text': full_text}
    })

    # Step 2: Apply paragraph styles AND full-range text styles together
    # This prevents split-run issues by styling the ENTIRE paragraph range
    current_pos = start_index
    for text, style in lines:
        line_end = current_pos + len(text)
        
        if text:
            if style in ("HEADING_1", "HEADING_2", "HEADING_3"):
                # Paragraph style
                all_requests.append({
                    'updateParagraphStyle': {
                        'range': {'startIndex': current_pos, 'endIndex': line_end + 1},
                        'paragraphStyle': {'namedStyleType': style},
                        'fields': 'namedStyleType'
                    }
                })
                
                # FULL-RANGE text style for headings
                if style == "HEADING_1":
                    all_requests.append({
                        'updateTextStyle': {
                            'range': {'startIndex': current_pos, 'endIndex': line_end},
                            'textStyle': {
                                'bold': True,
                                'foregroundColor': {'color': {'rgbColor': {'red': 0.1, 'green': 0.3, 'blue': 0.7}}}
                            },
                            'fields': 'bold,foregroundColor'
                        }
                    })
                elif style == "HEADING_2":
                    all_requests.append({
                        'updateTextStyle': {
                            'range': {'startIndex': current_pos, 'endIndex': line_end},
                            'textStyle': {
                                'bold': True,
                                'foregroundColor': {'color': {'rgbColor': {'red': 0.15, 'green': 0.15, 'blue': 0.15}}}
                            },
                            'fields': 'bold,foregroundColor'
                        }
                    })
                elif style == "HEADING_3":
                    all_requests.append({
                        'updateTextStyle': {
                            'range': {'startIndex': current_pos, 'endIndex': line_end},
                            'textStyle': {
                                'bold': True,
                                'foregroundColor': {'color': {'rgbColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2}}}
                            },
                            'fields': 'bold,foregroundColor'
                        }
                    })
            
            elif style == "NORMAL_TEXT":
                # Step A: Apply UNIFORM base styling to FULL paragraph range first
                all_requests.append({
                    'updateTextStyle': {
                        'range': {'startIndex': current_pos, 'endIndex': line_end},
                        'textStyle': {
                            'bold': False,
                            'italic': False,
                            'fontSize': {'magnitude': 10, 'unit': 'PT'}
                        },
                        'fields': 'bold,italic,fontSize'
                    }
                })
                
                # Step B: Then bold ONLY the label portion (if KV pair)
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
                        break
        
        current_pos = line_end + 1

    # Step 3: Footer styling (full range, grey italic 8pt)
    footer_prefix = "Generated by NASR"
    footer_idx = full_text.rfind(footer_prefix)
    if footer_idx >= 0:
        footer_start = start_index + footer_idx
        footer_end = start_index + len(full_text)
        all_requests.append({
            'updateTextStyle': {
                'range': {'startIndex': footer_start, 'endIndex': footer_end},
                'textStyle': {
                    'italic': True,
                    'bold': False,
                    'foregroundColor': {'color': {'rgbColor': {'red': 0.5, 'green': 0.5, 'blue': 0.5}}},
                    'fontSize': {'magnitude': 8, 'unit': 'PT'}
                },
                'fields': 'italic,bold,foregroundColor,fontSize'
            }
        })

    # Step 4: Execute all formatting in one batch
    result = docs.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': all_requests}
    ).execute()

    # Step 5: Second pass — make all URLs clickable hyperlinks
    import re
    doc = docs.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])
    url_pattern = re.compile(r'https?://[^\s\n]+')
    link_requests = []

    for element in content:
        if 'paragraph' in element:
            for elem in element['paragraph'].get('elements', []):
                text_run = elem.get('textRun', {})
                text = text_run.get('content', '')
                elem_start = elem.get('startIndex', 0)
                existing_link = text_run.get('textStyle', {}).get('link', {})
                if not existing_link:
                    for match in url_pattern.finditer(text):
                        url = match.group(0)
                        url_start = elem_start + match.start()
                        url_end = elem_start + match.end()
                        link_requests.append({
                            'updateTextStyle': {
                                'range': {'startIndex': url_start, 'endIndex': url_end},
                                'textStyle': {'link': {'url': url}},
                                'fields': 'link'
                            }
                        })

    if link_requests:
        docs.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': link_requests}
        ).execute()
        print(f"Made {len(link_requests)} URLs clickable.")

    # Step 6: Split-run verification (catch any API-induced splits)
    doc = docs.documents().get(documentId=doc_id).execute()
    fix_requests = []
    for element in doc.get('body', {}).get('content', []):
        if 'paragraph' not in element:
            continue
        elements_list = element['paragraph'].get('elements', [])
        if len(elements_list) < 2:
            continue
        named = element['paragraph'].get('paragraphStyle', {}).get('namedStyleType', '')
        if named in ('HEADING_1', 'HEADING_2', 'HEADING_3'):
            # Force uniform styling across ALL runs in this heading
            si = element.get('startIndex', 0)
            ei = element.get('endIndex', 0)
            color = {'red': 0.1, 'green': 0.3, 'blue': 0.7} if named == 'HEADING_1' else {'red': 0.15, 'green': 0.15, 'blue': 0.15}
            fix_requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': si, 'endIndex': ei - 1},
                    'textStyle': {
                        'bold': True,
                        'foregroundColor': {'color': {'rgbColor': color}}
                    },
                    'fields': 'bold,foregroundColor'
                }
            })
    
    if fix_requests:
        docs.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': fix_requests}
        ).execute()
        print(f"Split-run verification: fixed {len(fix_requests)} headings.")

    return len(all_requests) + len(link_requests) + len(fix_requests)


def main():
    parser = argparse.ArgumentParser(description="Generate premium Google Doc briefing")
    parser.add_argument("--data", required=True, help="Path to briefing data JSON")
    parser.add_argument("--doc-id", default=DEFAULT_DOC_ID, help="Google Doc ID")
    parser.add_argument("--fresh", action="store_true", help="Clear document first (fresh start)")
    args = parser.parse_args()

    # Load data
    with open(args.data) as f:
        data = json.load(f)

    print(f"Loading data from {args.data}...")

    # Get access token
    print("Authenticating with Google...")
    access_token = get_access_token()
    creds = Credentials(token=access_token)
    docs = build('docs', 'v1', credentials=creds)

    # --fresh flag or empty doc: clear and write header first
    has_content = document_has_content(docs, args.doc_id)

    if args.fresh or not has_content:
        print("Clearing document and writing header...")
        clear_document(docs, args.doc_id)
        header_lines = build_header_lines()
        num_requests = apply_formatting(docs, args.doc_id, header_lines)
        print(f"Header written ({num_requests} requests).")
        has_content = True  # now it has content for the append below

    # PREPEND: add today's content at the TOP (reverse chronological)
    # Insert after the document header/title section (index 1)
    print("Prepending today's briefing at top...")
    lines = build_document_lines(data)
    insert_index = 1  # Top of document, after any title
    print(f"Inserting at index {insert_index} (top of doc)...")
    num_requests = apply_formatting(docs, args.doc_id, lines, start_index=insert_index)

    print(f"Applied {num_requests} formatting requests.")
    print(f"Document: https://docs.google.com/document/d/{args.doc_id}/edit")

    # ===== SELF-VALIDATION (Fix 1) =====
    warnings = validate_output(docs, args.doc_id, data)
    if warnings:
        print(f"\n⚠️ VALIDATION WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("\n✅ Validation passed: premium format confirmed.")
    print("DONE")


def validate_output(docs, doc_id, data):
    """Post-write validator: catches format and content violations."""
    warnings = []

    # 1. Check that Jobs Radar has no verdicts without JD
    jobs = data.get("jobs", {})
    for job in jobs.get("qualified", []) + jobs.get("borderline", []):
        link = job.get("link", job.get("url", ""))
        if link and "linkedin.com" in link:
            if not job.get("jd_fetched"):
                warnings.append(f"VERDICT WITHOUT JD: {job.get('title', '?')} has no fetched JD. Verdict is unreliable.")

    # 2. Check doc formatting (sample first 20 paragraphs of today's section)
    try:
        doc = docs.documents().get(documentId=doc_id).execute()
        content = doc.get('body', {}).get('content', [])
        body_paras_checked = 0
        bad_format = 0
        for element in content[-40:]:  # Check last 40 elements (today's section)
            if 'paragraph' in element:
                para = element['paragraph']
                style = para.get('paragraphStyle', {}).get('namedStyleType', 'NORMAL_TEXT')
                if style == 'NORMAL_TEXT':
                    body_paras_checked += 1
                    for run in para.get('elements', []):
                        ts = run.get('textRun', {}).get('textStyle', {})
                        text = run.get('textRun', {}).get('content', '').strip()
                        if text and not ts.get('italic'):
                            bad_format += 1
                            break
        if bad_format > 3:
            warnings.append(f"FORMAT: {bad_format}/{body_paras_checked} body paragraphs missing italic styling.")
    except Exception as e:
        warnings.append(f"FORMAT CHECK FAILED: {e}")

    # 3. Check that scanner_note doesn't contain unverified numbers
    scanner_note = jobs.get("scanner_note", "")
    if scanner_note:
        import re
        numbers = re.findall(r'\d+', scanner_note)
        # Just flag if numbers are present but no source file referenced
        if numbers and "qualified-jobs" not in scanner_note:
            warnings.append(f"UNVERIFIED: scanner_note contains numbers but no source file reference.")

    return warnings


if __name__ == "__main__":
    main()
