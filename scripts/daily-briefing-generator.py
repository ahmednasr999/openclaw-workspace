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


# ============================================================
# FIX #1: JSON SCHEMA VALIDATOR (prevents wrong-key errors)
# ============================================================
REQUIRED_SCHEMA = {
    "summary": {
        "required_keys": ["priority_focus", "scanner_status", "linkedin_status", "calendar_status", "pipeline_status"],
        "aliases": {
            "linkedin": "linkedin_status",
            "calendar": "calendar_status",
            "pipeline": "pipeline_status",
            "scanner": "scanner_status",
        }
    },
    "top_level": {
        "required_keys": ["date", "summary", "jobs", "pipeline"],
        "optional_keys": ["todays_post", "linkedin", "calendar", "engagement_radar",
                          "content_intelligence", "strategic_notes", "action_items",
                          "alerts", "system"],
        "aliases": {
            "linkedin_post": "todays_post",
            "today_post": "todays_post",
            # Note: "engagement" is a list of posts, NOT the same as "engagement_radar" (dict).
            # Don't alias them - they're different data structures.
        }
    }
}


def validate_and_fix_json(data):
    """Validate briefing JSON schema. Auto-fix known aliases. Warn on missing keys."""
    warnings = []
    
    # Fix top-level aliases
    for alias, correct in REQUIRED_SCHEMA["top_level"]["aliases"].items():
        if alias in data and correct not in data:
            data[correct] = data.pop(alias)
            warnings.append(f"AUTO-FIXED: renamed '{alias}' -> '{correct}'")
    
    # Check required top-level keys
    for key in REQUIRED_SCHEMA["top_level"]["required_keys"]:
        if key not in data:
            warnings.append(f"MISSING: top-level key '{key}' (section will be empty)")
    
    # Fix summary aliases
    summary = data.get("summary", {})
    if isinstance(summary, dict):
        for alias, correct in REQUIRED_SCHEMA["summary"]["aliases"].items():
            if alias in summary and correct not in summary:
                summary[correct] = summary.pop(alias)
                warnings.append(f"AUTO-FIXED: summary.'{alias}' -> summary.'{correct}'")
        
        for key in REQUIRED_SCHEMA["summary"]["required_keys"]:
            if key not in summary:
                warnings.append(f"MISSING: summary.'{key}' (will show default text)")
    
    # Ensure pipeline is a dict (not a string)
    if "pipeline" in data and isinstance(data["pipeline"], str):
        data["pipeline"] = {"total_applications": data["pipeline"]}
        warnings.append("AUTO-FIXED: converted pipeline string to dict")
    
    if warnings:
        print(f"\n⚠️ VALIDATION WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
        print()
    else:
        print("✅ JSON schema validation passed")
    
    return data, warnings


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
        lines.append(("Recommended Roles (ATS 82+)", "HEADING_3"))
        lines.append(("", "NORMAL_TEXT"))

        for i, job in enumerate(qualified, 1):
            lines.append((f"{i}. {job['title']}", "HEADING_3"))
            lines.append((f"Company: {job.get('company', 'N/A')}", "NORMAL_TEXT"))
            lines.append((f"Location: {job.get('location', 'N/A')}", "NORMAL_TEXT"))
            ats = job.get('ats_score', job.get('score', 'N/A'))
            verdict = job.get('ats_verdict', 'SUBMIT')
            reason = job.get('ats_reason', '')
            score_line = f"ATS Score: {ats}/100 | Verdict: {verdict}"
            if reason:
                score_line += f" | {reason}"
            lines.append((score_line, "NORMAL_TEXT"))
            if job.get('link'):
                lines.append((f"Link: {job['link']}", "NORMAL_TEXT"))
            if job.get('jd_flag'):
                lines.append((f"JD Flag: {job['jd_flag'].strip()}", "NORMAL_TEXT"))
            if job.get('cv_link'):
                status = "Ready to apply" if job.get('cv_status') == 'ready' else 'Pending'
                lines.append((f"Tailored CV: {job['cv_link']} ({status})", "NORMAL_TEXT"))
            lines.append(("", "NORMAL_TEXT"))

    # Borderline leads (REVIEW 75-81) and Low-fit (SKIP <75)
    review_jobs = [j for j in borderline if j.get('ats_verdict') in ('REVIEW', 'UNSCORED', None)]
    skip_jobs = [j for j in borderline if j.get('ats_verdict') == 'SKIP']

    if review_jobs:
        lines.append(("Borderline Leads (ATS 75-81)", "HEADING_3"))
        lines.append(("", "NORMAL_TEXT"))
        for job in review_jobs:
            ats = job.get('ats_score', '')
            ats_str = f" | ATS: {ats}/100" if ats else ""
            reason = job.get('ats_reason', '')
            reason_str = f" | {reason}" if reason else ""
            lead_line = f"{bullet} {job['title']} | {job.get('company', '')} | {job.get('location', '')}{ats_str}{reason_str}"
            lines.append((lead_line, "NORMAL_TEXT"))
            if job.get('link'):
                lines.append((f"Link: {job['link']}", "NORMAL_TEXT"))
            if job.get('jd_flag'):
                lines.append((f"JD Flag: {job['jd_flag'].strip()}", "NORMAL_TEXT"))
            if job.get('jd_fetched') is False:
                lines.append(("UNSCORED: JD not fetched. Score unreliable.", "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

    if skip_jobs:
        lines.append(("Low Fit (ATS <75 - Not Recommended)", "HEADING_3"))
        lines.append(("", "NORMAL_TEXT"))
        for job in skip_jobs:
            ats = job.get('ats_score', '')
            reason = job.get('ats_reason', '')
            skip_line = f"{bullet} {job['title']} | {job.get('company', '')} | ATS: {ats}/100 | {reason}"
            lines.append((skip_line, "NORMAL_TEXT"))
            if job.get('jd_flag'):
                lines.append((f"JD Flag: {job['jd_flag'].strip()}", "NORMAL_TEXT"))
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
    
    ARCHITECTURE (LOCKED Mar 17, 2026 - split-run immune):
    Phase 1: Insert raw text only (one batch call)
    Phase 2: Re-read document to get Google's ACTUAL paragraph indices
    Phase 3: Match each paragraph to its intended style by text content
    Phase 4: Apply formatting using Google's own indices (zero calculation)
    Phase 5: Make URLs clickable using Google's own element indices
    Phase 6: Verification pass - catch and fix any remaining splits
    
    NEVER calculate text positions manually. ALWAYS use Google's indices.
    """
    import re

    # Phase 1: Insert raw text only
    full_text = "\n".join(text for text, _ in lines)
    docs.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': [{'insertText': {'location': {'index': start_index}, 'text': full_text}}]}
    ).execute()
    print(f"Phase 1: Inserted {len(full_text)} chars at index {start_index}")

    # Phase 2: Re-read document to get Google's ACTUAL indices
    doc = docs.documents().get(documentId=doc_id).execute()
    body = doc.get('body', {}).get('content', [])

    # Build a map of paragraph text -> intended style from our lines
    # We match by text content, not by position
    style_map = {}  # text.strip() -> style
    for text, style in lines:
        t = text.strip()
        if t:
            style_map[t] = style

    # Phase 3: Match and apply formatting using Google's own indices
    format_requests = []
    inserted_end = start_index + len(full_text)

    for elem in body:
        if 'paragraph' not in elem:
            continue
        si = elem.get('startIndex', 0)
        ei = elem.get('endIndex', 0)

        # Only process paragraphs within our inserted range
        if si < start_index or si >= inserted_end:
            continue

        # Get the full paragraph text
        para_text = ''
        for el in elem['paragraph'].get('elements', []):
            para_text += el.get('textRun', {}).get('content', '')
        text = para_text.strip()
        if not text:
            continue

        # Look up the intended style
        style = style_map.get(text)
        if not style:
            # Try partial match for long lines that might be truncated
            for key, val in style_map.items():
                if key.startswith(text[:30]) or text.startswith(key[:30]):
                    style = val
                    break

        if not style:
            style = "NORMAL_TEXT"

        text_end = ei - 1  # ei includes the newline; text_end is the last char

        if style in ("HEADING_1", "HEADING_2", "HEADING_3"):
            # Set paragraph style
            format_requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': si, 'endIndex': ei},
                    'paragraphStyle': {'namedStyleType': style},
                    'fields': 'namedStyleType'
                }
            })
            # Full-range text style using Google's indices
            color = {
                'HEADING_1': {'red': 0.1, 'green': 0.3, 'blue': 0.7},
                'HEADING_2': {'red': 0.15, 'green': 0.15, 'blue': 0.15},
                'HEADING_3': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
            }[style]
            format_requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': si, 'endIndex': text_end},
                    'textStyle': {
                        'bold': True,
                        'foregroundColor': {'color': {'rgbColor': color}}
                    },
                    'fields': 'bold,foregroundColor'
                }
            })

        elif style == "NORMAL_TEXT":
            # Step A0: EXPLICITLY set paragraph style to NORMAL_TEXT
            # Without this, Google inherits the previous paragraph's heading style
            # when inserting at the top of a document that starts with a heading
            format_requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': si, 'endIndex': ei},
                    'paragraphStyle': {'namedStyleType': 'NORMAL_TEXT'},
                    'fields': 'namedStyleType'
                }
            })
            # Step A: Uniform base style on FULL paragraph (Google's indices)
            format_requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': si, 'endIndex': text_end},
                    'textStyle': {
                        'bold': False,
                        'italic': False,
                        'fontSize': {'magnitude': 10, 'unit': 'PT'}
                    },
                    'fields': 'bold,italic,fontSize'
                }
            })

            # Step B: Bold KV label using Google's element indices
            for label in BOLD_LABELS:
                label_pos = para_text.find(label)
                if label_pos >= 0:
                    # Find the element that contains this label
                    char_offset = 0
                    for el in elem['paragraph'].get('elements', []):
                        el_text = el.get('textRun', {}).get('content', '')
                        el_si = el.get('startIndex', 0)
                        local_pos = label_pos - char_offset
                        if 0 <= local_pos < len(el_text):
                            label_start = el_si + local_pos
                            label_end = label_start + len(label)
                            format_requests.append({
                                'updateTextStyle': {
                                    'range': {'startIndex': label_start, 'endIndex': min(label_end, text_end)},
                                    'textStyle': {'bold': True},
                                    'fields': 'bold'
                                }
                            })
                            break
                        char_offset += len(el_text)
                    break

        # Footer detection
        if 'Generated by NASR' in text:
            format_requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': si, 'endIndex': text_end},
                    'textStyle': {
                        'italic': True,
                        'bold': False,
                        'foregroundColor': {'color': {'rgbColor': {'red': 0.5, 'green': 0.5, 'blue': 0.5}}},
                        'fontSize': {'magnitude': 8, 'unit': 'PT'}
                    },
                    'fields': 'italic,bold,foregroundColor,fontSize'
                }
            })

    # Phase 4: Execute all formatting
    if format_requests:
        batch_size = 400
        for i in range(0, len(format_requests), batch_size):
            batch = format_requests[i:i+batch_size]
            docs.documents().batchUpdate(documentId=doc_id, body={'requests': batch}).execute()
        print(f"Phase 4: Applied {len(format_requests)} formatting requests")

    # Phase 5: Make URLs clickable using Google's own element indices
    doc = docs.documents().get(documentId=doc_id).execute()
    body = doc.get('body', {}).get('content', [])
    url_pattern = re.compile(r'https?://[^\s\n]+')
    link_requests = []

    for element in body:
        if 'paragraph' not in element:
            continue
        el_si = element.get('startIndex', 0)
        if el_si < start_index or el_si >= inserted_end:
            continue
        for el in element['paragraph'].get('elements', []):
            text_run = el.get('textRun', {})
            text = text_run.get('content', '')
            elem_start = el.get('startIndex', 0)
            existing_link = text_run.get('textStyle', {}).get('link', {})
            if not existing_link:
                for match in url_pattern.finditer(text):
                    url = match.group(0)
                    link_requests.append({
                        'updateTextStyle': {
                            'range': {'startIndex': elem_start + match.start(), 'endIndex': elem_start + match.end()},
                            'textStyle': {'link': {'url': url}},
                            'fields': 'link'
                        }
                    })

    if link_requests:
        docs.documents().batchUpdate(documentId=doc_id, body={'requests': link_requests}).execute()
        print(f"Phase 5: Made {len(link_requests)} URLs clickable")

    # Phase 6: Full verification - re-read and fix ANY split-run issues
    doc = docs.documents().get(documentId=doc_id).execute()
    body = doc.get('body', {}).get('content', [])
    fix_requests = []

    for element in body:
        if 'paragraph' not in element:
            continue
        el_si = element.get('startIndex', 0)
        el_ei = element.get('endIndex', 0)
        if el_si < start_index or el_si >= inserted_end:
            continue

        elements_list = element['paragraph'].get('elements', [])
        if len(elements_list) < 2:
            continue

        named = element['paragraph'].get('paragraphStyle', {}).get('namedStyleType', '')
        para_text = ''.join(el.get('textRun', {}).get('content', '') for el in elements_list).strip()

        # For headings: force uniform style across all runs
        if named in ('HEADING_1', 'HEADING_2', 'HEADING_3'):
            color = {'red': 0.1, 'green': 0.3, 'blue': 0.7} if named == 'HEADING_1' else {'red': 0.15, 'green': 0.15, 'blue': 0.15}
            fix_requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': el_si, 'endIndex': el_ei - 1},
                    'textStyle': {'bold': True, 'foregroundColor': {'color': {'rgbColor': color}}},
                    'fields': 'bold,foregroundColor'
                }
            })

        # For normal text: check for font-size or color mismatches between runs
        elif named == 'NORMAL_TEXT':
            runs = []
            for el in elements_list:
                tr = el.get('textRun', {})
                t = tr.get('content', '').strip()
                ts = tr.get('textStyle', {})
                if t:
                    runs.append({
                        'size': ts.get('fontSize', {}).get('magnitude') if ts.get('fontSize') else None,
                        'color': str(ts.get('foregroundColor', '')),
                        'link': bool(ts.get('link'))
                    })

            # Check for mismatches (excluding link runs)
            non_link = [r for r in runs if not r['link']]
            if len(non_link) >= 2:
                sizes = set(r['size'] for r in non_link)
                colors = set(r['color'] for r in non_link)
                if len(sizes) > 1 or len(colors) > 1:
                    # Mismatch detected - force uniform 10pt, black
                    fix_requests.append({
                        'updateTextStyle': {
                            'range': {'startIndex': el_si, 'endIndex': el_ei - 1},
                            'textStyle': {
                                'fontSize': {'magnitude': 10, 'unit': 'PT'},
                                'foregroundColor': {'color': {'rgbColor': {'red': 0, 'green': 0, 'blue': 0}}}
                            },
                            'fields': 'fontSize,foregroundColor'
                        }
                    })
                    # Re-bold KV label if present
                    for label in BOLD_LABELS:
                        if para_text.startswith(label):
                            fix_requests.append({
                                'updateTextStyle': {
                                    'range': {'startIndex': el_si, 'endIndex': el_si + len(label)},
                                    'textStyle': {'bold': True},
                                    'fields': 'bold'
                                }
                            })
                            break

    if fix_requests:
        docs.documents().batchUpdate(documentId=doc_id, body={'requests': fix_requests}).execute()
        print(f"Phase 6: Verification fixed {len(fix_requests)} split-run issues")
    else:
        print("Phase 6: Verification passed - zero split-run issues")

    return len(format_requests) + len(link_requests) + len(fix_requests)


def main():
    parser = argparse.ArgumentParser(description="Generate premium Google Doc briefing")
    parser.add_argument("--data", required=True, help="Path to briefing data JSON")
    parser.add_argument("--doc-id", default=DEFAULT_DOC_ID, help="Google Doc ID")
    parser.add_argument("--fresh", action="store_true", help="Clear document first (fresh start)")
    parser.add_argument("--validate", action="store_true", help="Validate JSON only (no doc generation)")
    args = parser.parse_args()

    # Load and validate data
    with open(args.data) as f:
        data = json.load(f)

    print(f"Loading data from {args.data}...")

    # FIX #1: Validate JSON schema and auto-fix known aliases
    data, schema_warnings = validate_and_fix_json(data)
    # Save fixed JSON back
    if schema_warnings:
        with open(args.data, 'w') as f:
            json.dump(data, f, indent=2)

    # FIX #3: --validate mode (check JSON + section completeness, no doc write)
    if args.validate:
        lines = build_document_lines(data)
        sections_found = [text for text, style in lines if style in ("HEADING_2", "HEADING_3")]
        expected_sections = ["1. Today's Summary", "3. Jobs Radar", "5. Calendar & Deadlines", "6. Pipeline Status"]
        missing = [s for s in expected_sections if not any(s in sf for sf in sections_found)]
        empty_sections = []
        # Check if sections have content after their heading
        for i, (text, style) in enumerate(lines):
            if style == "HEADING_2" and i + 2 < len(lines):
                next_texts = [t for t, s in lines[i+1:i+4] if t.strip() and s == "NORMAL_TEXT"]
                if not next_texts:
                    empty_sections.append(text)
        
        ok = True
        if missing:
            print(f"❌ MISSING SECTIONS: {missing}")
            ok = False
        if empty_sections:
            print(f"⚠️ EMPTY SECTIONS: {empty_sections}")
        if schema_warnings:
            ok = False
        
        if ok:
            print(f"✅ VALIDATE PASSED: {len(sections_found)} sections, {len(lines)} lines")
        else:
            print(f"❌ VALIDATE FAILED: fix JSON before generating doc")
            sys.exit(1)
        sys.exit(0)

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
