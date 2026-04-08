# LinkedIn Image Post Flow (Tested 2026-03-25)

## The Problem
Posts were going out text-only when images were expected. The auto-poster had "tiered degradation" that allowed text-only posts if score was ≥80%.

## Root Cause
1. **Degradation logic**: Auto-poster posted without image if image upload failed but quality score was high
2. **Two competing paths**: Composio API and Voyager direct-post, neither handling images reliably

## Fix Applied
- Auto-poster now **ALWAYS holds** if image upload fails (no text-only degradation)
- Changed in `linkedin-auto-poster.py` line ~778

## Tested Working Flow (Composio API)

### Step 1: Register Image Upload
```
LINKEDIN_REGISTER_IMAGE_UPLOAD
  owner_urn: "urn:li:person:mm8EyA56mj"
```
Returns: `asset_urn` (e.g., `urn:li:digitalmediaAsset:D4D22AQG30lbQdFxFxg`) + `upload_url`

### Step 2: Upload Image Bytes
HTTP PUT to `upload_url` with:
- Body: raw image bytes
- Headers: `Content-Type: image/png`, `media-type-family: STILLIMAGE`
- Expected: 201 Created

### Step 3: Create Post with Image (via s3key method)
```
LINKEDIN_CREATE_LINKED_IN_POST
  author: "urn:li:person:mm8EyA56mj"
  commentary: "Post text..."
  visibility: "PUBLIC"
  images: [{
    "name": "post-image.png",
    "mimetype": "image/png", 
    "s3key": "<from upload_local_file()>"
  }]
```

### Alternative: Direct Asset URN (for Voyager path)
The registered `asset_urn` can be used directly in the Voyager `normalizedPosts` API.

## Agent Posting Checklist
1. ✅ Check if post has an image in Notion
2. ✅ Download image (GitHub raw URL or local)
3. ✅ Upload to Composio S3 via `upload_local_file()`
4. ✅ Get `s3key` from upload result
5. ✅ Call `LINKEDIN_CREATE_LINKED_IN_POST` with `images[]` containing s3key
6. ✅ Verify post URL includes image
7. ❌ NEVER post text-only if image was expected

## Test Results (2026-03-25)
- Register upload: ✅ 200 OK, got asset URN
- Upload bytes: ✅ 201 Created  
- S3 upload: ✅ Got s3key `project/pr_DBp_8iitCrNe/tool_router_session/trs_IpUA5TD-hiEt/JZAPq4rAmb1G`
- Draft post with s3key image: ✅ Created `urn:li:share:7442515872130416640` (then deleted)
- Full Composio flow: ✅ VERIFIED WORKING
- End-to-end live post: ⏳ Pending Ahmed approval to test with real scheduled post
