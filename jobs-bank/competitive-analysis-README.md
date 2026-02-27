# Competitive Positioning Analysis: Trigger System

*Last updated: 2026-02-27*
*Maintained by: NASR*

---

## What This Is

A recurring analysis that reads all job descriptions in the pipeline and cross-references them against Ahmed's master CV. It identifies:

- Which keywords appear most across all JDs (frequency ranking)
- Which high-frequency keywords are weak or missing in the CV (gap analysis)
- Specific phrases to add to LinkedIn headline and summary
- Market patterns in what GCC employers are consistently requesting
- Targeted lines to rewrite in the master CV before the next application batch

The goal is continuous calibration. As the market changes and the pipeline grows, this analysis ensures Ahmed's positioning stays aligned with what employers actually ask for, not what seemed right 30 applications ago.

---

## When to Run

**Rule: Run every 10 new CVs generated.**

This is tracked via the total application count in pipeline.md.

| Trigger Point | Application Count | Status |
|--------------|------------------|--------|
| First run | 27 applications | DONE (2026-02-27) |
| Second run | 37 applications | PENDING |
| Third run | 47 applications | Future |
| Fourth run | 57 applications | Future |

The current count is tracked in the "Pipeline Metrics" section of:
`/root/.openclaw/workspace/jobs-bank/pipeline.md`

---

## How to Run

```bash
bash /root/.openclaw/workspace/scripts/competitive-analysis.sh
```

The script:
1. Scans all job.md files in jobs-bank/applications/
2. Counts keyword frequency across all JDs
3. Checks master CV for gaps against high-frequency keywords
4. Saves a dated report to jobs-bank/competitive-analysis-[YYYY-MM-DD].md
5. Prints a summary to the terminal

**Expected runtime:** Under 30 seconds.

---

## What to Do With the Results

### Step 1: Review the Gap Analysis (5 minutes)

Open the generated report. Focus on the "MISSING" and "WEAK" gaps with HIGH or CRITICAL severity. These are keywords that appear in 5+ JDs but do not appear in the master CV. Every gap here means Ahmed's CV is being downranked by ATS systems.

### Step 2: Update master-cv-data.md (15 minutes)

For each CRITICAL or HIGH gap, add the appropriate line to:
`/root/.openclaw/workspace/memory/master-cv-data.md`

Use the "RECOMMENDATIONS" section in the analysis report. Each recommendation includes:
- Which section of the CV to update
- The exact current text (before)
- The recommended replacement or addition (after)
- The evidence basis for the change

Do NOT fabricate. Every addition must be grounded in actual experience.

### Step 3: Apply to Next Batch

After updating master-cv-data.md, the next round of CV generations (using the CV Optimizer agent) will automatically pick up the improved language. No manual updates to individual CV files are needed. The master CV is the source of truth.

### Step 4: Archive the Report

Reports are saved automatically as:
`jobs-bank/competitive-analysis-YYYY-MM-DD.md`

Keep all historical reports. They form a record of how the market is shifting over time.

---

## Files Involved

| File | Purpose |
|------|---------|
| `competitive-analysis-2026-02-27.md` | First analysis report (reference quality, full detail) |
| `competitive-analysis-[DATE].md` | Auto-generated reports from script |
| `competitive-analysis-README.md` | This file. Trigger system documentation. |
| `/scripts/competitive-analysis.sh` | The analysis script |
| `/memory/master-cv-data.md` | Ahmed's master CV (source of truth) |
| `pipeline.md` | Current application count (tracks trigger point) |

---

## First Analysis Key Findings (2026-02-27)

For reference, the first analysis found:

**Top 5 gaps (critical to high severity):**
1. Cloud platforms (AWS, Azure, GCP) - missing entirely from CV, affects 10/17 JDs
2. GenAI / LLM deployment - 14 production AI agents exist but NOT in CV
3. Vision 2030 - phrase missing, critical filter for 6/17 KSA-focused roles
4. Enterprise Architecture - missing language, affects 7/17 JDs
5. Cybersecurity governance - missing, affects 7/17 JDs

**Most surprising finding:**
The GCC market treats cloud competency as a baseline assumption at director level and above. It is often not even listed as a named "requirement" because it is assumed. Ahmed's CV has zero cloud language, making ATS systems likely to deprioritize the profile for 10 of 17 current roles.

**One immediate action from first analysis:**
Add "cloud platform strategy (AWS, Azure)" to the master CV Executive Summary. This single addition affects ATS scoring on 10/17 active applications and all future applications in cloud-adjacent roles.

---

## Notes

- Do NOT run this script during active LLM sessions (can slow the VPS during heavy loads)
- Preferred run time: morning, before the day's application batch
- If pipeline grows faster than expected (more than 10 new CVs in 3 days), run immediately rather than waiting for the count

---

*Links: pipeline.md | master-cv-data.md | competitive-analysis-2026-02-27.md*
