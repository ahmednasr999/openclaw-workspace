# OAuth Fix Guide

## The Problem

OAuth token exists but is encrypted in keyring and cannot be accessed in this environment.

## Solution

Run this script on your LOCAL machine:

```bash
# Step 1: Download the script
git clone https://github.com/ahmednasr999/openclaw-workspace.git
cd openclaw-workspace/healthtech-directory

# Step 2: Make executable
chmod +x create-local-drafts.sh

# Step 3: Install gog (if not installed)
brew install steipete/tap/gogcli

# Step 4: Authenticate with Gmail
gog auth add you@gmail.com --services gmail

# Step 5: Create 47 drafts
./create-local-drafts.sh
```

---

## What This Does

1. Creates 47 email drafts in your Gmail
2. Organizes them under "HealthTech Outreach" label
3. All personalized with company name and contact

---

## After Running

1. Open Gmail → Review drafts
2. Edit any that need changes
3. Reply "Drafts created" on Telegram
4. I'll help you send them!

---

## Alternative - Quick Fix

If you just want to send emails quickly:

```bash
# Use gog directly
gog gmail send --to "sara.alnaqbi@nationalwellnesspartners" \
  --subject "Executive PMO Leadership - National Wellness Partners" \
  --body-file email-body.txt
```

---

## Files for Local Use

```
healthtech-directory/
├── create-local-drafts.sh    ← RUN THIS LOCALLY
├── decision-makers.csv       ← Contact info
└── simple-emails.json        ← Email content
```
