# 📊 Cron Dashboard System - Index & Quick Start

## 🎯 What Is This?

The Cron Dashboard is an automated system that monitors all of Ahmed's cron jobs (system tasks that run on a schedule) and displays their status in a Notion database. It runs every hour and updates the dashboard with the latest information.

## 📁 Key Files

| File | Purpose |
|------|---------|
| **scripts/cron-dashboard-updater.py** | Main Python script that updates the dashboard (16KB) |
| **logs/cron-dashboard-summary.json** | Latest status of all crons in JSON format |
| **logs/CRON-DASHBOARD-REPORT.md** | Detailed report with analysis and action items |
| **logs/CRON-DASHBOARD-INDEX.md** | This file - quick reference guide |

## 🚀 Quick Commands

### View Dashboard in Notion
```
https://www.notion.so/3268d599a1628188b531e25071653203
```

### Manually Update Dashboard Now
```bash
python3 /root/.openclaw/workspace/scripts/cron-dashboard-updater.py
```

### View Latest Summary (JSON)
```bash
cat /root/.openclaw/workspace/logs/cron-dashboard-summary.json | jq '.'
```

### View Detailed Report
```bash
cat /root/.openclaw/workspace/logs/CRON-DASHBOARD-REPORT.md
```

### Check Cron is Registered
```bash
crontab -l | grep cron-dashboard
```

### View Update Logs
```bash
tail -20 /root/.openclaw/workspace/logs/cron-dashboard-updater.log
```

## 📊 Current Status

**Last Updated:** 2026-03-27 14:30 GMT+2

**Crons Monitored:** 23 active system crons → 59 total pages in Notion

**Status Breakdown:**
- ✅ **48 healthy** (81%) - running successfully
- ❌ **7 failing** (12%) - need investigation
- ⚠️ **3 unknown** (5%) - no log files found
- ⏸️ **1 disabled** (2%) - not actively running

## 🚨 Crons Needing Attention

**High Priority (Failing):**
1. `daily-backup.sh` - Backup may not be working
2. `run-briefing-pipeline.sh` - Multiple failing variants
3. `linkedin-engagement-agent.py` - LinkedIn integration issue

**Medium Priority (No Logs):**
4. `key-health-check.sh` - Not logging output
5. `token-health-check.sh` - Not logging output

👉 See `CRON-DASHBOARD-REPORT.md` for full analysis and next steps.

## ⚙️ How It Works

1. **Discovery** - Reads active crons from `crontab -l`
2. **Analysis** - Checks log files to detect success/failure
3. **Update** - Creates or updates Notion pages with status
4. **Reporting** - Saves JSON summary and status report
5. **Schedule** - Runs automatically every hour

## 🔄 Automation

The updater runs automatically:
- **Frequency:** Every hour
- **Time:** Top of the hour (0 * * * *)
- **Command:** Registered in system crontab
- **Output:** Logged to `cron-dashboard-updater.log`

**Next scheduled run:** See crontab for exact time

## 🛠 Log Mappings

The system automatically maps scripts to their log files:

```
daily-backup.sh              → /tmp/openclaw-backup.log
run-briefing-pipeline.sh     → /var/log/briefing/cron.log
github-radar.sh              → /root/.openclaw/workspace/logs/github-radar.log
linkedin-engagement-agent.py → /root/.openclaw/workspace/logs/linkedin-engagement.log
x-radar.sh                   → /root/.openclaw/workspace/logs/x-radar.log
... (23 total)
```

## 🔧 Troubleshooting

### "Unknown" Status Crons
- Indicates no log file was found for that cron
- Check if script has a redirect to a log file
- Add logging if missing

### "Failed" Status Crons
- Log file contains error patterns (error, failed, exception, traceback)
- Review the actual log file to understand the issue
- Example: `tail -100 /tmp/openclaw-backup.log`

### Dashboard Not Updating
- Check cron is registered: `crontab -l | grep cron-dashboard`
- Run manually: `python3 /root/.openclaw/workspace/scripts/cron-dashboard-updater.py`
- Check logs: `tail /root/.openclaw/workspace/logs/cron-dashboard-updater.log`
- Verify Notion token in: `/root/.openclaw/workspace/config/notion.json`

### Notion Connection Error
- Verify Notion token is valid
- Check internet connectivity
- Increase timeout in script if Notion API is slow

## 📈 Dashboard Properties

The Notion database tracks these properties for each cron:

| Property | Type | Description |
|----------|------|-------------|
| Name | Title | Script name |
| Schedule | Text | Cron expression (5-field) |
| Last Status | Select | ✅ OK / ❌ Failed / ⚠️ Unknown / ⏸️ Disabled |
| Last Run | Date | Timestamp from log file |
| Next Run | Date | Calculated next execution |
| Enabled | Checkbox | Always true for active crons |
| Run Window | Date | (Optional) Schedule window |
| Frequency | Select | Hourly / Daily / Weekly / Monthly / Custom |

## 📚 Related Documentation

- Full Report: `CRON-DASHBOARD-REPORT.md`
- Script Source: `scripts/cron-dashboard-updater.py`
- Config: `config/notion.json`

## ✅ Implementation Status

- ✅ Script created and tested
- ✅ Notion database updated (59 pages)
- ✅ Cron job registered (hourly)
- ✅ Documentation complete
- ✅ Status detection working
- ✅ Error handling implemented
- ✅ JSON logging active

---

**Deployed:** 2026-03-27 14:30 GMT+2  
**Maintenance Contact:** Ahmed Nasr  
**Last Verified:** 2026-03-27 14:32 GMT+2
