# MEMORY.md - Long-Term Memory

## CV Creation Workflow (Permanent)

**Trigger:** Ahmed shares job link + description

**Steps:**
1. Analyze job requirements
2. Report ATS compatibility score (X/100)
3. Recommend model switch to Opus (wait for approval)
4. Create tailored CV matching keywords & requirements
5. Export as PDF
6. **Filename:** `Ahmed Nasr - {Title} - {Company Name}.pdf`
7. Send PDF via Telegram
8. Ask if switch back to MiniMax

**Filename Rules:**
- Format: `Ahmed Nasr - {Title} - {Company Name}` (spaces and dashes, NO underscores)
- Apply to BOTH HTML and PDF files
- Always use actual company name, not recruiter name
- If company is confidential/unnamed, use format: `Ahmed Nasr - {Title}` (no company suffix)
- Title should match the job title exactly

**Example filenames:**
- `Ahmed Nasr - Senior Program Manager - Nabat.html`
- `Ahmed Nasr - Senior Program Manager - Nabat.pdf`
- `Ahmed Nasr - Director of Business Excellence - Equinix.html`
- `Ahmed Nasr - Director of Business Excellence - Equinix.pdf`

---

## CV Design Rules (Permanent — Lessons Learned)

**Full ATS guide:** `memory/ats-best-practices.md`

### ATS-Friendly (Non-Negotiable)
- ❌ NO tables — ATS scrambles them
- ❌ NO multi-column layouts — ATS reads left-to-right across columns
- ❌ NO text boxes or floating elements
- ❌ NO headers/footers (often ignored by ATS)
- ❌ NO images, icons, or graphics
- ❌ NO special bullet characters (● ► ★)
- ✅ Single column layout ONLY
- ✅ Simple bullet lists (use - or •)
- ✅ Standard section headers (Professional Summary, Experience, Education, Skills, Certifications)
- ✅ Reverse chronological order
- ✅ Consistent date format (MMM YYYY – Present)

### Bullet Writing (AVR Pattern)
Every bullet: **Action Verb + Value/What + Result/Metric**
- ✅ "Led digital transformation across 15-hospital network, managing $50M budget"
- ❌ "Responsible for digital transformation projects"

### Keyword Strategy
- Mirror exact JD phrases (not synonyms)
- Top 5 JD keywords must appear in Summary + most recent role
- Include both acronyms AND full terms: "Project Management Professional (PMP)"
- Critical keywords: 2-3x across CV (naturally distributed)

---

## Model Strategy

| Task | Model | Notes |
|------|-------|-------|
| Default / daily | MiniMax-M2.1 | Free tier |
| Background / cron | MiniMax-M2.1 | Free tier |
| CV creation/review | Claude Opus 4.5 | Requires approval |

**Rule:** Always ask before switching to paid models. Notify after any switch.

---

## Daily Self-Evaluation Protocol

Every session, end with quick reflection:
1. Did I think 2 steps ahead?
2. Did I surface opportunities early?
3. Did I connect dots across sessions?

**If no to any:** Document the miss in today's memory.

### Lessons Learned Log

Store in: `memory/lessons-learned.md`

Format:
```
## [Date]
### What I Missed
[Specific example]
### Why
[Root cause]
### Fix
[What I'll do differently]
```

---

## Preferences

- **Timezone:** Cairo (Africa/Cairo, UTC+2)
- **LinkedIn posts:** Always end with question/CTA for engagement
- **Backups:** Keep last 7, daily at 3 AM Cairo
- **Gmail check:** Daily at 8 AM Cairo

---

## Key Files

- **Master CV Data (Source of Truth):** `/root/.openclaw/workspace/memory/master-cv-data.md`
- **Master CV PDF:** `/root/.openclaw/media/inbound/file_99---61a97145-01ba-402f-b33b-5915c31c8daf.pdf`
- **Master CV DOCX:** `/root/.openclaw/media/inbound/file_100---a1dce511-4dda-481f-aff5-c9093298c040.docx`
- **LinkedIn tracker:** `/root/.openclaw/workspace/linkedin_analytics_tracker.md`

## CV Creation Rule (Critical)
**ALWAYS read `memory/master-cv-data.md` before creating any CV.**
Never fabricate roles, titles, or achievements. Use exact titles and dates from master CV.
