# Gmail Draft Setup - Complete Guide

## Your Goal

Create 47 email drafts directly in your Gmail that you can:
1. Review in Gmail
2. Edit if needed
3. Confirm on Telegram to send

---

## Step 1: Authenticate with Gmail

Run this command to connect to your Gmail:

```bash
cd ~/.openclaw/workspace/healthtech-directory
./setup-gmail-drafts.sh
```

**What this does:**
1. Checks if gog is installed ✅
2. Asks you to log in to Gmail (opens browser) 🔐
3. Creates 47 email drafts 📧
4. Organizes them in Gmail

---

## Step 2: Review in Gmail

After running the script:

1. Open Gmail: https://mail.google.com/mail/u/0/#drafts
2. Look for drafts with subject "Executive PMO Leadership - ..."
3. Click each draft
4. Review the content
5. Edit if needed
6. Leave as drafts (don't send yet!)

---

## Step 3: Confirm on Telegram

When you're happy with the drafts:

Reply on Telegram:
- **"Send all"** → I send all 47 emails
- **"Send batch 1"** → I send first 10
- **"Send 1,3,5"** → I send specific ones

---

## Commands Reference

### Create Drafts
```bash
./setup-gmail-drafts.sh
```

### List Drafts
```bash
gog gmail drafts list | grep HealthTech
```

### Send All Drafts
```bash
gog gmail drafts list | grep -v '^\[' | xargs -I {} gog gmail drafts send {}
```

### Delete All HealthTech Drafts
```bash
gog gmail drafts list | grep HealthTech | xargs -I {} gog gmail drafts delete {}
```

---

## What Happens Next

```
1. You run: ./setup-gmail-drafts.sh
           ↓
2. gog opens browser → You log in
           ↓
3. 47 drafts created in Gmail
           ↓
4. You review in Gmail
           ↓
5. You confirm: "Send all"
           ↓
6. I send all emails
           ↓
7. You get responses → Schedule calls
```

---

## Troubleshooting

### "gog not installed"
```bash
brew install steipete/tap/gogcli
```

### "Not authenticated"
```bash
gog auth add you@gmail.com --services gmail
```

### "No drafts created"
Check the CSV file exists:
```bash
cat outreach/decision-makers.csv | head -5
```

---

## Files

```
healthtech-directory/
├── setup-gmail-drafts.sh    ← RUN THIS
├── outreach/
│   ├── decision-makers.csv   ← Contact list
│   └── simple-emails.json    ← Email content
└── GMAIL_DRAFTS_SYSTEM.md    ← This guide
```

---

## Ready?

1. Open terminal
2. Run: `./setup-gmail-drafts.sh`
3. Follow prompts
4. Review in Gmail
5. Confirm on Telegram

**Let's do it!**
