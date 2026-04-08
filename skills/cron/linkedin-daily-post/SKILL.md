# LinkedIn Daily Post - SKILL.md

## Purpose
Post today's scheduled LinkedIn content. Script is end-to-end autonomous.

## NON-NEGOTIABLE RULES (READ THESE FIRST)
1. Run the script. It handles everything: extract from Notion, score, rewrite, image download, payload prep.
2. ONLY proceed to Step 3 if the script outputs exactly `READY_TO_POST`. Any other output = STOP.
3. Weekend (Fri/Sat in Egypt) = skip.
4. **NEVER work around failures.** If the script says HOLD, you HOLD. Do not download images yourself, do not rewrite content, do not retry with different URLs. The script's decision is FINAL.
5. **NEVER construct post text yourself.** Use ONLY the exact `content` field from `/tmp/linkedin-post-payload.json`. Do not use Python string escapes, do not reconstruct Unicode bold characters, do not copy text from Notion.
6. **NEVER post without an image if the payload says `image_required: true`.** If image upload to Composio S3 fails, report IMAGE_HOLD and STOP.

## Step 1: Run the script
```bash
cd /root/.openclaw/workspace && python3 scripts/linkedin-auto-poster.py 2>&1
```

## Step 2: Read the LAST LINE of output and act accordingly

Check ONLY the last meaningful line of script output:

| Last line contains | Action |
|---|---|
| `No scheduled post` | Report "No LinkedIn post scheduled for today." **STOP. Do nothing else.** |
| `QUALITY_HOLD` | Report score and failed criteria. **STOP. Do nothing else.** |
| `IMAGE_HOLD` | Report image failure. **STOP. Do nothing else. Do NOT attempt to download the image yourself.** |
| `POSTED_AUTONOMOUS` | Report success with title, URL, score. **DONE.** |
| `READY_TO_POST` | Proceed to Step 3. This is the ONLY output that allows posting. |
| `DELETED_TRUNCATED_POST` | Report truncation. **STOP. Do nothing else.** |

**CRITICAL: If the output is anything other than `READY_TO_POST`, you MUST stop immediately. Do not read the payload. Do not attempt workarounds. Do not try alternative image sources. Do not call any Composio tools. Just report the status and STOP.**

## Step 3: Post via Composio (ONLY if Step 2 output was READY_TO_POST)

Read the payload:
```bash
cat /tmp/linkedin-post-payload.json
```

**Verify the payload before posting:**
- The `action` field MUST be `post_to_linkedin`. If it says `image_failed_hold`, `quality_hold`, or anything else, STOP immediately.
- The `content` field contains the EXACT text to post (already has Unicode bold). Use it verbatim.

**If payload has `image_path` AND `image_required` is true:**

1. Upload the image at `image_path` to Composio S3 via `COMPOSIO_REMOTE_WORKBENCH`:
   - Use `upload_local_file(image_path)` in the workbench
   - Extract the `s3key` from the result
   - If upload fails: report "IMAGE_HOLD: S3 upload failed" and **STOP. Do NOT post text-only.**

2. Post with image:
   - tool: `LINKEDIN_CREATE_LINKED_IN_POST`
   - author: `urn:li:person:mm8EyA56mj`
   - commentary: EXACT `content` field from payload (copy the string, do not reconstruct it)
   - images: `[{"name": "image.png", "s3key": "<s3key from step 1>", "mimetype": "image/png"}]`
   - visibility: `PUBLIC`

**If `image_required` is false or no `image_path`:**

- Post text-only using the EXACT `content` field from payload
- tool: `LINKEDIN_CREATE_LINKED_IN_POST`
- author: `urn:li:person:mm8EyA56mj`
- commentary: EXACT `content` field from payload
- visibility: `PUBLIC`

**After successful post:**
Extract the post URL from Composio's response, then close the loop:
```bash
python3 scripts/linkedin-auto-poster.py --update-url '<POST_URL>' --page-id <page_id>
```

## Step 4: Report
Send via Telegram to the **Content thread (topic 7)**:
- Use `message` tool with `channel=telegram`, `target=-1003882622947`, `threadId=7`
- Include: Title, URL (or hold reason), Score X/13, Image yes/no

**Critical:** Always specify `threadId=7`. Never send to other threads.

## FORBIDDEN ACTIONS (will cause bad posts)
- ❌ Downloading images from Notion, GitHub, or any URL yourself
- ❌ Using `proxy_execute` to call LinkedIn API directly
- ❌ Constructing post text with Python Unicode escapes (`\U0001d5b9` etc.)
- ❌ Posting a text-only version "temporarily" then trying to delete and repost
- ❌ Uploading images to file sharing services (0x0.st, catbox, etc.)
- ❌ Bypassing any HOLD status from the script
- ❌ Calling `LINKEDIN_CREATE_LINKED_IN_POST` more than once per run
- ❌ Reading the payload file when the script did NOT output READY_TO_POST

## Error Handling
- Script handles retries, rewrites, and verification internally
- If script crashes: report the error output verbatim, STOP
- NEVER modify post content - the script handles bold conversion and formatting
- If in doubt: STOP and report. A missed post is better than a bad post.
