# LinkedIn Daily Post - SKILL.md

## Purpose
Post today's scheduled LinkedIn content from Notion Content Calendar via Composio API.

## NON-NEGOTIABLE RULES
1. ONLY post content from Notion Content Calendar - NEVER create or modify content
2. NEVER post if no scheduled content exists for today
3. If script says "No scheduled post" - STOP. Report "no post today" and exit
4. Weekend (Fri/Sat in Egypt) = skip

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
curl -s -X PUT -H "Content-Type: image/png" --data-binary @/tmp/linkedin-post-image.png "<upload_url_from_response>"
```

Save the image URN for Step 4.

### Step 4: Create the LinkedIn post

Call COMPOSIO_MULTI_EXECUTE_TOOL with LINKEDIN_CREATE_LINKED_IN_POST:
- author: "urn:li:person:mm8EyA56mj"
- commentary: content from payload JSON
- visibility: "PUBLIC"
- If image was uploaded: include images array

### Step 5: Update Notion status
```bash
python3 -c "
import json, ssl, urllib.request
token = json.load(open('/root/.openclaw/workspace/config/notion.json'))['token']
page_id = 'PAGE_ID_FROM_PAYLOAD'
post_urn = 'POST_URN_FROM_STEP_4'
post_url = f'https://www.linkedin.com/feed/update/{post_urn}'
data = json.dumps({'properties': {'Status': {'select': {'name': 'Posted'}}, 'Post URL': {'rich_text': [{'text': {'content': post_url}}]}}}).encode()
req = urllib.request.Request(f'https://api.notion.com/v1/pages/{page_id}', data=data, method='PATCH', headers={'Authorization': f'Bearer {token}', 'Notion-Version': '2022-06-28', 'Content-Type': 'application/json'})
urllib.request.urlopen(req, context=ssl.create_default_context())
print('Notion updated: Posted')
"
```

### Step 6: Report
Send: "✅ LinkedIn post published: {title}\n{post_url}"

## Error Handling
- If Composio fails: Send "⚠️ LinkedIn post failed: {error}. Manual post needed."
- If image upload fails: Post WITHOUT image, note in message
- If Notion update fails: Still report success (post is live on LinkedIn)
