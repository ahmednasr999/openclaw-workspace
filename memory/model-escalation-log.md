---
description: "Log of model escalations and fallbacks: which model, why, outcome"
type: log
topics: [system-ops]
updated: 2026-03-14
---

# Model Escalation Log — 7-Day Audit

*Started: 2026-02-28*
*Purpose: Track every non-M2.5 model usage for Ahmed's daily review*
*Rule: Log every escalation. Review daily. After 7 days, evaluate whether to make permanent.*

---

## Format

| Time (Cairo) | Task | Model Used | Why Not M2.5 |
|---|---|---|---|

---

## 2026-02-28 (Saturday)

| Time (Cairo) | Task | Model Used | Why Not M2.5 |
|---|---|---|---|
| ~10:00 AM | Session startup, strategic work (evolution proposals review) | claude-opus-4-6 | Rate limit cascade — M2.5 had 401 auth error, escalated to Opus for main session recovery |
| ~10:00–11:00 AM | Full session: proposals 1-3, cron investigation, CV tracking, system fixes | claude-sonnet-4-6 | Main session running on Sonnet for strategic reasoning tasks (150-500 token range) |

**Daily total:** 2 escalations (1 to Opus for recovery, 1 to Sonnet for main session strategic work)

---

## 2026-03-01 (Sunday)

| Time (Cairo) | Task | Model Used | Why Not M2.5 |
|---|---|---|---|

**Daily total:** — (not yet)

---

## 2026-03-02 (Monday)

| Time (Cairo) | Task | Model Used | Why Not M2.5 |
|---|---|---|---|

**Daily total:** — (not yet)

---

## 2026-03-03 (Tuesday)

| Time (Cairo) | Task | Model Used | Why Not M2.5 |
|---|---|---|---|

**Daily total:** — (not yet)

---

## 2026-03-04 (Wednesday)

| Time (Cairo) | Task | Model Used | Why Not M2.5 |
|---|---|---|---|

**Daily total:** — (not yet)

---

## 2026-03-05 (Thursday)

| Time (Cairo) | Task | Model Used | Why Not M2.5 |
|---|---|---|---|

**Daily total:** — (not yet)

---

## 2026-03-06 (Friday)

| Time (Cairo) | Task | Model Used | Why Not M2.5 |
|---|---|---|---|

**Daily total:** — (not yet)

---

## Weekly Summary (fill at end of 7-day window)

| Day | Total Escalations | Opus | Sonnet | Haiku | Notes |
|---|---|---|---|---|---|
| Feb 28 | 2 | 1 | 1 | 0 | Rate limit cascade forced Opus |
| Mar 1 | — | — | — | — | |
| Mar 2 | — | — | — | — | |
| Mar 3 | — | — | — | — | |
| Mar 4 | — | — | — | — | |
| Mar 5 | — | — | — | — | |
| Mar 6 | — | — | — | — | |
| **Total** | | | | | |

**Verdict (fill Mar 7):** Keep logging permanently? Y/N — Reason:

---

**Links:** [[../MEMORY.md]] | [[../AGENTS.md]] | [[active-tasks.md]]
