# Google Skills Adaptation Plan for OpenClaw

Date: 2026-05-13
Source reviewed: https://github.com/google/skills
Local analysis: reports/google-skills-repo-analysis.md

## Executive summary

Use Google's `google/skills` repository as a design reference, not as a direct install. The goal is to upgrade NASR/OpenClaw skills into smaller, safer, more modular, more verifiable capability packages.

The core shift:

- Current pattern: many skills and workflow rules are long, mixed with operational memory, and sometimes too broad.
- Target pattern: each skill has a concise `SKILL.md`, deeper `references/`, explicit validation checklists, tool preference order, approval boundaries, and failure recovery rules.

Priority should be HR/JobZoom and gateway/runtime skills first, because those have the highest recurring operational value and the clearest recent failure signals.

## Design principles to adopt

### 1. Progressive disclosure

Each skill should have three layers:

1. `SKILL.md`, short activation and workflow instructions.
2. `references/*.md`, deeper details used only when needed.
3. `checklists/*.md`, verification gates and acceptance criteria.

Do not put every detail in `SKILL.md`. The skill should tell the agent what to do and when to load supporting material.

### 2. Primary-source discipline

Every operational skill should name the source of truth.

Examples:

- JobZoom health: `workspace-jobzoom/jobzoom.db`, latest report PDF, generated CV artifacts.
- HR pipeline: HR DB and latest report, not memory guesses.
- Gateway config: `gateway config.schema.lookup`, then config read, then docs/source when needed.
- LinkedIn publishing: Notion/content source plus live duplicate check before publish.

Rule: query the primary source, answer from it, stop unless the result is weak or contradictory.

### 3. Tool preference order

Every operational skill should include a tool ladder:

1. First-class OpenClaw tool.
2. Existing safe wrapper script.
3. Small reusable wrapper if missing.
4. Shell only when necessary.
5. Approval-gated external/destructive/runtime action only when explicitly allowed.

This directly prevents approval noise and unsafe shell drift.

### 4. Validation before closeout

Every skill should define what "done" means.

Examples:

- CV generation done means PDF exists, opens/extracts text, filename is correct, ATS rules are respected, and delivery is verified.
- Gateway fix done means config/schema validated, service state verified, and user-visible behavior checked.
- JobZoom daily done means latest run, DB, report, CV ZIP, and delivery state agree.

### 5. Explicit approval boundaries

Every skill should declare what is pre-approved and what is not.

Pre-approved examples:

- Read-only inspection.
- Local reversible report generation.
- HR/JobZoom diagnostics.
- Drafting artifacts.

Approval required examples:

- Applications.
- Recruiter/employer messages.
- Public posts.
- Email sends.
- Paid actions.
- Credentials.
- Destructive deletes.
- Gateway/runtime changes unless explicitly approved.

## Target folder pattern

For each major workflow skill:

```text
skills/<skill-name>/
  SKILL.md
  references/
    sources-of-truth.md
    commands-and-tools.md
    schema-notes.md
    failure-modes.md
  checklists/
    preflight.md
    verification.md
    closeout.md
  examples/
    good-report.md
    bad-report.md
```

Not every skill needs all folders. Start with the workflows that have repeated use or repeated failures.

## Phase 0: Freeze current evidence

Goal: avoid changing behavior from vibes.

Actions:

1. Keep the Google repo analysis at:
   - `reports/google-skills-repo-analysis.md`
2. Create this plan at:
   - `plans/google-skills-adaptation-plan.md`
3. Do not install Google skills wholesale.
4. Do not alter gateway/global policy while skill refactors are in progress.

Acceptance criteria:

- Plan exists.
- Repo evidence is saved.
- No runtime/config changes made.

## Phase 1: Pick the first three OpenClaw skills to refactor

Recommended order:

### 1. HR / JobZoom operations

Why first:

- Recent approval-noise issue.
- Recurring daily workflow.
- Clear protected lane.
- Clear source-of-truth DB and artifacts.
- High user value.

Target skills/files:

- `/root/.openclaw/workspace-hr/skills/hr-agent/SKILL.md`
- `/root/.openclaw/workspace-hr/skills/hr-agent/SOUL.md`
- `/root/.openclaw/workspace-hr/tools/README.md`
- Potential new references/checklists under HR skill folder.

### 2. Gateway/runtime safety

Why second:

- High-risk operational lane.
- Needs strict schema-first behavior.
- Strong benefit from validation checklists.

Target likely existing areas:

- Gateway docs/rules in `SOUL.md`, `TOOLS.md`, and governance docs.
- Potential new skill or refactor if a gateway skill already exists.

### 3. LinkedIn/content publishing

Why third:

- Public-facing reputation risk.
- Repeated quality gates around visuals, duplicate prevention, and approval boundaries.

Target likely existing skills:

- `content-claw`
- CMO workspace skill files
- LinkedIn posting references in `TOOLS.md`

Acceptance criteria:

- We have a ranked list of three skills.
- Each has owner, source of truth, approval boundary, and verification gate.

## Phase 2: Refactor HR/JobZoom skill first

### Proposed HR/JobZoom skill structure

```text
/root/.openclaw/workspace-hr/skills/hr-agent/
  SKILL.md
  SOUL.md
  references/
    sources-of-truth.md
    safe-toolbox.md
    jobzoom-db-schema.md
    artifact-locations.md
    approval-boundaries.md
  checklists/
    daily-jobzoom-verification.md
    cv-generation-verification.md
    application-readiness.md
    approval-noise-prevention.md
  examples/
    daily-report-good.md
    escalation-good.md
```

### HR/JobZoom `SKILL.md` target content

Keep concise:

- Identity and domain lock.
- Trigger conditions.
- Workflow index.
- Source-of-truth rule.
- Safe-tool-first rule.
- Approval boundaries.
- When to load each reference/checklist.

Move long details out.

### New reference docs

#### `references/sources-of-truth.md`

Should define:

- HR workspace root.
- JobZoom workspace root.
- JobZoom DB path.
- Daily PDF/report paths.
- CV artifact paths.
- Pipeline DB paths.
- Master CV source.
- ATS guide source.

#### `references/safe-toolbox.md`

Should define:

- Approved wrappers:
  - `hr-status.py`
  - `jobzoom-latest-run.py`
  - `cv-artifact-verify.py`
  - `list-safe-files.py`
  - `show-safe-file.py`
- When to create a new wrapper.
- Prohibited routine command shapes:
  - `sed`
  - `awk`
  - `python -c`
  - `node -e`
  - shell pipelines for routine inspection.

#### `references/jobzoom-db-schema.md`

Should capture known columns:

- `runs.run_date`
- `runs.start_time`
- `runs.end_time`
- `runs.raw_jobs_found`
- `runs.successful_searches`
- `runs.failed_searches`
- `runs.after_dedup`
- `runs.after_pass1`
- `runs.after_pass2`
- `jobs.pass1_match`
- `jobs.pass2_score`
- `jobs.cv_generated`
- `jobs.search_title`
- `jobs.search_country`
- `gpt_api_calls.phase`
- `gpt_api_calls.created_at`

Also record schema gotchas:

- Do not assume `jobs_found`.
- Do not assume `eligible_after_exclusions`.
- Do not assume generic `started_at`.

#### `references/approval-boundaries.md`

Should define:

Pre-approved:

- Job scans.
- Diagnostics.
- Report generation.
- CV drafting/generation.
- Artifact verification.
- Telegram delivery to Ahmed inside protected lane.

Approval required:

- Actual applications.
- Recruiter/employer messages.
- Email sends.
- Public posts.
- Paid actions.
- Credentials.
- Destructive deletes.
- Gateway/runtime changes.

### New checklists

#### `checklists/daily-jobzoom-verification.md`

Minimum verification before reporting JobZoom daily status:

1. Confirm latest run date and run id.
2. Confirm successful vs failed searches.
3. Confirm funnel counts.
4. Confirm AI scoring health.
5. Confirm report PDF exists and is non-empty.
6. Confirm generated CVs exist and are non-empty.
7. Confirm ZIP exists if expected.
8. Confirm delivery status.
9. Classify result quality, not just operational success.

#### `checklists/cv-generation-verification.md`

Minimum verification before saying a CV is ready:

1. Master CV was read.
2. Job description was analyzed.
3. ATS score was estimated.
4. Filename matches rule.
5. PDF exists.
6. PDF text extracts cleanly.
7. No fabricated roles/credentials/achievements.
8. Artifact delivered or staged as requested.

#### `checklists/approval-noise-prevention.md`

Before running shell:

1. Can a first-class tool do this?
2. Can an existing safe wrapper do this?
3. Is this command a pipeline or inline eval?
4. If repeatable, should we write a wrapper instead?
5. If approval prompt appears for routine diagnostics, stop and switch to wrapper.

Acceptance criteria:

- HR skill shorter and clearer.
- References/checklists exist.
- Existing HR safe wrappers are documented.
- A routine JobZoom status check can be performed without approval noise.

## Phase 3: Refactor gateway/runtime skill

### Target structure

```text
skills/gateway-runtime-safety/
  SKILL.md
  references/
    config-schema-first.md
    service-lifecycle.md
    model-router.md
    runtime-patches.md
    failure-modes.md
  checklists/
    config-change-preflight.md
    restart-preflight.md
    update-preflight.md
    post-change-verification.md
```

### Core behavior

- Use `gateway config.schema.lookup` before config edits.
- Use `gateway config.patch` or `gateway config.apply`, not direct file edits.
- Use `gateway restart`, not CLI stop/start, unless explicitly requested.
- Before update, confirm explicit user request.
- Before runtime/config change, verify active binary/version and service path where needed.

### Acceptance criteria

- Gateway work has one canonical checklist.
- No casual restart behavior.
- Every config change has schema evidence and verification evidence.

## Phase 4: Refactor LinkedIn/content skill

### Target structure

```text
skills/content-publishing/
  SKILL.md
  references/
    linkedin-posting.md
    visual-quality.md
    notion-content-calendar.md
    duplicate-prevention.md
  checklists/
    pre-publish.md
    image-post-quality.md
    post-publish-verification.md
```

### Core behavior

- Never post text-only when image expected.
- Verify content source and approval state.
- Verify media quality before publishing.
- Upload image correctly and use true `s3key`.
- Check live state/local logs before retrying publish.
- Confirm post is live and not truncated.

### Acceptance criteria

- Public-posting risk is explicit.
- Duplicate prevention is checklist-driven.
- Visual quality gate is enforceable.

## Phase 5: Add skill quality linting

Create a lightweight local checker for skill hygiene.

Potential script:

`/root/.openclaw/workspace/scripts/check-skill-quality.py`

Checks:

- `SKILL.md` exists.
- Frontmatter has `name` and `description`.
- Description is specific and triggerable.
- Skill has source-of-truth guidance if operational.
- Skill has approval boundaries if it can write externally or change runtime.
- Skill has verification checklist if it produces artifacts or changes state.
- No huge all-in-one `SKILL.md` unless justified.
- References/checklists paths exist if mentioned.

Acceptance criteria:

- Run checker on selected skills.
- Output clear warnings, not hard failures at first.
- Add to manual maintenance workflow before making it automated.

## Phase 6: Build an OpenClaw skill template

Create template:

```text
templates/openclaw-skill-template/
  SKILL.md
  references/sources-of-truth.md
  references/tools-and-fallbacks.md
  references/approval-boundaries.md
  checklists/preflight.md
  checklists/verification.md
  examples/good-closeout.md
```

The template should encode NASR rules:

- outcome first
- source-of-truth first
- safe tool first
- approval gates explicit
- verify before closeout
- no public/external action without approval
- no em dashes

Acceptance criteria:

- New skills can be generated from the template.
- Existing skills can be migrated gradually.

## Phase 7: Pilot and measure

Pilot on HR/JobZoom for one week.

Measures:

- Approval prompts caused by routine HR diagnostics.
- Number of times HR uses safe wrappers instead of shell pipelines.
- Daily JobZoom report quality.
- Whether generated CV choices improve after calibration.
- User corrections or repeated asks.

Expected outcome:

- Fewer approval interruptions.
- More consistent closeouts.
- Less duplicated context in skill files.
- Faster debugging because references are easier to locate.

## Proposed implementation sequence

### Day 1

- Create HR/JobZoom `references/` and `checklists/`.
- Move existing rules from long files into focused references.
- Keep behavior unchanged except clearer routing.

### Day 2

- Add gateway/runtime safety skill or refactor existing gateway guidance into modular docs.
- Add config/restart/update checklists.

### Day 3

- Add LinkedIn/content publishing checklists.
- Align with existing content-claw quality gate.

### Day 4

- Create skill quality checker.
- Run it manually and fix high-signal warnings.

### Day 5

- Create reusable OpenClaw skill template.
- Document migration pattern.

### Days 6-7

- Observe HR/JobZoom and gateway use.
- Capture approval-noise misses and closeout quality misses.
- Adjust only where evidence shows friction.

## Risks and controls

### Risk: over-refactoring skills into bureaucracy

Control:

- Refactor only skills with repeated use or repeated failures.
- Keep `SKILL.md` short.
- Do not create checklists for one-off tasks.

### Risk: breaking existing skill trigger behavior

Control:

- Preserve current skill names and descriptions unless improving trigger accuracy deliberately.
- Change one skill at a time.
- Verify with a dry-run task.

### Risk: weakening approval boundaries accidentally

Control:

- Treat approval-boundary docs as explicit safety surfaces.
- Never change gateway permission policy as part of skill cleanup.
- Keep external/runtime/destructive actions approval-gated.

### Risk: importing Google assumptions that do not fit OpenClaw

Control:

- Do not install wholesale.
- Translate patterns, not commands.
- Replace MCP-first assumptions with OpenClaw first-class tools and safe wrappers.

## Immediate next action

Start with HR/JobZoom because it has the clearest recent pain and measurable outcome.

First implementation task:

1. Create HR references/checklists folders.
2. Add source-of-truth, safe-toolbox, approval-boundary, and JobZoom verification docs.
3. Update HR `SKILL.md` to point to these docs without expanding it further.
4. Run `hr-status.py` and `jobzoom-latest-run.py` as the verification gate.
5. Report changed files and evidence.
