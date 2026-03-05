# Batch CV Processor — Design Doc

## Sheet ID
`1uKOh3XlsVb6SC0tAHkr239N4Y2d2fQr_BiQJcMHrjNw`

## Sheet URL
https://docs.google.com/spreadsheets/d/1uKOh3XlsVb6SC0tAHkr239N4Y2d2fQr_BiQJcMHrjNw/edit

## Column Map (Sheet1)
| Col | Header | Who fills | Description |
|-----|--------|-----------|-------------|
| A | Link | Ahmed | Job posting URL |
| B | Company | Ahmed | Company name |
| C | Role Title | Ahmed | Role title |
| D | Full JD | Ahmed | Pasted full JD text |
| E | Salary (if listed) | Ahmed | Optional salary info |
| F | Notes | Ahmed | Referral source, urgency, etc |
| G | ATS Score | NASR | Auto-filled after scoring |
| H | Decision | NASR | Apply / Skip / Discuss |
| I | Reason | NASR | Why skip or apply |
| J | CV Status | NASR | Not Started / Ready / PDF Sent |
| K | Ahmed Decision | Ahmed | Go / Skip / Edit |
| L | Applied Date | Ahmed | Date applied |

## Processing Flow
1. Read all rows where column G (ATS Score) is empty = unprocessed
2. For each unprocessed row:
   - Score ATS against master CV (MiniMax M2.5)
   - Fill G (score), H (decision), I (reason)
3. For rows where H = "Apply":
   - Tailor CV (Sonnet 4.6 sub-agent)
   - Generate PDF
   - Update J = "Ready"
4. Send summary to Ahmed via Telegram
5. Ahmed marks K = "Go" for approved CVs
6. Pipeline.md updated for "Go" rows

## Model Assignment
- Sheet read/write: MiniMax M2.5 (via cron)
- ATS scoring: MiniMax M2.5
- CV tailoring: Sonnet 4.6 sub-agent
- Quality check: MiniMax M2.5
- Pipeline update: MiniMax M2.5

## Trigger
- Manual: Ahmed says "process batch"
- Scheduled: Can add cron later if needed
