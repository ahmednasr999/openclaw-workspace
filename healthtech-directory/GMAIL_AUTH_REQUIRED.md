# Gmail Authentication Required

## Issue

The gog CLI needs to authenticate with Gmail, but this requires:
1. Opening a browser
2. Clicking "Allow"
3. Copying a verification code

This can't be done automatically in the current environment.

---

## Solution

### Option 1: Authenticate Once (Recommended)

Run this command once manually:

```bash
cd ~/.openclaw/workspace/healthtech-directory
gog auth add you@gmail.com --services gmail
```

This will:
1. Open a browser
2. Ask you to log in to Gmail
3. Grant permission
4. Save credentials

After that, I can create drafts automatically!

---

### Option 2: Use Ready Templates

I've already prepared everything:

```
outreach/
├── QUICK_SEND_LIST.md      ← Copy/paste here
├── gmail-templates/        ← 47 individual templates
└── gmail-import.csv       ← Import to Gmail
```

**Quick workflow:**
1. Open: `outreach/QUICK_SEND_LIST.md`
2. Copy/paste emails to Gmail
3. Review and send

---

## After Authentication

Once you run `gog auth add`, reply "Authenticated" and I'll create all 47 drafts automatically!

---

## What I've Prepared

| File | Purpose |
|------|---------|
| `setup-gmail-drafts.sh` | Creates 47 drafts |
| `QUICK_SEND_LIST.md` | Copy/paste ready |
| `gmail-templates/` | 47 individual emails |
| `decision-makers.csv` | All contacts |

---

## Ready When You Are!

1. **Authenticate:** `gog auth add you@gmail.com --services gmail`
2. **Confirm:** Reply "Authenticated"
3. **I'll:** Create 47 drafts in Gmail
4. **You:** Review → Edit → Confirm "Send"
