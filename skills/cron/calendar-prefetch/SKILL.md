# Calendar Pre-fetch Skill

Fetch today's Google Calendar events via Composio and save to cache file for the morning briefing.

## Steps

### Step 1: Search Calendar Tools
Use COMPOSIO_SEARCH_TOOLS to find Google Calendar tools

### Step 2: Fetch Events
Call GOOGLECALENDAR_EVENTS_LIST_ALL_CALENDARS with today's date range (Cairo timezone, +02:00)

### Step 3: Save Results
Save results to `/tmp/calendar-events-YYYY-MM-DD.json` as a JSON array

### Step 4: Format Events
Each event should have: title, start, end, calendar, is_all_day

### Step 5: Report
Report count of events found

## Format

```json
[
  {"title": "Team standup", "start": "2026-03-19T09:00:00+02:00", "end": "2026-03-19T09:30:00+02:00", "calendar": "Work", "is_all_day": false},
  {"title": "Eid Holiday", "start": "2026-03-19", "end": "2026-03-20", "calendar": "Holidays in Egypt", "is_all_day": true}
]
```

## Important

- Use Cairo timezone (Africa/Cairo, UTC+2) for time_min and time_max
- time_min = today 00:00:00+02:00, time_max = today 23:59:59+02:00
- Include all calendars (don't filter by calendar_id)
- single_events = true (expand recurring events)

## Error Handling
- If COMPOSIO_SEARCH_TOOLS fails: retry once, then report "Calendar prefetch failed - Composio unavailable"
- If no events returned: save empty array `[]` to cache file, report "0 events"
- If timezone conversion fails: default to UTC+2 offset

## Quality Gates
- Cache file must be valid JSON array
- Each event has: title, start, end, calendar, is_all_day
- File saved to correct date-stamped path

## Manual Run
```bash
cd /root/.openclaw/workspace && openclaw cron run calendar-prefetch
```

## Output Rules
- No em dashes - use hyphens only
- Report format: "Calendar prefetch: [N] events for [YYYY-MM-DD]"
- Include timestamp of fetch in output
- List any all-day events separately from timed events
