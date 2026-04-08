# OpenClaw <> Notion Sync System

## Overview

This system provides bidirectional synchronization between OpenClaw workspace and Notion, with notifications, analytics, and follow-up reminders.

## Quick Start

```bash
# Full sync
python3 sync_engine.py --full-sync

# Analytics
python3 sync_engine.py --analytics

# Notifications
python3 notify.py --daily
```

## Directory Structure

```
/root/.openclaw/workspace/
├── sync_engine.py       # Main sync engine
├── sync_to_notion.py    # Legacy sync script
├── notify.py            # Notification system
├── response_tracker.py  # Response rate tracking
└── logs/               # Sync logs
```

## Commands

### Sync Engine (`sync_engine.py`)

| Command | Description |
|---------|-------------|
| `--full-sync` | Complete bidirectional sync |
| `--push` | Workspace → Notion |
| `--pull` | Notion → Workspace |
| `--watch` | Continuous sync (every 5 min) |
| `--analytics` | Pipeline metrics |
| `--auto-tag` | AI auto-categorize JDs |

### Notifications (`notify.py`)

| Command | Description |
|---------|-------------|
| `--test` | Test notification |
| `--daily` | Daily briefing |
| `--followups` | Follow-up reminders |
| `--check` | Check status changes |

### Response Tracker (`response_tracker.py`)

| Command | Description |
|---------|-------------|
| `--report` | Full report |
| `--trend` | Trend analysis |
| `--company` | Company breakdown |

## Notion Databases

| Database | ID | Description |
|----------|-----|-------------|
| Job Tracker | `...8140a655d...` | Opportunities pipeline |
| CV Library | `...8124a26bc...` | CV versions |
| Daily Notes | `...819caaece8...` | Journal entries |
| Knowledge Base | `...817fab62c4...` | Memory & learnings |
| Coordination | `...81a0a12ff...` | Dashboard & tasks |
| Skills Catalog | `...81a88e1bd...` | Skills inventory |

## Cron Schedule

| Time | Task |
|------|------|
| Every hour `:00` | Full sync |
| 8 AM daily | Daily briefing |
| 9 AM Monday | Weekly report |

## Analytics Dashboard

```python
# Run analytics
python3 sync_engine.py --analytics
```

Output includes:
- Total opportunities
- By status (Applied, Call, Interview, Offer)
- By ATS score range
- Average salary

## Response Tracking

```bash
# Record outcomes
python3 response_tracker.py --report
```

Track:
- Response rate
- Interview conversion
- Offer rate
- Company-level analysis

## Notifications

Configure Telegram for instant alerts:

```bash
# Test notification
python3 notify.py --test
```

Triggers:
- New applications
- Status changes (Call, Interview, Offer)
- Follow-up reminders

## Files

- `~/.config/notion/api_key` - Notion API key
- `~/.config/telegram/token` - Telegram bot token
- `/root/.openclaw/logs/` - Sync logs

## Best Practices

1. **Run `--auto-tag`** when new JDs are added
2. **Check `--analytics`** weekly to track progress
3. **Enable `--daily`** for morning briefings
4. **Update response tracker** when outcomes are known

## Troubleshooting

### No notifications?
- Check Telegram token: `cat ~/.config/telegram/token`
- Verify chat ID in config

### Sync errors?
- Check logs: `cat /root/.openclaw/logs/sync.log`
- Verify Notion API key: `cat ~/.config/notion/api_key`

### URLs not working?
- GitHub URLs use `blob/main/` not `tree/main/`
- CVs must be committed to git first
