# PUBLISH Layer — Daily Auto-Post

## Pre-Publish Sequence (9:00 AM Cairo)

1. Run `linkedin-preflight.py` — validates today's scheduled post:
   - Status = Scheduled
   - Planned Date = today
   - Content length > 200 characters
   - Image accessible (if assigned)
2. If preflight fails → alert Ahmed via Telegram, do not post

## Publish (9:30 AM Cairo)

1. Fetch today's post from Notion (Status=Scheduled, Date=today)
2. Convert any `**bold**` to Unicode Mathematical Bold characters
3. Post via Composio `LINKEDIN_CREATE_LINKED_IN_POST`:
   - author: `urn:li:person:mm8EyA56mj`
   - commentary: post text
   - visibility: PUBLIC
   - images: if image exists, upload via `LINKEDIN_INITIALIZE_IMAGE_UPLOAD` first
4. Update Notion status to "Posted"
5. Save post URL to Notion

## Post-Publish Alerts

**Immediately after posting:**
- Telegram: "🟢 Post live: [first 50 chars]. 60-min engagement window open."

**At 10:30 AM Cairo (60 min later):**
- Telegram: "🟡 Engagement window closing."

## Failure Protocol

If posting fails:
1. Read error message
2. Try alternate method (up to 3 attempts)
3. If still failing after 3 attempts, alert Ahmed:
   - "🔴 Post failed: [error]. Attempted 3 fixes. Manual intervention needed."
4. Do NOT mark as Posted in Notion
5. Do NOT skip and move to next day — today's post must be resolved

## Bold Text Conversion

LinkedIn doesn't render markdown. Convert `**text**` to Unicode:
- A-Z: U+1D5D4 to U+1D5ED
- a-z: U+1D5EE to U+1D607
- 0-9: U+1D7EC to U+1D7F5

Script helper: `scripts/linkedin-auto-poster.py` has `convert_bold_markdown()`.
