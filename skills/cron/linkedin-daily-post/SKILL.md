# LinkedIn Daily Post - SKILL.md

## Purpose
Post today's scheduled LinkedIn content. Script handles extraction, scoring, bold conversion, image download.

## NON-NEGOTIABLE RULES
1. Run the script FIRST. It does the prep.
2. Post the EXACT content from /tmp/linkedin-post-payload.json. Do NOT modify, truncate, or reformat it.
3. NEVER post without an image if image_required=true in the payload.
4. Weekend (Fri/Sat in Egypt) = skip.

## Step 1: Run the script
```bash
cd /root/.openclaw/workspace && python3 scripts/linkedin-auto-poster.py 2>&1
```

If output says "No scheduled post" - report "No LinkedIn post scheduled for today." STOP.
If output says "QUALITY_HOLD" - report the score and title. STOP.
If output says "READY_TO_POST" - continue to Step 2.

## Step 2: Read payload
```bash
cat /tmp/linkedin-post-payload.json
```

## Step 3: Upload image (ONLY if image_required=true AND image_path is not null)

Call COMPOSIO_SEARCH_TOOLS: query "upload image to LinkedIn"

Then COMPOSIO_MULTI_EXECUTE_TOOL with LINKEDIN_INITIALIZE_IMAGE_UPLOAD:
- owner: "urn:li:person:mm8EyA56mj"

Then PUT the image file:
```bash
curl -s -o /dev/null -w "%{http_code}" -X PUT -H "Content-Type: image/png" --data-binary @/tmp/linkedin-post-image.png "<upload_url>"
```

Expected: 201. If not, retry 3x with 5s delay.
If image upload fails after 3 retries: DO NOT post. Report failure. STOP.

Save the image URN from the INITIALIZE response.

## Step 4: Create the post

COMPOSIO_MULTI_EXECUTE_TOOL with LINKEDIN_CREATE_LINKED_IN_POST:
```json
{
  "author": "urn:li:person:mm8EyA56mj",
  "commentary": "<EXACT content from payload - copy the full string>",
  "visibility": "PUBLIC",
  "content": {
    "media": {
      "title": "<title from payload>",
      "id": "<image URN from Step 3>"
    }
  }
}
```

If no image: omit the "content" field entirely.

CRITICAL: The "commentary" must be the EXACT content string from the payload. It already has Unicode bold characters. Do not strip, truncate, or re-encode it.

## Step 5: Update Notion + Briefing
```bash
cd /root/.openclaw/workspace && python3 scripts/linkedin-auto-poster.py --update-url '<POST_URL>' --page-id <page_id>
```

Replace <POST_URL> with the LinkedIn post URL from Step 4 (format: https://www.linkedin.com/feed/update/urn:li:activity:XXXXX).

## Step 6: Report
Send: "LinkedIn Daily Post - [date]: POSTED\nTitle: ...\nURL: ...\nImage: yes/no\nScore: X/10"

## Error Handling
- If image upload fails: DO NOT post. Report "IMAGE_UPLOAD_FAILED" and stop.
- If post creation fails: try up to 3 times. Report what failed.
- NEVER post text-only when image exists. That is FAILURE.
- March 19 lesson: text-only post lost all engagement. Image is mandatory.
