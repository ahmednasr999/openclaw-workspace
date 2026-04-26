---
name: linkedin
description: LinkedIn automation via browser relay or cookies for messaging, profile viewing, and network actions.
Use for LinkedIn tasks: messaging, profiles, connections, content, search.
Do NOT use for: general browsing, bookmarking, LinkedIn account management, or non-LinkedIn tasks.

metadata: {"clawdbot":{"emoji":"💼"}}
---

# LinkedIn

Use browser automation to interact with LinkedIn - check messages, view profiles, search, and send connection requests.

## Connection Methods

### Option 1: Chrome Extension Relay (Recommended)
1. Open LinkedIn in Chrome and log in
2. Click the Clawdbot Browser Relay toolbar icon to attach the tab
3. Use `browser` tool with `profile="chrome"`

### Option 2: Isolated Browser
1. Use `browser` tool with `profile="clawd"` 
2. Navigate to linkedin.com
3. Log in manually (one-time setup)
4. Session persists for future use

## Common Operations

### Check Connection Status
```
browser action=snapshot profile=chrome targetUrl="https://www.linkedin.com/feed/"
```

### View Notifications/Messages
```
browser action=navigate profile=chrome targetUrl="https://www.linkedin.com/messaging/"
browser action=snapshot profile=chrome
```

### Search People
```
browser action=navigate profile=chrome targetUrl="https://www.linkedin.com/search/results/people/?keywords=QUERY"
browser action=snapshot profile=chrome
```

### View Profile
```
browser action=navigate profile=chrome targetUrl="https://www.linkedin.com/in/USERNAME/"
browser action=snapshot profile=chrome
```

### Send Message (confirm with user first!)
1. Navigate to messaging or profile
2. Use `browser action=act` with click/type actions
3. Always confirm message content before sending

## Safety Rules
- **Never send messages without explicit user approval**
- **Never accept/send connection requests without confirmation**
- **Avoid rapid automated actions** - LinkedIn is aggressive about detecting automation
- Rate limit: ~30 actions per hour max recommended

## Session Cookie Method (Advanced)
If browser relay isn't available, extract the `li_at` cookie from browser:
1. Open LinkedIn in browser, log in
2. DevTools → Application → Cookies → linkedin.com
3. Copy `li_at` value
4. Store securely for API requests

## Troubleshooting
- If logged out: Re-authenticate in browser
- If rate limited: Wait 24 hours, reduce action frequency
- If CAPTCHA: Complete manually in browser, then resume


---
## 🔧 Auto-Improvement (2026-03-21)
> Added by weekly-agent-review.py based on recurring failure pattern.

**Pattern detected (2 occurrences):**
Add completion guard: verify ALL required outputs (image, Notion update, etc.) before marking task done.

**Action required:**
- Review this section and integrate the fix into the relevant step above.
- Remove this block once the fix has been applied.

---
## 🔧 Auto-Improvement (2026-03-22)
> Added by weekly-agent-review.py based on recurring failure pattern.

**Pattern detected (2 occurrences):**
Add completion guard: verify ALL required outputs (image, Notion update, etc.) before marking task done.

**Action required:**
- Review this section and integrate the fix into the relevant step above.
- Remove this block once the fix has been applied.

---

## Learned Improvements

### 2026-04-25 - Weekly Skill Tune-Up

**Reviewed lessons:**
- 2026-04-22, prove the LinkedIn execution lane is exposed before blaming stale session state or asking Ahmed to reconnect.
- 2026-04-21, distinguish carousel preview, carousel asset, and single-post visual before delivery or publishing.
- 2026-04-20, live LinkedIn posting workflows must not go quiet or imply progress before a verified publish.

**Improvement recommendation:**
1. **Add a LinkedIn content pre-flight.** Before any content, visual, or posting action, identify the requested artifact type: text post, single-image post, carousel asset, carousel preview, comment, message, or profile/network action.
2. **Verify the live lane before user-facing fixes.** If a LinkedIn action fails, first prove whether the relevant lane is available: Ahmed-Mac Chrome for authenticated browser work, or the configured Composio/LinkedIn tool lane for approved posting. Do not send Ahmed through reconnect loops until lane exposure is proven.
3. **Separate draft, staged, and published states.** A post is not complete until the required text, image or carousel, destination account, live URL, and rendered content are all verified. If an image was expected, text-only publishing is a failure unless Ahmed explicitly approves the downgrade.
4. **Surface blockers after two failed publish paths.** For live posting, give short progress updates while debugging. If two independent publish paths fail, stop silently retrying and report the blocker with the fastest safe alternative.
5. **Create a future `eval/checklist.md`.** Cover artifact type, account identity, media requirement, full text verification, live URL, rendered post check, and Notion/status update when relevant.
