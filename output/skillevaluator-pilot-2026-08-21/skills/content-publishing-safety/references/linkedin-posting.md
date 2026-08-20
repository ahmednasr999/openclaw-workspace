# LinkedIn Posting Rules

## Approval

Publishing is pre-approved only when Ahmed directly asks to post a specific item or the specific post is already approved for publishing. Ask again if content/media changed materially, target account is unclear, or duplicate checks show risk.

## Known implementation notes

- Composio action: `LINKEDIN_CREATE_LINKED_IN_POST`.
- Person URN: `urn:li:person:mm8EyA56mj`.
- For image posts, upload image first and use the returned true `s3key`.
- Never pass raw GitHub URLs, local paths, Notion URLs, or short links as `s3key`.
- Never post text-only when an image was expected.

## Before external publish

- Confirm caption is approved or clearly requested for publishing.
- Confirm media exists and matches caption.
- Confirm platform, ratio, date, and account.
- Confirm no private/confidential data.
- Check local/live state for duplicates before retry.
