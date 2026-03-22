# LinkedIn Daily Post - SKILL.md

## Purpose
Post today's scheduled LinkedIn content from Notion Content Calendar via Composio API.

## NON-NEGOTIABLE RULES
1. ONLY post content from Notion Content Calendar - NEVER create or modify content
2. NEVER post if no scheduled content exists for today
3. If script says "No scheduled post" - STOP. Report "no post today" and exit
4. Weekend (Fri/Sat in Egypt) = skip
5. **NEVER post without an image if the content has an image.** If image upload fails, FIX IT. Do NOT post text-only as a fallback. (March 19, 2026 lesson - lost engagement from text-only post that had to be deleted)

## Execution

### Step 1: Extract today's post from Notion
```bash
cd /root/.openclaw/workspace && python3 scripts/linkedin-auto-poster.py 2>&1
```

**If output says "No scheduled post"** - Send: "📝 No LinkedIn post scheduled for today." STOP.

**If output says "READY_TO_POST"** - Read `/tmp/linkedin-post-payload.json` and continue.

### Step 2: Read the payload
```bash
cat /tmp/linkedin-post-payload.json
```

### Step 3: Upload image (if image_path is not null)

First, search for image upload tools:
Call COMPOSIO_SEARCH_TOOLS with query: "upload image to LinkedIn"

Then call COMPOSIO_MULTI_EXECUTE_TOOL with LINKEDIN_INITIALIZE_IMAGE_UPLOAD:
- owner: "urn:li:person:mm8EyA56mj"

After getting the upload_url, PUT the image:
```bash
curl -s -o /dev/null -w "%{http_code}" -X PUT -H "Content-Type: image/png" --data-binary @/tmp/linkedin-post-image.png "<upload_url_from_response>"
```

**Expected: HTTP 201.** If not 201:
- Retry the PUT up to 3 times with 5-second delays
- If still failing, try LINKEDIN_REGISTER_IMAGE_UPLOAD as alternative
- If STILL failing, try re-downloading the image and converting format (png->jpg or vice versa)
- **DO NOT proceed to Step 4 without a successful image upload if content has an image**

Save the image URN for Step 4.

### Step 4: Create the LinkedIn post

**Method A (preferred):** Use proxy_execute in COMPOSIO_REMOTE_WORKBENCH to call LinkedIn Posts API directly:
```python
body = {
    "author": "urn:li:person:mm8EyA56mj",
    "commentary": "<post content>",
    "visibility": "PUBLIC",
    "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
    "content": {"media": {"title": "<short title>", "id": "<image_urn>"}},
    "lifecycleState": "PUBLISHED",
    "isReshareDisabledByAuthor": False
}
result, error = proxy_execute("POST", "/rest/posts", "linkedin", body=body, headers={"LinkedIn-Version": "202601", "X-Restli-Protocol-Version": "2.0.0"})
```

**Method B (fallback):** Use COMPOSIO_MULTI_EXECUTE_TOOL with LINKEDIN_CREATE_LINKED_IN_POST.
Note: The `images` field in this tool expects Composio S3 keys, NOT LinkedIn image URNs. If you uploaded directly to LinkedIn, use Method A.

**If post creation fails:** Read the error, diagnose, try the other method. Do NOT give up.

### Step 5: Update Notion status

**CRITICAL: Post URL property is type `url` in Notion, NOT rich_text.**

```python
python3 -c "
import json, ssl, urllib.request
token = json.load(open('/root/.openclaw/workspace/config/notion.json'))['token']
page_id = 'PAGE_ID_FROM_PAYLOAD'
post_url = 'https://www.linkedin.com/feed/update/POST_URN_FROM_STEP_4'
data = json.dumps({'properties': {'Status': {'select': {'name': 'Posted'}}, 'Post URL': {'url': post_url}}}).encode()
req = urllib.request.Request(f'https://api.notion.com/v1/pages/{page_id}', data=data, method='PATCH', headers={'Authorization': f'Bearer {token}', 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json'})
try:
    urllib.request.urlopen(req, context=ssl.create_default_context())
    print('Notion updated: Posted')
except Exception as e:
    print(f'Notion update failed: {e}')
    # Diagnose: read error body, check field types, fix payload, retry
"
```

**If Notion update fails:** Read the error body. Common issues:
- Wrong property type (url vs rich_text vs select) - check with GET /pages/{id} first
- Invalid select option name - check existing options
- Fix the payload and retry. Do NOT skip this step.

### Step 5b: Update Today's Briefing Page

After posting, update the morning briefing Notion page to reflect the posted content inside the **📝 Content & Engagement** section.

```python
python3 << 'PYEOF'
import json, ssl, urllib.request, re
from datetime import datetime, timezone, timedelta

token = json.load(open('/root/.openclaw/workspace/config/notion.json'))['token']
ctx = ssl.create_default_context()
cairo = timezone(timedelta(hours=2))
today_str = datetime.now(cairo).strftime("%Y-%m-%d")

# Find today's briefing page
db_id = "3268d599-a162-812d-a59e-e5496dec80e7"
body = json.dumps({"filter": {"property": "Name", "title": {"contains": today_str}}}).encode()
req = urllib.request.Request(f"https://api.notion.com/v1/databases/{db_id}/query", data=body, method="POST",
    headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"})
with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
    pages = json.loads(r.read()).get("results", [])

if not pages:
    print("No briefing page found for today - skipping update")
    exit(0)

briefing_page_id = pages[0]["id"]

# Find the Content & Engagement section divider to insert after
req2 = urllib.request.Request(f"https://api.notion.com/v1/blocks/{briefing_page_id}/children?page_size=100",
    method="GET", headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"})
with urllib.request.urlopen(req2, context=ctx, timeout=15) as r:
    blocks = json.loads(r.read()).get("results", [])

# Find last bullet in Content section (before the divider after it)
content_section_start = None
content_last_block = None
for i, b in enumerate(blocks):
    rt = b.get(b["type"], {}).get("rich_text", [])
    text = "".join(t.get("text", {}).get("content", "") for t in rt)
    if "Content & Engagement" in text and b["type"] == "heading_2":
        content_section_start = i
    if content_section_start and i > content_section_start:
        if b["type"] == "divider":
            break  # Hit next section
        content_last_block = b["id"]

if not content_last_block:
    print("Could not find Content section - skipping")
    exit(0)

# POST_URL and IMAGE_URL are set by the caller
post_url = "POST_URL_PLACEHOLDER"  # Replace with actual
image_url = "IMAGE_URL_PLACEHOLDER"  # Replace with actual

new_blocks = [
    {"type": "callout", "callout": {
        "rich_text": [{"type": "text", "text": {"content": "✅ POSTED with image and bold text"}, "annotations": {"bold": True}}],
        "icon": {"type": "emoji", "emoji": "✅"}, "color": "green_background"
    }},
    {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [
        {"type": "text", "text": {"content": "🔗 LinkedIn: "}},
        {"type": "text", "text": {"content": post_url, "link": {"url": post_url}}}
    ]}},
]
if image_url:
    new_blocks.append({"type": "image", "image": {"type": "external", "external": {"url": image_url}}})

data = json.dumps({"children": new_blocks, "after": content_last_block}).encode()
req3 = urllib.request.Request(f"https://api.notion.com/v1/blocks/{briefing_page_id}/children", data=data, method="PATCH",
    headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"})
urllib.request.urlopen(req3, context=ctx, timeout=15)
print(f"✅ Briefing page updated with post details")
PYEOF
```

Replace `POST_URL_PLACEHOLDER` with the actual LinkedIn post URL from Step 4, and `IMAGE_URL_PLACEHOLDER` with the GitHub image URL from the payload.

### Step 6: Report
Send to Content topic: "📝 LinkedIn Daily Post Report - {date}\n\n✅ Post Published Successfully\n\nTitle: {title}\nPost URL: {post_url}\nImage: {'✅ Included' if image else '❌ No image in content'}\nNotion: ✅ Updated to Posted\nBriefing: ✅ Updated"

## Error Handling - The "Never Give Up" Rule

**There is no acceptable partial completion.** The goal is: post WITH image (if content has one) AND update Notion.

If something fails:
1. **Read the error** - understand WHY
2. **Try a different approach** - at least 3 attempts with different methods
3. **Only report failure after exhausting all options** - include what was tried and why each failed
4. **NEVER deliver partial results as success** - "Posted without image" is FAILURE, not success

**Specific retry strategies:**
- Image download fails → Try with different User-Agent, try wget, try curl
- Image upload to LinkedIn fails → Try INITIALIZE_IMAGE_UPLOAD, try REGISTER_IMAGE_UPLOAD, try different content type
- Post creation fails → Try proxy_execute with different API versions, try COMPOSIO tool
- Notion update fails → Check property types with GET, fix payload format, retry

**Real cost of giving up (March 19, 2026):** Posted without image → 4 likes lost → deleted and re-posted → cold algorithm restart. Engagement damage is permanent.


---
## 🔧 Auto-Improvement (2026-03-21)
> Added by weekly-agent-review.py based on recurring failure pattern.

**Pattern detected (2 occurrences):**
Add completion guard: verify ALL required outputs (image, Notion update, etc.) before marking task done.

**Action required:**
- Review this section and integrate the fix into the relevant step above.
- Remove this block once the fix has been applied.


## Quality Gates
- Image uploaded successfully (HTTP 201) before post creation is attempted
- Post creation returns a valid LinkedIn URN (not just HTTP 200)
- Notion status updated to "Posted" with correct post URL
- Today's briefing Notion page updated with post details
- Never mark complete if image was in content but not posted

## Output Rules
- No em dashes - use hyphens only
- Report sent to Content topic (topic 7)
- Format: "LinkedIn Daily Post Report - [date]: [POSTED|NO_POST|FAILED]"
- If posted: include post URL and image status
- If failed: include what was attempted and why each attempt failed
