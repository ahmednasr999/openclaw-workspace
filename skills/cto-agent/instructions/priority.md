# CTO Priority Framework

How CTO triages work and allocates resources.

## Priority Levels

### 🔴 RED (Fix Now)
**Respond in <10 min. Escalate to CEO immediately.**

These are system-critical failures with immediate impact:
- **Gateway down** — No tools work, all agents blocked
- **Composio broken** — Cannot access external APIs (LinkedIn, Notion, etc.)
- **Data loss risk** — Git corruption, backup missing, database issues
- **Security breach** — Exposed API keys, .gitignore violation, unauthorized access
- **Any cron blocking multiple downstream jobs** — E.g., pipeline-sync fails → all job decisions blocked

**Response checklist:**
1. Identify root cause (logs, config, system state)
2. Attempt immediate fix (restart, config reload)
3. If fix fails: loop in CEO via sessions_send with full context
4. Post alert to topic 8 (public visibility)
5. Stay on task until resolved

**Examples:**
- "Gateway responding with 503 errors"
- "Composio SEARCH_TOOLS timing out (config issue?)"
- "Git checkout fails — disk full in workspace"
- ".env file with plaintext API key left in staging"
- "Notion sync agent down — 500 error for 2 hours"

---

### 🟠 AMBER (Fix Today)
**Respond in <2 hours. May execute autonomously if straightforward.**

Impact is limited or degraded but not blocking:
- **Single cron failure** — linkedin-engagement-agent crashed, but cv-builder still runs
- **Agent performance degradation** — 3x slower than baseline, not hanging
- **Script bug in dev** — Not yet in production, but needs fix before next deployment
- **Config drift detected** — Environment var mismatch, but current job still runs
- **Backup sync delayed** — Scheduled to run 1h ago, hasn't started yet

**Response checklist:**
1. Identify root cause
2. Fix if straightforward (edit script, test, commit, push)
3. If complex: loop in CEO for guidance
4. Update cron dashboard with status
5. Post summary to topic 8 (technical detail OK, no alarm tone)

**Examples:**
- "linkedin-auto-poster.py failed on Notion image fetch — retrying next run"
- "briefing-agent took 45s instead of 12s — memory usage spike, cleaned up temp files"
- "application-lock.py has stale cache entry — manual cleanup, re-ran pipeline sync"
- "github-backup.sh skipped (git diff empty), but backup script itself is working"

---

### 🟢 GREEN (This Week)
**Respond in 1-7 days. Low impact, can batch with other improvements.**

Nice-to-have improvements, new features, optimizations:
- **New script Ahmed requested** — Not urgent, but on roadmap
- **Code cleanup & refactor** — Existing scripts work fine, just messy
- **Performance optimization** — 5s → 2s shave on a non-critical task
- **Better logging** — Adding debug output for future diagnostics
- **Skill improvement** — Autoresearch-based optimization pass

**Response checklist:**
1. Add to backlog or weekly task list
2. Schedule time in next sprint window (if batchable)
3. Execute when gateway/crons/red items are stable
4. Commit & push when done
5. Post summary to topic 8 (optional, unless Ahmed asked for it)

**Examples:**
- "Ahmed wants a dashboard script to visualize cron health (NEW)"
- "linkedin-engagement agent could use better filtering (IMPROVEMENT)"
- "cron logs are 2GB — add rotation (OPTIMIZATION)"
- "Test suite for cto-desk-agent (NEW)"

---

## Decision Flow

```
Issue reported (Ahmed, CEO, cron failure)
    ↓
Identify symptoms
    ↓
Does it block ALL work?
    ├─ YES → RED (fix now)
    └─ NO → Affects current jobs/agents?
        ├─ YES (degraded but running) → AMBER (fix today)
        └─ NO (future work only) → GREEN (this week)
```

## Escalation to CEO

**Always loop in CEO via sessions_send if:**
1. RED priority (any red issue)
2. Unsure if fix is safe (touching shared configs)
3. Fix requires secrets or credentials CTO doesn't have
4. Ahmed messages CTO directly (always escalate, even if GREEN)
5. Change affects 2+ systems (shared impact)

**Format:**
```
CTO: [issue title]
Severity: RED / AMBER / GREEN
Root cause: [1-2 sentence explanation]
Action taken: [what CTO did or tried]
Status: [blocked / fixed / escalating]
Next step: [awaiting CEO input / ready to deploy / monitoring]
```

## Examples

### RED → CEO Escalation
```
CTO: Gateway responding with 503 errors
Severity: RED
Root cause: /root/.openclaw/openclaw.json has invalid syntax (extra comma)
Action taken: Attempted restart, gateway still fails to start
Status: Blocked
Next step: Need CEO to validate config or provide backup
```

### AMBER → CTO Self-Heal
```
CTO: linkedin-engagement-agent crashed at 01:00 Cairo
Severity: AMBER
Root cause: Exa API rate limit hit (quota exceeded for today)
Action taken: Checked cron log, valid error. Will retry at tomorrow's 01:00 run.
Status: Fixed
Next step: Monitor tomorrow's run, no action needed
```

### GREEN → Backlog
```
CTO: New request from Ahmed
Severity: GREEN
Task: Build cto-desk-agent persistent loop script
Action taken: Added to task backlog, scheduled for next sprint
Status: Scheduled
Next step: Execute when gateway/crons stable
```

---

## Time Budgets

| Severity | Max Response | Max Fix Time | Escalation |
|----------|--------------|--------------|------------|
| RED | 10 min | 30 min (then CEO) | Immediate |
| AMBER | 2 hours | 1 hour (then CEO) | If stuck |
| GREEN | 1-7 days | Open-ended | Only if blocked |

## Notes for Ahmed

CTO triages ruthlessly. Not everything is urgent.
- RED = "The ship is sinking"
- AMBER = "The engine is sputtering"
- GREEN = "Polish the railings"

If you message CTO directly, CTO will handle it AND loop in CEO. CEO always knows what CTO is doing.
