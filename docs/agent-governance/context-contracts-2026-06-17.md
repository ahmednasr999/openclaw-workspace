# OpenClaw Context Contracts - 2026-06-17

Purpose: reduce context drift in long workflows by defining what each lane may read, remember, ignore, verify, and carry forward.

This is not a new agent layer. It is a control layer for the workflows we already depend on.

## Contract Standard

Every long workflow must define:

- Objective: the outcome, not the activity.
- Required sources: evidence that must be inspected before action.
- Allowed memory: durable context that may influence the work.
- Ignored context: stale or adjacent data that must not steer the run.
- Approval boundary: what the agent may do without Ahmed.
- Verification gate: the real outcome that must be inspected before closeout.
- Handoff packet: exact details that must survive compaction or delegation.
- Stop rule: when to stop instead of adding more tool calls.

Critical failure conditions:

- Acting from a summary when the source artifact is available and material.
- Treating a tool exit code, API 200, file existence, or generated artifact as completion.
- Letting old active tasks, old reports, or unrelated lane memory alter the current workflow.
- Crossing an external, public, paid, credential, destructive, or runtime boundary without approval.

## Workflow Contracts

### JobZoom Daily Lane

- Owner: HR / JobZoom.
- Objective: surface real GCC executive opportunities, score them, generate correct artifacts, and avoid duplicate applications.
- Required sources:
  - Latest JobZoom run DB/report in `/root/.openclaw/workspace-jobzoom`.
  - `memory/master-cv-data.md` before any CV creation.
  - `memory/ats-best-practices.md` before ATS/CV scoring or tailoring.
  - Applied ledger and `jobs.applied` state before generating or sending CV packs.
- Allowed memory:
  - Ahmed's role, salary, relocation, personal-data, and application rules from `MEMORY.md` and `USER.md`.
  - Confirmed HR pipeline facts and application locks.
- Ignored context:
  - Old role preferences that conflict with current salary-first GCC rules.
  - Prior daily report conclusions unless the current run evidence confirms them.
  - Unverified job alerts, recruiter names, or scraped snippets without a job source.
- Approval boundary:
  - Pre-approved: scans, scoring, diagnostics, CV/report generation, artifact verification, standard ATS/application-form submissions when known data is sufficient.
  - Ask first: email replies, recruiter/employer messages outside forms, unknown sensitive answers, MFA/OTP, salary/terms outside confirmed rules, paid actions, credential changes, destructive deletes, runtime changes.
- Verification gate:
  - Inspect the latest run state, selected job records, applied ledger, generated PDFs, and report delivery state.
  - A CV exists only after its content and filename are checked against the actual company/title.
- Handoff packet:
  - Run date/id, DB/report path, selected jobs, ATS scores, CV paths, applied/excluded URLs, blockers, next action.
- Stop rule:
  - Stop when every selected role is classified as application-ready, watchlist, already-applied, blocked, or rejected with evidence.

### CMO Content Lane

- Owner: CMO.
- Objective: move executive content from idea/draft/design/review to approved publishing without duplicates or weak visuals.
- Required sources:
  - Current content pipeline/calendar state.
  - Latest generated draft or visual artifact.
  - LinkedIn duplicate/posting logs before publish.
  - Relevant brand and content safety docs for public posts.
- Allowed memory:
  - Ahmed's executive positioning, LinkedIn tone, approved visual style, and posting rules.
  - Prior approved content only as style/context, not as proof of today's readiness.
- Ignored context:
  - Old content drafts outside the current pipeline item.
  - Generic social media advice that conflicts with Ahmed's executive voice.
  - Tool claims that an image or post is done before visual/text inspection.
- Approval boundary:
  - Pre-approved: draft, redesign, quality review, pipeline/local report updates.
  - Ask first: public posting unless Ahmed directly requested that specific post or it was already approved for publishing.
- Verification gate:
  - Inspect final text, media, duplicate state, and actual published LinkedIn content when publishing occurs.
  - Never close a visual task from generation success alone.
- Handoff packet:
  - Pipeline item, draft path/text, visual path, quality verdict, duplicate check result, approval state, publish state.
- Stop rule:
  - Stop when the item is in Review with verified assets, or Published with the live post inspected.

### Email Scan Lane

- Owner: CEO/NASR or HR depending on classification.
- Objective: interrupt Ahmed only for email that requires action, especially interview invites or recruiter screens.
- Required sources:
  - Full email body for any candidate alert, not subject line only.
  - Sender, date, thread context, and attachments where relevant.
  - Existing application/job pipeline state when the email is job-related.
- Allowed memory:
  - Job-email classification rules and Ahmed's HR/application preferences.
  - Known companies, applications, recruiters, and pending follow-ups.
- Ignored context:
  - Marketing/newsletter language that looks urgent but has no action.
  - Keyword hits without body confirmation.
  - Old classifications if the current email body contradicts them.
- Approval boundary:
  - Pre-approved: classify, summarize, draft safe reply, update local state.
  - Ask first: sending email, external replies, commitments, salary/terms, MFA/OTP, credential changes.
- Verification gate:
  - Body-read classification into interview invite, recruiter screen, acknowledgement, job alert, rejection, newsletter/noise.
  - Critical label only when Ahmed needs to act.
- Handoff packet:
  - Message id/thread id, sender, classification, why it matters, recommended action, draft if any, approval needed.
- Stop rule:
  - Stop when all new emails are classified and only actionable items are surfaced.

### Gateway Maintenance Lane

- Owner: CTO.
- Objective: keep OpenClaw healthy while avoiding avoidable runtime breakage.
- Required sources:
  - Current version, active binary, service path, config validation, gateway status/probe.
  - Relevant release notes or CLI help for update/config-sensitive actions.
  - Backup manifest before any update/config write.
  - Post-change verification report.
- Allowed memory:
  - Current model preference, runtime safety rules, known warnings, active patches, service topology.
- Ignored context:
  - Old gateway incident conclusions unless current live evidence confirms them.
  - Generic doctor/fix recommendations when there are known conflicting migration states.
  - Desire to clean warnings when runtime is healthy and cleanup risk is higher.
- Approval boundary:
  - Pre-approved: read-only checks, diagnostics, report generation.
  - Ask first: updates, config writes, restarts, service lifecycle changes, credential changes, destructive cleanup, public exposure changes.
- Verification gate:
  - Confirm live gateway version/status, Telegram path, config, model routing, plugins, cron, runtime patches, and user-visible delivery when relevant.
- Handoff packet:
  - Requested action, approval evidence, backup path, commands/actions run, changed paths, verification results, warnings left alone, rollback option.
- Stop rule:
  - Stop when the requested state is verified or a specific risk boundary requires Ahmed approval.

## Promotion Rule

Do not promote these contracts into core prompt files until they pass at least two real workflow runs without causing extra noise. If a contract prevents a failure, promote the smallest durable rule into the owning skill, AGENTS.md, or TOOLS.md.
