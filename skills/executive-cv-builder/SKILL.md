---
name: executive-cv-builder
description: Ahmed Nasr's executive CV builder. Produces ATS-optimized, tailored CVs scoring 82%+ for VP/C-Suite roles in GCC. ALWAYS use this skill (not resume-optimizer) when Ahmed asks to build, tailor, create, or generate a CV or resume for any job application, job description, or role. Also use when asked to score ATS fit, check CV match against a JD, update the master CV, or prepare application materials. Triggers on phrases like "make a CV for this", "tailor my resume", "score this against the JD", "prepare my application", "CV for [company]", or any mention of Ahmed applying to a specific role. Loads master CV from memory, applies pending updates, scores ATS fit, generates PDF via WeasyPrint, and updates the pipeline tracker automatically. This is the primary CV skill for this workspace.
metadata: {"openclaw":{"emoji":"📄","requires":{"bins":["weasyprint"]}}}
---

# Executive CV Builder — Ahmed Nasr

Produces ATS-optimized executive CVs scoring 82%+ every time. Purpose-built for Ahmed's GCC executive job search.

---

## Step 0 — Pre-Flight Checks (BLOCKING, before any CV work)

1. **Model check:** Verify you are running on **Opus 4.6** (opus46). If not, STOP. Either switch to Opus or spawn a sub-agent on opus46. Never generate a CV on any other model. Zero exceptions.
2. **Full JD check:** Do you have the COMPLETE job description? If Ahmed only shared a LinkedIn URL or job title, fetch the full JD first using `scripts/linkedin-jd-fetcher.py` or ask Ahmed to paste it. Never score or build a CV from title/summary alone (learned from Anduril incident: title said 85%, full JD revealed 64%).
3. **Duplicate check:** Search `cvs/` directory for existing CV for this company/role. If found, confirm with Ahmed before rebuilding.

## Step 1 — Load Context (mandatory, in this order)

1. Read `memory/master-cv-data.md` — the single source of truth for all CV content
2. Read `memory/cv-pending-updates.md` — check PENDING section. If anything is pending, apply it to the CV before proceeding
3. Read `memory/ats-best-practices.md` — ATS scoring rules and keyword matching methodology
4. Read the job description (from handoff file, URL, or user-provided text)

---

## Step 2 — ATS Scoring

Score the role against Ahmed's profile before writing a single word:

| Category | Weight | What to check |
|---|---|---|
| Keyword match | 35% | JD keywords present in master CV? |
| Seniority alignment | 20% | Role level matches 20yr exec profile? |
| Sector fit | 20% | FinTech / HealthTech / DT / AI / PMO? |
| Location match | 15% | GCC (UAE, KSA, Qatar, Bahrain, Kuwait, Oman)? |
| Skills coverage | 10% | Technical + leadership skills covered? |

**Floor: 82% ATS score required. Do not proceed below this threshold.**

If ATS < 82%: explain the gap, recommend Skip, do NOT build CV.

---

## Step 2.5 — Autoresearch Optimization Loop (NEW)

After ATS scoring in Step 2, if the score is between 82-89%, run the autoresearch loop to push it to 90%+:

1. Read the full autoresearch prompt: `scripts/cv-autoresearch.md`
2. Run the loop: baseline → identify gaps → make ONE atomic change → re-score → keep/revert → repeat
3. Max 10 iterations, stop at 90%+ or after 5 consecutive no-improvement iterations
4. Log all iterations to `/tmp/cv-autoresearch-log.tsv`

If score is already 90%+, skip the loop and proceed to Step 3.
If score is below 82%, recommend SKIP (do not enter the loop).

The loop ONLY adjusts: keyword selection, bullet ordering, summary wording, competency selection.
The loop NEVER: fabricates data, adds fake roles, invents metrics.

---

## Step 3 — CV Architecture Rules

### Positioning
- Ahmed is a **Digital Transformation Executive** — never a consultant, never a contractor
- Lead with transformation scope: $50M budget, 15 hospitals, 3 countries, 300+ projects, 233x growth
- Vision 2030 angle is a differentiator for ALL KSA roles — make it explicit

### Executive Summary (3-4 sentences)
- Sentence 1: Who he is + years + sectors
- Sentence 2: Signature achievement (Talabat scale OR TopMed scope — pick the one most relevant to the JD)
- Sentence 3: Current role and most relevant capability to the JD
- Sentence 4: What he delivers (outcomes, not responsibilities)

### Core Competencies (pick 12-16 most relevant)
Full list available in master-cv-data.md. Always include for tech roles:
- Cloud Platform Strategy (AWS, Azure, GCP)
- Enterprise AI & LLM Deployment
- Generative AI / GenAI Strategy

Always include for KSA roles:
- Saudi Vision 2030 Digital Transformation

Always include for healthcare roles:
- Healthcare AI / Clinical AI
- JCI / HIMSS / MOH Compliance

### Experience — Bullet Ordering
Reorder bullets within each role to lead with the most JD-relevant achievement. Never add bullets that aren't in master-cv-data.md. Reframing language is allowed; fabrication is not.

### Quantify everything
- Scale: $50M, 15 hospitals, 300+ projects, 8 countries, 30 PMs, 233x growth
- Teams: 16 Project Managers recruited and trained, 30-person cross-functional teams
- Outcomes: not "improved" but "reduced costs by X%" or "increased throughput from A to B"

---

## Step 4 — Hard Rules (zero tolerance)

| Rule | Detail |
|---|---|
| No em dashes | Use commas, periods, or colons instead |
| No fabrication | Every metric and role must exist in master-cv-data.md |
| Exact titles | PMO & Regional Engagement Lead (NOT Director). Product Development Manager (NOT COO) |
| ATS floor | 82% minimum. No exceptions |
| Positioning | Digital Transformation Executive — never consultant |
| File naming | "Ahmed Nasr - [Role Title] - [Company Name].pdf" |
| Save location | /root/.openclaw/workspace/cvs/ |

---

## Pre-Send Validation Gates (MANDATORY, BLOCKING)

Before sending any CV PDF to Ahmed, all 3 gates must pass:

1. **Model Gate (Opus-only for CV work)**
   - CV tailoring/writing must run on **Opus 4.6**.
   - If Opus is unavailable, STOP and ask Ahmed before continuing.

2. **Header Gate (No extra labels)**
   - First page header must contain only:
     - `Ahmed Nasr`
     - contact line
   - Forbidden in page content: `Ahmed Nasr CV`, `[Role] - [Company]`, or any role/company header label.
   - Role/company belongs in file name only.

3. **Text Extraction Gate (automated check)**
   - Run `pdftotext` on the final PDF before send.
   - Block send if any forbidden header string appears.

If any gate fails: regenerate CV, re-check, and only then send.

## Step 5 — PDF Generation

Use WeasyPrint (most consistent results, 19-25KB target size):

```bash
# Generate HTML version first
cat > /tmp/cv-ahmed-nasr.html << 'HTML'
[CV content formatted as clean HTML with inline CSS]
HTML

# Convert to PDF via WeasyPrint (preferred method)
weasyprint /tmp/cv-ahmed-nasr.html "/root/.openclaw/workspace/cvs/Ahmed Nasr - [Role] - [Company].pdf"

# Fallback only if WeasyPrint fails:
# npx playwright pdf /tmp/cv-ahmed-nasr.html "/root/.openclaw/workspace/cvs/Ahmed Nasr - [Role] - [Company].pdf"
```

PDF formatting requirements:
- Font: Clean sans-serif (Arial or Helvetica)
- Margins: 0.75 inch all sides
- Section headers: bold, slightly larger
- Bullets: left-aligned, consistent indentation
- No tables, text boxes, or graphics (ATS killer)
- Single or two-column header only (name + contact)
- Target file size: 15-30KB. If > 50KB, something is wrong (embedded fonts/images). If < 10KB, styling likely missing.

### Post-Generation Quality Gate (automated, mandatory)

Run these checks before sending to Ahmed. If any fail, regenerate:

```bash
PDF_PATH="/root/.openclaw/workspace/cvs/Ahmed Nasr - [Role] - [Company].pdf"

# 1. File size check (15-50KB expected)
SIZE=$(stat -c%s "$PDF_PATH")
echo "Size: ${SIZE}B"

# 2. Text extraction check (must be extractable for ATS)
TEXT=$(pdftotext "$PDF_PATH" - 2>/dev/null)
CHARS=$(echo "$TEXT" | wc -c)
echo "Extractable chars: $CHARS"

# 3. Em dash check (hard zero tolerance)
EMDASH=$(echo "$TEXT" | grep -cP '—' || echo 0)
echo "Em dashes found: $EMDASH"

# 4. Header check (no role/company in body text header)
HEADER_VIOLATION=$(echo "$TEXT" | head -5 | grep -ciE '(CV|Resume|Curriculum)' || echo 0)
echo "Header violations: $HEADER_VIOLATION"

# 5. Contact info present
CONTACT=$(echo "$TEXT" | grep -c 'ahmednasr999@gmail.com' || echo 0)
echo "Contact info: $CONTACT"
```

All checks must pass: size 15-50KB, chars > 2000, em dashes = 0, header violations = 0, contact = 1.

---

## Step 6 — Handoff Update (if running inside Pipeline 1)

If a handoff file exists at `jobs-bank/handoff/<job-id>.json`:

1. Populate the `cv` section:
```json
"cv": {
  "path": "cvs/Ahmed Nasr - [Role] - [Company].pdf",
  "github_url": "https://github.com/ahmednasr999/openclaw-nasr/blob/master/cvs/...",
  "ats_score": [score],
  "tailoring_notes": "[key adjustments made]",
  "pending_review": false
}
```
2. Update `status` to `"cv_ready"`
3. Update `nasr_review.approved` to `false`
4. Overwrite trigger file with: `NASR_REVIEW_NEEDED`

---

## Step 7 — Delivery to NASR

Every CV delivery must include:

```
CV COMPLETE
Company: [Company]
Role: [Role Title]
ATS Score: [X]%
Model Used: [model alias, e.g. opus46]
File: cvs/Ahmed Nasr - [Role] - [Company].pdf
GitHub: [link]

Key tailoring made:
- [Change 1]
- [Change 2]
- [Change 3]

Keywords matched: [list top 5]
Keywords missing: [list any gaps]

Recommendation: APPLY / HOLD (reason)
```

---

## Step 8 — Commit and Push

```bash
cd /root/.openclaw/workspace
git add cvs/ jobs-bank/
git commit -m "cv: Ahmed Nasr - [Role] - [Company] (ATS [X]%)"
git push origin master
```

---

## Ahmed's Story Arsenal (Quick Reference)

| Story | Key metrics | Use for |
|---|---|---|
| Talabat scale | 30K to 7M daily orders, 233x growth | Operations, e-commerce, scaling roles |
| TopMed transformation | $50M, 15 hospitals, 3 countries, 14 AI agents | HealthTech, AI, transformation, KSA roles |
| Network International PMO | 300+ projects, 8 countries, 16 PMs, 300+ banking clients | PMO, FinTech, enterprise, multi-country |
| PaySky SuperApp | Egypt's first SuperApp, FinTech market entry | FinTech, product, startup/scale-up |
| Revamp Consulting | Mayo Clinic, AT&T engagements | Consulting, healthcare, enterprise |

---

---

## Common Failure Modes (learned from 56 CV generations)

| Failure | Cause | Prevention |
|---------|-------|------------|
| CV built on wrong model | Session was on MiniMax/Haiku, not Opus | Step 0 model gate is BLOCKING |
| Wasted CV for unqualified role | Scored from title only, full JD revealed disqualifier | Step 0 full JD gate is BLOCKING |
| Tiny PDF (< 10KB) | Missing CSS/styling in HTML template | Post-gen quality gate checks file size |
| Bloated PDF (> 100KB) | Playwright embedded fonts/images | Use WeasyPrint, not Playwright |
| Em dashes in output | Model default punctuation | Post-gen automated check, hard rule in Step 4 |
| Header shows "Ahmed Nasr CV" | Model added label | Post-gen header check, Step 4 header gate |

---

**Links:** `memory/master-cv-data.md` | `memory/cv-pending-updates.md` | `memory/ats-best-practices.md` | `jobs-bank/pipeline.md` | `jobs-bank/handoff/SCHEMA.md`
