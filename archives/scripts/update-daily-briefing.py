#!/usr/bin/env python3
"""
Daily Briefing Google Doc Updater
==================================
RULES (NON-NEGOTIABLE):
1. NEVER delete old content. Only PREPEND new day at the top.
2. NEVER fabricate content. Only insert real, verified data.
3. Always reverse chronological order (newest first).
4. All URLs must be clickable hyperlinks.
5. Proper formatting: Title, Subtitle, H1 dates, H2 sections, bold labels, italic grey footer.
6. No duplicate dates. Check before inserting.
7. Backup current doc content before any modification.

Doc ID: 1gtl5sXIsvXiXhODFs29FD9L09i9mGQlsBVIrZbVkTYs
"""

import json, urllib.request, urllib.parse, re, sys, os

DOC_ID = '1gtl5sXIsvXiXhODFs29FD9L09i9mGQlsBVIrZbVkTYs'
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'ahmed-google.json')

def get_access_token():
    with open(CONFIG_PATH) as f:
        creds = json.load(f)
    data = urllib.parse.urlencode({
        'client_id': creds['client_id'],
        'client_secret': creds['client_secret'],
        'refresh_token': creds['refresh_token'],
        'grant_type': 'refresh_token'
    }).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())['access_token']

def get_doc_text(token):
    req = urllib.request.Request(
        f'https://www.googleapis.com/drive/v3/files/{DOC_ID}/export?mimeType=text/plain',
        headers={'Authorization': f'Bearer {token}'}
    )
    resp = urllib.request.urlopen(req)
    return resp.read().decode('utf-8')

def get_doc(token):
    req = urllib.request.Request(
        f'https://docs.googleapis.com/v1/documents/{DOC_ID}',
        headers={'Authorization': f'Bearer {token}'}
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

def batch_update(token, requests):
    batch_size = 80
    for i in range(0, len(requests), batch_size):
        batch = requests[i:i+batch_size]
        body = json.dumps({"requests": batch}).encode()
        req = urllib.request.Request(
            f'https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate',
            data=body,
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req)

def check_date_exists(text, date_str):
    """Check if a date already exists in the document."""
    return date_str in text

def find_insert_position(doc):
    """Find the position right after the subtitle to insert new content."""
    found_subtitle = False
    for element in doc['body']['content']:
        if 'paragraph' in element:
            para_text = ""
            for el in element['paragraph'].get('elements', []):
                if 'textRun' in el:
                    para_text += el['textRun']['content']
            if 'Executive Daily Briefing' in para_text:
                found_subtitle = True
                continue
            if found_subtitle:
                # Return the start index of the first content after subtitle
                return element['startIndex']
    # Fallback: insert at position 1
    return 1

def apply_formatting(token, new_content_start, new_content_end):
    """Apply formatting to newly inserted content only."""
    doc = get_doc(token)
    requests = []
    
    for element in doc['body']['content']:
        si = element.get('startIndex', 0)
        ei = element.get('endIndex', 0)
        
        # Only format within the new content range
        if si < new_content_start or si > new_content_end:
            continue
        
        if 'paragraph' in element:
            para_text = ""
            for el in element['paragraph'].get('elements', []):
                if 'textRun' in el:
                    para_text += el['textRun']['content']
            pt = para_text.strip()
            
            # Date headers -> HEADING_1
            if re.match(r'(?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday), March \d+, 2026', pt):
                requests.append({"updateParagraphStyle": {"range": {"startIndex": si, "endIndex": ei}, "paragraphStyle": {"namedStyleType": "HEADING_1"}, "fields": "namedStyleType"}})
            
            # Section headers -> HEADING_2
            elif re.match(r'\d+\. [A-Z]', pt):
                requests.append({"updateParagraphStyle": {"range": {"startIndex": si, "endIndex": ei}, "paragraphStyle": {"namedStyleType": "HEADING_2"}, "fields": "namedStyleType"}})
            
            # Bold labels + clickable links + footer styling
            for el in element['paragraph'].get('elements', []):
                if 'textRun' in el:
                    txt = el['textRun']['content']
                    el_si = el['startIndex']
                    
                    for m in re.finditer(r'(Priority Focus|Scanner Status|Calendar|Pipeline|Pillar|Status|Engagement tip|Action|Session|Budget|File|Image|GitHub|Company|Location|ATS Score|Link|Comment Angle|Target Layer|Recommendation|Author|Topic):', txt):
                        requests.append({"updateTextStyle": {"range": {"startIndex": el_si + m.start(), "endIndex": el_si + m.end()}, "textStyle": {"bold": True}, "fields": "bold"}})
                    
                    for m in re.finditer(r'(https?://[^\s\n]+)', txt):
                        url = m.group(1).rstrip('.,;:)')
                        requests.append({"updateTextStyle": {"range": {"startIndex": el_si + m.start(), "endIndex": el_si + m.start() + len(url)}, "textStyle": {"link": {"url": url}}, "fields": "link"}})
                    
                    if 'Generated by NASR' in txt:
                        gm = txt.find('Generated by NASR')
                        eol = txt.find('\n', gm)
                        if eol == -1:
                            eol = len(txt)
                        requests.append({"updateTextStyle": {"range": {"startIndex": el_si + gm, "endIndex": el_si + eol}, "textStyle": {"italic": True, "foregroundColor": {"color": {"rgbColor": {"red": 0.6, "green": 0.6, "blue": 0.6}}}}, "fields": "italic,foregroundColor"}})
    
    if requests:
        batch_update(token, requests)
    return len(requests)

def prepend_briefing(new_content, date_header):
    """
    Prepend a new day's briefing at the top of the document.
    NEVER deletes old content. Only inserts above existing dated sections.
    """
    token = get_access_token()
    
    # Step 1: Backup - save current text
    current_text = get_doc_text(token)
    backup_path = f'/tmp/briefing-backup-{date_header.replace(", ", "-").replace(" ", "-")}.txt'
    with open(backup_path, 'w') as f:
        f.write(current_text)
    print(f"Backup saved: {backup_path}")
    
    # Step 2: Check if date already exists
    if check_date_exists(current_text, date_header):
        print(f"ERROR: {date_header} already exists in document. Aborting to prevent duplicate.")
        sys.exit(1)
    
    # Step 3: Find insert position (after title/subtitle, before first dated section)
    doc = get_doc(token)
    insert_pos = find_insert_position(doc)
    print(f"Insert position: {insert_pos}")
    
    # Step 4: Insert new content with separator
    content_to_insert = "\n" + new_content + "\n\n"
    insert_req = json.dumps({"requests": [{"insertText": {"location": {"index": insert_pos}, "text": content_to_insert}}]}).encode()
    req = urllib.request.Request(
        f'https://docs.googleapis.com/v1/documents/{DOC_ID}:batchUpdate',
        data=insert_req,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    )
    urllib.request.urlopen(req)
    print(f"Inserted {len(content_to_insert)} chars")
    
    # Step 5: Apply formatting to new content only
    fmt_count = apply_formatting(token, insert_pos, insert_pos + len(content_to_insert))
    print(f"Applied {fmt_count} formatting requests")
    
    print("SUCCESS: Briefing prepended without touching old content.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 update-daily-briefing.py <briefing-file.txt>")
        print("The file should contain the new day's briefing content (without title/subtitle).")
        sys.exit(1)
    
    with open(sys.argv[1]) as f:
        content = f.read()
    
    # Extract date header from content
    m = re.search(r'((?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday), March \d+, 2026)', content)
    if not m:
        print("ERROR: No date header found in content.")
        sys.exit(1)
    
    prepend_briefing(content, m.group(1))
