# Gmail Drafts - Review & Confirm System

## How It Works

1. **I create drafts** in your Gmail (HealthTech Outreach folder)
2. **You review** them in Gmail
3. **You edit** any that need changes
4. **You confirm** on Telegram
5. **I send** the approved emails

---

## Step 1: Create Drafts in Gmail

```bash
cd ~/.openclaw/workspace/healthtech-directory
python3 gmail-drafts.py create
```

This creates:
- 47 email drafts in Gmail
- Drafts saved to: `outreach/drafts-status.json`

---

## Step 2: Review in Gmail

1. Open Gmail: https://mail.google.com/mail/u/0/#drafts
2. Look for folder: **"HealthTech Outreach"**
3. Review each draft
4. Edit any that need changes
5. When ready, come back to Telegram

---

## Step 3: Confirm on Telegram

Send me one of these commands:

| Command | Action |
|---------|--------|
| **"Approve all"** | Send all 47 emails |
| **"Approve 1-10"** | Send first 10 emails |
| **"Approve 1,3,5"** | Send specific emails |
| **"Send batch 1"** | Send emails 1-10 |
| **"Send now"** | Send all approved drafts |

---

## Draft Status Tracking

| Status | Meaning |
|--------|---------|
| ⏳ Pending | Waiting for your review |
| ✅ Approved | Ready to send |
| 📤 Sent | Email sent |

---

## Quick Commands

### On Telegram:
- `Approve all` - Send everything
- `Approve 1-10` - Send first 10
- `Approve 1,5,7` - Send specific ones
- `Status` - Show draft status
- `Pause` - Stop sending

---

## File Structure

```
outreach/
├── drafts-status.json    ← Tracks all drafts
├── decision-makers.csv   ← Contact info
└── simple-emails.json   ← Email content

healthtech-directory/
├── gmail-drafts.py       ← Create drafts
└── drafts-manager.py    ← Manage drafts
```

---

## Example Workflow

```
1. You: "Create drafts"
2. Me: Creates 47 drafts in Gmail
3. You: Reviews drafts in Gmail
4. You: Edits #3 and #7 in Gmail
5. You: "Approve 1-10, exclude 3,7"
6. Me: Sends 8 emails (1-2, 4-6, 8-10)
7. Me: Updates tracking
```

---

## Safety Features

- ✅ Drafts created before sending
- ✅ You review before sending
- ✅ Selective approval (exclude specific emails)
- ✅ Batch sending (send in groups)
- ✅ Pause anytime

---

## Ready?

Reply **"Create drafts"** and I'll:
1. Create 47 email drafts in Gmail
2. Save tracking file
3. Tell you to review in Gmail

Then reply **"Send batch 1"** when ready!
