---
description: "AI advisory board architecture: 8 expert personas, briefing engine, weekly synthesis"
type: reference
topics: [system-ops, strategy]
updated: 2026-03-14
---

# Business Advisory Board: Implementation Blueprint

*Created: 2026-03-01 | Status: Ready for Review*

---

## 1. System Architecture

```
INPUTS                    PROCESSING                 OUTPUTS
─────────────────────     ─────────────────────      ─────────────────────
memory/*.md               Domain Adapter Layer       Daily Brief (scored)
active-tasks.md           ↓                          Weekly Strategy Report
pipeline.md               8 Advisory Lenses          Decision Recommendations
GOALS.md                  ↓                          Risk Alerts
Calendar/Email             Scoring Engine             Opportunity Flags
TopMed project data       (I×U×C)/(E×(1-A))         Time Allocation Map
LinkedIn metrics          ↓                          Conflict Warnings
Financial snapshots       Priority Queue +           Weekly Bets Scorecard
                          Conflict Detector
```

**Core Loop:** Ingest state from all domains → run each advisory lens → score every item → detect conflicts across domains → deliver prioritized output.

The system is a single processing pipeline with swappable domain adapters. Adding a new life domain means adding one adapter file, not changing the core.

---

## 2. Eight Advisory Roles

Each role is a "lens" applied to the full input set. They are not siloed by domain. Every lens scans every domain.

| # | Role | Lens | Core Question |
|---|------|------|---------------|
| 1 | **Chief Strategy Officer** | Long-term positioning, career trajectory, market timing | "Does this move Ahmed closer to his 3-year target?" |
| 2 | **Chief Risk Officer** | Downside exposure, compliance, reputation, single points of failure | "What breaks if this goes wrong, and can we recover?" |
| 3 | **Chief Operating Officer** | Execution quality, bottlenecks, resource allocation, delivery timelines | "Can this actually get done with current capacity?" |
| 4 | **Chief Financial Officer** | ROI, cost exposure, salary negotiations, investment decisions | "What is the financial upside, and what does it cost?" |
| 5 | **Chief Brand Officer** | Personal brand, LinkedIn presence, thought leadership, market perception | "How does this shape how the market sees Ahmed?" |
| 6 | **Chief Technology Officer** | AI automation roadmap, tool selection, technical debt, integration | "Is the tech stack serving the strategy or creating drag?" |
| 7 | **Chief People Officer** | Network, relationships, mentors, team dynamics, stakeholder management | "Who needs to be involved, informed, or cultivated?" |
| 8 | **Devil's Advocate** | Contrarian challenge, assumption testing, blind spot detection | "What are we not seeing, and what assumption is weakest?" |

**Rule:** The Devil's Advocate lens runs last and explicitly challenges the consensus of the other seven.

---

## 3. Scoring Model

Every actionable item gets scored on five dimensions:

| Dimension | Symbol | Scale | Definition |
|-----------|--------|-------|------------|
| Impact | I | 1-10 | Magnitude of positive outcome if completed |
| Urgency | U | 1-10 | Time sensitivity. 10 = must act today |
| Confidence | C | 0.1-1.0 | How certain we are about the impact estimate |
| Effort | E | 1-10 | Resources, time, and energy required |
| Alignment | A | 0.1-1.0 | How well this maps to GOALS.md strategic objectives |

### Formula

```
Priority Score = (I × U × C) / (E × (1.1 - A))
```

**Why (1.1 - A) instead of (1 - A):** Prevents division by zero when alignment is perfect (A=1.0). Items perfectly aligned with goals get a 10x effort discount. Misaligned items (A=0.1) get no discount.

### Score Interpretation

| Score Range | Action |
|-------------|--------|
| 50+ | Do immediately. Block time today. |
| 20-49 | Schedule this week. High priority. |
| 10-19 | Queue for next week unless urgency spikes. |
| 5-9 | Backlog. Review monthly. |
| Below 5 | Drop or delegate. Not worth the effort. |

### Worked Example

"Apply to VP Digital Transformation role at major GCC bank"
- I=9, U=7 (closing in 5 days), C=0.8, E=6, A=0.9
- Score = (9 × 7 × 0.8) / (6 × (1.1 - 0.9)) = 50.4 / 1.2 = **42.0** → Schedule this week, high priority.

---

## 4. Cadence

### Daily (Morning Brief, delivered by 07:00 Cairo time)

1. **Scan** all domain adapters for new inputs (calendar, email, tasks, pipeline, metrics)
2. **Score** any new or changed items
3. **Surface** top 3 priorities with scores and the advisory lens that flagged them
4. **Flag** any conflicts across domains (e.g., interview prep colliding with TopMed deadline)
5. **Deliver** one new idea (per SOUL.md non-negotiable #4)

Output: 10-line max daily brief with scored priorities and one recommendation.

### Weekly (Sunday evening, delivered by 20:00 Cairo time)

1. **Review** all scored items from the week
2. **Run** all 8 lenses across the full state
3. **Score** the week's strategic bets (did they pay off?)
4. **Detect** drift from GOALS.md
5. **Propose** 2-3 strategic bets for the coming week
6. **Time audit:** where did hours actually go vs. where they should go

Output: Weekly Strategy Report (structured markdown, under 500 words).

### Monthly (First Sunday of each month)

1. **Recalibrate** scoring weights if patterns show misalignment
2. **Audit** which advisory lenses are producing value vs. noise
3. **Update** domain adapters if new areas emerge
4. **Archive** completed items and lessons learned

---

## 5. Input/Output Schema

### Inputs (what the system reads)

| Source | File/Location | Domain Adapter |
|--------|--------------|----------------|
| Strategic goals | GOALS.md | All lenses |
| Active tasks | memory/active-tasks.md | COO, CRO |
| Job pipeline | jobs-bank/pipeline.md | CSO, CFO |
| Long-term memory | MEMORY.md | All lenses |
| Daily logs | memory/YYYY-MM-DD.md | All lenses |
| Calendar | Google Calendar (via gog) | COO, CPO |
| Email | Gmail (via gog/himalaya) | CSO, CPO |
| LinkedIn metrics | Manual input or browser scrape | CBO |
| TopMed project state | memory/topmed-*.md | COO, CRO |
| Financial data | memory/financial-snapshot.md | CFO |
| AI roadmap | memory/ai-automation-roadmap.md | CTO |
| Content pipeline | skills/agent-content-pipeline/ | CBO |

### Outputs (what the system delivers)

| Output | Frequency | Destination |
|--------|-----------|-------------|
| Daily Brief | Daily 07:00 | Telegram main chat |
| Risk Alert | Real-time | Telegram (urgent flag) |
| Weekly Strategy Report | Sunday 20:00 | memory/weekly-report-YYYY-WNN.md + Telegram |
| Decision Recommendation | On-demand | Inline in conversation |
| Conflict Warning | When detected | Telegram (immediate) |
| Monthly Calibration | Monthly | memory/monthly-calibration-YYYY-MM.md |

---

## 6. Two-Phase Rollout

### Phase 1: Core Engine (Days 1-14)

**Goal:** Get the scoring model and daily brief running with 3 domain adapters.

- Implement scoring formula as a reusable function in a skill or script
- Build 3 domain adapters: Career/Jobs, TopMed PMO, Personal Brand
- Wire daily brief into morning cron (07:00 Cairo)
- Run all 8 lenses manually during daily brief generation
- Output to memory/daily-brief-YYYY-MM-DD.md and Telegram
- Ahmed reviews and gives feedback on scoring accuracy for 14 days

**Success criteria:** Ahmed finds the daily brief useful 4 out of 5 days.

### Phase 2: Full Board + Automation (Days 15-30)

**Goal:** Add remaining domain adapters, weekly cadence, and conflict detection.

- Add domain adapters: AI Automation, Risk/Compliance, Time Allocation, Financial
- Implement weekly strategy report (Sunday cron)
- Build conflict detector (cross-domain collision alerts)
- Add strategic bet tracker (propose, track, score weekly bets)
- Implement monthly calibration routine
- Tune scoring weights based on Phase 1 feedback

**Success criteria:** Weekly report surfaces at least one insight Ahmed did not already see. Conflict detector catches at least one real collision per week.

---

## 7. Failure Modes and Safeguards

| Failure Mode | Symptom | Safeguard |
|--------------|---------|-----------|
| **Score inflation** | Everything scores 40+, nothing gets deprioritized | Weekly recalibration: force-rank top 5 items, adjust if scores don't match rank |
| **Lens echo chamber** | All 8 lenses agree on everything | Devil's Advocate lens is mandatory and must produce at least one challenge per weekly report |
| **Stale inputs** | Adapter reads outdated files, gives wrong advice | Timestamp check: if any input file is older than 48 hours, flag it in the brief |
| **Alert fatigue** | Too many flags, Ahmed ignores them | Hard cap: daily brief surfaces max 3 items. Everything else goes to backlog. |
| **Domain neglect** | One domain dominates (e.g., job search drowns out TopMed) | Weekly balance check: each domain must appear at least once in the weekly report |
| **Over-engineering** | System becomes complex and brittle | Simplicity rule: if a component has not delivered value in 2 weeks, remove it |
| **Scoring gaming** | Urgency inflated to boost scores | Urgency requires evidence: a date, a deadline, or a dependency. No vague "feels urgent." |
| **Context loss** | Session compaction loses advisory state | All advisory state lives in files, not in session memory. Stateless by design. |

---

## 8. First 7 Days Action Plan

| Day | Action | Output |
|-----|--------|--------|
| **Day 1** | Create GOALS.md if missing. Create memory/ai-automation-roadmap.md stub. Create memory/financial-snapshot.md stub. | 3 files created, all domains have at least a stub input |
| **Day 2** | Implement scoring formula. Test with 5 real items from active-tasks.md and pipeline.md. | Validated scoring with worked examples in memory/scoring-test.md |
| **Day 3** | Build Career/Jobs domain adapter (reads pipeline.md, GOALS.md). Generate first scored priority list. | First domain adapter operational |
| **Day 4** | Build TopMed PMO adapter (reads active-tasks.md, calendar). Build Personal Brand adapter (reads content pipeline). | Three adapters operational |
| **Day 5** | Wire daily brief generation into morning cron. Run all 8 lenses across 3 adapters. Deliver first real Daily Brief. | First automated daily brief delivered to Telegram |
| **Day 6** | Ahmed reviews Days 5 brief. Collect feedback on scoring accuracy and relevance. Adjust weights if needed. | Calibration notes in memory/advisory-calibration.md |
| **Day 7** | Generate first Weekly Strategy Report (manual run). Include strategic bet proposals for Week 2. Retrospective on Day 1-7. | First weekly report + Phase 1 status assessment |

---

## Modular Core Design

```
advisory-board/
├── core/
│   ├── scoring-engine.md      # Formula, weights, interpretation
│   ├── lens-definitions.md    # 8 advisory roles and their questions
│   └── cadence-config.md      # Daily, weekly, monthly schedules
├── adapters/
│   ├── career-jobs.md         # Reads: pipeline.md, GOALS.md
│   ├── topmed-pmo.md          # Reads: active-tasks.md, calendar
│   ├── personal-brand.md      # Reads: content pipeline, LinkedIn metrics
│   ├── ai-automation.md       # Reads: ai-automation-roadmap.md
│   ├── risk-compliance.md     # Reads: all domains for risk signals
│   ├── time-allocation.md     # Reads: calendar, daily logs
│   └── financial.md           # Reads: financial-snapshot.md
├── outputs/
│   ├── daily-brief-YYYY-MM-DD.md
│   ├── weekly-report-YYYY-WNN.md
│   └── monthly-calibration-YYYY-MM.md
└── README.md                  # This blueprint
```

**Adding a new domain:** Create one adapter file in adapters/ that specifies: (1) what files it reads, (2) what signals it extracts, (3) which lenses are most relevant. The core engine picks it up automatically. No changes to scoring, lenses, or cadence needed.

---

## Recommendation

Start Phase 1 on Day 1 with the three highest-value adapters (Career, TopMed, Brand), run the daily brief for two weeks, and only expand to Phase 2 after Ahmed confirms the scoring feels accurate. The biggest risk is over-building before validating that the core scoring model matches Ahmed's actual priorities. Ship the simplest version that delivers a useful daily brief, then iterate.
