#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=/root/.openclaw/workspace
STAMP=$(date +%Y%m%d-%H%M%S)
OUT=/root/.openclaw/backups/gateway-hooks-recovery-${STAMP}
LOG=${OUT}/recovery.log
REPORT=/root/.openclaw/runtime/gateway-hooks-recovery-latest.json
mkdir -p "$OUT" "$(dirname "$REPORT")"
exec > >(tee -a "$LOG") 2>&1

started_at=$(date --iso-8601=seconds)
before_pid=$(systemctl --user show openclaw-gateway.service -p MainPID --value)
before_hooks=$(pgrep -x openclaw-hooks | wc -l)

cd "$ROOT"
security_output=$(timeout -k 5s 75s python3 scripts/check-memory-heist-security-suite.py)
grep -Fx "PASS: Memory Heist security suite 19/19" <<<"$security_output" >/dev/null

# Remove only leaked CLI/hook helpers. The gateway itself is a node process and
# is restarted separately below through this detached maintenance unit.
pgrep -x openclaw-hooks | xargs -r kill -TERM || true
pgrep -x openclaw | xargs -r kill -TERM || true
sleep 3
pgrep -x openclaw-hooks | xargs -r kill -KILL || true
pgrep -x openclaw | xargs -r kill -KILL || true

systemctl --user restart openclaw-gateway.service

pid_changed=false
for _attempt in $(seq 1 45); do
  after_pid=$(systemctl --user show openclaw-gateway.service -p MainPID --value)
  active=$(systemctl --user is-active openclaw-gateway.service || true)
  if [[ "$active" == active && -n "$after_pid" && "$after_pid" != 0 && "$after_pid" != "$before_pid" ]]; then
    pid_changed=true
    break
  fi
  sleep 2
done
[[ "$pid_changed" == true ]]

probe_ok=false
for _attempt in $(seq 1 30); do
  if timeout -k 5s 30s openclaw gateway probe --json >"$OUT/gateway-probe.json" 2>>"$LOG"; then
    if jq -e '.ok == true and .degraded == false' "$OUT/gateway-probe.json" >/dev/null; then
      probe_ok=true
      break
    fi
  fi
  pgrep -x openclaw-hooks | xargs -r kill -TERM || true
  pgrep -x openclaw | xargs -r kill -TERM || true
  sleep 2
done
[[ "$probe_ok" == true ]]

timeout -k 5s 60s openclaw config validate >"$OUT/config-validate.txt" 2>&1
timeout -k 5s 75s python3 scripts/check-openclaw-runtime-patches.py >"$OUT/runtime-patches.txt" 2>&1
timeout -k 5s 75s python3 scripts/check-memory-heist-security-suite.py >"$OUT/security-suite-after.txt" 2>&1
grep -Fx "PASS: Memory Heist security suite 19/19" "$OUT/security-suite-after.txt" >/dev/null
timeout -k 5s 60s openclaw plugins inspect memory-heist-guard --runtime --json >"$OUT/memory-heist-runtime.json" 2>&1
timeout -k 5s 60s openclaw status >"$OUT/openclaw-status.txt" 2>&1

sleep 10
after_hooks=$(pgrep -x openclaw-hooks | wc -l)
after_cli=$(pgrep -x openclaw | wc -l)
after_started=$(systemctl --user show openclaw-gateway.service -p ExecMainStartTimestamp --value)
ended_at=$(date --iso-8601=seconds)

jq -n \
  --arg startedAt "$started_at" \
  --arg endedAt "$ended_at" \
  --arg beforePid "$before_pid" \
  --arg afterPid "$after_pid" \
  --arg afterStarted "$after_started" \
  --argjson beforeHooks "$before_hooks" \
  --argjson afterHooks "$after_hooks" \
  --argjson afterCli "$after_cli" \
  --arg outputDir "$OUT" \
  '{ok:true,startedAt:$startedAt,endedAt:$endedAt,beforePid:$beforePid,afterPid:$afterPid,afterStarted:$afterStarted,beforeHooks:$beforeHooks,afterHooks:$afterHooks,afterCli:$afterCli,securitySuite:"19/19",gatewayProbe:"healthy",config:"valid",runtimePatches:"verified",outputDir:$outputDir}' \
  >"$REPORT"

echo "recovery complete: $REPORT"
