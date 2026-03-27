# LinkedIn Daily Post - SKILL.md

## Purpose
Post today's scheduled LinkedIn content. Script is end-to-end autonomous.

## NON-NEGOTIABLE RULES
1. Run the script. It handles: extract from Notion, score, rewrite if needed, image download, payload prep.
2. After `READY_TO_POST`: use Composio to post. This is the primary posting method — no cookies needed, supports up to 3,000 chars and images.
3. Weekend (Fri/Sat in Egypt) = skip.

## Step 1: Run the script
```bash
cd /root/.openclaw/workspace && python3 scripts/linkedin-auto-poster.py 2>&1
```

## Step 2: Read the output and act accordingly

| Output | What to do |
|--------|------------|
| `No scheduled post` | Report "No LinkedIn post scheduled for today." STOP. |
| `QUALITY_HOLD` | Report score, failed questions, and that rewrite also failed. STOP. |
| `IMAGE_HOLD` | Report image failure + score too low for text-only. STOP. |
| `POSTED_AUTONOMOUS` | Report success: title, URL, score, image yes/no. DONE. |
| `READY_TO_POST` | Script prep done. Use Composio to post (Step 3 — primary method, no cookies needed). |
| `DELETED_TRUNCATED_POST` | Report "Post was truncated and auto-deleted. Manual review needed." STOP. |

## Step 3: Post via Composio (primary method — no cookies needed)

Composio is the posting engine. It supports up to 3,000 chars and images. No cookies required.

Read the payload:
```bash
cat /tmp/linkedin-post-payload.json
```

**If payload has `"image_path"` (image required):**

1. Read the image path from the payload (field: `image_path`).

2. Upload to Composio S3 via `COMPOSIO_REMOTE_WORKBENCH`:
   - Use `upload_local_file(image_path)` in the workbench
   - Extract the `s3key` from the result dict (field name: `s3key`)
   - The s3key looks like: `project/pr_.../tool_router_session/trs_.../{id}`
   - If upload_local_file fails, print the error and STOP with IMAGE_HOLD. Do NOT post without image.

3. Create post with the s3key:
   - tool: `LINKEDIN_CREATE_LINKED_IN_POST`
   - author: `urn:li:person:mm8EyA56mj`
   - commentary: EXACT content from payload (already has Unicode bold)
   - images: `[{"name": "image.png", "s3key": "<s3key from step 2>", "mimetype": "image/png"}]`
   - visibility: `PUBLIC`

**If no image (text-only):**

- tool: `LINKEDIN_CREATE_LINKED_IN_POST`
- author: `urn:li:person:mm8EyA56mj`
- commentary: EXACT content from payload
- visibility: `PUBLIC`

Extract the post URL from Composio's response (`https://www.linkedin.com/feed/update/...`).

After posting, close the loop:
```bash
python3 scripts/linkedin-auto-poster.py --update-url '<POST_URL>' --page-id <page_id>
```

## Step 4: Report
Send via Telegram to the **Content thread (topic 7)**:
- Use `message` tool with `channel=telegram` and `target=-1003882622947` and set `threadId=7`
- Title
- URL (or reason for hold)
- Score X/13
- Image: yes/no/degraded

**Critical:** Always specify `threadId=7` (Content thread). Never send to the Jobs thread (topic 6).

## Error Handling
- Script handles retries, rewrites, and verification internally
- If script crashes entirely: report the error output verbatim
- NEVER modify post content - the script handles bold conversion and formatting
