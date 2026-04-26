# LinkedIn Daily Post - SKILL.md

## Purpose
Publish today's approved or scheduled LinkedIn content using the hardened Notion control flow.

## NON-NEGOTIABLE RULES (READ THESE FIRST)
1. Run the script first. It is the control gate for preflight, payload prep, and `Publishing` state transition.
2. ONLY proceed to the LinkedIn post step if the script outputs exactly `READY_TO_POST` on the last meaningful line.
3. If the script outputs `No scheduled post` or `ALREADY_POSTED`, stop quietly.
4. If the script outputs `PRECHECK_FAILED`, report the reason and stop.
5. **NEVER construct post text yourself.** Use ONLY the exact `content` field from `/tmp/linkedin-post-payload.json`.
6. **NEVER post text-only if `image_required` is true and image staging fails.** Mark failure and stop.
7. After a successful post, ALWAYS run the writeback step so Notion gets `Posted`, `Post URL`, and `Published At`.

## Step 1: Run the script
```bash
cd /root/.openclaw/workspace && python3 scripts/linkedin-auto-poster.py 2>&1
```

## Step 2: Read the LAST LINE of output and act accordingly

| Last line contains | Action |
|---|---|
| `No scheduled post` | Stop quietly. No user message needed. |
| `ALREADY_POSTED` | Stop quietly. No user message needed. |
| `PRECHECK_FAILED` | Report the failure to Ahmed DM and STOP. |
| `READY_TO_POST` | Proceed to Step 3. |

**CRITICAL:** If the output is anything other than `READY_TO_POST`, you MUST stop immediately.

## Step 3: Read payload and post via LinkedIn tool flow

Read the payload:
```bash
cat /tmp/linkedin-post-payload.json
```

Payload rules:
- `action` must be `post_to_linkedin`
- `content` is the exact commentary to publish
- `author` is the LinkedIn author URN
- `page_id` is the Notion page to write back
- `image_required` tells you whether text-only is allowed
- `image_staging_required` / `image_s3key_required` mean the image must be staged before posting
- `image_url` and `image_local_path` are source locations only; they are NEVER valid `s3key` values

### 3A. Discover and validate tool path
First call `COMPOSIO_SEARCH_TOOLS` for LinkedIn create-post flow. Use the returned active LinkedIn connection and the schema for `LINKEDIN_CREATE_LINKED_IN_POST`.

### 3B. Stage image if required
If `image_required` is `true`, staging is mandatory before any LinkedIn create-post call.

Hard gate:
- If `image_s3key_required` is `true`, do not call `LINKEDIN_CREATE_LINKED_IN_POST` until `upload_local_file()` has returned a non-empty `s3key`.
- Never pass `image_url`, `image_local_path`, Notion file URLs, raw GitHub URLs, or any public URL as `s3key`.
- The only valid `images[].s3key` is the value returned by `upload_local_file()` in `COMPOSIO_REMOTE_WORKBENCH`.

- If payload has `image_url` (HTTPS URL):
  - use `COMPOSIO_REMOTE_WORKBENCH` to download that URL inside the remote sandbox
  - verify the downloaded file is not tiny/broken (must be > 1000 bytes unless intentionally tiny)
  - use `upload_local_file()` to upload it and capture the returned `s3key`

- If payload has `image_local_path` (local VPS path — preferred for files the agent can access):
  - Agent reads the local file, transfers content into workbench `/tmp/`, uploads via `upload_local_file()` to get `s3key`
  - Transfer method depends on file size:
    - **Small files (< 200KB)**: base64-encode in workbench — pass `base64.b64encode(open(local_path,'rb').read()).decode()` in the workbench code, decode and write to `/tmp/<image_name>`, then upload
    - **Large files (≥ 200KB)**: chunked transfer — split base64 into ~100KB chunks, pass sequentially to workbench, concatenate in `/tmp/`, then upload
  - See canonical staging pattern below

- If payload has `image_base64` (legacy/fallback — use only when neither URL nor local path is available):
  - decode base64, write to `/tmp/<image_name>` in the sandbox
  - `upload_local_file('/tmp/<image_name>')` → capture returned `s3key`

**Composio workbench staging pattern — small files < 200KB (base64 transfer)**:
```python
# Agent side: read file and pass base64 to workbench
import base64
local_path = '<image_local_path from payload>'
image_name = '<image_name from payload>'
b64_data = base64.b64encode(open(local_path,'rb').read()).decode('ascii')
print('BASE64_READY')  # signal to hand off to workbench

# Workbench side: decode and write to /tmp/, then upload
import base64
b64_data = '<base64 string from agent>'
image_name = '<image_name from payload>'
sandbox_path = f'/tmp/{image_name}'
with open(sandbox_path,'wb') as f:
    f.write(base64.b64decode(b64_data))
from composio_media import upload_local_file
result = upload_local_file(sandbox_path)
s3key = result[0]['s3key']   # tuple: (data_dict, "")
```

**Large files ≥ 200KB (chunked transfer)**:
Agent splits base64 into ~100KB chunks, passes each to workbench to append, then the workbench decodes the complete base64 and writes/uploads.

**Key constraint**: Workbench sandbox cannot reach VPS paths like `/root/` or `/mnt/` directly. Always transfer via base64 encoding into the workbench.

**Important**: `upload_local_file()` takes a **string path**, not a list. Returns a tuple `(data_dict, stderr_str)`.

If staging fails:
```bash
python3 /root/.openclaw/workspace-cmo/scripts/report-publish-failure.py --page-id <page_id> --step asset --error "<reason>"
```
Then send Ahmed a brief DM and STOP.

### 3C. Create the LinkedIn post
Before creating the post:
- If `image_required` is `true`, assert `s3key` exists and came from `upload_local_file()` in this run.
- If that assertion fails, report asset failure and STOP. Do not post text-only.

Use `LINKEDIN_CREATE_LINKED_IN_POST` with:
- `author`: exact payload `author`
- `commentary`: exact payload `content`
- `visibility`: `PUBLIC`
- `images`: include exactly one image entry using `name`, `mimetype`, and the staged `s3key` if image staging succeeded

### 3D. Build the URL and write back
From the create-post response, prefer identifiers in this order:
- `data.x_restli_id`
- `data.id`
- `data.post_urn`

Construct the URL as:
```text
https://www.linkedin.com/feed/update/<identifier>/
```

Then run:
```bash
python3 /root/.openclaw/workspace/scripts/linkedin-auto-poster.py --update-url '<POST_URL>' --page-id <page_id>
```

If the post succeeded but writeback failed:
- report that exact state to Ahmed
- include the LinkedIn URL
- do NOT retry the post itself

## Step 4: Notify Ahmed
Send a concise Telegram DM to Ahmed (`866838380`) with:
- title
- post URL
- image yes/no

On failure, send:
- step that failed
- title
- short reason

## FORBIDDEN ACTIONS
- ❌ Rewriting or trimming the payload content
- ❌ Posting text-only when `image_required` is true and image staging failed
- ❌ Ignoring `PRECHECK_FAILED`
- ❌ Posting twice because writeback failed
- ❌ Reading old approval JSON as live truth

## Error Handling
- Preflight or payload prep failure -> report and stop
- Image staging failure -> mark failure and stop
- LinkedIn tool failure -> mark failure and stop
- Writeback failure after successful post -> report exact URL + failure, do not repost
