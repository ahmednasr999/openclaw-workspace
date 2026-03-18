---
name: email-check
description: "Check Gmail for job-related emails, categorize them, sync important ones to Notion Email Intelligence DB, and alert on urgent items."
---

# Email Check

Scan Gmail inbox for job-search-relevant emails and sync to Notion.

## Prerequisites
- Himalaya configured with Gmail App Password for ahmednasr999@gmail.com
- Config: `~/.config/himalaya/config.toml`
- Notion Email Intelligence DB: `3278d599-a162-8123-923c-f04999d7292d`
- Script: `scripts/notion_sync.py` with `sync_email_to_notion()` function

## Steps

### Step 1: Fetch recent emails
```bash
himalaya envelope list --account ahmed --folder INBOX --page-size 50 --output json
```

### Step 2: Categorize each email
Apply these rules in order (first match wins):

| Pattern | Category | Priority | Action Required |
|---------|----------|----------|-----------------|
| Subject contains "interview", "screening", "assessment" | 🎯 Interview Invite | 🔴 Urgent | Yes |
| From contains "recruiter", "talent", "hiring", "hr@", "careers@" + positive subject | 📩 Recruiter Response | 🔴 Urgent | Yes |
| Subject contains "unfortunately", "not moving forward", "regret" | ❌ Rejection | 🟢 Low | No |
| Subject contains "application received", "thank you for applying" | ✅ Application Confirmation | 🟢 Low | No |
| Subject contains "job vacancy", "new position", "career opportunity" | 📋 Job Alert | 🟡 Normal | No |
| From contains bayt, gulftalent, linkedin, indeed, naukrigulf | 📋 Job Alert | 🟡 Normal | No |
| Subject contains "follow up", "checking in" | ⏰ Follow-up Needed | 🟡 Normal | Yes |

Skip emails that don't match any category.

### Step 3: Sync to Notion
For each categorized email, call `sync_email_to_notion()` with:
- subject, sender, date, category, company (extract from sender domain)
- Gmail search link: `https://mail.google.com/mail/u/0/#search/subject:{subject}`
- Thread-based dedup (same thread won't create duplicates)

### Step 4: Alert on urgent items
If any 🔴 Urgent emails found:
- Send Telegram alert: "🚨 Urgent email: [subject] from [sender]"
- Only alert on NEW urgent emails (not previously synced)

### Step 5: Report summary
Output: "[X] emails scanned, [Y] job-related synced, [Z] urgent alerts sent"

## Error Handling
- If himalaya connection fails: Report "Gmail IMAP connection error" and stop
- If Notion API fails: Queue emails locally, retry next run
- If duplicate detected: Skip silently (not an error)

## Output Rules
- No em dashes. Use hyphens.
- Report numbers only, not individual email details (unless urgent)
