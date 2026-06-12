# MEMORY.md - Long-Term Memory

Full preserved snapshot lives in `docs/reference/MEMORY.full.md`. Keep this root file compact because it is injected into every turn.

## Core Preferences

- Timezone: Cairo, Africa/Cairo.
- Call the user Ahmed; pronouns he/him.
- Relocation: open to Jeddah, Saudi Arabia.
- Formatting: never use em dashes. Use commas or hyphens.
- LinkedIn posts should end with a question or CTA when appropriate.
- Backups: keep only the latest backup, daily at 3 AM Cairo.
- Gmail check: daily at 8 AM Cairo.
- Current default model is GPT-5.5 via OpenAI Codex OAuth. Do not silently switch models. Disclose any model switch immediately.
- ChatGPT subscription: Ahmed returned to ChatGPT Pro 20x on 2026-05-30. Treat GPT-5.5 headroom as 20x unless Ahmed changes it.
- Image generation cost preference: do not add direct OpenAI API billing just to unlock image generation if authenticated ChatGPT web Images workaround is viable.

## Strategy and Decision Rules

- Ahmed wants strategic judgment, direct answers, honest trade-offs, and end-to-end execution.
- Salary is the overriding factor for GCC executive roles unless Ahmed explicitly adds another hard filter.
- Minimum monthly total-package baselines: UAE AED 55,000; Saudi about SAR 56,000; Qatar about QAR 55,000; Oman about OMR 5,750; Bahrain about BHD 5,650; Kuwait about KWD 4,600.
- Reporting line and work arrangement are not hard filters if salary is high enough.
- For salary-expectation fields, use AED 55,000/month minimum and convert to local currency, rounded conservatively upward.
- Serious agent/coding/automation work should use `research -> plan -> execute -> verify`, a short plan artifact when substantial, one clear owner for parallel agents, raw evidence before summaries, `repeat twice -> system`, and human approval before external-impact actions. Do not adopt broad YOLO/permission-skipping advice.

## Job Search and Applications

Trigger: Ahmed shares a job link and description.
1. Analyze requirements.
2. Report ATS compatibility score out of 100.
3. Create tailored CV matching keywords and requirements.
4. Export PDF.
5. Send PDF via Telegram when appropriate.

Filename format: `Ahmed Nasr - {Title} - {Company Name}.pdf`. Use the actual company name, not recruiter name. If confidential/unnamed, use `Ahmed Nasr - {Title}`. Title should match the job title exactly.

Standard job application submission is pre-approved when the HR/JobZoom workflow has enough known information and Ahmed's confirmed role, salary, and personal-data rules are satisfied. Ask before email replies, recruiter/employer messages outside application forms, unknown sensitive answers, MFA/OTP, non-standard commitments, or salary/terms outside confirmed rules.

Confirmed reusable application defaults: date of birth 28/12/1983 (ISO 1983-12-28), marital status married, address UAE, Dubai, Bursha. Ahmed approved creating ATS/candidate accounts with his email when needed for job applications.

## CV Rules

- Always read `memory/master-cv-data.md` before creating any CV.
- Never fabricate roles, titles, credentials, achievements, dates, or metrics.
- ATS guide: `memory/ats-best-practices.md`.
- ATS-friendly CVs: no tables, multi-column layouts, text boxes, floating elements, headers, footers, images, icons, or graphics.
- Use single-column layout, simple bullet lists, standard section headers, reverse chronological order, and consistent dates.
- Bullets should follow Action Verb + Value/What + Result/Metric.
- Mirror exact JD phrases. Top JD keywords should appear in Summary and recent role. Include acronyms and full terms.
- JobZoom daily PDF policy: generate tailored PDF CVs for every main daily opportunity at `70+`; label `82+` as application-ready and `70-81` as watchlist CVs.
- Before sending/regenerating a JobZoom CV pack, check `applied_jobs` and `jobs.applied`; if already applied, report status and do not resend unless Ahmed asks.

## Content and LinkedIn

- Content Pipeline is the work; Task Board is only tracking. Pipeline columns: Ideas, Outline, Draft, Design, Review, Published. OpenClaw creates draft and moves to Review; Ahmed moves to Published when ready.
- LinkedIn reel style: premium, executive, concise, cinematic, 9:16, dark executive visual system, clean typography, glass-card treatment, subtle motion, restrained gradient, shift -> risk -> rule -> question pacing.
- Default Ahmed LinkedIn visual: `/root/.openclaw/workspace/output/jobzoom-visuals/ahmed-linkedin-ai-execution-card-4k.jpg`.
- Required visual style: 9:16 dark executive card, bold mobile-readable hook hierarchy, blue/gold accent system, execution/governance visual language, Ahmed-branded footer. Reject generic, flat, stock-like, under-designed, weak typography/depth, or weak execution metaphor.
- LinkedIn posting/image workflows require content/media quality checks and duplicate checks before publishing. Never post text-only when image was expected.

## Verify Before Reporting

Exit code 0, subprocess completion, file creation, tool success, generated media, monitoring, or API 200 is not proof.

Before saying done:
1. Check the actual outcome, not just logs.
2. For Telegram, confirm message reached the correct chat/thread or rely only on the current final reply path.
3. For LinkedIn, confirm full content posted correctly and was not truncated.
4. For OpenClaw CLI messages, use `--target`, not `--to`.
5. When uncertain, quote actual output and name residual risk.

## Runtime and Model Notes

- Primary model/router default: GPT-5.5 via OpenAI Codex OAuth.
- If GPT-5.5 fails, notify Ahmed immediately rather than silently switching.
- After gateway restart/update, verify `config/model-router.json`, gateway version, plugins, cron, runtime patches, and Telegram path before closeout.
- MiniMax is retired unless Ahmed explicitly asks.
- Do not modify JobZoom prompts/files unless the current task is explicitly JobZoom-related.
- Leave legacy plugin/dedupe state alone when OpenClaw reports conflicting migrated metadata unless there is a specific recovery plan.

## Memory and Knowledge

Session startup:
1. Read this file.
2. Check `memory/active-tasks.md` when relevant.
3. Read today's daily notes if relevant.

Write daily notes immediately when something important is completed, a user preference is learned, a decision is made, or something worth remembering happens. Pre-compaction memory flushes should append only to `memory/YYYY-MM-DD.md`; do not create timestamped variants or edit core files during flush unless explicitly requested.

Maintenance principle: text beats brain. If it should be remembered, write it down. Lessons log: `memory/lessons-learned.md`.

## Credentials and Key Files

Before OAuth/connection flows, check direct credentials and service registry first. Never use Composio for Notion or Telegram when direct credentials exist.

Known direct credentials:
- Notion: `config/notion.json`
- Telegram: direct Bot API tokens in `config/service-registry.md` and scripts
- Gmail: `/root/.config/gmail-smtp.json`
- GitHub: `/root/.config/gh/hosts.yml`
- HuggingFace: `config/huggingface.json`, client `scripts/huggingface-client.py`
- LinkedIn posting: Composio is required; do not use LinkedIn cookies for posting, engagement, scraping, or recovery.

Core files:
- `MEMORY.md`, `TOOLS.md`, `USER.md`, `SOUL.md`, `AGENTS.md`
- `memory/active-tasks.md`, `memory/master-cv-data.md`, `memory/ats-best-practices.md`
- `config/service-registry.md`, `config/model-router.json`, `config/notion.json`, `config/notion-databases.json`, `config/huggingface.json`, `config/tavily.json`

## Standing Operations

- Resume normal operations: heartbeats, cron jobs, daily intel, job hunting, and content pipeline.
- Run self-health-check every Sunday morning and post results to CEO General thread when that workflow is active.
- Slack pong timeouts can be monitored, but do not act unless they cause message drops.
- Mission Control task logging is retired. Only resume if Ahmed explicitly asks.
