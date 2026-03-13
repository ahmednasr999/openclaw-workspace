# Self-Improvement Engine (SIE) — Draft Spec

**Date:** 2026-03-13
**Author:** NASR
**Purpose:** System-wide self-improvement for OpenClaw - 360° coverage

---

## 1. Vision

A background engine that monitors all OpenClaw subsystems, detects patterns, learns from outcomes, and improves itself automatically. Triggered when system is idle.

## 2. Scope (A-Z)

| Area | Monitor | Action |
|------|---------|--------|
| **A**pplications | ATS scores, response rates, conversion | Log insights to CV learnings |
| **B**ackups | Git status, snapshot freshness | Auto-commit if stale |
| **C**rons | Failures, execution time | Alert if broken |
| **D**isk | Usage trends | Alert at 85%, critical at 95% |
| **E**rrors | Log patterns | Detect new error types |
| **F**eedback | User corrections | Update rules automatically |
| **G**ateway | Uptime, restarts | Escalate if unstable |
| **H**eartbeat | Check success rate | Fix or alert |
| **I**ntegrations | API health (Gmail, LinkedIn) | Reconnect if failed |
| **J**obs | Radar yield, quality | Tune filters |
| **K**nowledge | Memory gaps | Fill missing context |
| **L**earnings | Pending items | Apply unprocessed lessons |
| **M**odels | Usage, fallbacks | Optimize routing |
| **N**otifications | Alert frequency | Tune cooldowns |
| **O**utputs | CV quality, briefing accuracy | Adjust prompts |
| **P**ipeline | Conversion trends | Strategy shifts |
| **Q**uality | Content engagement | Refine posting |
| **R**eliability | Session health | Reset bloated sessions |
| **S**kills | Performance metrics | Upgrade or retire |
| **T**ools | Execution success | Fix broken tools |
| **U**ptime | System availability | Recovery orchestration |
| **V**elocity | Task throughput | Optimize workflow |
| **W**orkspace | File hygiene | Clean dead files |
| **X**ecution | Command success | Debug failures |
| **Y**ield | ROI on time spent | Prioritize wins |
| **Z**ero-downtime | Recovery time | Improve automation |

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Self-Improvement Engine                  │
├─────────────────────────────────────────────────────────────┤
│  Trigger: Idle for X minutes (configurable)                │
│  Model: MiniMax M2.5 (default), fallback to GPT-5.4       │
├─────────────────────────────────────────────────────────────┤
│  PHASE 1: Data Collection                                 │
│  ├── System health (gateway, crons, heartbeat)            │
│  ├── Pipeline metrics (applications, responses)            │
│  ├── Error logs (new patterns)                              │
│  ├── User feedback (lessons applied)                        │
│  ├── Memory quality (retrieval success)                     │
│  └── Integration status (Gmail, LinkedIn, etc.)            │
├─────────────────────────────────────────────────────────────┤
│  PHASE 2: Pattern Detection                                │
│  ├── What broke? (errors, failures)                        │
│  ├── What declined? (engagement, conversion)                │
│  ├── What's missing? (knowledge gaps)                      │
│  ├── What's working? (wins to amplify)                    │
│  └── Trends over time                                      │
├─────────────────────────────────────────────────────────────┤
│  PHASE 3: Insight Generation                               │
│  ├── Root cause analysis                                    │
│  ├── Actionable recommendations                            │
│  ├── Priority ranking (impact vs effort)                     │
│  └── Confidence score                                       │
├─────────────────────────────────────────────────────────────┤
│  PHASE 4: Action                                          │
│  ├── Auto-fix (if deterministic)                           │
│  ├── Log insight to memory/insights.md                     │
│  ├── Alert if urgent                                       │
│  └── Queue for human review (if complex)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Data Sources

| Source | File/System | Key Metrics |
|--------|-------------|-------------|
| Gateway | `openclaw status` | PID, uptime, channels |
| Crons | `openclaw cron list` | Failures, last run |
| Heartbeat | `.heartbeat/state.json` | Check success rates |
| Pipeline | Google Sheet | Applications, responses |
| Logs | `/tmp/openclaw/*.log` | Error patterns |
| Memory | `memory/*.md` | Knowledge gaps |
| Workspace | `memory/lessons-learned.md` | User corrections |
| Disk | `df -h` | Usage trends |

---

## 5. Trigger Conditions

| Trigger | Condition | Action |
|---------|-----------|--------|
| **Idle** | No active session for 30 min | Run full cycle |
| **Scheduled** | Daily at 2 AM Cairo | Full analysis |
| **Event** | Cron failure | Run targeted check |
| **Manual** | User request | Run on demand |

---

## 6. Output

### Primary: `memory/insights.md`

```markdown
# System Insights — YYYY-MM-DD

## Patterns Detected
- [pattern 1]
- [pattern 2]

## Wins Amplified
- [what's working]

## Fixes Applied
- [auto-fixes]

## Recommendations
- [for human review]

## Next Review
- [timestamp]
```

### Secondary: Alerts (if urgent)

- Telegram to Ahmed: critical issues only
- Dashboard indicator (future)

---

## 7. Exclusion List (What NOT to Improve)

- External APIs (LinkedIn, Gmail, etc.) — can't control
- User decisions (salary, location, timing) — human domain
- Market conditions (job availability) — out of scope
- Third-party service changes — monitor only

---

## 8. Constraints

- **Cost:** Must run on MiniMax M2.5 (free tier)
- **Time:** Max 5 minutes per cycle
- **Risk:** No destructive actions without approval
- **Privacy:** Insights only, no PII externalized

---

## 9. Files to Create

```
scripts/
  └── self-improvement-engine.py    # Main engine
  
memory/
  └── insights.md                   # Output log
  
.heartbeat/
  └── sie-state.json               # State tracking
```

---

## 10. Integration Points

| Existing System | Integration |
|----------------|-------------|
| Heartbeat | Use `.heartbeat/state.json` for baseline |
| Watchdog | Coordinate to avoid conflicts |
| Crons | Check failure status |
| Memory | Read/write insights |
| Lessons | Process unapplied learnings |

---

## 11. Future Enhancements (Out of Scope)

- BM25+ memory (like CashClaw)
- Self-modifying code
- Cross-instance learning
- Predictive analytics

---

## 12. Success Metrics

| Metric | Target |
|--------|--------|
| Coverage | All 26 areas (A-Z) |
| Auto-fix rate | 50%+ of issues |
| False positives | < 10% |
| Execution time | < 5 min |
| Cost per run | Near zero (MiniMax) |

---

## 13. Opus 4.6 Review Notes (Applied)

- **Full scope:** All 26 areas, no phasing. Build once.
- **Idle detection:** Use `openclaw sessions list` to check for active sessions. Trigger after 2 hours idle OR daily at 2 AM Cairo.
- **Pattern rules:** Each area has deterministic thresholds (not vague "detect patterns").
- **Auto-fix:** Log + alert for v1. Auto-fix enabled per-area as confidence builds.
- **State tracking:** `sie-state.json` tracks last run time, per-area results, and cooldowns.
- **Alert cap:** Max 1 summary per day unless critical (gateway down, disk critical).
- **CV feed:** Insights from Applications/Pipeline areas feed into CV generation.
- **Model:** MiniMax M2.5 for execution. Opus for weekly deep analysis (optional).

## 14. Deterministic Rules Per Area

| Area | Rule | Threshold |
|------|------|-----------|
| Applications | Track ATS score distribution | Log if avg drops below 85 |
| Backups | Check last git commit age | Alert if > 24h stale |
| Crons | Check failure count | Alert if > 2 consecutive failures |
| Disk | Check usage percentage | Alert at 85%, critical at 95% |
| Errors | Scan logs for new patterns | Alert if new error type appears 3x in 24h |
| Feedback | Check unprocessed corrections | Alert if > 3 unprocessed |
| Gateway | Check PID and uptime | Alert if restarted > 3x in 24h |
| Heartbeat | Check success rate | Alert if < 90% success |
| Integrations | Test Gmail, LinkedIn | Alert if API returns error |
| Jobs | Check radar yield | Alert if 0 results for 3 consecutive runs |
| Knowledge | Check memory file freshness | Alert if MEMORY.md > 7 days stale |
| Learnings | Check unapplied lessons | Alert if > 5 pending |
| Models | Check fallback frequency | Alert if fallbacks > 3 in 24h |
| Notifications | Check alert count | Auto-tune if > 5 alerts/day |
| Outputs | Check CV generation success | Log quality scores |
| Pipeline | Check conversion rate | Alert if 0 responses in 14 days |
| Quality | Check LinkedIn engagement | Log trends weekly |
| Reliability | Check session sizes | Alert if any > 5MB |
| Skills | Check skill execution errors | Alert if skill fails > 2x |
| Tools | Check tool success rate | Alert if < 80% success |
| Uptime | Check gateway availability | Alert if downtime > 5 min |
| Velocity | Count tasks completed/day | Log trend |
| Workspace | Count root files | Alert if > 20 files in root |
| Execution | Check command failure rate | Alert if > 20% failure |
| Yield | Calculate ROI metrics | Log weekly |
| Zero-downtime | Measure recovery time | Alert if > 10 min |

---

## 15. Phase 5: Improvement Suggestions (Opus 4.6 Approved)

### Concept
After the 26-area health check, the SIE generates actionable improvement suggestions that compound over time. Each run reads past suggestions, checks which were implemented, and generates NEW suggestions that build on progress.

### Architecture
- Python script collects data (Phase 1-4, already built)
- Phase 5: Bundle results into structured prompt
- Call LLM via OpenClaw cron agent (not direct API)
- LLM generates 3-5 ranked improvement suggestions
- Append to `memory/improvement-log.md`

### Data Fed to LLM
- Current insights.md (health scores, alerts, warnings)
- improvement-log.md (past suggestions + their outcomes)
- Key metrics: workspace structure, session count, error patterns
- Recent learnings from LEARNINGS.md
- Trends from sie-state.json history

### Output Format
```markdown
## Improvement Suggestions — YYYY-MM-DD HH:MM

### Previous Suggestions Status
- [DONE] description (outcome)
- [SKIPPED] description (reason)
- [PENDING] description (age: Xd)
- [EXPIRED] description (auto-archived after 7d)

### New Suggestions
1. [HIGH] [Area] Description. Rationale. Concrete action.
2. [MED] [Area] Description. Rationale. Concrete action.
3. [LOW] [Area] Description. Rationale. Concrete action.
```

### Rules
- Max 5 suggestions per run
- Priority: HIGH (system reliability), MED (optimization), LOW (nice-to-have)
- Suggestions expire after 7 days if not acted on → auto-archive
- Never auto-implement. Log only. Ahmed approves.
- Ground in real data only. No hallucinated improvements.
- Track DONE/SKIPPED/PENDING/EXPIRED per suggestion

### Implementation
- Update SIE cron prompt to include suggestion analysis
- Create `memory/improvement-log.md`
- Cron agent reads insights.md + improvement-log.md → generates suggestions
- Model: MiniMax M2.5 for daily, Opus for weekly deep analysis (optional)

**Status: Spec approved by Opus 4.6. Ready to build.**
