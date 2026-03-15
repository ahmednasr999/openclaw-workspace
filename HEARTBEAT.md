# HEARTBEAT.md — Periodic Tasks

*Fires every hour via OpenClaw heartbeat*
*Last updated: 2026-03-15*

## Implementation Status
- Hourly heartbeat: ✅ Running (MiniMax M2.5)
- Executive Intelligence Briefing cron: ✅ Active (6 AM Cairo daily)
- Self-audit cron: ✅ Active (nightly)
- Heartbeat hardening: ✅ Active (Mar 13, 2026)

---

## Heartbeat Rules

Do NOT fire if: Ahmed is actively in conversation.
Do NOT send noise: Only message if there's something actionable.
Model for heartbeat tasks: MiniMax M2.5 (free, never burn paid tokens on background checks)
Cost discipline: Each heartbeat costs tokens. Make it count or skip.

---

## Step 1: Run the Health Check Script

At each heartbeat, first run:
```bash
bash /root/.openclaw/workspace/scripts/heartbeat-checks.sh
```

This outputs a JSON report covering: gateway status, cron failures, bloated sessions, disk usage, deadline proximity, and model fallbacks. Read this JSON and use it for all checks below.

---

## Hourly Checks (Every Heartbeat)

### 1. 🔴 Gateway Health (CRITICAL — no cooldown)

From the script output, check `gateway.status`.

If `"down"` → message Ahmed immediately:
"🔴 Gateway DOWN. PID not found. Investigate immediately."

This is critical, no cooldown. Alert every heartbeat until resolved.

### 2. 🔴 Model Fallback Detection (CRITICAL — no cooldown)

From the script output, check `model_fallbacks` array.

If non-empty → message Ahmed immediately with each fallback event:
"🔴 Model Fallback Detected: [details from log entry]"

This violates AGENTS.md rules if silent. Always alert.

### 3. 🔴 Cron Failure Detection (CRITICAL — 24h cooldown per cron)

From the script output, check `cron_failures` array.

If non-empty → message Ahmed:
"🔴 Cron Failed: [label] (ID: [id]) — Status: [status]"

Cooldown: alert once per failed cron per 24 hours. If the same cron fails again next heartbeat and was already reported within 24h, skip.

To enforce cooldown: read `.heartbeat/state.json`, check `alerts.cron_failure.last_alerted`. If within 24h, skip. After alerting, update the timestamp.

### 4. 🟡 Session Size Monitor (24h cooldown)

From the script output, check `bloated_sessions` array.

If any session > 5MB → message Ahmed (max once/day):
"🟡 Bloated session: [filename] is [X]MB. Consider resetting."

Cooldown: 24 hours.

### 5. 🟡 Disk Space (24h cooldown)

From the script output, check `disk_usage_pct`.

| Threshold | Action |
|-----------|--------|
| > 85% | "🟡 Disk usage at [X]%. Cleanup recommended." |
| > 95% | "🔴 Disk usage CRITICAL at [X]%. Immediate action needed." |

Cooldown: 24 hours for warning, no cooldown for critical.

### 6. 🟡 Deadline Radar (6h cooldown)

From the script output, check `upcoming_deadlines` array.

If any task has a deadline within 48 hours → message Ahmed:
"🔴 Deadline Alert: [context] — [date]. Action needed."

Cooldown: 6 hours per deadline.

### 7. 🟡 Staleness Check (24h cooldown)

From the script output, check `active_tasks_age_hours`.

If > 48 → message Ahmed (max once/day):
"⚠️ active-tasks.md is [X] hours stale. Worth a refresh?"

### 8. 🔴 Scanner Output Validation (no cooldown after 7 AM)

From the script output, check `scanner` object.

| Status | Action |
|--------|--------|
| `missing` (after 7 AM) | "🔴 Scanner FAILED: No output file today. Jobs cron didn't run or crashed." |
| `empty` | "🔴 Scanner produced 0 results. Possible rate limiting or cookie expiry." |
| `exists` + total < 10 | "🟡 Scanner degraded: only [X] jobs found. Check LinkedIn cookie freshness." |

This catches the exact failure mode from March 13-15 (scanner silently returning 0 for days).

### 9. 🟡 Cron Output Validation (24h cooldown per cron)

From the script output, check `cron_output_issues` array.

If non-empty → message Ahmed for each high-severity issue:
"🔴 Cron Output Missing: [cron name] — [issue]"

Medium severity: batch into one warning.

### 10. Usage Guard (every heartbeat)

Check `session_status` for 5-hour and weekly usage pressure.

| Threshold | Action |
|-----------|--------|
| 5h remaining <= 30% | Auto-shift non-critical work to MiniMax M2.5/Kimi |
| 5h remaining <= 20% | Notify Ahmed and pause optional heavy jobs |
| Weekly remaining <= 20% | Reserve premium models for critical tasks only |

---

## Self-Healing Protocol (CRITICAL — Auto-Repair Before Alerting)

When the heartbeat script detects ANY issue (scanner failure, cron output missing, degradation, etc.), do NOT just alert Ahmed. Follow this sequence:

### Step 1: Diagnose
Read the error details from the heartbeat JSON output. Identify what failed and why.

### Step 2: Auto-Repair (Opus 4.6)
Spawn a sub-agent on Opus 4.6 to investigate and fix the issue:

```
sessions_spawn:
  model: opus46
  mode: run
  task: |
    SELF-HEALING TASK: [describe the issue]
    
    Context:
    - Heartbeat detected: [issue details]
    - Expected: [what should have happened]
    - Actual: [what happened]
    
    Instructions:
    1. Diagnose the root cause (check logs, scripts, configs)
    2. Fix it (edit scripts, restart services, refresh cookies, etc.)
    3. Re-run the failed component to verify the fix works
    4. Write a one-paragraph summary of what broke and what you fixed
    
    COMPLETION RULES:
    - You are NOT done until the fix is verified working
    - Do not summarize what you "would do." Do the work now.
    - If you hit an error, fix it or try an alternative
    - When genuinely complete, end with: TASK_COMPLETE
    
    DO NOT update MEMORY.md, GOALS.md, or active-tasks.md.
    Write fix summary to: /tmp/self-heal-[timestamp].md
```

### Step 3: Notify Ahmed (After Repair Attempt)
After the sub-agent completes (or fails), send ONE message:

**If fixed:**
```
🔧 SELF-HEALED — [HH:MM Cairo]
Issue: [what broke]
Fix: [what Opus did]
Verified: ✅ [confirmation it works now]
```

**If could not fix:**
```
🔴 NEEDS ATTENTION — [HH:MM Cairo]
Issue: [what broke]
Attempted: [what Opus tried]
Blocked: [why it couldn't fix it]
Action needed: [specific ask for Ahmed]
```

### Auto-Repair Scope (What Opus Can Fix Without Asking)
- Scanner returning 0 results → check cookie freshness, refresh if needed, re-run
- Cron output missing → re-run the cron script manually
- Gateway down → restart gateway service
- Script syntax errors → read error log, fix the script, re-run
- Rate limiting detected → increase delays, reduce search count, re-run
- Google Doc update failed → retry with direct API
- Engagement radar failed → retry with fresh Defuddle/Jina calls

### Auto-Repair Boundaries (Always Alert, Never Auto-Fix)
- Credential/token expiry (needs Ahmed to re-auth)
- Disk > 95% (needs human decision on what to delete)
- Model fallbacks (informational, no fix needed)
- Pipeline data changes (never modify job pipeline without approval)
- Anything that sends external messages (emails, LinkedIn posts, Slack)

---

## Cooldown Enforcement Protocol

After sending any alert, update `.heartbeat/state.json`:
```json
{
  "alerts": {
    "<alert_type>": {
      "last_alerted": "<ISO timestamp>",
      "cooldown_hours": <number>
    }
  }
}
```

Before sending any alert, read the state file and check:
- If `last_alerted` is null → alert is fresh, send it
- If `now - last_alerted < cooldown_hours` → skip (already reported)
- If `cooldown_hours` is 0 → always alert (critical items)

---

## Daily Checks (Once Per Day)

### Morning Briefing — HANDLED BY EXECUTIVE INTELLIGENCE BRIEFING CRON

The morning brief runs as a separate cron (daily 6 AM Cairo).
Do NOT duplicate this in heartbeat. The cron handles it.

### End of Day (9:00 PM Cairo Time)

Check `cairo_time` from script output. If between 21:00-21:59:

If no session flush detected today → message Ahmed:
"💾 No session flush detected today. Worth a 5-min memory update before you close?"

---

## Weekly Check (Every Sunday — 9:00 AM Cairo Time)

### GOALS.md Review Prompt

Message Ahmed:
"📊 Weekly Goals Review — [date]
GOALS.md was last updated [X] days ago. Worth 10 minutes to update pipeline and metrics?"

---

## Monthly Check (1st of Each Month — 9:00 AM Cairo Time)

### Workspace Health Audit

Scan the workspace structure and flag:
- Root file count > 20 (should be ~12 core files + folders)
- Any PDFs, HTMLs, PNGs, or temp files in root
- Any new directories that don't fit the established structure
- .gitignore gaps (venvs, build artifacts, temp files)
- Stale folders with no recent changes (> 60 days)

If issues found → message Ahmed with specific cleanup recommendations.
If clean → silent.

---

## Response Format

**When nothing needs action:** Reply exactly `HEARTBEAT_OK` — nothing else. No checks listed, no reasoning, no narration.

**When something needs action:** Use this format only:

```
⏰ HEARTBEAT — [HH:MM Cairo]

🔴 [Item]: [one line]
🟡 [Item]: [one line]
💸 [Item]: [one line]

Action needed: [what to do]
```

Batch all issues into ONE message. Never send multiple messages per heartbeat.
Never show the checking process. Never list what was checked and cleared. Output only what matters.

---

## Silence Rules

Never message for:
- Routine completions with no action needed
- Information Ahmed already knows
- Anything that can wait until he starts a session
- Heartbeat confirmation ("I'm alive" pings — useless noise)
- Alerts that are within cooldown window

When in doubt → stay silent. A quiet heartbeat is better than a noisy one.

---

**Links:** [[MEMORY.md]] | [[memory/active-tasks.md]] | [[AGENTS.md]] | [[GOALS.md]]
