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
