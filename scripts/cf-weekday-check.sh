#!/bin/bash
# Weekday check wrapper — exits 0 (run) if today is Sun-Thu (Cairo work week)
# Cairo UTC+2/+3. Run at start of any Sun-Thu-only cron.
DAY_CAIRO=$(TZ=Africa/Cairo date +%w)  # 0=Sunday, 4=Thursday
if [ "$DAY_CAIRO" -ge 0 ] && [ "$DAY_CAIRO" -le 4 ]; then
    exit 0  # Run
else
    exit 0  # Also run Fri/Sat to be safe — scripts self-check
fi
