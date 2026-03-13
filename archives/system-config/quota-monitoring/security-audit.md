# Security Audit — Quota Monitoring System
**Auditor:** Claude Opus 4.6 (Subagent)  
**Date:** 2026-02-27 08:28 UTC  
**Files Reviewed:** quota-monitor.js, fallback-validator.sh, workflow-guards.md  
**Severity Scale:** CRITICAL / HIGH / MEDIUM / LOW / INFO

---

## Executive Summary

The quota monitoring system has **no critical or high-severity vulnerabilities**. It is a read-heavy, local-only utility that does not expose network surfaces, accept user input from untrusted sources, or modify OpenClaw's runtime configuration. The few findings below are medium/low severity — defense-in-depth improvements, not blockers.

**Verdict: PASS with minor recommendations.**

---

## Finding 1: API Key Prefix Exposure in `validate-keys` Output
**Severity: MEDIUM**  
**File:** quota-monitor.js, line ~519  
**Issue:** The `validate-keys` command outputs the first 10 characters of each API key:  
```javascript
const prefix = key.substring(0, 10) + '***';
issues.push({ provider, issue: `OK — key present (${prefix}...)` });
```
**Output observed:** `"OK — key present (sk-cp-R4zF***...)"`

**Risk:** If this output is logged, piped to a file, or captured in a sub-agent response that gets stored in memory files, the first 10 chars of API keys are persisted in plaintext. For Anthropic keys (`sk-ant-oat01-...`), 10 chars reveals the key type but not the secret portion. For MiniMax keys, 10 chars reveals more of the actual key material.

**Recommendation:** Reduce to first 6 chars or use a fixed-length mask:
```javascript
const prefix = key.substring(0, 6) + '****';
```
Or better — just confirm presence without showing any chars:
```javascript
issues.push({ provider, issue: `OK — key present (${key.length} chars)` });
```

---

## Finding 2: Shell Injection Vector in `get_key()` / `get_agent_key()` (Theoretical)
**Severity: LOW**  
**File:** fallback-validator.sh, lines 65-78  
**Issue:** The `$1` parameter in `get_key()` is interpolated directly into a Python `-c` string:
```bash
python3 -c "
...
provider = providers.get('$1', {})
..."
```
If `$1` contained a single quote, it could break out of the Python string and execute arbitrary Python code.

**Mitigating factor:** The function is only called with values from the hardcoded `MODEL_PROVIDER` associative array — never with user-supplied input. The `set -euo pipefail` provides additional safety. This is NOT exploitable in practice.

**Recommendation:** No immediate fix needed. If this script is ever extended to accept arbitrary provider names, escape the input:
```bash
local safe_provider="${1//\'/\\\'}"
```

---

## Finding 3: Telegram Bot Token in curl Command
**Severity: LOW**  
**File:** fallback-validator.sh, line 523  
**Issue:** The Telegram bot token is passed in a curl URL:
```bash
curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" ...
```
This means:
- The token appears in `/proc/<pid>/cmdline` briefly while curl runs
- If bash debug logging (`set -x`) is ever enabled, the token would appear in logs

**Mitigating factor:** The token is read from `openclaw.json` (which is already `600` permissions), curl runs briefly, and the VPS is single-user (root). The `-s` flag suppresses curl's progress output. The token is NOT logged to `validation.log`.

**Recommendation:** No action needed for current single-user VPS setup. If this system ever runs in a multi-user environment, pass the bot token via environment variable or read from stdin.

---

## Finding 4: `daily-usage.json` World-Readable
**Severity: LOW**  
**File:** daily-usage.json (file permissions)  
**Issue:** The file is `644` (world-readable):
```
-rw-r--r-- root root daily-usage.json
```
While it contains no secrets (just token counts and timestamps), it leaks operational intelligence about model usage patterns, request counts, and cost estimates.

**Recommendation:** Set to `600`:
```bash
chmod 600 /root/.openclaw/workspace/system-config/quota-monitoring/daily-usage.json
```

---

## Finding 5: `validation-report.json` World-Readable
**Severity: INFO**  
**File:** validation-report.json (file permissions)  
**Issue:** Same as Finding 4. The report contains model health status but no secrets.

**Recommendation:** Set to `600` for consistency.

---

## Finding 6: No Input Validation on `record` Command Arguments
**Severity: LOW**  
**File:** quota-monitor.js, lines 485-490  
**Issue:** The `record` command accepts model ID and token counts from CLI args:
```javascript
const [modelId, inputTokens, outputTokens] = args;
const result = recordUsage(modelId, parseInt(inputTokens, 10), parseInt(outputTokens || '0', 10));
```
- `parseInt` with a non-numeric string returns `NaN`, which propagates into calculations
- An arbitrary `modelId` string creates a new entry in the usage store (no whitelist check)
- No upper bound check on token values (could record `999999999999`)

**Mitigating factor:** This tool is only called by NASR (the agent), not by external users. NaN values won't crash the system (they just produce `NaN` in cost calculations). Arbitrary model IDs would be harmless noise in the usage store.

**Recommendation:** Add basic validation:
```javascript
if (!MODELS[modelId]) {
  console.error(`Unknown model: ${modelId}. Known: ${Object.keys(MODELS).join(', ')}`);
  process.exit(1);
}
const inp = parseInt(inputTokens, 10);
const out = parseInt(outputTokens || '0', 10);
if (isNaN(inp) || isNaN(out) || inp < 0 || out < 0) {
  console.error('Token counts must be non-negative integers');
  process.exit(1);
}
```

---

## Finding 7: No Credential Exposure in Runtime Files
**Severity: PASS (Positive Finding)**  
**Details:** Verified that:
- `daily-usage.json` contains only token counts and timestamps — no keys
- `validation-report.json` contains only health status — no keys
- `validation.log` contains only timestamps and exit codes — no keys
- The embedded Python scripts in `fallback-validator.sh` read keys transiently (in subshell) and don't log them
- `workflow-guards.md` contains no real credentials

---

## Finding 8: No Network Surfaces Exposed
**Severity: PASS (Positive Finding)**  
**Details:** Neither script starts any listener, opens any port, or creates any network socket beyond:
- `curl` calls in `--live` mode (outbound only, to known API endpoints)
- `curl` call for Telegram notification (outbound only)

The system is purely local with no attack surface for remote exploitation.

---

## Summary Table

| # | Finding | Severity | Action Required |
|---|---------|----------|----------------|
| 1 | API key prefix exposure in validate-keys | MEDIUM | Reduce prefix to 6 chars or show only length |
| 2 | Shell injection in get_key (theoretical) | LOW | No action (hardcoded inputs) |
| 3 | Bot token in curl command | LOW | No action (single-user VPS) |
| 4 | daily-usage.json world-readable | LOW | `chmod 600` |
| 5 | validation-report.json world-readable | INFO | `chmod 600` |
| 6 | No input validation on `record` args | LOW | Add validation (nice-to-have) |
| 7 | No credential exposure in runtime files | ✅ PASS | None |
| 8 | No network surfaces exposed | ✅ PASS | None |

**Overall Security Assessment: PASS — Safe to deploy.**

---

*Audit completed 2026-02-27 08:28 UTC by Opus subagent.*
