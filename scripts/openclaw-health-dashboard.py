#!/usr/bin/env python3
"""Compact OpenClaw health dashboard for NASR.
Read-only checks. Exits 0 for OK/WARN, 2 for CRITICAL.
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, re, sqlite3, subprocess, sys
from pathlib import Path

SESSION_KEY = "agent:main:telegram:direct:866838380"
LCM_DB = Path("/root/.openclaw/lcm.db")
PATCH_CHECKER = Path("/root/.openclaw/workspace/scripts/check-openclaw-runtime-patches.py")
REPORT_DIR = Path("/root/.openclaw/workspace/reports/health")


def run(cmd, timeout=30):
    try:
        p = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        return 124, f"TIMEOUT after {timeout}s: {cmd}\n{e.stdout or ''}{e.stderr or ''}"
    except Exception as e:
        return 99, f"ERROR running {cmd}: {e}"


def status_line(name, state, detail):
    return {"name": name, "state": state, "detail": detail}


def severity_rank(s):
    return {"OK": 0, "WARN": 1, "CRITICAL": 2}.get(s, 1)


def check_gateway():
    rc, out = run("openclaw gateway status", timeout=20)
    if rc != 0:
        return status_line("gateway", "CRITICAL", f"gateway status failed rc={rc}: {out.strip()[-500:]}")
    ok = "Connectivity probe: ok" in out and "Runtime: running" in out
    pid = re.search(r"Runtime: running \(pid ([0-9]+)", out)
    listen = re.search(r"Listening: ([^\n]+)", out)
    detail = f"pid={pid.group(1) if pid else '?'}; {listen.group(0) if listen else 'listen=?'}"
    return status_line("gateway", "OK" if ok else "WARN", detail)


def check_config():
    rc, out = run("openclaw config validate", timeout=20)
    return status_line("config", "OK" if rc == 0 else "CRITICAL", "valid" if rc == 0 else out.strip()[-500:])


def check_patches():
    if not PATCH_CHECKER.exists():
        return status_line("runtime_patches", "WARN", f"missing checker {PATCH_CHECKER}")
    rc, out = run(f"python3 {PATCH_CHECKER}", timeout=20)
    if rc == 0 and "OK:" in out:
        return status_line("runtime_patches", "OK", "; ".join([l.strip() for l in out.splitlines() if l.startswith("OK:")]))
    return status_line("runtime_patches", "CRITICAL", out.strip()[-1000:])


def check_lcm():
    if not LCM_DB.exists():
        return status_line("lcm_context", "CRITICAL", f"missing {LCM_DB}")
    con = sqlite3.connect(str(LCM_DB))
    cur = con.cursor()
    row = cur.execute("""
    SELECT c.conversation_id, c.session_id,
      (SELECT COUNT(*) FROM context_items WHERE conversation_id=c.conversation_id),
      (SELECT COALESCE(SUM(CASE WHEN ci.item_type='message' THEN m.token_count ELSE s.token_count END),0)
       FROM context_items ci LEFT JOIN messages m ON m.message_id=ci.message_id LEFT JOIN summaries s ON s.summary_id=ci.summary_id
       WHERE ci.conversation_id=c.conversation_id),
      (SELECT pending FROM conversation_compaction_maintenance WHERE conversation_id=c.conversation_id),
      (SELECT current_token_count FROM conversation_compaction_maintenance WHERE conversation_id=c.conversation_id)
    FROM conversations c WHERE session_key=? ORDER BY conversation_id DESC LIMIT 1
    """, (SESSION_KEY,)).fetchone()
    if not row:
        return status_line("lcm_context", "WARN", f"no conversation for {SESSION_KEY}")
    conv, sid, items, ctx_tokens, pending, maint_tokens = row
    state = "OK"
    issues = []
    # Pending maintenance can appear briefly after tool-heavy turns. Alert only when
    # it combines with a large context or elevated maintenance-token count.
    if pending:
        issues.append("maintenance_pending")
    if (ctx_tokens or 0) > 120000:
        state = "CRITICAL"; issues.append("context_gt_120k")
    elif (ctx_tokens or 0) > 80000 or (pending and (maint_tokens or 0) > 60000):
        state = max(state, "WARN", key=severity_rank); issues.append("context_attention")
    return status_line("lcm_context", state, f"conv={conv}; items={items}; context_tokens={ctx_tokens}; maintenance_pending={pending}; maintenance_tokens={maint_tokens}; {' '.join(issues)}")


def journal_since(minutes):
    rc, out = run(f"journalctl --user -u openclaw-gateway --since '{int(minutes)} minutes ago' --no-pager", timeout=25)
    return out if rc == 0 else ""


def check_logs(minutes=30):
    out = journal_since(minutes)
    stuck = [l for l in out.splitlines() if "stuck session" in l]
    recent_stuck = [l for l in stuck if SESSION_KEY in l]
    direct_ms = []
    for l in out.splitlines():
        if "active-memory:" in l and "directFts=1" in l:
            m = re.search(r"elapsedMs=(\d+)", l)
            if m:
                direct_ms.append(int(m.group(1)))
    state = "OK"
    detail = []
    if len(recent_stuck) >= 5:
        state = "WARN"; detail.append(f"dm_stuck_warnings={len(recent_stuck)}")
    elif recent_stuck:
        detail.append(f"dm_stuck_warnings={len(recent_stuck)}")
    if direct_ms:
        mx = max(direct_ms); med = sorted(direct_ms)[len(direct_ms)//2]
        detail.append(f"active_memory_ms median~{med} max={mx} n={len(direct_ms)}")
        if mx > 500:
            state = max(state, "WARN", key=severity_rank)
    else:
        detail.append("no active-memory samples")
    return status_line("recent_logs", state, "; ".join(detail) + (f"; last_stuck={recent_stuck[-1][-240:]}" if recent_stuck else ""))


def check_status_cli():
    # bounded probe: full status is known slow, warn only if it times out past 70s
    rc, out = run("/usr/bin/time -f 'elapsed=%e' openclaw status >/tmp/openclaw-health-status.out", timeout=75)
    m = re.search(r"elapsed=([0-9.]+)", out)
    elapsed = float(m.group(1)) if m else None
    if rc == 124:
        return status_line("openclaw_status_cli", "WARN", "timed out >75s")
    state = "OK" if elapsed is not None and elapsed < 20 else "WARN"
    return status_line("openclaw_status_cli", state, f"elapsed={elapsed if elapsed is not None else '?'}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--with-status-cli", action="store_true", help="also run slow full openclaw status timing")
    ap.add_argument("--write-report", action="store_true")
    args = ap.parse_args()

    checks = [check_gateway(), check_config(), check_patches(), check_lcm(), check_logs()]
    if args.with_status_cli:
        checks.append(check_status_cli())
    overall = max((c["state"] for c in checks), key=severity_rank)
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds"),
        "overall": overall,
        "checks": checks,
    }
    if args.write_report:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        latest = REPORT_DIR / "latest.json"
        dated = REPORT_DIR / (dt.datetime.now().strftime("%Y-%m-%d_%H%M%S") + ".json")
        latest.write_text(json.dumps(payload, indent=2) + "\n")
        dated.write_text(json.dumps(payload, indent=2) + "\n")
        payload["report"] = str(latest)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"OpenClaw health: {overall}")
        for c in checks:
            print(f"- {c['state']}: {c['name']} - {c['detail']}")
    return 2 if overall == "CRITICAL" else 0

if __name__ == "__main__":
    raise SystemExit(main())
