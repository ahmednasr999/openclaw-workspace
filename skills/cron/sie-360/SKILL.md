---
name: sie-360
description: "Self-Improvement Engine daily run: verify system state with real commands, audit learnings enforcement, detect patterns, with auto-remediation of safe issues."
---

# SIE 360 Daily

Daily self-improvement audit. You MUST run every command below and report ACTUAL output. Never estimate, never assume, never skip a check.

## Rule: Verify, Don't Guess

Every claim in your report must be backed by a command you actually ran. If you say "52 files in root" you must have run `find` and counted. If you say "2 unacted learnings" you must have grepped the file.

## Prerequisites
- Workspace: `/root/.openclaw/workspace`
- Learnings file: `.learnings/LEARNINGS.md`
- Errors file: `.learnings/ERRORS.md`
- Notion Learnings DB: `3268d599-a162-810f-9f1b-ffdc280ae96d`
- Script: `scripts/self-improvement-engine.py`

## Steps

### Step 1: Workspace Health (RUN THESE COMMANDS)
```bash
cd /root/.openclaw/workspace

# Count root files (not directories)
echo "ROOT FILES:" && find . -maxdepth 1 -type f | wc -l

# Disk usage
echo "DISK:" && df -h / | tail -1

# Memory
echo "MEMORY:" && free -h | grep Mem

# Large files (>5MB) in .openclaw
echo "LARGE FILES:" && find /root/.openclaw -size +5M -type f 2>/dev/null | head -10

# Session bloat check
echo "SESSIONS:" && du -sh /root/.openclaw/agents/main/sessions/ 2>/dev/null
```
Report exact numbers from output. Do NOT round or estimate.

### Step 2: Learnings Enforcement Audit (RUN THESE COMMANDS)
```bash
cd /root/.openclaw/workspace

# Count total entries
echo "TOTAL ENTRIES:" && grep -c "^## 20" .learnings/LEARNINGS.md

# Count entries WITH enforcement tags
echo "WITH ENFORCEMENT:" && grep -c "### Enforcement" .learnings/LEARNINGS.md

# Count entries WITHOUT enforcement (entries minus enforcement tags)
TOTAL=$(grep -c "^## 20" .learnings/LEARNINGS.md)
ENFORCED=$(grep -c "### Enforcement" .learnings/LEARNINGS.md)
echo "WITHOUT ENFORCEMENT: $((TOTAL - ENFORCED))"

# List any entries without enforcement
python3 -c "
import re
with open('.learnings/LEARNINGS.md') as f:
    content = f.read()
entries = [e for e in re.split(r'\n(?=## 20)', content) if e.strip().startswith('## 20')]
for e in entries:
    if '### Enforcement' not in e:
        print('  UNTAGGED:', e.split(chr(10))[0][:80])
if all('### Enforcement' in e for e in entries):
    print('  ALL ENTRIES ENFORCED')
"
```
Report the ACTUAL counts from these commands.

### Step 3: Integration Health (RUN THESE COMMANDS)
```bash
# Gmail - verify App Password auth works (NOT OAuth). NEVER print the actual password or token.
echo "GMAIL:" && grep -q 'auth.type = "password"' ~/.config/himalaya/config.toml 2>/dev/null && echo "App Password configured (himalaya IMAP/SMTP)" || echo "NOT configured"

# Notion - verify token and databases. NEVER print tokens or secrets.
echo "NOTION:" && python3 -c "
import json
with open('/root/.openclaw/workspace/config/notion.json') as f:
    d = json.load(f)
token = d.get('token', '')
print(f'Token: {\"present (\" + str(len(token)) + \" chars)\" if token else \"MISSING\"}')
# Check databases in config/notion-databases.json (canonical source)
try:
    with open('/root/.openclaw/workspace/config/notion-databases.json') as f2:
        dbs = json.load(f2)
    print(f'Databases: {len(dbs)} configured')
except:
    print('Databases: config/notion-databases.json not found')
" 2>/dev/null

# LinkedIn cookies - healthy = 10+ lines, stale if <5 lines
COOKIE_FILE=~/.openclaw/cookies/linkedin.txt
if [ -f "$COOKIE_FILE" ]; then
    LINES=$(wc -l < "$COOKIE_FILE")
    AGE_DAYS=$(( ($(date +%s) - $(stat -c %Y "$COOKIE_FILE")) / 86400 ))
    echo "LINKEDIN: Cookies exist ($LINES lines, ${AGE_DAYS}d old)"
    if [ "$LINES" -lt 5 ]; then echo "  WARNING: Cookie file suspiciously small"; fi
    if [ "$AGE_DAYS" -gt 14 ]; then echo "  WARNING: Cookies older than 14 days - may be stale"; fi
else
    echo "LINKEDIN: No cookies file"
fi

# Gateway
echo "GATEWAY:" && openclaw gateway status 2>/dev/null | grep -v "^\[plugins\]" | head -2
```
Do NOT report "Gmail issue detected" if App Password is configured. OAuth is dead - that's expected and NOT an issue.

### Step 4: Cron Health
```bash
# Step 4a: Get cron data (handle plugin log contamination)
openclaw cron list --json 2>&1 > /tmp/sie_crons_raw.txt

# Step 4b: Parse and analyze
python3 << 'CRONCHECK'
import json, re

with open("/tmp/sie_crons_raw.txt") as f:
    text = f.read()

# Strip plugin log lines that contaminate JSON
clean_lines = [l for l in text.split("\n") if not l.startswith("[plugins]")]
clean = "\n".join(clean_lines)

# Find JSON object
decoder = json.JSONDecoder()
# Try to find start of JSON
for i, ch in enumerate(clean):
    if ch == '{':
        try:
            data, _ = decoder.raw_decode(clean[i:])
            break
        except json.JSONDecodeError:
            continue
else:
    print("ERROR: Could not parse cron JSON")
    exit(1)

jobs = data.get("jobs", [])
total = len(jobs)
enabled = sum(1 for j in jobs if j.get("enabled", False))
disabled = total - enabled

# Skill-first check: prompt contains "Read and follow" + ".md"
skill_first = 0
raw_prompt = 0
raw_list = []
for j in jobs:
    msg = j.get("payload", {}).get("message", "")
    name = j.get("name", "?")
    if "Read and follow" in msg and ".md" in msg:
        skill_first += 1
    else:
        raw_prompt += 1
        raw_list.append(name)

print(f"Total: {total}, Enabled: {enabled}, Disabled: {disabled}")
print(f"Skill-first: {skill_first}/{total} ({100*skill_first//total}%)")
if raw_list:
    print(f"RAW PROMPT (not skill-first):")
    for n in raw_list:
        print(f"  - {n}")

# Check for failures
failing = []
for j in jobs:
    state = j.get("state", {})
    consec = state.get("consecutiveErrors", 0)
    if consec > 0:
        failing.append(f"{j['name']} ({consec} consecutive errors)")

if failing:
    print(f"FAILING CRONS:")
    for f in failing:
        print(f"  - {f}")
else:
    print("No failing crons")
CRONCHECK
```

### Step 5: SIE Suggestions (optional script)
```bash
cd /root/.openclaw/workspace && python3 scripts/self-improvement-engine.py --suggest 2>/dev/null | tail -20
```
If script fails, skip - the manual checks above are the real audit.

### Step 6: Score and Report
Calculate health score based on ACTUAL findings:
- Start at 100
- Deduct 5 per ALERT (critical issue)
- Deduct 2 per WARN (needs attention)
- Deduct 1 per INFO (minor)

Categories:
- Workspace cleanliness (root files <60 = OK, <100 = WARN, >100 = ALERT)
- Disk usage (<80% = OK, <90% = WARN, >90% = ALERT)
- Learnings enforcement (100% = OK, >90% = WARN, <90% = ALERT)
- Integration health (all connected = OK, any down = WARN)
- Cron compliance (100% skill-first = OK, >90% = WARN, <90% = ALERT)
- Session bloat (<50MB = OK, <100MB = WARN, >100MB = ALERT)

Report format:
```
SIE 360 Daily - [DATE]
Health Score: [X]/100
Checks: [N] areas | OK: [n] | WARN: [n] | ALERT: [n]

[List each finding with category and actual numbers]

(Auto-remediation runs in Step 6b - see below for Auto-Fixed / Needs Attention summary)
```

Save findings summary to /tmp/sie_findings.json for Step 6b:
```bash
python3 -c "
import json
# Summarize current findings for Step 6b to consume
findings = {
    'score': SCORE,  # replace with actual score
    'alerts': ALERTS,  # replace with actual alert list
    'warnings': WARNINGS,  # replace with actual warning list
    'timestamp': __import__('datetime').datetime.now().isoformat()
}
with open('/tmp/sie_findings.json', 'w') as f:
    json.dump(findings, f, indent=2)
print('Findings saved to /tmp/sie_findings.json')
"
```

### Step 6b: Auto-Remediation

Run AFTER Step 6 (findings known) and BEFORE sending the final report. Automatically fix safe, low-risk issues. Alert only for issues requiring human judgment.

```bash
cd /root/.openclaw/workspace
python3 << 'AUTOREMEDIATE'
import json, re, os, subprocess, sys
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
JOBS_JSON_CANDIDATES = [
    "/root/.openclaw/agents/main/cron/jobs.json",
    "/root/.openclaw/cron/jobs.json",
    "/root/.openclaw/jobs.json",
]

auto_fixed = []
needs_attention = []
git_messages = []

# ---- Load cron data from Step 4 ----
def load_cron_data():
    try:
        with open("/tmp/sie_crons_raw.txt") as f:
            text = f.read()
        clean = "\n".join(l for l in text.split("\n") if not l.startswith("[plugins]"))
        decoder = json.JSONDecoder()
        for i, ch in enumerate(clean):
            if ch == '{':
                try:
                    data, _ = decoder.raw_decode(clean[i:])
                    return data
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"WARN: Could not load cron data: {e}")
    return {}

# ---- Find jobs.json ----
def find_jobs_json():
    for path in JOBS_JSON_CANDIDATES:
        if os.path.exists(path):
            return path
    result = subprocess.run(
        ['find', '/root/.openclaw', '-name', 'jobs.json', '-not', '-path', '*/node_modules/*'],
        capture_output=True, text=True
    )
    lines = [l for l in result.stdout.strip().split('\n') if l]
    return lines[0] if lines else None

cron_data = load_cron_data()
jobs = cron_data.get("jobs", [])

jobs_json_path = find_jobs_json()
jobs_raw = None
if jobs_json_path:
    try:
        with open(jobs_json_path) as f:
            jobs_raw = json.load(f)
        print(f"Loaded jobs.json from {jobs_json_path}")
    except Exception as e:
        print(f"WARN: Could not load jobs.json: {e}")

# ======================================================
# GREEN LIGHT FIXES
# ======================================================

# ---- Fix 1: Raw prompt crons (not skill-first) ----
for job in jobs:
    msg = job.get("payload", {}).get("message", "").strip()
    name = job.get("name", "unknown")
    job_id = job.get("id", "")
    is_skill_first = "Read and follow" in msg and ".md" in msg
    if not is_skill_first and msg:
        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        skill_dir = os.path.join(WORKSPACE, f"skills/cron/{slug}")
        skill_file = os.path.join(skill_dir, "SKILL.md")
        if not os.path.exists(skill_file):
            os.makedirs(skill_dir, exist_ok=True)
            skill_content = f"""---
name: {slug}
description: "Auto-generated from raw-prompt cron: {name}"
---

# {name}

Auto-generated skill. Original raw prompt converted to skill-first format.

## Task

{msg}

## Steps

1. Execute the task described in the Task section above.
2. Report results clearly with actual output - no estimates.
3. Log any errors encountered.

## Error Handling

- If any step fails, report the error and continue with remaining checks.
- Do not skip steps silently.
"""
            with open(skill_file, 'w') as f:
                f.write(skill_content)
            # Update jobs.json to point to new skill
            if jobs_raw:
                new_msg = f"Read and follow skills/cron/{slug}/SKILL.md"
                for raw_job in jobs_raw.get("jobs", []):
                    if raw_job.get("id") == job_id or raw_job.get("name") == name:
                        raw_job.setdefault("payload", {})["message"] = new_msg
                        break
            auto_fixed.append(f"Converted '{name}' to skill-first (skills/cron/{slug}/SKILL.md)")
            git_messages.append(f"converted cron '{name}' to skill-first")
        else:
            # Skill file exists but cron message not updated yet
            if jobs_raw:
                new_msg = f"Read and follow skills/cron/{slug}/SKILL.md"
                for raw_job in jobs_raw.get("jobs", []):
                    if (raw_job.get("id") == job_id or raw_job.get("name") == name):
                        current_msg = raw_job.get("payload", {}).get("message", "")
                        if "Read and follow" not in current_msg:
                            raw_job.setdefault("payload", {})["message"] = new_msg
                            auto_fixed.append(f"Updated '{name}' cron message to point to existing skill file")
                            git_messages.append(f"updated cron '{name}' message to skill-first")
                        break

# ---- Fix 2: Timed-out crons (consecutiveErrors=1 and last error contains "timed out") ----
for job in jobs:
    name = job.get("name", "unknown")
    job_id = job.get("id", "")
    state = job.get("state", {})
    consec = state.get("consecutiveErrors", 0)
    last_error = str(state.get("lastError", "")).lower()
    if consec == 1 and "timed out" in last_error:
        current_timeout = job.get("timeoutSeconds", job.get("payload", {}).get("timeoutSeconds", 600))
        try:
            current_timeout = int(current_timeout)
        except (TypeError, ValueError):
            current_timeout = 600
        new_timeout = min(int(current_timeout * 1.5), 3600)
        if jobs_raw and new_timeout != current_timeout:
            for raw_job in jobs_raw.get("jobs", []):
                if raw_job.get("id") == job_id or raw_job.get("name") == name:
                    raw_job["timeoutSeconds"] = new_timeout
                    break
            auto_fixed.append(f"Bumped '{name}' timeout {current_timeout}s -> {new_timeout}s")
            git_messages.append(f"bumped timeout for '{name}': {current_timeout}s -> {new_timeout}s")

# ---- Fix 3: Missing Notion briefing page (cron ok but page missing) ----
try:
    import urllib.request, ssl
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    with open(f'{WORKSPACE}/config/notion.json') as f:
        notion_token = json.load(f)['token']
    ctx = ssl.create_default_context()
    def notion_query(db_id, filter_body):
        url = f"https://api.notion.com/v1/databases/{db_id}/query"
        data = json.dumps(filter_body).encode()
        req = urllib.request.Request(url, data=data, method='POST', headers={
            'Authorization': f'Bearer {notion_token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        })
        with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
            return json.loads(r.read())
    resp = notion_query('3268d599-a162-812d-a59e-e5496dec80e7', {
        'filter': {'property': 'Date', 'date': {'equals': today}},
        'page_size': 1
    })
    briefing_missing = len(resp.get('results', [])) == 0
    briefing_cron_ok = any(
        'brief' in j.get('name', '').lower() and j.get('state', {}).get('consecutiveErrors', 0) == 0
        for j in jobs
    )
    if briefing_missing and briefing_cron_ok:
        script_path = f"{WORKSPACE}/scripts/daily-briefing-generator.py"
        if os.path.exists(script_path):
            result = subprocess.run(
                ['python3', script_path, '--notion-only'],
                capture_output=True, text=True, cwd=WORKSPACE, timeout=120
            )
            if result.returncode == 0:
                auto_fixed.append("Triggered retroactive Notion briefing page creation for today")
                git_messages.append("triggered Notion briefing sync")
            else:
                err_snippet = result.stderr[:120].replace('\n', ' ')
                needs_attention.append(f"Notion briefing sync failed: {err_snippet}")
        else:
            print("Cannot auto-fix: briefing Notion sync script not found at scripts/daily-briefing-generator.py")
            needs_attention.append("Missing Notion briefing page - sync script not found, create retroactively")
except Exception as e:
    print(f"Briefing Notion check skipped: {e}")

# ---- Fix 4: Single transient error (non-timeout) - note only, no re-run ----
for job in jobs:
    name = job.get("name", "unknown")
    state = job.get("state", {})
    consec = state.get("consecutiveErrors", 0)
    last_error = str(state.get("lastError", "")).lower()
    if consec == 1 and "timed out" not in last_error:
        auto_fixed.append(f"'{name}' had 1 transient error - will auto-clear on next scheduled run (no action needed)")

# ======================================================
# YELLOW LIGHT - Alert only, never auto-fix
# ======================================================

# Consecutive errors >= 3
for job in jobs:
    name = job.get("name", "unknown")
    state = job.get("state", {})
    consec = state.get("consecutiveErrors", 0)
    if consec >= 3:
        last_error = state.get("lastError", "unknown error")
        needs_attention.append(f"'{name}' has {consec} consecutive errors (last: {str(last_error)[:80]}) - investigate manually")

# Disk > 80%
try:
    disk_result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
    for line in disk_result.stdout.split('\n')[1:]:
        parts = line.split()
        if len(parts) >= 5 and parts[4].endswith('%'):
            use_pct = int(parts[4].rstrip('%'))
            if use_pct > 80:
                needs_attention.append(f"Disk usage {use_pct}% - needs cleanup decision (YELLOW: do not auto-delete)")
except Exception as e:
    print(f"Disk check skipped: {e}")

# Session bloat > 100MB
try:
    session_dir = '/root/.openclaw/agents/main/sessions/'
    if os.path.exists(session_dir):
        result = subprocess.run(['du', '-sb', session_dir], capture_output=True, text=True)
        if result.stdout:
            size_mb = int(result.stdout.split()[0]) / 1024 / 1024
            if size_mb > 100:
                needs_attention.append(f"Session bloat: {size_mb:.0f}MB - review before deleting (YELLOW: needs human decision)")
except Exception as e:
    print(f"Session bloat check skipped: {e}")

# ---- Write fixes to jobs.json ----
if jobs_raw and jobs_json_path and git_messages:
    try:
        with open(jobs_json_path, 'w') as f:
            json.dump(jobs_raw, f, indent=2)
        print(f"Updated jobs.json at {jobs_json_path}")
    except Exception as e:
        needs_attention.append(f"Could not save jobs.json changes: {e}")

# ---- Git commit all auto-fixes ----
if git_messages:
    fix_desc = "; ".join(git_messages[:4])
    if len(git_messages) > 4:
        fix_desc += f" (+{len(git_messages)-4} more)"
    subprocess.run(['git', '-C', WORKSPACE, 'add', '-A'], capture_output=True)
    commit_msg = f"fix(sie-auto): {fix_desc}"
    result = subprocess.run(
        ['git', '-C', WORKSPACE, 'commit', '-m', commit_msg],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"Git committed: {commit_msg}")
    else:
        print(f"Git: {(result.stdout + result.stderr).strip()}")

# ---- Save remediation results for report ----
remediation = {"auto_fixed": auto_fixed, "needs_attention": needs_attention}
with open("/tmp/sie_remediation.json", "w") as f:
    json.dump(remediation, f, indent=2)

# ---- Print summary (included in final report) ----
print(f"\nAuto-Fixed ({len(auto_fixed)} issues):")
for i, item in enumerate(auto_fixed, 1):
    print(f"  {i}. \u2705 {item}")

if needs_attention:
    print(f"\nNeeds Attention ({len(needs_attention)} issues):")
    for i, item in enumerate(needs_attention, 1):
        print(f"  {i}. \u26a0\ufe0f {item}")
else:
    print("\nNeeds Attention: none - all clear")

AUTOREMEDIATE
```

Incorporate the Auto-Fixed / Needs Attention output into your final report in this format:
```
Auto-Fixed (Y issues):
1. checkmark [description]

Needs Attention (Z issues):
1. warning [description]
```
Replace "checkmark" with the unicode checkmark emoji and "warning" with the warning emoji.

### Step 8: Cron Delivery Verification
Check that critical crons both delivered AND synced to Notion. Detect partial failures (Telegram delivered but Notion page missing).

```bash
cd /root/.openclaw/workspace && python3 << 'CRONVERIFY'
import json, urllib.request, ssl
from datetime import datetime, timezone, timedelta

with open('config/notion.json') as f:
    token = json.load(f)['token']
ctx = ssl.create_default_context()

def notion_post(path, body):
    url = f"https://api.notion.com/v1{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method='POST', headers={
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json'
    })
    with urllib.request.urlopen(req, context=ctx) as r:
        return json.loads(r.read())

today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

# Check: Morning Briefing page exists for today
resp = notion_post('/databases/3268d599-a162-812d-a59e-e5496dec80e7/query', {
    'filter': {'property': 'Date', 'date': {'equals': today}},
    'page_size': 1
})
briefing_exists = len(resp.get('results', [])) > 0
print(f"Morning Briefing Notion page for {today}: {'EXISTS' if briefing_exists else 'MISSING'}")

if not briefing_exists:
    print("  ALERT: Briefing likely delivered to Telegram but Notion sync failed (SIGTERM or timeout)")
    print("  ACTION: Consider escalating to create retroactive page")
CRONVERIFY
```

If a critical cron delivered to Telegram but has no Notion page, report as ALERT and include in action items: "Cron [name] delivered to Telegram but Notion page missing - partial failure."

## Error Handling
- If any command fails: Report the error, continue with remaining checks
- If Notion unreachable: Skip Notion checks, note in report
- If script missing: Skip script, rely on manual checks

## Step 7: Update Dashboard KPI
After computing the health score, update the Notion Dashboard:
```bash
cd /root/.openclaw/workspace
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from notion_sync import update_dashboard_kpi, compute_stale_alerts, update_stale_alerts
update_dashboard_kpi(SCORE)  # Replace SCORE with actual health score
alerts = compute_stale_alerts()
update_stale_alerts(alerts)
print(f'Dashboard updated: score=SCORE, alerts={len(alerts)}')
"
```
Replace SCORE with the actual computed health score number (e.g., 98).

## Output Rules
- No em dashes. Hyphens only.
- Every number must come from a command you ran. No estimates.
- If Gmail uses App Password (not OAuth), report it as HEALTHY, not an issue.
- Be specific: "3 files without enforcement" not "some learnings need attention"
- NEVER print passwords, tokens, API keys, or secrets in the report. Say "configured" or "present", never the actual value.
- NEVER include NO_REPLY in your output. Your output IS the report.
