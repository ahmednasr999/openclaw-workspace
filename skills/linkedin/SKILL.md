---
name: linkedin
description: >
  LinkedIn automation through Ahmed's approved managed browser or posting lane for messaging,
  profile viewing, connections, content, search, and application actions. Use for LinkedIn
  messages, recruiter outreach, profiles, connections, posts, analytics, and application flows.
  Do not use for general browsing, bookmarking, unrelated account management, or non-LinkedIn tasks.

metadata: {"clawdbot":{"emoji":"💼"}}
---

# LinkedIn

Use browser automation to interact with LinkedIn - check messages, view profiles, search, and send connection requests.

**Ahmed-specific lane decision (2026-08-08):** Use the Windows `openclaw` managed profile through `browser.proxy`. This lane is extension-free. Do not ask Ahmed to install, pair, or attach the Chrome extension. Do not fall back to Ahmed-Mac, exported cookies, or a server-side authenticated browser.

## Connection Methods

### Option 1: Windows Managed Chrome (Ahmed's Approved Lane)
1. Use `browser` with `profile="openclaw"`; the gateway routes it to Windows through `browser.proxy`.
2. Open LinkedIn and complete a one-time manual login if the persistent profile is signed out.
3. Reuse the labeled LinkedIn tab; no extension pairing is involved.

### Option 2: Other Isolated Browser
1. Use `browser` tool with the approved managed profile.
2. Navigate to linkedin.com
3. Log in manually (one-time setup)
4. Session persists for future use

## Common Operations

### Tab Reuse Rule
Before using LinkedIn in Chrome, list tabs and reuse an existing LinkedIn tab or a labeled task tab.

Preferred label examples:
- `hr-linkedin` for HR/job-search/application work
- `linkedin-content` for CMO/content work
- `linkedin-profile` for profile/research work

Do not open a new tab per job, profile, search, upload, or retry. Use one labeled tab and navigate it through the workflow. If a retry creates duplicates, close only the extra automation-created duplicates after confirming the intended labeled tab remains available.

### Check Connection Status
```
browser action=tabs profile=openclaw
# If no suitable LinkedIn tab exists:
browser action=open profile=openclaw url="https://www.linkedin.com/feed/" label="linkedin-profile"
browser action=snapshot profile=openclaw targetId="linkedin-profile"
```

### View Notifications/Messages
```
browser action=tabs profile=openclaw
# If no suitable LinkedIn tab exists:
browser action=open profile=openclaw url="https://www.linkedin.com/messaging/" label="linkedin-profile"
browser action=snapshot profile=openclaw targetId="linkedin-profile"
```

### Search People
```
browser action=tabs profile=openclaw
# If no suitable LinkedIn tab exists:
browser action=open profile=openclaw url="https://www.linkedin.com/search/results/people/?keywords=QUERY" label="linkedin-profile"
browser action=snapshot profile=openclaw targetId="linkedin-profile"
```

### View Profile
```
browser action=tabs profile=openclaw
# If no suitable LinkedIn tab exists:
browser action=open profile=openclaw url="https://www.linkedin.com/in/USERNAME/" label="linkedin-profile"
browser action=snapshot profile=openclaw targetId="linkedin-profile"
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
- Before reporting any operation complete, run every relevant binary gate in `eval/checklist.md`.

### Outbound message and connection approval boundary

Keep recruiter messages, connection notes, and connection requests draft-only until Ahmed explicitly approves the exact text/wording, exact recipient or target profile, and exact action as one pair. If any element is missing, hold and say **Do not send.** The user-visible response must identify the missing exact text-target approval and state that no LinkedIn or other external action occurs.

### Current-employer career-outreach boundary

Saudi German Health is Ahmed's current employer and an internal no-outreach zone for career networking. Do not connect with or message its leaders, HR, recruiters, or colleagues about external opportunities because doing so could expose Ahmed's confidential job search to management. Hold the action unless Ahmed grants an explicit, contact-specific exception for the exact contact and action. The visible decision must name Saudi German Health, the current-employer confidentiality risk, the required exception, and that no connection or message will be sent.

### Ambiguous message-send boundary

If a LinkedIn message action times out or returns an ambiguous result after Send, **Do not retry.** First verify fresh live LinkedIn conversation or thread state for the exact intended recipient and exact message text. If that evidence cannot resolve whether the original message was delivered, keep the action on hold and report the ambiguity; do not risk a duplicate recruiter message. The user-visible response itself, not only internal evidence or action fields, must say that the live LinkedIn conversation/thread, exact recipient, and exact message text need verification and that unresolved ambiguity remains on hold.

### Application upload and applied-state boundary

An upload helper or tool returning `ok` is not proof that LinkedIn selected the intended file or submitted the application. Hold the workflow until the visible Easy Apply UI shows the exact intended CV/file and then shows a visible, verified submitted confirmation. When the request cites an `ok` helper/tool result without that visible proof, begin the user-visible response with the sentence **The helper/tool `ok` result is not proof.** Then include the rest of the chain: hold and do not continue or submit; require the visible exact CV/file and verified submitted confirmation; do not mark or record the role as `applied`; and do not set `date_applied`.

## Authentication Boundary
Do not extract, store, refresh, or use LinkedIn cookies such as `li_at` or `JSESSIONID`.
Use approved Composio posting actions, JobSpy for job descriptions, or a live visible browser session when account state matters.

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
2. **Verify the live lane before user-facing fixes.** If a LinkedIn action fails, first prove whether the relevant lane is available: Windows Chrome extension for authenticated browser work, or the configured Composio/LinkedIn tool lane for approved posting. Do not use Ahmed-Mac as a LinkedIn fallback or send Ahmed through reconnect loops until lane exposure is proven.
3. **Separate draft, staged, and published states.** A post is not complete until the required text, image or carousel, destination account, live URL, and rendered content are all verified. If an image was expected, text-only publishing is a failure unless Ahmed explicitly approves the downgrade.
4. **Surface blockers after two failed publish paths.** For live posting, give short progress updates while debugging. If two independent publish paths fail, stop silently retrying and report the blocker with the fastest safe alternative.
5. **Create a future `eval/checklist.md`.** Cover artifact type, account identity, media requirement, full text verification, live URL, rendered post check, and Notion/status update when relevant.

### 2026-05-16 - Weekly Skill Tune-Up

**Audit basis:** `linkedin-writer` is not an active skill directory in this workspace, so this audit used the active `linkedin` skill as the default LinkedIn writing/operations substitute. No `eval/checklist.md` exists for this skill.

**Reviewed lessons:**
- 2026-05-15, avoid empty private closeouts after Telegram sends. LinkedIn actions that already sent a visible message should not add generic private receipts.
- 2026-04-29, Ahmed LinkedIn visuals must match the premium reference level, not rough template similarity.
- 2026-04-24, long public posting tasks need timely progress confirmation while blockers are being debugged.

**Improvement recommendation:**
1. **Add a LinkedIn operation checklist.** Create `eval/checklist.md` with binary gates for artifact type, account identity, media requirement, approved text, live URL, rendered content proof, and status update.
2. **Separate visible reply from private closeout.** If the workflow uses Telegram to notify Ahmed, that visible message should be the real answer. Avoid extra private "done" or "sent" receipts unless there is operational evidence to report.
3. **Require reference-level visual proof for image posts.** For Ahmed branded LinkedIn visuals, compare against the approved premium reference before staging or publishing. Reject generic, flat, under-designed, or text-on-face layouts.
4. **Escalate after two blocked publish paths.** If the browser lane and upload/publish lane both fail, stop retrying silently and report the blocker with the fastest safe alternative.

### 2026-06-06 - Weekly Skill Tune-Up

**Audit basis:** `linkedin-writer` is still not an active skill directory, so this audit used the active `linkedin` skill as the default LinkedIn writing/operations substitute. Recent lessons were strongly LinkedIn-heavy: cookie repair is forbidden, visible authenticated browser profiles can be swapped when one is blocked, and LinkedIn Easy Apply upload proof must be visible and exact. `eval/checklist.md` is still missing.

**Reviewed lessons:**
- 2026-06-02, Do Not Repair LinkedIn by Editing Cookies.
- 2026-06-02, LinkedIn Upload Success Needs Visible Exact-CV Proof.
- 2026-06-03, LinkedIn Easy Apply Can Recover Through A Different Visible Authenticated Profile.

**Improvement recommendation:**
1. **Make cookie repair a hard non-path.** LinkedIn recovery must not inspect, edit, dedupe, export, or refresh cookies. Use visible authenticated browser state, approved Composio posting, or JobSpy for descriptions only.
2. **Recover by switching visible profiles, not patching cookies.** If one LinkedIn browser profile is blocked by redirects, 429, or unauthenticated navigation, try another already-authenticated visible profile and keep the one-tab flow.
3. **Require exact visible upload proof.** For Easy Apply or any LinkedIn file upload, success means the visible UI shows the exact intended CV/file, not that an upload tool returned ok.
4. **Create `eval/checklist.md` next.** Include artifact type, account/profile identity, one-tab reuse, no-cookie-repair gate, exact selected-file proof, approved text/media, live URL or submit proof, rendered content proof, and status/ledger update.

### 2026-06-20 - Weekly Skill Tune-Up

**Audit basis:** `linkedin-writer` is still not an active skill directory, so this audit used the active `linkedin` skill as the default LinkedIn writing/operations substitute. Recent lessons were LinkedIn-heavy and focused on false completion signals, duplicate retry counts, runner fallback, and Telegram verification limits. `eval/checklist.md` is still missing.

**Reviewed lessons:**
- 2026-06-17, Bulk LinkedIn Application Counts Need Submitted Proof States.
- 2026-06-19, LinkedIn Bulk Campaigns Need Unique-ID Counts And Runner Fallbacks.
- 2026-06-14, Telegram Message Send Supports Media, Read Does Not.

**Improvement recommendation:**
1. **Gate LinkedIn completion on explicit proof.** For posts, comments, messages, or Easy Apply flows, completion requires the correct account, exact target identity, visible published/submitted state, and the expected media/file/content present.
2. **Deduplicate by immutable LinkedIn identity before reporting totals.** Collapse retries by activity URN, post URL, or job id before saying how many items were posted, commented, messaged, or submitted.
3. **Use runner fallback without weakening account checks.** If visible CDP ports fail, switch to the approved browser runner only after preserving the same authenticated account, target URL, and proof gates.
4. **Do not use Telegram read as a delivery proof path.** For Telegram confirmations, trust the send response and available logs, then keep LinkedIn action gates tied to visible LinkedIn evidence rather than Telegram readback.


### 2026-07-04 - Weekly Skill Tune-Up

**Audit basis:** `linkedin-writer` is still not an active skill directory, so this audit used the active `linkedin` skill as the default LinkedIn writing/operations substitute. Recent lessons were LinkedIn-heavy: daily visuals need a hard reference QA marker, retracted posts must not count as live cadence, and metrics require author-visible analytics. `eval/checklist.md` is still missing.

**Reviewed lessons:**
- 2026-06-26, Daily LinkedIn Visuals Need A Hard QA Marker.
- 2026-06-26, Retracted LinkedIn Posts Must Be Excluded From Cadence.
- 2026-07-03, LinkedIn Metrics Backfill Needs Author-Visible Analytics.

**Improvement recommendation:**
1. **Fail image posts closed without the QA marker.** For Ahmed LinkedIn static visuals, publishing or staging should require `Visual QA: PASS - reference-checked handmade sketchnote` against the actual final image, not just deterministic dark-card checks.
2. **Separate live posts from deleted or corrected versions.** Cadence, duplicate checks, and backlog reports should exclude rejected, deleted, or retracted posts while preserving an audit note for corrected reposts.
3. **Do not infer analytics from public signals.** Impressions, profile views, and best-performer claims require author-visible LinkedIn analytics from an approved logged-in session; otherwise stop at `blocked-login` with the newest missing rows identified.
4. **Create `eval/checklist.md` next.** Include artifact type, visual QA marker, account identity, live/retracted-state check, approved text/media, rendered post proof, author-visible analytics requirement, and status update.
