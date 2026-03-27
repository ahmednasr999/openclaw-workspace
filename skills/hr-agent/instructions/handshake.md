# Handshake Protocol — instructions/handshake.md

## Source Identification

Every incoming task has a source. Identify it first — it changes the loop-in rules.

---

## Source 1: CEO (Main Agent) via sessions_send

**Signal:** Message arrives via `sessions_send` from `agent:main:telegram:direct:866838380`

**Protocol:**
1. Parse the task (job link, CV request, pipeline query, outreach, etc.)
2. Execute immediately — CEO has already assessed and delegated
3. Report results back via `sessions_send` to the CEO session
4. Do NOT ask clarifying questions for straightforward tasks — execute and report
5. If task is ambiguous, make reasonable assumptions, execute, then flag assumptions in report

**Report format:**
```
[HR Agent] Task complete ✅

Task: {what was requested}
Result: {what was done}
Status updated: {Notion/SQLite/ontology}
Next action: {if any}
Flags: {anything CEO should know}
```

---

## Source 2: Ahmed Direct (Topic 9)

**Signal:** Ahmed messages topic 9 (-1003882622947:9) directly

**Protocol:**
1. Respond to Ahmed in topic 9 (acknowledge and act)
2. **ALWAYS loop in CEO** with a brief summary of what was requested and what action was taken
3. CEO loop is informational — do not wait for CEO approval before acting on routine tasks
4. Exception: If Ahmed requests something that involves spending, posting publicly, or a major pipeline decision → pause and confirm with Ahmed first, then inform CEO

**CEO loop format (informational):**
```python
sessions_send(
    target="agent:main:telegram:direct:866838380",
    message="[HR Agent] FYI — Ahmed requested: {brief description}\nAction taken: {what was done}\nNo action needed from you."
)
```

**When CEO loop requires attention (not just FYI):**
- Interview invite received → alert (see interviews.md)
- Recruiter positive response → alert (see outreach.md)
- Offer received → urgent alert
- Pipeline has 0 new jobs for the week → flag

---

## Source 3: Morning Briefing (Automated)

**Signal:** Morning briefing script runs and passes pipeline context

**Protocol:**
1. Review pipeline for stale applications (>14 days Applied, no movement)
2. Check for upcoming interview dates (prep needed?)
3. Check outreach queue for pending follow-ups
4. Summarize state for CEO's morning brief
5. Flag anything requiring Ahmed's input

**Briefing contribution format:**
```
📊 HR Pipeline Update

Active apps: {n}
Interviews scheduled: {n}
Stale (>14d): {n} — {list}
New this week: {n}
Outreach pending reply: {n}

⚠️ Flags: {any urgent items}
```

---

## Escalation Rules

| Situation | Escalate To | Method |
|---|---|---|
| Interview invite | CEO (urgent) | sessions_send immediately |
| Offer received | CEO (urgent) | sessions_send immediately |
| Recruiter positive response | CEO (FYI) | sessions_send |
| Pipeline 0 new jobs for 7 days | CEO (flag) | sessions_send |
| Ahmed requests out-of-scope task | Ahmed (redirect) | Reply in topic 9 |
| Duplicate application detected | Ahmed (confirm) | Reply in topic 9 |
