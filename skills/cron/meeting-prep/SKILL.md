---
name: meeting-prep
description: "Prepare concise, actionable meeting briefs for tomorrow's calendar events."
---

# Meeting Prep - Calendar Triggered

Build meeting briefs for tomorrow's meetings.

## Prerequisites
- Google Calendar access (currently expired - needs re-auth)
- Company research capability

## Steps

### Step 1: Get tomorrow's calendar
Fetch all events for tomorrow from Google Calendar.

### Step 2: For each meeting, research
- Who are the attendees? (LinkedIn profiles if external)
- What's the meeting about? (from description/invite)
- What prep does Ahmed need?
- Key talking points

### Step 3: Build brief
For each meeting:
```
📅 [Time] - [Title]
👥 With: [attendees]
📋 Prep: [what to prepare]
💡 Talking points: [3 bullet points]
```

### Step 4: Deliver
Send briefs to Telegram by 9 PM the night before.

## Error Handling
- If calendar auth expired: Report "Calendar auth needed - no meeting prep possible"
- If no meetings tomorrow: Report "Clear schedule tomorrow"

## Output Rules
- No em dashes. Hyphens only.
- One brief per meeting, concise
