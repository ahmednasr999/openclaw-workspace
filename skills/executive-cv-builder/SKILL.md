---
name: executive-cv-builder
description: Ahmed Nasr's executive CV builder. Produces ATS-optimized, tailored CVs scoring 82%+ for VP/C-Suite roles in GCC. ALWAYS use this skill (not resume-optimizer) when Ahmed asks to build, tailor, create, or generate a CV or resume for any job application, job description, or role. Also use when asked to score ATS fit, check CV match against a JD, update the master CV, or prepare application materials. Triggers on phrases like "make a CV for this", "tailor my resume", "score this against the JD", "prepare my application", "CV for [company]", or any mention of Ahmed applying to a specific role. Loads master CV from memory, applies pending updates, scores ATS fit, generates PDF via WeasyPrint, and updates the pipeline tracker automatically. This is the primary CV skill for this workspace.
metadata:
  author: Ahmed Nasr <ahmednasr999@gmail.com>
  openclaw:
    emoji: "📄"
    requires:
      bins:
        - weasyprint
---

# Executive CV Builder — Ahmed Nasr

Produces ATS-optimized executive CVs scoring 82%+ every time. Purpose-built for Ahmed's GCC executive job search.

Model policy: CV creation must use `openai/gpt-5.6-sol` with high reasoning. Do not use another model unless Ahmed explicitly changes the rule in the current task.

## Critical visible stop contracts

These safety decisions must appear in the user-visible response exactly and completely, even when Ahmed asks for “the decision only”:

- Below 82%: `The verified [X]% fit is below the 82% floor. SKIP. Do not generate the CV. Do not add unsupported facts or invent evidence to raise the score.`
- PDF generated without verified submission or delivery: `HOLD. This opportunity is not applied. Keep status cv_ready and omit date_applied. Do not mutate the ontology or ledgers, commit, push, or send anything. Mark applied only after verified proof of submission or CV delivery.`
- Existing PDF and both applied-job ledgers already show applied: `HOLD. The applied-ledger exclusion gate is active. Do not regenerate. Do not resend. Proceed only for a specific exception explicitly approved by Ahmed.`

---

## Step 0 — Pre-Flight Checks

Read `instructions/pre-flight.md` and execute all checks. All checks are BLOCKING — do not proceed until every check passes.

If the complete JD or another required source is missing, explicitly refuse to infer requirements or fabricate achievements, metrics, titles, keywords, or evidence. Block scoring and CV generation until the source is available.

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

Read `eval/checklist.md` and block delivery until every item is checked **YES**.

## Step 5.5 — Ontology Graph Update (mandatory after generation, submission-safe)

After the PDF is generated, register the artifact and opportunity in the knowledge graph without falsely recording an application. PDF generation means `cv_ready`, not `applied`; omit `date_applied` until a real submission is verified.

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
  --props "{\"title\": \"[Role]\", \"company\": \"[Company]\", \"status\": \"cv_ready\", \"fit_score\": \"[X]/100\", \"location\": \"[Location]\", \"notes\": \"ATS: [X]%; tailored CV generated, application not yet verified as submitted\"}"

# 4. Link CV to Application (note the IDs returned from steps 1 and 3 above)
python3 /root/.openclaw/workspace/skills/ontology/scripts/ontology.py relate \
  --from [job_application_id] --rel used_cv --to [document_id]
```

**Submission boundary:** Do not mark or create the JobApplication as `applied`, and do not set `date_applied`, unless the submission workflow has visible proof that the application was submitted or the CV was sent. Only after that proof may the application workflow transition the record to `applied`, add the verified submission date, and update the permanent applied-job ledgers. For planning-only requests or instructions that prohibit operational tools, perform no ontology, ledger, Git, delivery, or external write.

**Verification note:** Use the `id` values returned by each create command for the relate step and verify every returned id is non-empty before continuing. If the company already exists in the graph, skip step 2 and use the existing organization id. Fail closed on an empty id; never claim the graph update succeeded.

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

## Maintenance history

Read `references/learned-improvements-history.md` only when maintaining or evaluating this skill. Do not load it during normal CV scoring, generation, or delivery.
