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
- Always use actual company name, not recruiter name
- If company is confidential/unnamed, ask Ahmed for company name before generating PDF
- Title should match the job title exactly

**Example filenames:**
- `Ahmed Nasr - Senior Program Manager - Nabat.pdf`
- `Ahmed Nasr - Director of Business Excellence - Equinix.pdf`

---

## CV Design Rules (Permanent — Lessons Learned)

**ALWAYS follow these rules for every CV:**

### ATS-Friendly (Non-Negotiable)
- ❌ NO tables — ATS scrambles them
- ❌ NO multi-column layouts — ATS reads left-to-right across columns
- ❌ NO text boxes or floating elements
- ❌ NO headers/footers (often ignored by ATS)
- ❌ NO images, icons, or graphics
- ✅ Single column layout ONLY
- ✅ Simple bullet lists
- ✅ Standard section headers (Experience, Education, Skills)
- ✅ Reverse chronological order

### Professional Styling
- ❌ NO gradient backgrounds — won't render in PDF
- ❌ NO colored backgrounds with white text — print issues
- ✅ Clean black & white
- ✅ Serif font (Times New Roman) or clean sans-serif (Arial, Calibri)
- ✅ Borders are OK (solid, simple)
- ✅ Bold for emphasis
- ✅ Print-safe always

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

- **Base CV:** `/root/.openclaw/workspace/Ahmed_Nasr_-_Senior_Project_Manager.pdf`
- **LinkedIn tracker:** `/root/.openclaw/workspace/linkedin_analytics_tracker.md`
