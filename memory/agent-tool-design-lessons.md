---
description: "Lessons learned from designing agent tools: patterns, anti-patterns, best practices"
type: reference
topics: [knowledge, system-ops]
updated: 2026-03-14
---

# Agent Tool Design - Claude Code Lessons

*Source: @trq212 (Thariq, Claude Code team @ Anthropic)*
*Tweet: https://x.com/trq212/status/2027463795355095314*
*Date: Feb 27, 2026*

---

## Core Framework

> "How do you design the tools of your agent? You want to give it tools that are shaped to its own abilities. But how do you know what those abilities are? You pay attention, read its outputs, experiment. You learn to see like an agent."

---

## Key Lessons Learned

### 1. Elicitation & AskUserQuestion Tool

**Problem:** Claude could ask questions in plain text but answering felt like unnecessary friction.

**Attempts:**
1. ExitPlanTool with questions parameter - Confused Claude
2. Modified output format - Not guaranteed, inconsistent
3. Dedicated AskUserQuestion tool - Worked best

**Insight:** Structured output tools work better than hoping for specific format from plain text.

---

### 2. Tasks vs Todos

**Problem:** Claude kept forgetting todos, reminders every 5 turns became limiting.

**Evolution:**
- Todos: Keeping model on track
- Tasks: Helping agents communicate with each other

**Insight:** "As model capabilities increase, the tools that your models once needed might now be constraining them."

---

### 3. Search Interface - Grep vs RAG

**Old approach:** Vector database RAG for context
**New approach:** Give Claude Grep tool to search itself

**Insight:** "Claude became increasingly good at building its own context if it's given the right tools."

---

### 4. Progressive Disclosure

**Problem:** Too much info in system prompt causes "context rot"

**Solution:** Instead of adding tools, give Claude:
- Links to docs it can search
- Subagents with specific instructions
- Skills that reference other skills

**Insight:** "Add functionality without adding a tool."

---

## Design Principles

### The High Bar

> "The bar to add a new tool is high, because this gives the model one more option to think about."

Before adding a tool, ask:
1. Can this be a skill instead?
2. Can Claude search docs for this?
3. Can a subagent handle this?

### The Art, Not Science

> "Designing the tools for your models is as much an art as it is a science. It depends heavily on the model you're using, the goal of the agent and the environment it's operating in."

**Rule:** Experiment often, read outputs, try new things. See like an agent.

---

## OpenClaw Application

| Claude Code Pattern | OpenClaw Current | Improvement |
|--------------------|-------------------|-------------|
| AskUserQuestion | message tool | Could add structured prompts |
| Task Tool | active-tasks.md | Good, but could add subagent coordination |
| Grep for context | Semantic search | Already aligned |
| Progressive disclosure | Skills | Already aligned |
| Guide subagent | Agent-specific prompts | Could improve with subagent routing |

---

## Action Items

1. [ ] Review tools in openclaw.json - is the bar high enough?
2. [ ] Consider replacing reminders with Task-like coordination
3. [ ] Audit skills for progressive disclosure patterns
4. [ ] Build eval suite to measure tool effectiveness
5. [ ] Read Claude Code outputs for patterns

---

## Related

- [[eval-suite/README.md]] - Skill evaluation framework
- [[memory/2026-03-06.md]] - Today's session
- Source: Thariq (@trq212), Claude Code team
