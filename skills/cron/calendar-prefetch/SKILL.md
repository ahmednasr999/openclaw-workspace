# Calendar Pre-fetch Skill

Fetch today's Google Calendar events via Composio and save to cache file for the morning briefing.

## Steps

1. Use COMPOSIO_SEARCH_TOOLS to find Google Calendar tools
2. Call GOOGLECALENDAR_EVENTS_LIST_ALL_CALENDARS with today's date range (Cairo timezone, +02:00)
3. Save results to `/tmp/calendar-events-YYYY-MM-DD.json` as a JSON array
4. Each event should have: title, start, end, calendar, is_all_day
5. Report count of events found

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
