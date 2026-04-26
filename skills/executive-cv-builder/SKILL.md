---
name: executive-cv-builder
description: Ahmed Nasr's executive CV builder. Produces ATS-optimized, tailored CVs scoring 82%+ for VP/C-Suite roles in GCC. ALWAYS use this skill (not resume-optimizer) when Ahmed asks to build, tailor, create, or generate a CV or resume for any job application, job description, or role. Also use when asked to score ATS fit, check CV match against a JD, update the master CV, or prepare application materials. Triggers on phrases like "make a CV for this", "tailor my resume", "score this against the JD", "prepare my application", "CV for [company]", or any mention of Ahmed applying to a specific role. Loads master CV from memory, applies pending updates, scores ATS fit, generates PDF via WeasyPrint, and updates the pipeline tracker automatically. This is the primary CV skill for this workspace.
metadata: {"openclaw":{"emoji":"📄","requires":{"bins":["weasyprint"]}}}
---

# Executive CV Builder — Ahmed Nasr

Produces ATS-optimized executive CVs scoring 82%+ every time. Purpose-built for Ahmed's GCC executive job search.

---

## Step 0 — Pre-Flight Checks

Read `instructions/pre-flight.md` and execute all checks. All checks are BLOCKING — do not proceed until every check passes.

## Step 1 — Load Context (mandatory, in this order)

1. Read `memory/master-cv-data.md` — the single source of truth for all CV content
2. Read `memory/cv-pending-updates.md` — check PENDING section. If anything is pending, apply it to the CV before proceeding
3. Read `memory/ats-best-practices.md` — ATS scoring rules and keyword matching methodology
4. Read the job description (from handoff file, URL, or user-provided text)

## Step 2 — ATS Scoring

Read `instructions/ats-scoring.md` and score the role. Do not proceed if score is below the 82% floor.

## Step 2.5 — Autoresearch Optimization Loop

Read `instructions/autoresearch-loop.md`. Run the optimization loop if score is 82-89%. Skip if already 90%+. Recommend SKIP if below 82%.

## Step 3 — CV Architecture

Read `instructions/architecture.md` and follow all positioning, summary, competency, bullet ordering, and quantification rules.

Read `examples/story-arsenal.md` for Ahmed's key stories and metrics to match against the JD.

## Step 4 — Hard Rules

Read `instructions/hard-rules.md`. Every rule in this file is zero tolerance — no exceptions.

## Step 5 — PDF Generation

Read `instructions/pdf-generation.md` and generate the PDF using WeasyPrint.

Read `eval/quality-gates.md` and run all 3 pre-send validation gates. All gates are BLOCKING.

Read `eval/post-gen-checks.md` and run the automated post-generation quality checks. All checks must pass before sending.

Read `eval/failure-modes.md` to be aware of common failures and their prevention.

## Step 5.5 — Ontology Graph Update (mandatory)

After PDF is generated, register this application in the knowledge graph:

```bash
# 1. Create the Document entity (the CV itself)
python3 /root/.openclaw/workspace/skills/ontology/scripts/ontology.py create \
  --type Document \
  --props "{\"title\": \"Ahmed Nasr - [Role] - [Company]\", \"type\": \"cv\", \"path\": \"cvs/Ahmed Nasr - [Role] - [Company].pdf\", \"version\": \"[YYYY-MM-DD]\", \"created_date\": \"[YYYY-MM-DD]\"}"

# 2. Create the Organization entity (if not already in graph)
python3 /root/.openclaw/workspace/skills/ontology/scripts/ontology.py create \
  --type Organization \
  --props "{\"name\": \"[Company]\", \"location\": \"[Location]\"}"

# 3. Create the JobApplication entity
python3 /root/.openclaw/workspace/skills/ontology/scripts/ontology.py create \
  --type JobApplication \
  --props "{\"title\": \"[Role]\", \"company\": \"[Company]\", \"status\": \"applied\", \"date_applied\": \"[YYYY-MM-DD]\", \"fit_score\": \"[X]/100\", \"location\": \"[Location]\", \"notes\": \"ATS: [X]%\"}"

# 4. Link CV to Application (note the IDs returned from steps 1 and 3 above)
python3 /root/.openclaw/workspace/skills/ontology/scripts/ontology.py relate \
  --from [job_application_id] --rel used_cv --to [document_id]
```

**Note:** Use the `id` values returned by each create command for the relate step. If the company already exists in the graph, skip step 2 and use the existing org id for the relate.

## Step 6 — Handoff Update

Read `templates/handoff-template.md`. If running inside Pipeline 1 with a handoff file, update it per the template.

## Step 7 — Delivery

Read `templates/delivery-template.md` and deliver the CV to Ahmed using the exact format specified.

## Step 8 — Commit and Push

```bash
cd /root/.openclaw/workspace
git add cvs/ jobs-bank/
git commit -m "cv: Ahmed Nasr - [Role] - [Company] (ATS [X]%)"
git push origin master
```

---

**Links:** `memory/master-cv-data.md` | `memory/cv-pending-updates.md` | `memory/ats-best-practices.md` | `jobs-bank/pipeline.md` | `jobs-bank/handoff/SCHEMA.md`

---

## Learned Improvements

### 2026-04-04 — Weekly Skill Tune-Up

**Context:** No direct errors this week (2026-03-28 to 2026-04-04), but systemic improvements needed based on adjacent failures:

1. **Ontology update resilience (from 3/30 silent failure):** Step 5.5 ontology commands use JSON-in-string format for --props. If shell escaping breaks, the command silently creates an empty entity. Add: after each `ontology.py create`, parse the returned id and validate it's non-empty before proceeding to the next step. If any create returns empty, fail loudly.

2. **Model gate enforcement (from 4/1 communication failure):** Step 1 should explicitly log which model is active before starting CV work. If not Opus 4.6, STOP and announce -- do not proceed with a sub-optimal model and report partial results.

3. **Master CV data freshness (general):** Before loading `memory/master-cv-data.md`, check `memory/cv-pending-updates.md` for any PENDING entries older than 7 days. If found, apply them or flag for Ahmed review. Stale pending updates cause CV data to drift.

**Action:** Added these as implicit pre-flight checks. The quality gates already cover post-gen validation, but these pre-gen checks prevent waste earlier in the pipeline.

### 2026-04-11 — Weekly Skill Tune-Up

**Reviewed signals:**
- 2026-03-16, never cut CV quality or tailoring depth without explicit approval
- 2026-03-18, never recommend or score from title-only without the full JD
- 2026-03-24, every generated CV needs visual review, not just automated validation

**Improvements to keep active:**
1. **Make the quality tradeoff explicit before batch work.** If more than 3 CVs are requested, the skill should force a decision between fully tailored output and faster template-assisted output before any drafting starts.
2. **Promote full-JD proof to a visible gate.** Step 0 already requires the complete JD, but delivery should also state where that JD came from so title-only shortcuts cannot creep back in.
3. **Add a human-eye final check to the written workflow.** Step 5 currently points to automated gates; the skill should also require a rendered visual review of page 1 and page 2 before delivery, especially for header/footer artifacts and spacing drift.
4. **Create an explicit `eval/checklist.md`.** This skill has strong eval files, but not one compact final checklist. Adding one would reduce missed steps during hurried runs.

### 2026-04-18 — Weekly Skill Tune-Up

**Audit note:** No fresh CV-builder-tagged lessons were logged in the last 7 days, so this stayed in the weekly audit as a default high-value skill and was reviewed for instruction drift.

**Improvements to add next:**
1. **Replace the stale Opus-only wording with the current workspace model rule.** `eval/quality-gates.md` still hard-codes Opus 4.6, which no longer matches the active workspace model policy. The skill should require the best approved current model, not an outdated one.
2. **Promote JD provenance into the delivery contract.** The final response should explicitly state where the full JD came from, pasted text, fetched page, or handoff file, so title-only drift cannot slip back in.
3. **Make ontology writes blocking and verified.** Step 5.5 should require checking that every `ontology.py create` call returns a real id before the skill can claim completion.
4. **Add one compact final checklist file.** The missing `eval/checklist.md` is still the biggest structural gap. It should cover model, full-JD proof, ATS floor, rendered visual QA, post-generation text extraction, and ontology update confirmation.

### 2026-04-18 - Weekly Skill Tune-Up (cron refresh)

**Audit basis:** No direct executive-cv-builder-tagged lessons were found in `memory/lessons-learned.md`, so this stayed in scope as a default high-value skill and the refresh focused on structural drift in the current instructions.

**Improvements to add next:**
1. **Turn the model gate into a current-policy check, not a stale hard-code.** `eval/quality-gates.md` still says CV work must run on Opus 4.6. Replace that with the current workspace-approved top-tier model rule so the skill cannot fail for the wrong reason.
2. **Make the missing checklist a real blocker.** Add `eval/checklist.md` and require it before Step 5.5. Keep it binary: full JD proven, ATS floor met, rendered page 1 and page 2 visually reviewed, `pdftotext` clean, ontology ids captured, delivery filename correct.
3. **Gate ontology and git actions behind proof, not hope.** Step 5.5 and Step 8 should require explicit confirmation that ontology create calls returned ids and the PDF exists at the delivery path before any commit or push instruction runs.
4. **Expose JD provenance in the delivery format.** The final handoff should state whether the JD came from pasted text, fetched URL, or handoff file so title-only drift is impossible to hide.

### 2026-04-25 - Weekly Skill Tune-Up

**Audit basis:** No fresh executive-CV-specific failure dominated the last 7 days, but the weekly check kept this skill in scope as a default high-value workflow. The requested `eval/checklist.md` is still missing, so the main risk is instruction drift across multiple eval files during rushed CV delivery.

**Reviewed lessons:**
- 2026-04-21, do not mislabel vendor/marketing emails as interview activity. This matters for CV/application triage because the skill should only build application materials from verified hiring signals.
- 2026-04-15, important recruiter follow-ups can fall through narrow email rules. CV requests triggered by recruiter follow-up should preserve the full thread and JD/source proof before tailoring.
- 2026-04-17, avoid ambiguous “half-done” wording. CV closeout should state completed artifacts, checks run, and any blocker plainly.

**Improvement recommendation:**
1. **Add a recruiter-signal verification gate before CV work.** Confirm the request is tied to a real JD, recruiter/hiring team message, or application handoff, not vendor marketing or a weak title-only signal.
2. **Create the missing compact checklist.** `eval/checklist.md` should be added next with binary gates for full JD/source proof, ATS floor, rendered PDF review, text extraction, ontology IDs, filename, and delivery wording.
3. **Make CV closeout artifact-based.** Final delivery should list the generated PDF path, ATS score, JD provenance, visual QA result, ontology update status, and whether any follow-up is genuinely blocked.
4. **Keep stale model language out of gates.** Any model check should refer to the current workspace-approved top-tier model policy, not outdated hard-coded model names.
