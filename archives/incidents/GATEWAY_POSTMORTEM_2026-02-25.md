# Gateway Crash Post-Mortem — February 25, 2026

**Investigation Date:** 2026-02-25 16:15 UTC  
**Incident Window:** 2026-02-25 15:12 – 15:49 UTC (37 minutes)  
**Impact:** Gateway unresponsive; Telegram blocked; 37 restart cycles; zombie process (PID 932407)  
**Status:** ROOT CAUSE IDENTIFIED + REMEDIATION PLAN READY

---

## Executive Summary

**What happened:**  
The gateway entered a cascading failure loop triggered by:
1. **Memory exhaustion** — peak at 6.4GB on an 8GB VPS (80% threshold breached)
2. **Unclean child process termination** — systemd's `KillMode=control-group` allowed sub-processes (npm, node, next-server) to survive SIGTERM
3. **Lock file persistence** — gateway lock file (`/root/.openclaw/gateway.lock` or similar) not cleaned up between restarts
4. **Delivery queue timeout** — 4 stale Telegram messages (from Feb 21-22) with recovery budget exhausted on every restart
5. **Restart storm** — systemd kept restarting every 5 seconds, but old processes blocked port/lock

**Result:** 37 restart attempts in 37 minutes, all failing. Zombie [openclaw-gatewa] process left running.

**Root Cause (Single Point of Failure):** Service definition lacks `KillMode=mixed` + `KillSignal=SIGKILL` to forcefully clean child processes before restart.

---

## Part 1: Gateway Crash Root Cause Analysis

### 1.1 Timeline of the Failure

| Time | Event | Evidence |
|------|-------|----------|
| **14:00-15:12** | Gateway operating normally (12m 57s CPU, 6.4GB mem peak) | Journal: healthy startup at 14:01 |
| **15:12:40** | User/system issued SIGTERM (stop signal) | Journal: "Stopping openclaw-gateway.service" |
| **15:12:41** | **CRITICAL ISSUE**: 13 child processes remain after SIGTERM | Journal: "Unit process X remains running after unit stopped" |
| **15:12:41-15:49:44** | Systemd auto-restart loop (5sec interval, 37 attempts) | NRestarts counter: 0 → 37 |
| **15:49:44** | Last restart before manual intervention | Journal: "NRestarts=37" |
| **15:50:54** | Manual `openclaw gateway restart` executed | Journal: "Found left-over process... Ignoring" |
| **15:53:52** | Fresh gateway finally starts successfully (PID 924824) | Journal: "listening on ws://127.0.0.1:18789" |

### 1.2 Root Cause: Unclean Child Process Termination

**The Problem:**

When systemd sends SIGTERM to the gateway (PID 870530), the gateway's Node.js process exits cleanly. However, the service definition has **no `KillMode=mixed`**, which means systemd relies on the default `control-group` mode:

```
KillMode=control-group (default)
↓
Sends SIGTERM to PID only
↓
Child processes (ssh-agent, PM2, npm, next-server, node) NOT terminated
↓
Systemd marks service as "stopped"
↓
But child processes still hold:
  - Port 18789 (socket)
  - Lock file
  - Memory/resources
```

**Evidence from Systemd Journal:**

```
Feb 25 15:12:41 srv1352768 systemd[1025]: openclaw-gateway.service: Unit process 232742 (ssh-agent) remains running after unit stopped.
Feb 25 15:12:41 srv1352768 systemd[1025]: openclaw-gateway.service: Unit process 690150 (PM2 v6.0.14: Go) remains running after unit stopped.
Feb 25 15:12:41 srv1352768 systemd[1025]: openclaw-gateway.service: Unit process 733305 (bash) remains running after unit stopped.
Feb 25 15:12:41 srv1352768 systemd[1025]: openclaw-gateway.service: Unit process 733306 (npm run dev) remains running after unit stopped.
Feb 25 15:12:41 srv1352768 systemd[1025]: openclaw-gateway.service: Unit process 733338 (node) remains running after unit stopped.
Feb 25 15:12:41 srv1352768 systemd[1025]: openclaw-gateway.service: Unit process 733351 (next-server (v1) remains running after unit stopped.
... [13 total processes remain]
```

**Restart Attempt:**

When systemd tries to restart, it detects the port is still in use:

```
Feb 25 15:15:31 srv1352768 node[870530]: 2026-02-25T15:15:30.980Z [gateway] signal SIGTERM received
Feb 25 15:15:31 srv1352768 node[870530]: 2026-02-25T15:15:31.027Z [gmail-watcher] gmail watcher stopped
Feb 25 15:15:31 srv1352768 systemd[1025]: openclaw-gateway.service: Unit process X remains running after unit stopped.
```

Then it tries to start again, but fails:

```
Feb 25 16:05:43 srv1352768 node[936353]: 2026-02-25T16:05:43.770+00:00 Gateway service appears enabled. Stop it first.
Feb 25 16:05:43 srv1352768 node[936353]: 2026-02-25T16:05:43.772+00:00 Tip: openclaw gateway stop
```

### 1.3 Memory Exhaustion — Secondary Factor

**Memory Peak:** Consistent 6.4GB across ALL restart cycles (Feb 25, 00:00-15:49).

This is **suspicious** — indicates:
- Either a memory leak that accumulates over the gateway's lifetime
- Or Mission Control / sub-agent processes consuming 4GB+ of the 8GB VPS

**Evidence:**

```
Feb 25 15:12:41 systemd[1025]: openclaw-gateway.service: Consumed 12min 57.560s CPU time, 6.4G memory peak, 2.3G memory swap peak.
Feb 25 15:15:31 systemd[1025]: openclaw-gateway.service: Consumed 36.023s CPU time, 6.4G memory peak, 2.3G memory swap peak.
Feb 25 15:18:10 systemd[1025]: openclaw-gateway.service: Consumed 26.973s CPU time, 6.4G memory peak, 2.3G memory swap peak.
... [repeated every 3-5 minutes]
```

**Note:** After successful restart at 16:00:20, memory dropped to **674.9MB** — indicating the old processes WERE consuming 6.4GB.

**Conclusion:** The 37 restart attempts were fighting against:
1. Old processes blocking port/lock
2. 6.4GB of zombie/orphaned memory
3. Systemd hammer-restart every 5 seconds

### 1.4 No Kernel-Level OOM Kill Detected

**Finding:** No OOM killer or segfault in dmesg or journalctl.

The gateway did not crash due to OOM — it was **forcibly stopped by user/system** (SIGTERM at 15:12:40), and then **systemd's restart logic failed**.

---

## Part 2: Deferred Delivery Entries Analysis

### 2.1 What Are the 4 Entries?

**Location:** `/root/.openclaw/delivery-queue/`

**Files:**
1. `05766573-9edf-4b58-992a-47ab96be96af.json` — Created Feb 21 (11:48 AM)
2. `154dc268-b0af-404f-83fd-d66ccc2358fd.json` — Created Feb 21 (20:29 AM)
3. `845f70a0-b6bb-4ece-be7a-6500f2de6b0c.json` — Created Feb 21 (23:24 AM)
4. `971d014a-b836-4af7-835e-910ded78824d.json` — Created Feb 22 (23:24 AM)

**Timestamps Relative to Now:**
- Entries 1-3: **4-5 days old**
- Entry 4: **3 days old**

### 2.2 Content of Each Entry

All four are **Telegram Telegram message payloads** to chat ID `866838380` (Ahmed).

**Entry Summary:**

| ID | Message | Size | Retries | Status |
|---|---|---|---|---|
| `05766573-...` | "✅ Subagent main finished" (CV for Riyadh Shared Services) | ~9KB | Unknown | DEFERRED |
| `845f70a0-...` | "✅ Subagent main finished" (CV for Riyadh Strategic PMO VRO) | ~8.5KB | Unknown | DEFERRED |
| `154dc268-...` | "✅ Subagent main finished" (CV for Carter Murray Data Services) | ~9.2KB | Unknown | DEFERRED |
| `971d014a-...` | "✅ Phase 2: Layout Shell COMPLETE" (Mission Control build results) | ~5.9KB | Unknown | DEFERRED |

**All are sub-agent completion notifications from Feb 21-22 that failed to deliver.**

### 2.3 Why Do They Keep Failing?

**Log Evidence:**

```json
{
  "subsystem": "gateway/delivery-recovery",
  "message": "Found 4 pending delivery entries — starting recovery",
  "timestamp": "2026-02-25T15:50:59.805Z"
}

{
  "subsystem": "gateway/delivery-recovery",
  "message": "Recovery time budget exceeded — 4 entries deferred to next restart",
  "timestamp": "2026-02-25T15:50:59.811Z"
}

{
  "subsystem": "gateway/delivery-recovery",
  "message": "Delivery recovery complete: 0 recovered, 0 failed, 0 skipped (max retries)",
  "timestamp": "2026-02-25T15:50:59.814Z"
}
```

**Interpretation:**

The delivery recovery system has a **time budget** (likely 50-100ms per entry, or 200-500ms total).

Four entries × ~6KB payload = too much to retry within budget → **deferred to next restart**.

**Why it repeats on every restart:**

Each gateway restart runs the same recovery logic:
1. Load 4 entries
2. Check recovery budget
3. **Budget exceeded → defer to next restart**
4. Loop repeats at next restart

**This creates a permanent loop** — the entries are never retried because:
- Recovery budget is too short to retry them
- They never expire or get moved to failed queue
- Each restart just defers them again

### 2.4 Are They Permanently Stuck?

**Answer:** Yes, in a **soft-lock state**.

They are not corrupted or unrecoverable, but they're:
1. **Too old to retry** (4-5 days)
2. **Outside recovery window** (assume Telegram rate limits kicked in)
3. **Never escalated to failed queue** (recovery times out)

**Risk:** If these persist, they will:
- Slow down every gateway startup (recovery scan)
- Eventually consume disk space if queue grows
- Represent lost sub-agent completions

---

## Part 3: Remediation & Fixes

### 3.1 Immediate Action: Clear Stale Delivery Queue

**Safe to do: YES**

These are 4-5 day old messages. If they haven't delivered by now, Telegram has likely discarded them from its ingest queue anyway.

**Steps:**

```bash
# Move stale entries to failed queue for archive
mkdir -p /root/.openclaw/delivery-queue/failed
mv /root/.openclaw/delivery-queue/*.json /root/.openclaw/delivery-queue/failed/

# Document what was cleared
echo "Cleared 4 stale delivery entries from Feb 21-22 (all sub-agent completions)" >> /root/.openclaw/delivery-queue/CLEARED_LOG.txt
```

**Verification:**

```bash
# Confirm cleared
ls /root/.openclaw/delivery-queue/ | wc -l  # Should be 0 or 1 (only subdirs)
ls /root/.openclaw/delivery-queue/failed/ | wc -l  # Should be 4
```

### 3.2 Fix #1: Update Systemd Service (CRITICAL)

**File:** `/root/.config/systemd/user/openclaw-gateway.service`

**Current Config:**
```ini
[Service]
Type=simple
Restart=always
RestartSec=5
```

**Problem:** No `KillMode=mixed`, so child processes survive SIGTERM.

**Fixed Config:**
```ini
[Service]
Type=simple
Restart=always
RestartSec=5
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=10
```

**Explanation:**
- `KillMode=mixed` — sends SIGTERM to PID + all child processes, then SIGKILL orphans
- `KillSignal=SIGTERM` — gives graceful shutdown 10 seconds
- `TimeoutStopSec=10` — after 10s, kill remaining processes with SIGKILL

**Apply Changes:**

```bash
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway
```

### 3.3 Fix #2: Add Lock File Cleanup

**File:** `/root/.openclaw/gateway-start.sh` (create if missing)

**Content:**
```bash
#!/bin/bash

# Clean up stale lock/state before starting
rm -f /root/.openclaw/gateway.lock 2>/dev/null
rm -f /tmp/openclaw/gateway.sock 2>/dev/null

# Kill any orphaned processes on port 18789
fuser -k 18789/tcp 2>/dev/null

exec /root/.nvm/versions/node/v22.22.0/bin/node /root/.nvm/versions/node/v22.22.0/bin/openclaw gateway --port 18789
```

**Update Service to Use Script:**

```ini
[Service]
ExecStart=/root/.openclaw/gateway-start.sh
```

### 3.4 Fix #3: Aggressive Delivery Queue Cleanup

**Location:** OpenClaw codebase (`delivery-recovery.ts` or equivalent)

**Current Logic:**
```
Budget: 500ms (estimated)
Items: 4 × 6KB
→ Timeout → Defer
```

**Proposed Fix:**

```typescript
// In delivery-recovery startup:

if (entries.length > 0) {
  const MAX_RETRIES = 3;
  const RECOVERY_BUDGET_MS = 5000; // 5 seconds (increased from ~500ms)
  
  for (const entry of entries) {
    if (entry.retries >= MAX_RETRIES || isStale(entry)) {
      // Move to failed queue instead of deferring forever
      moveToFailed(entry);
      log.warn(`Delivery ${entry.id} exceeded retries or is stale; archived to failed queue`);
    } else {
      // Retry if within budget
      await retryDelivery(entry);
    }
  }
}
```

**Key Changes:**
1. **Increase recovery budget** from ~500ms to 5 seconds
2. **Add retry counter** to entries (track how many times attempted)
3. **Auto-archive stale entries** (age > 24 hours) to failed queue
4. **Don't defer forever** — explicit "moved to failed" instead of silent deferral

### 3.5 Fix #4: Monitor Memory Leaks

**Action:** Investigate 6.4GB memory peak.

**Suspects:**
- Mission Control (Next.js dev/prod server)
- Embedded sub-agent processes
- QMD memory indexing (318 chunks might be cached)

**Check:**
```bash
# Break down memory usage by process
ps aux --sort=-%mem | head -20

# Monitor over time
watch -n 5 'free -m && echo "---" && top -b -n 1 | head -12'
```

**Recommendation:** Profile gateway on next startup to identify leak source.

---

## Part 4: Implementation Checklist

- [ ] **Immediate:** Clear stale delivery queue (move 4 entries to failed/)
- [ ] **Short-term (next 30 min):** Update systemd service with `KillMode=mixed`
- [ ] **Short-term:** Test restart sequence to confirm child processes cleanup
- [ ] **Medium-term:** Create gateway-start.sh with lock cleanup
- [ ] **Medium-term:** Profile memory usage to find 6.4GB leak
- [ ] **Medium-term:** Update delivery-recovery timeout + retry logic
- [ ] **Long-term:** Add monitoring alert if delivery queue > 10 entries
- [ ] **Long-term:** Add recovery budget metric to observability

---

## Part 5: Preventive Measures

### Monitor & Alert

**Add to heartbeat/monitoring:**
1. **Delivery queue size** — warn if > 5 entries
2. **Gateway restart frequency** — alert if > 5 in 10 min
3. **Memory peak** — alert if > 5GB
4. **Child process orphans** — alert if systemd reports "remains running"

### Testing

**After fixes applied:**
1. Verify child processes clean up on `systemctl --user stop openclaw-gateway`
2. Confirm restart succeeds within 5 seconds
3. Test delivery recovery with synthetic stale entries
4. Memory profile under 1-hour load

---

## Summary Table

| Issue | Root Cause | Fix | Priority | Impact |
|-------|-----------|-----|----------|--------|
| **Zombie process (PID 932407)** | Unclean child termination | `KillMode=mixed` in systemd | CRITICAL | Blocks restarts |
| **Restart storm (37 cycles)** | Lock/port held by orphans | gateway-start.sh cleanup | CRITICAL | 37 min downtime |
| **4 stale deliveries persist** | Recovery budget too short | Increase to 5s + auto-archive | HIGH | Clogs queue |
| **6.4GB memory leak** | Unknown sub-process | Profile & investigate | MEDIUM | May cause OOM |

---

## Appendix A: Commands for Immediate Recovery

```bash
# 1. Clear stale delivery queue
mkdir -p /root/.openclaw/delivery-queue/failed
mv /root/.openclaw/delivery-queue/*.json /root/.openclaw/delivery-queue/failed/ 2>/dev/null

# 2. Kill orphaned processes
sudo fuser -k 18789/tcp 2>/dev/null
sudo killall -9 npm node next-server 2>/dev/null

# 3. Reload systemd + restart
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway

# 4. Verify
systemctl --user status openclaw-gateway
ps aux | grep openclaw | grep -v grep
```

---

**Report Generated:** 2026-02-25 16:15 UTC  
**Investigator:** NASR (automated post-mortem)  
**Status:** READY FOR IMPLEMENTATION
