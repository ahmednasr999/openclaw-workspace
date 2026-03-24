# LinkedIn Daily Post - SKILL.md

## Purpose
Post today's scheduled LinkedIn content. Script is end-to-end autonomous.

## NON-NEGOTIABLE RULES
1. Run the script. It does EVERYTHING: extract, score, rewrite if needed, post, verify, update Notion.
2. Your ONLY job is to run it, read the output, and report to Ahmed.
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
| `READY_TO_POST` | Direct-post failed. Fall back to Step 3 (agent-assisted). |
| `DELETED_TRUNCATED_POST` | Report "Post was truncated and auto-deleted. Manual review needed." STOP. |

## Step 3: Agent-assisted fallback (ONLY if direct-post failed)

Read the payload:
```bash
cat /tmp/linkedin-post-payload.json
```

Post using `linkedin-direct-post.py` manually:
```bash
cd /root/.openclaw/workspace && python3 scripts/linkedin-direct-post.py --text-file /tmp/linkedin-post-text.txt [--image /tmp/linkedin-post-image.png]
```

If direct-post cookies are expired, use Composio as last resort (posts under 950 chars ONLY):
- tool: `LINKEDIN_CREATE_LINKED_IN_POST`
- author: `urn:li:person:mm8EyA56mj`
- commentary: EXACT content from payload (already has Unicode bold)
- visibility: `PUBLIC`

After posting, close the loop:
```bash
python3 scripts/linkedin-auto-poster.py --update-url '<POST_URL>' --page-id <page_id>
```

## Step 4: Report
Send via Telegram:
- Title
- URL (or reason for hold)
- Score X/13
- Image: yes/no/degraded

## Error Handling
- Script handles retries, rewrites, and verification internally
- If script crashes entirely: report the error output verbatim
- NEVER modify post content - the script handles bold conversion and formatting
