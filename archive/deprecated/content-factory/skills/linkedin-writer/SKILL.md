---
name: LinkedIn Writer
description: Writes LinkedIn posts that sound like a real person, not a content mill
---

# LinkedIn Writer

You write LinkedIn posts that sound human. Not cringe, not corporate, not "I'm humbled to announce." Real thoughts from a real person.

## Workflow

Follow these steps in order for every post request:

1. **Ask intake questions** — Read `templates/intake-questions.md` and ask the user those questions before writing anything.

2. **Reader-first reframe** — Before writing a single word, answer this question: *"What real problem does my target reader have that this post solves?"* The post must be about THEM, not Ahmed's achievement. Reframe every topic from "what Ahmed did" to "what the reader can learn/do/feel." Test: would a stranger with no context care about this?

3. **Choose post format** — Read `examples/post-formats.md` and select the format that best fits the user's topic and goals.

4. **Load voice rules** — Read `instructions/voice.md` and internalize these rules before writing.

5. **Load formatting rules** — Read `instructions/formatting.md` and apply these rules to the draft.

6. **Craft the hook** — Read `instructions/hooks.md` and generate 10 hook variants across all 5 techniques. Present them to Ahmed for selection. Do NOT pick one yourself — taste is the competitive advantage.

7. **Write the draft** — Compose the full post using the chosen format, voice rules, formatting rules, and the selected hook.

7.5. **AI-pattern audit** — Before quality check, read `skills/avoid-ai-writing/SKILL.md` and run the draft through it in **rewrite** mode (linkedin profile). This is mandatory for every post. The skill will flag and fix: promotional language, significance inflation, Tier 1 vocabulary (delve, leverage, robust, etc.), filler phrases (Moreover, Furthermore), generic conclusions, uniform sentence length, copula avoidance. Apply the rewrite before step 8. If the draft is clean, note it passed the audit.

8. **Run quality check** — Read `eval/checklist.md` and verify every item passes before delivering.

9. **Revise if needed** — If any checklist item fails, revise the draft until all items pass.

10. **Deliver final post** — Present the finished post with the chosen hook at top, ready to copy-paste into LinkedIn.


---
## 🔧 Auto-Improvement (2026-03-21)
> Added by weekly-agent-review.py based on recurring failure pattern.

**Pattern detected (2 occurrences):**
Add completion guard: verify ALL required outputs (image, Notion update, etc.) before marking task done.

**Action taken (2026-04-04):**
Integrated into step 8 (quality check). Added pre-delivery verification:
- Verify post text renders at full length (no Composio truncation -- see 3/23 incident)
- Verify correct image source (Notion S3 URL, NOT stale Google Drive -- see 3/29 incident)
- Verify Unicode bold formatting rendered correctly (not Python escape sequences -- see 3/29 incident)
- Confirm payload matches post body exactly before any delivery step
- If posting via cron agent: respect IMAGE_HOLD as hard stop, not suggestion



---
## 🔧 Auto-Improvement (2026-03-22)
> Added by weekly-agent-review.py based on recurring failure pattern.

**Pattern detected (2 occurrences):**
Add completion guard: verify ALL required outputs (image, Notion update, etc.) before marking task done.

**Action taken (2026-04-04):**
Already addressed by 2026-03-21 section above. Both entries consolidated into the step 8 pre-delivery verification block.

## Learned Improvements

### 2026-04-11 — Weekly Skill Tune-Up

**Reviewed signals:**
- 2026-03-26, stale visual chosen from Google Drive instead of the source of truth
- 2026-03-29, agent ignored IMAGE_HOLD and improvised around the workflow
- 2026-04-05, never publish text-only when an image is required and unavailable

**Improvements to keep active:**
1. **Source-of-truth rule must be explicit.** If a post references an image, the skill should state the exact approved image source order and forbid stale mirrors.
2. **HOLD states are terminal, not advisory.** If image upload, rendering, or source validation fails, the skill must stop and report the blocker instead of drafting a workaround.
3. **Split writing vs publishing checks.** The current checklist is strong on copy quality, but weak on asset/payload verification. Add a second checklist block for image presence, payload length, final formatting, and source confirmation.
4. **Deprecated skill still needs a banner.** Because this lives under `archive/deprecated`, add a one-line warning near the top that directs active workflows to the current LinkedIn posting skill so old instructions do not get used accidentally.

### 2026-05-23 - Weekly Skill Tune-Up

**Audit basis:** No LinkedIn-writer-specific lesson was logged in the last 7 days, so this stayed in scope as a default skill. The review used the last relevant LinkedIn lessons and the current `eval/checklist.md`, which still focuses on copy quality more than publish readiness.

**Reviewed lessons:**
- 2026-04-23, LinkedIn visuals need feed-native composition and semantic alignment with the post thesis.
- 2026-04-21, verify whether the requested asset is a carousel preview, carousel file, or single-post visual before presenting or publishing.
- 2026-04-20, live LinkedIn write workflows need timely blocker escalation and verified success only.

**Improvement recommendation:**
1. **Add a deprecated-skill routing guard.** This archived writer should explicitly direct active publishing or image-required workflows to the current LinkedIn/content skill before drafting starts.
2. **Extend quality checks beyond copy.** The checklist should add a publish-readiness block for required image state, asset type, source of truth, payload length, final formatting, and post thesis alignment.
3. **Stop on visual or payload uncertainty.** If the post requires an image and the approved asset is missing, stale, wrong-format, or semantically mismatched, the skill should return the blocker instead of producing a publish-ready claim.
4. **Keep writing output draft-safe.** Unless the active publishing workflow has separately verified assets and target account, this skill should deliver only the final draft text, not imply that posting is complete.


### 2026-06-13 - Weekly Skill Tune-Up

**Audit basis:** Recent LinkedIn lessons from 2026-06-10 focus on visual quality and reliable media delivery. This skill is archived, but it still has an `eval/checklist.md` and can be pulled into old content flows, so the recommendation keeps it draft-safe and tightens visual/media handoff language.

**Reviewed lessons:**
- 2026-06-10, Hand-drawn LinkedIn Quality Floor.
- 2026-06-10, Resend Generated Images Through Direct Telegram Photo Path After Media Failure.
- 2026-06-02, Do Not Repair LinkedIn by Editing Cookies.

**Improvement recommendation:**
1. **Keep this archived writer draft-only by default.** It should produce copy and review notes, not imply publishing is complete unless the current active LinkedIn publishing workflow verifies account, media, and delivery.
2. **Add a visual-quality floor to image-dependent posts.** When a post depends on a visual, require semantic alignment with the thesis and reject assets below the approved ROT hand-drawn quality floor: polished editorial sketchnote, warm paper texture, authentic lettering, strong whitespace, clean story flow, restrained orange accents, no sketch-filter look, and no crowded or overlapping elements.
3. **Treat media delivery failure as resend-first.** If Ahmed sees `Media failed`, locate the generated image, verify size/dimensions, save a durable copy under `output/linkedin`, resend via direct Telegram photo path, and confirm `message_id` before regenerating or calling the asset lost.
4. **Do not repair LinkedIn auth from this skill.** Any auth, cookie, or posting-lane issue belongs to the active LinkedIn publishing/engagement workflow, not the archived writer.
