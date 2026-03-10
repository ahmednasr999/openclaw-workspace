# LinkedIn Comment Poster

## Trigger Phrases
- "post this comment on LinkedIn"
- "publish comment on [URL]"
- "submit comment [text]"
- "post comment to [URL]"
- "publish to LinkedIn"
- "submit LinkedIn comment"

## Description
Completes the LinkedIn engagement loop by posting drafted comments to specific posts via browser automation. Works with comments already drafted by linkedin-comment-radar or LinkedIn Writer.

## When NOT to Use
- For creating original posts (use LinkedIn Writer)
- For discovering posts to engage (use linkedin-comment-radar)
- For messaging connections (use linkedin skill)
- Without an already-drafted comment (draft first, then post)

## Workflow

### Step 1: Validate Input
- Must have: LinkedIn post URL
- Must have: Comment text (already drafted)
- Validate URL is a valid LinkedIn post (contains linkedin.com/posts/)

### Step 2: Open LinkedIn Post
- Use Camoufox (not Chrome) - bypasses bot detection
- Navigate to the post URL directly
- Wait for page load (reaction/comment buttons visible)

### Step 3: Locate Comment Box
- Find the comment input field (usually below the post)
- Scroll post into view if needed
- Click to focus

### Step 4: Type and Submit
- Type the drafted comment exactly as provided
- Press Enter or click Submit/Post button
- Verify comment appears in comment stream

### Step 5: Confirmation
- Capture screenshot of posted comment
- Log: post URL, comment preview, timestamp
- Return confirmation to user

## Error Handling
- If LinkedIn prompts login: abort and ask user to import cookies
- If comment fails to post: retry once, then report failure
- If URL invalid: ask for valid LinkedIn post URL

## Requirements
- Camoufox browser available
- LinkedIn session authenticated (cookies imported if needed)
- Comment text must be < 3000 characters

---

Built: 2026-03-10
