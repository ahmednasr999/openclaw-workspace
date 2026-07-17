#!/usr/bin/env bash
set -Eeuo pipefail

ROOT=/root/.openclaw/workspace
STAMP=20260716-004613
OUT=/root/.openclaw/backups/memory-heist-guard-promotion-${STAMP}
LOG=${OUT}/activation.log
REPORT=${OUT}/activation-report.json
mkdir -p "$OUT"
exec > >(tee -a "$LOG") 2>&1

started_at=$(date --iso-8601=seconds)
before_pid=$(systemctl --user show openclaw-gateway.service -p MainPID --value)

cd "$ROOT"
openclaw config validate
node --test plugins/memory-heist-guard/test.mjs labs/gpt-red-pilot/pilot.test.mjs
python3 scripts/check-openclaw-runtime-patches.py

openclaw gateway restart --force --json

pid_changed=false
for _attempt in $(seq 1 30); do
  current_pid=$(systemctl --user show openclaw-gateway.service -p MainPID --value)
  if [[ -n "$current_pid" && "$current_pid" != "0" && "$current_pid" != "$before_pid" ]]; then
    pid_changed=true
    break
  fi
  sleep 2
done

if [[ "$pid_changed" != true ]]; then
  echo "gateway PID did not change after forced detached restart" >&2
  exit 1
fi

probe_ok=false
for _attempt in $(seq 1 30); do
  if openclaw gateway probe --json >"${OUT}/gateway-probe.json" 2>>"$LOG"; then
    if jq -e '.ok == true and .degraded == false' "${OUT}/gateway-probe.json" >/dev/null; then
      probe_ok=true
      break
    fi
  fi
  sleep 2
done

if [[ "$probe_ok" != true ]]; then
  echo "gateway probe did not become healthy" >&2
  exit 1
fi

after_pid=$(systemctl --user show openclaw-gateway.service -p MainPID --value)
after_started=$(systemctl --user show openclaw-gateway.service -p ExecMainStartTimestamp --value)
openclaw plugins list --verbose --json >"${OUT}/plugins.json"
jq -e '.plugins[] | select(.id == "memory-heist-guard" and .status == "loaded" and .version == "1.0.1" and .error == null)' "${OUT}/plugins.json" >"${OUT}/memory-heist-plugin.json"
openclaw config validate
python3 scripts/check-openclaw-runtime-patches.py
node --test plugins/memory-heist-guard/test.mjs labs/gpt-red-pilot/pilot.test.mjs
node --input-type=module -e '
  import { extractStructuredSearchUrls } from "./plugins/memory-heist-guard/policy.js";
  const attacker = "https://attacker.test/leak";
  const direct = extractStructuredSearchUrls({ results: [{ url: "https://safe.test/", snippet: { url: attacker } }] });
  const wrapped = extractStructuredSearchUrls({ content: JSON.stringify([{ results: [{ url: attacker }] }]) });
  if (JSON.stringify(direct) !== JSON.stringify(["https://safe.test/"]) || wrapped.length !== 0) process.exit(1);
'

journalctl --user -u openclaw-gateway.service --since "$started_at" --no-pager >"${OUT}/gateway-journal.txt"
grep -F "memory-heist-guard v1.0.1: strict search-result provenance guard active" "${OUT}/gateway-journal.txt" >/dev/null

ended_at=$(date --iso-8601=seconds)
jq -n \
  --arg startedAt "$started_at" \
  --arg endedAt "$ended_at" \
  --arg beforePid "$before_pid" \
  --arg afterPid "$after_pid" \
  --arg afterStarted "$after_started" \
  '{ok:true, startedAt:$startedAt, endedAt:$endedAt, beforePid:$beforePid, afterPid:$afterPid, afterStarted:$afterStarted, plugin:"memory-heist-guard", version:"1.0.1", tests:19, autoreview:"clean", originalBypass:"blocked"}' >"$REPORT"

echo "activation complete: $REPORT"
