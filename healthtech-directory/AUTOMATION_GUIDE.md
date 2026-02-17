# HealthTech Directory - Complete Automation Guide

## Overview

A fully automated job search outreach system for 47 GCC HealthTech companies.

---

## Quick Start

```bash
cd /root/.openclaw/workspace/healthtech-directory

# 1. Review decision makers
cat outreach/decision-makers.csv

# 2. Check tracking sheet
cat outreach/tracking-sheet.csv

# 3. See LinkedIn URLs
cat outreach/linkedin-urls.json

# 4. Run LinkedIn automation
bash linkedin-outreach.sh
```

---

## System Components

### 1. Company Database
```
data/job-search-targets.json (47 companies)
data/gcc-healthtech-enriched.json (357 companies)
```

### 2. Decision Makers
```
outreach/decision-makers.csv (47 DMs)
outreach/decision-makers.json (detailed)
```

### 3. Outreach Automation
```
outreach/automation-queue.json (141 messages: 47 companies × 3 touches)
outreach/linkedin-urls.json (47 LinkedIn profiles)
outreach/email-blast.json (47 emails ready to send)
outreach/tracking-sheet.csv (Google Sheets ready)
```

### 4. Automation Scripts
```
linkedin-automator.py - LinkedIn automation
linkedin-outreach.sh - Shell wrapper
create-automation-messages.py - Generate messages
find-decision-makers.py - Find DMs
auto-outreach.py - Full automation
```

---

## 3-Touch Campaign

| Day | Action | Status |
|-----|--------|--------|
| 0 | Initial outreach | Ready |
| 3 | Follow-up | Ready |
| 7 | Final message | Ready |

---

## Sending Messages

### Option 1: LinkedIn (Browser Automation)

```bash
# Review URLs
cat outreach/linkedin-urls.json

# Use browser automation to:
# 1. Open each LinkedIn profile
# 2. Click "Message"
# 3. Send pre-written message
```

### Option 2: Email (Gmail)

```bash
# Create Gmail-ready format
python3 linkedin-automator.py

# Import outreach/gmail-blast.json to Gmail API
```

### Option 3: Manual

```bash
# Review all messages
cat outreach/automation-queue.json

# Send manually via LinkedIn/Email
```

---

## Sample Message (Day 0)

**To:** Sara Al Naqbi, CTO at National Wellness Partners  
**Subject:** Executive PMO Leadership - National Wellness Partners

```
Hi Sara,

I noticed National Wellness Partners is leading digital transformation 
in UAE's healthcare sector.

I'm a Senior Technology Executive with 20+ years experience:
• SGH (Egypt): Led $50M transformation, reduced reporting by 97%
• Talabat (GCC): Scaled operations 233x in 18 months
• Network (8 countries): PMO for 300+ projects

I'm exploring senior leadership opportunities in HealthTech, 
particularly PMO, Digital Transformation, or CDO roles.

Would you have 15 minutes for a brief call this week?

Best regards,
Ahmed Nasr
Senior Technology Executive | PMO & AI Transformation
```

---

## Tracking

### Google Sheets Import

```bash
# Import this file to Google Sheets
cat outreach/tracking-sheet.csv
```

Columns:
- Priority, Company, Decision Maker, Title
- LinkedIn URL, Email
- Day 0 (Sent), Day 3 (Follow-up), Day 7 (Final)
- Response, Call Scheduled, Notes

---

## Automation Commands

```bash
# Create all automation files
python3 create-automation-messages.py

# Run LinkedIn automation
python3 linkedin-automator.py 10  # Send 10 messages

# Check queue status
python3 linkedin-automator.py

# Generate email blast
python3 linkedin-automator.py --gmail

# Auto-find decision makers
python3 find-decision-makers.py
```

---

## Cron Schedule

```bash
# Daily follow-up check (9 AM Cairo)
0 9 * * * cd /root/.openclaw/workspace/healthtech-directory && \
  python3 linkedin-automator.py --check >> outreach/cron.log 2>&1
```

---

## File Structure

```
healthtech-directory/
├── data/
│   ├── job-search-targets.json
│   ├── anco-prospects.json
│   └── gcc-healthtech-enriched.json
├── outreach/
│   ├── automation-queue.json      (141 messages)
│   ├── linkedin-urls.json         (47 profiles)
│   ├── email-blast.json          (47 emails)
│   ├── gmail-blast.json           (Gmail API ready)
│   ├── tracking-sheet.csv         (Google Sheets)
│   ├── decision-makers.csv
│   └── decision-makers.json
├── research/
│   ├── master-tracker.csv
│   └── research-*.md (47 files)
├── linkedin-automator.py
├── linkedin-outreach.sh
├── create-automation-messages.py
└── find-decision-makers.py
```

---

## Stats

| Metric | Value |
|--------|-------|
| Companies | 47 |
| Decision Makers | 47 |
| Total Messages | 141 |
| Touches per Company | 3 |
| Countries | UAE, KSA, Egypt, Kuwait, Qatar, Oman, Bahrain |

---

## Next Steps

1. ☐ Review outreach/tracking-sheet.csv
2. ☐ Add any real decision maker names
3. ☐ Send Day 0 messages (via LinkedIn/Email)
4. ☐ Track responses in Google Sheets
5. ☐ Schedule discovery calls
6. ☐ Follow up (Day 3, Day 7)

---

*Automated Outreach System - Ready to Execute*
