#!/usr/bin/env python3
"""Create a premium-quality Google Doc briefing with proper formatting."""

import json, requests as req
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

DOC_ID = "1gtl5sXIsvXiXhODFs29FD9L09i9mGQlsBVIrZbVkTYs"

# Load refresh token
with open('/tmp/gog-token.json') as f:
    token_data = json.load(f)

with open('/root/.config/gogcli/credentials.json') as f:
    creds_data = json.load(f)

# Refresh to get access token
resp = req.post("https://oauth2.googleapis.com/token", data={
    "client_id": creds_data["client_id"],
    "client_secret": creds_data["client_secret"],
    "refresh_token": token_data["refresh_token"],
    "grant_type": "refresh_token"
})

if resp.status_code != 200:
    print(f"Token refresh failed: {resp.text}")
    exit(1)

access_token = resp.json()["access_token"]
print("Got access token.")

creds = Credentials(token=access_token)
docs = build('docs', 'v1', credentials=creds)

# Step 1: Clear document
doc = docs.documents().get(documentId=DOC_ID).execute()
content = doc.get('body', {}).get('content', [])
end_index = max((el.get('endIndex', 1) for el in content), default=1)

if end_index > 2:
    docs.documents().batchUpdate(
        documentId=DOC_ID,
        body={'requests': [{'deleteContentRange': {'range': {'startIndex': 1, 'endIndex': end_index - 1}}}]}
    ).execute()
    print("Cleared document.")

# Step 2: Define document structure
# Each entry: (text, style) where style is one of:
# 'TITLE', 'SUBTITLE', 'HEADING_1', 'HEADING_2', 'HEADING_3', 'NORMAL_TEXT'

lines = [
    ("Ahmed Nasr", "TITLE"),
    ("Executive Daily Briefing", "SUBTITLE"),
    ("", "NORMAL_TEXT"),
    ("Thursday, March 12, 2026", "HEADING_1"),
    ("", "NORMAL_TEXT"),
    
    # Section 1
    ("1. Today's Summary", "HEADING_2"),
    ("", "NORMAL_TEXT"),
    ("Priority Focus: Job search pipeline + LinkedIn engagement", "NORMAL_TEXT"),
    ("Scanner Status: 4 qualified roles found (threshold 65+)", "NORMAL_TEXT"),
    ("LinkedIn Posts: 3 engagement opportunities identified", "NORMAL_TEXT"),
    ("Calendar: No events scheduled", "NORMAL_TEXT"),
    ("", "NORMAL_TEXT"),
    
    # Section 2
    ("2. Jobs Radar", "HEADING_2"),
    ("", "NORMAL_TEXT"),
    
    ("2.1 Chief Strategy Officer, National Transformation Delivery", "HEADING_3"),
    ("Company: Confidential Government", "NORMAL_TEXT"),
    ("Location: Riyadh, Saudi Arabia", "NORMAL_TEXT"),
    ("ATS Score: 68/100  |  Status: New", "NORMAL_TEXT"),
    ("Link: https://www.linkedin.com/jobs/view/4382046908", "NORMAL_TEXT"),
    ("Fit: Saudi priority. National transformation aligns with DT experience.", "NORMAL_TEXT"),
    ("", "NORMAL_TEXT"),
    
    ("2.2 Group Chief Executive Officer", "HEADING_3"),
    ("Company: Confidential Government", "NORMAL_TEXT"),
    ("Location: Jeddah, Saudi Arabia", "NORMAL_TEXT"),
    ("ATS Score: 66/100  |  Status: New", "NORMAL_TEXT"),
    ("Link: https://www.linkedin.com/jobs/view/4382549204", "NORMAL_TEXT"),
    ("Fit: C-suite role. Requires broad operational leadership.", "NORMAL_TEXT"),
    ("", "NORMAL_TEXT"),
    
    ("2.3 Executive Director, Smart City Connectivity & IoT", "HEADING_3"),
    ("Company: Confidential Government", "NORMAL_TEXT"),
    ("Location: Riyadh, Saudi Arabia", "NORMAL_TEXT"),
    ("ATS Score: 65/100  |  Status: New", "NORMAL_TEXT"),
    ("Link: https://www.linkedin.com/jobs/view/4382050714", "NORMAL_TEXT"),
    ("Fit: IoT/Smart City focus. Adjacent to DT but niche.", "NORMAL_TEXT"),
    ("", "NORMAL_TEXT"),
    
    ("2.4 Chief Operations Officer (COO), Bahrain", "HEADING_3"),
    ("Company: APM Terminals", "NORMAL_TEXT"),
    ("Location: Al-Hidd, Bahrain", "NORMAL_TEXT"),
    ("ATS Score: 65/100  |  Status: New", "NORMAL_TEXT"),
    ("Link: https://www.linkedin.com/jobs/view/4373942359", "NORMAL_TEXT"),
    ("Fit: Operations heavy. Port/logistics sector.", "NORMAL_TEXT"),
    ("", "NORMAL_TEXT"),
    
    ("Recommendation", "HEADING_3"),
    ("Review Chief Strategy Officer JD (Riyadh, 68/100). Strongest alignment with your digital transformation executive positioning.", "NORMAL_TEXT"),
    ("", "NORMAL_TEXT"),
    
    # Section 3
    ("3. LinkedIn Engagement Opportunities", "HEADING_2"),
    ("", "NORMAL_TEXT"),
    
    ("3.1 GCC Enterprise Digital Readiness 2026", "HEADING_3"),
    ("Author: A4bakr", "NORMAL_TEXT"),
    ("Topic: Saudi Vision 2030 + UAE 2031 digital transformation", "NORMAL_TEXT"),
    ("Link: https://www.linkedin.com/posts/a4bakr_saudivision2030-uae2031-digitaltransformation-activity-7431413967614443520-Tt3B", "NORMAL_TEXT"),
    ("Comment Angle: Share TopMed hospital digitization experience as real-world GCC example.", "NORMAL_TEXT"),
    ("", "NORMAL_TEXT"),
    
    ("3.2 Saudi Digital Economy Milestone", "HEADING_3"),
    ("Author: Mohammed Nazeer Khan", "NORMAL_TEXT"),
    ("Topic: Saudi Arabia digital economy achievements as of Feb 2026", "NORMAL_TEXT"),
    ("Link: https://www.linkedin.com/posts/mohammednazeerkhan_as-of-february-2026-saudi-arabia-has-reached-activity-7431621798103937024-Dvbq", "NORMAL_TEXT"),
    ("Comment Angle: Connect to healthcare IT transformation within Vision 2030.", "NORMAL_TEXT"),
    ("", "NORMAL_TEXT"),
    
    ("3.3 Digital Shift in UAE/GCC 2026", "HEADING_3"),
    ("Author: Rebecca Farooq", "NORMAL_TEXT"),
    ("Topic: AI and digital transformation in UAE", "NORMAL_TEXT"),
    ("Link: https://www.linkedin.com/posts/rebecca-farooq-mcmi-chmc-4a389098_digitaltransformation-ai-uae-activity-7416741603265908736-MYaH", "NORMAL_TEXT"),
    ("Comment Angle: Perspective on AI adoption gaps in healthcare vs fintech.", "NORMAL_TEXT"),
    ("", "NORMAL_TEXT"),
    
    ("Recommendation", "HEADING_3"),
    ("Engage with post 3.1 first (highest relevance to your positioning).", "NORMAL_TEXT"),
    ("", "NORMAL_TEXT"),
    
    # Section 4
    ("4. Calendar & Deadlines", "HEADING_2"),
    ("", "NORMAL_TEXT"),
    ("Today: No events scheduled", "NORMAL_TEXT"),
    ("", "NORMAL_TEXT"),
    ("Upcoming:", "NORMAL_TEXT"),
    ("\u2022 Weekly goals review: Sunday, March 15", "NORMAL_TEXT"),
    ("\u2022 LinkedIn content: 2-3 posts this week (Sun-Thu)", "NORMAL_TEXT"),
    ("\u2022 Weekly self-improvement cron: Sunday, March 15 at 6 PM Cairo", "NORMAL_TEXT"),
    ("", "NORMAL_TEXT"),
    
    # Section 5
    ("5. Pipeline Status", "HEADING_2"),
    ("", "NORMAL_TEXT"),
    ("Delphi Consulting | Senior AI PM | Interview (Feb 23) | Awaiting response", "NORMAL_TEXT"),
    ("New roles today | 4 qualified | Screening | Review JDs", "NORMAL_TEXT"),
    ("", "NORMAL_TEXT"),
    
    # Section 6
    ("6. Strategic Notes", "HEADING_2"),
    ("", "NORMAL_TEXT"),
    ("\u2022 LinkedIn engagement is low (2-3 likes per post). Increase commenting on others' posts.", "NORMAL_TEXT"),
    ("\u2022 Job scanner: daily 6 AM Cairo. 120 searches across 6 GCC countries.", "NORMAL_TEXT"),
    ("\u2022 ATS threshold: 65+ qualified, 70+ auto-CV trigger.", "NORMAL_TEXT"),
    ("\u2022 Morning briefing cron: Sun-Thu 7 AM Cairo to Slack #ai-content.", "NORMAL_TEXT"),
    ("\u2022 Google Docs integration: Active. Daily briefing auto-appends.", "NORMAL_TEXT"),
    ("", "NORMAL_TEXT"),
    
    # Section 7
    ("7. Action Items", "HEADING_2"),
    ("", "NORMAL_TEXT"),
    ("\u2610 Review Chief Strategy Officer JD (Riyadh, 68/100)", "NORMAL_TEXT"),
    ("\u2610 Comment on GCC Digital Readiness post (LinkedIn)", "NORMAL_TEXT"),
    ("\u2610 Plan next LinkedIn post for this week", "NORMAL_TEXT"),
    ("\u2610 Follow up on Delphi Consulting if no response by Friday", "NORMAL_TEXT"),
    ("", "NORMAL_TEXT"),
    
    # Footer
    ("Generated by NASR | OpenClaw | Updated: March 12, 2026 15:51 UTC", "NORMAL_TEXT"),
]

# Build requests
all_requests = []

# Insert all text at once (reverse order to maintain indices)
full_text = "\n".join(text for text, _ in lines)
all_requests.append({
    'insertText': {
        'location': {'index': 1},
        'text': full_text
    }
})

# Calculate paragraph indices and apply styles
current_pos = 1
for text, style in lines:
    line_end = current_pos + len(text)
    if style != "NORMAL_TEXT" and text:
        all_requests.append({
            'updateParagraphStyle': {
                'range': {'startIndex': current_pos, 'endIndex': line_end + 1},
                'paragraphStyle': {'namedStyleType': style},
                'fields': 'namedStyleType'
            }
        })
    current_pos = line_end + 1  # +1 for newline

# Bold key labels
current_pos = 1
for text, style in lines:
    if style == "NORMAL_TEXT" and text:
        for label in ["Priority Focus:", "Scanner Status:", "LinkedIn Posts:", "Calendar:",
                       "Company:", "Location:", "ATS Score:", "Link:", "Fit:", "Status:",
                       "Author:", "Topic:", "Comment Angle:", "Today:", "Upcoming:"]:
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

# Style the footer
footer_text = "Generated by NASR | OpenClaw | Updated: March 12, 2026 15:51 UTC"
footer_start = full_text.rfind(footer_text) + 1
if footer_start > 0:
    all_requests.append({
        'updateTextStyle': {
            'range': {
                'startIndex': footer_start,
                'endIndex': footer_start + len(footer_text)
            },
            'textStyle': {
                'italic': True,
                'foregroundColor': {
                    'color': {'rgbColor': {'red': 0.5, 'green': 0.5, 'blue': 0.5}}
                },
                'fontSize': {'magnitude': 9, 'unit': 'PT'}
            },
            'fields': 'italic,foregroundColor,fontSize'
        }
    })

# Execute
result = docs.documents().batchUpdate(
    documentId=DOC_ID,
    body={'requests': all_requests}
).execute()

print(f"Applied {len(all_requests)} formatting requests.")
print(f"Document: https://docs.google.com/document/d/{DOC_ID}/edit")
print("DONE - Premium quality document created!")
