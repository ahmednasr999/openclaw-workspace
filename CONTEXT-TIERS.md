# CONTEXT-TIERS.md - Tiered Context Loading System

Inspired by OpenViking's L0/L1/L2 pattern for efficient context management.

---

## Overview

Instead of loading all project context files every session, we use a tiered approach that loads only what's needed based on the task type. This reduces token usage and improves response speed while maintaining context continuity.

---

## L0: Always Loaded (Every Session)

**Tokens:** ~minimal (~500-800 tokens)
**Trigger:** Every session, unconditionally

| File | Purpose |
|------|---------|
| `IDENTITY.md` | Who I am (NASR - Strategic AI Consultant) |
| `USER.md` | Who Ahmed is (profile, preferences, timezone) |
| `SOUL.md` | Behavioral rules and operating principles |
| `HEARTBEAT.md` | If non-empty - critical alerts and time-sensitive items |
| `config/service-registry.md` | How we connect to every external service (direct API vs Composio vs CLI). MUST be checked before any external service call. |

**Rationale:** These files define core identity, behavioral rules, and service connection methods. Without them, the assistant loses essential context or makes wrong assumptions about how to connect to services.

---

## L1: Task-Triggered Loading

**Tokens:** ~1,500-2,500 tokens per file
**Trigger:** When specific task type is identified

| File | When to Load |
|------|--------------|
| `AGENTS.md` | Spawning sub-agents or coordinating multi-step workflows |
| `TOOLS.md` | Technical configurations needed (LinkedIn posting, CV creation, model switching) |
| `SKILL.md` | When a specific skill is triggered |
| `coordination/pipeline.json` | Job application tracking operations |
| `coordination/dashboard.json` | Metrics and KPI operations |
| `coordination/content-calendar.json` | Content pipeline operations |

**Rationale:** These files are only needed for specific task types. Loading them on-demand prevents unnecessary context bloat.

---

## L2: On-Demand Loading

**Tokens:** Variable (typically 1,000-3,000 tokens)
**Trigger:** Only when explicitly requested or referenced

| File | When to Load |
|------|--------------|
| `memory/master-cv-data.md` | CV creation tasks only |
| `memory/daily-YYYY-MM-DD.md` | Referencing specific past sessions |
| `memory/ats-best-practices.md` | CV creation, ATS scoring |
| `memory/lessons-learned.md` | Reviewing past mistakes or learning |
| `memory/briefings/*` | Referencing past briefings |
| `coordination/outreach-queue.json` | Lead outreach operations |
| Pipeline history files | Analyzing application trends |

**Rationale:** These are specialty files accessed only when directly relevant to the current task.

---

## Loading Rules

1. **Start with L0** — Always load identity, user, soul, and heartbeat (if present)
2. **Identify task type** — Determine if the task requires L1 files
3. **Load L1 only when needed** — Don't pre-load technical configs for a simple conversation
4. **Load L2 only on explicit request** — Never load CV master data unless creating a CV
5. **Minimize file switches** — If loading a new tier, complete that task before returning to L0-only mode

---

## Implementation Notes

- **Session startup:** Load L0 files first (~500-800 tokens)
- **Task identification:** After first user message, determine if L1 needed
- **On-demand:** Use `read` tool to load L2 files only when explicitly referenced
- **Context window:** Total target < 5,000 tokens for typical session

---

## Anti-Patterns to Avoid

- ❌ Loading all files on session start (current inefficient state)
- ❌ Keeping L1/L2 files in context after task completion
- ❌ Loading CV master data for non-CV tasks
- ❌ Loading coordination files for general conversation
