# Reactive Patterns Skill

Event-driven automation patterns for OpenClaw. Since we don't have native lifecycle hooks (PreToolUse, PostToolUse), we simulate them through webhook handlers and post-action chaining.

## When to Use
ALWAYS use these patterns when handling the triggering events below. These are automatic - don't ask Ahmed, just do them.

## Pattern 1: Recruiter Email Detected
**Trigger:** Gmail webhook delivers email from recruiter, hiring platform, or with subject containing "interview", "application", "opportunity", "role", "position", "CV", "resume"
**Auto-actions:**
1. Flag as 🔴 PRIORITY in notification
2. Extract: company name, role title, recruiter name, deadline (if any)
3. Check `jobs-bank/pipeline.md` - is this company/role already tracked?
4. If new: append to pipeline with status "Inbound" and date
5. If existing: update status with latest touchpoint

## Pattern 2: CV Created
**Trigger:** Any CV/resume file is generated (HTML or PDF) in workspace
**Auto-actions:**
1. Copy final PDF to `cvs/` directory
2. Move any working files to `cvs/in-progress/`
3. Update `jobs-bank/pipeline.md` with "CV Sent" status and filename
4. Log to `memory/cv-history.md` with date, company, role, filename

## Pattern 3: LinkedIn Post Published
**Trigger:** After successful `LINKEDIN_CREATE_LINKED_IN_POST` execution
**Auto-actions:**
1. Save post URN from response
2. Update content calendar (coordination/content-calendar.json) status to "Posted"
3. Log post date + topic to `memory/linkedin_content_calendar.md`
4. Schedule engagement check for +24h (if not already covered by Engagement Radar cron)

## Pattern 4: Job Application Submitted
**Trigger:** Ahmed says "I applied to X" or "submitted application for Y"
**Auto-actions:**
1. Update `jobs-bank/pipeline.md` - status → "Applied", add date
2. Create/update company dossier in `jobs-bank/dossiers/`
3. Set follow-up reminder for +7 days if no response
4. Log to daily notes

## Pattern 5: Interview Scheduled
**Trigger:** Ahmed shares interview details or calendar event detected
**Auto-actions:**
1. Update pipeline status → "Interview Scheduled"
2. Spawn parallel agents: company dossier refresh + role analysis + question prep
3. Create interview prep doc in `jobs-bank/applications/`
4. Set reminder for day-before prep review

## Pattern 6: File Cleanup After Session
**Trigger:** End of any session where files were created in workspace root
**Auto-actions:**
1. Check for orphan files in workspace root (CVs, temp files, test files)
2. Move CVs to `cvs/` or `archive/cvs/`
3. Move temp/test files to `tmp/`
4. Rebuild workspace index: `bash skills/workspace-index/generate-index.sh`

## Implementation Notes
- Patterns 1-3 are partially automated via webhooks and crons
- Patterns 4-6 rely on the agent recognizing triggers during conversation
- All patterns are SILENT - execute without asking unless there's ambiguity
- If a pattern conflicts with an explicit user instruction, user wins
