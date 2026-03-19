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
