# MEMORY.md - Long-Term Memory Index

Full preserved history lives in `docs/reference/MEMORY.full.md`. This injected file keeps only current cross-workflow state not owned by `USER.md`, `AGENTS.md`, or `TOOLS.md`.

## Current Decisions

- Backups: keep only the latest, daily at 3 AM Cairo. Gmail check: daily at 8 AM Cairo.
- Use authenticated ChatGPT web Images when viable instead of adding direct OpenAI API billing solely for image generation.
- Telegram messages may use rich formatting when useful, but must remain readable as plain text when rich UI degrades.
- MiniMax is retired unless Ahmed explicitly asks for it.
- Normal operations remain active: heartbeats, cron, daily intel, job hunting, and content pipeline.
- Slack pong timeouts may be monitored without action unless they cause message loss.

## Job and CV Workflow

When Ahmed shares a job link and description: analyze requirements, report ATS score, tailor the CV, export PDF, and deliver it through the approved Telegram artifact path.

- Filename: `Ahmed Nasr - {Exact Job Title} - {Actual Company}.pdf`; omit company if confidential or unnamed.
- Read `memory/master-cv-data.md` and `memory/ats-best-practices.md` before creating a CV.
- Use a single-column ATS layout without tables, columns, graphics, text boxes, headers, or footers. Mirror exact JD phrases and use evidence-based action/result bullets.
- JobZoom daily PDFs: generate for main opportunities at 70+; label 82+ application-ready and 70-81 watchlist.
- Before regenerating or sending a JobZoom CV pack, check `applied_jobs` and `jobs.applied`; do not resend applied roles unless Ahmed asks.

## Content System

- The Content Pipeline is authoritative: Ideas, Outline, Draft, Design, Review, Published. OpenClaw moves completed drafts to Review; Ahmed moves approved work to Published.
- Default LinkedIn static visual: premium hand-drawn sketchnote on warm off-white paper, black ink, restrained orange accents, a toolkit/system metaphor, large handwritten headline, compact flow, and Ahmed Nasr signature/footer.
- Reference: `/root/.openclaw/workspace/media/inbound/234fe40d-96c3-4b4a-bf6f-dc1f75f91bbf.jpg`.
- Reel/video exception when explicitly requested: premium executive 9:16 dark visual system with restrained motion and `shift -> risk -> rule -> question` pacing.
- JobZoom executive-card reference: `/root/.openclaw/workspace/output/jobzoom-visuals/ahmed-linkedin-ai-execution-card-4k.jpg`.

## Memory Discipline

- At session start, read this file, then `memory/active-tasks.md` and today's daily note when relevant.
- Record important completions, decisions, preferences, and learnings in the current dated note under `memory/`.
- During pre-compaction flush, append only to that daily note unless Ahmed explicitly requests a core-file change.
- Lessons: `memory/lessons-learned.md`.

## Key Locations

- Service registry and credentials: `config/service-registry.md`
- Model router: `config/model-router.json`
- Notion: `config/notion.json`, `config/notion-databases.json`
- Tavily: `config/tavily.json`
- HuggingFace: `config/huggingface.json`
- Gmail: `/root/.config/gmail-smtp.json`
- GitHub: `/root/.config/gh/hosts.yml`

Before OAuth or connection work, check direct credentials and the service registry. Direct Notion and Telegram access take precedence over Composio. LinkedIn posting uses Composio and never exported cookies.

## Runtime Recovery Notes

- If GPT-5.6 Sol fails, notify Ahmed rather than silently switching.
- After an approved gateway restart or update, verify the router, version, plugins, cron, runtime patches, and Telegram path.
- Leave conflicting migrated plugin/dedupe metadata untouched without a specific recovery plan.
- Sunday self-health-checks may post to CEO General when that workflow is active.
