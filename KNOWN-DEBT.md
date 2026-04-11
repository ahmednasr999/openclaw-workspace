# KNOWN-DEBT.md

## 2026-04-08

Only items not fixed during the cleanup pass.

1. **Active localhost helper services left in place intentionally**
   - `github-webhook-proxy.py` on `127.0.0.1:8791`
   - `calendar-push-receiver.py` on `127.0.0.1:8789`
   - `docker` workload on `:8080`
   These were not removed because they appear intentional and not orphaned.

2. **Disk usage still heavy by design, not obvious junk**
   - `/root/.openclaw/extensions` remains large because active plugin dependencies are installed there.
   - `/root/.openclaw/lcm.db` remains large because LCM is active and healthy.
   - `/root/.openclaw/workspace/.git` remains large, but that is repo history, not disposable junk.
