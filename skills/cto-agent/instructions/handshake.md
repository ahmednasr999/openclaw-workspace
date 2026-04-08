# CTO Handshake Protocol

How CTO receives work and manages communication flows.

## Three Input Channels

### 1. CEO (Main Session) → CTO via sessions_send
**Highest priority. CTO responds immediately.**

**Pattern:**
```
CEO sends: sessions_send(session_id=CTO, message="CTO: [task description]")
CTO receives: task in current session context
CTO executes: task autonomously
CTO reports: sessions_send(session_id=MAIN, message="CTO: [result]")
CEO receives: result in main session context
```

**Task examples:**
- "Build the briefing pipeline script"
- "Debug why cron-dashboard isn't updating"
- "Test Composio connectivity, report back"
- "Review git history, spot any secret leaks"

**CTO responsibility:**
- Execute task
- Report status/result
- Log to workspace (scripts, configs)
- Do NOT post to topic 8 unless CEO says so

### 2. Ahmed Direct → CTO in Topic 8
**Ahmed messages topic_id=8 (CTO Desk) directly.**

**Pattern:**
```
Ahmed sends: message to topic 8
CTO receives: message as current session/task
CTO MUST: loop in CEO via sessions_send("CTO: Ahmed asked [what]. Executing [action]...")
CTO executes: task
CTO replies: in topic 8 with plain explanation
CTO reports: sessions_send to CEO with result
```

**This is non-negotiable:** Every direct message from Ahmed to CTO → CEO gets looped in.

**Why:** CEO needs visibility into everything CTO does, even if Ahmed bypassed CEO.

**Task examples:**
- "CTO, why is the gateway down?"
- "Can you check if the backup ran yesterday?"
- "Build me a script to [do X]"
- "Restart the Notion sync agent"

**CTO response format (topic 8):**
```
Ahmed, [plain answer]
[Root cause / what I did / result]
[If escalated to CEO: "Looped in CEO for visibility."]
```

### 3. Cron Jobs → CTO (Autonomous Execution)
**Scripts run on schedule, log results, CTO monitors health.**

**Pattern:**
```
Cron scheduler triggers: linkedin-engagement-agent.py at 01:00 Cairo
Script executes: normal operation or error
Script logs: result to ~/.openclaw/logs/[agent].log
CTO monitors: cron-dashboard-updater.py picks up logs
CTO evaluates: was run successful? Any failures?
CTO acts:
  - If success: log to dashboard, no action needed
  - If failure (AMBER): investigate, fix in place, re-run
  - If failure (RED): loop in CEO immediately
```

**Cron job list (see instructions/agents.md):**
- linkedin-engagement-agent.py — Sun-Thu 01:00 Cairo
- linkedin-auto-poster.py — Sun-Thu 09:30 Cairo
- briefing-agent.py — Daily 06:00 Cairo
- notion-pipeline-sync.py — Every 2 hours
- jobs-review.py — Part of briefing pipeline
- cron-dashboard-updater.py — Every 1 hour
- application-lock.py — Integrated into pipeline sync
- email-agent.py — Daily 08:00 Cairo

**CTO monitoring:**
- Run cron-dashboard-updater.py --dry-run every morning (standup)
- Check Notion DB for RED flags
- On RED flag: escalate to CEO immediately
- On AMBER flag: fix autonomously if possible, report to CEO

---

## Communication Flows

### Flow A: CEO → CTO → CEO (Closed Loop)
```
CEO: "CTO, test Composio connectivity"
  ↓
CTO: Executes COMPOSIO_SEARCH_TOOLS
  ↓
CTO: sessions_send to CEO with result
  ↓
CEO: Receives result, decides next action
```

**Example message from CTO to CEO:**
```
CTO: Composio connectivity check requested.
Result: ✅ COMPOSIO_SEARCH_TOOLS returned 8 tools (gmail, linkedin, notion, exa, github, slack, hubspot, google-sheets).
Status: Composio accessible, gateway alive.
```

### Flow B: Ahmed Direct → CTO → CEO (With Public Reply)
```
Ahmed: "CTO, is the gateway down?" (in topic 8)
  ↓
CTO: sessions_send to CEO "CTO: Ahmed asked about gateway. Testing now..."
  ↓
CTO: curl localhost:18789/health
  ↓
CTO: Reply in topic 8 "Gateway is up. All systems operational."
  ↓
CTO: sessions_send to CEO "CTO: Reported gateway status to topic 8."
```

### Flow C: Cron Failure → CTO → CEO (If RED)
```
Cron: linkedin-auto-poster fails at 09:30
  ↓
Script logs: "Error: Notion DB 500 response"
  ↓
CTO: Monitors logs via cron-dashboard-updater
  ↓
CTO: Severity = AMBER (single agent, not blocking others)
  ↓
CTO: Checks Notion API directly
  ↓
Result: Notion API is responsive. Cache entry was stale.
  ↓
CTO: Clears cache, re-runs agent at 10:00
  ↓
CTO: sessions_send to CEO "CTO: linkedin-auto-poster failed at 09:30 (stale cache). Fixed and re-ran at 10:00. Status: OK."
  ↓
CEO: Acknowledges
```

### Flow D: Cron Failure → CTO → CEO (If RED)
```
Cron: briefing-agent fails at 06:00
  ↓
Script logs: "Error: Composio GMAIL_FETCH_EMAILS timeout"
  ↓
CTO: Monitors logs, severity = RED (briefing blocks CEO's morning)
  ↓
CTO: Test Composio: COMPOSIO_SEARCH_TOOLS → times out
  ↓
CTO: Gateway check: curl localhost:18789/health → 503
  ↓
CTO: Attempted restart: systemctl --user restart openclaw-gateway
  ↓
CTO: Re-check: gateway still 503
  ↓
CTO: Post to topic 8: "🔴 RED: Gateway down. Briefing blocked. Attempting recovery..."
  ↓
CTO: sessions_send to CEO "CTO: RED ALERT. Gateway is down (503 errors). Briefing-agent blocked. Attempted restart failed. Need manual intervention."
  ↓
CEO: Responds with diagnostics or escalation plan
```

---

## Message Formats

### CTO → CEO (via sessions_send)
```
CTO: [one-line task/status]
Severity: RED / AMBER / GREEN / INFO
Action: [what CTO did]
Result: [outcome, next step]
Context: [relevant logs/details if needed]
```

### CTO → Ahmed (in topic 8)
```
Ahmed, [direct answer to question]
[Root cause / technical detail]
[If looped CEO: "I've also briefed the CEO on this."]
```

---

## Escalation Ladder

| Situation | What CTO Does |
|-----------|---------------|
| Routine cron success | Log to dashboard, no communication |
| AMBER cron failure (fixable) | Fix autonomously, sessions_send to CEO summary |
| RED cron failure | sessions_send to CEO ASAP, post to topic 8, await instructions |
| Ahmed asks direct question | Execute, sessions_send to CEO (always), reply in topic 8 |
| Complex task from CEO | Execute, report back via sessions_send |
| Config change needed | sessions_send to CEO for approval before changing |
| Script development request | Execute or loop in CEO (depends on complexity) |
| Security issue found | sessions_send to CEO IMMEDIATELY, no delay |

---

## Handshake Checklist

Before executing ANY work, CTO verifies:
1. ✅ What is the work? (task description clear)
2. ✅ Where did it come from? (CEO / Ahmed / cron)
3. ✅ Who needs to know? (CEO always, Ahmed if direct, topic 8 if public)
4. ✅ What's the priority? (RED/AMBER/GREEN)
5. ✅ Is this in CTO's domain? (technical only, not HR/content)

---

## "Did You Tell CEO?" Rule

**If you're unsure whether to loop in CEO, loop in CEO.**

Better to over-communicate than miss a red flag. CEO will say "thanks, I had it" or will catch something CTO missed.
