# posting.md — LinkedIn Posting Runbook

## Source of Truth
- **Notion Content DB:** `3268d599-a162-814b-8854-c9b8bde62468`
- **Status values:** `Draft` | `Scheduled` | `Posted` | `Ideas` | `Outline`
- **Author URN:** `urn:li:person:mm8EyA56mj`
- **Composio connection:** ACTIVE (verified 2026-03-27)

---

## Auto-Posting (Cron)

**Schedule:** 9:30 AM Cairo (Africa/Cairo), Sun–Thu
**Script:** `scripts/linkedin-auto-poster.py`
**Flow:**
1. Query Notion DB for pages where `Status = Scheduled` AND `Planned Date = today`
2. Extract post text from `Draft` property
3. Convert bold markdown → Unicode Mathematical Bold via `convert_bold_markdown()`
4. Check for image block in page body (type `file` → signed S3 URL)
5. If image exists → download → upload to Composio S3 → get `s3key` → post with image
6. If no image → text-only post
7. On success → update Notion `Status` to `Posted` and write `Post URL` field

---

## Manual Post (On-Demand)

Use `COMPOSIO_SEARCH_TOOLS` + `COMPOSIO_MULTI_EXECUTE_TOOL`:

### Text-only post
```
tool_slug: LINKEDIN_CREATE_LINKED_IN_POST
arguments:
  author: "urn:li:person:mm8EyA56mj"
  commentary: "<post text with Unicode bold>"
  visibility: "PUBLIC"
```

### Post with image
Step 1: Get image from Notion page body (use `file` block type — gives signed S3 URL)
Step 2: Download to `/tmp/image.png`
Step 3: Upload via REMOTE_WORKBENCH:
```python
result, error = upload_local_file("/tmp/image.png")
s3key = result["s3key"]
```
Step 4: Post:
```
tool_slug: LINKEDIN_CREATE_LINKED_IN_POST
arguments:
  author: "urn:li:person:mm8EyA56mj"
  commentary: "<post text>"
  visibility: "PUBLIC"
  images:
    - name: "image.png"
      mimetype: "image/png"
      s3key: "<s3key from step 3>"
```

**NEVER post text-only if an image was expected — hold for review instead.**

---

## Bold Text Conversion

LinkedIn does not render markdown. Use `convert_bold_markdown()` from `scripts/linkedin-auto-poster.py`.

- **A–Z bold:** U+1D5D4–U+1D5ED
- **a–z bold:** U+1D5EE–U+1D607
- **0–9 bold:** U+1D7EC–U+1D7F5

Always convert `**text**` spans before posting.

---

## Image Source Priority (Topic-Aware)

| Topic | Priority Chain |
|-------|---------------|
| AI/Tech, Digital Transformation, HealthTech, FinTech, Data, Innovation | Gemini Flash → FLUX.1 → SD XL → Stock → PIL |
| PMO, Strategy, Leadership, Business, Healthcare | Stock → Gemini Flash → FLUX.1 → SD XL → PIL |
| Default | Gemini Flash → FLUX.1 → Stock → SD XL → PIL |

Use `scripts/image-gen-chain.py` for automated routing.

---

## Image Source Notes

- **NEVER use Google Drive links** — may be stale/outdated
- **Notion signed S3 URLs expire in 1–6 hours** — download immediately after extraction
- **Always pull images from Notion page blocks**, not the Notion `Cover` property

---

## Post URL Update (Mandatory)

After every successful post, write the LinkedIn post URL back to Notion:
- Property: `Post URL`
- Status: change to `Posted`

This is non-negotiable — it's how we track what's live and prevents double-posting.

---

## Failure Handling

- If Composio fails → log error → do NOT mark as Posted → reschedule to next business day
- If image upload fails → attempt text-only post → flag for image retry
- If post returns 429 → back off 60s → retry once → escalate to CEO DM if still failing
- Always notify CEO DM (866838380) on any posting failure with post title + error

---

## Limits

- Post commentary max: 3,000 characters
- Images per post: up to 20
- Do not post more than once per day per account
