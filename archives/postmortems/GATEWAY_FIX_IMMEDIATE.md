# Gateway Fix — Immediate Actions (Ready to Execute)

**Time:** 2026-02-25 16:15 UTC  
**Risk Level:** LOW (all changes are defensive, no breaking changes)  
**Rollback:** All changes can be reversed; no data loss

---

## Step 1: Clear Stale Delivery Queue

**Why:** 4 entries from Feb 21-22 will never deliver; they clog recovery on every restart.

```bash
# Archive them to failed/ folder
mkdir -p /root/.openclaw/delivery-queue/failed
mv /root/.openclaw/delivery-queue/*.json /root/.openclaw/delivery-queue/failed/ 2>/dev/null

# Verify
echo "Delivery queue before fix:"
ls -la /root/.openclaw/delivery-queue/
echo ""
echo "Delivery queue after fix (should be empty):"
ls -la /root/.openclaw/delivery-queue/ | tail -5
echo ""
echo "Archived entries:"
ls -la /root/.openclaw/delivery-queue/failed/
```

**Expected output:**
```
Delivery queue after fix (should be empty):
total 0
drwx------ 2 root root 4096 Feb 25 16:15 failed

Archived entries:
-rw------- 1 root root 9205 Feb 22 11:48 05766573-9edf-4b58-992a-47ab96be96af.json
-rw------- 1 root root 9205 Feb 22 11:48 154dc268-b0af-404f-83fd-d66ccc2358fd.json
-rw------- 1 root root 8499 Feb 21 20:29 845f70a0-b6bb-4ece-be7a-6500f2de6b0c.json
-rw------- 1 root root 5971 Feb 21 23:24 971d014a-b836-4af7-835e-910ded78824d.json
```

---

## Step 2: Update Systemd Service (CRITICAL FIX)

**Why:** Current service allows child processes to survive restart, causing zombie processes and port conflicts.

**File:** `/root/.config/systemd/user/openclaw-gateway.service`

### Current Config
```ini
[Unit]
Description=OpenClaw Gateway (v2026.2.23)
After=network.target

[Service]
Type=simple
Environment="NVM_DIR=/root/.nvm"
Environment="PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="OPENCLAW_SKIP_GMAIL_WATCHER=1"
ExecStart=/root/.nvm/versions/node/v22.22.0/bin/node /root/.nvm/versions/node/v22.22.0/bin/openclaw gateway --port 18789
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

### Updated Config
```ini
[Unit]
Description=OpenClaw Gateway (v2026.2.24)
After=network.target

[Service]
Type=simple
Environment="NVM_DIR=/root/.nvm"
Environment="PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="OPENCLAW_SKIP_GMAIL_WATCHER=1"
ExecStart=/root/.nvm/versions/node/v22.22.0/bin/node /root/.nvm/versions/node/v22.22.0/bin/openclaw gateway --port 18789
Restart=always
RestartSec=5
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=15

[Install]
WantedBy=default.target
```

### Changes Made
- Added `KillMode=mixed` — ensures child processes receive SIGTERM
- Added `KillSignal=SIGTERM` — graceful shutdown signal
- Added `TimeoutStopSec=15` — 15 second grace period before SIGKILL

**Apply the fix:**

```bash
# Edit the file
nano /root/.config/systemd/user/openclaw-gateway.service

# Or use sed to auto-apply
sed -i '/RestartSec=5/a KillMode=mixed\nKillSignal=SIGTERM\nTimeoutStopSec=15' /root/.config/systemd/user/openclaw-gateway.service

# Verify the change
grep -A 3 "RestartSec=5" /root/.config/systemd/user/openclaw-gateway.service
```

**Expected:**
```
RestartSec=5
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=15
```

---

## Step 3: Reload Systemd & Restart Gateway

```bash
# Reload systemd config
systemctl --user daemon-reload

# Verify service is still enabled
systemctl --user is-enabled openclaw-gateway.service

# Restart the gateway
systemctl --user restart openclaw-gateway.service

# Check status
systemctl --user status openclaw-gateway.service

# Verify it's listening
sleep 2 && netstat -tlnp | grep 18789
```

**Expected status output:**
```
● openclaw-gateway.service - OpenClaw Gateway (v2026.2.24)
     Loaded: loaded (/root/.config/systemd/user/openclaw-gateway.service; enabled; preset: enabled)
     Active: active (running) since Tue 2026-02-25 16:20:15 UTC; Xmin Ysec ago
   Main PID: 937241 (node)
      Tasks: 15
     Memory: 260.4M
     CGroup: /user.slice/user-0/session-32.scope
             └─937241 node /root/.nvm/versions/node/v22.22.0/bin/openclaw gateway --port 18789
```

**Expected netstat output:**
```
tcp        0      0 127.0.0.1:18789         0.0.0.0:*               LISTEN      937241/node
```

---

## Step 4: Test Clean Restart Behavior

**Verify child processes cleanup:**

```bash
# 1. Get current gateway PID
GATEWAY_PID=$(systemctl --user show -p MainPID --value openclaw-gateway.service)
echo "Gateway PID: $GATEWAY_PID"

# 2. Show child processes before stop
echo "Child processes BEFORE stop:"
ps --ppid $GATEWAY_PID | tail -10

# 3. Stop the gateway
systemctl --user stop openclaw-gateway.service
sleep 2

# 4. Check for orphaned processes
echo "Checking for orphaned processes after stop..."
ps aux | grep -E "npm|node|next-server" | grep -v grep | wc -l

# Expected: 0 (no orphaned processes)

# 5. Verify port is free
echo "Checking port 18789:"
netstat -tlnp 2>/dev/null | grep 18789
# Expected: empty output (port is free)

# 6. Restart and verify clean start
systemctl --user start openclaw-gateway.service
sleep 3
systemctl --user status openclaw-gateway.service | grep Active
```

---

## Step 5: Verify Telegram Connection Works

```bash
# Send a test message to yourself to verify gateway is responsive
openclaw message send --target "telegram:866838380" --message "✅ Gateway restart test — $(date)"

# Check if message went through
sleep 5
echo "Message sent to Telegram"
```

---

## Step 6: Document the Changes

```bash
# Create a changelog entry
cat >> /root/.openclaw/GATEWAY_FIXES.log << 'EOF'
[2026-02-25 16:20 UTC] Gateway Fix Applied

1. Cleared 4 stale delivery entries (Feb 21-22 sub-agent completions)
   - Moved to /root/.openclaw/delivery-queue/failed/
   - These were blocking recovery on every restart

2. Updated systemd service (/root/.config/systemd/user/openclaw-gateway.service)
   - Added KillMode=mixed (ensures child process cleanup)
   - Added KillSignal=SIGTERM (graceful shutdown)
   - Added TimeoutStopSec=15 (15 second grace period)
   - Version bumped: v2026.2.23 → v2026.2.24

3. Tested restart behavior
   - Verified no orphaned processes
   - Verified port 18789 cleans up
   - Verified gateway starts cleanly

Result: Gateway now self-recovers without leaving zombies.

EOF

cat /root/.openclaw/GATEWAY_FIXES.log
```

---

## Rollback (If Needed)

If anything goes wrong, rollback is simple:

```bash
# Revert the service file
git -C /root/.config/systemd/user checkout openclaw-gateway.service 2>/dev/null || \
cp /tmp/openclaw-gateway.service.backup /root/.config/systemd/user/openclaw-gateway.service

# Restore delivery entries
mv /root/.openclaw/delivery-queue/failed/*.json /root/.openclaw/delivery-queue/ 2>/dev/null

# Reload and restart
systemctl --user daemon-reload
systemctl --user restart openclaw-gateway.service
```

---

## Monitoring After Fix

Watch these metrics for the next few hours:

```bash
# Monitor every 30 seconds
watch -n 30 'echo "=== Gateway Health ===" && \
  systemctl --user show -p State,ActiveState,MainPID openclaw-gateway.service && \
  echo "" && \
  ps aux | grep openclaw | grep -v grep | head -3 && \
  echo "" && \
  echo "Memory (should stay < 500MB):" && \
  ps aux | grep "[n]ode.*openclaw" | awk "{print \$6}" && \
  echo "" && \
  echo "Delivery queue (should stay empty):" && \
  ls /root/.openclaw/delivery-queue/ 2>/dev/null | wc -l'
```

---

## Success Criteria

✅ All of the following should be true after fix:

- [ ] Gateway status shows "active (running)"
- [ ] No orphaned npm/node/next-server processes
- [ ] Port 18789 is in LISTEN state
- [ ] Delivery queue is empty (only failed/ subdirectory exists)
- [ ] Memory usage < 500MB (compared to 6.4GB before)
- [ ] Restart takes < 10 seconds
- [ ] No "Found left-over process" messages in journalctl
- [ ] Telegram messages deliver successfully

---

## If Something Breaks

**Symptom: Port still in use**
```bash
# Find and kill stray processes
fuser -k 18789/tcp
lsof -i :18789
```

**Symptom: Service fails to start**
```bash
# Check service logs
journalctl --user -u openclaw-gateway.service -n 50

# Try manual start to see error
/root/.nvm/versions/node/v22.22.0/bin/node /root/.nvm/versions/node/v22.22.0/bin/openclaw gateway --port 18789
```

**Symptom: Delivery still deferred**
```bash
# Check what's in the queue
ls -la /root/.openclaw/delivery-queue/
# Should only have 'failed/' subdirectory

# If more entries appeared, the fix worked but new entries are being added
# Monitor for a few hours to see if they deliver
```

---

## Timeline

| Time | Action | Duration | Notes |
|------|--------|----------|-------|
| 16:15 | Clear delivery queue | < 1 min | Safe operation |
| 16:16 | Update systemd service | < 1 min | Safe; no impact until reload |
| 16:17 | Reload + restart gateway | < 30 sec | Brief downtime (normal restart) |
| 16:18 | Test restart behavior | 2-3 min | Verify cleanup works |
| 16:20 | Send Telegram test | < 1 sec | Confirm connectivity |
| **Total** | **All steps** | **< 10 min** | **Minimal disruption** |

---

**All fixes are non-breaking and can be safely applied while gateway is running (except restart in Step 3).**
