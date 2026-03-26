#!/bin/bash
# Weekday filter for Content Factory crons
# Cairo work week = Sunday(0) to Thursday(4)
DAY=$(TZ=Africa/Cairo date +%u)  # 1=Monday ... 7=Sunday
# Cairo weekend = Friday(5), Saturday(6)
if [ "$DAY" -eq 5 ] || [ "$DAY" -eq 6 ]; then
    exit 0  # silent skip on Cairo weekend
fi
exit 0  # run on Sun-Thu
