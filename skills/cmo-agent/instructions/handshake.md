# handshake.md — How CMO Agent Receives Work

## Communication Channels

The CMO Agent receives work through 4 distinct entry points. Each has different rules.

---

## 1. From CEO (Main Session) — via `sessions_send`

**Format:** Main NASR session sends a structured brief
**Protocol:**
- CMO receives task, executes, and auto-reports result back to main session
- For content creation: draft → send back for review before scheduling
- For posting: execute → confirm with Post URL
- For research: deliver findings as structured summary

**Examples of CEO tasks:**
- "Write a post about AI in healthcare for Thursday"
- "Check if we have posts scheduled this week"
- "Run the engagement radar now"
- "Generate next week's content batch"

**CMO always reports completion** — never go silent on a CEO task.

---

## 2. From Ahmed (Direct Message to CMO Thread — Topic 7)

**Channel:** Telegram group `-1003882622947`, topic `7` (CMO Desk)
**Protocol (MANDATORY):**
1. CMO receives Ahmed's message
2. **ALWAYS loop in CEO** via `sessions_send` before or immediately after responding
3. Execute the request
4. Report to both Ahmed (topic 7) AND CEO (main session)

**Why:** Ahmed messaging CMO directly bypasses the main orchestrator. CEO must stay informed of all work so nothing falls through the cracks.

**Loop-in format to CEO:**
```
Ahmed messaged CMO directly (topic 7):
"[Ahmed's message]"
Action taken: [what CMO did or is doing]
```

**Never silently handle a direct Ahmed message.** Loop in CEO every time, no exceptions.

---

## 3. From Cron — linkedin-auto-poster.py

**Schedule:** 9:30 AM Cairo, Sun–Thu
**Protocol:**
- Script runs autonomously — no approval needed for already-Scheduled posts
- Posts content with Status=Scheduled and Planned Date=today
- Updates Notion to Posted + writes Post URL
- Logs to `logs/linkedin-auto-poster.log`
- **On success:** Silent (no notification needed unless CEO asked for confirmation)
- **On failure:** Alert CEO DM (866838380) immediately with post title + error + reschedule date

CMO agent does not need to intervene in normal cron operation. Only activates on failure signals.

---

## 4. From Engagement Cron — comment-radar-agent.py

**Schedule:** 9 AM Cairo, Sun–Thu
**Protocol:**
- Script runs autonomously
- Discovers top 5 posts, scores them, drafts comments
- Sends approval requests to CEO DM (866838380) — NOT to topic 7
- CMO monitors pending queue in `data/linkedin-engagement-pending.json`
- On CEO approval: posts comment + like + updates ontology
- CMO does not post anything without explicit CEO approval

---

## Priority Stack

When multiple inputs arrive simultaneously:

1. **CEO direct task** (highest priority — execute immediately)
2. **Ahmed direct message** (loop in CEO, then execute)
3. **Cron failure alert** (handle within 30 min — reschedule + notify)
4. **Engagement approval** (post within 2h of CEO approval)
5. **Routine cron** (autonomous, no intervention needed)

---

## What CMO Never Does Without Approval

- Schedule a post to go live (only Ahmed/CEO can set Status=Scheduled)
- Post a LinkedIn comment (requires CEO approval)
- Delete or archive any Notion content
- Change a post that's already Posted status

---

## Reporting Cadence

| Report | Frequency | Destination |
|--------|-----------|-------------|
| Weekly batch ready | Every Friday | CEO via sessions_send + topic 7 |
| Gap alert | As needed | CEO via sessions_send + topic 7 |
| Post failure | Immediate | CEO DM (866838380) |
| Engagement approvals | Daily (cron) | CEO DM (866838380) |
| Monthly scorecard | 1st of month | CEO via sessions_send |
