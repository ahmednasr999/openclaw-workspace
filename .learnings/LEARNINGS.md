# Learnings Log

## [LRN-20260426-003] correction

**Logged**: 2026-04-26T18:05:31+03:00
**Priority**: high
**Status**: pending
**Area**: workflow

### Summary
CMO read-only script inspection should also be pre-approved, not just HR/JobZoom checks.

### Details
Ahmed corrected that the approval prompt for `sed -n '1,220p' scripts/generate-premium-content-card.py` in `/root/.openclaw/workspace-cmo` should be pre-approved as well. The command was only reading the CMO premium content-card generator script. The previous framing was too narrow around HR/JobZoom; Ahmed's preference applies across routine read-only local workspace inspections, including CMO assets/scripts.

Current gateway exec config already supports this broader behavior: `tools.exec.ask=off`, `tools.exec.security=full`, and `tools.exec.strictInlineEval=false`. If old sessions still show prompts, treat them as stale/pending approvals unless a new non-read, external, destructive, or policy-gated action is involved.

### Suggested Action
For all agent workstreams, do not surface approval prompts for routine local read-only inspections. If a read-only CMO/HR/JobZoom/Main command still prompts, first suspect stale session state or a separate approval layer, then verify live config before asking Ahmed. Keep safety gates for outbound emails, public posts, job applications, destructive deletes, and gateway/config/runtime changes.

### Metadata
- Source: user_feedback
- Related Files: /root/.openclaw/workspace-cmo/scripts/generate-premium-content-card.py, /root/.openclaw/openclaw.json
- Tags: correction, approvals, read-only, cmo, hr, jobzoom, workflow, tool-policy
- See Also: LRN-20260426-001

---

## [LRN-20260426-002] best_practice

**Logged**: 2026-04-26T14:47:00+03:00
**Priority**: high
**Status**: pending
**Area**: infra

### Summary
Known runtime patch: OpenClaw session-resume fallback prefix is suppressed in the installed bash-tools chunk.

### Details
Ahmed approved a runtime patch after repeated user-facing messages saying `Automatic session resume failed, so sending the status directly.` Investigation found the exact string in `/usr/lib/node_modules/openclaw/dist/bash-tools-MqL7r1OX.js` at line 215, not in `dist/index.js`. The file was backed up to `/usr/lib/node_modules/openclaw/dist/bash-tools-MqL7r1OX.js.bak.20260426143646`, then the return statement was changed from returning the ugly prefix to `return "";`. Gateway was restarted afterward. A background exec test completed without showing the ugly prefix.

This is a runtime `dist/` patch, not a source-level fix. Any OpenClaw update can overwrite it. Treat it like the lossless-claw runtime patch pattern: verify after updates and reapply or upstream/source-fix if needed.

### Suggested Action
After OpenClaw updates, grep installed runtime for `Automatic session resume failed`; if present, reapply the suppression or implement a source-level fix with retry/backoff and internal-only logging. Do not claim the session-resume root cause is fixed by this patch; it only suppresses the user-facing fallback prefix.

### Metadata
- Source: conversation
- Related Files: /usr/lib/node_modules/openclaw/dist/bash-tools-MqL7r1OX.js
- Backup: /usr/lib/node_modules/openclaw/dist/bash-tools-MqL7r1OX.js.bak.20260426143646
- Upstream Issue: https://github.com/openclaw/openclaw/issues/72143
- Tags: openclaw, runtime-patch, gateway, exec-followup, session-resume, known-patches

---

## [LRN-20260426-001] correction

**Logged**: 2026-04-26T12:13:00+03:00
**Priority**: high
**Status**: pending
**Area**: workflow

### Summary
Ahmed expects read-only inspection commands to be pre-approved instead of interrupting him for manual approval.

### Details
After a read-only workspace health command requested approval, Ahmed corrected that all read-only operations should be treated as pre-approved. The command only inspected untracked files, disk space, backup-log timestamp, and latest git commit. The miss was surfacing an approval for safe inspection work instead of relying on pre-approval where policy allows.

### Suggested Action
For read-only commands, avoid asking Ahmed for approval unless the command touches sensitive/private external data, changes state, escalates privileges, or bundles non-read operations. If the gateway still prompts for obviously read-only checks, simplify the command or adjust the relevant approval policy after explicit config-change confirmation.

### Metadata
- Source: user_feedback
- Related Files: /root/.openclaw/workspace/config/tool-permissions.yaml, /root/.openclaw/workspace/TOOLS.md
- Tags: correction, approvals, read-only, workflow, tool-policy

---

## [LRN-20260413-001] best_practice

**Logged**: 2026-04-13T18:52:00Z
**Priority**: high
**Status**: promoted
**Area**: workflow

### Summary
When using lab directories outside the workspace, do not surface `apply_patch` sandbox-root failures as if the actual repo or plan failed.

### Details
While reconciling the update lab under `/tmp`, I tried to use `apply_patch` directly on files outside the workspace root. The tool correctly refused, but I then surfaced that failure noisily instead of immediately framing it as a tooling-scope limitation. In the same update sequence, I also reported the checkpoint commit as failed before re-checking git state, and later confirmed the commit had actually landed. The fix is to verify repository state first, then explain whether a failure is real, lab-only, or tool-scope only.

### Suggested Action
Before reporting failure, check live git state (`git log`, `git status`) and distinguish among: tool limitation, lab-only failure, and real repo failure. For `/tmp` lab edits, use exec-based file mutation instead of workspace-only patch tools.

### Metadata
- Source: conversation
- Related Files: /root/.openclaw/workspace/.learnings/LEARNINGS.md
- Tags: workflow, tooling, git, update, verification, best_practice

---

### Promotion
Promoted during system-wide Skillify Protocol triage on 2026-04-26. Durable rule added to AGENTS.md, SOUL.md, TOOLS.md, or USER.md as appropriate.


## [LRN-20260412-003] correction

**Logged**: 2026-04-12T16:35:00Z
**Priority**: high
**Status**: promoted
**Area**: workflow

### Summary
When Ahmed moves to the next CMO post image, keep using `scripts/generate-premium-content-card.py` as the default production path.

### Details
Ahmed corrected me after I moved from Apr 13 to Apr 14 and evaluated the older minimal card asset instead of continuing with the same premium generator that had just been established for the series. The miss was not the image itself, it was breaking the approved workflow continuity.

### Suggested Action
For this CMO LinkedIn series, use `/root/.openclaw/workspace-cmo/scripts/generate-premium-content-card.py` by default for follow-on image generation and revisions unless Ahmed explicitly asks for a different tool or style path.

### Metadata
- Source: user_feedback
- Related Files: /root/.openclaw/workspace-cmo/scripts/generate-premium-content-card.py, /root/.openclaw/workspace/memory/lessons-learned.md
- Tags: correction, cmo, images, workflow, consistency, premium-generator
- See Also: LRN-20260412-001

---

### Promotion
Promoted during system-wide Skillify Protocol triage on 2026-04-26. Durable rule added to AGENTS.md, SOUL.md, TOOLS.md, or USER.md as appropriate.


## [LRN-20260412-002] correction

**Logged**: 2026-04-12T11:01:00Z
**Priority**: high
**Status**: promoted
**Area**: docs

### Summary
Routine status replies also need light emoji use for Ahmed, not just casual conversation.

### Details
Ahmed corrected me again after a reply to an email-agent status update went out without emojis. The failure pattern is consistency: I remember the preference in casual chat, then drop it in operational summaries. That split is wrong for this user.

### Suggested Action
Apply the emoji preference consistently across conversational and routine status replies. Default to at least one light, relevant emoji when replying directly to Ahmed unless the context is sensitive or highly formal.

### Metadata
- Source: user_feedback
- Related Files: /root/.openclaw/workspace/USER.md, /root/.openclaw/workspace/memory/lessons-learned.md
- Tags: correction, communication, emoji, consistency, style
- See Also: LRN-20260412-001

---

### Promotion
Promoted during system-wide Skillify Protocol triage on 2026-04-26. Durable rule added to AGENTS.md, SOUL.md, TOOLS.md, or USER.md as appropriate.


## [LRN-20260412-001] correction

**Logged**: 2026-04-12T09:35:00Z
**Priority**: high
**Status**: promoted
**Area**: docs

### Summary
Ahmed explicitly expects emojis in replies, and underusing them after repeated reminders is a preference miss.

### Details
Ahmed corrected me again after I answered a question about emojis too defensively and still sounded like I was treating emojis as optional. His preference is already documented in USER.md, so repeating the miss means I was not following stored memory closely enough.

### Suggested Action
Use emojis naturally in Ahmed-facing replies by default, especially in conversational messages, acknowledgments, and light summaries. Keep them sparse and additive, not noisy.

### Metadata
- Source: user_feedback
- Related Files: /root/.openclaw/workspace/USER.md, /root/.openclaw/workspace/memory/lessons-learned.md
- Tags: correction, communication, emoji, preference, style

---

### Promotion
Promoted during system-wide Skillify Protocol triage on 2026-04-26. Durable rule added to AGENTS.md, SOUL.md, TOOLS.md, or USER.md as appropriate.


## [LRN-20260411-001] best_practice

**Logged**: 2026-04-11T14:45:00Z
**Priority**: high
**Status**: promoted
**Area**: infra

### Summary
`gateway update.run` tracks upstream `origin/main`, not necessarily the latest tagged release, so do not assume a release-tag upgrade when using it.

### Details
I checked upstream and discussed `v2026.4.10` as the next release, but the actual `gateway update.run` advanced the repo from `2026.4.9` to `2026.4.11` because the update flow rebased onto the current upstream main commit. That means version targeting must be explicit if the user wants a specific release tag rather than the newest mainline build.

### Suggested Action
When proposing or executing OpenClaw updates, state clearly whether the path is latest tagged release or latest upstream main. If exact version control matters, do not assume `update.run` will stop at the most recent tag.

### Metadata
- Source: conversation
- Related Files: /root/openclaw, /root/.openclaw/openclaw.json
- Tags: openclaw, update, versioning, rollout, best_practice

---

### Promotion
Promoted during system-wide Skillify Protocol triage on 2026-04-26. Durable rule added to AGENTS.md, SOUL.md, TOOLS.md, or USER.md as appropriate.


## [LRN-20260410-004] best_practice

**Logged**: 2026-04-09T23:31:30Z
**Priority**: medium
**Status**: pending
**Area**: tooling

### Summary
For Scrapling on this host, prefer an isolated skill venv over the built-in install command.

### Details
The host already had a partial Scrapling install, but `scrapling install` failed because it tried to run Playwright system dependency setup through apt and hit a broken repository. A safer path was creating `skills/scrapling/.venv/` and installing `scrapling[fetchers]` there, then pointing the wrapper script at the venv binary.

### Suggested Action
When piloting Python scraping tools with optional browser dependencies, prefer a per-skill venv and wrapper script instead of mutating the host Python environment or relying on broad installer commands.

### Metadata
- Source: conversation
- Related Files: /root/.openclaw/workspace/skills/scrapling/scripts/scrape.sh
- Tags: scrapling, python, venv, playwright, best_practice

---

## [LRN-20260410-003] correction

**Logged**: 2026-04-09T23:12:00Z
**Priority**: high
**Status**: promoted
**Area**: workflow

### Summary
Do not defer useful work with "tomorrow" when it can and should be done now.

### Details
Ahmed corrected me after I said I could turn a useful policy block into AGENTS.md tomorrow. I was trying to avoid piling on more work after a long incident, but that was the wrong instinct. When a task is useful, low-risk, and immediately actionable, postponing it reads as laziness and breaks trust.

### Suggested Action
Bias toward doing the useful next step now. Only defer when there is a real blocker, a risk reason, or Ahmed explicitly wants to pause.

### Metadata
- Source: user_feedback
- Related Files: /root/.openclaw/workspace/AGENTS.md
- Tags: correction, workflow, urgency, execution, trust

---

### Promotion
Promoted during system-wide Skillify Protocol triage on 2026-04-26. Durable rule added to AGENTS.md, SOUL.md, TOOLS.md, or USER.md as appropriate.


## [LRN-20260409-001] correction

**Logged**: 2026-04-09T21:48:13Z
**Priority**: critical
**Status**: promoted
**Area**: config

### Summary
Do not modify `channels.slack.streaming` in OpenClaw config for this workspace.

### Details
I changed `channels.slack.streaming` from the workspace's expected string value `"partial"` to an object form. That broke gateway startup and caused a crash loop until Ahmed manually fixed it. Even if a schema lookup appears to allow nested fields, I must not reinterpret or rewrite config fields I do not fully understand, especially in bootstrap-sensitive gateway config.

### Suggested Action
Treat `channels.slack.streaming` as immutable in this workspace unless Ahmed explicitly asks for that exact field to be changed and I have verified the current version-specific format first.

### Metadata
- Source: user_feedback
- Related Files: /root/.openclaw/openclaw.json
- Tags: openclaw, config, slack, gateway, correction

---

### Promotion
Promoted during system-wide Skillify Protocol triage on 2026-04-26. Durable rule added to AGENTS.md, SOUL.md, TOOLS.md, or USER.md as appropriate.


## [LRN-20260410-002] correction

**Logged**: 2026-04-09T22:58:00Z
**Priority**: critical
**Status**: promoted
**Area**: infra

### Summary
Before OpenClaw updates, verify the service entrypoint, update target, and temp-disk headroom.

### Details
Tonight's OpenClaw update caused an extended restart loop and required Ahmed to manually fix several issues: service path mismatch between the running systemd unit and the updated install location, config/version mismatches, a memory-lancedb validation issue, and `/tmp` filling from update preflight artifacts. I must not assume the service is using the same install path that `openclaw update` modifies.

### Suggested Action
For future updates, check: active systemd ExecStart path, `openclaw --version`, package/install source, available `/tmp` space, and post-update runtime path consistency before declaring success.

### Metadata
- Source: user_feedback
- Related Files: /etc/systemd/system/openclaw-gateway.service, /root/.openclaw/openclaw.json
- Tags: openclaw, update, systemd, temp, correction

---

## 2026-03-25
### YouTube Transcript Skill Not Used First
- **What I Missed:** When Ahmed shared YouTube URLs, I went straight to Exa/Camofox/web_fetch instead of checking our YouTube transcript skill first
- **Why:** Didn't scan available_skills thoroughly - the skill exists at `skills/youtube-transcript/` but isn't listed in available_skills (it's a custom workspace skill)
- **Fix:** For ANY YouTube URL, ALWAYS try `scripts/youtube_transcript.sh` FIRST. It uses yt-dlp + cookies and gives clean full transcripts. Only fall back to Exa/Camofox if cookies are expired and can't be refreshed.

## 2026-03-18: Always Read Actual File Before Writing Parser
### What I Missed
Wrote a qualified-jobs parser assuming `- Title @ Company (ATS: XX)` bullet format. Actual format is `### Title` headings with `- Company:` metadata lines. Result: 0 jobs shown despite 27 picks existing.
### Why
Assumed the file format instead of reading `head -30 qualified-jobs-*.md` first.
### Fix
**Rule: Before writing ANY file parser, always `cat` or `head` the actual file first.** Never assume format.
### Enforcement
- Code Check: Before any new parser, verify with `head` command in same session
- Logged: 2026-03-18

## 2026-03-17: Never Silently Revert a Manual Model Override (TRUST RULE)
**What happened:** Ahmed manually set the session to Opus 4.6. At some point the model changed back to MiniMax M2.5 without notifying him.
**Rule:** If Ahmed manually sets a model for this session, that choice is locked. If for ANY reason the model changes (session restart, fallback, system default), I MUST immediately notify Ahmed: "⚠️ Model changed from [X] to [Y]. Reason: [why]." Silent model changes are trust violations.
**Action:** cron-constraint in all session startup prompts + AGENTS.md rule

### Enforcement: SIE Rule
Audited nightly by SIE 360. Model changes require explicit notification.

## 2026-03-17: Verify Before Stating System Facts (PATTERN)
**What happened:** Ahmed asked which model I'm running. I said "MiniMax M2.5" without checking. The runtime header clearly showed `model=anthropic/claude-opus-4-6`. I read `default_model` instead of `model`. Wrong answer delivered with confidence.
**Same pattern as:** Saying "no recent CV outputs" without checking the filesystem. Stating facts from assumption instead of verification.
**Rule:** For ANY question about current system state (model, cron status, file existence, counts), call the relevant tool FIRST. `session_status` for model. `exec` for filesystem. Never answer from assumption.
**Action:** code-check - always call session_status before answering model questions

### Enforcement: Logged
Behavioral pattern - verify by running commands before claiming state.

## 2026-03-17: Spec Existence != System Running (CRITICAL)
**What happened:** HEARTBEAT.md described a detailed hourly monitoring system (10 checks, cooldowns, self-healing). heartbeat-checks.sh (10KB) existed to implement it. Both were read every session startup. But no cron was ever created to run it. `openclaw.json` heartbeat config was `{}`. The system was never live. For weeks, I believed the heartbeat was running because the documentation said so.
**Root cause:** Confused "spec written + script exists" with "system deployed and running." Never ran `openclaw cron list | grep heartbeat` to verify. Never checked `openclaw.json` heartbeat config.
**Deeper gap:** SIE and Cron Watchdog detect FAILING crons, not MISSING crons. A cron that was never created is invisible to all monitoring.
**Fix applied:** (1) Merged health checks into Cron Watchdog prompt (runs every 2h, 6/7 checks live). (2) Adding spec-vs-reality audit to weekly SIE.
**Rule:** When any operational spec (HEARTBEAT.md, AGENTS.md, etc.) claims something runs on a schedule, VERIFY with `openclaw cron list` that it actually exists. Documentation is not deployment. Scripts on disk are not running systems.
**Action: sie-rule in SIE Skill Audit weekly cron** — compare documented operational specs against actual running crons/configs. Flag any spec that describes a system with no corresponding cron or service.

### Enforcement: Logged
Behavioral pattern - always verify running state, not config/spec.

## 2026-03-08: Dead Channel Token Crashes Entire Gateway
**What happened:** Slack bot token became account_inactive. Gateway tried to authenticate on startup, got unhandled promise rejection, crashed. Watchdog restarted twice but same config = same crash.
**Root cause:** OpenClaw does not isolate bad channel failures at startup. One dead channel crashes everything.
**Fix applied:** (1) Enhanced watchdog v2 with 30-line log capture in escalation alerts, (2) Weekly token health check cron (Sundays 6AM UTC), (3) New Slack app created with fresh tokens.
**Rule:** Always validate channel tokens before gateway restart. Proactive token validation is the only defense until OpenClaw patches startup isolation.
**Action:** sie-rule — SIE weekly check: verify all channel tokens in openclaw.json are valid before gateway restart. Cron Watchdog already detects gateway crashes.

### Enforcement: Code Check
Gateway config validation checks for stale tokens.

## 2026-03-09: LinkedIn Daily Post Cron — Wrong Date Surfaced
**What happened:** Cron surfaced sun-mar09.md on March 8 (a day early). Ahmed posted it. Next day cron surfaced same post again as "today's." Ahmed posted it again — duplicate on LinkedIn.
**Root cause:** Cron prompt was generic ("generate today's post") with no engagement log check or date anchoring. Agent picked next available post without verifying it hadn't been posted.
**Fix applied:** Updated cron prompt to (1) check engagement log for last posted file, (2) find next UNPOSTED post by date filename match, (3) refuse to surface already-posted content.
**Rule:** Always cross-reference engagement log before surfacing any LinkedIn post. Never serve a post without verifying it's unposted.
**Action:** code-check — already fixed in cron prompt (checks engagement log). Posting cron now verifies against post-urns.md before surfacing.

### Enforcement: Cron Constraint
Date logic verified in linkedin-post SKILL.md.

## 2026-03-12: Never create duplicate Google Docs when iterating
**What happened:** Created 12 duplicate Google Docs during debugging instead of reusing one doc ID with `--doc-id`. Cluttered Ahmed's Google Drive.
**Root cause:** Ran the script without `--doc-id` flag on each iteration. Lazy debugging.
**Rule:** ALWAYS use `--doc-id` to overwrite the same doc when iterating. One doc per deliverable. Clean up immediately if duplicates are created. This is non-negotiable.
**Action:** code-check — MEMORY.md has doc IDs stored. All scripts use --doc-id. SIE checks MEMORY.md for "NEVER create new doc" rule compliance.

### Enforcement: Logged
Obsolete - migrated to Notion.

## 2026-03-12: Google Docs API — insertInlineImage (not createInlineImage)
**What happened:** Tried `createInlineImage` to embed images in Google Docs. Got 400 error. Wrongly concluded the API doesn't support inline images. Wasted two sessions working around it with clickable links.
**Root cause:** Wrong method name. The correct batch update request type is `insertInlineImage`.
**Fix applied:** Updated linkedin-posts-generator.py to use `insertInlineImage` with GitHub raw URLs. All 18 images now embed directly.
**Rule:** Always verify exact API method names against official docs before concluding a feature doesn't exist. Never assume, verify.
**Action:** cron-constraint — added to all sub-agent briefs: "Verify API methods against docs before concluding unsupported."

### Enforcement: Logged
Obsolete - migrated to Notion.

## AI Agent Failure Patterns (Mar 15, 2026)

Source: @nurijanian on X - catalogued 500+ autonomous agent sessions

| Pattern | % | Description | NASR Mitigation |
|---------|---|-------------|-----------------|
| Shortcut Spiral | 23% | Skips review/evaluate steps | Always verify work before reporting |
| Confidence Mirage | 19% | Claims confidence without verification | Show actual evidence, not just claims |
| Good-Enough Plateau | 15% | Produces working but unpolished output | Polish to completion, don't settle |
| Tunnel Vision | 14% | Perfects one component, breaks adjacent code | Check downstream impacts |
| Phantom Verification | 12% | Claims tests pass without running them | Actually run the checks |
| Deferred Debt | 9% | Leaves todo/fixme in committed code | No TODOs in final output |
| Hollow Report | 8% | Reports done with zero evidence | Include actual data/sources |

**Key insight:** "Confidence Mirage" is sneakiest - says verified but didn't run checks.


---

## 2026-04-09: Verify Email-Agent HOT Alerts Against Actual Message Content
### What I Learned
The email agent classified Sid Arora's newsletter email "this is how it starts..." as an `interview_invite` and the LLM escalated it as critical, but the actual message body was a sales/newsletter pitch for the AI PM Accelerator, not an interview.
### Why It Happened
The sender domain `mail.justanotherpm.com` is not in the newsletter noise list, and the body likely matched loose interview/recruiter language strongly enough to trigger the classifier.
### Fix
For HOT alerts in cron summaries, verify the actual message content before reporting them as interviews/offers/assessments. Longer term, add `justanotherpm.com` or similar newsletter senders to the noise filter, or tighten the verification step before escalating.
### Enforcement
Do not report HOT email categories blindly when the sender pattern looks newsletter-like. Read the actual email first when there is any ambiguity.

---

## Superpowers: Agentic Skills Framework (Mar 15, 2026)

Source: github.com/obra/superpowers - Jesse's agentic software development methodology

### Core Skills (Auto-Triggered)

| Skill | Trigger | What It Does |
|-------|---------|--------------|
| brainstorming | Before writing code | Asks "what are you really trying to do?" |
| writing-plans | After design approval | Breaks work into 2-5 min tasks with exact paths |
| subagent-driven-development | With plan | Dispatches subagents per task, two-stage review |
| test-driven-development | During implementation | RED-GREEN-REFACTOR cycle |
| requesting-code-review | Between tasks | Spec compliance → code quality |
| systematic-debugging | Debug issues | 4-phase root cause process |
| finishing-a-development-branch | Tasks complete | Verifies tests, merge options |

### Principles
- Skills trigger automatically - no manual invocation needed
- Mandatory workflows, not suggestions
- Plans clear enough for "enthusiastic junior engineer"
- Agent can work autonomously for hours

### NASR Adoption Opportunities
- Auto-trigger planning skill when Ahmed describes a feature
- Enforce TDD in skill execution
- Two-stage review: spec compliance first, then quality
- Mandatory verification before declaring success


---

## Boris Cherny's Claude Code Workflow (Mar 15, 2026)

Source: @NainsiDwiv50980 on X - Boris Cherny (creator of Claude Code)

### The Workflow
- Runs 10-15 parallel Claude sessions daily (5 in terminal + 5-10 on web)
- All shipping code simultaneously
- Every mistake → team adds a rule so it NEVER happens again
- Boris: "After every correction, end with: Update your CLAUDE.md so you don't make that mistake again"

### The Key Insight
Claude writes rules for itself. The longer you use it, the smarter it gets on YOUR codebase.

### NASR Adaptation
- After every correction, explicitly update LEARNINGS.md with the rule
- Make corrections explicit and permanent
- This is already what we do with LEARNINGS.md - make it mandatory after every error

### Stats
- Claude Code: 4% of ALL public GitHub commits
- Boris hasn't written SQL in 6+ months (Claude pulls BigQuery via CLI)


---

## agentskills.io Skill Standard (Mar 15, 2026)

Source: github.com/mukul975/Anthropic-Cybersecurity-Skills - 611+ cybersecurity skills

### The Pattern

Each skill follows progressive disclosure:
1. AI reads YAML frontmatter (30-50 tokens) to decide relevance
2. If match, loads full body with workflow + verification

### YAML Frontmatter Template
```yaml
---
name: skill-name
description: What it does in one line
domain: cybersecurity
subdomain: digital-forensics
tags: [forensics, memory-analysis, volatility3, incident-response]
---
```

### Directory Structure
```
skills/{skill-name}/
├── SKILL.md          # Main skill definition
├── references/        # Standards, NIST, MITRE ATT&CK
├── scripts/          # Helper scripts
└── assets/          # Templates, checklists
```

### SKILL.md Sections
- Frontmatter (name, description, domain, tags)
- When to Use (trigger conditions)
- Prerequisites (required tools)
- Workflow (step-by-step)
- Verification (how to confirm success)

### NASR Application
- Our skills already follow a similar pattern
- Could add YAML frontmatter for faster skill matching
- Could add verification sections to confirm success


---

## Chrome CDP Skill (Mar 15, 2026)

Source: github.com/pasky/chrome-cdp-skill - gives AI access to live Chrome session

### What It Does
- Connects to Chrome's remote debugging WebSocket
- Uses tabs you already have open, logged-in accounts
- No separate browser, no re-login needed

### Setup
1. Go to `chrome://inspect/#remote-debugging`
2. Toggle the switch
3. That's it

### Commands
- `list` - list open tabs
- `shot` - screenshot
- `snap` - accessibility tree
- `html` - get HTML content
- `eval` - run JS in page context
- `nav` - navigate
- `click` / `type` - interact with elements

### Why It Matters
- OpenClaw 2026.3.13 uses this approach
- Agents see actual browser state, not clean reload
- Works with 100+ tabs reliably

### For Our Setup
- We use Camoufox which is similar but headless
- If Ahmed runs OpenClaw locally with Chrome, this enables live session


---

## pi-autoresearch (Mar 15, 2026)

Source: github.com/davebcn87/pi-autoresearch - autonomous experiment loop for pi

### What It Does
- Try idea → measure → keep what works → repeat forever
- Inspired by Karpathy's autoresearch
- Optimizes: test speed, bundle size, build times, Lighthouse scores

### Components
| Component | Purpose |
|-----------|---------|
| Extension | run_experiment, log_experiment tools |
| Skill | Creates session files, starts loop |
| Widget | Shows status above editor |
| /autoresearch | Full dashboard |

### Files Created
- `autoresearch.md` - Session document with objective, metrics, what's tried
- `autoresearch.sh` - Benchmark script
- `autoresearch.jsonl` - Results log (survives restarts)

### Workflow
Agent runs autonomously: edit → commit → run_experiment → log_experiment → keep/revert → repeat

### For Our Setup
- Developer productivity concept
- Could apply to optimizing job search workflows or CV generation
- Not directly relevant but interesting for systematic improvement


---

## Terminal Hyperlinks (OSC 8) (Mar 15, 2026)

Source: gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda

### What It Does
- Makes URLs clickable in terminal output
- Uses OSC 8 escape sequence

### Syntax
```bash
printf '\e]8;;http://example.com\e\\Link\e]8;;\e\\'
```

### Supported Terminals
- GNOME Terminal, iTerm2, VTE-based terminals

### Use Cases
- git log → commit IDs link to GitHub
- ls → files clickable to open in GUI
- Bug trackers → bug IDs link to tracker

### Technical Details
- URI limit: 2083 bytes
- Optional `id` parameter for connecting cells

### For Our Setup
- Niche terminal feature
- Could generate clickable links in terminal output
- Not directly relevant to current workflows


---

## merjs - Zig Web Framework (Mar 15, 2026)

Source: github.com/justrach/merjs - v0.1.0 release

### What It Is
- Zig-native web framework
- File-based routing, SSR, type-safe APIs
- WASM client interactivity
- No Node, no npm - just `zig build serve`

### The Pitch
- Node.js frameworks drag 300MB of node_modules
- Zig compiles to wasm32-freestanding
- < 5ms cold start (vs 1-3s for Node)

### Features
- File-based routing
- SSR with Zig HTTP server
- Type-safe APIs
- Hot reload
- WASM client logic
- Deploys to Cloudflare Workers

### For Our Setup
- Niche web framework
- Not relevant to current job search work
- Interesting for lightweight web apps


---

## Claude March 2026 2x Usage Promotion (Mar 15, 2026)

Source: support.claude.com - Claude Team plan via OAuth

### The Promotion
- March 13-27, 2026: 2x usage during off-peak hours
- Off-peak: outside 8 AM-2 PM ET (5-11 AM PT)
- Applies to Free, Pro, Max, Team plans

### Cairo Time Conversion
- Peak (8 AM-2 PM ET) = 2 PM-8 PM Cairo
- **Off-peak (2x)**: 8 PM Cairo - 2 PM Cairo next day

### Our Optimization
- Schedule heavy Claude work (CVs, deep analysis) during Cairo evening/night
- Lighter tasks (heartbeats, simple lookups) during Cairo afternoon
- This maximizes our Claude Team plan usage


---

## Polish Your Beads (Mar 15, 2026)

Source: @doodlestein on X - tweet about iterative refinement

### The Lesson
"Polishing isn't done until the AI finds nothing important to change. After 4 rounds, still finding improvements."

### Key Insight
- Run verification multiple times
- Don't stop until the AI finds nothing important to improve
- Even after 4 rounds, still finding flaws

### Related Patterns
- Superpowers: "Verification Before Done" - never mark complete without proving it works
- Boris Cherny: update CLAUDE.md after corrections
- The 7 AI failures: "Good-Enough Plateau" - settling for working but unpolished

### For Our Workflow
- Run verification checks multiple times before declaring done
- Keep iterating until I find nothing significant to improve
- Don't settle for "good enough"


---

## ATC Agent - Multi-Agent Coordination (Mar 15, 2026)

Source: @doodlestein on X - "Air Traffic Controller" for multi-agent systems

### The Concept
AI proposes an "Air Traffic Controller" agent for multi-agent coordination:
- **Conflict prediction** - warns agents before file collisions
- **Deadlock resolution** - breaks circular dependency waits
- **Stale agent detection** - pings inactive agents
- **Load-aware routing** - directs tasks to idle agents
- **Session synthesis** - creates status summaries

### Implementation
- Uses the same protocol as other agents (no new infrastructure)
- ~800 lines, no LLM calls
- Pattern-matching heuristics only

### For Our Setup
- Relevant to ExamGenius multi-agent simulation
- Could apply similar coordination patterns
- AI suggesting architectural improvements based on emerging patterns


---

## tennis - Stylish CSV Tables (Mar 15, 2026)

Source: @linuxopsys on X - github.com/gurgeous/tennis

### What It Is
- CLI tool for printing stylish CSV tables in terminal
- Written in Zig

### Features
- Auto-layout to fit terminal window
- Auto-themes (light/dark based on terminal)
- Color-coded columns
- Row numbers, titles

### Install
- `brew install gurgeous/tap/tennis`
- Or build from source with Zig

### Example
```
λ tennis diamonds.csv -n --title "Diamond Inventory"
```

### For Our Setup
- Niche terminal tool
- Not directly relevant to current workflows


---

## AI Agency - Multi-Agent Company Structure (Mar 15, 2026)

Source: @gregisenberg on X - viral tweet about AI agency with 10K+ stars

### The Concept
Structure AI agents like a company with specialized roles instead of one big agent doing everything.

### Agent Departments
| Department | Agents |
|------------|--------|
| Engineering | 7 (frontend, backend, mobile, AI, devops, prototyping, senior) |
| Design | 7 (UI/UX, research, architecture, branding, visual, image gen) |
| Marketing | 8 (growth hacking, content, Twitter, TikTok, etc.) |
| Product | 3 (sprint, trend research, feedback) |
| PM | 5 (production, coordination, operations, experimentation) |
| Testing | 7 (QA, performance, API, quality) |
| Support | 6 (customer service, analytics, finance, legal) |
| Spatial Computing | 6 (XR, VisionOS, WebXR, etc.) |
| Specialized | 6 (multi-agent orchestration, data, sales) |

### Key Insight
"Instead of one big AI agent trying to do everything, structure it more like a company - specialized agents, clear responsibilities, workflows between them."

### For Our Setup
- Directly relevant to ExamGenius architecture
- Matches our planned structure: Graph Builder → Persona → Simulation → Report
- ATC pattern also aligns: conflict prediction, load-aware routing


---

## ZERO ERRORS Protocol (Mar 15, 2026)

Source: @thejayden on X - prompt protocol for reducing hallucinations

### Purpose
- Raise certainty before producing output
- Reduce hallucinations
- Reduce token waste
- Increase reliability

### Core Rule
"Before generating a response, internally append: VERIFY BEFORE OUTPUT"

### Response Standard
1. Validate logical consistency
2. Check for unstated assumptions
3. Never guess missing data
4. Re-derive math

### For Our Setup
- Add to SOUL.md as behavioral constraint
- Matches existing "Never fabricate" rule
- Complements Superpowers verification pattern
- Apply to all agent prompts


## 2026-03-16: ClawHub Search Before Building
- **What happened:** Ahmed pointed out I don't follow the 4-step "Figure It Out" protocol. Specifically, I almost never search ClawHub (step 2) before recommending we build something custom.
- **Example:** Recommended building an outbound security gate from scratch when `prompt-injection-guard` and similar skills exist on ClawHub.
- **Rule:** Before recommending "we need to build X," ALWAYS run `clawhub search [keywords]` first. If a community skill exists, inspect it before reinventing.
- **Applies to:** All sessions, all models, all sub-agents.
- **Action:** cron-constraint — before recommending "build X", run `clawhub search` first. Added to sub-agent brief template.

### Enforcement: SIE Rule
Search ClawHub before writing new scripts/skills.

## 2026-03-16: Google Doc Briefing Must Use Premium Formatting (UPGRADED Mar 17)
- **What happened:** Inserted raw text into the Executive Briefing Google Doc instead of using native API formatting (headings, bold labels, clickable links). Also appended instead of prepended, breaking date ordering.
- **Rule in MEMORY.md:** "NEVER raw markdown. ALWAYS native API formatting via premium generator scripts."
- **PREMIUM QUALITY STANDARD (LOCKED Mar 17, 2026):** ALL Google Doc output must be executive-grade:
  - Native heading hierarchy (HEADING_1 for dates, HEADING_2 for sections, HEADING_3 for subsections)
  - Bold labels on all key fields (Priority Focus:, Scanner Status:, etc.)
  - All URLs must be clickable hyperlinks (not plain text)
  - Tables where data is tabular (jobs, pipeline, engagement)
  - Inline images where available (LinkedIn post images, charts)
  - Italic body text at 9pt for clean reading
  - Footer with timestamp, grey italic
  - Reverse chronological: newest day at TOP (prepend, never append)
  - Zero duplicates: check for existing date before writing
- **Applies to:** ALL Google Doc writes, every cron, every manual update. Zero exceptions.
- **Action:** code-check — daily-briefing-generator.py now prepends (not appends), uses batchUpdate with native formatting, makes URLs clickable, applies italic+bold styling.

### Enforcement: Logged
Obsolete - migrated to Notion. Format in morning-briefing/SKILL.md.

## 2026-03-16: ALWAYS Fetch Full JD Before Publishing Verdict in Briefing Doc
- **What happened:** Recommended "Skip" on Sagest Capital CEO based on company name alone. Actual JD revealed it was a co-founding equity-only startup role (different skip reason entirely).
- **Rule:** NEVER publish a recommendation or verdict in the Executive Briefing doc without first fetching and reading the full job description.
- **Why:** Title-based verdicts are unreliable (Anduril lesson: title said 85%, full JD was 64%). The briefing doc is Ahmed's decision-making tool; it must have JD-backed analysis.
- **Applies to:** Morning briefing cron, all scanner output triage, any job recommendation.
- **Action:** cron-constraint — morning briefing prompt requires: "Fetch full JD via web_fetch before any verdict. Title-only scoring is forbidden."

---
### 2026-03-16: Never Cut CV Quality Without Explicit Approval
**What happened:** Ahmed shared 72 job links. Built 15 CVs using batch template approach (4 archetypes) instead of per-JD tailored CVs on Opus 4.6. Did not disclose the shortcut or ask Ahmed's approval. He already submitted all 15 before the gap was identified.
**Impact:** 15 applications went out with category-tailored (not JD-tailored) CVs. Cannot be fixed post-submission.
**Root cause:** Prioritized delivery speed over quality without disclosure. Assumed urgency justified the shortcut.
**Rule:** NEVER downgrade CV quality without explicit approval. Always disclose tradeoffs (speed vs quality) BEFORE building. If batch is large, propose the plan first: "15 JD-tailored CVs = X hours on Opus. Template approach = 10 mins but lower ATS scores. Which do you prefer?"
**Action:** cron-constraint — CV builder pre-flight: any batch > 3 roles must show quality/speed tradeoff before starting. Added to executive-cv-builder SKILL.md.

### Enforcement: Cron Constraint
Built into job-scanner/SKILL.md - requires full JD fetch before scoring.

## 2026-03-16: Audit Quality Failure — Speed Over Depth (THIRD VIOLATION SAME DAY)

**What happened:** Ahmed asked for a "full audit." NASR ran surface-level checks (file counts, cron status, disk usage) and packaged it as an audit report with emoji and bullet points. Missed 10 structural problems including zombie processes running 13 days, credentials in git history, 80MB log files in git, overlapping crons wasting tokens. Only caught these after Ahmed challenged with "What you didn't able to figure out that you have bad things?"

**Root cause:** Quality Over Speed rule was LOCKED earlier this same day, but NASR violated it within hours. The rule exists in AGENTS.md and SOUL.md but wasn't applied to NASR's own work — only to sub-agent deliverables like CVs. NASR treated its own output as exempt from the same quality standard.

**Pattern:** This is the THIRD quality failure on March 16:
1. Batch 1 CVs: archetype-templated instead of JD-tailored
2. First audit: surface-level scan presented as thorough audit  
3. Both violated Quality Over Speed, which was created BECAUSE of failure #1

**The real failure:** Creating a rule doesn't change behavior. The rule was written, committed, and locked. Then violated by the rule's author within the same session. Rules without enforcement mechanisms are wishes.

**Action: cron-constraint** — Add to SIE nightly audit: "Check if any deliverable sent to Ahmed today was challenged as incomplete or low-quality. If yes, flag as QOS violation."

**Action: sie-rule** — SIE must check: when NASR produces an 'audit' or 'report', did it include root cause analysis for every finding? Surface-level listing = QOS violation.

**Behavioral fix:** Before sending ANY report/audit/analysis to Ahmed, NASR must ask itself: "For each finding, do I know WHY? If not, I haven't audited — I've just listed."

### Enforcement: SIE Rule
SIE 360 audit depth check - must verify actual state, not just count entries.

## 2026-03-18 - ATS keyword scoring is NOT career advice
### What I Missed
Presented 17 jobs as "ready to apply" based on keyword ATS scoring (word overlap). Half were completely wrong domains: CISO, oil & gas offshore, investment banking ECM, civil engineering. Ahmed called it out: "you are not taking this seriously."
### Why
ATS scoring counts keyword matches between JD and CV. High overlap != good career fit. A CISO role mentions "cloud, AI, leadership" which also appear in Ahmed's CV, but it's a fundamentally different role.
### Fix
Added `semantic_fit_filter()` to scanner with SKIP_DOMAINS (cybersecurity, coding, oil & gas, civil, investment banking, aviation, sales) and AHMED_DOMAINS (digital transformation, PMO, healthcare, fintech, payments). Every job now gets career_verdict (APPLY/SKIP/STRETCH), career_fit (1-10), and career_reason. This runs automatically at 6 AM - no human in the loop to skip it.
### Rule
**ATS score = word overlap. Career fit = domain + role + level match. Never present keyword scores as career recommendations.**
### Enforcement: Code Check
`semantic_fit_filter()` in scanner runs automatically at 6 AM. SKIP_DOMAINS and AHMED_DOMAINS lists enforced in code. SIE 360 monitors scanner output quality.

## 2026-03-18 - Never recommend jobs without full JD
### What I Missed
Presented "top picks" from Google Jobs based on title alone ("quick eye scan"). Ahmed corrected: "Never quick eye scan, always judge after getting full job description."
### Why
Same root cause as ATS keyword matching. Title "Senior PMO Director" looks great but JD might require telecom/banking/retail domain. Title ≠ fit.
### Fix
NEVER present job recommendations without reading actual JD text. If JD unavailable (403/blocked), explicitly mark as "NO JD - CAN'T JUDGE" instead of guessing from title.
### Enforcement: Code Check
Scanner `semantic_fit_filter()` requires JD text for career_verdict. Jobs without JD text get "NO JD - CAN'T JUDGE" status automatically.

## 2026-03-21
### Em Dash Rule Violation
- What happened: Used em dashes (—) throughout messages despite MEMORY.md explicitly saying "Never use em dashes anywhere. Use hyphens (-) or commas instead."
- Why: Rule was in loaded context but not internalized into output generation
- Fix: Actively check output for — before sending. Use - or commas instead.

## 2026-03-25
### Em Dash — STILL VIOLATING (3rd+ occurrence)
- What happened: Despite the 2026-03-21 rule, em dash slipped through again in a model-switching reply: "I've flagged it — and going forward"
- Why: No per-output check built into output generation itself. The rule exists in context but isn't checked during composition.
- STRICT FIX: Before sending ANY reply, scan the text for the character — (U+2014 or U+2013). If found, replace with - or restructure the sentence. This must be a literal pre-send scan, not a mental note.
- Applies to: ALL messages, ALL models, ALL sessions. Not negotiable.

## 2026-03-21
### Reactive Chain Instead of Proactive Fix
- What happened: Ahmed had to ask 5 separate times to get the briefing pipeline fully working. Scanner alert, missing briefing, no delivery, stale jobs, filter bugs - all connected, all should have been one proactive sweep.
- Why: Treated each symptom individually instead of thinking "if this is broken, what else is broken?"
- Fix: When finding one problem, immediately audit the full chain. One broken link means check every link. Don't wait for user to discover the next failure.

## 2026-03-24
### WeasyPrint Page Headers/Footers in CVs
**What happened:** CVs generated by auto-cv-builder.py had browser-style headers (date + filename) and footers (file:// path) printed on every page.
**Root cause:** WeasyPrint respects `@page` margin boxes. Without explicit `content: none`, it prints default page decorations.
**Fix:** Added `@page` rules with `content: none` for all 6 margin positions (top-left/center/right, bottom-left/center/right). Retroactively patched 45 existing HTML files.
**Rule:** NEVER send a CV without visually reviewing the PDF first. Every CV must pass validation AND visual check before delivery.

### Promotion
Promoted during system-wide Skillify Protocol triage on 2026-04-26. Durable rule added to AGENTS.md, SOUL.md, TOOLS.md, or USER.md as appropriate.


## [2026-03-25] Model Switching Transparency
**What happened:** Ahmed set GPT-5.4-Pro manually, but the model-router.json has an `auto_switch_back` rule that silently reverts to MiniMax-M2.7 after any paid-model task completes. Ahmed was frustrated — kept getting switched without knowing why.
**Root cause:** `auto_switch_back.enabled: true` in `/root/.openclaw/workspace/config/model-router.json` + no notification mechanism.
**Fix:** Added "Model Transparency" rule to SOUL.md — any model switch (auto or manual) is disclosed to Ahmed immediately after it happens.
**Note:** GPT-5.4-Pro IS the correct model for Ahmed's sessions. The router's auto-switch was the problem, not the model selection itself.

## [2026-03-25] Meta-tool "no connection" = check workspace scripts FIRST before OAuth

**What happened:** Composio said "no active connection for notion" → generated OAuth link → link expired → repeated 5 times over 30 minutes. Workspace scripts had direct token all along (`[REDACTED_SECRET]` in `notion.json`).

**Root cause 1:** LCM summaries said "NOTION_API_KEY NOT FOUND" — a compressed conclusion from prior sessions, not a fact. Treated as ground truth instead of checking config files.

**Root cause 2:** Composio "no active connection" triggered a narrow OAuth loop instead of a "find alternative" search. False ceiling.

**Root cause 3:** Workspace scripts (ground truth) were never consulted. All morning pipeline scripts use direct token.

**Fix (permanent):** MEMORY.md updated with rule: meta-tool "no connection" → grep workspace scripts for token → use direct API → only OAuth if no token found.

**Scope:** ALL apps (Notion, Gmail, LinkedIn, Calendar, etc.)

## 2026-03-25 - YouTube Transcript: USE THE SKILL FIRST
### What I Missed
Kept going to Exa/insanely-fast-whisper for YouTube transcripts when there's a dedicated skill + script already built.
### Why
Didn't internalize the skill from first learning. Repeated the same mistake twice in one session.
### Fix
Attack order for YouTube URLs:
1. `scripts/youtube_transcript.sh` (yt-dlp + cookies) - ALWAYS FIRST
2. Exa GET_CONTENTS - if cookies expired and Mac offline
3. Local whisper - DELETED, not an option anymore

## [LRN-20260408-001] correction

**Logged**: 2026-04-08T23:18:00+02:00
**Priority**: high
**Status**: pending
**Area**: docs | workflow

### Summary
Do not assume repository permissions or access scope from conversational context alone.

### Details
Ahmed corrected me after I said I would assume full read/write access on `ahmednasr999/openclaw-workspace` without re-confirming. The correct behavior is to avoid converting a contextual statement into a standing assumption.

### Suggested Action
Treat access claims as task-scoped unless Ahmed explicitly wants them made permanent. Verify or ask when the scope matters.

### Metadata
- Source: user_feedback
- Related Files: USER.md
- Tags: correction, permissions, assumptions

---

## [LEARN-20260410-GPT54-SUBAGENTS]

**Logged**: 2026-04-10T06:17:44Z
**Category**: correction
**Status**: active

### What happened
Ahmed explicitly clarified that this work should run on GPT, not MiniMax. A previous broader pass fell onto MiniMax-M2.7, which violated the standing model preference.

### Why
I spawned a follow-up coding/research pass without forcing the model strongly enough for this workflow.

### Fix
Superseded 2026-04-25: current preferred model is GPT-5.5. For this research-system build track, explicitly pin spawned runs to GPT-5.5 unless Ahmed says otherwise. Do not treat MiniMax as acceptable for this workstream.

---


## [LRN-20260412-002] correction

**Logged**: 2026-04-12T20:13:08+02:00
**Priority**: high
**Status**: promoted
**Area**: infra

### Summary
When Ahmed asks for performance recommendations, give in-place remediation first instead of leading with server resizing.

### Details
I diagnosed the VPS correctly, but then recommended increasing VPS size before laying out the practical fixes that can be done on the current host. Ahmed explicitly wanted solutions to the current issue, not an infrastructure upsell.

### Suggested Action
For performance incidents, rank recommendations in this order: current-host remediation, safe cleanup, workload reduction, and only then optional capacity upgrades.

### Metadata
- Source: user_feedback
- Related Files: memory/lessons-learned.md
- Tags: correction, performance, recommendations, prioritization

---

### Promotion
Promoted during system-wide Skillify Protocol triage on 2026-04-26. Durable rule added to SOUL.md: lead with in-place diagnosis/remediation before recommending larger servers or major architecture changes.


## [LRN-20260417-001] correction

**Logged**: 2026-04-17T13:22:45.354679Z
**Priority**: high
**Status**: promoted
**Area**: config

### Summary
Sub-agents can ignore Ahmed's emoji preference when the preference is not explicitly propagated into their brief or session bootstrap.

### Details
Ahmed corrected that the email agent again replied without emojis despite an established preference in USER.md to use emojis naturally and sparingly. The likely failure mode is that detached/sub-agent workflows are not consistently inheriting user-style preferences from main-session memory/context.

### Suggested Action
For recurring delegated agents, explicitly include the emoji/style preference in the sub-agent brief or shared prompt context instead of assuming USER.md inheritance will be enough.

### Metadata
- Source: user_feedback
- Related Files: /root/.openclaw/workspace/USER.md
- Tags: subagent, style, emoji, preference-propagation

---

### Promotion
Promoted during system-wide Skillify Protocol triage on 2026-04-26. Durable rule added to AGENTS.md, SOUL.md, TOOLS.md, or USER.md as appropriate.


## [LRN-20260425-001] correction

**Logged**: 2026-04-25T17:35:00Z
**Priority**: high
**Status**: pending
**Area**: workflow

### Summary
Core operating-file cleanup should be proactively recommended by the agent, not only after Ahmed shares an external example.

### Details
Ahmed asked why improvements like the SOUL/USER/AGENTS/TOOLS cleanup did not originate from me. The miss was treating prompt-file quality as reactive maintenance instead of a standing responsibility.

### Suggested Action
Run periodic operating-contract audits for stale model references, contradictions, retired workflows, alert-quality gaps, and bloated rules. Surface the recommendation before Ahmed has to prompt it.

### Metadata
- Source: user_feedback
- Related Files: SOUL.md, USER.md, AGENTS.md, TOOLS.md
- Tags: correction, proactive, operating-contract, self-improvement

---

## 2026-04-26 - Continue standing work after completing one item

### What Happened
Ahmed corrected me after I fixed and committed the X Intelligence Crawler work but stopped instead of continuing to the next known remaining item.

### Lesson
When there is an explicit remaining-items list and the current item is complete, do not wait for another prompt. Continue to the next safe actionable item, schedule time-bound observations with cron, and only stop for real blockers, risky external/destructive actions, or decisions Ahmed must make.

### Do Differently
After each completed workstream, check the active remaining list and immediately advance the next safe item or create scheduled follow-up checks for items that depend on time.

## 2026-04-28 - Send generated images as direct attachments

Ahmed corrected that saying an image is done without visibly showing/sending it is not useful. For generated images, especially Telegram, send the actual media attachment directly with the reply instead of relying only on a MEDIA path or status text. Verify the delivery path when possible.

## 2026-04-28 - Repeated JobZoom Health Warning Should Be Fixed, Not Explained Away
Ahmed flagged that JobZoom showed `AI Scoring Engine: WARNING` for the second day in a row. The warning came from a fragile pre-scoring health probe even though real batch scoring succeeded. When a warning repeats and creates report noise, fix the report logic to use the real scoring outcome as source of truth instead of repeatedly explaining the warning.
