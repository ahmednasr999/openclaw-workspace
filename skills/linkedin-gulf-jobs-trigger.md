# LinkedIn Gulf Jobs Scanner Trigger

When user sends "run linkedin-gulf-jobs" or "/run linkedin-gulf-jobs" in Slack:

Execute:
```bash
cd /root/.openclaw/workspace && python3 scripts/linkedin-gulf-jobs.py
```

This runs the full LinkedIn Gulf Jobs Scanner v2:
- 120 searches (6 countries × 20 titles)
- ATS scoring (82+ threshold)
- Slack notification to #ai-jobs
