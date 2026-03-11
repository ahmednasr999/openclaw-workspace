# OPERATIONAL RELIABILITY PROTOCOL (ORP) v2

Last updated: 2026-03-01
Owner: NASR
Scope: ALL workflows, ALL models, ALL sessions, ALL sub-agents
Version: 2.0
Previous: v1.0 (2026-03-01, replaced same day after Opus review)

---

## Purpose

Prevent repeat misses by enforcing blocking gates, event-driven updates, and auditable execution across every workflow in this workspace. Reliability comes from architecture, not memory or trust.

---

## 1. State Machine

All workflows must use ordered states with defined forward and backward transitions.

```
NEW -> TRIAGED -> READY -> IN_PROGRESS -> VALIDATED -> DELIVERED -> LOGGED -> CLOSED
                                |                         |
                                v                         v
                             FAILED -----------------> ROLLED_BACK
```

Rules:
- No state skipping. Every item must pass through each state in sequence.
- FAILED state: triggered when any gate fails. Item returns to the prior valid state after remediation.
- ROLLED_BACK state: triggered when a delivered item is rejected or recalled. Requires explicit reason capture.
- LOGGED is mandatory before CLOSED. No silent completions.

---

## 2. Risk Tiers

Not all tasks need the same level of control.

### Tier 1: Full ORP (User-facing deliverables)
All 4 gates required. Pre-send validation mandatory. Automated checks where available.

Applies to:
- CV generation and delivery
- Job applications
- LinkedIn content and posts
- Emails sent on Ahmed's behalf
- Any external-facing communication

### Tier 2: Standard ORP (Internal operational tasks)
Gates A and D required. Gates B and C recommended but non-blocking.

Applies to:
- Jobs bank pipeline updates
- Memory file updates
- State file updates
- Cron and system configuration changes

### Tier 3: Lightweight (Internal bookkeeping)
Gate D only (state sync). No blocking validation required.

Applies to:
- Daily log entries
- Session flush writes
- Internal notes and context carries

---

## 3. Blocking Gates

### Gate A: Input Completeness
All required inputs exist and are non-empty before work begins.

Owner: The agent or sub-agent starting the task.
Failure action: STOP. Do not proceed. Request missing input.

### Gate B: Policy Compliance
Task follows all agreed constraints.

Checks:
- Correct model assigned (e.g., Opus 4.6 for CV work)
- Style rules followed (e.g., no em dashes, no role-specific header labels)
- Safety rules followed (e.g., dry-run approval for system changes)
- Domain-specific rules followed (see Domain Adapters)

Owner: The agent executing the task.
Failure action: STOP. Remediate before continuing.

### Gate C: Output Validation
Output passes automated and manual checks before delivery.

Checks:
- Content checks (forbidden strings, format compliance)
- File existence and readability
- Automated extraction verification (e.g., pdftotext for CVs)
- Quality threshold met (e.g., ATS score floor)

Owner: The agent delivering the output, or an automated script.
Failure action: STOP. Regenerate output. Re-validate.

### Gate D: State Sync
Source of truth is updated before announcing completion.

Checks:
- Canonical file updated (e.g., pipeline.md, active-tasks.md)
- Commit and push completed (if applicable)
- Metrics/counters updated

Owner: The agent completing the task.
Failure action: STOP. Update state first, then announce.

---

## 4. Event-Driven Update Rules

On each event, update source of truth before the next user-facing message.

| Event | Immediate Action |
|-------|-----------------|
| JD received | Update pipeline: JD Status = Full JD |
| CV generated | Update pipeline: CV link added |
| Application confirmed | Update pipeline: Stage = Applied, dates set |
| Follow-up sent | Update pipeline: follow-up logged |
| Role rejected/expired | Update pipeline: move to Inactive with reason |
| Content approved | Update content calendar status |
| System config changed | Update STATE.yaml or relevant config |

SLA definition: "Immediate" means within the same tool-call sequence, before the next reply to Ahmed. Not next session. Not later. Same execution block.

---

## 5. Enforcement

### 5.1 Automated Gate Scripts (Tier 1 workflows)

Executable validation scripts that block progression programmatically.

Location: `/root/.openclaw/workspace/scripts/orp-gates/`

| Script | Domain | What it checks |
|--------|--------|---------------|
| validate-cv.sh | CV | Model used, header content, forbidden strings, file exists, pipeline updated |
| validate-pipeline.sh | Jobs | Required fields present, no duplicate rows, metrics consistent |
| validate-content.sh | Content | Brand voice, banned words, format compliance |
| validate-system.sh | Ops | Dry-run approval exists, pre/post health check |

### 5.2 Manual Checklist (fallback for gaps not yet automated)

Used only when no automated script exists for a gate. Must be replaced by automation within 7 days of first use.

---

## 6. Exception Handling

### 6.1 Exception-First Monitoring
Only report exceptions. Never report routine green checks.

Exception classes:
- MISSING: required field absent
- MISMATCH: state does not reflect reality
- VALIDATION_FAIL: output failed a gate check
- DUPLICATE: conflicting or redundant records
- STALE: item beyond SLA without update
- BYPASS: a gate was skipped (requires approval record)

### 6.2 Bypass Protocol
Any bypass requires:
1. Explicit user approval before proceeding
2. Reason captured in writing
3. Risk assessment (LOW / MEDIUM / HIGH)
4. Recovery plan documented
5. Logged in daily notes

---

## 7. Post-Incident Hardening Loop

For every miss or failure:

1. **Identify** root cause (not symptoms)
2. **Add or tighten** the specific gate that would have caught it
3. **Automate** the check if possible (add to gate script)
4. **Test** the workflow against the original failure scenario
5. **Log** the hardening change in the ORP Change Log below

---

## 8. Domain Adapters

Each domain inherits ORP core and adds domain-specific gates.

### 8.1 CV Domain Adapter

| Gate | Check | Owner |
|------|-------|-------|
| Model | Must be Opus 4.6 | NASR (spawn sub-agent) |
| Header | Only "Ahmed Nasr" + contact line, no role/company label | Sub-agent + pdftotext validation |
| Content | No em dashes, no fabricated metrics, exact titles from master CV | Sub-agent |
| ATS Floor | Score must be 85%+ before proceeding | Sub-agent |
| Pipeline Sync | CV link added to pipeline before delivery | NASR |

### 8.2 Jobs Pipeline Domain Adapter

| Gate | Check | Owner |
|------|-------|-------|
| Intake | Every URL logged with status on receipt | NASR |
| JD Status | Updated immediately when JD is received | NASR |
| State Progression | NEW -> TRIAGED -> CV_READY -> APPLIED -> FOLLOW_UP | NASR |
| Required Fields | Company, Role, Location, ATS, Stage, JD Status, Job URL | NASR |
| Commit | Pipeline changes committed and pushed immediately | NASR |

### 8.3 Content Domain Adapter

| Gate | Check | Owner |
|------|-------|-------|
| Voice | Matches Ahmed's calibrated tone (humanizer skill) | Content sub-agent |
| Banned Words | No AI-smell words, no em dashes | Content sub-agent |
| Approval | Ahmed approves before any public posting | NASR |
| Calendar Sync | Content calendar updated on draft/post | NASR |

### 8.4 System Ops Domain Adapter

| Gate | Check | Owner |
|------|-------|-------|
| Dry Run | All locked commands shown to Ahmed first | NASR |
| Pre-Health | System status checked before changes | NASR |
| Post-Health | System status verified after changes | NASR |
| Config Schema | Verify key exists in OpenClaw schema before any config change | NASR |

---

## 9. Regular Assessment Cycle

### Weekly (Every Sunday, part of Goals Review)
- Count of gate failures this week
- Count of bypasses and reasons
- Any new hardening changes applied
- Are all Tier 1 gates automated? If not, which ones remain manual?

### Monthly (1st of each month, part of Monthly Maintenance)
- Full ORP effectiveness review
- Are domain adapters still current?
- Any new workflows that need an adapter?
- Protocol version bump if changes were made
- Stress-test: pick 3 random recent tasks and verify full state machine compliance

### Quarterly
- Strategic review: is ORP reducing misses measurably?
- Should risk tiers be adjusted?
- Should new automation be invested in?
- Protocol maturity assessment (manual -> scripted -> fully automated)

---

## 10. ORP Change Log

| Date | Version | Change | Trigger |
|------|---------|--------|---------|
| 2026-03-01 | v1.0 | Initial ORP created | CV header miss, pipeline update miss, model gate miss |
| 2026-03-01 | v2.0 | Full rebuild: risk tiers, failed states, gate owners, enforcement scripts, assessment cycle, domain adapters | Opus 4.6 review critique |

---

## 11. Adoption

This protocol is active immediately for all workflows.
Every sub-agent brief must include: "Follow ORP v2 from OPERATIONAL_RELIABILITY_PROTOCOL.md. All gates are blocking."
NASR enforces ORP on every task, every session, every model.

---

**Links:** [[AGENTS.md]] | [[SOUL.md]] | [[MEMORY.md]] | [[skills/executive-cv-builder/SKILL.md]] | [[jobs-bank/pipeline.md]]
