---
name: infra-monitor
description: "Weekly infrastructure health check: disk usage, memory, services, SSL certs, backup status."
---

# Infrastructure - Disk & Memory Monitor

Weekly server health check.

## Steps

### Step 1: Disk usage
```bash
df -h / /root
du -sh /root/.openclaw/ /root/.openclaw/workspace/ /tmp/
```
Alert if any filesystem >80% full.

### Step 2: Memory usage
```bash
free -h
```
Alert if available memory <500MB.

### Step 3: Service health
Check critical services: openclaw-gateway, tailscaled, sshd.

### Step 4: Process check
```bash
ps aux --sort=-%mem | head -10
```
Flag any runaway processes.

### Step 5: Backup status
Verify last backup exists and is recent.

### Step 6: Report
Summary of all checks with status indicators.

## Error Handling
- If any check fails: Report partial results with failed check noted
- If disk >90%: Suggest cleanup actions

## Output Rules
- No em dashes. Hyphens only.
- Plain text output, no fancy formatting
