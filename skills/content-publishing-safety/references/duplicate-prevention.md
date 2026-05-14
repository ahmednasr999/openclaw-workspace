# Duplicate Prevention

Before retrying any external publish or public action, re-check local success logs and live state immediately before the final publish call.

## Why

External publish retries can create duplicate LinkedIn posts or repeated public actions.

## Minimum checks

1. Check local workflow logs/status for prior success.
2. Check the source item status if using Notion/content calendar.
3. Check live platform state when available.
4. If state is ambiguous, pause and report the ambiguity instead of retrying blindly.

## Report duplicates risk clearly

If a post may already be live, say:

- what evidence suggests it may be live
- what evidence is missing
- recommended next action
