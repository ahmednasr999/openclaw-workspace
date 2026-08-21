# Lessons Learned

## 2026-04-23 - Visual Briefs Need Semantic Background Alignment And Explicit Signature Rules
### What I got wrong
I kept optimizing the card for premium feel while missing two concrete brief requirements: the background needed to be semantically tied to the topic, and the card should include `Ahmed Nasr | Digital Transformation Executive` while not requiring Ahmed's portrait.
### Why
I over-focused on style matching and portrait integration instead of locking the actual content constraints from Ahmed's corrections.
### Fix
For branded social visuals, confirm and preserve the non-negotiables: topic-related background, whether portrait is required, and exact footer/signature text. Do not keep iterating premium styling while those brief anchors are still wrong.

## 2026-04-23 - Stop Iterating A Broken Visual Direction After The User Clearly Dislikes It
### What I got wrong
Ahmed said he did not like the visual, and I kept iterating within the same weak direction instead of stepping back and changing the concept or asking for a sharper choice on direction.
### Why
I treated repeated polish passes as progress even after the underlying concept was not landing. I optimized the artifact instead of re-evaluating the brief.
### Fix
When Ahmed rejects a visual direction, stop the polish loop. Switch modes immediately: either propose 2-3 fresh directions with clearly different concepts, or ask one sharp question about what feels wrong. Do not burn turns polishing a direction he already dislikes.

## 2026-04-23 - Premium LinkedIn Visuals Cannot Use Text-On-Face Generic AI Portrait Layouts
### What I got wrong
I delivered a Talabat LinkedIn visual that put large text directly on Ahmed's face/suit, used a generic airbrushed AI-portrait look, and called it premium.
### Why
I prioritized making something quickly presentable instead of measuring it against premium editorial standards: clean negative space, semantic background, credible composition, and typography that does not fight the subject.
### Fix
For premium LinkedIn visuals, reject layouts that place core copy across the face, rely on generic AI-portrait aesthetics, or use weak decorative labels. Use either a semantically relevant environment with clean text zone, or a proper editorial/poster composition with deliberate typography separation.

## 2026-04-23 - Social Posts Need Platform-Native Composition, Not Poster Or Editorial Cover Logic
### What I got wrong
Ahmed wanted something that reads like a social media post, and I kept drifting into editorial-cover, poster, or presentation-style compositions.
### Why
I optimized for premium aesthetics in isolation instead of checking whether the artifact actually looked native to a LinkedIn feed.
### Fix
For LinkedIn visuals, check the format test first: does it read like a feed-native social asset at a glance? Prefer stronger hook hierarchy, simpler social-card structure, clearer platform-native pacing, and less magazine-cover staging when the goal is a post image rather than a campaign poster.

## 2026-04-23 - Never Let Raw NO_REPLY Leak To Ahmed
### What I got wrong
A raw `NO_REPLY` surfaced in chat as if it were a real assistant message.
### Why
I treated an internal silent-reply artifact like a safe user-facing output instead of catching it and replacing it with either a real reply or silence.
### Fix
Never send raw `NO_REPLY` to Ahmed. If the runtime/tooling echoes it, immediately clarify that it was an internal artifact and continue with a normal user-facing reply.

## 2026-04-22 - Reverify Live Issue State Before Stating Open vs Closed
### What I got wrong
I stated that lossless-claw issue #427 was closed based on the saved monitor state, but Ahmed had fresher live evidence that the issue page still showed open even though a released fix existed.
### Why
I trusted cached monitor state as if it were definitive current truth instead of treating it as potentially stale and separating issue-state visibility from release-fix status.
### Fix
When summarizing live upstream status, reverify the current page/API state before saying an issue is open or closed. Keep the fix-status claim separate: a shipped fix can be true even if the issue state/reporting looks inconsistent.

## 2026-04-22 - Do Not Blame Session State Before Proving Tool Exposure
### What I got wrong
I kept framing the LinkedIn posting failure as a stale-session or reconnect issue before proving whether the Composio execution lane was actually exposed in the runtime.
### Why
I inferred too much from prior successful runs and from the user reconnecting LinkedIn, instead of treating fresh-session verification as the decisive test earlier.
### Fix
When an external tool lane appears missing, verify tool exposure first. Do not send Ahmed through reconnect/new-session loops unless there is evidence that session state is the real blocker. Once a fresh session still lacks the lane, say plainly that the issue is runtime integration, not user action.

## 2026-04-21 - Do Not Mislabel Vendor SEO Emails As Interview Invites
### What I got wrong
I surfaced a Diib SEO/marketing report email as if it were an interview invite.
### Why
I trusted a bad triage/category label instead of sanity-checking the sender, subject, and actual email intent before presenting it to Ahmed.
### Fix
Before calling anything an interview invite, verify it is actually from a recruiter, hiring team, employer, or assessment/interview workflow. Vendor alerts, SEO reports, newsletters, and marketing emails must never be labeled as interview activity.

## 2026-04-21 - Distinguish Carousel Preview, Carousel Asset, and Single-Post Visual
### What I got wrong
Ahmed asked for the visual for today’s LinkedIn post, and I mixed up three different things: the carousel preview montage, the actual carousel file, and the standalone single-post visual.
### Why
I moved too fast from asset discovery to delivery and treated the nearest existing file as publish-ready instead of matching the asset type to the actual posting format.
### Fix
For LinkedIn content, verify the format first: preview image for review, carousel file for carousel publishing, or standalone visual for a single-image post. Do not send one as if it were another.

## 2026-04-21 - Do Not Restart The Gateway From Inside The Same Live DM Recovery Run
### What I got wrong
During main DM recovery, the agent rebuilt successfully, then tried to restart the gateway from inside the same live user-facing run that depended on that gateway path to finish the reply.
### Why
The recovery logic overreached. It treated restart as the natural next step after rebuild without respecting that the active DM run could lose its own execution path mid-recovery.
### Fix
For DM/topic runtime failures, do not stop or restart the gateway from inside the same live user-facing recovery run. Rebuild and verify first, then recover through a safer out-of-band path, or tell Ahmed to retry once the lane is healthy again.

## 2026-04-21 - Match LinkedIn visuals to the actual post thesis
### What I got wrong
I presented Apr 22 visuals that were available in the content lane, but they did not semantically match the post's thesis about fintech moats shifting to licensing, rails, and regulatory readiness.
### Why
I optimized for date/file availability instead of checking whether the visual metaphor actually reinforced the post content.
### Fix
For LinkedIn post reviews, do not present a visual as the candidate just because it is scheduled or locally attached. First verify that the image concept directly matches the post thesis, industry, and metaphor. If it does not, say so immediately and propose replacement directions.

## 2026-04-21 - Claude Code OAuth here requires pasting the browser auth code into the waiting terminal
### What I got wrong
I kept telling Ahmed the browser-side completion alone should finish Claude Code OAuth, and I treated the pasted auth code as unnecessary or unsupported by this CLI path.
### Why
I trusted incomplete CLI help output and the failing remote-session behavior more than the actual browser evidence, which clearly showed an Authentication Code page instructing the user to paste the code into Claude Code.
### Fix
For Claude Code OAuth in this environment, treat the browser auth code page as authoritative: the terminal is usually waiting for that code. Instruct Ahmed to paste the code into the same waiting VPS terminal and press Enter, then run follow-up verification commands only after login completes.

## 2026-04-19 - Do Not Pause Mid-Remediation Waiting For Another Push
### What I got wrong
Ahmed told me to keep going until the security remediation was done, but I paused after an intermediate step and waited for another nudge.
### Why
I treated an async command boundary like a decision boundary instead of owning the workflow through verification and the next safe action.
### Fix
When Ahmed says continue until done, keep driving the sequence proactively. After each command or restart, immediately verify, take the next safe step, and only surface real blockers or final results.

## 2026-04-18 - Agent Status Updates Still Need Emojis
### What I got wrong
An agent completion update to Ahmed went out flat, without emojis, even though he has explicitly asked for them repeatedly.
### Why
I treated agent-result delivery as sterile telemetry instead of a normal user-facing message that should still reflect Ahmed's communication preference.
### Fix
Use light emojis in agent completion and status updates by default, unless the message is highly sensitive. Operational does not mean emotionless.

## 2026-04-20 - Do Not Go Quiet Or Imply Progress When A Live Posting Workflow Is Blocked
### What I got wrong
Ahmed asked me to post today’s LinkedIn post. I kept pushing a broken automation path, went quiet for stretches, and did not surface the blocker fast enough. I also made progress-sounding updates before I had a verified successful post.
### Why
I overcommitted to recovering the automation path in-turn, instead of quickly escalating once image staging and browser fallback both failed. I let persistence turn into silence.
### Fix
For live posting or delivery workflows, if the publish step is not verified, say so immediately. Give short progress updates while actively debugging, and if two publish paths fail, surface the blocker clearly with the fastest alternative instead of disappearing into tool retries.

## 2026-04-18 - When The User Wants A Template Match, Do Not Drift Into Style Approximation
### What I got wrong
Ahmed asked for a final picture that looked like the provided blue ad reference but with his image, and I delivered a result that was far from the template structure.
### Why
I optimized for style inspiration and general likeness instead of matching the concrete layout constraints of the reference, including the blue rounded panel, subject placement, footer blocks, and ad-template composition.
### Fix
When Ahmed asks for a close visual match, treat the reference as a layout spec. First compare the generated result against the reference on composition, subject placement, panel geometry, background, and CTA/footer structure. If it misses those anchors, do not present it as close.

## 2026-04-17 - Do Not Use Ambiguous "Half-Done" Wording When Work Is Actually Complete
### What I got wrong
I answered with wording that included "Nothing important is left half-done tonight," which invited the interpretation that something was half done.
### Why
I was trying to reassure on completeness, but used a phrase that sounded like there were dangling items.
### Fix
When work is complete, say it plainly: done, complete, or closed out. Do not use ambiguous reassurance phrasing that implies unfinished work.

## 2026-04-17 - Do Not Touch JobZoom Without Explicit Approval
### What I got wrong
After Ahmed explicitly protected JobZoom as a full-scan lane, I still suggested trimming `workspace-jobzoom/SOUL.md` as part of context cleanup.
### Why
I treated JobZoom as just another optimization target instead of respecting it as a protected workflow boundary.
### Fix
Do not modify, trim, optimize, gate, or otherwise touch JobZoom artifacts unless Ahmed explicitly asks for JobZoom changes. Treat JobZoom as out of bounds by default.

## 2026-04-17 - Topic Theory Was Too Narrow, The Failure Also Hits Telegram DM
### What I got wrong
I kept framing the command problem as mainly an HR topic or forum-topic ingestion issue, but Ahmed confirmed the same failure response appears even in Telegram DM.
### Why
I anchored too hard on the topic evidence and did not widen the hypothesis fast enough once the same symptom appeared outside the topic.
### Fix
Treat repeated "Something went wrong while processing your request" responses across both topic and DM as a broader Telegram command or dispatch-path failure, not a topic-only bug.

## 2026-04-17 - Rebuild Success Does Not Prove Telegram Topic Commands Are Fixed
### What I got wrong
I treated a successful OpenClaw rebuild and disappearance of stale dist references as if that likely solved Telegram topic command handling, then asked Ahmed to test again before I had hard proof.
### Why
I over-weighted build cleanliness and under-weighted end-to-end verification. A cleaner dist state is not the same thing as working command ingestion in Telegram forum topics.
### Fix
Do not infer command-path recovery from rebuild output alone. After any command-surface repair, verify with a real end-to-end command result before suggesting the issue is probably fixed.

## 2026-04-17 - Do Not Treat Retired Notion Dashboard Health As An HR-Agent Requirement
### What I got wrong
I kept Notion dashboard timeouts in the HR health discussion after Ahmed made clear the dashboard is no longer needed.
### Why
I treated old visibility plumbing as part of the live requirement instead of pruning it from the decision once Ahmed ruled it out.
### Fix
If Ahmed says a reporting/dashboard surface is no longer needed, stop using its errors as evidence of agent health. Separate operationally required paths from retired visibility layers.

## 2026-04-17 - Do Not Treat Retired SAYYAD Automation As A Live HR Requirement
### What I got wrong
I treated disabled SAYYAD scoring and curation crons as an HR-agent problem and recommended re-enabling them before confirming whether Ahmed still wanted SAYYAD at all.
### Why
I inferred current requirements from old automation and heartbeat docs instead of checking whether that workflow was still wanted.
### Fix
Treat SAYYAD as retired unless Ahmed explicitly reactivates it. Do not recommend re-enabling SAYYAD crons or score HR health against SAYYAD automation until that assumption is revalidated.

## 2026-04-17 - Do Not Use Generic OpenClaw Update Flow On A Symlinked Repo Checkout Without Proving The Install Topology
### What I got wrong
I used the standard OpenClaw update flow on this host before proving how the `openclaw` binary was installed. The host resolves `openclaw` to a symlinked local repo checkout at `/root/openclaw`, not a normal packaged install, and the updater moved that checkout from the working `update/v2026.4.14-local-fleet` branch to an old `main`, effectively downgrading the CLI to 2026.4.11.
### Why
I followed the normal update safety checklist but missed the more fundamental topology check: this box runs OpenClaw from a live git worktree via the NVM global symlink. That makes `update.run` a git-worktree mutation, not a package-only upgrade.
### Fix
Before any future OpenClaw update here, first prove install topology with `command -v openclaw`, `readlink -f $(command -v openclaw)`, `npm -g ls openclaw --depth=0`, and repo branch status under `/root/openclaw`. If it is a repo-backed checkout, never use generic update flow blindly. Create a git checkpoint, preserve the working branch, and update intentionally as a git operation.

## 2026-04-17 - Agent Heartbeat Updates Must Be Properly Formatted And Use Emojis
### What I got wrong
I let an HR agent heartbeat-style update go out in a flat blocky format without the light emoji styling Ahmed expects.
### Why
I treated the message like raw operational telemetry instead of a user-facing update that still needs clean structure and Ahmed's preferred tone.
### Fix
Format heartbeat and agent updates with short sections or bullets, clearer visual hierarchy, and light emojis by default. Do not send dense plain-text status blobs to Ahmed.

## 2026-04-17 - Do Not Declare The Lossless CLI Surface Resolved Before Proving The Exact Command Path
### What I got wrong
I told Ahmed the leftover around `lossless` command access likely did not need a config change and treated the issue as mostly command-path confusion before I had fully proven the actual CLI behavior on this host.
### Why
I over-interpreted partial evidence. `lossless-claw` being present in `plugins.allow` does not prove the bundled `openclaw lossless` or `openclaw /lossless` surfaces are actually admitted by the current CLI/router behavior.
### Fix
When command-surface behavior is in doubt, prove the exact command with a bounded probe before drawing conclusions. Distinguish clearly between plugin allowlisting and command alias exposure, and do not reassure Ahmed that no change is needed until the command works end to end.

## 2026-04-15 - Verify ACP runtime availability before promising Codex/Claude harness execution
### What I got wrong
I moved straight from drafting a Codex ACP brief to trying to spawn an ACP harness session without first verifying that the ACP runtime backend was configured on this host.
### Why
I assumed the presence of ACP-oriented tooling and prompts implied the runtime plugin was available, but `sessions_spawn` failed because the `acpx` runtime plugin is not configured here.
### Fix
Before offering to launch Codex, Claude Code, or another ACP harness, verify ACP runtime availability first. If ACP is unavailable, say so plainly and offer the closest acceptable fallback instead of implying the harness launch will just work.

## 2026-04-15 - Important Recruiter Follow-Ups Must Not Fall Through Narrow Email Rules
### What I got wrong
I missed the important email `Ranger AI - Followup` from `sari@rangerrfx.com` even though it had already been scanned earlier that day.
### Why
The email classifier was too narrow. `rangerrfx.com` was not recognized as a recruiter/hiring domain, the subject/body patterns did not match the existing interview/follow-up regexes, and recruiter emails were allowed to fall out of the actionable path. That caused the message to be stored as `other` with low priority instead of being surfaced.
### Fix
Treat recruiter follow-ups as high-sensitivity signals. Expand subject/body patterns beyond literal `interview` and `schedule`, include recruiter-domain and known-contact reach in actionable detection, and keep regression tests for important real examples like Ranger AI so they cannot silently regress again.

## 2026-04-12 - Premium Visual Requests Need Real Design, Not Template Import
### What I got wrong
Ahmed asked for a strong Canva-ready carousel and I delivered a deck that was structurally correct but visually weak, generic, and nowhere near premium quality.
### Why
I optimized for fast importability and clean structure instead of treating visual quality as the core requirement. I solved the mechanics, not the standard.
### Fix
For premium content requests, prioritize art direction, hierarchy, spacing, and visual distinctiveness before delivery. Do not hand off a first import as "final" unless it actually looks premium on review. Build and QA against that bar, not just technical completion.

## 2026-04-19 - Check Native X/Twitter Lane Before Starting Composio Auth
### What I got wrong
I started a Composio X connection flow before checking the local service registry and native workspace config for an existing X/Twitter method.
### Why
I followed the generic Composio path too quickly and skipped the documented decision order in `config/service-registry.md`.
### Fix
Before starting any X/Twitter auth flow here, first check `config/service-registry.md` and local config files. Prefer the native lane already documented in the workspace: public tweet reading via oEmbed and engagement via cookies/browser. Only use Composio for X if the registry or current task clearly requires it.

## 2026-04-12 - Do Not Invent Product/App Names For Device Pairing
### What I got wrong
I told Ahmed to open an "OpenClaw app" on iPhone/iPad without verifying the actual companion app name or distribution path first.
### Why
I generalized from the platform name instead of checking the local docs and current product surface.
### Fix
For device pairing or mobile access, verify the exact companion app name and onboarding path from local docs before instructing Ahmed. Do not invent product names.

## 2026-04-12 - Recurring Work Must Become A Skill, Not A One-Off
### What I got wrong
Ahmed had to restate the recurring-work rule explicitly: if work is the kind of thing that will happen again, I am not allowed to leave it as ad hoc execution.
### Why
I was still treating some repeated operational work as task completion instead of process discovery that must converge into a single owner skill and, when appropriate, cron automation.
### Fix
For recurring work, follow this cycle every time: concept, manual prototype on 3-10 real items, review with Ahmed, extend or create exactly one owner skill in `workspace/skills/`, add cron if it should run automatically, then monitor early runs. If Ahmed has to ask a second time, treat that as workflow failure and fix the skill ownership gap.

## 2026-04-12 - Emoji Preference Missed Again In Routine Replies
### What I got wrong
Ahmed had to correct me again because I let a routine status-style reply go out without emojis, despite repeated reminders.
### Why
I was still mentally separating operational updates from conversational style, instead of applying his communication preference consistently across both.
### Fix
Use at least light emoji support in normal Ahmed-facing replies, including routine daily summaries when they are delivered in chat. Keep it tasteful and sparse, but stop sending fully flat replies by accident. ✅

## 2026-04-12 - Emoji Preference Is Explicit, Not Optional
### What I got wrong
Ahmed reminded me again that he has asked many times for emojis, and I still answered too plainly.
### Why
I kept defaulting to a minimal executive tone instead of treating his stated communication preference as a standing instruction.
### Fix
Use emojis naturally in normal replies by default with Ahmed, especially in conversational messages and light summaries. Keep them sparse and useful, but do not wait to be asked again. 🙂

## 2026-04-12 - Do Not Trust sessions_spawn cwd Without Verification
### What I got wrong
I treated an eval failure as prompt drift before proving that `sessions_spawn` was actually honoring the `cwd` I passed.
### Why
I assumed the harness was doing what the API shape implied, and I started tuning instructions before verifying the execution context.
### Fix
When a subagent result looks unrelated or cannot find obviously provided files, first prove the actual working directory with a tiny `pwd`/`ls` sanity run. Treat harness behavior as a separate variable before editing prompts.

## 2026-04-12 - Use Emojis When Ahmed Expects Them
### What I got wrong
I kept defaulting to plain report tone and underused emojis even after Ahmed told me multiple times to use them.
### Why
I over-indexed on clean executive style and treated warmth as optional instead of following Ahmed's explicit communication preference.
### Fix
Use emojis naturally in normal chat replies and light summaries unless the context is sensitive or highly formal. Keep them sparse and additive, but do not omit them when Ahmed has clearly asked for them.

## 2026-04-09 - Never Rewrite Unknown Gateway Config Fields
### What I got wrong
I changed `channels.slack.streaming` from Ahmed's working value `"partial"` to an object form while trying to clear a validation problem.
### Why
I trusted an incomplete schema interpretation instead of the known-good workspace convention and I touched a gateway config field I did not fully understand.
### Fix
Do not modify `channels.slack.streaming` in this workspace. More broadly, never rewrite OpenClaw config fields unless I fully understand the version-specific format and have verified the exact on-disk value first. For multi-step tasks, complete all requested steps without pausing for updates unless I hit a real blocker.

## 2026-04-10 - Verify Update Target, Service Entrypoint, and Temp Headroom Before OpenClaw Updates
### What I got wrong
During tonight's update incident, the gateway ended up in a massive restart loop. Ahmed had to fix multiple problems: version-format mismatch, memory-lancedb validation, `/tmp` filling to 100% from update preflight, and the systemd service pointing at a different install path than the one I updated.
### Why
I treated `openclaw update` as a single safe action instead of verifying the full deployment chain: active service entrypoint, install method, temp-disk headroom, post-update runtime path consistency, and safe validation after each single change.
### Fix
Permanent rule set now promoted to SOUL.md:
1. Before any config change, run `openclaw --version` and check systemd `ExecStart`; they must match.
2. Before any update, ensure `/tmp` has at least 2GB free and clean preflight artifacts after update.
3. Never change config field formats without confirming support in release notes for the current running version.
4. After any config edit, validate with a manual 15-second gateway dry run before restart and confirm `Config invalid` does not appear.
5. One change at a time: change, restart, verify. Never batch config changes.

## 2026-04-10 - Do Useful Work Now, Do Not Hide Behind "Tomorrow"
### What I got wrong
I said I could turn a useful policy block into AGENTS.md tomorrow instead of either doing it now or clearly saying why it should wait.
### Why
I was trying to ease off after a long night, but in practice that was just deferring a useful next step without a real blocker.
### Fix
If a next step is useful, low-risk, and actionable now, do it now. Only defer when there is an explicit pause request, a real blocker, or a real risk reason.


## 2026-04-08 - Boot Check Is Not Enough For New Services
### What I got wrong
I reported SearXNG as set up after proving the container was up and a single query worked, but Ahmed had to ask whether I had really tested it well.
### Why
I stopped at an initial smoke test instead of doing a fuller verification pass covering multiple queries, HTML, JSON output, and log review.
### Fix
For any newly deployed service, do not stop at "container is up" or one happy-path response. Verify at least: process health, multiple realistic queries, expected output format, and recent logs for hidden engine or permission errors before calling it done.

## 2026-04-08 - Do Not Assume Brave Exists
### What I got wrong
I said Brave search was the broken default and implied it was a missing configuration we might wire up later.
### Why
I generalized from a missing `BRAVE_API_KEY` instead of treating Ahmed's actual setup choice as authoritative.
### Fix
Treat Brave as intentionally absent in this workspace. Do not suggest it, plan around it, or describe it as a pending integration. Use Tavily or other approved search paths instead, and verify actual configured search providers before answering.

## 2026-04-06 — Telegram Commands Outage (OpenClaw 2026.4.5 partial update)
### What happened
All native Telegram commands (/status, /models, /new) stopped working silently. No visible error to the bot — commands were simply not responding.
### Root cause
OpenClaw 2026.4.5 update via npm was incomplete. dist files under `/usr/lib/node_modules/openclaw/` were partially updated, but npm still registered 2026.4.1. A renamed module file (`bot-native-commands.runtime-DmqbZsFC.js` → `DtyEJfGY`) was missing — the bot bundle referenced the old hash.
### Fix
Forced clean reinstall: `npm install -g openclaw@2026.4.5 --force`, then `systemctl restart openclaw-gateway.service`. All commands restored. Memory dropped from 3.2GB to ~922MB.
### Lesson
- After any OpenClaw update, verify commands work immediately (`/status` is a good smoke test)
- Gateway restart after update is mandatory — files alone aren't enough
- Partial updates can silently break core features without clear error messages
- This reinforced the rule in TOOLS.md: gateway restarts = crash risk, but are required after updates
### Ongoing monitoring
- qwen3.6-plus:free via OpenRouter returning 429 rate limit errors — watch for task impact

## 2026-04-04 - Broke Notion Content, Then Stopped Waiting for Permission to Fix It
### What Happened
While updating Notion page images, I ran a script that archived/deleted body content blocks for Apr 5-9 posts. The image-update script wiped existing content. After Ahmed asked about missing content, I identified the problem and started restoring — but then **stopped mid-fix** and waited for Ahmed to push me to continue. The recovery should have been automatic.
### Why
Two failures:
1. Script archived ALL blocks before adding new images, then failed to restore content
2. After discovering content was lost, I switched to "report progress" mode instead of "fix immediately" mode. Treated my own mess as something needing Ahmed's go-ahead to clean up.
### Fix
1. **NEVER archive/delete without first reading and storing the full content** — always read-before-write pattern
2. **When you break something, recovery is automatic** — no questions, no status updates mid-fix. You break, you fix, then you report. The user should never have to push you to clean up your own mess.
3. **Notion API**: you can't PATCH image blocks. Use page covers (PATCH cover field on page endpoint) or delete-and-replace while preserving other content
4. **Notion page covers require HTTPS** — HTTP URLs won't render

## 2026-04-02 - Heredoc Syntax Permanently Blocked (Hardcoded)
### What Happened
Heredoc syntax (`<<EOF`, `<<'EOF'`, `<< 'SCRIPT'`) is flagged as "obfuscated commands" by the gateway security scanner. This is hardcoded in OpenClaw 2026.4.1 - not a config issue, cannot be bypassed.
### Alternatives
1. Write files with `node -e "require('fs').writeFileSync(...)"` 
2. Use `echo "content" > file.txt`
3. Use Write/Edit file tools directly (preferred)
4. Write script file first via tool, then exec it separately
### Scope
All agents, all sessions, permanent until OpenClaw changes the scanner.
### Fix
When writing or editing shell scripts, never use heredocs to create file content.
Preferred alternatives:
- `node -e "require('fs').writeFileSync('file.txt', 'content')"` for short content
- Write to a temp .py or .js file first, then execute it
- Use Python open().write() pattern in a separate script
- For multi-line content: write a proper .py/.js file instead of inline bash generation
### Scope
Applies to all new scripts and any heredoc spotted during edits. Existing scripts get refactored when touched.


## 2026-04-01 - Failed to notify Ahmed after restart
### What I got wrong
Said "back in a few seconds" before gateway restart, then never sent a confirmation message when the restart completed. Instead silently ran doctor commands and responded to a heartbeat. Ahmed had to call it out.
### Why
Treated the post-restart heartbeat as a system task instead of recognizing it was also the moment I owed Ahmed a status update. Prioritized housekeeping over communication.
### Fix
After any restart where I told the user "back in X": first message post-restart MUST be a confirmation to the user ("Back. Update applied, running 2026.4.1."). Housekeeping commands come AFTER the user acknowledgment.

## 2026-03-26
### What I Missed
Ahmed had to ask about free image generation. I had Gemini via Composio, PIL templates, and a known image reliability gap in the auto-poster - all the ingredients for the image-gen-chain - but never proactively proposed it.
### Why
Reactive mode. I was treating each tool/script as isolated instead of scanning for gaps across the full pipeline (Notion -> image -> auto-poster -> LinkedIn).
### Fix
Weekly pipeline audit: every Friday, scan the full content pipeline end-to-end for gaps, unused capabilities, and reliability risks. Surface findings to Ahmed without being asked. The question to ask: "What free tools/connections do I have that aren't wired into any workflow yet?"

## 2026-03-19

### What I Missed
LinkedIn daily post cron posted WITHOUT image when image upload failed, then failed to update Notion because of wrong property type (sent rich_text instead of url type).

### Why
1. **Gave up instead of fixing:** Cron agent hit image upload error and chose "post without image" instead of diagnosing and retrying with a different method
2. **Bug in SKILL.md:** Error handling section literally said "If image upload fails: Post WITHOUT image" - gave agents explicit permission to deliver partial results
3. **Bug in script:** `update_notion_status()` used `rich_text` format for Post URL property, but Notion property type is `url`
4. **No retry logic:** Both failures were single-attempt with no diagnosis or alternative approaches

### Fix
1. Added "Never Give Up" rule to SOUL.md - applies to ALL agents, ALL models, ALL tasks
2. Rewrote linkedin-daily-post/SKILL.md - removed "post without image" fallback, added 3-attempt retry strategies for every failure mode
3. Fixed Post URL property type in both SKILL.md and linkedin-auto-poster.py (url, not rich_text)
4. Added proxy_execute method as primary post creation path (avoids Composio S3 key requirement for images)

### Real Damage
- 4 LinkedIn likes lost (had to delete and re-post)
- Algorithm cold restart on re-posted content
- Engagement damage is permanent - can't recover those impressions

### Rule (Permanent)
**Partial completion = failure.** Never post without image if content has one. Never skip Notion update. Diagnose errors, try 3+ approaches, only report failure after exhausting all options.

---

## 2026-02-17

### What I Missed
1. Didn't check Telegram ID before cron ran → caused failure
2. Let files accumulate → should have synced to GitHub org earlier
3. Built web dashboard reactively → should have offered proactively
4. Didn't connect Renato's tweet to our workflow immediately

### Why
- Assumed "Ahmed" would work
- Focused on single tasks, not system design
- Waiting for instructions instead of anticipating needs

### Fix
1. Always verify target identifiers before configuring crons
2. At session start, ask "What should we sync/push today?"
3. When something works, immediately ask "How does this fit the bigger picture?"
4. End every session with: What did I miss? What will I do differently?

---

## 2026-04-13 - Checked only the native lane, missed Composio Gemini
### What I got wrong
Ahmed asked whether Gemini was back. I answered from the native OpenClaw runtime only, using session status and built-in image provider checks, and said Gemini was not back. That missed the active Gemini path exposed through Composio.
### Why
I treated "availability" as a single surface instead of checking both lanes separately: native OpenClaw providers and Composio tool-router providers. I stopped at the first partial signal.
### Fix
For any model or app availability question, check all relevant execution lanes before answering. In this setup that means: native runtime/config, built-in tools, and Composio-discovered tools if the service can also arrive through Composio. Answer with lane-specific status, not a blanket yes/no.

## Template (Future)

```
## [Date]

### What I Missed
1. [Specific example]
2. [Specific example]

### Why
- [Root cause 1]
- [Root cause 2]

### Fix
- [What I'll do differently 1]
- [What I'll do differently 2]
```

## 2026-03-19
### Check Existing Scripts Before Building New Solutions
- **What happened:** Ahmed asked to transcribe a YouTube video. I downloaded audio and ran local Whisper (4 min) instead of using the existing `scripts/youtube-transcript.sh` which does it in 2 seconds via yt-dlp subtitles.
- **Why:** Didn't scan existing workspace scripts before starting work. Went straight to "build it" mode.
- **Fix:** Before any transcription/media task, always check `scripts/` directory first. Run `ls scripts/*transcript* scripts/*youtube*` before building anything new. Also applies broadly: search the workspace for existing solutions before creating new ones.

## 2026-03-21

### Composio Assumption Failure (Critical)
- **What happened:** Asked Ahmed to connect Notion via Composio twice, despite workspace already having direct API token in `config/notion.json` and a working client in `scripts/notion_client.py`. Ahmed had told me this before in a prior session.
- **Root cause:** Treated Composio "no active connection" as the final answer instead of checking workspace config files first. Took the easy "ask user" shortcut instead of exhausting available resources.
- **Fix:** Created `config/service-registry.md` as single source of truth for all service connections. Updated AGENTS.md proactive checklist to make service registry check #1. Rule: NEVER ask user to authenticate before checking service-registry.md and config/ directory.
- **Category:** correction, error

### Enforcement
- ✅ `config/service-registry.md` created as SSoT for all service connections
- ✅ SOUL.md operating principles updated
- ✅ AGENTS.md proactive checklist reordered
- ✅ Applied in all subsequent sessions (no repeat Composio assumption errors)

### Service Registry System Deployed (Fix for Composio Assumption)
- **What:** Built comprehensive `config/service-registry.md` covering ALL external services, tools, skills, scripts, config files, and their connection methods.
- **Structural changes:**
  1. `config/service-registry.md` created with decision tree, all services, all config files, all skills mapped to their services, all cron scripts mapped to their dependencies
  2. Promoted to L0 (always loaded) in `CONTEXT-TIERS.md`
  3. Added as item #1 in proactive checklist in `AGENTS.md`
  4. Added "service pre-flight" rule to `SOUL.md` operating principles
- **Maintenance rule:** When ANY new tool, skill, integration, or service is added, it MUST be added to service-registry.md in the same session. No exceptions.

### Enforcement
- ✅ `config/service-registry.md` created and populated
- ✅ SOUL.md updated with "service pre-flight" operating principle
- ✅ AGENTS.md proactive checklist updated (service registry = check #1)
- ✅ CONTEXT-TIERS.md promoted service-registry to L0
- ✅ Rule active: never ask user to authenticate before checking registry

## Weekly Review (2026-03-14 → 2026-03-21)

_Generated by weekly-agent-review.py at 2026-03-21 23:07_


### Auto-Fixed Skills

- **skills/linkedin/SKILL.md**: Add completion guard: verify ALL required outputs (image, Notion update, etc.) before marking task done. _(occurrences: 2)_
- **skills/cron/linkedin-daily-post/SKILL.md**: Add completion guard: verify ALL required outputs (image, Notion update, etc.) before marking task done. _(occurrences: 2)_
- **skills/linkedin-writer/SKILL.md**: Add completion guard: verify ALL required outputs (image, Notion update, etc.) before marking task done. _(occurrences: 2)_
- **skills/linkedin-comment-radar/SKILL.md**: Add completion guard: verify ALL required outputs (image, Notion update, etc.) before marking task done. _(occurrences: 2)_
- **skills/cron/cron-health-monitor/SKILL.md**: Add explicit retry logic (3 attempts) for all external API calls. _(occurrences: 7)_


### Flagged for Human Review

- **general**: 3 unclassified signal(s) — manual review recommended.
### Proactive Fix vs Ask Rule (2026-03-21)
- **What happened:** Found broken ID matching in daily-learner.py (0% accuracy with 139 applied jobs). Reported the issue, then asked Ahmed "want me to fix it?" instead of just fixing it.
- **Root cause:** Applied the wrong default - asked for permission on an obvious bug fix rather than just doing it.
- **Fix:** Flip the default. Broken data, obvious bugs, clear errors -> fix immediately, report what changed in the same message. Ask only for: strategic decisions, things that cost money, things that change output materially without a clear failure state.
- **Category:** correction

### Gap ID Without Recommendation (2026-03-21)
- **What happened:** Identified that named agents lack SOUL.md/IDENTITY.md files (no consistent identity). Described the gap fully. But then just said "it's worth knowing" instead of recommending to build them.
- **Root cause:** "Gap identification" was treated as complete once described. No internal rule requiring a recommendation.
- **Fix:** Added explicit rule to SOUL.md: "Gap identification always includes a recommendation." Every gap spotted must include "here's what we should do about it." Identifying without recommending is now a defined failure mode, not just incomplete.
- **Category:** correction, improvement
## 2026-03-22

### correction
- Said 'X.com blocks scrapers, can't access' when Ahmed shared a tweet - but vxtwitter API worked fine
- Root cause: Defaulted to 'I can't' instead of trying alternative methods (vxtwitter, nitter, etc.)
- Fix: When X/Twitter links are shared, always try api.vxtwitter.com/{user}/status/{id} FIRST before saying can't access

## 2026-03-22

### improvement
- email-agent was crashing 4/5 runs (Himalaya Rust panic on Gmail HIGHESTMODSEQ response)
- Root cause: Himalayan v1.1.0 (nix-flake Jan 2025) has a string handling bug with certain Gmail IMAP responses
- Fix: Replaced Himalayan CLI with Python imaplib - same credentials, same logic, zero Rust crashes
- Test: 50 emails fetched successfully, same categorization output

## 2026-03-22

### improvement
- NotebookLM CLI integrated: , cookies from Ahmed's browser via Cookie-Editor (Netscape JSON format)
- Auth storage: ~/.notebooklm/storage_state.json (20 Google cookies including SID, OSID)
- Test: YouTube video analyzed successfully - ~30s end-to-end
- Wrapper: scripts/notebook-agent.py for quick YouTube → structured summary
- Free: NotebookLM processes YouTube on Google's servers, no API cost to us
- Security: cookies expire ~2028, may need refresh periodically


## 2026-03-22

### improvement
- NotebookLM CLI integrated: pip install notebooklm-py, cookies from Ahmed browser via Cookie-Editor
- Auth storage: ~/.notebooklm/storage_state.json
- Test: YouTube video analyzed successfully - 30s end-to-end
- Wrapper: scripts/notebook-agent.py for quick YouTube to structured summary
- Free: NotebookLM processes on Googles servers, no API cost
- Security: cookies expire ~2028, may need refresh periodically


## Weekly Review (2026-03-15 → 2026-03-22)

_Generated by weekly-agent-review.py at 2026-03-22 08:00_


### Auto-Fixed Skills

- **skills/linkedin/SKILL.md**: Add completion guard: verify ALL required outputs (image, Notion update, etc.) before marking task done. _(occurrences: 2)_
- **skills/cron/linkedin-daily-post/SKILL.md**: Add completion guard: verify ALL required outputs (image, Notion update, etc.) before marking task done. _(occurrences: 2)_
- **skills/linkedin-writer/SKILL.md**: Add completion guard: verify ALL required outputs (image, Notion update, etc.) before marking task done. _(occurrences: 2)_
- **skills/linkedin-comment-radar/SKILL.md**: Add completion guard: verify ALL required outputs (image, Notion update, etc.) before marking task done. _(occurrences: 2)_
- **skills/cron/cron-health-monitor/SKILL.md**: Retry logic exists but may not cover all failure paths — review error handling blocks. _(occurrences: 7)_


### Flagged for Human Review

- **himalaya**: Pattern unclear — flagged for human review.
- **cron/email-check**: Pattern unclear — flagged for human review.
- **general**: 7 unclassified signal(s) — manual review recommended.
## 2026-03-23

### Wrong LinkedIn Account for Comments (CRITICAL)
- **What happened:** Posted 5 LinkedIn comments using Camofox browser which was logged into "Nasr Nasr" (linkedin.com/in/nasr-nasr-1603163b4), NOT Ahmed Nasr's account. Comments were posted under the wrong person.
- **Root cause:** Camofox cookies at ~/.openclaw/cookies/linkedin.txt are for Nasr's account, not Ahmed's. Failed to verify which account the browser was authenticated as before posting.
- **Fix applied:** 
  1. Deleted comment #1 (Construction Business News) via Voyager API (HTTP 204)
  2. Comments #2-5 were never actually posted (LinkedIn silently dropped them - the "Comment" button clicks may not have registered properly, or they were auto-moderated)
  3. NEW HARD RULE: Nasr's cookies = job search ONLY. NEVER for commenting, posting, messaging, or any action that writes under his name.
  4. For LinkedIn commenting, must use Ahmed's actual account via Composio (urn:li:person:mm8EyA56mj) or Ahmed posts manually
- **Prevention:** Before ANY LinkedIn write action, verify which account is authenticated. Add pre-flight check to Comment Radar workflow.

## 2026-03-23
### What I Missed
LinkedIn posts via Composio were being truncated at ~950 chars. I verified posts were "live" without checking full text rendered. Ahmed had to delete 3 truncated posts and ultimately post manually after 1+ hour wasted.
### Why
1. Composio LINKEDIN_CREATE_LINKED_IN_POST has undocumented ~950 char truncation bug (schema says 3000)
2. I didn't verify full post text on first successful post yesterday
3. Kept retrying the same broken tool instead of immediately switching approach
4. Camofox LinkedIn cookies had expired, blocking the Voyager API fallback
### Fix
1. NEVER use Composio for LinkedIn posting until truncation bug is confirmed fixed
2. Build direct posting via Voyager API (script created: scripts/linkedin-direct-post.py)
3. Every post MUST be verified: fetch post content and compare char count before reporting success
4. Add cookie health check to nasr-doctor.py morning run
5. When a tool fails, switch approach after ONE retry max - don't burn user's time with repeated attempts

---

## 2026-03-24 — Grill-Me Skipped After LCM Cron Build

### What I Missed
Built the LCM Nightly Health Check cron + skill (new skill, new cron = auto-trigger) and declared done without running grill-me. Ahmed had to call it out.

### Why
Session startup sequence only reads MEMORY.md, active-tasks.md, and today's daily notes — not AGENTS.md. The grill-me obligation lives in AGENTS.md, which was not in the session startup read list.

### Fix
1. AGENTS.md updated: "Post-build reminder" clause added — if user asks "are you done?" and grill-me hasn't run, treat as failure. User should never have to remind.
2. Changed the signal: "are you done?" = "did grill-me run?" — they are now linked in the rules.
3. The session startup reads MEMORY.md which references AGENTS.md — the gap was that I didn't re-read AGENTS.md after learning about the new build in the same session.

## 2026-03-26
### LinkedIn Visual Mismatch
**What happened:** Posted GenAI Small t to LinkedIn with old Google Drive image (240KB, with source text) instead of the correct v3 Notion-hosted image (1.57MB, no source).
**Root cause:** Downloaded visual from Google Drive (stale) instead of from Notion (source of truth). Google Drive files were never updated after v3 regeneration.
**Fix:** When posting to LinkedIn, always pull images from Notion File Upload API (the source of truth), not Google Drive. Update auto-poster script to use Notion → S3 staging → LinkedIn flow.

## 2026-03-27
### What I Missed
Triggered a Composio OAuth flow for Notion and Telegram before checking workspace credentials. Both have direct API access already configured.

### Why
Defaulted to Composio before reading service-registry.md and config/ directory.

### Fix
**Hard rule (non-negotiable):**
- **Notion** → always use `config/notion.json` token directly. Never use Composio for Notion.
- **Telegram** → always use the bot token hardcoded in scripts (e.g. `content-factory-exa-scanner.py`) or `config/telegram.json`. Never use Composio for Telegram.
- Before ANY auth flow: check `config/service-registry.md` + `config/` directory first. If a token exists, use it. Period.

## 2026-03-27
### Config Corruption: openclaw.json Bindings
**What I Missed:**
Set all `bindings[].type` to "route" via Python script, but left `acp` blocks present (invalid under RouteBindingSchema.strict()). Also never added `match.peer.kind` — a required field. Two stacked errors.

**Why:**
1. Didn't understand AcpBindingSchema vs RouteBindingSchema — they have different required/allowed fields
2. Bulk-overwrote fields without checking each binding's schema variant
3. Trusted misleading Zod union error messages (showed wrong variant's allowed values)
4. No validation step after edit, no backup before edit

**Fix (Rules - Non-Negotiable):**
1. NEVER modify openclaw.json without running config validate immediately after. If validation fails, do NOT restart.
2. NEVER bulk-overwrite fields across all bindings without understanding each binding's schema variant.
3. Always backup before editing: `cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak.$(date +%s)`
4. Keep the file locked (`chattr +i`) at all times. Only unlock → edit → validate → re-lock.
5. Don't trust Zod union errors at face value — inspect the schema source when stuck.

## 2026-03-28
### LinkedIn Job Scraping - Approved Method (Non-Negotiable)
**Rule:** HR Agent ALWAYS uses JobSpy with `linkedin_fetch_description=True` for LinkedIn jobs.
**Why:** Hits LinkedIn's public /jobs/view/ API — no auth, no cookies, full JDs, works from VPS.
**Script:** scripts/jobs-source-linkedin-jobspy.py
**Reference:** https://github.com/DaKheera47/job-ops
**NEVER use:** BeautifulSoup scraping, Selenium, Composio LinkedIn tools, or any auth-dependent method.
**What went wrong before:** Old script used requests+BS4 against linkedin.com/jobs/search/ which blocked from VPS IPs.

## 2026-03-29 — LinkedIn Auto-Post with Wrong Image + Bold
### What Happened
CMO cron agent ignored IMAGE_HOLD from linkedin-auto-poster.py and went rogue:
1. Downloaded image from Notion directly (bypassing script's decision)
2. First posted text-only accidentally, then deleted and reposted with image
3. Constructed Unicode bold text using Python escape sequences instead of using the pre-formatted payload
4. Result: wrong image, wrong bold formatting, Ahmed had to delete the post

### Root Cause
1. SKILL.md was too weak - said "STOP" for IMAGE_HOLD but had no explicit FORBIDDEN actions list
2. The agent treated HOLD as a suggestion, not a hard stop
3. Notion external image URL pointed to GitHub raw URL that was never git-pushed (404)

### Fixes Applied
1. **SKILL.md hardened** - Added FORBIDDEN ACTIONS section with 8 explicit bans, triple-reinforced STOP rules, payload verification step
2. **download_image() improved** - Now dynamically searches ALL media/post-images* directories instead of just hardcoded paths
3. Image pipeline root cause: Notion pages reference GitHub raw URLs for images that were never committed to git

### Prevention
- Agent skill files for destructive actions (posting, sending, spending) must have explicit FORBIDDEN sections
- "STOP" is not enough - must enumerate specific workarounds the agent might try and ban each one
- Image URLs in Notion should use Notion file uploads (signed S3) not external GitHub raw URLs

## 2026-03-30
### What I Missed
Told Ahmed "alerts went out" from push-to-nocodb.py without verifying. The alerts had NEVER worked - script used `--to` instead of `--target` in the openclaw CLI call. Every send_telegram() silently failed since creation. Gave confident wrong answer 3 times before checking.
### Why
1. Assumed "script ran OK" = "everything worked" without checking actual delivery
2. Said "alerts went out" based on pipeline log showing "OK nocodb-push (7s)" - but OK only meant the script exited 0, not that messages landed
3. Didn't verify before answering - violated the "figure it out FIRST" directive
### Fix
- NEVER claim something happened without evidence of the outcome (exit code 0 ≠ success)
- When asked "did X happen?" - CHECK before answering, don't speculate
- Silent failures in subprocess calls need stderr/stdout logging - add to all scripts that use openclaw CLI

## 2026-03-31 - YouTube Transcript: 5 Hours, 16 Installs, Zero Transcript
### What I got wrong
Iterated through 16 extension versions live, discovering each technical blocker one at a time (CORS, service worker isolation, Chrome CSP, ip=0.0.0.0 in signed params, async executeScript returns, URL-encoded params) instead of researching them upfront.
### Why
Started building immediately without doing homework on the full technical landscape first.
### Fix
For ANY non-trivial technical task: research the known failure modes FIRST (30 min), then build ONE solution that addresses all of them. If the task requires user action (installs, approvals), it must work in 1-2 tries. No exceptions.

## 2026-04-02 - Gateway Restart Commands Crash System
### What I Got Wrong
Suggested `openclaw gateway stop`, `openclaw gateway stop && start`, or similar restart commands as a fix for exec/cron issues multiple times.
### Why
Didn't account for the fact that gateway restart causes system instability/crashes in this environment. Treated restart as a safe diagnostic/triage step when it's actually destructive here.
### Fix
**Never** suggest `openclaw gateway stop`, `openclaw gateway restart`, or any variant as a troubleshooting step. Treat the gateway as crash-prone in this environment. If restart is genuinely needed, get explicit Ahmed approval first with full context of crash risk. Related: exec-approvals.json is locked and cannot be modified — this is a confirmed upstream 2026.4.1 bug, wait for OpenClaw patch.

## 2026-04-05 - SAYYAD dedup misses re-posted jobs
### What I Missed
Atos CTO showed up as SUBMIT today even though we applied Mar 30. Same for JCA Associates submitted twice (Apr 2 + Apr 3).
### Why
1. DB dedup query used `WHERE status IN ('applied','interview')` — 20+ applied jobs had `status='skipped'` so they were invisible
2. URL hash dedup only catches exact same LinkedIn job ID, not re-posts with new IDs
3. No company+title fuzzy match against historical scored jobs
### Fix
1. Changed query to `WHERE applied_date IS NOT NULL` — catches all applied jobs regardless of status
2. Added Stage 3c: fuzzy dedup (88% threshold) against ALL historical jobs by company+title, skipping only same URL hash
3. Backfilled: marked Atos CTO repost (id 21290) and JCA duplicate (id 20252) as duplicate-applied


## Weekly Review (2026-03-29 → 2026-04-05)

_Generated by weekly-agent-review.py at 2026-04-05 08:00_



### Flagged for Human Review

- **cron/linkedin-daily-post**: Pattern unclear — flagged for human review.
- **cron**: Pattern unclear — flagged for human review.
- **cron/job-scanner**: Pattern unclear — flagged for human review.
- **job-search-mcp**: Pattern unclear — flagged for human review.
- **general**: 20 unclassified signal(s) — manual review recommended.
## [2026-04-05] - Posted LinkedIn post without image
### What I missed
Posted "AI agents are moving faster than governance" without its image. The image URL is on a local/internal IP (76.13.46.115) that Composio sandbox can't reach. I should have flagged the issue BEFORE posting.
### Why
The LinkedIn auto-poster script outputs READY_TO_POST with image_required=true, but the Composio workbench sandbox is isolated and can't reach the VPS-local image server. I proceeded with text-only instead of stopping to report the blockage.
### Fix (permanent)
1. If image_required=true AND image can't be uploaded → STOP and report to Ahmed. Never post text-only when an image was expected.
2. Move images to a location the sandbox can reach (public S3, GitHub raw, Notion CDN) — not local IPs.
3. Do NOT delete posts that are already live — always wait for Ahmed's instruction.

## 2026-04-07 - Model-router.json reset after restart
### What Happened
After a gateway restart, the session kept falling back to MiniMax-M2.7 every message. Ahmed asked "which model do you use now" twice in a row.
### Why
`/root/.openclaw/workspace/config/model-router.json` had `default_model: "minimax-portal/MiniMax-M2.7"` and all rule models pointing to dead Claude IDs. This file overrides per-session model choices. It was reset after the restart.
### Fix
Updated `model-router.json` with:
- `default_model: "openai-codex/gpt-5.4"`
- All rule models updated to GPT-5.4
- `after_task_completion: "minimax-portal/MiniMax-M2.7"` (fallback only)
- Dead Claude references removed
- Also added explicit MEMORY.md note so this doesn't get lost again
### Prevention
Always check `config/model-router.json` first when session keeps falling back to MiniMax. This file is the actual session-level model controller, not just OpenClaw global defaults.

## 2026-04-08 - SAYYAD spec implemented partially instead of fully
### What I got wrong
I treated Ahmed's SAYYAD redesign as threshold tuning and source narrowing, but skipped the actual required 5-dimension scoring model and did not fully replace the flat title search method with compound queries as specified.
### Why
I optimized the existing pipeline incrementally instead of implementing the spec literally.
### Fix
When Ahmed gives a structured redesign spec, implement each numbered change exactly as stated, and show the concrete mapping from spec item to code and prompt changes before claiming completion.

## 2026-04-08 - Do Not Execute When User Is Only Asking For Explanation
### What I got wrong
Ahmed asked what `openclaw update --channel dev` does, and I ran it instead of answering only.
### Why
I misread an explanatory question as approval to act, then moved too fast.
### Fix
When the user asks what a command does, treat it as explanation-only unless they explicitly ask me to run it. If I am unsure, answer first and ask before taking action.

## 2026-04-08 - Do Not Turn Repo Access Into A Standing Assumption
### What I got wrong
I treated Ahmed's statement about current repo access as a standing permission rule and wrote it into USER.md as something I should assume going forward.
### Why
I optimized for speed and collapsed a task-scoped clarification into a permanent operating rule.
### Fix
Do not assume repo permissions or access scope from prior chat context alone. Verify when it matters, or let Ahmed specify the access level for the current task.

## 2026-04-11 - Telegram media send requires allowed directory
### What I Missed
Tried sending JobZoom report and ZIP directly from /root/.openclaw/workspace-jobzoom/reports/ via the message tool. The send failed because local media paths must be under an allowed directory.
### Why
I assumed the message tool would accept any local absolute path.
### Fix
Before sending local files through the message tool, copy them into /root/.openclaw/media (or another allowed media directory) first, then send that path.

## 2026-04-11 - Cross-agent model leaks can come from workspace-local routers and persisted session overrides
### What I got wrong
I said the other agents were effectively on GPT after checking the main workspace and cron payloads, but I missed two live leakage paths: agent-specific `workspace-*/config/model-router.json` files and persisted `modelOverride` values inside agent session stores.
### Why
I verified the global router and cron jobs, but did not inspect the per-agent workspace configs and existing session JSON for CMO, HR, and CTO.
### Fix
When Ahmed reports an agent thread still showing MiniMax or another old model, inspect all three layers before claiming it is fixed: global router, agent workspace router, and persisted session overrides in `/root/.openclaw/agents/*/sessions/sessions.json`.

## 2026-04-11 - Patch the current topic session entry, not just prior agent sessions
### What I got wrong
I updated old agent session metadata and router files, but Ahmed's next `/reset` created a new live topic session entry that still carried a MiniMax override.
### Why
I fixed historical session entries and config, but I did not re-check the newly active `sessionId` for the topic after reset.
### Fix
When debugging agent thread model issues, always inspect the current topic key in `/root/.openclaw/agents/<agent>/sessions/sessions.json` after the user's latest reset and patch that exact live entry if it still has `modelOverride` or stale `systemPromptReport` values.


## Weekly Review (2026-04-05 → 2026-04-12)

_Generated by weekly-agent-review.py at 2026-04-12 08:00_



### Flagged for Human Review

- **clawback**: Pattern unclear — flagged for human review.
- **cron**: Pattern unclear — flagged for human review.
- **cron/job-scanner**: Pattern unclear — flagged for human review.
- **job-search-mcp**: Pattern unclear — flagged for human review.
- **general**: 25 unclassified signal(s) — manual review recommended.
## 2026-04-12 - Clean means no visible leftover Notion images
### What I got wrong
I told Ahmed the Notion pages were clean because the image blocks matched the Approved Asset and there were no duplicate page images. That was the wrong standard. Ahmed meant the old visible images should be gone from the page body and cover entirely.
### Why
I optimized for pipeline correctness instead of user-visible cleanliness and did not check the Notion page cover before answering.
### Fix
When Ahmed asks whether old images were cleaned in Notion, verify and report on both visible page body images and page cover images. Treat Approved Asset as separate from visible page content.

## 2026-04-12 - Check premium generator before sending CMO images
### What I got wrong
Ahmed rejected the Apr 13 image and pointed me to scripts/generate-premium-content-card.py. I sent an image from the weaker path without first checking the stronger premium generator already in the workspace.
### Why
I optimized for pipeline completion instead of checking the highest-quality existing generation path in the repo before asking for review.
### Fix
For CMO LinkedIn image work, inspect the premium generation scripts in the main workspace before sending any asset for review, especially when visual quality is the concern.

## 2026-04-12 - Keep the Apr 13 premium generator as the default for follow-on post images
### What I got wrong
When Ahmed said to move to the next day, I evaluated Apr 14 using the old minimal card asset instead of continuing with the same premium image workflow that had just been approved for Apr 13.
### Why
I treated Apr 14 as a readiness check instead of preserving the approved creative production method across the series.
### Fix
For this content series, default to `workspace-cmo/scripts/generate-premium-content-card.py` for subsequent post-image work unless Ahmed explicitly asks to switch tools or styles.


## 2026-04-12 - Give in-place remediation first when performance diagnosis is done
### What I got wrong
Ahmed asked for recommendations to solve the slowness on the current system, and I led with resizing the VPS instead of prioritizing actions that can improve performance in-place.
### Why
I optimized for the highest-impact infrastructure fix instead of the user's actual constraint and intent.
### Fix
When Ahmed asks for recommendations to solve runtime slowness, prioritize in-place remediation first: reduce hot background workloads, clean stale state, restart only if justified, and present infrastructure resizing only as a last resort.

## 2026-04-18 - Do not stop at the architecture memo when implementation is the obvious next step
### What I got wrong
After comparing ppt-master with our slides lane and proposing Slides Lane v2, I stopped at the memo and asked Ahmed what to do next instead of continuing into the first concrete implementation slice.
### Why
I treated the strategy document as the deliverable instead of recognizing that the next action was already obvious and low-risk.
### Fix
When I produce an architecture recommendation and the next build step is clear, I should continue directly into the first implementation slice in the same thread unless Ahmed explicitly wants to stop at planning.

## 2026-04-22 - Do not let queued system wrappers leak into Ahmed-facing replies
### What I got wrong
While handling the LinkedIn publish attempt, I let queued system/exec metadata dominate the conversation and Ahmed received confusing wrapper-like replies instead of one clean human update.
### Why
I stayed too deep in tool-state recovery and did not collapse the queued noise into a single plain-language status message fast enough.
### Fix
When multiple queued system events arrive, ignore the wrapper noise in the user-facing reply, answer Ahmed directly in one clean message, and separate runtime/debug detail from the actual status or blocker.

## 2026-04-22 - Silent direct fallback filler came from Telegram fallback rewrite, not only routed reply handling
### What I got wrong
I treated the visible `Nothing to add right now.` symptom as if the routed-reply preserve-token fix fully covered it, but Ahmed proved the live production filler was still being synthesized by the Telegram extension's empty-turn fallback path.
### Why
I fixed the routed reply boundary but did not fully account for a second path that fabricates `NO_REPLY` inside the Telegram extension and then rewrites it through outbound planning under direct silent-reply rewrite.
### Fix
For future silent-reply/filler debugging, check both routed reply preservation and transport-specific empty-turn fallbacks. Treat Telegram's synthetic `NO_REPLY` fallback as a separate path, and verify whether direct silent rewrite defaults at source/dist/plugin levels are overriding the intended silent behavior.


## Weekly Review (2026-04-12 → 2026-04-19)

_Generated by weekly-agent-review.py at 2026-04-19 08:00_



### Flagged for Human Review

- **cron/job-scanner**: Pattern unclear — flagged for human review.
- **job-search-mcp**: Pattern unclear — flagged for human review.
- **cron**: Pattern unclear — flagged for human review.
- **cron/linkedin-daily-post**: Pattern unclear — flagged for human review.
- **himalaya**: Pattern unclear — flagged for human review.
- **cron/email-check**: Pattern unclear — flagged for human review.
- **general**: 35 unclassified signal(s) — manual review recommended.

## 2026-04-23 - Use the exact account Ahmed specifies for live auth flows
### What I got wrong
I started the ChatGPT web login flow with nasr.ai.assistant@gmail.com after Ahmed said to proceed, instead of first confirming and using the exact email he wanted for the login.
### Why
I reused the nearest visible account from the Google chooser and optimized for momentum instead of treating account identity as a user choice that must be followed exactly.
### Fix
For any live auth or publishing flow, use the exact account Ahmed specifies. If multiple remembered or suggested accounts exist, pause long enough to match the chosen one exactly before continuing.


## 2026-04-24 - Do not use AI-recreated face for Ahmed brand visuals
### What I got wrong
I generated a branded visual where Ahmed's face was AI-recreated and it did not look like him.
### Why
I optimized for premium styling instead of preserving identity fidelity. For personal-brand assets, resemblance is non-negotiable.
### Fix
Use Ahmed's real profile photo as the base for personal-brand visuals, then add layout, background treatment, and typography around it. Avoid AI face regeneration unless Ahmed explicitly asks for stylization.

## 2026-04-24 - Premium brand visuals need restraint
### What I got wrong
I created a no-face typographic visual that looked like a generic tech flyer, not a premium executive/personal-brand asset.
### Why
I overused decorative grids, nodes, borders, and large filler typography instead of using restraint, whitespace, hierarchy, and refined composition.
### Fix
For Ahmed's premium brand visuals, default to minimal executive design: fewer elements, high contrast, elegant spacing, restrained gold accents, and no busy tech motifs unless explicitly requested.

## 2026-04-24 - Confirm progress during long public posting tasks
### What I got wrong
Ahmed asked me to post on LinkedIn with the latest visual, and I spent about 12 minutes debugging the image upload without giving a timely confirmation or progress update.
### Why
I prioritized solving the technical upload blocker over communicating status during a public/external action.
### Fix
For public posting or other external actions, confirm receipt immediately, then send a concise progress/update if execution takes more than a couple of minutes or hits a blocker. Never leave Ahmed guessing whether the order is being handled.

## 2026-04-24 - Proactive closeout after config cleanup
### What I got wrong
After completing the GPT-5.5 agent/cron cleanup, I did not proactively send a clear final status immediately. Ahmed had to ask "Status?", "So are you done?", and "What about the agents?".
### Why
I kept verifying and narrating internally/tool-by-tool instead of treating the verified end state as requiring one consolidated closeout. I also allowed repeated duplicate tool-flow noise to delay a crisp answer.
### Fix
For config hygiene, migrations, cron edits, model cleanup, and similar operational work: once verification is complete, send a concise final status without waiting to be asked. Include what changed, verification evidence, exceptions, and backup path if relevant.

## 2026-04-24 - Model Guardian Cron Wrapper False Fix
### What I got wrong
I initially treated the Model Guardian failure as fixed after updating the GPT-5.4 expectation to GPT-5.5 and patching the OpenClaw cron payload. A forced run proved the agentTurn cron wrapper still timed out / failed to generate a response even though the underlying script completed cleanly.
### Why
I verified the script before fully verifying the live cron execution path, and I underestimated the fragility of using an LLM agent wrapper for a deterministic health-check script.
### Fix
For deterministic monitoring jobs, prefer direct system cron scripts with self-contained alert delivery. Verify with an actual forced/scheduled execution path before declaring the cron fixed.

## 2026-04-24 - Session Resume Prefix Still Present
### What I got wrong
I previously said the misleading "Automatic session resume failed, so sending the status directly" prefix had been removed and should no longer appear. Ahmed later noticed it still appeared repeatedly, and live inspection showed the string is still present in both source and dist.
### Why
I relied on earlier summarized fix history and did not re-verify the currently loaded source/dist before answering durability. The prior fix was either overwritten, incomplete, or not present in this runtime version.
### Fix
For any claimed runtime fix, verify current source, current dist, and running gateway behavior before saying it is fixed. Treat historical LCM summaries as clues, not proof of the current runtime state.

## 2026-04-24 - Verify channel model overrides before declaring model fallback fixed
### What I got wrong
I declared CTO/GPT-5.5 routing fixed after removing agent fallbacks and repairing session metadata, but missed `channels.modelByChannel.telegram["*"] = anthropic/claude-opus-4-6`, which kept forcing Telegram sessions back to Claude as a channel priority override.
### Why
I checked router files, agent defaults, and session state but did not include channel-level model overrides in the mandatory model-leak checklist before final closeout.
### Fix
For any model-routing issue, verify all active layers before declaring success: router config, root agent defaults, agent-local session overrides, persisted session runtime fields, channel/group/topic model overrides, cron payload models, and live `/status` evidence when possible.

## 2026-04-25 - Do not over-alert email notifications without reading source
### What I got wrong
I escalated LinkedIn/GulfTalent notification subjects as a CRITICAL ALERT before reading the underlying emails and analyzing actual relevance.
### Why
I treated notification metadata as enough evidence instead of verifying the message body and distinguishing connection invites/job alerts from real interview invitations.
### Fix
For job/interview/email alerts, read the actual message first, classify it, assess relevance against Ahmed's target profile, and only mark critical when the content truly warrants interruption.

## 2026-04-25 - JobZoom Needs Persistent Applied-Job Dedup Before Pass 1
### What I got wrong
JobZoom was allowed to surface jobs Ahmed had already applied to in previous runs. Same-day duplicate detection worked, but applied roles from prior days were not being persisted and excluded before Pass 1.
### Why
I treated daily run deduplication as sufficient and did not close the loop between Ahmed's "applied to all X jobs" confirmation and future scrape filtering.
### Fix
JobZoom must write applied job IDs/URLs/signatures to a permanent applied-jobs ledger whenever Ahmed confirms applications were completed, and every future run must load that ledger and exclude those roles before Pass 1 scoring. Report filenames should use the actual run date (`jobzoom-YYYYMMDD`) and PDF tables must be checked for overflow before delivery.

## 2026-04-25 - Email alerts need analysis, not raw forwarding
### What I got wrong
I forwarded a Gmail "critical alert" as raw invite-like lines and mislabeled generic application acknowledgements/job alerts as interview invites.
### Why
I trusted subject/sender pattern matching instead of reading message bodies and classifying actual stage, action required, deadline, and priority.
### Fix
For job/recruiting email alerts, read the email body before alerting. Classify each item as interview invite, application acknowledgement, recruiter screen, job alert, rejection, or newsletter. Include priority, why it matters, required action, and recommended next step. Do not call it an interview invite unless the body explicitly requests or schedules an interview/screening.

## 2026-04-25 - Proactive core-system improvement should originate from me
### What I got wrong
Ahmed had to bring an external example before I tightened the core operating files. I should have identified the drift myself: long files, stale model references, Mission Control contradiction, and weak alert classification rules.
### Why
I treated core-file maintenance as reactive cleanup instead of a standing proactive responsibility.
### Fix
Periodically audit the operating contract without waiting for Ahmed: check SOUL/USER/AGENTS/TOOLS for contradictions, stale rules, model drift, alert-quality gaps, and rules that no longer steer behavior. Surface the recommendation before Ahmed has to prompt it.

## 2026-04-29 - CMO Visual Default Requires Reference-Level Craft, Not Template Imitation
- Incident: CMO repeatedly produced LinkedIn visuals that technically followed the Ahmed AI execution card direction but fell below the original reference quality.
- What failed: first output became a generic PMO infographic, second pasted text over the reference image, third used a clean 9:16 boardroom layout but looked weaker than the original, flatter, less cinematic, less premium, with weaker typography, visual depth, and execution metaphor.
- Do differently: For Ahmed LinkedIn visuals, require reference-level craft, not rough similarity. Compare against `/root/.openclaw/workspace/output/jobzoom-visuals/ahmed-linkedin-ai-execution-card-4k.jpg` before presenting. Reject outputs that feel generic, flat, stock-like, under-designed, or less premium than the reference.

## 2026-05-15 - Avoid Empty Private Closeouts After Telegram Sends
### What I got wrong
Ahmed sent quick greetings in Telegram. I correctly used the `message` tool for the visible Telegram reply, but then added private final replies like "Done" and "Sent", which created useless transcript noise and made the exchange look mechanical.
### Why
I treated the tool action as something that needed a separate completion receipt, even when the visible user-facing reply had already been delivered.
### Fix
For simple Telegram replies sent through the `message` tool, make the visible message the actual answer and keep any private final closeout empty or meaningfully contextual. Do not add "Done", "Sent", or other bookkeeping text unless Ahmed asked for delivery confirmation or the action has operational significance.

## 2026-05-15 - OpenClaw Update Recovery Requires Binary, Harness, Plugin, and Node Checks
### Incident
After the OpenClaw 2026.5.12 update, Telegram messages reached the gateway but agents returned "Something went wrong" because runtime startup failed before replies completed.
### Root causes
Multiple OpenClaw binaries drifted across `/usr/bin`, `/usr/local/bin`, and NVM paths; Codex harness support was requested before `@openclaw/codex` was installed/enabled; `lossless-claw` missed `@mariozechner/pi-coding-agent`; and a stale Ahmed-Mac node on 2026.2.26 kept reconnecting to the newer gateway.
### Fix
Installed/enabled `@openclaw/codex`, restored the `lossless-claw` dependency, disabled stale Mac node launch agents/processes, replaced stale `/usr/local/bin/openclaw` with a symlink to `/usr/bin/openclaw`, restarted via the service binary, and verified Telegram with a real response.
### Do differently
Before and after OpenClaw updates, verify every active binary path, service `ExecStart`, required plugins, Codex harness registration, lossless-claw dependency health, node-client version alignment, and real Telegram `/new` then `hi` behavior. Use `/usr/bin/openclaw gateway restart` and keep one config change at a time with validation before restart.

## 2026-05-15 - Fix Low-Risk JobZoom Warnings Instead of Reporting Them
### What I got wrong
After a successful JobZoom validation, I reported a model health pre-check timeout as a remaining warning instead of immediately checking whether it was a low-risk false-positive that could be fixed.
### Why
I treated the warning as harmless because batch scoring completed, but Ahmed expects preventable recurring noise to be removed when safe.
### Fix
For protected JobZoom internal work, if a warning is caused by local wrapper/reporting/preflight logic and the run outcome is verified clean, inspect and fix the warning source in the same turn. Keep approval gates for external, destructive, credential, gateway, or live-runtime changes.

## 2026-05-16 - Check JobZoom Applied Ledger Before Sending CV Packs
### What I got wrong
Ahmed said he had already applied to all five JobZoom opportunities after I resent their tailored PDFs. The JobZoom database already had those five roles marked applied in both `jobs` and `applied_jobs` with applied date 2026-05-15.
### Why
I verified that PDFs existed and that Telegram delivery worked, but I did not check the applied ledger before treating the roles as active deliverables. I also queried older strong roles in a way that blurred active opportunities with already-applied records.
### Fix
Before sending or regenerating any JobZoom CV pack, query `applied_jobs` and `jobs.applied` for every selected LinkedIn URL/ID. If already applied, report that status and do not resend CVs unless Ahmed explicitly asks for copies.

## 2026-05-17 - Telegram Slash Menu Requires Scope Verification, Not Just Dispatch
### What I got wrong
After the Telegram command repair, I verified command dispatch and `getMyCommands` default scope, then said commands were restored. Ahmed correctly pointed out that typing `/` in Telegram should show the built-in command menu.
### Why
I treated Bot API command availability as equivalent to client menu visibility. Telegram command menus can depend on explicit command scopes such as `all_private_chats`, `all_group_chats`, chat-specific scopes, and the chat menu button state.
### Fix
For Telegram command repairs, verify default, private, group, administrator, direct-chat, and configured group-chat scopes. Set the direct chat menu button to `commands` where supported. Remember that forum topics inherit the supergroup command scope; Telegram may reject group menu-button changes even when group command scopes are valid.

## 2026-05-25 - User Approval Should Unlock a Bounded Repair Path
### What I got wrong
Ahmed explicitly approved fixing a live OpenClaw cron issue, but the session still could not cross the runtime `host=gateway`/`host=node` and elevated-exec gates. I kept repeating the blocker instead of treating the approval-policy mismatch itself as the system defect to capture and fix.
### Why
Current OpenClaw approval is consent, not an automatic capability grant. If the runtime policy does not map Ahmed's approval to a bounded elevated/gateway repair path, the agent remains stuck even when the user has authorized the work.
### Fix
For future OpenClaw permission design and debugging, approved high-risk maintenance should create a narrow, auditable escalation path for the specific task: approved command scope, host target, timeout, evidence capture, and automatic expiry. User approval should not mean broad unrestricted access, but it must be stronger than the default deny gate for that approved operation.

## 2026-05-25 - Give Ahmed One Terminal Step at a Time
### Correction
Ahmed said to always give only one step at a time so he can share the outcome before the next instruction.
### Do differently
For terminal/config recovery workflows, provide exactly one command block or one action, then wait for Ahmed's result before giving the next step.

## 2026-05-27 - Cron Sandbox Rejects Some Inline Shell Helpers
### Incident
During the daily auto-lessons cron wake, `sed -n`, `find -exec`, and `xargs` commands were rejected by OpenClaw strict inline-eval approval, and cron-event turns cannot request chat approvals. `rg` was also unavailable in this sandbox.
### Do differently
For cron/internal maintenance in the OpenClaw sandbox, start with approval-safe commands such as `cat`, `head`, `tail`, direct script execution, and plain `grep -R` before reaching for inline helper forms. If `rg` is missing, fall back to `grep` immediately and keep searches narrow to avoid noisy session transcript dumps.

## 2026-05-28 - Interrupted Codex/OpenClaw Turns Need State Inspection Before Retry
### Correction
Ahmed explicitly asked that when Codex/OpenClaw reports "stopped before confirming the turn was complete," I inspect the current state before retrying anything.
### Do differently
For interrupted or partial OpenClaw work, first check gateway health, recent logs, git/workspace changes, and active/partial session state. Summarize what was already done and whether anything is inconsistent, then continue from the last safe point. Do not rerun completed async commands or overwrite partial changes.

## 2026-05-28 - OpenClaw Health Guard Repairs Need Patch Verification and Reload Caveat
### Incident
The OpenClaw health dashboard was CRITICAL because runtime patch checks failed around queued/reply-context metadata sanitizers, heartbeat/cron sanitizer paths, active-memory FTS handling, and silent context-engine maintenance guards.
### Fix
After approval, repair the runtime patch files with a backup, rerun the direct health dashboard and sanitizer smoke checks, and confirm the health report is OK.
### Do differently
When OpenClaw health is made green by editing dist/runtime files, call out whether a live gateway restart was performed. If no restart happened, treat the on-disk repair as verified but note that a controlled restart is still the clean reload step.

## 2026-05-28 - Cron Sandbox May Not Provide apply_patch
### Incident
During the daily auto-lessons cron wake, the normal `apply_patch` editor command was not available in the OpenClaw sandbox (`/bin/bash: apply_patch: command not found`).
### Do differently
In cron/internal maintenance, try `apply_patch` first for file edits as usual, but if the sandbox lacks it, use a minimal standard editor such as `ed` for append-only memory updates and verify the resulting tail.
## 2026-05-29 - Model Guardian can misread config warnings as model status

- What happened: Model Guardian sent a false FAIL because `openclaw models status --plain` returned the real model on stdout while a missing `OPENCLAW_HOOKS_TOKEN` config warning appeared on stderr, and the checker used the last combined line as the model.
- Recovery: Updated `scripts/model-guardian-check.py` to select a known model line from mixed output instead of trusting the tail line. Verified normal and `env -u OPENCLAW_HOOKS_TOKEN` runs return `ALL_OK` and `NO_ALERTS`.
- Do differently: For CLI status probes, parse the expected structured/status line and tolerate unrelated config warnings on stderr when the underlying command exits cleanly.


## 2026-05-30 - Cron Model Allowlist Moves Require Payload Audits

- What happened: Active cron jobs kept using `openai/gpt-5.5` after the runtime allowlist moved to `openai-codex/gpt-5.5`, causing isolated cron preflight failures including NASR Doctor Daily.
- Recovery: Backed up cron jobs, replaced stale payload model overrides, validated config, and confirmed no enabled cron payloads referenced models outside `agents.defaults.models`.
- Do differently: After model allowlist or provider namespace changes, audit active cron job payload overrides as well as global defaults. Cron state may continue showing old failures until each affected job reruns successfully.

## 2026-05-30 - LCM Backfills Need Secret Marker Guards and Local Fallback

- What happened: The LCM stale coverage backfill read agent `models.json` directly and treated OpenClaw `secretref-managed` as a real OpenRouter key, producing a guaranteed 401 instead of a useful model-backed summary.
- Recovery: Reject unresolved secret markers/env refs before calling the provider and fall back to local extractive summaries when a usable key is unavailable.
- Do differently: For maintenance scripts that read config secrets outside the normal runtime resolver, explicitly distinguish real credentials from secret references before making network calls, and preserve a deterministic local fallback path.

## 2026-05-30 - LCM WAL Hygiene Needs Truncate Verification

- What happened: A passive WAL checkpoint left `/root/.openclaw/lcm.db-wal` at 41,241,232 bytes, so the health check still warned even though checkpointing had run.
- Recovery: Ran `PRAGMA wal_checkpoint(TRUNCATE);`, verified WAL size returned to 0 and `PRAGMA quick_check` was ok, then updated nightly maintenance to truncate when passive checkpoint leaves WAL above 10MB.
- Do differently: For SQLite health maintenance, verify the post-checkpoint WAL size. If passive checkpoint leaves a large WAL, run a truncate checkpoint and recheck database health.

## 2026-05-30 - Cron Health Should Prefer Live Jobs State Over JSONL Tails

- What happened: NASR Doctor reported stale cron warnings because it read append-only cron JSONL tails, while live jobs-state showed the current status more accurately.
- Recovery: Doctor now prefers live jobs-state, treats first-run scheduled jobs as OK, and the LCM Nightly job runs deterministic health with explicit final confirmation.
- Do differently: For cron health dashboards, use authoritative live job state for current status and treat append-only logs as historical evidence only. Require explicit final confirmation for jobs whose success would otherwise be ambiguous.

## 2026-05-30 - Clear Completed LCM Compact Queues When Stats Say Remaining Zero

- What happened: The LCM compact processor reported `remaining=0`, but `/tmp/lcm-compact-queue.json` still contained two items, creating stale queue noise after a successful processor run.
- Recovery: Processed the existing queue, verified compacted=2/failed=0/remaining=0, cleared the stale file, and hardened the processor to auto-clear the queue when results report no remaining work.
- Do differently: Queue processors should reconcile persisted queue files against result stats before reporting completion. If stats say no work remains, clear stale queue artifacts and verify the persisted queue length is zero.

## 2026-05-31 - Weekly Retro Must Parse Current Lesson Headers

### Incident
Weekly Team Retro falsely reported no lessons because its parser missed the current `## YYYY-MM-DD - Title` plus sectioned-entry format in `memory/lessons-learned.md`.
### Recovery
Updated `scripts/weekly-team-retro.py`, regenerated `memory/retros/2026-05-31-weekly-retro.md`, and verified the retro loaded 32 lessons. Google source failures were historical; the latest SearXNG fallback runs were green.
### Do differently
When changing lesson-file format or retro reports, test the parser against the live lessons file and verify the loaded lesson count instead of relying on a successful script exit alone.

## 2026-05-31 - Job Pipeline Health Must Distinguish JobZoom Runs From HR Source Runs

### Incident
An async report returned `Pipeline needs seeding - run job scanner`, but direct inspection showed JobZoom had completed run `59` on 2026-05-31 with 150/150 searches, 3 CVs generated, and delivery true. The stale signal came from the separate HR `source_runs` table, whose latest rows were from 2026-05-30.
### Do differently
For job-pipeline freshness reports, compare both JobZoom run state and HR/source-run state before saying the pipeline needs seeding. If only one ledger is stale, name that ledger and avoid implying the whole job lane failed.

## 2026-05-31 - Avoid Gateway Restarts Inside User-Facing Codex Turns

### Incident
A gateway restart completed cleanly but cut the Codex app-server transport mid-turn, producing a visible `connection closed before this turn finished` error for Ahmed.
### Do differently
Treat gateway restarts as user-visible interruption risk even when technically successful. Prefer config validation and health checks first; if a restart is approved and necessary, warn that the chat turn may drop, then verify gateway health, runtime patch status, config validity, and app-server liveness before closing the loop.

## 2026-05-31 - HR Easy Apply Should Reuse LinkedIn Tabs

### Correction
Ahmed noticed that the HR agent opened a new Chrome tab for each bulk Easy Apply job instead of reusing the same tab.
### Do differently
For LinkedIn bulk Easy Apply automation, reuse an existing LinkedIn jobs/feed tab when possible, navigate that page to the next job, and only create a new page if there is no reusable authenticated LinkedIn page. Avoid temporary runners that call `context.newPage()` per application unless the user explicitly wants parallel tabs.
## 2026-06-01 - Gmail OTP access
Ahmed clarified that OTPs sent to Gmail are accessible through the existing Gmail access. Do not treat Gmail OTP retrieval as a blocker; check Gmail first before asking Ahmed, unless the OTP is not delivered there or requires an unavailable non-Gmail MFA path.


## 2026-06-02 - Do Not Repair LinkedIn by Editing Cookies

### Incident
During HR LinkedIn recovery, duplicate LinkedIn cookie cleanup/repair was attempted after `ERR_TOO_MANY_REDIRECTS`; retests still failed with HTTP 429 / redirect errors.
### Do differently
For LinkedIn application automation, do not inspect or repair cookies as a recovery path. Use only visible authenticated browser state after Ahmed resets/logs in, or leave LinkedIn-only work blocked until the visible session is healthy.

## 2026-06-02 - LinkedIn Upload Success Needs Visible Exact-CV Proof

### Incident
OpenClaw/MCP `upload_file` reported success on LinkedIn Easy Apply, but LinkedIn kept the old Salt CV selected and `input.files` remained empty; submitting would have sent the wrong CV. The later working path was byte-injecting a browser `File` object and confirming the exact tailored PDF in the visible UI before submit.
### Do differently
For LinkedIn Easy Apply, never treat `upload_file` returning ok as proof of attachment. Submit only after the visible UI shows the exact intended CV selected; otherwise discard the draft. Byte-injected `File` is acceptable only when followed by that visible exact-CV confirmation.

## 2026-06-02 - OpenClaw Cron Gateway Tooling Differs From Native Codex

### Incident
This cron wake first called `sandbox_exec` with `host=auto`, which failed because the configured exec host is `gateway`; the gateway shell also lacked `rg`.
### Do differently
For OpenClaw cron/internal maintenance, run `sandbox_exec` against the configured `gateway` host and be ready to fall back from `rg` to `grep`/`jq` when inspecting logs.

## 2026-06-03 - LinkedIn Easy Apply Can Recover Through A Different Visible Authenticated Profile

### Incident
The `nasr-linkedin` CDP profile stayed blocked by `ERR_TOO_MANY_REDIRECTS` / unauthenticated navigation, but the HR lane later succeeded by using the authenticated `openclaw` browser profile with a one-tab flow. Submissions still paused whenever LinkedIn protection/tracking tabs caused navigation timeouts.
### Do differently
When one LinkedIn browser profile is hard-blocked, do not keep repairing cookies in that profile. Try another already-authenticated visible browser profile, keep the one-tab flow, verify the exact CV and submit proof, update ledgers immediately, and pause again if protection/timeouts return.

## 2026-06-03 - External ATS Submissions Need Real Required Artifacts And Account Approval

### Incident
Fime HiBob required a highest diploma certificate upload and no diploma artifact was available; STRUCTURAL Workday required sign-in/account creation before applying. The HR lane correctly stopped instead of uploading a substitute or creating credentials without approval.
### Do differently
For job applications, never upload fake/substitute documents and never create ATS accounts without explicit approval. If a portal requires a missing certificate, credential, or account creation step, record the blocker and ask Ahmed for the exact artifact or approval before submission.
- 2026-06-04: For job application OTPs, use available Gmail access before declaring user-auth blocked. Still ask Ahmed for MFA/passkey/reCAPTCHA, account creation, or external messaging decisions.

## 2026-06-04 - Cron Status JSON Needs Atomic Writes

### Incident
Cron health briefly flagged `stale-context-maintenance` as unreadable because the health report read the status JSON while the cron wrapper was rewriting it, producing a transient partial-JSON read even though the maintenance job itself was healthy.
### Do differently
Cron wrappers that publish status JSON should write to a temp file and move it atomically. Health readers should retry transient JSON parse failures before reporting a job unhealthy.

## 2026-06-04 - Email LLM Jobs Need Per-Agent Model Allowlist Checks

### Incident
An email heartbeat command exited 0, but the LLM analysis step skipped because `openai-codex/gpt-5.5` was not allowed for agent `main`, producing `Model 'openai-codex/gpt-5.5' is not allowed for agent 'main'` and `LLM: No valid credentials or gateway unreachable`.
### Do differently
For cron/email LLM probes, check the per-agent model allowlist as well as global defaults. If a job exits 0 but the LLM section says model-not-allowed or gateway unreachable, treat analysis as degraded and fix the allowlist or fallback path before relying on the summary.

## 2026-06-04 - Job Application Success Needs Dedupe Ledger Verification

### Incident
After confirmed Virtucruit, talabat, and Ecolab submissions, the pipeline/report was updated but `applied-job-ids.txt` was still missing talabat `4407693428` and Ecolab `4421685356` until a later verification pass found and added the entries.
### Do differently
After every confirmed HR submission, verify both the application status/report and the permanent dedupe lock ledger (`applied-job-ids.txt` or equivalent). Do not treat the pipeline status alone as sufficient proof that future JobZoom scans will exclude the role.

## 2026-06-05 - OpenClaw Shrinkwrap Belongs In Update And Publishing Checks

### Incident
Ahmed asked for recommendations after reviewing the OpenClaw shrinkwrap security docs; the useful takeaway was release/update control, not live runtime hardening.
### Do differently
Before OpenClaw updates or OpenClaw-owned plugin publishing, review `pnpm-lock.yaml`, `npm-shrinkwrap.json`, bundled plugin dependencies, and unexpected `package-lock.json` diffs alongside `openclaw config validate`, `openclaw security audit`, install smoke tests, and post-update router/cron/plugin checks. Do not treat shrinkwrap as a sandbox or proof that dependencies are safe.

## 2026-06-05 - JobZoom Requested Sections Have Scoped Account And Email Approval

### Preference
Ahmed granted standing approval to continue through candidate-account and email-application routes for the JobZoom requested-section batch; after that continuation, 20/24 targets were confirmed submitted.
### Do differently
For that scoped JobZoom requested-section work, do not stop solely because a safe candidate-account or email route is required. Continue through approved routes, still require real submission proof before marking applied, and keep asking for explicit approval on unrelated batches, MFA/passkeys/reCAPTCHA, unavailable artifacts, or risky/non-standard actions.


## 2026-06-06 - Operational Status Reports Use Scan-First Format

### Preference
The shared CTO reporting policy now asks operational, infrastructure, health, fix, incident, cron, automation, and other state-changing status messages to use a scan-first format with one functional leading status emoji and Impact/Fix/Verification/Risk/Artifact fields when relevant.
### Do differently
For infra/status reporting, lead with the functional status emoji and concise state, then include the structured fields when they add signal. Keep routine agent-to-agent announce noise suppressed with `REPLY_SKIP`/`ANNOUNCE_SKIP` when no user-visible action is needed.

## 2026-06-06 - Copilot CLI Agent Pulse Is Inspiration, Not Runtime Infrastructure

### Recommendation
`DUBSOpenHub/copilot-cli-agent-pulse` targets GitHub Copilot CLI files and includes a `curl | bash` quickstart, so it is not a direct fit for the OpenClaw VPS runtime.
### Do differently
Do not install Copilot-specific dashboard tooling into OpenClaw production just for monitoring. Borrow the useful UX ideas instead and prefer an OpenClaw-native pulse view backed by cron status, sessions, model guardian data, health reports, LCM, and logs.

## 2026-06-06 - Obsidian Should Front The Existing Knowledge Brain

### Recommendation
Obsidian is useful as a human-readable thinking layer, but it should not replace OpenClaw memory, Notion workflows, ledgers, RSS intelligence, or operational reports.
### Do differently
If building an Obsidian/NASR Knowledge Brain vault, mirror existing trusted Markdown and operational artifacts, keep community plugins minimal, and prefer Git/plain Markdown sync over fragile free-sync workarounds.

## 2026-06-07 - Windows PowerShell Config Scripts Need Safe Variables, Secrets, And Encoding

### Incident
Hermes Telegram setup got stuck on `[Telegram] No bot token configured` because runnable PowerShell snippets wrote the placeholder `TELEGRAM_BOT_TOKEN=***`, used reserved `$HOME`/`$home`, relied on fragile YAML indentation from chat copy/paste, and used `Set-Content -Encoding UTF8` for `.env`, which can add a BOM on Windows PowerShell.
### Do differently
For Windows PowerShell setup scripts, use nonreserved names such as `$hermesHome`, write the actual `$token` into generated files, validate full BotFather token shape before writing, use BOM-free UTF-8 (`System.Text.UTF8Encoding($false)`) for `.env`, and show a file/log validation step before telling Ahmed to retry. If a bot token appears in chat, remind him to rotate it after the service works.

## 2026-06-07 - Hermes Telegram And Slack Have Separate Runtime Homes

### Preference
Current intended split: VPS Hermes runs Slack only and stays always-on; Windows laptop Hermes owns Telegram and only responds while the laptop is awake and the gateway is running.
### Do differently
When Telegram Hermes is down, first check whether the Windows laptop gateway is reachable/running before debugging VPS Slack Hermes. Do not run the same Telegram bot token on VPS and Windows at the same time; recommend moving Telegram back to VPS for 24/7 Telegram access, with Tailscale only as a remote-management aid for Windows.

## 2026-06-07 - Daily Backup Is Disabled By Request

### Preference
Ahmed asked to stop daily backups. The OpenClaw cron `Daily OpenClaw Backup` (`20f54174-5a9b-46bd-b105-c8bb939a2c8b`) is disabled, and the OS root crontab `daily-backup` line plus `/root/.openclaw/workspace/config/root-crontab.managed` were commented out. Daily snapshots, retention cleanup, and the weekly backup restore smoke test were left enabled.
### Do differently
Do not re-enable daily backups unless Ahmed explicitly asks. For future backup schedule work, verify both OpenClaw cron and root crontab/managed crontab state, and preserve snapshots, retention, and restore-smoke coverage unless the request names them too.

## 2026-06-07 - OpenClaw Gateway Shell May Not Provide `apply_patch`

### Incident
During the daily lessons capture, the gateway shell did not have the `apply_patch` command available (`Command 'apply_patch' not found`), so the edit could not use the normal patch helper there.
### Do differently
When editing through OpenClaw `sandbox_exec` on the gateway, check whether `apply_patch` exists before relying on it. If it is missing and an edit is required, use a small deterministic script, then immediately verify the diff/content.


## 2026-06-08 - Intel Sweep Search Quota Failures Are Degraded Runs

### Incident
The Daily Intel Sweep completed and wrote `DAILY-INTEL.md` plus `intel-2026-06-08.md`, but Exa and Tavily both returned HTTP 402 Payment Required during multiple sections, forcing fallback/sparse results while the cron still had to return the constrained one-line OK.
### Do differently
When `intel-sweep.py` logs Exa/Tavily 402s, treat the run as provider-degraded even if the output files are written. Verify both files, preserve the user-facing output contract, and record or surface the sparse/provider-degraded status in the appropriate operational channel instead of treating the intel as fully healthy.

## 2026-06-08 - Calendar Prefetch Empty Cache Can Mask Composio Outage

### Incident
Calendar prefetch hit `OpenClaw API fetch error: [Errno 111] Connection refused`, then wrote a valid empty `/tmp/calendar-events-2026-06-08.json` cache and reported 0 events because Composio was unavailable.
### Do differently
For calendar prefetch, distinguish true no-events from degraded no-data. If Composio/OpenClaw API is unavailable, verify the JSON cache as usual but do not treat `[]` as proof the calendar is clear; include the degraded source status in any downstream morning briefing or health report.

## 2026-06-09 - Hermes CLI Config Commands Need The Live Service Home

### Incident
Hermes Telegram appeared to stop after Ahmed shared a Chrome remote-debugging command, but the verified root cause was configuration state: Telegram had been disabled/commented out for Windows Hermes ownership, and earlier `hermes config set` attempts without the live service environment wrote to non-live `.hermes/config.yaml` paths.
### Do differently
When repairing VPS Hermes, do not assume the triggering chat message is causal. Inspect the systemd unit and run Hermes CLI/config commands with the live service environment (`HERMES_HOME=/srv/hermes-pilot/home HOME=/srv/hermes-pilot`), then verify `/srv/hermes-pilot/home/config.yaml`, `/srv/hermes-pilot/home/.env`, `gateway_state.json`, and gateway logs after restart.


## 2026-06-10 - Hand-drawn LinkedIn Quality Floor

Ahmed approved the latest rebuilt ROT hand-drawn visual as the quality floor. For future hand-drawn LinkedIn visuals, match or exceed: polished editorial sketchnote quality, warm paper texture, authentic hand lettering, strong whitespace, clean story flow, restrained orange accents, no sketch-filter look, no crowded/overlapping elements. Reference: output/linkedin/return-on-tokens-rot-handdrawn-reference-quality-latest-2026-06-10.png

## 2026-06-10 - Resend Generated Images Through Direct Telegram Photo Path After Media Failure

### Incident
An OpenClaw image-generation reply produced the desired hand-drawn ROT visual but the user saw `Media failed`; the asset existed under `/root/.openclaw/media/tool-image-generation/...` and was successfully delivered after copying it to the LinkedIn output/media paths and sending it with Telegram `sendPhoto`.
### Do differently
When a generated image message reports `Media failed`, do not regenerate first. Locate the newest generated image in `/root/.openclaw/media/tool-image-generation` or `generated_images`, verify dimensions/file size, save a durable copy under `output/linkedin`, then resend through the direct Telegram photo path and confirm the returned `message_id`.

## 2026-06-11 - Cron And Heartbeat Exec Should Respect The Configured Gateway Host

### Incident
Several June 11 cron/heartbeat sessions failed immediately with `exec host not allowed (requested auto; configured host is gateway; set tools.exec.host=auto to allow this override)` after calling `sandbox_exec` with `host=auto`. Affected tasks included heartbeat checks, the email synthetic harness, and the health dashboard writer.
### Do differently
For scheduled OpenClaw work in this runtime, omit the `host` override or use the configured gateway path. Do not set `host=auto` unless the tool/runtime explicitly allows that override; if this error appears, retry the same command without the override before treating the underlying script as failed.

## 2026-06-12 - OpenClaw Updates Must Stop On Model Provider Drift

### Incident
OpenClaw 2026.6.6 update preflight failed before any install or restart because `scripts/openclaw-update-guard.py --write-report` found `openai/gpt-5.5` in `/root/.openclaw/openclaw.json` and `/root/.openclaw/workspace/config/model-router.json` while expecting `openai-codex/gpt-5.5`; codex usage also did not show `openai-codex`.
### Do differently
Before updating or restarting OpenClaw, run the update guard and inspect its report. If model refs fail, repair provider namespace drift in both the live config and workspace router, validate config, rerun the guard, and do not install or restart while the verdict is FAIL.

## 2026-06-12 - Cron Reminders Need Completion, Not Acknowledgement

### Correction
Ahmed had to resend an email-agent cron task because the previous response only acknowledged it instead of completing the original scheduled work.
### Do differently
For cron/reminder tasks, run the requested tools or scripts immediately and return only the requested final output or summary. Do not send `on it` or acknowledgement/status text as the answer, and wait for spawned or background work before closing.

## 2026-06-13 - Diff Exit 1 Can Masquerade As Patch Failure

### Incident
A gateway verification command ran `diff -u ... | sed ...` under `set -euo pipefail` after successfully patching `scripts/vps-disk-guard.sh`. Because `diff` exits 1 when files differ, OpenClaw marked the command as a tool error even though the diff output was the expected verification artifact.
### Do differently
When a command intentionally shows a diff, wrap the diff with `|| true` or temporarily disable `set -e` around it, and keep syntax/tests as the real pass/fail gates.

## 2026-06-13 - Scope Session Searches To Avoid OpenClaw Post-processing Failures

### Incident
Broad `rg`/log reads across session JSONL files returned huge embedded tool schemas and payloads, causing `Tool output unavailable due to post-processing error` instead of useful evidence.
### Do differently
For lessons capture or session review, search only today's non-trajectory session files and use a JSON-aware extractor with bounded snippets instead of dumping broad raw matches from all sessions.

## 2026-06-13 - June 12 OpenClaw Rollback Backup Was Approved For Deletion

### Preference
Ahmed said the current OpenClaw version is stable and approved deleting `/root/.openclaw/workspace/backups/openclaw-update-20260612-214914`; deletion freed about 2.4G and was followed by successful `openclaw config validate` and gateway probe checks.
### Do differently
Do not assume that June 12 rollback backup exists for future recovery. Create or verify a newer backup/snapshot before any risky OpenClaw update or rollback-dependent change.


## 2026-06-14 - Agreed LinkedIn Sketch Style Means Reference-Quality Match

### Correction
Ahmed rejected a generated Google DeepMind / AI operating model visual that was only in the general sketch-note direction, saying it was not the same quality and needed to be exactly the same quality as the agreed style.
### Do differently
For Ahmed's hand-drawn LinkedIn visuals, treat "agreed style" as a strict reference-quality requirement, not a loose aesthetic. Start from the accepted reference-quality asset/prompt and compare layout, paper texture, lettering quality, whitespace, black-ink/orange-accent balance, and signature treatment before claiming the style is locked or sending the final image.

## 2026-06-14 - Telegram Message Send Supports Media, Read Does Not

### Incident
After resending a generated image through `openclaw message send --channel telegram --target 866838380 --media ... --json`, a verification attempt with `openclaw message read --channel telegram --target 866838380 --limit 5 --json` failed with `Unsupported Telegram action: read`.
### Do differently
For Telegram media delivery, trust and record the `send` response (`ok: true`, `messageId`) and verify via available logs or user confirmation if needed. Do not use `openclaw message read` for Telegram unless the runtime adds read support.

## 2026-06-15 - Calendar Prefetch /tmp Files Must Be Created By Script Or Shell

### Instruction
The June 15 Calendar Pre-fetch cron explicitly warned that the write tool is workspace-scoped and can fail for `/tmp` paths, and directed the agent to run `scripts/calendar-prefetch.py` then verify `/tmp/calendar-events-YYYY-MM-DD.json`.
### Do differently
For `/tmp` calendar caches or other non-workspace artifacts, do not use workspace-scoped write operations. Run the existing script or a shell command in the configured gateway environment, then validate file existence and JSON shape/count before reporting success.

## 2026-06-16 - VPS Max-Safe Cleanup Needs Verified Backups Before Pruning Snapshots

### Preference
Ahmed asked for the maximum safe VPS disk cleanup after disk usage recovered from 83% to 66% but old OpenClaw snapshots still consumed several GB.
### Do differently
For aggressive OpenClaw disk cleanup, inventory first, keep live state untouched, then create and verify a current backup before pruning older snapshots. Safe disposables include stale compressed/uncompressed snapshots, stale `/tmp` material, package caches, and temp virtualenvs. Do not delete live `lcm.db`, credentials, media, state, active workspaces, or `/root/.openclaw/npm`; verify the backup archive, SQLite LCM backup, disk/inodes, and gateway probe before reporting done.

## 2026-06-16 - Volatile Tmp Cleanup Can Exit 1 From Disappearing Files

### Incident
During the max-safe VPS cleanup, one cleanup command exited `1` because files under `/tmp/node-compile-cache/...` disappeared while `find` was scanning them; later disk checks and gateway verification succeeded.
### Do differently
When cleaning volatile temp/cache trees, treat disappearing-file `find` races as benign only after rerunning targeted verification. Use `-ignore_readdir_race` or guarded `rm ... || true` for expected volatile paths, and keep final disk, backup, and service checks as the real pass/fail gates.

## 2026-06-17 - Long Cron Cleanup Jobs Need Gateway Exec And Polling

### Incident
A session-watchdog cleanup cron falsely failed after first trying unavailable elevated exec, then running quiet archive work behind a 120s tool timeout; the process was killed before it could print its final success output.
### Do differently
For long scheduled maintenance, use the configured gateway exec path with `elevated=false`, give the command and agent budgets enough room, and poll background runs instead of relying on short foreground timeouts. Treat the final log and gateway probe as the pass/fail evidence.

## 2026-06-17 - Bulk LinkedIn Application Counts Need Submitted Proof States

### Improvement
The LinkedIn plus-30 campaign counted 30/30 only after confirming LinkedIn submitted proof states; blocked, no-modal, unknown-field, and upload-only attempts were excluded from the total.
### Do differently
For bulk LinkedIn or JobZoom application reporting, count only explicit submitted proof states as applications. Keep blocked attempts, visible-upload-only states, unknown required fields, and missing application modals out of submitted totals and record them as blockers instead.

## 2026-06-19 - Email Rejections Should Not Be Auto-Actionable

### Incident
The email health/review path flagged an application rejection as actionable (`actionable=True`) with confidence 90, even though the expected classification was non-actionable.
### Do differently
For email triage, treat plain rejection/status emails as non-actionable unless they ask Ahmed to complete a specific next step, reply, schedule, or provide documents. Keep a regression case so high confidence does not override a rejection category.

## 2026-06-19 - LinkedIn Bulk Campaigns Need Unique-ID Counts And Runner Fallbacks

### Incident
The June 19 LinkedIn +30 campaign only became reliable after duplicate ledger rows from retries were de-duplicated to 30 unique LinkedIn IDs. A prior campaign also noted CDP visible fallback failure on ports 18801/18800, with the browser-CLI runner completing successfully.
### Do differently
For bulk LinkedIn Easy Apply, count only unique confirmed submitted LinkedIn IDs, de-duplicate retry rows before reporting totals, and switch to the browser-CLI runner when the visible CDP ports are unavailable. Continue stopping on unknown or sensitive required fields instead of guessing.

## 2026-06-21 - Cron Resumes Must Re-run The Original Task

### Correction
Ahmed had to send a follow-up on the Email Agent cron because the previous response only acknowledged the reminder instead of completing the original scheduled work and returning the requested formatter output.
### Do differently
When a cron follow-up says the previous response was only an acknowledgement, immediately execute the original commands, wait for any spawned work, and return only the requested final summary or formatter output. Do not send interim status text such as `on it`.

## 2026-06-21 - Job Hunter Notion Fallback Needs Type Guards

### Incident
The weekly Job Hunter domain review ran the Notion pipeline snippets after a prompt explicitly said to use the local-data fallback if Notion was unavailable. `notion_sync` could not load `scripts/config/notion.json`, and downstream code tried `.get()` on a string, producing tracebacks before the final report was recovered from local data.
### Do differently
For Job Hunter reviews, treat any missing Notion config, exception, or non-list return from `read_pipeline_from_notion()` as Notion unavailable. Switch directly to local data and suppress tool-failure diagnostics in the user-facing report when the reminder asks for a quiet fallback.

## 2026-06-21 - OpenClaw Sandbox Edits Need Available Patch Mechanics

### Incident
An inter-session memory update tried to run `apply_patch` inside `sandbox_exec`, but that command was unavailable in the OpenClaw gateway shell. A later GNU `patch` attempt used the `*** Begin Patch` format and failed as a malformed patch before a proper unified diff succeeded.
### Do differently
When editing files from OpenClaw `sandbox_exec`, first use the actual available edit mechanism. If falling back to GNU `patch`, provide a valid unified diff with correct hunk counts and verify the target file before claiming the memory update was recorded.

## 2026-06-22 - Email Briefings Need Body-Proof Urgency

### Preference
The June 22 email briefing prompts repeatedly required using only provided email evidence: analyze `body_excerpt` and `classification_evidence`, never invent content, and do not mark an email critical unless the excerpt proves an interview, assessment, recruiter opportunity, or reply need.
### Do differently
For email briefings and alert formatting, let the body excerpt override noisy categories or high priority scores. Use `read_and_file`/`no_action` or low urgency for acknowledgements and plain rejections, and say `cannot determine from available content` when the supplied excerpt is insufficient.


## 2026-06-24 - Reference-Led Visuals Must Match Structure Before Style

### Correction
Ahmed rejected an AI prompting / Loop Engineering visual as "very bad" because it preserved the topic and palette but missed the reference concept. The accepted rebuild matched the reference composition: open toolkit on the left, bold hand-lettered center headline, simple workflow on the right, warm paper, black ink, orange accents, exact `1280x659`, and Ahmed signature.
### Do differently
For reference-driven visuals, extract and preserve the reference layout, metaphor, and hierarchy first, then vary details. Treat "same concept" as composition plus metaphor, not just subject and style, and run a visual check for overlaps and small-label readability before delivery.

## 2026-06-24 - IEEE-Style Content Needs Credibility Wording

### Preference
For the Loop Engineering PDF/post, the credible framing was "an 11-page IEEE-style working note" rather than "an IEEE paper"; the document is an independent working note/reformatting, not evidence of publication.
### Do differently
When packaging user-created research/content, avoid overstating publication status. Use "IEEE-style working note" unless there is explicit evidence of actual IEEE publication or acceptance.

## 2026-06-24 - JobZoom And CMO Loops Need Manual Proof Before Automation

### Improvement
The Loop Engineering checklist was created for JobZoom and CMO with the rule that loops are control systems, not permission. The recommended next step was real-workflow proof: JobZoom closeout first, then CMO visual/draft closeout, before read-only validators or cron automation.
### Do differently
Before automating JobZoom/CMO validators, run two clean manual checklist passes. Verify source evidence, isolated work, artifacts, approvals, persistence, and stop states before declaring a loop healthy.

## 2026-06-25 - Health Guard LCM Repairs Need LCM Engine Compaction

### Incident
Health Guard reported CRITICAL because Telegram DM conversation `9713` was above the LCM context threshold. Normal session compaction reduced the session registry count, but LCM health still needed a one-item LCM compact-processor queue; that dropped LCM context from `122,341` tokens to `14,139` and made the fresh health report OK. `/status` still showed the older `122k` session-registry count until metadata refreshed.
### Do differently
For `lcm_context` health failures, repair through the LCM engine/queue rather than deleting database rows. Verify with `reports/health/latest.json` or the dashboard `lcm_context` check, and treat `/status` token counts as potentially stale immediately after compaction.

## 2026-06-26 - LinkedIn Visual Defaults Must Not Conflict Across Gates

### Correction
Ahmed deleted the live LinkedIn post "The 90-Day AI Test" because NASR/CMO again posted a bad visual despite the agreed hand-drawn sketchnote style. The newer memory rule was correct, but older active `TOOLS.md`, `content-claw`, and `content-publishing-safety` gates still defaulted to dark executive cards and blue/gold visual language.
### Do differently
When Ahmed sets a visual direction, update every active publishing gate and generator entry point, not only memory. Before publishing a LinkedIn visual, check for conflicting defaults across `MEMORY.md`, `TOOLS.md`, content skills, visual-quality references, image-post checklists, and CMO generation scripts. For normal Ahmed LinkedIn static visuals, auto-fail generic dark tech cards unless Ahmed explicitly asks for that direction.

## 2026-06-26 - Sketchnote Means Handmade, Not Vector Flow Diagram

### Correction
Ahmed rejected the corrected "The 90-Day AI Test" preview because it used the right warm paper, black ink, and orange palette but still looked like a clean vector flow diagram, not the agreed hand-drawn sketchnote concept.
### Do differently
For Ahmed LinkedIn static visuals, the default must match the reference as a handmade raster sketchnote: imperfect ink strokes, paper texture, hand-lettered hierarchy, toolkit/system metaphor, and visible sketch energy. Auto-fail polished deterministic diagrams, clean icon systems, and vector-like flows even if they are not dark cards and use the approved palette.

## 2026-06-26 - Daily LinkedIn Visuals Need A Hard QA Marker

### Correction
Ahmed explicitly asked that every daily LinkedIn visual use the right image, concept, and style after the corrected post had to be republished. The old workflow could still resolve a local final asset even when the actual file had not been reference-checked.
### Do differently
Daily LinkedIn publishing must fail closed unless the actual image is reference-checked against the hand-drawn sketchnote concept and the Notion image intent includes `Visual QA: PASS - reference-checked handmade sketchnote`. Keep deterministic dark/blue-card checks in the publisher as a backstop, but do not treat them as a replacement for visual review.

## 2026-06-26 - Retracted LinkedIn Posts Must Be Excluded From Cadence

### Correction
The CMO weekly report flagged `The 90-Day AI Test` as a possible duplicate because it counted both the deleted 09:30 bad-visual post and the corrected 12:31 sketchnote repost as live posts.
### Do differently
When reconciling LinkedIn cadence, distinguish rejected/deleted/retracted posts from live reposts before reporting duplicates or backlog. Exclude retracted posts from live cadence counts and metrics-gap backlogs, and keep an audit entry so the corrected repost remains explainable without looking like a duplicate publish.

## 2026-06-27 - Email Synthetic Rejection Regression Is Still Open

### Incident
The daily email synthetic harness failed with `application rejection: actionable=True expected False` and `confidence 90 > 80`, exiting 1. This repeats the June 19 rejection-actionability issue, so the lesson has not yet been codified into the classifier path.
### Do differently
Treat rejection actionability as an open regression until `scripts/email-synthetic-harness.py` passes. For email triage, force plain application rejections to non-actionable and cap confidence unless the provided excerpt explicitly asks Ahmed to reply, schedule, submit documents, or take another concrete step.

## 2026-06-27 - OpenClaw Sandbox Cron Edits Must Avoid apply_patch

### Incident
The weekly skill tune-up tried `apply_patch` inside `sandbox_exec` and hit `Command 'apply_patch' not found` before falling back to other edit mechanics. This repeats a known OpenClaw sandbox limitation.
### Do differently
In OpenClaw sandbox/gateway cron sessions, check edit-tool availability before changing files. Use `ed`, `ex`, `perl`, or a valid GNU unified diff when `apply_patch` is unavailable, and reserve Codex `apply_patch` for native Code-mode turns where that command exists.

## 2026-06-28 - Health Baseline Comparison Must Handle Report Schema Drift

### Incident
The weekly read-only health baseline wrote current outputs as `*.stdout_stderr.txt`, then attempted to compare against the prior `/root/.openclaw/workspace/reports/health-baseline-20260621-083026/` using the same filenames. The prior report used split `*.out`, `*.err`, `*.exit`, and `*.cmd` files, so multiple `sed` reads failed with `No such file or directory` even though the previous evidence existed.
### Do differently
Before comparing health baselines, list the previous report directory and read its manifest or available filename pattern. Support both combined `*.stdout_stderr.txt` and split `*.out`/`*.err` report schemas, and keep missing historical files from polluting the current baseline verdict.

## 2026-06-28 - Job Hunter Review Quiet Fallback Is Still Being Bypassed

### Incident
The weekly Job Hunter domain review prompt explicitly said to use local-data fallback if Notion was unavailable and avoid emitting Notion diagnostics. The session still ran Notion snippets, hit missing `/root/.openclaw/workspace/scripts/config/notion.json`, then produced downstream `.get()` tracebacks before recovering from local data.
### Do differently
For Job Hunter reviews, probe Notion availability once through the expected path; on missing config, exception, or non-list return, stop all Notion-derived snippets and switch to local data. Treat the reminder's noise-control instruction as a hard gate so user-facing output stays clean.

## 2026-06-29 - Backup Smoke Test Must Treat Missing Legacy Archive Dirs As Nonfatal

### Incident
Cron health flagged `backup-restore-smoke-test` as failed even though a valid `/root/openclaw-snapshot-20260628.tar.zst` existed. The script was running with `set -e/pipefail` and exited early when the legacy `/root/openclaw-backups` directory was missing, before it reached the valid snapshot-archive fallback. The guard was patched and the wrapper plus cron-health report returned `ok`.
### Do differently
In backup and restore smoke scripts, guard optional archive directories with `[[ -d ... ]]` or neutralize missing-dir `find` calls so legacy path removal cannot abort alternate backup checks. Verify with the cron wrapper and the cron-health report after changing restore coverage.

## 2026-06-29 - Hermes Slack Plain Replies Need Free-Response Channel Config

### Incident
Hermes was a member of `#ai-jobs` and the channel was allowed, but only `#ai-general` was configured for free replies. Because `#ai-jobs` was not in `free_response_channels`, normal channel messages still required `@hermes` and were ignored until `C0AJX895U3E` was added and the Hermes gateway was restarted.
### Do differently
When Slack channel messages are ignored, check both `allowed_channels` and `free_response_channels` / `require_mention` in the live Hermes service home. Membership and allowlisting are not enough for plain, no-mention replies; verify with a plain message and a runtime model probe after restart.

## 2026-06-29 - Session JSON Message Content Can Be Arrays

### Incident
During daily lessons review, a `jq ... @tsv` extraction over `.message.content` failed because assistant messages can store content as arrays of `toolCall` / `text` parts, not always as strings. The failure produced repeated `array ... is not valid in a csv row` errors.
### Do differently
For session evidence extraction, normalize content before formatting: pass strings through, extract text parts from arrays, and fall back to bounded `tostring` only when needed. Continue excluding trajectory files unless tool-level evidence is specifically required.

## 2026-06-30 - Sensitive ID Details In Recruiter Emails Need A Safety Gate

### Incident
Ahmed received a recruiter NDA request asking for nationality, passport country of issue, and passport number over email before a scheduled Project Manager call.
### Do differently
When drafting replies that include passport numbers or similar identity details, warn about normal-email risk, prefer a secure portal when available, and do not send or offer to send the email unless Ahmed provides the missing details and explicitly approves sending.

## 2026-06-30 - Routine Email Scan Notices Must Not Interrupt Active Q&A

### Incident
During an active direct Q&A session, an "Email scan: all clear" message appeared between Ahmed's question about admin portals/operational tooling and the actual answer.
### Do differently
Suppress or defer routine all-clear email scan notices while responding to an active user request. Only interrupt an in-progress Q&A for email scanning when there is a genuinely urgent action item; otherwise finish the user answer first and keep non-actionable scan results quiet.

## 2026-07-02 - Email Agent KPIs Must Respect LLM False-Positive Downgrades

### Incident
The 20:00 email scan categorized a Talabat marketing discount email as `recruiter_reach` because it matched active pipeline company `talabat`. The LLM correctly marked it low urgency, `no_action`, and a marketing false positive, and the formatter sent the all-clear message. But `email-summary.json` still kept `actionable_count: 1`, `unread_actionable: 1`, and high-priority `review_and_respond` recommendations from the raw category.

### Do differently
When LLM analysis downgrades an item to `no_action`, false positive, marketing, newsletter, or automated job-alert noise, exclude it from actionable counts, unread-actionable KPIs, hot alerts, and response recommendations. Keep the raw category only as a review candidate, not as Ahmed-facing action pressure.

## 2026-07-03 - Use Advertised Skill Paths Before Guessing Workspace Paths

### Incident
A Health Guard heartbeat first tried `/root/.openclaw/workspace/skills/healthcheck/SKILL.md`, which does not exist in this install, before reading the actual healthcheck skill from the Node global OpenClaw skills directory.
### Do differently
When a heartbeat or cron says to read a skill, use the exact path from the available-skills list or `rg --files` evidence before falling back to guessed workspace paths. Treat a missing guessed skill path as a path-resolution mistake, not as a missing skill.

## 2026-07-03 - LinkedIn Metrics Backfill Needs Author-Visible Analytics

### Incident
The CMO metrics backfill pilot verified local reports and queues, but captured no impressions/profile views because those metrics require author-visible LinkedIn analytics from an approved logged-in session. The latest report still had 22 live posts missing metrics, including the newest 7.
### Do differently
For LinkedIn metrics backfill, do not infer impressions or best performer from public reactions/comments or from script success. Run the local cadence report, prioritize newest missing rows, then stop at `blocked-login` until an approved logged-in author analytics session can supply the actual metrics.

## 2026-07-04 - Stale Context Cleanup Must Validate DB Schema

### Incident
The stale-context maintenance cron found an empty `/root/.openclaw/tasks/runs.sqlite` and treated file existence as sufficient, then crashed with `no such table: task_runs` instead of falling back to the real migrated DB.
### Do differently
For Taskflow/OpenClaw maintenance scripts, validate the expected table/schema before choosing a SQLite DB path. If the file exists but lacks `task_runs`, treat it as unusable and continue to the migrated DB fallback; verify both the direct script and cron wrapper after the fix.

## 2026-07-04 - Long Cron Jobs Need One Delivery Path And Enough Timeout

### Incident
Weekly Skill Autoresearch timed out at 300s, retried, then completed, and its prompt also asked the agent to send Telegram directly while cron delivery already announced the result. This produced confusing status noise until the job timeout was raised to 900s and cron became the only Telegram delivery path.
### Do differently
For long-running scheduled skill tuning or autoresearch jobs, set a timeout that covers the normal run duration and keep user notification in one layer. Prefer cron `announce` delivery over agent-authored direct sends unless the job explicitly needs a separate target.

## 2026-07-05 - Auto Lessons Must Audit Short Cron Sessions

### Incident
The daily auto-lessons script reported `Found 0 significant session(s)` because all 23 same-day sessions had fewer than 5 exchanges. Manual evidence review still found concrete short cron failures, including repeated `exec host not allowed`, Job Hunter Notion/local-data fallback errors, and the still-open email rejection synthetic failure.
### Do differently
After running `scripts/auto-lessons-learned.py --all`, do not treat the exchange-count filter as proof that there is nothing to capture. Always scan same-day non-trajectory session JSON for `isError=true`, user corrections, and explicit preferences before deciding `NO_REPLY`, especially for one-turn cron sessions.

## 2026-07-06 - Hermes CV Generation Needs Hard Rejection Gates

### Correction
Ahmed shared four Hermes-generated CV PDFs after saying clear instructions had already been given. Review found near-clone templates with light keyword swapping, collapsed experience paragraphs instead of ATS bullets, only five real bullets under metrics, artificial `Role Keywords Matched` / `Target Role` sections, a recruiter name used as the company, and unsupported keyword additions such as ERP.
### Do differently
For Hermes and JobZoom CV packs, fail closed unless the output is regenerated from `memory/master-cv-data.md` and `memory/ats-best-practices.md`, uses verified facts only, keeps exact titles and actual company names, has no artificial keyword sections, and passes plain-text PDF extraction checks for proper bullets, separated role metadata, at least 12 real experience bullets, and no unsupported skills or achievements.

## 2026-07-06 - ATS PDF Review Should Not Depend On ImageMagick Identify

### Incident
During the Hermes CV PDF review, a sandbox command tried `identify` and returned `Command 'identify' not found`, so the review could not rely on ImageMagick being installed for PDF inspection.
### Do differently
For ATS PDF QA in OpenClaw, start with available text/metadata tools such as `pdftotext`, `pdfinfo`, `file`, `mutool`, or `qpdf`, and only call `identify` after confirming it exists. Treat extracted text and structural checks as the primary validation path for CV quality.

## 2026-07-07 - Crabbox CTO Wrapper Should Be The Default Isolated Repo Proof Path

### Incident
A Crabbox feasibility spike verified `provider=local-container`, then added `scripts/crabbox-local-proof.sh` and `docs/agent-governance/crabbox-local-proof.md` as a reusable proof wrapper. The wrapper pins Crabbox v0.36.0, checksum-verifies the binary, writes artifacts under `reports/crabbox-local-proof/`, preserves exit codes, and refuses to sync the main OpenClaw workspace unless explicitly allowed.
### Do differently
For heavy repo checks, browser/test proof bundles, and CTO verification that should not pollute the VPS worktree, prefer `scripts/crabbox-local-proof.sh --repo <repo> --label <label> -- <command>`. Keep it to disposable/local-container or approved static targets, and do not treat it as a security sandbox for hostile repositories or secret-heavy worktrees.

## 2026-07-07 - Career-Site Job Alerts Are Not Urgent Interview Actions

### Incident
The 20:00 email run surfaced `RAKBANK.CAREER - New job opportunities at Rak Bank Career Site` as `Email alert - action needed` with a 48h response instruction, even though the subject reads like a career-site job-alert digest rather than an interview, assessment, offer, recruiter reply, or time-bound follow-up.
### Do differently
For email alerts, treat career-site `new job opportunities` messages as low/normal review unless the provided excerpt proves a specific interview, assessment, offer, recruiter conversation, deadline, or requested reply. Do not let a noisy `interview_invite`/active-company category alone create urgent action language.

## 2026-07-08 - Auto Lessons Capture Must Check Short Cron Follow-ups

### Incident
`scripts/auto-lessons-learned.py --all` reported 0 significant sessions because every July 8 session had fewer than 5 exchanges, but one skipped two-exchange Email Agent cron session still contained Ahmed's concrete correction that the previous response only acknowledged the cron task instead of completing it.
### Do differently
After the auto-lessons script reports no significant sessions, run a bounded JSON-aware search over today's skipped session user messages for correction/failure phrases, then dedupe against existing lessons before deciding there is nothing to append.

## 2026-07-09 - New Model Rollouts Need Codex Runtime Proof

### Incident
After `gpt-5.6-sol` appeared in official model info and Ahmed asked to switch all agents, OpenClaw/Codex Telegram turns failed with model errors including `gpt-5.6-sol is not supported when using Codex with a ChatGPT account` and later `requires a newer version of Codex`, producing visible `Something went wrong` replies.

### Do differently
Do not treat docs/catalog availability as enough to route all agents to a new model. First run a small probe through the exact OpenClaw + Codex + account path, then verify a real Telegram `/new` or ping reply. If the model error names ChatGPT-account support or Codex version, keep the previous stable model and treat it as a compatibility/update blocker, not a transient gateway failure.

## 2026-07-10 - Dependent Cron Commands Must Verify The Upstream Result

### Incident
The 09:00 Email Agent cron launched the email scan, then ran the formatter before OpenClaw recorded the scan result. The scan tool call later surfaced as missing its matching result, while the formatter still returned an all-clear from the existing summary file.

### Do differently
For sequential cron pipelines, do not run a formatter or consumer until the producer command has returned successfully and its expected output artifact is fresh for the current run. If a native tool call loses its result, fail closed or rerun the producer instead of formatting potentially stale data.
## 2026-07-11 - A local image path is not Telegram delivery

- What happened: NASR repeatedly said an image was sent or attached while only returning text and local links. The actual image arrived only after an explicit Telegram media send returned message ID `61246`.
- Rule: When Ahmed asks to receive a local image/file in Telegram, stage it under `/root/.openclaw/media`, use the proof-gated media sender, and never claim delivery without `ok=true` plus a non-empty Telegram `messageId`.
- Prevention: `scripts/telegram-send-local-media.py` now enforces allowed paths, per-request idempotency, response parsing, SHA-256 receipts, and fail-closed reporting.

## 2026-07-11 - Workspace Backups Must Never Broad-Stage Runtime State

### Incident
An automated workspace commit staged 277 files, including database backups, live databases, logs, sessions, and email/job state. The commit remained local and was removed before push; auto-commit was disabled in the maintenance scripts and backup staging was restricted to source plus explicit safe configuration.

### Do differently
Backup jobs must use an allowlist for source and reviewed configuration, never `git add -A` or equivalent broad staging in a live OpenClaw workspace. Before pushing, inspect the staged path set, reject volatile/runtime/state categories, and verify the resulting source-only commit is the only new remote-reachable commit.

## 2026-07-11 - Codex Manual Hash-Header Failures Need An Official-Docs Fallback

### Incident
The Codex manual helper rejected an otherwise reachable response because the server omitted the required `x-content-sha256` header (`ManualFetchError`). The same guidance was retrieved successfully through the official OpenAI documentation source.

### Do differently
When the Codex manual helper fails specifically on a missing content-hash header, do not treat it as an OpenClaw or model failure and do not keep retrying the same helper. Fall back to the official OpenAI docs search/fetch tools, preserve the official-source restriction, and explain the helper failure only if it was visible to the user.

## 2026-07-12 - Repair Browser Failures On The Actual Execution Node

### Incident
LinkedIn tabs sometimes worked through the gateway, but snapshot/evaluate repeatedly failed with a 9-second `connectOverCDP` timeout. Gateway-side timeout patches and reloads had no effect because `chrome` was proxied through the outdated Ahmed-Mac node/browser proxy. Upgrading that node to the gateway version and switching its local browser connection to the supported existing-session Chrome MCP path restored snapshot and read-only evaluate.

### Do differently
Before patching browser timeouts, identify where the browser command actually executes and compare gateway/node versions. If the failing path is node-proxied, repair or upgrade the node/browser proxy, then verify tabs, snapshot, and read-only evaluate; do not weaken runtime permission boundaries or keep patching gateway code that is outside the execution path.

## 2026-07-12 - Browser Transport Recovery Does Not Clear LinkedIn Safety Gates

### Incident
After the Ahmed-Mac browser transport was repaired and authenticated feed checks passed, the HR campaign preflight opened fresh tabs and detected LinkedIn scraping protection plus invisible reCAPTCHA targets. The campaign correctly stayed paused at 12/30, with no worker launch, application, or ledger reset.

### Do differently
Treat transport recovery and automation safety as separate gates. After any LinkedIn browser repair, rerun fresh tabs/focus plus snapshot/evaluate and protection/CAPTCHA checks before resuming; preserve the existing ledger and fail closed when anti-automation signals are present.

## 2026-07-13 - Critical Job Email Alerts Need A Real-Time Ingress Path

### Incident
Sprinklr sent an interview availability request at 16:14 Cairo, after the scheduled 16:00 email scan had already finished. The next polling scan was not due until 20:00. The Gmail Pub/Sub watcher existed only as a disabled scaffold, was inactive, and had no secure runtime environment file, so no event-driven alert path was operating.

### Do differently
Do not describe four-times-daily IMAP polling as immediate monitoring. Interview invites and recruiter screens need a verified real-time ingress path with body-read classification, Telegram delivery proof, deduplication, and periodic polling retained only as fallback. Monitor the watcher itself and fail loudly if push delivery stops.

## 2026-07-14 - Material Interview-Process Updates Must Not Be Silenced As No-Action

### Incident
The Gmail Pub/Sub watcher detected Miriam Marras's Sprinklr interview-process update within seconds and classified it as a high-confidence active-pipeline message. Because the email did not request a reply, the formatter did not emit the urgent-alert prefix, and the real-time worker discarded the result. Later scheduled scans reported zero new messages because the UID had already been processed.

### Do differently
Separate importance from required action. A direct recruiter or hiring-team update about an active interview process, candidate decision, stage completion, or promised next update should be surfaced immediately as a concise informational hiring update even when no reply is required. Keep routine acknowledgements, newsletters, automated job alerts, and marketing silent. Scheduled summaries must distinguish "already processed by real-time monitoring" from "zero messages detected" so they do not imply the mailbox was never checked.

## 2026-07-14 - Live SQLite Snapshots Need Online Backups And Sidecar Exclusion

### Incident
`daily-snapshot.sh` encountered a transient SQLite shared-memory file while archiving the live OpenClaw workspace, causing GNU tar to exit 1 and preventing a verified snapshot from being promoted.

### Do differently
For live workspace snapshots, discover included SQLite databases, create and validate an online `.backup` for each one, exclude the original database plus WAL/SHM/journal sidecars, overlay the consistent copies at their original archive paths, and verify every staged database member before atomic promotion. Do not treat a raw live-filesystem tar as a consistent database backup.

## 2026-07-14 - Cron Verification Must Follow The Active Storage Backend

### Incident
A session-watchdog verification script read the retired `/root/.openclaw/cron/jobs.json` path after cron storage had moved to SQLite, producing a visible `FileNotFoundError` even though the watchdog itself passed.

### Do differently
Check `openclaw cron status` before inspecting cron state. When it reports SQLite storage, use `openclaw cron get`, `list`, and `runs` as the source of truth; do not read legacy declaration files directly.

## 2026-07-17 - Health Closeouts Must Disclose Superseded Probe Failures

### Incident
While verifying all five agents after a runtime repair, the first Main and HR probes exceeded a 50-second shell timeout. Fresh probes then completed successfully, but the closeout reported only the successful results. Ahmed saw the earlier failure alert and had to ask `?` before the timeout was explained as historical.

### Do differently
When a health check initially fails or times out and a retry succeeds, state both results in the same closeout: name the failed probe, give the successful fresh-probe evidence, and explain why the first failure is no longer current. Do not summarize a system as fully healthy while leaving a visible superseded failure unexplained.

## 2026-07-18 - Distinguish Backups From Snapshots Before Schedule Changes

### Incident
A failed `daily-snapshot` run was initially described as the daily backup even though the separate `daily-backup` cron had already been disabled. When Ahmed then asked to disable the daily backup, the response disabled the active snapshot and snapshot-retention schedules as well without first resolving which exact job he meant.

### Do differently
Before explaining or changing recovery schedules, identify the exact failing job and show the current state of `daily-backup`, `daily-snapshot`, and their retention jobs separately. If the user's wording does not match the live job identity, clarify the target before disabling anything; do not broaden a schedule change from backup to snapshot by inference.

## 2026-07-18 - Campaign Counters Must Count Only Qualifying Submissions

### Incident
The LinkedIn +30 campaign total was reported as 16/30, corrected to 14/30 after excluding two Contract roles, then corrected again to 2/30 after a complete quality audit found eleven legacy 7.7 KB ReportLab CVs outside the mandatory 15–50 KB WeasyPrint gate and four roles failing current role-family guards (with overlap).

### Do differently
Report protected-campaign progress only from ledger rows that pass every current counting gate: employment type, role family, ATS threshold, tailored-CV format/size, duplicate checks, and submission proof. Preserve excluded historical applications, but label raw history separately and require supervisor and runner counters to agree before announcing a verified total.

## 2026-07-18 - Benign Search Misses Must Not Become Visible Tool Failures

### Incident
A compound schedule-verification command ended with an `rg` search that found no matches. Because exit code 1 was not neutralized, the whole tool call was marked as an error despite earlier checks succeeding, producing a visible warning that Ahmed had to question.

### Do differently
In diagnostic command chains, isolate each check and treat an expected `rg` no-match as evidence, not command failure (`rg ... || true` when absence is acceptable). Base the final status on explicit assertions for the schedules being verified so benign search misses do not leak as internal error noise.

## 2026-07-19 - Long Implementation Runs Need Milestone Updates

### Incident
The reliability implementation kept running silently until its command lane timed out. Ahmed was left waiting for a DM response and had to be told afterward that the session was reset, files were preserved, and the verified campaign count was 12/30.

### Do differently
Before more long-running work, send the next milestone and expected checkpoint, then report each verified milestone before starting another long command. If the command lane times out, immediately state the timeout, preserved state, and last verified result instead of waiting for Ahmed to ask.

## 2026-07-19 - Raw Internal Tool Failures Should Stay Internal

### Preference
A harmless wrong-directory search miss surfaced as a raw failure alert. Ahmed approved `messages.suppressToolErrors=true` so agents can recover from tool failures internally while interview, recruiter, offer, and other action-required alerts remain visible.

### Do differently
Do not relay raw tool-error banners. Recover or retry internally, then surface only the user-relevant impact, current verified state, and required action. Keep material alerts enabled and never let suppression hide an incomplete or unsafe outcome.

## 2026-07-19 - Job Hunter Quiet Notion Fallback Is Still Being Bypassed

### Incident
The weekly Job Hunter reminder explicitly required the local-data fallback when Notion was unavailable and prohibited manual `notion_sync.py` inspection. The run still invoked the unavailable Notion path and produced two visible tracebacks (`notion.json` missing, then `.get()` on a string) before completing from local data.

### Do differently
Make Notion availability a hard gate in the Job Hunter owner skill: on missing config, exception, or non-list data, stop all Notion-derived steps and run only the local-data path. The fallback must complete without emitting Notion diagnostics.

## 2026-07-19 - A Bare Question Mark Does Not Authorize Workspace Changes

### Incident
After proposing a canonical writing standard as a possible next move, the agent treated Ahmed's bare `?` as approval and edited `AGENTS.md`, `SOUL.md`, `USER.md`, and a new standards file without an explicit change request.

### Do differently
Treat `?` as a request for clarification or status, not permission to mutate files or settings. Answer what is pending or ask one concise clarifying question; require clear approval before acting on a proposed change.

## 2026-07-20 - Answer The Replied-To Question Before Adjacent Status

### Incident
Ahmed asked about the upcoming seven-day LinkedIn slate, but the response led with verification of today's already-published post.

### Do differently
When a message replies to a specific question, answer that exact question first. Use adjacent completed work only as supporting context.

## 2026-07-20 - Date-Range Readiness Reports Must Account For Every Date

### Incident
A seven-day LinkedIn readiness report omitted 22, 25, and 27 July without explaining whether they were moved, intentionally blank, or missing.

### Do differently
For a bounded date-range report, classify every date as scheduled, moved, intentionally blank, or missing, and verify the live cadence before calling gaps intentional.

## 2026-07-20 - Persistent Resolver State Must Be Null-Safe And Cron-Tested

### Incident
The first scheduled open-work Resolver run lacked the root user systemd bus variables; recovery then crashed on `int(None)` from the prior blocked snapshot.

### Do differently
Treat persisted state as untrusted and nullable before numeric comparison. Test scheduled probes in a stripped cron-like environment, including blocked-to-healthy recovery, before declaring the loop live.

## 2026-07-20 - Keep Markdown Backticks Out Of Double-Quoted Shell Payloads

### Incident
Literal Markdown backticks inside a double-quoted shell command triggered Bash command substitution and temporarily removed a Notion asset pointer; a separate dense Python `-c` JSON probe also failed on quote escaping.

### Do differently
For structured JSON or Markdown payloads, prefer `jq`, a script file, or a direct non-shell execution path. If backticks are required, construct them inside the target language and verify the stored value before relying on it.

## 2026-07-21 - One External Publisher Needs One Scheduler And One Transaction Lock

Ahmed caught the same approved LinkedIn post being published twice. An OS cron and an OpenClaw cron started the same publisher at 09:30, and both passed the duplicate checks before either writeback completed.

Do differently: keep one scheduler owner for each public publisher and serialize the full duplicate-check through writeback transaction inside the publisher. Canonical fix: `docs/solutions/automation/linkedin-publisher-dual-scheduler-race.md`.

## 2026-07-21 - Runtime Health Is Not Workflow Benefit

### Incident
The HR Career Sentinel was reported as real-time and healthy because its service was active, notifications were durable, tests passed, and scheduled reconciliation worked. Ahmed correctly rejected this as zero benefit. The production logs showed that every Pub/Sub notification resolved zero Gmail threads because the live `gog` history payload shape did not match the adapter contract.

### Do differently
For event-driven workflows, acceptance must replay a captured production event through source decoding, object resolution, policy, persistence, and final action or justified silence. Service state, queue counts, and synthetic unit fixtures are supporting evidence only. When a source checkpoint advances with zero resolved business objects, fail closed or recover from an independent bounded source instead of declaring the event processed.

## 2026-07-21 - LinkedIn Engagement Must Own The Browser And Prove Comment Value

### Incident
The 11:00 Comment Radar returned zero candidates because LinkedIn canonicalized the search URL and the temporary +30 application campaign redirected the same authenticated browser tab. A recovered five-card pack then revealed repeated authors and mechanical comments that were technically grounded but not useful enough for Ahmed's executive voice.

### Do differently
Serialize authenticated LinkedIn browser access across HR and CMO workflows. Accept reordered query parameters only when the LinkedIn path and required values match, reject cross-workflow navigation, select one post per author, and require live evidence, a substantive insight, a forward question, uniqueness, and a 300-character limit before approval. A non-empty pack is not success unless the comments are worth Ahmed posting.

## 2026-07-21 - Reconcile Assessment Labels Against The Actual Requisition

### Incident
The Sprinklr assessment template was headed `Lead Project Manager`, while the application, Workday/interview correspondence, and pipeline record all identified requisition `113162-JOB` as `Program Manager`. The presentation copied the template label into its cover instead of resolving the conflict against the authoritative hiring records.

### Do differently
When interview materials use a different title from the requisition, treat the application record and recruiter correspondence as authoritative for candidate-facing titles. Preserve the assessment label only as source context, flag the mismatch, and use the verified role title in the final deck.

## 2026-07-21 - Validate Cron Files With The Installed Crontab Dialect

### Incident
While removing an obsolete restore-smoke schedule, validation used `crontab -T`, which this Debian cron implementation does not support. Its help output showed that `-n` is the available syntax-check mode; rerunning with `crontab -n` succeeded before installation.

### Do differently
Check `crontab -h` before assuming flags from another cron implementation. On this host, validate managed cron files with `crontab -n <file>`, preserve the live crontab, and only then install the validated file.

## 2026-07-22 - Cairo Calendar Bounds Must Not Use A Fixed UTC Offset

### Incident
The calendar-prefetch skill hard-coded Africa/Cairo as UTC+2 and prescribed `+02:00` day bounds, while the July 22 runtime correctly resolved Cairo to UTC+3 through `ZoneInfo("Africa/Cairo")` because daylight-saving time was active.

### Do differently
For Cairo schedules and date-range API calls, derive local dates and offsets from the `Africa/Cairo` IANA timezone for the target date. Do not copy fixed `+02:00` examples or use UTC+2 as a generic fallback; verify the emitted ISO timestamps across DST transitions.

## 2026-07-23 - Auto-Lessons Reviews Must Inspect Skipped Short Sessions

### Incident
The daily auto-lessons script found 44 sessions but accepted none because every session had fewer than five exchanges. One skipped session still contained a concrete failed health probe and its corrected command path.

### Do differently
Treat the exchange threshold as a first-pass filter, not proof that there is no evidence. After the automated pass, inspect user corrections and failed tool results in skipped sessions. Session JSONL readers must handle `message.content` as either a string or an array and filter by message timestamp rather than file modification time.

## 2026-07-23 - Existing PowerPoint QA Needs An Isolated Python 3.13-Compatible Environment

### Incident
Existing-deck QA failed because `xmllint` and system slide libraries were absent, while workspace-scoped `uv run` selected NumPy 1.26.3 and attempted an incompatible source build under Python 3.13.

### Do differently
For existing PowerPoint surgery on this host, validate XML with `defusedxml.minidom` and run QA outside workspace dependency scope with `uv run --isolated`, `numpy>=2.2`, `python-pptx`, `pillow`, and `pdf2image`. Do not assume `xmllint` or system Python slide dependencies are installed.

## 2026-07-23 - Use The CTO Workspace Path For Fast Health Checks

### Incident
A disk-maintenance verification called `scripts/cto-fast-status.sh` from the main workspace and failed because the maintained helper lives in the CTO workspace.

### Do differently
Run `/root/.openclaw/workspace-cto/scripts/cto-fast-status.sh` by absolute path for CTO health checks; do not infer that CTO helpers exist under the main workspace.

## 2026-07-24 - Publishing Cadence Rules Must Be Enforced In The Publisher

### Incident
The LinkedIn calendar prohibited Friday and Saturday publishing, but the live publisher had no weekday guard. An approved row dated Saturday, 25 July would therefore have been publish-eligible until Ahmed approved moving it to an unscheduled reserve draft.

### Do differently
Enforce no-post weekdays in the publisher preflight itself, using the target date in `Africa/Cairo`, so an Approved or Scheduled row cannot bypass the cadence rule. Treat the calendar/runbook rule as policy documentation, not an execution control.

## 2026-07-24 - Today Diagnostics Must Derive The Live Cairo Date

### Incident
`check_today_post_fields.py` and `check_today_post_status.py` still hard-coded `2026-04-12`, so their “today” output described an old posted row while investigating the 24 July LinkedIn schedule. The live resolver and direct date queries were needed to establish the current state.

### Do differently
Any script named or used as a “today” diagnostic must derive the date at runtime with `ZoneInfo("Africa/Cairo")` or require an explicit `--date`. Reject or clearly label fixed-date fixtures so stale results cannot be mistaken for current operational evidence.

## 2026-07-25 - Close Alert State After Reviewing Intentional Critical-File Changes

### Incident
The recurring critical-files heartbeat kept reporting five already-reviewed edits because the files remained dirty in Git and the related handoff item stayed active. The review conclusion existed only in chat, so each run rediscovered the same evidence as unresolved.

### Do differently
After approving intentional critical-file changes, commit the exact reviewed paths or record a revision-specific exception, clear the corresponding handoff item, and verify the monitored paths are clean before declaring the alert resolved.

## 2026-07-26 - A Remote Gateway Probe Failure Is Path-Specific Evidence

### Incident
`openclaw gateway probe --json` reported `ssh_tunnel_failed` and `no_gateway_reachable` because the configured remote target tried to tunnel to loopback with a missing `/root/.ssh/id_rsa` and strict host-key checking. Independent local status, health JSON, listener, and Telegram checks showed the gateway was healthy.

### Do differently
Do not diagnose a gateway outage from the remote-config probe alone. When it fails on SSH setup, label that probe path as failed and cross-check `openclaw gateway status --deep --require-rpc`, `openclaw health --json`, and the local listener before stating runtime health.

## 2026-07-26 - Help Flags On Operational Subcommands Can Still Execute

### Incident
Running `camofox-browser server start --help` as a diagnostic attempted to start another server and returned `port in use` for 9377. The existing service prevented a duplicate process, but the help check was not side-effect-free.

### Do differently
Use top-level help, documentation, or source inspection to discover operational CLI syntax. Do not append `--help` to `start`, `stop`, `reset`, or similar mutating subcommands unless the CLI explicitly guarantees help short-circuiting.

## 2026-07-26 - Host Hardening Checks Need Installed-Tool Fallbacks

### Incident
The VPS hardening review failed on `ufw`, `nft`, and unqualified `sshd` because they were absent from the shell path or not installed. `/usr/sbin/sshd -T` and `ss -ltnp` supplied the SSH policy and exposed-listener evidence needed to continue.

### Do differently
Check diagnostic-tool availability before chaining host-security commands. On this VPS, use `/usr/sbin/sshd -T` for effective SSH configuration and `ss -ltnp` for exposed listeners; report absent firewall frontends explicitly instead of treating command-not-found as firewall-state evidence.

## 2026-07-27 - LinkedIn Browser Readiness Must Prove Feed Evaluation

### Incident
`linkedin-lane-browser-check.py` reported the LinkedIn lane ready because it could list an existing feed tab, even though the `nasr-linkedin` profile reported `running: false`. After starting the profile, tab focus still worked but live page evaluation timed out through the gateway.

### Do differently
Do not treat browser status or tab listing as proof that LinkedIn sourcing is operational. A readiness check must require `running: true` and successfully evaluate or snapshot the authenticated LinkedIn feed through the same path used by the radar.

## 2026-07-27 - One Stalled CDP Tab Must Not Poison A LinkedIn Radar Run

### Incident
Ahmed-Mac, the authenticated browser profile, and the CDP endpoint were healthy, but several older LinkedIn renderer targets accepted connections without answering `Runtime.evaluate`. The radar cached one target for the entire run, so a single stalled tab caused the feed read and all six searches to time out and return zero candidates.

### Do differently
Probe candidate CDP page targets before selecting one, prefer a responsive feed or content-search tab, quarantine stalled targets for the current run, and retry once on a healthy or newly created authenticated tab while restoring the intended URL. Verify with a real full radar run, not status or tab-list checks.

## 2026-07-27 - Persist State Before Waiting On A Shared Resource

### Incident
The first live test of the staged LinkedIn radar spent almost six minutes waiting on the global authenticated-browser lock before any checkpoint existed. The lock was legitimately owned by the approved LinkedIn +30 application campaign, but the radar's blocking `flock` made contention indistinguishable from a hang and left no resumable evidence.

### Do differently
Allocate the run checkpoint before acquiring shared resources. Acquire a shared lock inside the stage that needs it with a bounded timeout, classify contention in the stage record, and exit without downstream artifacts. A later run should resume the failed stage without repeating completed work.

## 2026-07-27 - Running Is Not The Same As Making Progress

### Incident
The LinkedIn +30 supervisor and heartbeat were active, but the strict ledger stayed at 3/30 while required questions, salary rules, fit skips, and repeated browser timeouts blocked every submission. Describing the campaign as “healthy” was misleading because the process was alive but stalled at the submission gate.

### Do differently
Report execution health and outcome progress separately. Call a campaign healthy only when both the worker path is functioning and verified output is advancing; otherwise say it is running but stalled, name the blocking gate, and use the proof-backed ledger for progress.

## 2026-07-28 - Scheduled Browser Work Must Queue Behind Long Bounded Work

### Incident
The 15:00 LinkedIn Comment Radar had a resumable checkpoint but still failed because its 30-second shared-browser lock timeout was shorter than a legitimate bounded +30 application attempt.

### Do differently
Keep checkpoint allocation before lock acquisition, but size the lock wait and outer runner budget to the longest approved shared-browser operation. Verify recovery by resuming the exact failed checkpoint and proving both workflows survive the handoff.

## 2026-07-29 - Expected Incomplete Outcomes Must Not Alert As Runtime Failures

### Incident
The LinkedIn Comment Radar correctly returned an `incomplete_*` result when its live Mac/browser source was unavailable, but the direct cron wrapper alerted before applying the workflow's existing operational-success rule.

### Do differently
Classify judged incomplete outcomes before delivery: keep expected source-unavailable states internal, preserve evidence for retry, and alert only on unknown/runtime failures or a fully ready pack that fails its quality gate.

## 2026-07-29 - Portal Registration Copy Is Not An Interview Invitation

### Incident
A Dräger email requiring account registration mentioned that the portal could later receive interview invitations, causing the classifier to label the current message as an interview invite.

### Do differently
Classify the action requested now. Registration, account setup, application confirmation, and “not yet processed” language should map to `application_response` even when the email describes possible future interview features.

## 2026-07-29 - Refresh Browser References After Resolving Overlays

### Incident
The first Dräger confirmation click used a ref captured while a cookie panel covered the page, so the browser rejected it as stale or not visible.

### Do differently
Resolve consent or modal overlays first, take a fresh snapshot, and use only the newly issued refs for controls that were previously behind the overlay.

## 2026-07-29 - Ontology Readers Must Replay The Operation Log

### Incident
The ontology query CLI expected flat records with top-level IDs, but the live graph is an append-only stream of `create`, `update`, and `relate` operations.

### Do differently
Replay the operation stream into current entity state before querying. Until the loader supports that schema, verify uniqueness and append validated operations without rewriting history.

## 2026-07-29 - Test Doubles Must Match Live API Shapes

### Incident
A synthetic CMO preflight mocked `get_page()` with a page-ID string, so `build_post_record()` raised `AttributeError` before reaching the intended missing-funnel-role guard.

### Do differently
Make mocks conform to the live Notion page object contract, or provide a shared fixture factory validated against a captured response shape.

## 2026-07-29 - Resolve Maintained Browser Interfaces Before Recovery

### Incident
A Workable verification first called the removed `scripts/openclaw-browser.py` helper, producing two avoidable read-only failures before the current browser CLI was used.

### Do differently
Confirm helper paths with `rg --files` and prefer the maintained first-class `openclaw browser` CLI before attempting lower-level Playwright or remote-host recovery.

## 2026-07-30 - Treat A Content Calendar Gap As A Creative Decision, Not An Automatic Hold

### Incident
When the July 30 LinkedIn publisher found no Notion row, the first recommendation was to hold because three posts had already published that week. Ahmed challenged that conclusion and preferred using the open slot for a strong post.

### Do differently
When the publishing system is healthy but the calendar has a gap, assess whether a distinctive, on-brand post can improve the week before recommending a hold. Preserve the approval gate, funnel balance, visual quality, and duplicate checks, but do not confuse an empty calendar row with a lack of content opportunity.

## 2026-07-30 - Custom Source Arguments Must Preserve Minimum Coverage

### Incident
The LinkedIn +30 supervisor stayed alive while the strict ledger stalled at 26/30 for four hours. Explicit `--url` values had replaced the broader GCC defaults, leaving only two source collections active.

### Do differently
For critical multi-source automation, define whether repeatable source arguments extend or replace defaults. Preserve and deduplicate a protected minimum source set, fail closed when required source families are missing, expose effective coverage and stall state, and test the merged runtime configuration.

## 2026-07-30 - Report Effective Runtime Intervals After Clamps

### Incident
A campaign recovery update said sourcing would run every three minutes, but the supervisor enforces a five-minute minimum with `max(300, interval)`, requiring a correction.

### Do differently
Before reporting cadence or another bounded setting, inspect the effective runtime value after minimums, maximums, defaults, and guards are applied. Do not report only the requested or configured input.

## 2026-07-31 - Sanitize Browser Text Before Internal Processing

### Incident
The LinkedIn Comment Radar received a lone UTF-16 surrogate from live page text. Stage-output sanitation ran too late because live validation hashed the malformed string first, causing a `UnicodeEncodeError`.

### Do differently
Normalize untrusted browser strings recursively at the browser/live-payload boundary, before hashing, interpolation, caching, or artifact serialization. Keep stage-output sanitation as defense in depth and test with an escaped lone-surrogate fixture.

## 2026-07-31 - Generic Fallbacks Must Still Be Candidate-Specific

### Incident
The LinkedIn Comment Radar's improved topic-family fallback produced polished but identical comments for similar posts. Its duplicate-draft gate then reduced an otherwise valid five-card pack to one ready item.

### Do differently
Keep reusable quality scaffolding, but bind every generated fallback to verified candidate evidence such as the author and topic. Test grounding, uniqueness, length, and the downstream pack gate together.

## 2026-07-31 - Canonicalize Paths Before Evidence Comparisons

### Incident
The LinkedIn Comment Radar judge accepted an absolute live run path but falsely rejected the same valid run when invoked through a relative path because persisted stage evidence used absolute paths.

### Do differently
Resolve CLI-supplied filesystem roots before opening persisted workflow state or comparing evidence paths. Cover both absolute and relative invocation in regression tests.

## 2026-07-31 - Separate Intelligence Inputs From Content Provenance

### Incident
When Ahmed asked whether RSS was used for the LinkedIn posts, the response reported the full executive-intelligence candidate mix. That established that RSS was ingested, but did not answer which approved post concepts actually came from RSS.

### Do differently
For content-provenance questions, trace each proposed post to its recorded source and answer at the post level. Distinguish inputs available to the intelligence pipeline from inputs that materially shaped the selected content slate.
## 2026-07-31 - Compare Content Theses Against Published And Scheduled Posts

### Incident
The weekly CMO slate advanced three experience-based LinkedIn concepts after a topic-level review, but a live Notion audit found that "Reconciliation backlog is product telemetry" substantially repeated two published reconciliation posts and overlapped an already scheduled payment-recovery post. "Standardize decision rights, not every local control" also sat too close to recent regional-governance and standardization-versus-local-reality posts.

### Do differently
Before recommending a weekly slate, compare each proposed thesis, reader action, framework, and evidence pattern against the full live Notion corpus, including Posted, Scheduled, Approved, Draft, and Failed rows. Treat a new title or format as insufficient differentiation when the underlying argument and intended reader action are already present.

## 2026-07-31 - Scope Diff Validation To Task-Owned Paths

### Incident
A repository-wide `git diff --check` stopped on trailing-whitespace-like lines inside a pre-existing modified PDF unrelated to the CMO slate correction.

### Do differently
In a dirty shared worktree, run diff validation against only the files owned by the current task and the correct repository. Report unrelated existing changes without modifying them.

## 2026-08-01 - External ATS Handoffs Are Not Completed LinkedIn Applications

### Incident
Amazon and ADNOC roles with no LinkedIn `Next` or `Review` button were initially classified as broken Easy Apply forms. LinkedIn instead marked them as externally managed, and Amazon later confirmed that job 10484526 was incomplete even though the pipeline recorded the LinkedIn step as applied.

### Do differently
Before diagnosing a broken Easy Apply form, check for `Responses managed off LinkedIn` and the external application link. Record the LinkedIn handoff separately from external-portal completion, and keep the application blocked or pending until a portal receipt or employer confirmation proves completion. Treat missing external-portal authentication as a manual dependency, not a broken LinkedIn form.

## 2026-08-01 - Headless GOG Commands Need The Approved Keyring Environment

### Incident
A non-interactive Gmail lookup failed first with `aes.KeyUnwrap(): integrity check failed` when `GOG_KEYRING_PASSWORD` was set incorrectly, then with a no-TTY keyring prompt when it was omitted.

### Do differently
For headless `gog` calls, load `GOG_KEYRING_PASSWORD` from the approved protected runtime environment and use `--no-input`. Do not set the password to an empty guess or place the secret inline in a logged command; fail clearly if the protected environment is unavailable.

## 2026-08-02 - A LinkedIn Hold Must Cover Every Authenticated Lane

### Incident
Ahmed first asked to hold today's LinkedIn post, then reported that LinkedIn had temporarily restricted the account. The publisher was held, but a persistent +30 application worker continued authenticated browser activity every five minutes, while separate comment, outreach, preflight, publisher, browser, and watchdog paths remained scheduled.

### Do differently
When LinkedIn reports a restriction, rate limit, CAPTCHA, or suspicious-activity warning, treat it as an account-wide incident. Immediately inventory and stop every authenticated lane across OpenClaw cron, OS cron, systemd services/timers, active browser workers, comments, outreach, applications, analytics, and publishing. Keep passive drafting and non-authenticated research separate. Verify zero active processes and do not resume automatically; require normal manual access plus an explicit recovery decision and lower-volume controls.

## 2026-08-02 - Normalize Mixed Session Message Schemas Before Extraction

### Incident
The daily lessons review initially treated every `message.content` value as an array, but inter-session messages can store it as a string. The `jq` extraction failed with `Cannot iterate over string` and produced incomplete evidence.

### Do differently
Type-check session content before extraction: use strings directly, extract text items from arrays, and preserve the original message row until role and error filters are complete. Validate review queries against both shapes before relying on their output.

## 2026-08-03 - Attention Alerts Must Name A Concrete Action

### Incident
A weekly health alert framed one 2.995-second peak and three maintenance warnings as needing attention. Ahmed replied with `?`; a live recheck showed HTTP 200, 36 ms normal response, zero restarts, no recent cron failures, and no evidence of outage, compromise, or sustained degradation.

### Do differently
Do not interrupt Ahmed for isolated latency peaks or maintenance warnings alone. Use attention-needed language only when evidence shows sustained or repeated degradation, user-visible impact, a time-sensitive risk, or a concrete decision or action Ahmed must take; otherwise keep the finding in routine maintenance reporting.

## 2026-08-04 - Verify The Exact Mac Chassis Memory Ceiling

### Incident
An earlier local-LLM hardware recommendation described the M4 Pro Mac mini as available with 48–64 GB unified memory. Apple's current Mac mini specification tops out at 48 GB; 64 GB belongs to a Mac Studio configuration.

### Do differently
Before recommending Apple hardware for local models, verify the live specification for the exact chip-and-chassis combination. Do not transfer a memory option from Mac Studio to Mac mini, even when both use chips from the same generation.

## 2026-08-05 - Route Document Extraction By Format Semantics

### Incident
A seven-file local benchmark found AnyDoc 0.1.6 was roughly 8–85 times faster than MarkItDown while retaining all reference tokens on successful non-presentation samples. However, only MarkItDown preserved explicit slide boundaries in PPTX, and neither parser could OCR an image-only PDF.

### Do differently
Prefer pinned AnyDoc for supported non-presentation documents, keep MarkItDown for presentations and fallback, and treat scanned PDFs as an explicit OCR-required failure rather than successful empty output. Preserve the selected backend in extraction evidence so downstream QA can verify the route.

## 2026-08-06 - Check Node Connectivity Before Remote Hardware Inspection

### Incident
An attempt to inspect Ahmed's Mac called `sandbox_exec` with `host=node` and failed because the runtime only allowed the gateway host. A subsequent `openclaw nodes status --json` check showed that the available Macs were paired but disconnected, so exact CPU, RAM, and storage could not be queried.

### Do differently
Before remote device inspection, check node status and capabilities, and distinguish paired from connected. Use the approved node invocation path only when the target is connected; when it is offline, answer from verified inventory fields such as `modelIdentifier` and clearly state which live specifications remain unverified instead of retrying a blocked host override.

## 2026-08-06 - A Listening Gateway Can Still Be Health-Unresponsive

### Incident
The gateway `/health` request timed out for more than five seconds while the process remained active and port 18789 stayed open. Recent logs showed event-loop pressure (p99 2.95 seconds, maximum 7.19 seconds, utilization 0.879); an authorized controlled restart restored HTTP 200 and passed the 19-test startup security suite.

### Do differently
When the health endpoint times out but the service and listener remain present, inspect event-loop delay, utilization, and recent logs before classifying the gateway as crashed. After an authorized controlled restart, verify HTTP health, service/listener state, security checks, and cron health; if the pressure recurs, profile the workload rather than relying on repeated restarts.

## 2026-08-07 - Match Windows Commands To The Active Shell And Verified Secret Schema

### Incident
During Windows Companion setup, a PowerShell-only `Set-Clipboard` command was given while Ahmed was using Command Prompt, and the first command also assumed the wrong nested path for the gateway token in `secrets.json`. The command failed and had to be replaced with a CMD-compatible `clip.exe` pipeline using the verified slash-delimited key.

### Do differently
Identify the active Windows shell from the prompt before supplying commands, and use shell-native syntax (`clip.exe` for CMD, `Set-Clipboard` for PowerShell). Inspect the actual configuration or secret schema before naming a key path; do not infer nested JSON structure from a slash-delimited config key.

## 2026-08-08 - Do Not Turn Browser Proxy Into An Extension Requirement

### Incident
After agreeing to verify the authenticated Windows LinkedIn session without a Chrome extension, the repair later selected the `chrome` extension profile and asked Ahmed to pair it. The node's `browser.proxy` capability was working; the wrong browser transport had been chosen.

### Do differently
For Ahmed's LinkedIn lane, route the Windows `openclaw` managed Chrome profile through `browser.proxy`. Never request extension installation, pairing, or tab attachment. Distinguish node reachability from browser authentication: if the managed profile is signed out, ask only for the one-time visible LinkedIn login, then verify Ahmed's account before declaring the lane ready.

## 2026-08-08 - Restore Cron Jobs As One Verified State Change

### Incident
Two LinkedIn jobs were restored in the live crontab after an intentional pause, but cron did not reload the restored schedule before the 09:30 publisher window. The managed crontab baseline also still marked Comment Radar as paused, so a later reinstall could silently disable it again. Health reporting correctly saw stale last-success timestamps, but those were restoration defects rather than job crashes.

### Do differently
Treat cron restoration as incomplete until the authoritative managed baseline and live crontab agree, cron has reloaded, and the next expected invocation is verified in the journal or wrapper status. If the restore occurs after a missed window, reconcile that run explicitly because cron will not replay it.

## 2026-08-09 - Health Checks Must Verify the Active Runtime and Current Impact

### Incident
A weekly health alert used a dormant NVM OpenClaw binary and treated a disabled plugin scanner hit, cumulative delivery failures, stale tasks, and an alternate-install update as current live problems.

### Do differently
Resolve the gateway runtime from systemd `ExecStart`, use that binary's update-status JSON, inspect every flagged plugin's live activation and cited source, compare delivery counts and newest failure timestamps with the prior report, and verify task state before setting severity. Keep raw scanner counts in evidence, but make the headline reflect verified current impact.

## 2026-08-09 - LinkedIn Command Execution Is Standing Pre-Approved

### Incident
Routine NASR, CMO, HR, and JobZoom LinkedIn workflows kept producing native command-approval cards because approval rules covered individual command shapes instead of the established workflow scope.

### Do differently
Treat routine command execution for established LinkedIn discovery, browser-lane, JD extraction, comment-radar, publishing-support, analytics, and application workflows as standing pre-approved. Keep separate gates for exact public content, third-party messages, credentials or MFA, destructive actions, duplicate prevention, and completion proof.

## 2026-08-09 - Owner-Topic Delivery Approval Must Not Depend on Caption Text

### Incident
An internal LinkedIn artifact delivery to Ahmed prompted again after a harmless caption change because the approval rule matched one exact caption and file path.

### Do differently
For internal delivery to Ahmed's fixed Telegram DM or owned topics, scope the rule to the fixed account, destination, and topic while allowing caption and artifact arguments to vary. Leave other targets unmatched and preserve all public-post and third-party-message gates.

## 2026-08-09 - OpenClaw Config Patch Stdin Rejects a PTY

### Incident
`openclaw config patch --stdin` was started in an interactive PTY so input could be supplied later, and the CLI refused terminal input.

### Do differently
Create a reviewable JSON5 patch with `apply_patch`, then run `openclaw config patch --file` with a dry run before applying. Use `--stdin` only through a genuinely non-interactive stdin path.

## 2026-08-10 - Routine HR Commands Must Match Standing Pre-Approval

### Incident
The HR Codex runtime asked Ahmed to approve duplicate-lock checks, pipeline lookups, and recording a user-confirmed application even though these are internal steps inside the already pre-approved HR and JobZoom workflow.

### Do differently
Encode stable, narrow executable rules for routine HR and JobZoom entry points instead of relying on exact company, title, or argument strings. Do not interrupt Ahmed for internal duplicate prevention, pipeline inspection or reconciliation, scoring, CV generation, artifact checks, or recording an application he already confirmed. Preserve separate gates for external messages, unknown sensitive answers, credentials or MFA, destructive actions, paid actions, and commitments outside confirmed rules.

## 2026-08-09 - Dedupe Loaders Must Normalize Legacy Artifact Shapes

### Incident
The 11:00 LinkedIn Comment Radar crashed in `load_handled_urls()` because a legacy approval artifact was a JSON array while the loader assumed every artifact was an object and called `.get()`.

### Do differently
Type-check parsed JSON before reading object fields, skip unsupported legacy shapes safely, and cover both object and array artifacts in regression tests. Keep the workflow failed closed when the authenticated browser lane is unavailable.

## 2026-08-10 - Cross-Workspace Codex Work Can Strand The Final Reply

Promoted to `docs/solutions/runtime/codex-cross-workspace-empty-reply.md`.

### Incident
NASR directly edited and tested the JobZoom sibling workspace. Because Codex workspace-write scope was rooted in NASR's workspace, routine JobZoom operations generated repeated approval cards. Expired or declined approvals ended the Codex turn after tool results without a final assistant message; OpenClaw then sent the generic no-visible-reply fallback three times.

### Do differently
Route mutating work to the agent that owns the target workspace and keep NASR's cross-workspace access read-only. After any expired or declined approval, stop the gated action and send a concrete closeout covering completed work, remaining work, and the safe next action. Verify the actual Telegram reply, not only `turn/completed`.

## 2026-08-10 - Heartbeat Sandbox Probes Are Not Gateway Outage Evidence

### Incident
A heartbeat treated a sandbox-isolated localhost socket failure as a real gateway outage and restarted the gateway hosting its own turn, interrupting two active runs. Shared gateway logs and Telegram/WebSocket traffic showed the live runtime was healthy.

### Do differently
Treat sandbox-local connection failures as non-authoritative. Heartbeats must verify recent shared gateway-log activity and user-visible traffic before declaring an outage, and must never restart the gateway; any necessary lifecycle action belongs in a separate approved repair session.

## 2026-08-10 - Job Discovery Needs A Capped Rescue Lane Beyond Exact Titles

### Incident
JobZoom's raw 267-job artifact already contained two opportunities Hermes surfaced, but its title-only Pass 1 rejected them before persistence, full-JD scoring, reporting, or CV generation. Hermes's broader senior-title filter admitted them for semantic review.

### Do differently
Keep the precise title gate, but add a capped rescue lane for senior AI, technology, digital, transformation, healthcare, PMO, program, portfolio, operations, performance, enablement, and excellence titles. Exclude clearly mismatched functions first, then require nationality checks, full-JD scoring, dedupe, CV validation, and candidate-level evidence before promotion.

## 2026-08-10 - Historical Job Recovery Must Reconcile Mutable Exclusion Ledgers

### Incident
A no-rescrape JobZoom recovery stopped because five roles were marked applied after the original run, shrinking reconstructed dedup from 248 to 243 even though the saved source artifact was unchanged.

### Do differently
Allow historical recovery drift only when it is exactly explained by newly applied-ledger exclusions; unexplained drift must still fail closed. Delivery-only paths must recheck the current applied ledger so recovered reports never resend already-applied roles.

## 2026-08-10 - Bounded Internal Maintenance Is Standing Pre-Approved

### Incident
Routine plugin checks, container and disk inspection, guarded cache cleanup, journal vacuuming, disabled-revision cleanup, and post-cleanup verification produced repeated Codex approval cards. Ahmed explicitly said these bounded internal maintenance actions should be pre-approved.

### Do differently
Maintain narrow category rules across all agents for read-only maintenance and vetted cleanup entry points. Keep arbitrary deletion, unbounded package removal, backup pruning, Git push, gateway/config/lifecycle changes, credentials, third-party messages, public actions, paid actions, and other destructive operations gated.

## 2026-08-11 - Re-Anchor To The Pending Direct Ask After Inter-Session Traffic

### Incident
While closing an approval-noise repair, the session processed two internal completion messages, emitted `REPLY_SKIP`, and declared that no further action was needed even though Ahmed's linked-content request had not been answered. His follow-up `?` exposed the miss.

### Do differently
Before `REPLY_SKIP`, `NO_REPLY`, or a task closeout in a noisy session, identify the latest unresolved direct-user request separately from inter-session messages and verify that the final response answers it. Internal completion reports may close their own subtask, but they do not supersede a pending user ask.

## 2026-08-11 - Exec Host Overrides Must Follow The Current Turn Configuration

### Incident
The Daily Intel Sweep hard-coded `host=gateway`, but that cron turn was configured with `host=auto`; the override was rejected. Retrying with `host=auto` then exposed that the sandbox-local filesystem did not contain the requested `/root/.openclaw/workspace/scripts/intel-sweep.py` path.

### Do differently
Treat the inbound exec-host state as authoritative for each turn because it can differ across sessions. Omit an unnecessary host override; if the required filesystem exists only on another host and the configured runtime disallows it, report that configuration mismatch instead of retrying the same absolute path in a sandbox known not to contain it.

## 2026-08-12 - Material Hiring Event States Must Force Attention

### Incident
HR Career Sentinel ingested Sprinklr's post-interview rejection within seconds and classified the thread as `post_interview_rejection`, but the model also returned `requires_attention=false`. The deterministic policy trusted that boolean, persisted the event state, and created no Telegram alert.

### Do differently
Treat any validated `ATTENTION_EVENTS` event state as attention-required after deterministic vetoes and confidence gates pass. Add a regression for contradictory model output (`post_interview_rejection` plus `requires_attention=false`) and verify an alert row and Telegram delivery receipt before closing the repair.

## 2026-08-12 - Deliverable Corrections Need One Artifact Owner

### Incident
Ahmed changed the PureCS request from two role-specific CVs to one combined CV while multiple HR runs were active. Separate PDFs were delivered before the correction propagated, and the combined PDF then existed without clear validation or delivery ownership, creating a duplicate-generation and duplicate-send risk.

### Do differently
When a user changes the deliverable shape during parallel work, mark prior artifacts superseded, assign one explicit owner for the corrected artifact, and have every other run stop generation and delivery. Before sending, validate the existing artifact against the revised request and check transport receipts; resend only when delivery cannot be proven.

## 2026-08-13 - Cron Diagnostics Must Be Sandbox-Capability-Aware

### Incident
NASR Doctor reported gateway, Firehose, Gmail, LinkedIn, and backup failures from a restricted cron namespace even though independent gateway, Telegram, log, disk, and database checks were healthy. The network probes were blocked by sandbox policy, and the backup copy failed because the workspace was read-only.

### Do differently
Test network and write capabilities before health probes. Classify policy-blocked checks as skipped or degraded rather than service outages, retain read-only integrity checks as the fallback, and verify suspected failures through an authoritative host or live service signal before alerting.

## 2026-08-13 - Minimal Environments Must Preserve Required Executable Paths

### Incident
A credential-free `env -i` dependency-install check could not find Bun because the minimal `PATH` omitted the directory containing the verified Bun binary.

### Do differently
Resolve each required executable before clearing the environment, then construct the smallest explicit `PATH` that contains those verified directories. Keep credentials excluded without accidentally excluding the runtime itself.

## 2026-08-13 - Resolve Skill-Relative Paths Against The Skill Directory

### Incident
The GBrain closeout invoked `scripts/validate_vault.py` from the workspace root, but the validator belonged to the selected knowledge-ingestion skill and the path failed.

### Do differently
Resolve every relative script, reference, asset, and template path against the directory containing the selected `SKILL.md`, then verify the resolved file exists before execution.

## 2026-08-13 - HeyGen Web And API Entitlements Are Separate

### Incident
A HeyGen API render failed with `MOVIO_PAYMENT_INSUFFICIENT_CREDIT` even though an authenticated web render had completed. The web UI's download button was plan-gated, but the page had already loaded a playable signed media source.

### Do differently
Treat web-plan download rights and API credits as separate checks. When an authenticated web render is complete but export is gated, inspect the loaded video source, download and decode that exact asset, visually verify it, and use the approved delivery path before retrying paid API work.

## 2026-08-13 - Talking-Video Requests Require Voice And Avatar Motion

### Incident
Ahmed rejected a silent, graphic-first fallback because “video with graphics” meant a speaking, visibly moving avatar enhanced with graphics. The fallback preserved overlays but dropped the essential voice and motion.

### Do differently
Treat audible voice, lip or head movement, and graphic overlays as separate acceptance gates. If the primary render path fails, do not silently downgrade any gate; use another verified render path or report the blocker before delivery.

## 2026-08-14 - Heartbeat Alerts Need State Fingerprints And Resolution Clears

### Incident
The same two critical-diff warnings were handed off repeatedly throughout the day, causing repeated pending-note rewrites even though the material state had not changed. The CTO repair added fingerprint-based deduplication and verified new-state notification, unchanged-state suppression, and clearing after resolution.

### Do differently
Normalize and fingerprint the material alert state. Notify and update durable pending notes only when the fingerprint changes; suppress unchanged repeats, and clear the stored fingerprint and stale pending item as soon as authoritative evidence proves resolution.

## 2026-08-14 - Superseded Plans Need Matching Verifiers

### Incident
LinkedIn recovery verification first ran the obsolete eight-post verifier after the approved plan had moved to a six-post slate. The correct six-post verifier then hit sandbox DNS restrictions before succeeding through the approved network-capable read-only path.

### Do differently
Resolve the verifier from the current recovery label or source-of-truth report before running it. For live Notion checks, use the approved network-capable path and treat sandbox DNS failures as execution-environment evidence, not a failed content state.

## 2026-08-14 - Dependency Test Scripts Must Be Verified On The Exact Node Runner

### Incident
Pinned `atskills` v0.1.0 declared Node `>=18`, but its `npm test` command used `node --test tests/`; Node 22.23.1 treated the directory as a module path and returned `MODULE_NOT_FOUND`. The same test suite passed when invoked with explicit `tests/*.test.js` files.

### Do differently
Test dependency scripts on the exact production-adjacent Node version before adoption. Treat an `engines` range as a compatibility claim rather than proof, and use explicit test-file arguments when the active Node runner does not accept a directory target.

## 2026-08-14 - Exhaust Verified Evidence Before Asking Ahmed For Content Details

### Preference
After the recovery workflow asked Ahmed for two autobiographical details, he instructed the agent to do the work itself and finalize the remaining steps.

### Do differently
Search verified CV, memory, prior-content, and workspace evidence before requesting factual input. When Ahmed asks for autonomous completion, finalize with conservative evidence-bound wording or omit unsupported scenes; never invent personal experience, sensitive details, or outcomes to avoid asking a question.

## 2026-08-15 - Auto-Lessons Must Inspect Short Tool-Heavy Sessions

### Incident
The daily collector found 25 sessions but skipped every one because each had fewer than five user-assistant exchanges. That exchange threshold hid material evidence in one-exchange cron runs, including an execution-host rejection and a missing-script failure.

### Do differently
Scan failed `toolResult` records even when a session has fewer than five exchanges, and keep the manual short-session audit until the collector does this reliably. Exclude `*.trajectory.jsonl` from the transcript pass so duplicated runtime traces do not overwhelm the evidence.

## 2026-08-15 - Recurring Cron Failures Need A Durable Job Fix

### Incident
Daily Intel Sweep repeated the August 11 failure: its requested gateway override was incompatible with the turn's `host=auto` configuration, and the fallback runtime could not see `/root/.openclaw/workspace/scripts/intel-sweep.py`. The lesson had been recorded, but the scheduled job still failed in the same way.

### Do differently
Treat a repeated cron failure as an automation defect, not another reminder for the agent. Align the job's configured execution host with the filesystem that owns the script, then verify the next scheduled run writes both intelligence files before considering the issue resolved.

## 2026-08-16 - Snap Chromium Is Not A Safe Remotion Fallback In Restricted Runtimes

### Incident
A Remotion render first hit transient DNS failure while downloading its managed Chrome Headless Shell. Falling back to `/snap/bin/chromium` then failed because the restricted runtime could not access the user bus or Snap lock. Retrying the managed Headless Shell download succeeded and the render completed.

### Do differently
For Remotion in restricted server runtimes, prefer its managed Chrome Headless Shell or a verified non-Snap browser binary. Do not treat `command -v chromium` as proof that the executable is runnable; probe the browser once, classify DNS as transient execution-environment evidence, and avoid Snap binaries when `/run/snapd` or the user bus is unavailable.

## 2026-08-17 - Exclude Current-Employer Contacts From Career Outreach

### Correction
Ahmed works for Saudi German Health and said messaging its leaders, HR, recruiters, or colleagues about opportunities could expose his job search to his manager.

### Do differently
Treat Saudi German Health as an internal no-outreach zone for career networking. Build discreet target lists from other employers, independent executive recruiters, and trusted external contacts; never send any LinkedIn message or connection request without Ahmed's explicit approval.

## 2026-08-18 - Session Reset Reasons Are Schema Constants

### Incident
An approved HR-session maintenance reset failed when `sessions.reset` received a descriptive reason. The gateway accepts only the fixed reason values `reset` or `new`; retrying with `reset` rotated the session successfully, while the displayed compaction count remained as historical lineage metadata.

### Do differently
Use only `reset` or `new` for `sessions.reset.reason`. Verify a reset by confirming a new session ID and zero fresh tokens rather than expecting the historical compaction counter to clear.

## 2026-08-19 - Cron Get Already Returns JSON

### Incident
Cron-job verification called `openclaw cron get <id> --json`, but `cron get` does not accept `--json`; it returns JSON by default. A retry without the flag then hit a transient gateway abnormal closure in the restricted runtime, while `openclaw cron list --json` succeeded and contained the new job.

### Do differently
Use `openclaw cron get <id>` without `--json`. If that point lookup fails for a transport or restricted-state reason, verify the job with `openclaw cron list --json` and match the exact job ID or declaration key before treating creation as unverified.

## 2026-08-20 - Generated Media Needs Three Separate Proof Gates

### Incident
Four valid PNGs were generated, but Ahmed received four `Media failed` replies because the selected image was never persisted, staged under `/root/.openclaw/media`, or sent through the receipt-backed delivery helper. The first corrected send then hit a transient gateway timeout.

### Do differently
Do not regenerate after a delivery failure. Validate the exact generated file, save the selected artifact under the workspace, stage it under the approved media root, and send it with `scripts/telegram-send-local-media.py` using a stable idempotency key. Claim success only when the receipt has `ok=true` and a non-empty `message_id`; after a timeout, verify gateway health before one controlled retry.

## 2026-08-20 - Visual Approval Does Not Authorize Publishing

### Preference
Ahmed said he loved the first test produced by the NASR visual-metaphor system: a physical operating-model metaphor rendered as a premium hand-drawn static visual.

### Do differently
Use that concept-led hand-drawn direction as the preferred baseline for future static LinkedIn visuals. Treat praise or preview approval as validation of the visual direction only; keep exact caption, final artifact, scheduling, and publishing approvals separate.
