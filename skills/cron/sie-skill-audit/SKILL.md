---
name: sie-skill-audit
description: "Weekly audit of all skills: verify SKILL.md exists, check for broken references, validate triggers."
---

# SIE Skill Audit (Weekly)

Audit all installed skills for health and consistency.

## Steps

### Step 1: Scan all skill directories
Find all SKILL.md files in `skills/` and `~/.openclaw/workspace/skills/`.

### Step 2: Validate each skill
For each SKILL.md:
- Has name and description in frontmatter?
- Has Prerequisites section?
- Has Steps section?
- Has Error Handling section?
- References valid file paths?

### Step 3: Check for orphans
- Skills with no cron referencing them
- Crons with no skill file

### Step 4: Grade each skill
- A: Complete (all sections, valid paths)
- B: Functional (missing some sections)
- C: Broken (missing file, bad references)

### Step 5: Report
"🔍 Skill audit: [X] total, [Y] grade A, [Z] need attention"
List any grade C skills.

## Error Handling
- If skill directory not found: Report as critical issue

## Output Rules
- No em dashes. Hyphens only.
