---
name: sie-360
description: "Self-Improvement Engine daily run: verify system state with real commands, audit learnings enforcement, detect patterns."
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
# Gmail - verify App Password auth works (NOT OAuth)
echo "GMAIL:" && grep -q "passwd" ~/.config/himalaya/config.toml 2>/dev/null && echo "App Password configured" || echo "NOT configured"

# Notion - verify token exists
echo "NOTION:" && python3 -c "
import json
with open('/root/.openclaw/workspace/config/notion.json') as f:
    d = json.load(f)
print('Token present' if d.get('token') else 'NO TOKEN')
print(f'Databases: {len(d.get(\"databases\", {}))}')
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

Actions needed: [specific list with priority]
```

## Error Handling
- If any command fails: Report the error, continue with remaining checks
- If Notion unreachable: Skip Notion checks, note in report
- If script missing: Skip script, rely on manual checks

## Output Rules
- No em dashes. Hyphens only.
- Every number must come from a command you ran. No estimates.
- If Gmail uses App Password (not OAuth), report it as HEALTHY, not an issue.
- Be specific: "3 files without enforcement" not "some learnings need attention"
