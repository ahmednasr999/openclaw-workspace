# Learnings Log

## [LRN-20260312-001] Never assume how a system works — verify first
**Date:** 2026-03-12
**Category:** User Correction
**What happened:** Assumed Slack x-analysis had X API integration because it could fetch tweet content. Was wrong — it was using Camoufox browser. Wasted time arguing about API credits.
**Rule:** When asked how something works, verify the actual implementation before explaining. Never state assumptions as facts. If unsure, say "I don't know" or "let me check" rather than guessing.
**Fix:** Added Camoufox as default tool for X/Twitter, LinkedIn, Amazon. Test before claiming.

---

# Learnings Log

*Corrections, knowledge gaps, and best practices.*
*Format: [LRN-YYYYMMDD-XXX]*

## [LRN-20260311-001] Job Radar surfacing junk as "High Priority"
**Date:** 2026-03-11
**Category:** User Correction
**What happened:** Job Radar v2 surfaced 8 "High Priority" roles. 1 was already applied (HungerStation, in applied-job-ids.txt for weeks). 7 were completely irrelevant (BPO, beauty CRM, risk management, junior associate, manufacturing, rail CTO). Ahmed rightfully called it out.
**Root cause:** Radar flags anything Director+ in GCC without checking: (a) already-applied dedup, (b) sector fit against kill list, (c) JD keyword overlap against master CV.
**Fix:** Update radar script to: (1) dedup against applied-job-ids.txt before surfacing, (2) enforce sector kill filter at scan level, (3) require minimum JD keyword overlap before "High Priority" label, (4) never surface roles without full JD available for scoring.
**Rule:** Never label a role "High Priority" without confirming it passes sector fit AND isn't already applied.

## [LRN-20260309-001] Always cross-check pipeline before presenting radar results
- **Date:** 2026-03-09
- **What happened:** Presented 7 radar roles to Ahmed one by one. All 5 viable ones were already applied to (in pipeline.md). Wasted 15+ minutes of his time.
- **Rule:** BEFORE presenting any role from Job Radar or LinkedIn Scout, cross-reference against jobs-bank/pipeline.md (check LinkedIn job IDs and company+role combos). Never present already-applied roles. The radar crons and briefing must dedup against the pipeline.
- **Fix needed:** (1) Build a dedup list from pipeline.md LinkedIn URLs, (2) Update scout/radar scripts to filter out applied jobs, (3) Update briefing cron to cross-reference before presenting.
- **Promoted to:** AGENTS.md (job radar rules)

## [LRN-20260306-001] CV creation MUST use Opus 4.6 — no exceptions
- **Date:** 2026-03-06
- **What happened:** Ahmed requested CVs tailored on Opus 4.6. Session was on MiniMax M2.5. Built 7 CVs on MiniMax without switching. Ahmed caught it.
- **Rule:** Before generating ANY CV, check session model. If not Opus 4.6, switch model or spawn sub-agent on opus46. Never proceed with CV generation on a lower model. Hard rule, zero exceptions.
- **Promoted to:** TOOLS.md (model routing rules)

## [LRN-20260306-002] Always disclose model used in CV delivery
- **Date:** 2026-03-06
- **What happened:** Ahmed wants transparency on which model was used for each CV.
- **Rule:** Every CV delivery message must include "Model Used: [alias]" so Ahmed always knows. Added to executive-cv-builder SKILL.md delivery template.
- **Promoted to:** skills/executive-cv-builder/SKILL.md

---

## [LRN-20260304-001] best_practice

**Logged**: 2026-03-04T10:23:00Z
**Priority**: medium
**Status**: resolved
**Area**: infra

### Summary
QMD embed fails on VPS without GPU, falls back to CPU at ~500 B/s (unusable)

### Details
QMD uses node-llama-cpp for local GGUF embeddings. On our Hostinger VPS (no GPU, 2 CPU cores), it tries to build llama.cpp with CUDA, fails, falls back to CPU. Embedding 459 chunks would take 30+ minutes. Fix: set searchMode to "search" (BM25 only) which works instantly.

### Suggested Action
For any VPS without GPU: always use QMD in BM25-only mode (searchMode: "search"). Only enable vector search if remote embedding provider is available.

### Metadata
- Source: error
- Related Files: ~/.openclaw/openclaw.json
- Tags: qmd, embeddings, gpu, vps
- Pattern-Key: infra.no_gpu_embedding_fallback

---


### 2026-03-05: Never use sed to delete markdown table rows
**What happened:** Used `sed -i` to remove a row from pipeline.md. It left a blank line that broke the table rendering on GitHub.
**What to do:** Always use the `edit` tool with exact old/new text replacement when modifying markdown tables. Never use sed for table row operations.

### 2026-03-05: Pipeline table sorting rules
**Rule:** Active Pipeline table: always sorted by Applied date (newest first). Radar Needs Action table: always sorted by Priority (🔴 High first, then 🟡 Medium, then 🟢 Low).
**Applies to:** Every pipeline.md update.

### 2026-03-05: Never replace table row with empty string
**What happened:** Used edit tool to replace a table row with empty string `""`. This left a blank line that broke the markdown table rendering. Happened twice in one session.
**What to do:** When removing a row, include it together with the adjacent row in old_string, and put only the adjacent row in new_string. This eliminates the blank line cleanly.

### 2026-03-05: Never conclude a file doesn't exist after checking one path
**What happened:** Ahmed asked about LinkedIn cookies. Checked `/root/.openclaw/config/` (wrong), concluded "no cookies", asked Ahmed to provide them. They were at `/root/.openclaw/workspace/config/` all along. Wasted time and broke trust.
**What to do:** (1) Always run `find /root -name "*filename*"` before saying "not found". (2) Read the script that uses the file to find the correct path. (3) Never guess paths, always verify.

### 2026-03-05: Always use linkedin-jd-fetcher.py for full JDs before ATS scoring
**What happened:** Scored Anduril at 85% based on job title alone. Full JD revealed Secret Clearance requirement and defense-only focus, dropping real score to 64%. Wasted time generating a CV for a role that's a poor fit.
**What to do:** Always fetch full JD with `linkedin-jd-fetcher.py` BEFORE scoring or generating CVs. Never score based on title alone.

## 2026-03-08: Dead Channel Token Crashes Entire Gateway
**What happened:** Slack bot token became account_inactive. Gateway tried to authenticate on startup, got unhandled promise rejection, crashed. Watchdog restarted twice but same config = same crash.
**Root cause:** OpenClaw does not isolate bad channel failures at startup. One dead channel crashes everything.
**Fix applied:** (1) Enhanced watchdog v2 with 30-line log capture in escalation alerts, (2) Weekly token health check cron (Sundays 6AM UTC), (3) New Slack app created with fresh tokens.
**Rule:** Always validate channel tokens before gateway restart. Proactive token validation is the only defense until OpenClaw patches startup isolation.

## 2026-03-09: LinkedIn Daily Post Cron — Wrong Date Surfaced
**What happened:** Cron surfaced sun-mar09.md on March 8 (a day early). Ahmed posted it. Next day cron surfaced same post again as "today's." Ahmed posted it again — duplicate on LinkedIn.
**Root cause:** Cron prompt was generic ("generate today's post") with no engagement log check or date anchoring. Agent picked next available post without verifying it hadn't been posted.
**Fix applied:** Updated cron prompt to (1) check engagement log for last posted file, (2) find next UNPOSTED post by date filename match, (3) refuse to surface already-posted content.
**Rule:** Always cross-reference engagement log before surfacing any LinkedIn post. Never serve a post without verifying it's unposted.

## 2026-03-12: Google Docs API — insertInlineImage (not createInlineImage)
**What happened:** Tried `createInlineImage` to embed images in Google Docs. Got 400 error. Wrongly concluded the API doesn't support inline images. Wasted two sessions working around it with clickable links.
**Root cause:** Wrong method name. The correct batch update request type is `insertInlineImage`.
**Fix applied:** Updated linkedin-posts-generator.py to use `insertInlineImage` with GitHub raw URLs. All 18 images now embed directly.
**Rule:** Always verify exact API method names against official docs before concluding a feature doesn't exist. Never assume — verify.
