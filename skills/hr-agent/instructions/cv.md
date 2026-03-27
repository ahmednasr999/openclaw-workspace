# CV Creation — instructions/cv.md

## Source of Truth

| Asset | Path |
|---|---|
| Master CV data | `/root/.openclaw/workspace/memory/master-cv-data.md` |
| Master PDF reference | `/root/.openclaw/media/inbound/file_99---61a97145-01ba-402f-b33b-5915c31c8daf.pdf` |
| ATS best practices | `/root/.openclaw/workspace/memory/ats-best-practices.md` |

---

## Model Requirement

**CV creation MUST use Claude Opus 4.6 (`opus46`).** No exceptions.
- Before starting CV work, switch to Opus 4.6 via session_status(model="opus46")
- After CV is delivered, switch back to default model via session_status(model="default")
- This applies to: CV drafting, ATS scoring, cover letter generation
- Reason: CV quality directly impacts Ahmed's career — this is not a place to save tokens

---

## Trigger

CV creation ONLY starts when BOTH conditions are met:
1. Ahmed has provided a job link (URL or JD text)
2. Ahmed explicitly confirms: **"build CV"** (or equivalent: "make the CV", "create it", "go ahead")

Do NOT start building until both signals are present.

---

## Workflow (Step by Step)

### Step 1 — Load master data
```
READ /root/.openclaw/workspace/memory/master-cv-data.md
```
This is mandatory before any CV work. Never fabricate roles, titles, or achievements.

### Step 2 — Analyse the job
- Extract: job title, company name, key requirements, must-have keywords, preferred sector terms
- Identify ATS keywords to target (usually 8-12 critical terms)
- Score fit against master-cv-data (flag any gaps honestly)

### Step 3 — Draft the CV
**ATS compliance rules (non-negotiable):**
- Single-column layout only
- No tables, no text boxes, no columns, no headers/footers with key info
- No graphics, logos, or images
- Fonts: Arial or Calibri, 10-12pt body, 14-16pt name
- File format: PDF (WeasyPrint or equivalent)
- Section order: Summary → Core Competencies → Professional Experience → Education → Certifications
- Quantify achievements wherever possible (%, $, # headcount, timeframes)
- Mirror language from JD without keyword stuffing
- Keep to 2 pages maximum for Senior/Executive roles

### Step 4 — Output filename (strict format)
```
Ahmed Nasr - {Title} - {Company Name}.pdf
```
Examples:
- `Ahmed Nasr - VP Digital Transformation - SEHA.pdf`
- `Ahmed Nasr - Chief Digital Officer - Saudi Aramco.pdf`

### Step 5 — Quality check
Before delivering to Ahmed:
- [ ] No tables or columns in layout
- [ ] All quantified achievements verified against master-cv-data
- [ ] Company name and title match job posting exactly
- [ ] File named correctly
- [ ] PDF renders cleanly (no encoding artifacts)

### Step 6 — Deliver
- Send PDF to topic 9
- Add CV to Notion pipeline entry (attach file)
- Update job status: `Applied` → `CV Built`
- Log in ontology graph (Document entity linked to JobApplication entity)

---

## Boil the Lake (Last 10%)

After delivering CV, always include:
- **Cover letter draft** (optional but proactively offered)
- **ATS score estimate** vs the JD
- **Flag** if same company has competing roles worth applying to
- **Salary market rate** for the role in the target geography

---

## What NOT to Do

- Never fabricate a role, company, or achievement not in master-cv-data.md
- Never use a template from memory — always start from master data
- Never deliver without the PDF (Word/text only = incomplete)
- Never skip the filename convention
