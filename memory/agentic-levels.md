# 5 Levels of Agentic Software

*Source: Ashpreet Bedi (X/Twitter)*
*Saved: 2026-02-21*

---

## The 5 Levels

### Level 1: Agent with Tools
An agent without tools is just an LLM. Tools turn an LLM into an Agent.

**For coding agents:**
- Read files
- Write files
- Run shell commands

**What's missing:**
- No session recall
- No project conventions
- No knowledge beyond context

---

### Level 2: Agent with Storage + Knowledge

**Storage:**
- Saves sessions to database
- Chat history as context
- Record of what happened

**Knowledge:**
- Searchable store of specs, ADRs, runbooks, meeting notes
- Agent can find relevant context before coding

---

### Level 3: Agent with Memory + Learning

**Memory:**
- Remembers conversations across sessions
- User preferences learned over time
- Follow-up questions have full context

**Learning:**
- Agent decides what's worth remembering
- Stores patterns that worked
- Mistakes to avoid

---

### Level 4: Multi-Agent Teams

**Roles:**
- Coder: writes code
- Reviewer: reviews quality/bugs
- Tester: writes/runs tests
- Team leader: coordinates

**Warning:** "Multi-agent teams are powerful but unpredictable. For production systems where reliability matters, prefer explicit workflows over dynamic teams."

---

### Level 5: Production System

- PostgreSQL + PgVector
- AgentOS (FastAPI)
- Tracing/observability
- Multiple users, uptime requirements

---

## Key Advice

> "Start at Level 1. Build the simplest agent that could solve the problem. Run it. See where it fails. Then add exactly the capability it's missing.
> 
> Most teams skip to Level 4 because multi-agent architectures look impressive in demos. Then they spend months debugging coordination failures that a single agent with good instructions would have avoided."

---

## Our Status

| Level | Status | Action |
|-------|--------|--------|
| Level 1 | ✅ | OpenClaw has tools |
| Level 2 | ⚠️ | Storage OK, Knowledge needs work |
| Level 3 | ❌ | Not implemented |
| Level 4 | ❌ | Not needed yet |
| Level 5 | ❌ | Not needed |

---

## Recommendations for Our Setup

1. **Focus on Level 2**: Improve knowledge base (CV data, job specs, project docs)
2. **Fix session storage**: Make conversations persist properly
3. **Skip Level 4**: Multi-agent is overkill for now
4. **Build foundation first**: Then add complexity

---

*This is the blueprint we should follow for building our agentic system.*
