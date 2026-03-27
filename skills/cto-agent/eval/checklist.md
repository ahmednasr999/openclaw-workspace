# CTO Agent Quality Checklist

Run this checklist at the start of each standup and after any system change.
Each item is binary: **PASS** or **FAIL**. No partial credit.

---

## Checklist

### 1. Gateway Health
```bash
curl -sf http://localhost:18789/health && echo PASS || echo FAIL
```
- **Pass:** HTTP 200 response
- **Fail:** Connection refused, timeout, or non-200 response
- **If FAIL:** See `instructions/gateway.md` for restart procedure

---

### 2. Composio Tools Reachable
```bash
# Run a lightweight COMPOSIO_SEARCH_TOOLS call and verify non-empty response
# (Done via OpenClaw session, not CLI)
```
- **Pass:** COMPOSIO_SEARCH_TOOLS returns tools list with session_id
- **Fail:** Timeout, auth error, or empty response
- **If FAIL:** Check internet, check Composio dashboard at https://dashboard.composio.dev

---

### 3. Critical Crons — Last 24h
```bash
python3 /root/.openclaw/workspace/scripts/cron-dashboard-updater.py --dry-run
# Verify: daily-backup, run-briefing-pipeline, linkedin-auto-poster all ran
```
- **Pass:** All 3 critical crons show last_run within past 24 hours
- **Fail:** Any critical cron has last_run > 24h ago or shows ERROR status
- **If FAIL:** See `instructions/cron-health.md` for fix workflow

---

### 4. No Uncommitted Secrets in Workspace
```bash
cd /root/.openclaw/workspace && git diff --staged | grep -iE "(api_key|password|secret|token)" && echo FAIL || echo PASS
```
- **Pass:** No secrets found in staged changes
- **Fail:** Any API key, password, secret, or token string in staged diff
- **If FAIL:** Unstage immediately with `git reset HEAD <file>`, add to `.gitignore`

---

### 5. Backup Pushed to GitHub in Last 24h
```bash
cd /root/.openclaw/workspace && git log --remotes=origin --since="24 hours ago" --oneline | head -5
```
- **Pass:** At least 1 commit pushed to remote in last 24 hours
- **Fail:** No remote commits in last 24h
- **If FAIL:** Run `scripts/daily-backup.sh` manually, check for git race in `cron-health.md`

---

### 6. Notion API Returns 200
```bash
curl -sf -H "Authorization: Bearer $(grep NOTION_API_KEY ~/.env | cut -d= -f2)" \
  -H "Notion-Version: 2022-06-28" \
  "https://api.notion.com/v1/databases/3268d599-a162-8188-b531-e25071653203" \
  -o /dev/null -w "%{http_code}" | grep -q "200" && echo PASS || echo FAIL
```
- **Pass:** HTTP 200
- **Fail:** 401 (bad token), 403 (no access), 404, or timeout
- **If FAIL:** Check `NOTION_API_KEY` in `~/.env`, verify integration has DB access

---

### 7. All Agents in agents.md Are Reachable
```bash
# Check: Orchestrator, Chief of Staff, CV Agent, Research Agent, Writer Agent, Content Agent
# Method: sessions_list and verify expected agents are registered
```
- **Pass:** All 6 agent types can be spawned (sessions_spawn dry check succeeds)
- **Fail:** Any agent fails to initialize or model endpoint is unreachable
- **If FAIL:** See `instructions/agents.md` for model fallback chain

---

### 8. CTO Can Execute a New Script Task Autonomously
```bash
# Smoke test: create a temp script and run it
echo 'echo "CTO smoke test OK"' > /tmp/cto-smoke-test.sh
bash /tmp/cto-smoke-test.sh && echo PASS || echo FAIL
rm /tmp/cto-smoke-test.sh
```
- **Pass:** Script executes and returns expected output
- **Fail:** Permission error, shell unavailable, or exec tool blocked
- **If FAIL:** Check sandbox policy, check exec permissions

---

## Scoring

| Score | Status |
|-------|--------|
| 8/8 PASS | ✅ System healthy — proceed normally |
| 6-7/8 PASS | ⚠️ Degraded — fix failures before standup |
| <6/8 PASS | 🚨 Critical — escalate to CEO immediately |

---

## Running the Checklist

The CTO Agent runs this checklist:
1. **Daily at 8:20 AM Cairo** (before 8:30 standup post)
2. **After any system change** (cron fix, script deploy, gateway restart)
3. **On demand** when Ahmed asks "system status?"

Results are included in the daily standup message to Telegram topic 8.
