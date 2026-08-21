#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=/root/.openclaw/workspace
STAMP=$(date +%Y%m%d-%H%M%S)
OUT=${ROOT}/reports/prompt-efficiency-phase1-restart-${STAMP}
LATEST=${ROOT}/reports/prompt-efficiency-phase1-restart-latest.json
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
    --text "Detached prompt-efficiency phase-1 maintenance ${outcome}. Read ${LATEST} and continue Ahmed's pending turn with the verified result." \
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
    '{ok:false,phase:"fresh-tail-8000",startedAt:$startedAt,endedAt:$endedAt,beforePid:$beforePid,exitCode:$exitCode,errorLine:$errorLine,outputDir:$outputDir}' \
    >"$LATEST"
  notify_continuation failed
  exit "$code"
}
trap on_error ERR

cd "$ROOT"

test -s backups/prompt-efficiency-20260816/openclaw.json.pre-runtime-pilot
test "$(openclaw config get tools.exec.mode)" = auto
test "$(openclaw config get 'agents.list[3].id')" = cmo
test "$(openclaw config get 'agents.list[3].tools.exec.node')" = 99b2230411ad696339a96f1af24f7fe0d32315a45ad5074eaff5691193dd0a5e
if openclaw config get 'agents.list[3].tools.exec.mode' >/dev/null 2>&1; then
  echo "CMO exec mode override still exists" >&2
  exit 1
fi
test "$(openclaw config get plugins.entries.lossless-claw.config.freshTailMaxTokens)" = 8000
test "$(openclaw config get plugins.entries.lossless-claw.config.summaryPrefixTargetTokens)" = 12000
openclaw config validate >"${OUT}/config-before.txt" 2>&1
python3 scripts/check-memory-heist-security-suite.py --require-runtime-contract \
  | grep -Fx "PASS: Memory Heist security suite 19/19"
python3 scripts/check-openclaw-runtime-patches.py >"${OUT}/runtime-patches-before.txt" 2>&1
jq -e '.default_model == "openai/gpt-5.6-sol"' config/model-router.json >/dev/null

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
test "$(openclaw config get tools.exec.mode)" = auto
test "$(openclaw config get plugins.entries.lossless-claw.config.freshTailMaxTokens)" = 8000
test "$(openclaw config get plugins.entries.lossless-claw.config.summaryPrefixTargetTokens)" = 12000
openclaw config validate >"${OUT}/config-after.txt" 2>&1
python3 scripts/check-memory-heist-security-suite.py --require-runtime-contract \
  >"${OUT}/security-suite-after.txt" 2>&1
grep -Fx "PASS: Memory Heist security suite 19/19" "${OUT}/security-suite-after.txt" >/dev/null
python3 scripts/check-openclaw-runtime-patches.py >"${OUT}/runtime-patches-after.txt" 2>&1
openclaw plugins inspect lossless-claw --runtime --json \
  >"${OUT}/lossless-claw-runtime.json" 2>&1
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
  '{ok:true,phase:"fresh-tail-8000",startedAt:$startedAt,endedAt:$endedAt,beforePid:$beforePid,afterPid:$afterPid,afterStarted:$afterStarted,config:"valid",securitySuite:"19/19",runtimePatches:"verified",gatewayProbe:"healthy",model:"openai/gpt-5.6-sol",globalExecMode:"auto",cmoExecMode:"inherited",freshTailMaxTokens:8000,summaryPrefixTargetTokens:12000,outputDir:$outputDir}' \
  >"$LATEST"

trap - ERR
notify_continuation completed
echo "maintenance complete: $LATEST"
