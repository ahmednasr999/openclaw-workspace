---
name: meeting-prep
description: "Prepare concise, actionable meeting briefs for tomorrow's calendar events."
---

# Meeting Prep - Calendar Triggered

Build meeting briefs for tomorrow's meetings.

## Prerequisites
- Google Calendar access via Composio or direct API

## Steps

### Step 1: Get tomorrow's calendar
```bash
# Check if Google Calendar is accessible
python3 << 'CAL'
import datetime
tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
print(f"Checking calendar for: {tomorrow}")
# Try to read from Google Calendar via available tools
# If not available, report and exit
CAL
```
If calendar auth is expired, report that clearly and stop.

### Step 2: For each meeting, research
For each event found:
- Who are the attendees? (Search LinkedIn if external)
- What company are they from?
- What's the meeting about? (from description/invite)
- Any recent news about their company?

### Step 3: Build brief
For each meeting:
```
[TIME] - [TITLE]
With: [attendees and their roles]
Prep: [what to prepare - specific documents, talking points]
Talking points:
  1. [specific point based on research]
  2. [specific point]
  3. [specific point]
Context: [any pipeline/application history with this company]
```

### Step 4: Deliver
Send briefs to Telegram by 9 PM the night before.

## Error Handling
- If calendar auth expired: Report "Calendar auth needed - cannot check meetings"
- If no meetings tomorrow: Report "Clear schedule tomorrow - no prep needed"
- If attendee research fails: Provide brief without attendee details

## Quality Gates
- Each brief must have specific talking points, not generic
- Must cross-reference attendees with job pipeline
- Must include company research for external meetings
- Deliver by 9 PM (not midnight, not morning of)

## Output Rules
- No em dashes. Hyphens only.
- One brief per meeting, concise but actionable
- Include LinkedIn profile URLs for external attendees when found
