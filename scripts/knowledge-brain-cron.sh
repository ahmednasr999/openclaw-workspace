#!/bin/bash
# Knowledge Brain maintenance cron
cd /root/.openclaw/workspace && python3 scripts/knowledge-brain.py maintain >> logs/knowledge-brain-maintain.log 2>&1
