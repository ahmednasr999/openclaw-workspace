#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=/root/.openclaw/workspace
STAMP=$(date +%Y%m%d-%H%M%S)
OUT=${ROOT}/reports/gateway-autoreview-restart-${STAMP}
LATEST=${ROOT}/reports/gateway-autoreview-restart-latest.json
LOG=${OUT}/maintenance.log
SESSION_KEY=agent:main:telegram:direct:866838380

mkdir -p "$OUT"
exec > >(tee -a "$LOG") 2>&1

started_at=$(date --iso-8601=seconds)
before_pid=$(systemctl --user show openclaw-gateway.service -p MainPID --value)

notify_continuation() {
  local outcome=$1
  openclaw system event \
    --session-key "$SESSION_KEY" \
    --mode now \
    --text "Detached Codex auto-review gateway maintenance ${outcome}. Read ${LATEST} and continue Ahmed's pending turn with the verified result." \
    >/dev/null 2>&1 || true
}

on_error() {
  local code=$?
  local line=${BASH_LINENO[0]:-unknown}
  local ended_at
  ended_at=$(date --iso-8601=seconds)
  jq -n \
    --arg startedAt "$started_at" \
    --arg endedAt "$ended_at" \
    --arg beforePid "$before_pid" \
    --arg outputDir "$OUT" \
    --arg errorLine "$line" \
    --argjson exitCode "$code" \
    '{ok:false,startedAt:$startedAt,endedAt:$endedAt,beforePid:$beforePid,exitCode:$exitCode,errorLine:$errorLine,outputDir:$outputDir}' \
    >"$LATEST"
  notify_continuation failed
  exit "$code"
}
trap on_error ERR

cd "$ROOT"

test -s backups/openclaw.json.pre-approval-noise-20260811-0641
openclaw config get plugins.entries.codex.config.appServer.approvalsReviewer \
  | grep -Fx auto_review
openclaw config validate >"${OUT}/config-before.txt" 2>&1
python3 scripts/check-memory-heist-security-suite.py --require-runtime-contract \
  | grep -Fx "PASS: Memory Heist security suite 19/19"
python3 scripts/check-openclaw-runtime-patches.py >"${OUT}/runtime-patches-before.txt" 2>&1
jq -e '.default_model == "openai/gpt-5.6-sol"' config/model-router.json >/dev/null

# This script is launched from a detached transient user unit. The forced
# restart cannot sever the caller's app-server transport before the unit has
# been accepted by systemd, and the continuation event restores the user turn.
openclaw gateway restart --force --json >"${OUT}/restart.json" 2>&1

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
  if timeout -k 5s 30s openclaw gateway probe --json >"${OUT}/gateway-probe.json" 2>>"$LOG"; then
    if jq -e '.ok == true and .degraded == false' "${OUT}/gateway-probe.json" >/dev/null; then
      probe_ok=true
      break
    fi
  fi
  sleep 2
done
[[ "$probe_ok" == true ]]

after_started=$(systemctl --user show openclaw-gateway.service -p ExecMainStartTimestamp --value)
openclaw config get plugins.entries.codex.config.appServer.approvalsReviewer \
  | grep -Fx auto_review
openclaw config validate >"${OUT}/config-after.txt" 2>&1
python3 scripts/check-memory-heist-security-suite.py --require-runtime-contract \
  >"${OUT}/security-suite-after.txt" 2>&1
grep -Fx "PASS: Memory Heist security suite 19/19" "${OUT}/security-suite-after.txt" >/dev/null
python3 scripts/check-openclaw-runtime-patches.py >"${OUT}/runtime-patches-after.txt" 2>&1
openclaw plugins inspect memory-heist-guard --runtime --json \
  >"${OUT}/memory-heist-runtime.json" 2>&1
openclaw status >"${OUT}/openclaw-status.txt" 2>&1
jq -e '.default_model == "openai/gpt-5.6-sol"' config/model-router.json >/dev/null

ended_at=$(date --iso-8601=seconds)
jq -n \
  --arg startedAt "$started_at" \
  --arg endedAt "$ended_at" \
  --arg beforePid "$before_pid" \
  --arg afterPid "$after_pid" \
  --arg afterStarted "$after_started" \
  --arg outputDir "$OUT" \
  '{ok:true,startedAt:$startedAt,endedAt:$endedAt,beforePid:$beforePid,afterPid:$afterPid,afterStarted:$afterStarted,approvalsReviewer:"auto_review",gatewayProbe:"healthy",config:"valid",securitySuite:"19/19",runtimePatches:"verified",model:"openai/gpt-5.6-sol",rollbackBackup:"backups/openclaw.json.pre-approval-noise-20260811-0641",outputDir:$outputDir}' \
  >"$LATEST"

trap - ERR
notify_continuation completed
echo "maintenance complete: $LATEST"
