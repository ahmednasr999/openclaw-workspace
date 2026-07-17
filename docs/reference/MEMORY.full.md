# MEMORY.md - Long-Term Memory

## Core Preferences
- Timezone: Cairo, Africa/Cairo.
- Relocation: open to relocating to Jeddah, Saudi Arabia, confirmed 2026-02-18.
- LinkedIn posts: always end with a question or CTA for engagement.
- Backups: keep only the latest backup, daily at 3 AM Cairo.
- Gmail check: daily at 8 AM Cairo.
- Formatting: never use em dashes. Use hyphens or commas.
- Current default model is GPT-5.5 via OpenAI Codex OAuth unless Ahmed changes it. Do not silently switch models.
- ChatGPT subscription status: Ahmed returned to ChatGPT Pro 20x on 2026-05-30 after briefly planning a 2026-06-07 downgrade to Pro 5x. Treat GPT-5.5 quota headroom as the 20x plan unless Ahmed changes the subscription again.
- Salary is the overriding decision factor when evaluating GCC executive roles; do not treat it as already resolved, secondary, or outweighed by non-salary hard-no filters unless Ahmed explicitly adds one. Reporting line and work arrangement are not hard filters if salary is high enough; onsite, hybrid, or remote can be acceptable when compensation justifies it. <!-- dream-promoted 2026-05-11 -->
- Image generation cost preference: do not add direct OpenAI API billing just to unlock image generation if the authenticated ChatGPT web Images workaround is viable. <!-- dream-promoted 2026-04-29 -->

## Agentic Engineering Operating Standard, Confirmed 2026-06-03

For serious agent/coding/automation work, use research-before-plan, a short plan artifact, one clear owner for parallel agents, raw evidence retention, and human approval before external-impact actions. Do not adopt broad YOLO/permission-skipping advice; OpenClaw autonomy must stay bounded by approval gates and verification.

## Content Pipeline Workflow, Confirmed 2026-02-19
Mission Control had two boards:
1. Task Board for high-level tracking.
2. Content Pipeline for LinkedIn/X content creation.

Current rule:
- Content Pipeline is the work. Task Board is only tracking.
- Task: create LinkedIn post about X, then create the content post in Pipeline, then mark task complete.
- Pipeline columns: Ideas, Outline, Draft, Design, Review, Published.
- Approval flow: OpenClaw creates draft and moves to Review, Ahmed reviews, Ahmed moves to Published when ready.

## LinkedIn Reel Style, Confirmed 2026-04-25 <!-- dream-promoted 2026-04-27 -->
Repurposed LinkedIn video/reel assets should be premium, executive, concise, and cinematic rather than basic utility renders.

Approved pattern: 9:16 vertical reel, dark executive visual system, clean typography hierarchy, glass-card UI treatment, subtle motion, restrained premium gradient, and narrative pacing such as shift -> risk -> rule -> question.

## LinkedIn Static Visual Default, Updated 2026-06-26
Universal default for Ahmed LinkedIn static post visuals: use the approved hand-drawn sketchnote concept unless Ahmed explicitly requests another direction.

Reference asset: `/root/.openclaw/workspace/media/inbound/234fe40d-96c3-4b4a-bf6f-dc1f75f91bbf.jpg`

Quality floor: `/root/.openclaw/workspace/output/linkedin/return-on-tokens-rot-handdrawn-reference-quality-latest-2026-06-10.png`

Required style: warm off-white paper, black ink illustration, restrained orange accents, toolkit/system metaphor, large handwritten headline, compact flow diagram, and Ahmed Nasr signature/footer.
Quality bar: match the hand-drawn reference craft level, not just its rough structure; reject outputs that feel generic, flat, stock-like, under-designed, sketch-filter-like, crowded, missing the system metaphor, or default to dark tech cards without explicit request. Dark executive visuals remain only for explicit reel/video/dark-card requests or JobZoom-specific visuals.

## Job Application and CV Workflow
Trigger: Ahmed shares a job link and description.

Steps:
1. Analyze job requirements.
2. Report ATS compatibility score out of 100.
3. Create tailored CV matching keywords and requirements.
4. Export as PDF.
5. Send PDF via Telegram.

Filename rules:
- Format: Ahmed Nasr - {Title} - {Company Name}
- Apply to both HTML and PDF files.
- Always use actual company name, not recruiter name.
- If company is confidential or unnamed, use: Ahmed Nasr - {Title}
- Title should match the job title exactly.

Examples:
- Ahmed Nasr - Senior Program Manager - Nabat.html
- Ahmed Nasr - Senior Program Manager - Nabat.pdf
- Ahmed Nasr - Director of Business Excellence - Equinix.html
- Ahmed Nasr - Director of Business Excellence - Equinix.pdf


## HR Application Approval Boundary, Confirmed 2026-06-02
- Standard job application submission is pre-approved when the approved HR/JobZoom workflow has enough known information. This includes ATS/job portals and application forms.
- Do not ask approval for routine application submission that fits Ahmed's confirmed role, salary, and personal-data rules.
- Ask Ahmed before replying to any email, even if the email is related to an application, recruiter process, form request, JD, or CV request.
- Ask Ahmed before sending recruiter/employer messages outside the ATS/job portal/application-form flow.
- Ask Ahmed if an application needs an unknown sensitive answer, MFA/OTP unavailable to the agent, a non-standard commitment, or salary/terms outside Ahmed's confirmed rules.

## CV Design Rules
Full ATS guide: `memory/ats-best-practices.md`

ATS-friendly requirements:
- No tables, multi-column layouts, text boxes, floating elements, headers, footers, images, icons, or graphics.
- No special bullet characters such as filled circles, arrows, or stars.
- Use single-column layout only.
- Use simple bullet lists.
- Use standard section headers: Professional Summary, Experience, Education, Skills, Certifications.
- Use reverse chronological order.
- Use consistent date format, for example MMM YYYY - Present.

Bullet writing:
- Every bullet should follow Action Verb + Value/What + Result/Metric.
- Good: Led digital transformation across 15-hospital network, managing $50M budget.
- Weak: Responsible for digital transformation projects.

Keyword strategy:
- Mirror exact JD phrases, not synonyms.
- Top 5 JD keywords should appear in Summary and the most recent role.
- Include acronyms and full terms, such as Project Management Professional (PMP).
- Critical keywords should appear 2-3x naturally.

## CV Creation Rule, Critical
Always read `memory/master-cv-data.md` before creating any CV. Never fabricate roles, titles, dates, or achievements. Use exact titles and dates from the master CV data.
All CV generation must use GPT-5.5 unless Ahmed explicitly changes that instruction. Do not silently use a fallback model for CV work.
- Before sending or regenerating any JobZoom CV pack, check `applied_jobs` and `jobs.applied` for each selected LinkedIn URL/ID. If already applied, report that status and do not resend CVs unless Ahmed explicitly asks for copies. <!-- dream-promoted 2026-05-17 -->
- JobZoom daily PDF policy, approved 2026-05-21: generate tailored PDF CVs for every main daily opportunity included in the report at `70+`. Label `82+` roles as application-ready and `70-81` roles as watchlist CVs that should not be applied to unless Ahmed approves. Do not generate CVs by default for suppressed below-70, older still-open, or already-applied roles unless Ahmed explicitly asks. <!-- approved from JobZoom enriched PDF review -->

## Verify Before Reporting, Non-Negotiable
Exit code 0 is not success. Subprocess ran is not success. API returned 200 is not proof that content is correct.

Before saying done or it worked:
1. Check the actual outcome, not just logs or exit code.
2. For Telegram, confirm the message reached the correct chat or thread.
3. For LinkedIn, confirm the full content posted correctly and was not truncated.
4. For scripts using the OpenClaw CLI, use --target, not --to.
5. When in doubt, quote actual output.

Specific gotcha: OpenClaw CLI uses --target for recipient. Using --to can fail silently.

## Task Board Rule, Historical
Previous workflow used Mission Control task logging at localhost:3001. Override from Ahmed on 2026-04-09: no more Mission Control.
- Do not log tasks to Mission Control.
- Do not treat localhost:3001 task-board failures as blockers.
- Only resume this workflow if Ahmed explicitly asks to re-enable it.

## Strategic Intelligence Framework, Optional
Activation only when Ahmed explicitly requests it with phrases like:
- use the framework
- think strategically about
- apply the 10-step system
- explicit request for multi-agent debate

Implementation:
- Quick strategic request: internal simulation.
- High-stakes complex work: spawn sub-agents for true debate.
- Routine tasks: skip framework and respond directly.

## Memory System Protocol
Session startup:
1. Read this file.
2. Check `memory/active-tasks.md`.
3. Read today's daily notes if they exist.

During session, write to daily notes immediately when:
- Something important is completed.
- A user preference is learned.
- A decision gets made.
- Something worth remembering happens.
- Pre-compaction memory flushes should append only to the canonical daily note path pattern memory/YYYY-MM-DD.md. Do not create timestamped variants or edit bootstrap/core files during flushes unless explicitly requested. <!-- dream-promoted 2026-05-18 -->

Finding things:
- Use memory search across all memory files.
- Use exact memory reads for specific sections.

Maintenance:
- Weekly: promote important daily notes here.
- Monthly: promote technical learnings to `TOOLS.md`.
- Quarterly: remove outdated content.

Principle: text beats brain. If it should be remembered, write it down.

Lessons learned log: `memory/lessons-learned.md`

## Service Credentials, Non-Negotiable
Before initiating any OAuth or Composio connection flow:
1. Stop. Do not generate auth links yet.
2. Check `config/service-registry.md`.
3. Check the `config/` directory for existing token files.
4. Grep workspace scripts for API calls to that service.
5. If credentials exist, use direct API. Never use Composio for Notion or Telegram.
6. Only if nothing is found, consider OAuth.

Known direct credentials:
- Notion: `config/notion.json`
- Telegram: direct Bot API tokens are documented in `config/service-registry.md` and scripts.
- Gmail: `/root/.config/gmail-smtp.json`
- HuggingFace: `config/huggingface.json`, client `scripts/huggingface-client.py`
- LinkedIn posting: Composio is required.
- LinkedIn browser automation: use cookies documented in the service registry when available.

## Key Files
Core memory:
- `MEMORY.md`
- `TOOLS.md`
- `USER.md`
- `memory/active-tasks.md`
- `memory/master-cv-data.md`
- `memory/ats-best-practices.md`

Config and credentials:
- `config/service-registry.md`
- `config/model-router.json`
- `config/notion.json`
- `config/notion-databases.json`
- `config/huggingface.json`
- `config/tavily.json`

Useful scripts and directories:
- Notion helper scripts if present in the scripts directory.
- `scripts/huggingface-client.py`
- `marketing-skills/`
- `docs/content-claw/caught/`

## Model Router and Gateway Notes
- Current primary model is GPT-5.5 via OpenAI Codex OAuth. See `USER.md` and `TOOLS.md` for current details.
- If Ahmed sets a model, do not revert it. Treat his model choice as final until he changes it.
- If GPT-5.5 fails, notify Ahmed immediately rather than silently switching models.
- After any gateway restart, verify `config/model-router.json` before doing model-sensitive work.
- MiniMax is retired and should not be used unless Ahmed explicitly asks.

## Standing Operations
- Resume normal operations: heartbeats, cron jobs, daily intel, job hunting, and content pipeline.
- Run a self-health-check every Sunday morning and post results to CEO General thread when that workflow is active.
- Slack pong timeouts can be monitored, but do not act unless they cause message drops.
