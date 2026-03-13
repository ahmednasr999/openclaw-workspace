# Browser Automation Helper

Before any browser interaction (click/type), always:

1. **Snapshot first** - Always take a snapshot to see current page state
2. **Check element** - Verify the element ref exists in snapshot
3. **Wait if needed** - If not found, sleep 2s and snapshot again (max 2 retries)
4. **Then interact** - Only then click/type
5. **Verify success** - Take another snapshot to confirm action worked

## Retry Pattern

For complex forms (like job applications):

```bash
# Try up to 3 times with backoff
for attempt in 1 2 3; do
  camofox_snapshot ...
  if element exists; then
    camofox_type ...
    break
  fi
  sleep $((attempt * 2))
done
```

## Screenshot on Failure

After any failed action, automatically capture screenshot:

```bash
# After failure
camofox_screenshot --tabId "$TAB_ID"
# Saves to default location, helps debug
```

## Common Fixes

- **Timeout on type**: Click the field first, then type
- **Element not found**: Scroll to it, wait, try again
- **Form not loaded**: Wait for "Loading..." to disappear
