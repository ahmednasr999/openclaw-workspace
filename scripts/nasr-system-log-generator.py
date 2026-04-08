#!/usr/bin/env python3
"""
NASR System Log Generator - Premium Google Docs Output
======================================================
Maintains a running daily log of system operations, improvements, and learnings.
Unlike the briefing (which is rebuilt daily), this APPENDS each day's entry.

Usage:
    python3 nasr-system-log-generator.py --data /path/to/system-log-data.json
    python3 nasr-system-log-generator.py --data /path/to/system-log-data.json --init  (first time only)
"""

import json, sys, argparse, os, re, subprocess
from datetime import datetime, timezone, timedelta
import requests as req
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

DOC_ID = None  # Set after creation
GOG_TOKEN_PATH = "/tmp/gog-token.json"
GOG_CREDS_PATH = "/root/.config/gogcli/credentials.json"
ACCOUNT = "ahmednasr999@gmail.com"
DOC_ID_FILE = "/root/.openclaw/workspace/config/nasr-system-log-doc-id.txt"

BOLD_LABELS = [
    "Streak:", "Total Enhancements:", "Total Errors Fixed:",
    "Cron:", "Script:", "Config:", "Model:", "Source:", "Impact:",
    "Fix:", "Root Cause:", "Prevention:", "Lesson:", "Applied:",
    "Status:", "Result:", "Before:", "After:", "Trigger:",
]


def get_access_token():
    subprocess.run(
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


def get_doc_id():
    if os.path.exists(DOC_ID_FILE):
        with open(DOC_ID_FILE) as f:
            return f.read().strip()
    return None


def save_doc_id(doc_id):
    os.makedirs(os.path.dirname(DOC_ID_FILE), exist_ok=True)
    with open(DOC_ID_FILE, 'w') as f:
        f.write(doc_id)


def create_document(docs, drive):
    """Create the NASR System Log document."""
    doc = docs.documents().create(body={
        'title': 'NASR System Log'
    }).execute()
    doc_id = doc['documentId']
    save_doc_id(doc_id)
    print(f"Created document: {doc_id}")
    return doc_id


def get_document_end(docs, doc_id):
    """Get the end index of the document."""
    doc = docs.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])
    return max((el.get('endIndex', 1) for el in content), default=1)


def build_header_lines():
    """Build the document header (only for init)."""
    lines = []
    lines.append(("NASR System Log", "TITLE"))
    lines.append(("Continuous Improvement Tracker", "SUBTITLE"))
    lines.append(("", "NORMAL_TEXT"))
    lines.append(("This document logs daily system operations, errors, fixes, enhancements, and lessons learned. Each day's entry is appended, creating a permanent record of how the system improves over time.", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))
    return lines


def build_daily_entry(data):
    """Build a single day's log entry."""
    lines = []
    bullet = "\u2022"
    cairo_tz = timezone(timedelta(hours=2))
    now_cairo = datetime.now(cairo_tz)
    date_str = data.get("date", now_cairo.strftime("%A, %B %d, %Y"))
    update_time = now_cairo.strftime("%H:%M Cairo")

    # Day header
    lines.append(("", "NORMAL_TEXT"))
    lines.append((date_str, "HEADING_1"))
    lines.append(("", "NORMAL_TEXT"))

    # Streak & stats
    stats = data.get("stats", {})
    if stats:
        streak = stats.get("streak_days", 1)
        total_enhancements = stats.get("total_enhancements", 0)
        total_errors_fixed = stats.get("total_errors_fixed", 0)
        lines.append((f"Streak: {streak} consecutive days | Total Enhancements: {total_enhancements} | Total Errors Fixed: {total_errors_fixed}", "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

    # Operations Summary
    ops = data.get("operations_summary", {})
    if ops:
        lines.append(("Operations Summary", "HEADING_2"))
        lines.append(("", "NORMAL_TEXT"))
        for key, val in ops.items():
            label = key.replace("_", " ").title()
            lines.append((f"{bullet} {label}: {val}", "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

    # What Went Right
    went_right = data.get("went_right", [])
    lines.append(("What Went Right", "HEADING_2"))
    lines.append(("", "NORMAL_TEXT"))
    if went_right:
        for item in went_right:
            lines.append((f"\u2705 {item}", "NORMAL_TEXT"))
    else:
        lines.append(("No entries today.", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))

    # What Went Wrong
    went_wrong = data.get("went_wrong", [])
    lines.append(("What Went Wrong", "HEADING_2"))
    lines.append(("", "NORMAL_TEXT"))
    if went_wrong:
        for item in went_wrong:
            if isinstance(item, dict):
                lines.append((f"\u274c {item.get('issue', '')}", "NORMAL_TEXT"))
                if item.get('root_cause'):
                    lines.append((f"   Root Cause: {item['root_cause']}", "NORMAL_TEXT"))
                if item.get('fix'):
                    lines.append((f"   Fix: {item['fix']}", "NORMAL_TEXT"))
                if item.get('prevention'):
                    lines.append((f"   Prevention: {item['prevention']}", "NORMAL_TEXT"))
            else:
                lines.append((f"\u274c {item}", "NORMAL_TEXT"))
    else:
        lines.append(("No issues today.", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))

    # Lessons Learned
    lessons = data.get("lessons_learned", [])
    lines.append(("Lessons Learned", "HEADING_2"))
    lines.append(("", "NORMAL_TEXT"))
    if lessons:
        for item in lessons:
            if isinstance(item, dict):
                lines.append((f"\U0001f4a1 {item.get('lesson', '')}", "NORMAL_TEXT"))
                if item.get('applied'):
                    lines.append((f"   Applied: {item['applied']}", "NORMAL_TEXT"))
            else:
                lines.append((f"\U0001f4a1 {item}", "NORMAL_TEXT"))
    else:
        lines.append(("No new lessons today.", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))

    # Enhancements Applied
    enhancements = data.get("enhancements_applied", [])
    lines.append(("Enhancements Applied", "HEADING_2"))
    lines.append(("", "NORMAL_TEXT"))
    if enhancements:
        for item in enhancements:
            if isinstance(item, dict):
                lines.append((f"\u2699\ufe0f {item.get('enhancement', '')}", "NORMAL_TEXT"))
                if item.get('before'):
                    lines.append((f"   Before: {item['before']}", "NORMAL_TEXT"))
                if item.get('after'):
                    lines.append((f"   After: {item['after']}", "NORMAL_TEXT"))
                if item.get('impact'):
                    lines.append((f"   Impact: {item['impact']}", "NORMAL_TEXT"))
            else:
                lines.append((f"\u2699\ufe0f {item}", "NORMAL_TEXT"))
    else:
        lines.append(("No enhancements today.", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))

    # Cron & Script Health
    cron_health = data.get("cron_health", [])
    if cron_health:
        lines.append(("Cron & Script Health", "HEADING_2"))
        lines.append(("", "NORMAL_TEXT"))
        for item in cron_health:
            status_icon = "\u2705" if item.get("status") == "ok" else "\u274c" if item.get("status") == "error" else "\u26a0\ufe0f"
            lines.append((f"{status_icon} {item.get('name', '')}: {item.get('detail', '')}", "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

    # Model Usage
    model_usage = data.get("model_usage", {})
    if model_usage:
        lines.append(("Model Usage", "HEADING_2"))
        lines.append(("", "NORMAL_TEXT"))
        for model, detail in model_usage.items():
            lines.append((f"{bullet} {model}: {detail}", "NORMAL_TEXT"))
        lines.append(("", "NORMAL_TEXT"))

    # Queued for Tomorrow
    tomorrow = data.get("tomorrow_improvements", [])
    lines.append(("Queued for Tomorrow", "HEADING_2"))
    lines.append(("", "NORMAL_TEXT"))
    if tomorrow:
        for item in tomorrow:
            lines.append((f"\u2192 {item}", "NORMAL_TEXT"))
    else:
        lines.append(("No items queued.", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))

    # Entry footer
    lines.append((f"Entry logged at {update_time}", "NORMAL_TEXT"))
    lines.append(("", "NORMAL_TEXT"))
    lines.append(("\u2500" * 60, "NORMAL_TEXT"))

    return lines


def apply_formatting(docs, doc_id, lines, start_index=1):
    """Insert text and apply formatting starting at given index."""
    all_requests = []

    full_text = "\n".join(text for text, _ in lines)
    all_requests.append({
        'insertText': {'location': {'index': start_index}, 'text': full_text}
    })

    # Apply heading styles
    current_pos = start_index
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
    current_pos = start_index
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

    result = docs.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': all_requests}
    ).execute()

    return len(all_requests)


def main():
    parser = argparse.ArgumentParser(description="Generate/append NASR System Log")
    parser.add_argument("--data", required=True, help="Path to system log data JSON")
    parser.add_argument("--init", action="store_true", help="Initialize new document with header")
    parser.add_argument("--doc-id", help="Override Google Doc ID")
    args = parser.parse_args()

    with open(args.data) as f:
        data = json.load(f)

    print("Authenticating with Google...")
    access_token = get_access_token()
    creds = Credentials(token=access_token)
    docs = build('docs', 'v1', credentials=creds)
    drive = build('drive', 'v3', credentials=creds)

    doc_id = args.doc_id or get_doc_id()

    if args.init or not doc_id:
        print("Creating new NASR System Log document...")
        doc_id = create_document(docs, drive)

        # Write header
        header_lines = build_header_lines()
        num = apply_formatting(docs, doc_id, header_lines, start_index=1)
        print(f"Header: {num} formatting requests.")

    # Build daily entry
    print("Building daily entry...")
    daily_lines = build_daily_entry(data)

    # Append at end of document
    end_index = get_document_end(docs, doc_id) - 1
    if end_index < 1:
        end_index = 1

    print(f"Appending at index {end_index}...")
    num = apply_formatting(docs, doc_id, daily_lines, start_index=end_index)

    # Make URLs clickable
    doc = docs.documents().get(documentId=doc_id).execute()
    content = doc.get('body', {}).get('content', [])
    url_pattern = re.compile(r'https?://[^\s\n]+')
    link_requests = []
    for element in content:
        if 'paragraph' in element:
            for elem in element['paragraph'].get('elements', []):
                text_run = elem.get('textRun', {})
                text = text_run.get('content', '')
                si = elem.get('startIndex', 0)
                existing = text_run.get('textStyle', {}).get('link', {})
                if not existing:
                    for match in url_pattern.finditer(text):
                        link_requests.append({
                            'updateTextStyle': {
                                'range': {'startIndex': si + match.start(), 'endIndex': si + match.end()},
                                'textStyle': {'link': {'url': match.group(0)}},
                                'fields': 'link'
                            }
                        })
    if link_requests:
        docs.documents().batchUpdate(documentId=doc_id, body={'requests': link_requests}).execute()
        print(f"Made {len(link_requests)} URLs clickable.")

    print(f"Applied {num} formatting requests.")
    print(f"Document: https://docs.google.com/document/d/{doc_id}/edit")
    print("DONE")


if __name__ == "__main__":
    main()
