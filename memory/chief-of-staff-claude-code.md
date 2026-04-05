---
description: "Chief of Staff pattern for Claude Code: delegation, orchestration, oversight"
type: reference
topics: [knowledge, system-ops]
updated: 2026-03-14
---

# My Chief of Staff, Claude Code - Jim Prosser

*Source: @jimprosser (Jim Prosser, Founder Tamalpais Strategies)*
*Tweet: https://x.com/jimprosser/status/2029699731539255640*
*Article: https://x.com/i/notes/2029698920159531010*
*Posted: Mar 5, 2026*
*Views: 1.3M+*

---

## The Results

| Metric | Value |
|--------|-------|
| Build time | 36 hours |
| Coding experience | None (43-year-old consultant) |
| Time saved | 30-45 min/day = 130-195 hours/year |
| Cost | $100/month (Claude Max) + $5-10 API |
| Replaces | Part-time ops person ($400-1,000/month) |

---

## What It Does

### Morning Routine (Automated)

| Time | What Happens |
|------|--------------|
| Overnight | Scans Google Calendar → calculates drive times → creates transit events |
| Overnight | Triages email → identifies action items → creates Todoist tasks |
| 6:15 AM | Task system is current without human touch |

### AM Sweep (Button Press)

| Category | What It Means |
|----------|---------------|
| Green | Claude completes fully |
| Yellow | Claude gets 80%, human finishes |
| Red | Needs human brain/presence |
| Gray | Not actionable today |

### 6 Parallel Agents

| Agent | Task |
|-------|------|
| Email drafter | Drafts (never sends), human reviews |
| Client files updater | Updates Obsidian knowledge base |
| Meeting scheduler | Books meetings |
| Researcher | Background research on prospects/topics |

### Time Block (Button Press)
- Converts remaining tasks to time-blocked calendar
- Batches errands into single outing
- Routes geographically to minimize backtracking
- Respects location constraints (home vs office)

---

## The Architecture

| Layer | What It Does |
|-------|-------------|
| Overnight scanner | Scans calendar + email, creates tasks with metadata |
| AM Sweep | Classifies tasks, assembles context packages for agents |
| 6 parallel subagents | Each with own context, tool access |
| Time blocker | Reads all upstream output, builds schedule |

---

## The Key Design Principle

### Dispatch / Prep / Yours / Skip

| Category | Action |
|----------|--------|
| Dispatch | Handle fully |
| Prep | Get 80% ready, options for human |
| Yours | Flag as human task with context |
| Skip | Defer with reason |

> "The bias is always toward involving me on anything ambiguous."

---

## The Layering Insight

> "Each component had to know the others existed. The overnight email scanner doesn't just dump tasks; it attributes them with metadata that the Morning Sweep needs. The AM Sweep assembles context packages each subagent needs."

**This is exactly what separates a system from a collection of scripts. Each piece is designed to feed the next one.**

---

## Cost Breakdown

| Item | Cost |
|------|------|
| Claude Max | $100/month |
| Google Maps API | Free tier |
| Hosting | Free (Mac Studio) |
| **Total** | **$5-10/month** |

---

## Key Quotes

> "I didn't need to understand the code at a syntax level. But I did need to have a clear picture of the architecture: what talks to what, what each piece is responsible for, where the human-AI boundaries are. That's systems thinking, not software engineering."

> "This is what separates a system from a collection of scripts. Each piece is designed to feed the next one. Remove any layer and the others still work. But the whole is dramatically more than the sum."

> "The gap is going to close eventually. Professionals who figured it out early and developed the instinct for what to automate and what to keep human, who learned to think in systems rather than prompts, are going to have an enormous advantage over the ones who waited for someone to package it into a SaaS product."

---

## OpenClaw Application

| Pattern | Apply To |
|---------|----------|
| Overnight scan | Job radar, email triage |
| AM Sweep | Job applications, content creation |
| 6 parallel agents | CV generation, LinkedIn posting |
| Time blocking | Schedule optimization |
| Dispatch/Prep/Yours/Skip | Task classification |
| Metadata passing | Each layer feeds the next |

---

## Action Items from This

1. [ ] Create overnight job radar scan
2. [ ] Build morning AM Sweep for job applications
3. [ ] Add Dispatch/Prep/Yours/Skip classification
4. [ ] Build time-blocking for your schedule
5. [ ] Each component should pass metadata to the next

---

## Related

- [[eval-suite/README.md]] - Skill evaluation framework
- [[memory/agent-tool-design-lessons.md]] - Agent tool design
- [[memory/24-7-ai-company-50-month.md]] - $50/month setup
- [[memory/openclaw-codex-swarm-setup.md]] - Multi-agent architecture
