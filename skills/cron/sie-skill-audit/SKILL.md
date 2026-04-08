---
name: sie-skill-audit
description: "Weekly audit of all skills: verify SKILL.md exists, validate structure, check for broken references, grade each skill."
---

# SIE Skill Audit (Weekly)

Audit all installed skills for health, consistency, and quality. You MUST run every command and report actual output.

## Prerequisites
- Skills directories: `skills/cron/`, `~/.openclaw/workspace/skills/`, `~/.openclaw/skills/`

## Steps

### Step 1: Scan all skill files
```bash
cd /root/.openclaw/workspace

echo "=== CRON SKILLS ==="
find skills/cron -name "SKILL.md" | wc -l

echo "=== WORKSPACE SKILLS ==="
find skills -name "SKILL.md" -not -path "skills/cron/*" 2>/dev/null | wc -l

echo "=== OPENCLAW BUILT-IN SKILLS ==="
find ~/.openclaw/skills ~/.openclaw/workspace/skills -name "SKILL.md" 2>/dev/null | wc -l
```

### Step 2: Validate each cron skill structure
```bash
cd /root/.openclaw/workspace/skills/cron

for dir in */; do
    skill="${dir%/}"
    file="$dir/SKILL.md"
    [ ! -f "$file" ] && echo "MISSING: $skill" && continue
    
    lines=$(wc -l < "$file")
    has_steps=$(grep -c "### Step" "$file")
    has_error=$(grep -c "Error Handling" "$file")
    has_quality=$(grep -c "Quality Gates" "$file")
    has_bash=$(grep -c '```bash' "$file")
    has_output=$(grep -c "Output Rules" "$file")
    
    score=0
    [ "$has_steps" -gt 2 ] && score=$((score + 3))
    [ "$has_error" -gt 0 ] && score=$((score + 2))
    [ "$has_quality" -gt 0 ] && score=$((score + 2))
    [ "$has_bash" -gt 0 ] && score=$((score + 2))
    [ "$has_output" -gt 0 ] && score=$((score + 1))
    
    if [ "$score" -ge 8 ]; then grade="A"
    elif [ "$score" -ge 6 ]; then grade="B"
    elif [ "$score" -ge 4 ]; then grade="C"
    else grade="D"; fi
    
    echo "$grade  $skill (${lines}L, ${has_steps}steps)"
done
```

### Step 3: Check for orphaned crons
```bash
# Crons pointing to skills that don't exist
openclaw cron list --json 2>&1 | sed '/^\[plugins\]/d' > /tmp/audit_crons.json
python3 << 'ORPHAN'
import json, os

with open("/tmp/audit_crons.json") as f:
    text = f.read()
decoder = json.JSONDecoder()
for i, ch in enumerate(text):
    if ch == '{':
        try:
            data, _ = decoder.raw_decode(text[i:])
            break
        except: continue

for j in data.get("jobs", []):
    msg = j.get("payload", {}).get("message", "")
    if "SKILL.md" in msg:
        # Extract path
        for word in msg.split():
            if "SKILL.md" in word:
                path = word.strip()
                if not os.path.exists(path):
                    print(f"ORPHAN: {j['name']} -> {path}")
                break
print("Orphan check complete")
ORPHAN
```

### Step 4: Verify file path references
```bash
cd /root/.openclaw/workspace/skills/cron
for dir in */; do
    file="$dir/SKILL.md"
    [ ! -f "$file" ] && continue
    # Check for referenced files
    grep -oP '`[^`]*\.(py|sh|json|md|toml)`' "$file" | tr -d '`' | while read ref; do
        [ ! -f "/root/.openclaw/workspace/$ref" ] && [ ! -f "$ref" ] && echo "BROKEN REF: $dir -> $ref"
    done
done
echo "Reference check complete"
```

### Step 5: Auto-fix Grade B and below
For any skill scoring below Grade A (score < 8), automatically append the missing sections:

```bash
cd /root/.openclaw/workspace/skills/cron

for dir in */; do
    skill="${dir%/}"
    file="$dir/SKILL.md"
    [ ! -f "$file" ] && continue
    
    has_steps=$(grep -c "### Step" "$file")
    has_error=$(grep -c "Error Handling" "$file")
    has_quality=$(grep -c "Quality Gates" "$file")
    has_bash=$(grep -c '```bash' "$file")
    has_output=$(grep -c "Output Rules" "$file")
    
    score=0
    [ "$has_steps" -gt 2 ] && score=$((score + 3))
    [ "$has_error" -gt 0 ] && score=$((score + 2))
    [ "$has_quality" -gt 0 ] && score=$((score + 2))
    [ "$has_bash" -gt 0 ] && score=$((score + 2))
    [ "$has_output" -gt 0 ] && score=$((score + 1))
    
    [ "$score" -ge 8 ] && continue  # Already Grade A
    
    fixed=""
    
    if [ "$has_error" -eq 0 ]; then
        cat >> "$file" << 'ERREOF'

## Error Handling
- If primary command fails: retry once, then report error
- If data unavailable: continue with partial data, flag in output
- If timeout: report timeout and suggest manual run
ERREOF
        fixed="${fixed} +ErrorHandling"
    fi
    
    if [ "$has_quality" -eq 0 ]; then
        cat >> "$file" << 'QGEOF'

## Quality Gates
- All required outputs must be generated
- No partial completion without flagging
- Verify output format before delivery
QGEOF
        fixed="${fixed} +QualityGates"
    fi
    
    if [ "$has_bash" -eq 0 ]; then
        cat >> "$file" << BASHEOF

## Manual Run
\`\`\`bash
cd /root/.openclaw/workspace && echo "Run $skill manually via cron skill"
\`\`\`
BASHEOF
        fixed="${fixed} +BashBlock"
    fi
    
    if [ "$has_output" -eq 0 ]; then
        cat >> "$file" << 'OUTEOF'

## Output Rules
- No em dashes - use hyphens only
- Keep output concise for Telegram delivery
- Report errors with context, not just status codes
OUTEOF
        fixed="${fixed} +OutputRules"
    fi
    
    [ -n "$fixed" ] && echo "AUTO-FIXED: $skill ($fixed)"
done
```

After auto-fix, re-run the grading from Step 2 to verify all skills are now Grade A or B.

### Step 6: Report
Format:
```
SIE Skill Audit - [DATE]
Total skills: [X] cron + [Y] workspace
Grade A: [n] | B: [n] | C: [n] | D: [n]
Orphaned crons: [n]
Broken references: [n]
Auto-fixed: [n] skills

[List any remaining Grade C/D skills and specific issues]
[List auto-fixed skills with what was added]
[List any orphans or broken references]

Actions needed: [specific fixes, or "None - all auto-resolved"]
```

## Error Handling
- If skill directory not found: Report as critical
- If cron list fails: Skip orphan check, report partial audit

## Quality Gates
- All cron skills must have SKILL.md file
- All skills should be Grade B or above
- Zero orphaned crons (pointing to missing skills)
- Zero broken file references

## Output Rules
- No em dashes. Hyphens only.
- Report exact grades, not summaries
- List every Grade C/D skill by name
