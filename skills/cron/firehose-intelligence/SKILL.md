# Firehose Intelligence - Real-time Web Monitor

## What
Check Firehose.com (by Ahrefs) for new web pages matching NASR's rules. Report job postings, industry trends, and company news.

## Steps

### Step 1: Run Monitor
Run: `cd /root/.openclaw/workspace && python3 scripts/firehose-monitor.py --check`

### Step 2: Handle No Matches
If output says "No new matches" → report that and stop

### Step 3: Send Matches
If matches found → send the report verbatim

### Step 4: Flag Priority Jobs
If jobs found with FIT potential → flag as HIGH PRIORITY

## Rules (configured in Firehose)
- job-postings-executive: Executive IT/PMO/DT roles
- job-postings-gulf: Any job in GCC region
- industry-trends: Digital transformation + AI news
- company-tracking: Companies Ahmed applied to
- tech-leadership: Technology executive trends

## Output
Send report to Telegram. Format:
- Jobs → 💼 with title + URL
- Trends → 📰 with title + URL
- Company news → 🏢 with title + URL

## Rules
- Do NOT summarize or modify the script output
- If script fails, report the error
- Keep output under 2000 chars for Telegram

## Error Handling
- If script not found: report "firehose-monitor.py missing" and stop
- If script errors: report stderr verbatim, do not retry
- If no matches: report "No new matches" (not an error)

## Quality Gates
- Script must exit 0 for success
- Output under 2000 chars for Telegram
- HIGH PRIORITY flag only for jobs with FIT potential

## Manual Run
```bash
cd /root/.openclaw/workspace && python3 scripts/firehose-monitor.py --check
```

## Output Rules
- No em dashes - use hyphens only
- Keep output under 2000 chars for Telegram delivery
- Jobs prefixed with emoji: 💼 jobs, 📰 trends, 🏢 company news
- Include timestamp and match count in header
