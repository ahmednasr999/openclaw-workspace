# linkedin-engagement-agent

**Trigger:** Ahmed says "scan" in Telegram thread 7 (Content thread), or taps the "Scan Now" button from the morning cron message.

## Workflow

### Step 1 — Load Context
Read `memory/master-cv-data.md` and `memory/ontology/graph.jsonl` to build Ahmed's lens:
- Career: Talabat (Delivery Hero), HealthTech, FinTech, PMO, Digital Transformation, E-Commerce
- Target personas: VP+, Director, C-suite in GCC (UAE, Saudi, Qatar, Kuwait)
- 14-day cooldown: Person entities with `last_commented` within last 14 days — skip those

### Step 2 — Browser Discovery (Ahmed-Mac)
Use browser tool on Ahmed-Mac node. Run these 5 searches sequentially via LinkedIn:
1. `https://www.linkedin.com/search/results/content/?keywords=digital+transformation+AI+GCC&datePosted=past-24h&sortBy=date_posted`
2. `https://www.linkedin.com/search/results/content/?keywords=HealthTech+digital+health+Saudi+UAE&datePosted=past-24h&sortBy=date_posted`
3. `https://www.linkedin.com/search/results/content/?keywords=FinTech+payments+BNPL+Middle+East&datePosted=past-24h&sortBy=date_posted`
4. `https://www.linkedin.com/search/results/content/?keywords=PMO+program+management+executive+GCC&datePosted=past-24h&sortBy=date_posted`
5. Main feed: `https://www.linkedin.com/feed/`

For each page, use browser snapshot (compact=true, depth=4) to extract:
- Post content/text
- Author name + title
- Reactions + comments count
- Post URL (from `feed/update/urn:li:activity:...`)

Collect 20-40 unique posts.

### Step 3 — Context Scoring
Score each post 0-100 across 4 factors (25pts each):
1. **Career overlap** — does topic match: Talabat, Delivery Hero, HealthTech, FinTech, PMO, AI transformation?
2. **Persona match** — is author VP+/Director+/C-suite, GCC/MENA region?
3. **Comment opportunity** — high reactions, FEW comments (< 10) = open field
4. **Brand fit** — commenting reinforces Digital Transformation Executive brand

Skip any post where author URL matches 14-day cooldown list.
Select top 5.

### Step 4 — Draft Comments
For each of the 5 posts, draft a comment in Ahmed's voice:
- Reference his ACTUAL experience naturally (Talabat/scaling/HealthTech/FinTech as relevant)
- Add genuine insight — NOT flattery
- End with a question or observation that invites response
- 2-4 sentences MAX
- NO em dashes — use commas or hyphens
- Peer tone, not job seeker tone

### Step 5 — Send Approval Cards to Telegram Thread 7
Send header first, then 5 separate messages to `-1003882622947` thread `7`:

**Header:**
```
🔍 LinkedIn Engagement — {date}
Found 5 posts worth your attention. Review and approve below.
```

**Each post card:**
```
🎯 Post {n} of 5  |  Score: {score}/100

👤 {Author Name}
   {Author Title}
🔗 {Post URL}

💬 Draft Comment:
"{comment text}"

✅ Why: {one-line reason}
```
With inline buttons: [✅ Post It] [✏️ Edit] [❌ Skip]

### Step 6 — On Approval (✅ Post It)
When Ahmed taps ✅ or replies "post {n}":
1. Navigate browser to the post URL
2. Find comment box, type comment, submit
3. Like the post
4. Update ontology graph: find/create Person entity, set `last_commented` = today

### Step 7 — On Edit (✏️ Edit)
Reply: "What would you like to change?" — wait for Ahmed's reply, update comment, re-display card.

### Step 8 — On Skip (❌ Skip)
Reply "⏭ Skipped" and move on.

## Key Rules
- Only post after explicit ✅ approval — never auto-post
- No em dashes anywhere in comments
- Max 5 posts per day (never more)
- Skip authors commented on in last 14 days
- Log each posted comment to ontology graph
- Before counting a comment as posted, pass every gate in `eval/checklist.md`.

---

## Learned Improvements

### 2026-04-04 — Weekly Skill Tune-Up

**Context:** Two high-severity LinkedIn incidents in the prior week directly impact this workflow:

1. **Account verification pre-flight (from 3/23 wrong-account incident):** Before Step 6 (posting), ALWAYS verify which account the browser is authenticated as. The 3/23 incident posted comments under "Nasr Nasr" instead of Ahmed's account because Camofox cookies belonged to the wrong person. HARD RULE: Before any LinkedIn write action, verify authenticated account matches Ahmed (urn:li:person:mm8EyA56mj) or Ahmed-Mac Chrome. If in doubt, abort and ask.

2. **Browser discovery fallback (from 3/23 cookie expiration):** Step 2 relies on Ahmed-Mac Chrome browser. If Ahmed-Mac is offline, skip that day's scan entirely — do NOT fall back to Camofox or server-side scraping for anything that involves authenticated LinkedIn access. The 14-day cooldown in Step 1 also depends on correct account identity.

3. **Comment posting verification (from 3/29 agent going rogue):** After Step 6 posts a comment, verify the comment actually appears on the post page before reporting success. The 3/29 incident showed LinkedIn sometimes silently drops comments — never assume click = posted. Navigate back to the post and confirm the comment text is visible.

4. **No auto-scoring changes:** The scoring model (career overlap + persona + comment gap + brand fit) is working well. No changes needed this cycle.

### 2026-04-11 — Weekly Skill Tune-Up

**Reviewed signals:**
- 2026-03-23, comments risked going out under the wrong LinkedIn account
- 2026-03-29, agents on LinkedIn write paths need stronger forbidden-action language
- Weekly review history, completion guards need to be explicit, not implied

**Improvements to keep active:**
1. **Turn Step 6 into a hard pre-flight + post-flight block.** Require account identity check, comment submission, like action, then visible confirmation of both before success is reported.
2. **Add explicit forbidden fallbacks.** State clearly: no Camofox cookies, no server-side authenticated fallback, no posting from any account that is not Ahmed-Mac Chrome.
3. **Add an `eval/checklist.md`.** This skill currently has no dedicated checklist file. It should have a compact approval/posting checklist covering account identity, cooldown, URL match, posted-comment visibility, and ontology update.
4. **Separate discovery success from posting success.** Finding good posts is not completion. Completion only happens after approval flow, verified comment publish, and graph update all pass.

### 2026-04-18 — Weekly Skill Tune-Up

**Reviewed signals:**
- 2026-03-23, wrong LinkedIn account was used for comments
- Weekly reviews on 2026-03-21 and 2026-03-22, completion guards on LinkedIn engagement flows were still too implicit
- 2026-03-29, LinkedIn write paths needed explicit forbidden-action language, not soft STOP wording

**Improvements to add next:**
1. **Lock approvals to a post identity, not just a number.** Each Telegram card should carry the author URL plus activity URN, and Step 6 should re-check both before typing any comment so stale "post 3" approvals cannot land on the wrong target.
2. **Make proof-of-post explicit.** After submit + like, the workflow should require a fresh snapshot showing Ahmed's visible comment text on the intended post before success is reported.
3. **Add a hard abort for missing provenance.** If account identity, post URL, author URL, or cooldown status cannot be proven in the same session, abort instead of improvising.
4. **Create the missing `eval/checklist.md`.** Keep it short and binary: right account, right post, cooldown clear, approved text matches, visible comment confirmed, ontology updated.

### 2026-04-18 - Weekly Skill Tune-Up (cron refresh)

**Reviewed lessons:**
- 2026-03-23, wrong LinkedIn account for comments
- Weekly Review (2026-03-15 → 2026-03-22), LinkedIn comment-radar still needed explicit completion guards
- Weekly Review (2026-03-14 → 2026-03-21), the same completion-guard pattern was already recurring

**Improvements to add next:**
1. **Bind every approval card to an immutable post identity.** Include activity URN, author profile URL, and a short hash of the approved comment text. Step 6 must re-check all three before typing anything.
2. **Abort on environment drift.** If Ahmed-Mac is offline, the authenticated account changed, the post resolves to a different activity, or cooldown status cannot be proven, abort and regenerate cards instead of improvising.
3. **Make proof-of-post a first-class output.** Success requires a fresh post-submit snapshot showing Ahmed's visible comment text on the exact post, plus the like state when that step runs.
4. **Create the missing `eval/checklist.md`.** Keep it binary and short: right account, right post, cooldown clear, approved text unchanged, visible comment confirmed, ontology updated.

### 2026-04-25 - Weekly Skill Tune-Up

**Reviewed lessons:**
- 2026-04-22, do not frame LinkedIn failures as stale-session issues before proving tool/lane exposure.
- 2026-04-21, LinkedIn content workflows must verify the exact asset or post identity before acting.
- 2026-04-20, live LinkedIn write workflows need timely blocker escalation and verified success only.

**Improvement recommendation:**
1. **Add a same-session lane check before discovery and before posting.** Discovery must prove Ahmed-Mac Chrome is online and logged into Ahmed's account. Posting must re-prove the same account before typing or liking anything.
2. **Bind approvals to immutable post identity.** Each approval card should include activity URN, post URL, author profile URL, and approved comment text hash. Step 6 should re-check all fields before submitting so stale approvals cannot land on the wrong post.
3. **Treat write-path ambiguity as a hard abort.** If the account, post identity, cooldown status, or visible comment proof cannot be verified, abort and regenerate cards rather than improvising with another browser/session.
4. **Escalate live blockers quickly.** If submit or proof-of-post fails twice, report the blocker in thread 7 with a concise recovery option. Do not keep retrying silently or imply that the comment is posted before visible proof exists.
5. **Create the missing `eval/checklist.md`.** Keep it binary: Ahmed account verified, post identity matched, cooldown clear, approval text unchanged, visible comment confirmed, like state checked, ontology updated.

### 2026-05-09 - Weekly Skill Tune-Up

**Audit basis:** No lessons were logged in the last 7 days, so this stayed in scope as a default LinkedIn operations skill. The skill still has no `eval/checklist.md`, and the latest LinkedIn lessons continue to stress verified lane/account/post identity before any write action.

**Reviewed lessons:**
- 2026-04-22, prove LinkedIn tool or browser lane exposure before blaming stale sessions or asking Ahmed to reconnect.
- 2026-04-20, live LinkedIn write workflows need timely blocker escalation and verified success only.
- 2026-04-23, use the exact account Ahmed specifies for live auth or publishing flows.

**Improvement recommendation:**
1. **Add a lane-exposure preflight.** Before discovery and again before posting, prove Ahmed-Mac Chrome is online, logged into the correct Ahmed account, and able to access the target post.
2. **Bind approvals to immutable identity.** Approval cards should include activity URN, post URL, author profile URL, and a hash or exact copy of the approved comment text. Step 6 must re-check all fields before typing.
3. **Create the missing `eval/checklist.md`.** Keep it binary: correct account, correct post, cooldown clear, approved text unchanged, visible comment confirmed, like state checked, ontology updated, blocker escalated after two failed proof attempts.

### 2026-05-16 - Weekly Skill Tune-Up

**Audit basis:** Recent lessons from 2026-05-15 did not identify a LinkedIn engagement-specific failure, but they reinforce clean Telegram behavior and fixing preventable workflow noise. This skill still has no `eval/checklist.md`.

**Reviewed lessons:**
- 2026-05-15, avoid empty private closeouts after Telegram sends. Approval cards and post confirmations should carry the actual status, not bookkeeping.
- 2026-04-24, long public posting tasks need timely progress confirmation while blockers are being debugged.
- 2026-04-22, prove lane exposure before blaming stale sessions or asking Ahmed to reconnect.

**Improvement recommendation:**
1. **Create the missing engagement checklist.** Add `eval/checklist.md` with binary checks for Ahmed-Mac online, correct Ahmed account, activity URN match, author URL match, cooldown clear, approved text unchanged, visible comment confirmed, like state checked, and ontology updated.
2. **Make approval cards self-verifying.** Each card should include post URL, activity URN, author profile URL, and exact approved comment text so Step 6 can re-check identity before typing.
3. **Keep Telegram confirmations meaningful.** After a comment is posted, send one visible status with the post URL, visible-comment proof, like state, and ontology update result. Avoid extra private closeouts unless there is a real blocker.
4. **Fail fast on lane drift.** If Ahmed-Mac, account identity, target post, or visible proof fails twice, abort and report the blocker instead of falling back to another account or session.

### 2026-05-23 - Weekly Skill Tune-Up

**Audit basis:** No LinkedIn engagement-specific lesson appeared in the last 7 days, so this stayed in scope as a default LinkedIn operations skill. The recent Telegram slash-menu lesson reinforces that Bot/API success is not the same as user-visible channel behavior, and this skill still lacks `eval/checklist.md`.

**Reviewed lessons:**
- 2026-05-17, verify the actual Telegram client/menu-visible state, not only Bot API dispatch.
- 2026-05-15, avoid empty private closeouts after Telegram sends.
- 2026-04-22, prove LinkedIn lane exposure before blaming stale sessions or asking Ahmed to reconnect.

**Improvement recommendation:**
1. **Verify approval-card visibility, not just send success.** After sending the 5 Telegram approval cards, confirm the cards are visible in thread 7 with actionable approve/edit/skip controls or provide a plain-text fallback that still preserves post identity.
2. **Treat missing interactive controls as a degraded state.** If buttons or thread delivery fail, do not proceed to any posting path. Re-send a text-only approval card with the post URL, activity URN, author URL, and exact comment text.
3. **Keep post approval bound to exact evidence.** Approval should reference immutable post identity plus the exact approved comment text, not just "post n".
4. **Add the missing checklist next.** `eval/checklist.md` should include Telegram card visibility, Ahmed-Mac online, correct account, activity URN match, author URL match, cooldown clear, approved text unchanged, visible comment confirmed, like state checked, and ontology updated.

### 2026-05-30 - Weekly Skill Tune-Up

**Audit basis:** No LinkedIn-engagement-specific lesson appeared in the last 7 days, so this stayed in scope as a default LinkedIn operations skill. The recent Telegram slash-menu lesson reinforces that API success is not enough; user-visible approval-card state must be verified before any write path can proceed.

**Reviewed lessons:**
- 2026-05-17, verify actual Telegram client/menu-visible state, not just Bot API dispatch.
- 2026-05-15, avoid empty private closeouts after Telegram sends.
- 2026-04-22, prove LinkedIn lane exposure before blaming stale sessions or asking Ahmed to reconnect.

**Improvement recommendation:**
1. **Verify approval-card visibility as a gate.** After sending engagement cards to thread 7, confirm the cards and controls are visible or provide a text-only fallback with full post identity.
2. **Do not treat send success as approval readiness.** If buttons, thread delivery, or card visibility cannot be proven, stop before posting and report the degraded approval state.
3. **Re-check lane and account before every write action.** Posting still requires Ahmed-Mac online, correct Ahmed account, exact activity URN, author URL, approved text unchanged, cooldown clear, and visible proof after submit.
4. **Create `eval/checklist.md` next.** Include Telegram card visibility, fallback-card completeness, Ahmed-Mac/account check, post identity match, cooldown, approved text match, visible comment proof, like state, ontology update, and one meaningful closeout.

### 2026-06-06 - Weekly Skill Tune-Up

**Audit basis:** No direct LinkedIn-engagement lesson appeared this week, but multiple LinkedIn automation lessons affect this skill's write path: do not repair cookies, prefer visible authenticated profiles, keep one-tab browser flow, and require visible proof before reporting success. `eval/checklist.md` is still missing.

**Reviewed lessons:**
- 2026-06-02, Do Not Repair LinkedIn by Editing Cookies.
- 2026-06-03, LinkedIn Easy Apply Can Recover Through A Different Visible Authenticated Profile.
- 2026-06-02, LinkedIn Upload Success Needs Visible Exact-CV Proof.

**Improvement recommendation:**
1. **Forbid cookie-based engagement recovery.** If engagement discovery or posting hits redirects, 429, or auth drift, do not inspect or repair cookies. Use Ahmed-Mac Chrome or another visible authenticated profile, or stop.
2. **Keep approvals bound to the visible session.** Approval cards should remain tied to activity URN, author URL, approved comment text, and the browser profile/account that produced the evidence.
3. **Use one visible LinkedIn tab for engagement posting.** Reuse the authenticated LinkedIn tab through comment submission and proof capture. Do not open a new tab per post unless no reusable tab exists.
4. **Report only after visible proof.** A posted comment is complete only when a fresh visible snapshot shows Ahmed's comment on the exact target post, the like state is checked, and ontology `last_commented` is updated.
5. **Create `eval/checklist.md` next.** Include approval-card visibility, Ahmed account/profile identity, no-cookie-repair gate, one-tab reuse, activity URN match, author URL match, cooldown clear, approved text match, visible comment proof, like state, ontology update, and one meaningful closeout.


### 2026-06-13 - Weekly Skill Tune-Up

**Audit basis:** Recent LinkedIn lessons from 2026-06-02 to 2026-06-03 continue to affect engagement safety: cookie repair is a dead end, visible authenticated profiles are the recovery path, and one-tab visible proof is required before completion. `eval/checklist.md` is still missing.

**Reviewed lessons:**
- 2026-06-02, Do Not Repair LinkedIn by Editing Cookies.
- 2026-06-03, LinkedIn Easy Apply Can Recover Through A Different Visible Authenticated Profile.
- 2026-05-31, HR Easy Apply Should Reuse LinkedIn Tabs.

**Improvement recommendation:**
1. **Make cookie repair explicitly forbidden for engagement.** If LinkedIn redirects, 429s, or profile auth drifts, do not inspect, delete, edit, or replay cookies. Use Ahmed-Mac Chrome or another already-visible authenticated profile, or stop and report the blocked state.
2. **Reuse one visible LinkedIn tab where possible.** Discovery and posting should stay in the same authenticated visible session when feasible, navigating the tab to each approved post instead of spawning fresh pages that lose state.
3. **Bind approval to browser/profile evidence.** Approval cards should include activity URN, author URL, exact approved comment text, and the visible profile/account used during discovery; Step 6 must re-check all before typing or liking.
4. **Treat proof as the only completion signal.** Success requires a fresh visible snapshot showing Ahmed's comment on the exact post, like state checked, ontology `last_commented` updated, and one meaningful Telegram closeout. Add these gates to `eval/checklist.md` next.


### 2026-06-20 - Weekly Skill Tune-Up

**Audit basis:** No direct engagement-comment failure appeared in the last 7 days, but recent LinkedIn automation lessons apply to this skill's approval and posting path. The skill still has no `eval/checklist.md`, so the recommendation stays here.

**Reviewed lessons:**
- 2026-06-17, Bulk LinkedIn Application Counts Need Submitted Proof States.
- 2026-06-19, LinkedIn Bulk Campaigns Need Unique-ID Counts And Runner Fallbacks.
- 2026-06-14, Telegram Message Send Supports Media, Read Does Not.

**Improvement recommendation:**
1. **Count only unique verified engagement actions.** For comments, success means one unique activity URN with Ahmed's visible comment proof. Retries, queued approvals, skipped posts, failed proof captures, or duplicate rows do not count.
2. **Deduplicate by immutable post identity.** Before posting or reporting totals, collapse candidates and results by activity URN plus author URL so retry loops cannot inflate the scan or posted-comment count.
3. **Use runner fallback with the same approval gates.** If visible CDP ports are unavailable, switch to the approved browser runner only after preserving account identity, activity URN, author URL, approved text, cooldown status, and visible proof requirements.
4. **Do not rely on Telegram read for verification.** For approval-card or media delivery, trust the send response and available logs, then keep posting blocked unless Ahmed's approval and the exact post identity are present.

### 2026-06-27 - Weekly Skill Tune-Up

**Audit basis:** Recent lessons did not show a direct comment-posting failure, but they reinforce proof-state, unique identity, and live-content reconciliation for LinkedIn workflows. Engagement should only count verified live actions against immutable post identities.

**Reviewed lessons:**
- 2026-06-19, LinkedIn Bulk Campaigns Need Unique-ID Counts And Runner Fallbacks.
- 2026-06-26, Retracted LinkedIn Posts Must Be Excluded From Cadence.
- 2026-06-14, Telegram Message Send Supports Media, Read Does Not.

**Improvement recommendation:**
1. **Count engagement by immutable live post identity.** Discovery, approvals, comments, and reports should deduplicate by activity URN plus author URL. Retries, stale cards, failed proof captures, and duplicate rows do not count.
2. **Exclude retracted or deleted targets from live cadence.** Before reporting engagement coverage or acting on a post tied to Ahmed's own content, verify the target is still live and not a deleted/retracted version replaced by a corrected repost.
3. **Use runner fallback without weakening proof gates.** If the visible browser path is unavailable, any approved runner fallback must preserve account identity, activity URN, author URL, approved text, cooldown status, visible comment proof, like state, and ontology update.
4. **Handle Telegram verification realistically.** For approval-card delivery, trust send responses and available logs when read APIs cannot fetch media/buttons, but keep posting blocked unless Ahmed approval and exact post identity are present.
5. **Create `eval/checklist.md` next.** Include live post identity, dedupe by URN/author, retracted-post exclusion, correct Ahmed account, approved text match, visible comment proof, like state, ontology update, and one meaningful closeout.


### 2026-07-04 - Weekly Skill Tune-Up

**Audit basis:** Recent lessons did not show a direct engagement-comment posting failure, but LinkedIn workflow failures now cluster around live-state reconciliation and analytics proof. This skill should keep engagement discovery and approvals tied to immutable live post identities, and `eval/checklist.md` is still missing.

**Reviewed lessons:**
- 2026-06-26, Retracted LinkedIn Posts Must Be Excluded From Cadence.
- 2026-07-03, LinkedIn Metrics Backfill Needs Author-Visible Analytics.
- 2026-06-26, Daily LinkedIn Visuals Need A Hard QA Marker.

**Improvement recommendation:**
1. **Verify target posts are still live before approval or posting.** Engagement candidates should exclude deleted, retracted, or superseded posts, especially when a corrected repost exists.
2. **Bind engagement reporting to immutable post identity.** Discovery, approval cards, comments, and metrics should reconcile by activity URN plus author URL so retries or corrected reposts cannot inflate coverage.
3. **Keep analytics claims behind author-visible evidence.** Public reactions/comments can inform candidate scoring, but impressions/profile views or best-performer claims require approved author analytics; otherwise mark the metric path `blocked-login`.
4. **Create `eval/checklist.md` next.** Include live post identity, retracted-post exclusion, correct Ahmed account, approved text match, visible comment proof, like state, ontology update, analytics evidence boundary, and one meaningful closeout.
