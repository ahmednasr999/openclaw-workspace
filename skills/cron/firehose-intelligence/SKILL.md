# Firehose Intelligence - Real-time Web Monitor

## What
Check Firehose.com (by Ahrefs) for new web pages matching NASR's rules. Report job postings, industry trends, and company news.

## Steps
1. Run: `cd /root/.openclaw/workspace && python3 scripts/firehose-monitor.py --check`
2. If output says "No new matches" → report that and stop
3. If matches found → send the report verbatim
4. If jobs found with FIT potential → flag as HIGH PRIORITY

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
