# Workflow Guards — Integration Guide for NASR
**Version:** 1.0 | **Created:** 2026-02-27 | **Incident:** Feb 27 07:28 UTC cascade failure

---

## Why This Exists

On Feb 27, 2026 at 07:28 UTC, 26 parallel CV generations hit Anthropic rate limits simultaneously. The fallback chain tried M2.5 — but it had an expired OAuth token. All 6 models failed in a cascade. Gmail hooks died. Heartbeats stalled. 30+ minutes of degraded service.

**This guard system prevents that.** Every large batch spawn, every gateway start, every high-parallelism task now runs a pre-check before proceeding.

---

## Guard 1: Pre-Spawn Quota Check (MANDATORY for batches ≥2)

### When to invoke

Before **any** of the following:
- Spawning 2+ sub-agents in parallel
- Running CV generation for multiple roles
- Batch job processing (screening, research, etc.)
- Any loop that will call a model >5 times

### How to invoke (in NASR's reasoning)

Before spawning agents, run this check in your internal `exec` call:

```bash
node /root/.openclaw/workspace/system-config/quota-monitoring/quota-monitor.js check-spawn <N> <model>
```

**Example — 10 CV generations on Sonnet:**
```bash
node /root/.openclaw/workspace/system-config/quota-monitoring/quota-monitor.js check-spawn 10 anthropic/claude-sonnet-4-6
```

**Decision matrix based on exit code:**

| Exit Code | Meaning | NASR Action |
|-----------|---------|-------------|
| `0` | PROCEED — quota healthy | Spawn as planned |
| `1` | CAUTION — warnings exist | Notify Ahmed, await confirmation OR switch to phased approach |
| `2` | BLOCK — quota critical | DO NOT spawn. Switch model or delay. Alert Ahmed. |

### Quick inline check pattern

When NASR is about to spawn agents, add this guard block:

```
Before spawning [N] agents for [task]:
1. Run: quota-monitor.js check-spawn N model
2. If exit=0: proceed
3. If exit=1: inform Ahmed of warnings, default to phased approach
4. If exit=2: STOP. Tell Ahmed: "⛔ Quota guard blocked spawn — [reason]. Options: [A] Delay, [B] Use M2.5, [C] Override"
```

---

## Guard 2: CV Batch Size Limiter (MANDATORY for >5 roles)

### Trigger condition
Any request to generate, tailor, or optimize CVs for more than 5 roles at once.

### Check to run

```bash
node /root/.openclaw/workspace/system-config/quota-monitoring/quota-monitor.js estimate-cv <N> anthropic/claude-sonnet-4-6
```

### Decision rules

| Batch Size | Rule |
|-----------|------|
| 1–5 roles | Proceed normally, use recommended model |
| 6–10 roles | Run estimate, confirm with Ahmed if >$1 projected cost |
| 11–26 roles | **MANDATORY PHASE**: Screen all with M2.5 first, then top-10 with Sonnet |
| >26 roles | **BLOCK until phased plan approved by Ahmed** |

### The Feb 27 Safe Pattern (Two-Phase CV Generation)

**Phase 1 — Screening with M2.5 (free, fast):**
- Spawn up to 15 M2.5 agents in parallel
- Task: "Review JD against Ahmed's profile. Score fit 1-10. Output: score, 3 gaps, recommend proceed/skip"
- M2.5 is flat-rate — no quota risk
- Wait for all to complete

**Phase 2 — Full CV tailoring with Sonnet (only top roles):**
- Take top 10 scores from Phase 1
- Spawn max 5 Sonnet agents at a time (not 10–26 simultaneously)
- 2-minute cooldown between batches
- Record usage after each batch: `quota-monitor.js record anthropic/claude-sonnet-4-6 <in> <out>`

---

## Guard 3: Gateway Startup Validation (MANDATORY on every restart)

### When
- After any `openclaw gateway restart` or `systemctl restart`
- After any model config change in `openclaw.json`
- At daily boot (via cron)

### Command

```bash
/root/.openclaw/workspace/system-config/quota-monitoring/fallback-validator.sh --quick --notify
```

Use `--live` for thorough validation (slower, ~15s):
```bash
/root/.openclaw/workspace/system-config/quota-monitoring/fallback-validator.sh --live --notify
```

### Exit code handling

| Exit | Meaning | Action |
|------|---------|--------|
| `0` | All models valid | Proceed with normal operations |
| `1` | Warnings (1-2 models degraded) | Log, notify Ahmed, continue but alert |
| `2` | Critical (primary down, <2 fallbacks) | Pause batch work, fix before proceeding |
| `3` | Fatal (most of chain invalid) | STOP all spawning. Alert Ahmed immediately. |

### NASR's duty after gateway restart

After any restart, NASR must:
1. Run `fallback-validator.sh --quick`
2. If exit≠0: Send Telegram alert to Ahmed with specific model failures
3. If exit=3: Do NOT proceed with any queued work. Block until fixed.

---

## Guard 4: Quota Status in Heartbeat (OPTIONAL but recommended)

Include quota status in every heartbeat check:

```bash
node /root/.openclaw/workspace/system-config/quota-monitoring/quota-monitor.js status
```

**Heartbeat inclusion rule:**
- If any model is in `warning` state: include one-liner in heartbeat message
- If any model is in `critical` state: interrupt normal heartbeat with urgent alert
- If all healthy: no mention needed (noise-free by default)

**Example heartbeat addition (only when needed):**
```
⚠️ Model quota alert: Claude Sonnet at 74% daily limit. Recommend M2.5 for remaining tasks today.
```

---

## Guard 5: Rate Limit Recording (AUTOMATED)

When any model call fails with HTTP 429 (rate limit), NASR must record it:

```bash
node /root/.openclaw/workspace/system-config/quota-monitoring/quota-monitor.js rate-limit anthropic/claude-sonnet-4-6
```

**This serves two purposes:**
1. Lets the monitor know quota is under pressure
2. Builds a pattern log so we can identify peak usage windows

---

## Integration Checklist for NASR

Before any major task that involves model calls, mentally run through:

```
□ How many parallel agents am I about to spawn? 
  → If >1: run check-spawn first
  → If >10: mandatory phased approach

□ Is this a CV/document generation batch?
  → If >5: run estimate-cv first
  → If >10: use M2.5 screening phase first

□ Is the gateway freshly restarted?
  → Always run fallback-validator.sh --quick

□ Has any model hit a rate limit in the last hour?
  → Check quota status before spawning more

□ Are all fallbacks healthy?
  → If <3 healthy fallbacks: do NOT spawn large batches
```

---

## Quick Reference Commands

```bash
# Status check (runs in <200ms)
node /root/.openclaw/workspace/system-config/quota-monitoring/quota-monitor.js status

# Pre-spawn check for N parallel agents
node /root/.openclaw/workspace/system-config/quota-monitoring/quota-monitor.js check-spawn N model

# Estimate CV batch cost
node /root/.openclaw/workspace/system-config/quota-monitoring/quota-monitor.js estimate-cv N

# Validate fallback chain (quick, format-only)
/root/.openclaw/workspace/system-config/quota-monitoring/fallback-validator.sh --quick

# Validate fallback chain (live API ping)
/root/.openclaw/workspace/system-config/quota-monitoring/fallback-validator.sh --live

# Record usage after batch completes
node /root/.openclaw/workspace/system-config/quota-monitoring/quota-monitor.js record MODEL IN_TOKENS OUT_TOKENS

# Reset daily counters (run at midnight UTC via cron)
node /root/.openclaw/workspace/system-config/quota-monitoring/quota-monitor.js reset
```

---

## Suggested Cron Additions

> ⚠️ These are DRY-RUN suggestions — Ahmed must approve before adding to crontab

```cron
# Reset quota counters at midnight UTC
0 0 * * * node /root/.openclaw/workspace/system-config/quota-monitoring/quota-monitor.js reset >> /root/.openclaw/workspace/system-config/quota-monitoring/reset.log 2>&1

# Daily startup validation at 06:00 UTC (before morning briefing)
0 6 * * * /root/.openclaw/workspace/system-config/quota-monitoring/fallback-validator.sh --quick --notify >> /root/.openclaw/workspace/system-config/quota-monitoring/validation.log 2>&1

# Quota status check every 4 hours (no notification unless warning/critical)
0 */4 * * * node /root/.openclaw/workspace/system-config/quota-monitoring/quota-monitor.js status >> /root/.openclaw/workspace/system-config/quota-monitoring/quota.log 2>&1
```

---

## The Feb 27 Failure — Annotated

```
07:28 UTC — 26 CV generation agents spawned simultaneously
           → NO pre-spawn check (this guard didn't exist yet)
           
07:29 UTC — Anthropic Sonnet/Opus/Haiku hit rate limits
           → All 3 Anthropic models fail

07:29 UTC — Fallback tries MiniMax M2.5
           → FAILS: OAuth token expired/invalid (NOT caught at startup)

07:29 UTC — Fallback tries Kimi K2.5 
           → FAILS: also rate-limited (shared peak-time pressure)

07:29 UTC — Fallback tries GPT-5.1
           → FAILS: rate-limited

07:29 UTC — ALL 6 models exhausted simultaneously
           → Gmail hooks fail, heartbeats stall
           
08:00 UTC — Anthropic rate limits begin resetting
           → Service gradually recovers over ~30 minutes
```

**With these guards in place:**
- The pre-spawn check at step 1 would have blocked the 26-parallel spawn
- The gateway startup validator would have flagged the M2.5 OAuth issue at boot
- Maximum recommended parallel for Sonnet with typical daily usage: 10 agents
- The two-phase approach would have used M2.5 for screening, limiting Sonnet exposure

---

*Maintained by NASR. Do not modify without reviewing quota-monitor.js model definitions.*
